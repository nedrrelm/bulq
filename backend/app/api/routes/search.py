from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import ProductServiceDep, StoreServiceDep
from app.api.routes.auth import require_auth
from app.api.schemas import (
    GroupSearchResult,
    SearchResponse,
    StoreSearchResult,
)
from app.core.models import User
from app.infrastructure.database import get_db
from app.repositories import get_user_repository

router = APIRouter(prefix='/search', tags=['search'])


@router.get('', response_model=SearchResponse)
async def search_all(
    product_service: ProductServiceDep,
    store_service: StoreServiceDep,
    db: Session = Depends(get_db),
    q: str = Query(..., min_length=1, description='Search query'),
    current_user: User = Depends(require_auth),
):
    """Consolidated search across products, stores, and groups.

    Returns up to 3 results per category.
    """
    # Search products
    all_products = product_service.search_products(q)
    products = all_products[:3]  # Limit to 3

    # Search stores
    all_stores = store_service.store_repo.search_stores(q)
    stores = [
        StoreSearchResult(id=str(store.id), name=store.name, address=store.address)
        for store in all_stores[:3]  # Limit to 3
    ]

    # Search groups (only user's groups - Group objects from repository)
    user_repo = get_user_repository(db)
    user_groups = user_repo.get_user_groups(current_user)
    matching_groups = []
    for group in user_groups:
        if q.lower() in group.name.lower():
            # Group object has members relationship set up by repository
            member_count = len(group.members)
            matching_groups.append(
                GroupSearchResult(id=str(group.id), name=group.name, member_count=member_count)
            )
            if len(matching_groups) >= 3:
                break

    return SearchResponse(products=products, stores=stores, groups=matching_groups)
