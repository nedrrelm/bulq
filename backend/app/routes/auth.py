from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from ..database import get_db
from ..models import User
from ..auth import hash_password, create_session, get_session, delete_session
from ..repository import get_repository

router = APIRouter(prefix="/auth", tags=["authentication"])




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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return user

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserRegister, response: Response, db: Session = Depends(get_db)):
    """Register a new user."""
    repo = get_repository(db)

    # Check if user already exists
    existing_user = repo.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

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
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax"
    )

    return UserResponse(
        id=str(new_user.id),
        name=new_user.name,
        email=new_user.email
    )

@router.post("/login", response_model=UserResponse)
async def login(user_data: UserLogin, response: Response, db: Session = Depends(get_db)):
    """Login user."""
    repo = get_repository(db)

    # Find user by email
    user = repo.get_user_by_email(user_data.email)
    if not user or not repo.verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Create session
    session_token = create_session(str(user.id))
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax"
    )

    return UserResponse(
        id=str(user.id),
        name=user.name,
        email=user.email
    )

@router.post("/logout")
async def logout(request: Request, response: Response):
    """Logout user."""
    session_token = request.cookies.get("session_token")
    if session_token:
        delete_session(session_token)

    response.delete_cookie(key="session_token")
    return {"message": "Logged out successfully"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(require_auth)):
    """Get current user information."""
    return UserResponse(
        id=str(current_user.id),
        name=current_user.name,
        email=current_user.email
    )