from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.auth import require_auth
from app.api.schemas import (
    CreateStoreRequest,
    StorePageResponse,
    StoreResponse,
)
from app.core.error_codes import INVALID_ID_FORMAT
from app.core.exceptions import BadRequestError
from app.core.models import User
from app.infrastructure.database import get_db
from app.services import StoreService

router = APIRouter(prefix='/stores', tags=['stores'])


@router.get('', response_model=list[StoreResponse])
async def get_stores(
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """Get all available stores (paginated, max 100 per page)."""
    service = StoreService(db)
    stores = await service.get_all_stores(limit, offset)

    return [StoreResponse(id=str(store.id), name=store.name) for store in stores]


@router.get('/check-similar', response_model=list[StoreResponse])
async def check_similar_stores(
    name: str = Query(..., min_length=1, description='Store name to check for similarity'),
    current_user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """Check for stores with similar names.

    Returns stores that are similar to the provided name, useful for preventing duplicates.
    """
    service = StoreService(db)
    similar_stores = await service.get_similar_stores(name)

    return [StoreResponse(id=str(store.id), name=store.name) for store in similar_stores]


@router.get('/{store_id}', response_model=StorePageResponse)
async def get_store_page(
    store_id: str, current_user: User = Depends(require_auth), db:  AsyncSession = Depends(get_db)
):
    """Get store page data including store info, products, and active runs."""
    try:
        store_uuid = UUID(store_id)
    except ValueError as e:
        raise BadRequestError(code=INVALID_ID_FORMAT, message='Invalid ID format') from e

    service = StoreService(db)
    return await service.get_store_page_data(store_uuid, current_user.id)


@router.post('/create', response_model=StoreResponse)
async def create_store(
    request: CreateStoreRequest,
    current_user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """Create a new store."""
    service = StoreService(db)
    store = await service.create_store(request.name)

    return StoreResponse(id=str(store.id), name=store.name)
