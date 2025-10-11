from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..routes.auth import require_auth
from ..models import User
from ..repository import get_repository
from ..services import ProductService
from ..schemas import (
    ProductSearchResult,
    StoreSearchResult,
    GroupSearchResult,
    SearchResponse,
)

router = APIRouter(prefix="/search", tags=["search"])

@router.get("", response_model=SearchResponse)
async def search_all(
    q: str = Query(..., min_length=1, description="Search query"),
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Consolidated search across products, stores, and groups.
    Returns up to 3 results per category.
    """
    repo = get_repository(db)

    # Search products
    product_service = ProductService(repo)
    all_products = product_service.search_products(q)
    products = all_products[:3]  # Limit to 3

    # Search stores
    all_stores = repo.search_stores(q)
    stores = [
        StoreSearchResult(
            id=str(store.id),
            name=store.name,
            address=store.address
        )
        for store in all_stores[:3]  # Limit to 3
    ]

    # Search groups (only user's groups - Group objects from repository)
    user_groups = repo.get_user_groups(current_user)
    matching_groups = []
    for group in user_groups:
        if q.lower() in group.name.lower():
            # Group object has members relationship set up by repository
            member_count = len(group.members)
            matching_groups.append(GroupSearchResult(
                id=str(group.id),
                name=group.name,
                member_count=member_count
            ))
            if len(matching_groups) >= 3:
                break

    return SearchResponse(
        products=products,
        stores=stores,
        groups=matching_groups
    )
