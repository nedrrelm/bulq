from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db
from app.core.models import User
from app.api.routes.auth import require_auth
from app.api.schemas import (
    AvailabilityInfo,
    CreateProductRequest,
    CreateProductResponse,
    ProductDetailResponse,
    ProductSearchResult,
)
from app.services import ProductService

router = APIRouter(prefix='/products', tags=['products'])


@router.get('/search', response_model=list[ProductSearchResult])
async def search_products(
    q: str = Query(..., min_length=1, description='Search query'),
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Search for products by name across all stores.

    Returns products matching the search query.
    """
    service = ProductService(db)
    return service.search_products(q)


@router.get('/check-similar', response_model=list[ProductSearchResult])
async def check_similar_products(
    name: str = Query(..., min_length=1, description='Product name to check for similarity'),
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Check for products with similar names.

    Returns products that are similar to the provided name, useful for preventing duplicates.
    """
    service = ProductService(db)
    return service.get_similar_products(name)


@router.post('/create', response_model=CreateProductResponse)
async def create_product(
    request: CreateProductRequest,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Create a new product and optionally link to a store with price."""
    service = ProductService(db)

    try:
        store_uuid = UUID(request.store_id) if request.store_id else None

        product, availability = service.create_product(
            name=request.name,
            brand=request.brand,
            unit=request.unit,
            store_id=store_uuid,
            price=request.price,
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
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get('/{product_id}', response_model=ProductDetailResponse)
async def get_product_details(
    product_id: str, current_user: User = Depends(require_auth), db: Session = Depends(get_db)
):
    """Get detailed product information including price history from shopping list items.

    Shows the product across different stores and historical prices recorded during shopping.
    """
    service = ProductService(db)

    result = service.get_product_details(UUID(product_id))
    if not result:
        raise HTTPException(status_code=404, detail='Product not found')

    return result
