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
    store_id: str
    name: str
    base_price: float

@router.get("/search")
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
    return service.search_products(q)

@router.post("/create")
async def create_product(
    request: CreateProductRequest,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Create a new product for a store.
    """
    repo = get_repository(db)
    service = ProductService(repo)

    try:
        product = service.create_product(
            store_id=UUID(request.store_id),
            name=request.name,
            base_price=request.base_price
        )
        return {
            "id": str(product.id),
            "name": product.name,
            "store_id": str(product.store_id),
            "base_price": float(product.base_price)
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{product_id}")
async def get_product_details(
    product_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Get detailed product information including price history from shopping list items.
    Shows the product across different stores and historical prices encountered during shopping.
    """
    repo = get_repository(db)
    service = ProductService(repo)

    result = service.get_product_details(UUID(product_id))
    if not result:
        raise HTTPException(status_code=404, detail="Product not found")

    return result
