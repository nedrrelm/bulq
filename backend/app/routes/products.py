from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel
from ..database import get_db
from ..routes.auth import require_auth
from ..models import User
from ..repository import get_repository
from ..services import ProductService

router = APIRouter(prefix="/products", tags=["products"])

class CreateProductRequest(BaseModel):
    name: str
    brand: Optional[str] = None
    unit: Optional[str] = None
    store_id: Optional[str] = None  # Optional: add availability if provided
    price: Optional[float] = None    # Optional: price for availability

class StoreInfo(BaseModel):
    store_id: str
    store_name: str
    price: Optional[float]

class ProductSearchResult(BaseModel):
    id: str
    name: str
    brand: Optional[str]
    stores: List[StoreInfo]

class AvailabilityInfo(BaseModel):
    store_id: str
    price: Optional[float]
    notes: Optional[str]

class CreateProductResponse(BaseModel):
    id: str
    name: str
    brand: Optional[str]
    unit: Optional[str]
    availability: Optional[AvailabilityInfo] = None

class PricePoint(BaseModel):
    price: float
    notes: str
    timestamp: Optional[str]
    run_id: Optional[str] = None

class StoreDetail(BaseModel):
    store_id: str
    store_name: str
    current_price: Optional[float]
    price_history: List[PricePoint]

class ProductDetailResponse(BaseModel):
    id: str
    name: str
    brand: Optional[str]
    unit: Optional[str]
    stores: List[StoreDetail]

@router.get("/search", response_model=List[ProductSearchResult])
async def search_products(
    q: str = Query(..., min_length=1, description="Search query"),
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Search for products by name across all stores.
    Returns products matching the search query.
    """
    repo = get_repository(db)
    service = ProductService(repo)
    results = service.search_products(q)
    return [ProductSearchResult(**r) for r in results]

@router.post("/create", response_model=CreateProductResponse)
async def create_product(
    request: CreateProductRequest,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Create a new product. Optionally link to a store with price.
    """
    repo = get_repository(db)
    service = ProductService(repo)

    try:
        store_uuid = UUID(request.store_id) if request.store_id else None

        product, availability = service.create_product(
            name=request.name,
            brand=request.brand,
            unit=request.unit,
            store_id=store_uuid,
            price=request.price,
            user_id=current_user.id
        )

        availability_info = None
        if availability:
            availability_info = AvailabilityInfo(
                store_id=str(availability.store_id),
                price=float(availability.price) if availability.price else None,
                notes=availability.notes
            )

        return CreateProductResponse(
            id=str(product.id),
            name=product.name,
            brand=product.brand,
            unit=product.unit,
            availability=availability_info
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{product_id}", response_model=ProductDetailResponse)
async def get_product_details(
    product_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Get detailed product information including price history from shopping list items.
    Shows the product across different stores and historical prices recorded during shopping.
    """
    repo = get_repository(db)
    service = ProductService(repo)

    result = service.get_product_details(UUID(product_id))
    if not result:
        raise HTTPException(status_code=404, detail="Product not found")

    return ProductDetailResponse(**result)
