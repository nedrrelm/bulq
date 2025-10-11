from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from ..database import get_db
from ..models import User
from ..auth import hash_password, create_session, get_session, delete_session
from ..repository import get_repository
from ..exceptions import UnauthorizedError, BadRequestError
from ..config import SESSION_EXPIRY_HOURS, SECURE_COOKIES
from ..request_context import get_logger

router = APIRouter(prefix="/auth", tags=["authentication"])
logger = get_logger(__name__)




class UserRegister(BaseModel):
    name: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    is_admin: bool = False

class MessageResponse(BaseModel):
    message: str

def get_current_user(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    """Get current user from session cookie."""
    session_token = request.cookies.get("session_token")
    if not session_token:
        return None

    session = get_session(session_token)
    if not session:
        return None

    repo = get_repository(db)
    from uuid import UUID
    user_id = UUID(session["user_id"])
    user = repo.get_user_by_id(user_id)
    return user

def require_auth(request: Request, db: Session = Depends(get_db)) -> User:
    """Dependency that requires authentication."""
    user = get_current_user(request, db)
    if not user:
        logger.warning(
            "Unauthorized access attempt",
            extra={"path": request.url.path, "method": request.method}
        )
        raise UnauthorizedError("Authentication required")
    return user

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserRegister, response: Response, db: Session = Depends(get_db)):
    """Register a new user."""
    logger.info(
        "Registration attempt",
        extra={"email": user_data.email}
    )
    repo = get_repository(db)

    # Check if user already exists
    existing_user = repo.get_user_by_email(user_data.email)
    if existing_user:
        logger.warning(
            "Registration failed - email already exists",
            extra={"email": user_data.email}
        )
        raise BadRequestError("Email already registered")

    # Create new user
    password_hash = hash_password(user_data.password)
    new_user = repo.create_user(
        name=user_data.name,
        email=user_data.email,
        password_hash=password_hash
    )

    # Create session
    session_token = create_session(str(new_user.id))
    response.set_cookie(
        key="session_token",
        value=session_token,
        max_age=SESSION_EXPIRY_HOURS * 3600,  # Convert hours to seconds
        httponly=True,
        secure=SECURE_COOKIES,
        samesite="lax",
        path="/"
    )

    logger.info(
        "User registered successfully",
        extra={"user_id": str(new_user.id), "email": new_user.email}
    )

    return UserResponse(
        id=str(new_user.id),
        name=new_user.name,
        email=new_user.email
    )

@router.post("/login", response_model=UserResponse)
async def login(user_data: UserLogin, response: Response, db: Session = Depends(get_db)):
    """Login user."""
    logger.info(
        "Login attempt",
        extra={"email": user_data.email}
    )
    repo = get_repository(db)

    # Find user by email
    user = repo.get_user_by_email(user_data.email)
    if not user or not repo.verify_password(user_data.password, user.password_hash):
        logger.warning(
            "Failed login attempt",
            extra={"email": user_data.email}
        )
        raise UnauthorizedError("Invalid email or password")

    # Create session
    session_token = create_session(str(user.id))
    response.set_cookie(
        key="session_token",
        value=session_token,
        max_age=SESSION_EXPIRY_HOURS * 3600,  # Convert hours to seconds
        httponly=True,
        secure=SECURE_COOKIES,
        samesite="lax",
        path="/"
    )

    logger.info(
        "User logged in successfully - Session cookie set",
        extra={
            "user_id": str(user.id),
            "email": user.email,
            "session_token_length": len(session_token),
            "max_age": SESSION_EXPIRY_HOURS * 3600
        }
    )

    return UserResponse(
        id=str(user.id),
        name=user.name,
        email=user.email,
        is_admin=user.is_admin
    )

@router.post("/logout", response_model=MessageResponse)
async def logout(request: Request, response: Response):
    """Logout user."""
    session_token = request.cookies.get("session_token")
    if session_token:
        delete_session(session_token)
        logger.info(
            "User logged out successfully",
            extra={"session_token_length": len(session_token)}
        )

    response.delete_cookie(key="session_token")
    return MessageResponse(message="Logged out successfully")

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(require_auth)):
    """Get current user information."""
    return UserResponse(
        id=str(current_user.id),
        name=current_user.name,
        email=current_user.email,
        is_admin=current_user.is_admin
    )