from fastapi import APIRouter, Depends, Query

from app.api.dependencies import ProductServiceDep
from app.api.routes.auth import require_auth
from app.api.schemas import (
    AvailabilityInfo,
    CreateProductRequest,
    CreateProductResponse,
    ProductDetailResponse,
    ProductSearchResult,
)
from app.core.error_codes import PRODUCT_NOT_FOUND
from app.core.exceptions import NotFoundError
from app.core.models import User
from app.utils.validation import validate_uuid

router = APIRouter(prefix='/products', tags=['products'])


@router.get('/search', response_model=list[ProductSearchResult])
async def search_products(
    service: ProductServiceDep,
    q: str = Query(..., min_length=1, description='Search query'),
    current_user: User = Depends(require_auth),
):
    """Search for products by name across all stores.

    Returns products matching the search query.
    """
    return service.search_products(q)


@router.get('/check-similar', response_model=list[ProductSearchResult])
async def check_similar_products(
    service: ProductServiceDep,
    name: str = Query(..., min_length=1, description='Product name to check for similarity'),
    current_user: User = Depends(require_auth),
):
    """Check for products with similar names.

    Returns products that are similar to the provided name, useful for preventing duplicates.
    """
    return service.get_similar_products(name)


@router.post('/create', response_model=CreateProductResponse)
async def create_product(
    request: CreateProductRequest,
    service: ProductServiceDep,
    current_user: User = Depends(require_auth),
):
    """Create a new product and optionally link to a store with price."""
    store_uuid = validate_uuid(request.store_id, 'Store') if request.store_id else None

    product, availability = service.create_product(
        name=request.name,
        brand=request.brand,
        unit=request.unit,
        store_id=store_uuid,
        price=request.price,
        minimum_quantity=request.minimum_quantity,
        user_id=current_user.id,
    )

    availability_info = None
    if availability:
        availability_info = AvailabilityInfo(
            store_id=str(availability.store_id),
            price=float(availability.price) if availability.price else None,
            notes=availability.notes,
        )

    return CreateProductResponse(
        id=str(product.id),
        name=product.name,
        brand=product.brand,
        unit=product.unit,
        availability=availability_info,
    )


@router.get('/{product_id}', response_model=ProductDetailResponse)
async def get_product_details(
    product_id: str, service: ProductServiceDep, current_user: User = Depends(require_auth)
):
    """Get detailed product information including price history from shopping list items.

    Shows the product across different stores and historical prices recorded during shopping.
    """
    result = service.get_product_details(validate_uuid(product_id, 'Product'))
    if not result:
        raise NotFoundError(
            code=PRODUCT_NOT_FOUND, message='Product not found', product_id=product_id
        )

    return result
