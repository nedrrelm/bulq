from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.auth import require_auth
from app.api.schemas import (
    GroupSearchResult,
    SearchResponse,
    StoreSearchResult,
)
from app.core.models import User
from app.infrastructure.database import get_db
from app.services import ProductService

router = APIRouter(prefix='/search', tags=['search'])


@router.get('', response_model=SearchResponse)
async def search_all(
    q: str = Query(..., min_length=1, description='Search query'),
    current_user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """Consolidated search across products, stores, and groups.

    Returns up to 3 results per category.
    """
    # Search products
    product_service = ProductService(db)
    repo = product_service.product_repo
    all_products = await product_service.search_products(q)
    products = all_products[:3]  # Limit to 3

    # Search stores
    all_stores = await repo.search_stores(q)
    stores = [
        StoreSearchResult(id=str(store.id), name=store.name, address=store.address)
        for store in all_stores[:3]  # Limit to 3
    ]

    # Search groups (only user's groups - Group objects from repository)
    user_groups = await product_service.user_repo.get_user_groups(current_user)
    matching_groups = []
    for group in user_groups:
        if q.lower() in group.name.lower():
            # Group object has members relationship set up by repository
            member_count = await product_service.group_repo.get_group_member_count(group.id)
            matching_groups.append(
                GroupSearchResult(id=str(group.id), name=group.name, member_count=member_count)
            )
            if len(matching_groups) >= 3:
                break

    return SearchResponse(products=products, stores=stores, groups=matching_groups)
