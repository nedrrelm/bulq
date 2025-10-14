from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db
from app.core.models import User
from app.api.routes.auth import require_auth
from app.api.schemas import (
    CreateStoreRequest,
    StorePageResponse,
    StoreProductResponse,
    StoreResponse,
    StoreRunResponse,
)
from app.services import StoreService

router = APIRouter(prefix='/stores', tags=['stores'])


@router.get('', response_model=list[StoreResponse])
async def get_stores(
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Get all available stores (paginated, max 100 per page)."""
    service = StoreService(db)
    stores = service.get_all_stores(limit, offset)

    return [StoreResponse(id=str(store.id), name=store.name) for store in stores]


@router.get('/{store_id}', response_model=StorePageResponse)
async def get_store_page(
    store_id: str, current_user: User = Depends(require_auth), db: Session = Depends(get_db)
):
    """Get store page data including store info, products, and active runs."""
    try:
        store_uuid = UUID(store_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail='Invalid store ID format') from e

    service = StoreService(db)
    return service.get_store_page_data(store_uuid, current_user.id)


@router.post('/create', response_model=StoreResponse)
async def create_store(
    request: CreateStoreRequest,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Create a new store."""
    service = StoreService(db)
    store = service.create_store(request.name)

    return StoreResponse(id=str(store.id), name=store.name)
