"""Admin routes for managing users, products, and stores."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import AdminServiceDep
from app.api.routes.auth import require_auth
from app.api.schemas import (
    AdminGroupResponse,
    AdminProductResponse,
    AdminStoreResponse,
    AdminUserResponse,
    DeleteResponse,
    MergeResponse,
    UpdateProductRequest,
    UpdateStoreRequest,
    UpdateUserRequest,
    VerificationToggleResponse,
)
from app.core.error_codes import NOT_SYSTEM_ADMIN
from app.core.exceptions import ForbiddenError
from app.core.models import User
from app.infrastructure.database import get_db
from app.utils.validation import validate_uuid

router = APIRouter(prefix='/admin', tags=['admin'])


def require_admin(current_user: User = Depends(require_auth)) -> User:
    """Verify that the current user is an admin."""
    if not current_user.is_admin:
        raise ForbiddenError(
            code=NOT_SYSTEM_ADMIN, message='Admin access required', user_id=str(current_user.id)
        )
    return current_user


@router.get('/users', response_model=list[AdminUserResponse])
async def get_users(
    service: AdminServiceDep,
    search: str | None = Query(None),
    verified: bool | None = Query(None),
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    admin_user: User = Depends(require_admin),
):
    """Get all users with optional search and filtering (paginated, max 100 per page)."""
    return await service.get_users(search, verified, limit, offset)


@router.post('/users/{user_id}/verify', response_model=VerificationToggleResponse)
async def toggle_user_verification(
    user_id: str, service: AdminServiceDep, admin_user: User = Depends(require_admin)
):
    """Toggle user verification status."""
    return await service.toggle_user_verification(validate_uuid(user_id, 'User'), admin_user)


@router.get('/groups', response_model=list[AdminGroupResponse])
async def get_groups(
    service: AdminServiceDep,
    search: str | None = Query(None),
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    admin_user: User = Depends(require_admin),
):
    """Get all groups with optional search (paginated, max 100 per page)."""
    return await service.get_groups(search, limit, offset)


@router.get('/products', response_model=list[AdminProductResponse])
async def get_products(
    service: AdminServiceDep,
    search: str | None = Query(None),
    verified: bool | None = Query(None),
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    admin_user: User = Depends(require_admin),
):
    """Get all products with optional search and filtering (paginated, max 100 per page)."""
    return await service.get_products(search, verified, limit, offset)


@router.post('/products/{product_id}/verify', response_model=VerificationToggleResponse)
async def toggle_product_verification(
    product_id: str, service: AdminServiceDep, admin_user: User = Depends(require_admin)
):
    """Toggle product verification status."""
    return await service.toggle_product_verification(
        validate_uuid(product_id, 'Product'), admin_user
    )


@router.get('/stores', response_model=list[AdminStoreResponse])
async def get_stores(
    service: AdminServiceDep,
    search: str | None = Query(None),
    verified: bool | None = Query(None),
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    admin_user: User = Depends(require_admin),
):
    """Get all stores with optional search and filtering (paginated, max 100 per page)."""
    return await service.get_stores(search, verified, limit, offset)


@router.post('/stores/{store_id}/verify', response_model=VerificationToggleResponse)
async def toggle_store_verification(
    store_id: str, service: AdminServiceDep, admin_user: User = Depends(require_admin)
):
    """Toggle store verification status."""
    return await service.toggle_store_verification(validate_uuid(store_id, 'Store'), admin_user)


# ==================== Update Routes ====================


@router.put('/products/{product_id}', response_model=AdminProductResponse)
async def update_product(
    product_id: str,
    data: UpdateProductRequest,
    service: AdminServiceDep,
    admin_user: User = Depends(require_admin),
):
    """Update product fields."""
    return await service.update_product(
        validate_uuid(product_id, 'Product'), data.model_dump(), admin_user
    )


@router.put('/stores/{store_id}', response_model=AdminStoreResponse)
async def update_store(
    store_id: str,
    data: UpdateStoreRequest,
    service: AdminServiceDep,
    admin_user: User = Depends(require_admin),
):
    """Update store fields."""
    return await service.update_store(
        validate_uuid(store_id, 'Store'), data.model_dump(), admin_user
    )


@router.put('/users/{user_id}', response_model=AdminUserResponse)
async def update_user(
    user_id: str,
    data: UpdateUserRequest,
    service: AdminServiceDep,
    admin_user: User = Depends(require_admin),
):
    """Update user fields."""
    return await service.update_user(validate_uuid(user_id, 'User'), data.model_dump(), admin_user)


# ==================== Merge Routes ====================


@router.post('/products/{source_id}/merge/{target_id}', response_model=MergeResponse)
async def merge_products(
    source_id: str,
    target_id: str,
    service: AdminServiceDep,
    admin_user: User = Depends(require_admin),
):
    """Merge one product into another. All bids and availabilities will be transferred."""
    return await service.merge_products(
        validate_uuid(source_id, 'Product'), validate_uuid(target_id, 'Product'), admin_user
    )


@router.post('/stores/{source_id}/merge/{target_id}', response_model=MergeResponse)
async def merge_stores(
    source_id: str,
    target_id: str,
    service: AdminServiceDep,
    admin_user: User = Depends(require_admin),
):
    """Merge one store into another. All runs and availabilities will be transferred."""
    return await service.merge_stores(
        validate_uuid(source_id, 'Store'), validate_uuid(target_id, 'Store'), admin_user
    )


@router.post('/users/{source_id}/merge/{target_id}', response_model=MergeResponse)
async def merge_users(
    source_id: str,
    target_id: str,
    service: AdminServiceDep,
    admin_user: User = Depends(require_admin),
):
    """Merge one user into another. All data will be transferred."""
    return await service.merge_users(
        validate_uuid(source_id, 'User'), validate_uuid(target_id, 'User'), admin_user
    )


# ==================== Delete Routes ====================


@router.delete('/products/{product_id}', response_model=DeleteResponse)
async def delete_product(
    product_id: str, service: AdminServiceDep, admin_user: User = Depends(require_admin)
):
    """Delete a product. Cannot delete if it has associated bids."""
    return await service.delete_product(validate_uuid(product_id, 'Product'), admin_user)


@router.delete('/stores/{store_id}', response_model=DeleteResponse)
async def delete_store(
    store_id: str, service: AdminServiceDep, admin_user: User = Depends(require_admin)
):
    """Delete a store. Cannot delete if it has associated runs."""
    return await service.delete_store(validate_uuid(store_id, 'Store'), admin_user)


@router.delete('/users/{user_id}', response_model=DeleteResponse)
async def delete_user(
    user_id: str, service: AdminServiceDep, admin_user: User = Depends(require_admin)
):
    """Delete a user. Cannot delete yourself or other admins."""
    return await service.delete_user(validate_uuid(user_id, 'User'), admin_user)


@router.get('/settings/registration')
async def get_registration_setting(
    admin_user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)
):
    """Get the current registration allowed setting."""
    from app.infrastructure.runtime_settings import is_registration_allowed

    return {'allow_registration': await is_registration_allowed(db)}


@router.post('/settings/registration')
async def set_registration_setting(
    allow_registration: bool,
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Enable or disable user registration."""
    from app.infrastructure.request_context import get_logger
    from app.infrastructure.runtime_settings import set_registration_allowed

    logger = get_logger(__name__)

    await set_registration_allowed(db, allow_registration)

    logger.info(
        f'Registration {"enabled" if allow_registration else "disabled"} by admin',
        extra={'admin_id': str(admin_user.id), 'admin_name': admin_user.name},
    )

    return {'allow_registration': allow_registration, 'message': 'Setting updated successfully'}
