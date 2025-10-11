"""Admin routes for managing users, products, and stores."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel

from ..database import get_db
from ..models import User
from ..routes.auth import require_auth
from ..repository import get_repository
from ..services import AdminService
from ..exceptions import ForbiddenError

router = APIRouter(prefix="/admin", tags=["admin"])

class AdminUserResponse(BaseModel):
    id: str
    name: str
    email: str
    verified: bool
    is_admin: bool
    created_at: Optional[str]

class AdminProductResponse(BaseModel):
    id: str
    name: str
    brand: Optional[str]
    unit: Optional[str]
    verified: bool
    created_at: Optional[str]

class AdminStoreResponse(BaseModel):
    id: str
    name: str
    address: Optional[str]
    verified: bool
    created_at: Optional[str]

class VerificationToggleResponse(BaseModel):
    id: str
    verified: bool
    message: str


def require_admin(current_user: User = Depends(require_auth)) -> User:
    """Verify that the current user is an admin."""
    if not current_user.is_admin:
        raise ForbiddenError("Admin access required")
    return current_user


@router.get("/users", response_model=List[AdminUserResponse])
async def get_users(
    search: Optional[str] = Query(None),
    verified: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get all users with optional search and filtering (paginated, max 100 per page)."""
    repo = get_repository(db)
    service = AdminService(repo)
    results = service.get_users(search, verified, limit, offset)
    return [AdminUserResponse(**r) for r in results]


@router.post("/users/{user_id}/verify", response_model=VerificationToggleResponse)
async def toggle_user_verification(
    user_id: str,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Toggle user verification status."""
    repo = get_repository(db)
    service = AdminService(repo)
    result = service.toggle_user_verification(UUID(user_id), admin_user)
    return VerificationToggleResponse(**result)


@router.get("/products", response_model=List[AdminProductResponse])
async def get_products(
    search: Optional[str] = Query(None),
    verified: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get all products with optional search and filtering (paginated, max 100 per page)."""
    repo = get_repository(db)
    service = AdminService(repo)
    results = service.get_products(search, verified, limit, offset)
    return [AdminProductResponse(**r) for r in results]


@router.post("/products/{product_id}/verify", response_model=VerificationToggleResponse)
async def toggle_product_verification(
    product_id: str,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Toggle product verification status."""
    repo = get_repository(db)
    service = AdminService(repo)
    result = service.toggle_product_verification(UUID(product_id), admin_user)
    return VerificationToggleResponse(**result)


@router.get("/stores", response_model=List[AdminStoreResponse])
async def get_stores(
    search: Optional[str] = Query(None),
    verified: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get all stores with optional search and filtering (paginated, max 100 per page)."""
    repo = get_repository(db)
    service = AdminService(repo)
    results = service.get_stores(search, verified, limit, offset)
    return [AdminStoreResponse(**r) for r in results]


@router.post("/stores/{store_id}/verify", response_model=VerificationToggleResponse)
async def toggle_store_verification(
    store_id: str,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Toggle store verification status."""
    repo = get_repository(db)
    service = AdminService(repo)
    result = service.toggle_store_verification(UUID(store_id), admin_user)
    return VerificationToggleResponse(**result)
