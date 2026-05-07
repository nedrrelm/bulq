from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import ProductServiceDep, SellerServiceDep, StoreServiceDep, TagServiceDep
from app.api.routes.auth import require_auth
from app.api.schemas import (
    GroupSearchResult,
    SearchResponse,
    StoreSearchResult,
)
from app.api.schemas.search_schemas import SellerSearchResultBrief
from app.core.models import User
from app.infrastructure.database import get_db
from app.repositories import get_user_repository

router = APIRouter(prefix='/search', tags=['search'])


@router.get('', response_model=SearchResponse)
async def search_all(
    product_service: ProductServiceDep,
    store_service: StoreServiceDep,
    tag_service: TagServiceDep,
    seller_service: SellerServiceDep,
    db: AsyncSession = Depends(get_db),
    q: str = Query(..., min_length=1, description='Search query'),
    current_user: User = Depends(require_auth),
):
    """Consolidated search across products, stores, groups, tags, and sellers.

    Returns up to 3 results per category.
    """
    all_products = await product_service.search_products(q)
    products = all_products[:3]

    all_stores = await store_service.store_repo.search_stores(q)
    stores = [
        StoreSearchResult(id=str(store.id), name=store.name, address=store.address)
        for store in all_stores[:3]
    ]

    user_repo = get_user_repository(db)
    user_groups = await user_repo.get_user_groups(current_user)
    matching_groups = []
    for group in user_groups:
        if q.lower() in group.name.lower():
            member_count = len(group.members)
            matching_groups.append(
                GroupSearchResult(id=str(group.id), name=group.name, member_count=member_count)
            )
            if len(matching_groups) >= 3:
                break

    tags = await tag_service.search_tags(q, limit=3)

    seller_results = await seller_service.search_sellers(q)
    sellers = [
        SellerSearchResultBrief(
            id=s.id,
            store_id=s.store_id,
            display_name=s.display_name,
            description=s.description,
        )
        for s in seller_results[:3]
    ]

    return SearchResponse(
        products=products, stores=stores, groups=matching_groups, tags=tags, sellers=sellers
    )
