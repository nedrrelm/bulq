from fastapi import APIRouter, Depends, Query

from app.api.dependencies import StoreServiceDep
from app.api.routes.auth import require_auth
from app.api.schemas import (
    CreateStoreRequest,
    StorePageResponse,
    StoreResponse,
)
from app.core.models import User
from app.utils.validation import validate_uuid

router = APIRouter(prefix='/stores', tags=['stores'])


@router.get('', response_model=list[StoreResponse])
async def get_stores(
    service: StoreServiceDep,
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_auth),
):
    """Get all available stores (paginated, max 100 per page)."""
    stores = service.get_all_stores(limit, offset)

    return [StoreResponse(id=str(store.id), name=store.name) for store in stores]


@router.get('/check-similar', response_model=list[StoreResponse])
async def check_similar_stores(
    service: StoreServiceDep,
    name: str = Query(..., min_length=1, description='Store name to check for similarity'),
    current_user: User = Depends(require_auth),
):
    """Check for stores with similar names.

    Returns stores that are similar to the provided name, useful for preventing duplicates.
    """
    similar_stores = service.get_similar_stores(name)

    return [StoreResponse(id=str(store.id), name=store.name) for store in similar_stores]


@router.get('/{store_id}', response_model=StorePageResponse)
async def get_store_page(
    store_id: str, service: StoreServiceDep, current_user: User = Depends(require_auth)
):
    """Get store page data including store info, products, and active runs."""
    store_uuid = validate_uuid(store_id, 'Store')
    return service.get_store_page_data(store_uuid, current_user.id)


@router.post('/create', response_model=StoreResponse)
async def create_store(
    request: CreateStoreRequest,
    service: StoreServiceDep,
    current_user: User = Depends(require_auth),
):
    """Create a new store."""
    store = service.create_store(request.name)

    return StoreResponse(id=str(store.id), name=store.name)
