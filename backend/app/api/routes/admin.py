"""Admin routes for managing users, products, and stores."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db
from app.core.exceptions import ForbiddenError
from app.core.models import User
from app.api.routes.auth import require_auth
from app.api.schemas import (
    AdminProductResponse,
    AdminStoreResponse,
    AdminUserResponse,
    VerificationToggleResponse,
)
from app.services import AdminService

router = APIRouter(prefix='/admin', tags=['admin'])


def require_admin(current_user: User = Depends(require_auth)) -> User:
    """Verify that the current user is an admin."""
    if not current_user.is_admin:
        raise ForbiddenError('Admin access required')
    return current_user


@router.get('/users', response_model=list[AdminUserResponse])
async def get_users(
    search: str | None = Query(None),
    verified: bool | None = Query(None),
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get all users with optional search and filtering (paginated, max 100 per page)."""
    service = AdminService(db)
    return service.get_users(search, verified, limit, offset)


@router.post('/users/{user_id}/verify', response_model=VerificationToggleResponse)
async def toggle_user_verification(
    user_id: str, admin_user: User = Depends(require_admin), db: Session = Depends(get_db)
):
    """Toggle user verification status."""
    service = AdminService(db)
    return service.toggle_user_verification(UUID(user_id), admin_user)


@router.get('/products', response_model=list[AdminProductResponse])
async def get_products(
    search: str | None = Query(None),
    verified: bool | None = Query(None),
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get all products with optional search and filtering (paginated, max 100 per page)."""
    service = AdminService(db)
    return service.get_products(search, verified, limit, offset)


@router.post('/products/{product_id}/verify', response_model=VerificationToggleResponse)
async def toggle_product_verification(
    product_id: str, admin_user: User = Depends(require_admin), db: Session = Depends(get_db)
):
    """Toggle product verification status."""
    service = AdminService(db)
    return service.toggle_product_verification(UUID(product_id), admin_user)


@router.get('/stores', response_model=list[AdminStoreResponse])
async def get_stores(
    search: str | None = Query(None),
    verified: bool | None = Query(None),
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get all stores with optional search and filtering (paginated, max 100 per page)."""
    service = AdminService(db)
    return service.get_stores(search, verified, limit, offset)


@router.post('/stores/{store_id}/verify', response_model=VerificationToggleResponse)
async def toggle_store_verification(
    store_id: str, admin_user: User = Depends(require_admin), db: Session = Depends(get_db)
):
    """Toggle store verification status."""
    service = AdminService(db)
    return service.toggle_store_verification(UUID(store_id), admin_user)


# ==================== Update Routes ====================


@router.put('/products/{product_id}', response_model=AdminProductResponse)
async def update_product(
    product_id: str,
    request: 'UpdateProductRequest',
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Update product fields."""
    from app.api.schemas import UpdateProductRequest

    service = AdminService(db)
    return service.update_product(UUID(product_id), request.dict(), admin_user)


@router.put('/stores/{store_id}', response_model=AdminStoreResponse)
async def update_store(
    store_id: str,
    request: 'UpdateStoreRequest',
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Update store fields."""
    from app.api.schemas import UpdateStoreRequest

    service = AdminService(db)
    return service.update_store(UUID(store_id), request.dict(), admin_user)


@router.put('/users/{user_id}', response_model=AdminUserResponse)
async def update_user(
    user_id: str,
    request: 'UpdateUserRequest',
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Update user fields."""
    from app.api.schemas import UpdateUserRequest

    service = AdminService(db)
    return service.update_user(UUID(user_id), request.dict(), admin_user)


# ==================== Merge Routes ====================


@router.post('/products/{source_id}/merge/{target_id}', response_model='MergeResponse')
async def merge_products(
    source_id: str,
    target_id: str,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Merge one product into another. All bids and availabilities will be transferred."""
    from app.api.schemas import MergeResponse

    service = AdminService(db)
    return service.merge_products(UUID(source_id), UUID(target_id), admin_user)


@router.post('/stores/{source_id}/merge/{target_id}', response_model='MergeResponse')
async def merge_stores(
    source_id: str,
    target_id: str,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Merge one store into another. All runs and availabilities will be transferred."""
    from app.api.schemas import MergeResponse

    service = AdminService(db)
    return service.merge_stores(UUID(source_id), UUID(target_id), admin_user)


# ==================== Delete Routes ====================


@router.delete('/products/{product_id}', response_model='DeleteResponse')
async def delete_product(
    product_id: str, admin_user: User = Depends(require_admin), db: Session = Depends(get_db)
):
    """Delete a product. Cannot delete if it has associated bids."""
    from app.api.schemas import DeleteResponse

    service = AdminService(db)
    return service.delete_product(UUID(product_id), admin_user)


@router.delete('/stores/{store_id}', response_model='DeleteResponse')
async def delete_store(
    store_id: str, admin_user: User = Depends(require_admin), db: Session = Depends(get_db)
):
    """Delete a store. Cannot delete if it has associated runs."""
    from app.api.schemas import DeleteResponse

    service = AdminService(db)
    return service.delete_store(UUID(store_id), admin_user)


@router.delete('/users/{user_id}', response_model='DeleteResponse')
async def delete_user(
    user_id: str, admin_user: User = Depends(require_admin), db: Session = Depends(get_db)
):
    """Delete a user. Cannot delete yourself or other admins."""
    from app.api.schemas import DeleteResponse

    service = AdminService(db)
    return service.delete_user(UUID(user_id), admin_user)
