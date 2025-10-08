from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from ..database import get_db
from ..routes.auth import require_auth
from ..models import User
from ..repository import get_repository
from ..services import ProductService

router = APIRouter(prefix="/products", tags=["products"])

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
