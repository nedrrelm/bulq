"""Sale routes for managing sales."""

from fastapi import APIRouter, Depends

from app.api.dependencies import SaleServiceDep
from app.api.routes.auth import require_auth
from app.api.schemas import (
    AddSaleProductRequest,
    CreateSaleRequest,
    SaleDetailResponse,
    SaleResponse,
    UpdateSaleProductRequest,
    UpdateSaleRequest,
)
from app.core.models import User
from app.utils.validation import validate_uuid

router = APIRouter(prefix='/sales', tags=['sales'])


@router.post('', response_model=SaleResponse)
async def create_sale(
    request: CreateSaleRequest,
    service: SaleServiceDep,
    current_user: User = Depends(require_auth),
):
    """Create a new sale."""
    return await service.create_sale(current_user, request.title, request.description)


@router.get('/my-sales', response_model=list[SaleResponse])
async def get_my_sales(
    service: SaleServiceDep,
    current_user: User = Depends(require_auth),
):
    """Get all sales for the current seller."""
    return await service.get_my_sales(current_user)


@router.get('/{sale_id}', response_model=SaleDetailResponse)
async def get_sale_details(
    sale_id: str,
    service: SaleServiceDep,
    current_user: User = Depends(require_auth),
):
    """Get sale details with products."""
    sale_uuid = validate_uuid(sale_id, 'Sale')
    return await service.get_sale_details(sale_uuid)


@router.patch('/{sale_id}', response_model=SaleDetailResponse)
async def update_sale(
    sale_id: str,
    request: UpdateSaleRequest,
    service: SaleServiceDep,
    current_user: User = Depends(require_auth),
):
    """Update sale title/description."""
    sale_uuid = validate_uuid(sale_id, 'Sale')
    return await service.update_sale(current_user, sale_uuid, request.title, request.description)


@router.post('/{sale_id}/products', response_model=SaleDetailResponse)
async def add_product_to_sale(
    sale_id: str,
    request: AddSaleProductRequest,
    service: SaleServiceDep,
    current_user: User = Depends(require_auth),
):
    """Add a product to a sale."""
    sale_uuid = validate_uuid(sale_id, 'Sale')
    product_uuid = validate_uuid(request.product_id, 'Product')
    return await service.add_product_to_sale(
        current_user, sale_uuid, product_uuid, request.price, request.available_quantity
    )


@router.patch('/{sale_id}/products/{product_id}', response_model=SaleDetailResponse)
async def update_sale_product(
    sale_id: str,
    product_id: str,
    request: UpdateSaleProductRequest,
    service: SaleServiceDep,
    current_user: User = Depends(require_auth),
):
    """Update a sale product's price/quantity."""
    sale_uuid = validate_uuid(sale_id, 'Sale')
    product_uuid = validate_uuid(product_id, 'Product')
    return await service.update_sale_product(
        current_user, sale_uuid, product_uuid, request.price, request.available_quantity
    )


@router.delete('/{sale_id}/products/{product_id}', response_model=SaleDetailResponse)
async def remove_product_from_sale(
    sale_id: str,
    product_id: str,
    service: SaleServiceDep,
    current_user: User = Depends(require_auth),
):
    """Remove a product from a sale."""
    sale_uuid = validate_uuid(sale_id, 'Sale')
    product_uuid = validate_uuid(product_id, 'Product')
    return await service.remove_product_from_sale(current_user, sale_uuid, product_uuid)


@router.post('/{sale_id}/activate', response_model=SaleDetailResponse)
async def activate_sale(
    sale_id: str,
    service: SaleServiceDep,
    current_user: User = Depends(require_auth),
):
    """Activate a sale (PLANNING → ACTIVE)."""
    sale_uuid = validate_uuid(sale_id, 'Sale')
    return await service.activate_sale(current_user, sale_uuid)


@router.post('/{sale_id}/deactivate', response_model=SaleDetailResponse)
async def deactivate_sale(
    sale_id: str,
    service: SaleServiceDep,
    current_user: User = Depends(require_auth),
):
    """Deactivate a sale (ACTIVE → PLANNING)."""
    sale_uuid = validate_uuid(sale_id, 'Sale')
    return await service.deactivate_sale(current_user, sale_uuid)


@router.post('/{sale_id}/cancel', response_model=SaleDetailResponse)
async def cancel_sale(
    sale_id: str,
    service: SaleServiceDep,
    current_user: User = Depends(require_auth),
):
    """Cancel a sale."""
    sale_uuid = validate_uuid(sale_id, 'Sale')
    return await service.cancel_sale(current_user, sale_uuid)
