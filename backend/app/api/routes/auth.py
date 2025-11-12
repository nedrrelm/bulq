from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.infrastructure.auth import create_session, delete_session, get_session, hash_password
from app.infrastructure.config import SECURE_COOKIES, SESSION_EXPIRY_HOURS
from app.infrastructure.database import get_db
from app.core.exceptions import BadRequestError, UnauthorizedError
from app.core.models import User
from app.repositories import get_repository
from app.infrastructure.request_context import get_logger
from app.api.schemas import (
    ChangeNameRequest,
    ChangePasswordRequest,
    ChangeUsernameRequest,
    MessageResponse,
    UserLogin,
    UserRegister,
    UserResponse,
    UserStatsResponse,
)

router = APIRouter(prefix='/auth', tags=['authentication'])
logger = get_logger(__name__)


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    """Get current user from session cookie."""
    session_token = request.cookies.get('session_token')
    if not session_token:
        return None

    session = get_session(session_token)
    if not session:
        return None

    repo = get_repository(db)
    from uuid import UUID

    user_id = UUID(session['user_id'])
    user = repo.get_user_by_id(user_id)
    return user


def require_auth(request: Request, db: Session = Depends(get_db)) -> User:
    """Dependency that requires authentication."""
    user = get_current_user(request, db)
    if not user:
        logger.warning(
            'Unauthorized access attempt',
            extra={'path': request.url.path, 'method': request.method},
        )
        raise UnauthorizedError('Authentication required')
    return user


@router.post('/register', response_model=UserResponse)
async def register(
    user_data: UserRegister, response: Response, db: Session = Depends(get_db)
) -> UserResponse:
    """Register a new user."""
    logger.info('Registration attempt', extra={'username': user_data.username})
    repo = get_repository(db)

    # Check if user already exists
    existing_user = repo.get_user_by_username(user_data.username)
    if existing_user:
        logger.warning(
            'Registration failed - username already exists', extra={'username': user_data.username}
        )
        raise BadRequestError('Username already registered')

    # Create new user
    password_hash = hash_password(user_data.password)
    new_user = repo.create_user(
        name=user_data.name, username=user_data.username, password_hash=password_hash
    )

    # Create session
    session_token = create_session(str(new_user.id))
    response.set_cookie(
        key='session_token',
        value=session_token,
        max_age=SESSION_EXPIRY_HOURS * 3600,  # Convert hours to seconds
        httponly=True,
        secure=SECURE_COOKIES,
        samesite='lax',
        path='/',
    )

    logger.info(
        'User registered successfully', extra={'user_id': str(new_user.id), 'username': new_user.username}
    )

    return UserResponse(id=str(new_user.id), name=new_user.name, username=new_user.username)


@router.post('/login', response_model=UserResponse)
async def login(
    user_data: UserLogin, response: Response, db: Session = Depends(get_db)
) -> UserResponse:
    """Login user."""
    logger.info('Login attempt', extra={'username': user_data.username})
    repo = get_repository(db)

    # Find user by username
    user = repo.get_user_by_username(user_data.username)
    if not user or not repo.verify_password(user_data.password, user.password_hash):
        logger.warning('Failed login attempt', extra={'username': user_data.username})
        raise UnauthorizedError('Invalid username or password')

    # Create session
    session_token = create_session(str(user.id))
    response.set_cookie(
        key='session_token',
        value=session_token,
        max_age=SESSION_EXPIRY_HOURS * 3600,  # Convert hours to seconds
        httponly=True,
        secure=SECURE_COOKIES,
        samesite='lax',
        path='/',
    )

    logger.info(
        'User logged in successfully - Session cookie set',
        extra={
            'user_id': str(user.id),
            'username': user.username,
            'session_token_length': len(session_token),
            'max_age': SESSION_EXPIRY_HOURS * 3600,
        },
    )

    return UserResponse(id=str(user.id), name=user.name, username=user.username, is_admin=user.is_admin)


@router.post('/logout', response_model=MessageResponse)
async def logout(request: Request, response: Response) -> MessageResponse:
    """Logout user."""
    session_token = request.cookies.get('session_token')
    if session_token:
        delete_session(session_token)
        logger.info(
            'User logged out successfully', extra={'session_token_length': len(session_token)}
        )

    response.delete_cookie(key='session_token')
    return MessageResponse(message='Logged out successfully')


@router.get('/me', response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(require_auth)) -> UserResponse:
    """Get current user information."""
    return UserResponse(
        id=str(current_user.id),
        name=current_user.name,
        username=current_user.username,
        is_admin=current_user.is_admin,
    )


@router.get('/profile/stats', response_model=UserStatsResponse)
async def get_profile_stats(
    current_user: User = Depends(require_auth), db: Session = Depends(get_db)
) -> UserStatsResponse:
    """Get current user's statistics."""
    logger.info('Fetching user statistics', extra={'user_id': str(current_user.id)})
    repo = get_repository(db)
    stats = repo.get_user_stats(current_user.id)
    return UserStatsResponse(**stats)


@router.post('/change-password', response_model=MessageResponse)
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
) -> MessageResponse:
    """Change user password."""
    logger.info('Password change request', extra={'user_id': str(current_user.id)})
    repo = get_repository(db)

    # Verify current password using repository method (handles memory vs database)
    if not repo.verify_password(request.current_password, current_user.password_hash):
        logger.warning(
            'Password change failed - incorrect current password',
            extra={'user_id': str(current_user.id)},
        )
        raise UnauthorizedError('Current password is incorrect')

    # Hash new password and update
    from app.infrastructure.auth import hash_password

    new_password_hash = hash_password(request.new_password)
    repo.update_user(current_user.id, password_hash=new_password_hash)

    logger.info('Password changed successfully', extra={'user_id': str(current_user.id)})
    return MessageResponse(message='Password changed successfully')


@router.post('/change-username', response_model=UserResponse)
async def change_username(
    request: ChangeUsernameRequest,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
) -> UserResponse:
    """Change username."""
    logger.info(
        'Username change request',
        extra={'user_id': str(current_user.id), 'new_username': request.new_username},
    )
    repo = get_repository(db)

    # Verify current password using repository method (handles memory vs database)
    if not repo.verify_password(request.current_password, current_user.password_hash):
        logger.warning(
            'Username change failed - incorrect password', extra={'user_id': str(current_user.id)}
        )
        raise UnauthorizedError('Current password is incorrect')

    # Check if new username is already taken
    existing_user = repo.get_user_by_username(request.new_username)
    if existing_user and existing_user.id != current_user.id:
        logger.warning(
            'Username change failed - username already exists',
            extra={'user_id': str(current_user.id), 'new_username': request.new_username},
        )
        raise BadRequestError('Username already taken')

    # Update username
    updated_user = repo.update_user(current_user.id, username=request.new_username)
    if not updated_user:
        raise BadRequestError('Failed to update username')

    logger.info(
        'Username changed successfully',
        extra={
            'user_id': str(current_user.id),
            'old_username': current_user.username,
            'new_username': request.new_username,
        },
    )

    return UserResponse(
        id=str(updated_user.id),
        name=updated_user.name,
        username=updated_user.username,
        is_admin=updated_user.is_admin,
    )


@router.post('/change-name', response_model=UserResponse)
async def change_name(
    request: ChangeNameRequest,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
) -> UserResponse:
    """Change display name."""
    logger.info(
        'Name change request',
        extra={'user_id': str(current_user.id), 'new_name': request.new_name},
    )
    repo = get_repository(db)

    # Verify current password using repository method (handles memory vs database)
    if not repo.verify_password(request.current_password, current_user.password_hash):
        logger.warning(
            'Name change failed - incorrect password', extra={'user_id': str(current_user.id)}
        )
        raise UnauthorizedError('Current password is incorrect')

    # Update name
    updated_user = repo.update_user(current_user.id, name=request.new_name)
    if not updated_user:
        raise BadRequestError('Failed to update name')

    logger.info(
        'Name changed successfully',
        extra={
            'user_id': str(current_user.id),
            'old_name': current_user.name,
            'new_name': request.new_name,
        },
    )

    return UserResponse(
        id=str(updated_user.id),
        name=updated_user.name,
        username=updated_user.username,
        is_admin=updated_user.is_admin,
    )
