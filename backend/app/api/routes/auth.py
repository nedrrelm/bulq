from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.infrastructure.auth import create_session, delete_session, get_session, hash_password
from app.infrastructure.config import SECURE_COOKIES, SESSION_EXPIRY_HOURS
from app.infrastructure.database import get_db
from app.core.exceptions import BadRequestError, UnauthorizedError
from app.core.models import User
from app.core.repository import get_repository
from app.infrastructure.request_context import get_logger
from app.api.schemas import MessageResponse, UserLogin, UserRegister, UserResponse

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
    logger.info('Registration attempt', extra={'email': user_data.email})
    repo = get_repository(db)

    # Check if user already exists
    existing_user = repo.get_user_by_email(user_data.email)
    if existing_user:
        logger.warning(
            'Registration failed - email already exists', extra={'email': user_data.email}
        )
        raise BadRequestError('Email already registered')

    # Create new user
    password_hash = hash_password(user_data.password)
    new_user = repo.create_user(
        name=user_data.name, email=user_data.email, password_hash=password_hash
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
        'User registered successfully', extra={'user_id': str(new_user.id), 'email': new_user.email}
    )

    return UserResponse(id=str(new_user.id), name=new_user.name, email=new_user.email)


@router.post('/login', response_model=UserResponse)
async def login(
    user_data: UserLogin, response: Response, db: Session = Depends(get_db)
) -> UserResponse:
    """Login user."""
    logger.info('Login attempt', extra={'email': user_data.email})
    repo = get_repository(db)

    # Find user by email
    user = repo.get_user_by_email(user_data.email)
    if not user or not repo.verify_password(user_data.password, user.password_hash):
        logger.warning('Failed login attempt', extra={'email': user_data.email})
        raise UnauthorizedError('Invalid email or password')

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
            'email': user.email,
            'session_token_length': len(session_token),
            'max_age': SESSION_EXPIRY_HOURS * 3600,
        },
    )

    return UserResponse(id=str(user.id), name=user.name, email=user.email, is_admin=user.is_admin)


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
        email=current_user.email,
        is_admin=current_user.is_admin,
    )
