from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from ..database import get_db
from ..models import User
from ..routes.auth import require_auth
from ..repository import get_repository
from ..services import StoreService
from ..exceptions import NotFoundError
from pydantic import BaseModel

router = APIRouter(prefix="/stores", tags=["stores"])

class StoreResponse(BaseModel):
    id: str
    name: str

    class Config:
        from_attributes = True

class CreateStoreRequest(BaseModel):
    name: str

class ProductResponse(BaseModel):
    id: str
    name: str
    brand: str | None
    unit: str | None
    current_price: str | None

    class Config:
        from_attributes = True

class RunResponse(BaseModel):
    id: str
    state: str
    group_id: str
    group_name: str
    store_name: str
    leader_name: str
    planned_on: str | None

    class Config:
        from_attributes = True

class StorePageResponse(BaseModel):
    store: StoreResponse
    products: list[ProductResponse]
    active_runs: list[RunResponse]

@router.get("", response_model=list[StoreResponse])
async def get_stores(
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get all available stores (paginated, max 100 per page)."""
    repo = get_repository(db)
    service = StoreService(repo)
    stores = service.get_all_stores(limit, offset)

    return [StoreResponse(id=str(store.id), name=store.name) for store in stores]

@router.get("/{store_id}", response_model=StorePageResponse)
async def get_store_page(
    store_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get store page data including store info, products, and active runs."""
    try:
        store_uuid = UUID(store_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid store ID format")

    repo = get_repository(db)
    service = StoreService(repo)

    data = service.get_store_page_data(store_uuid, current_user.id)

    # Service now returns fully formatted data
    return StorePageResponse(
        store=StoreResponse(**data["store"]),
        products=[ProductResponse(**p) for p in data["products"]],
        active_runs=[RunResponse(**r) for r in data["active_runs"]]
    )

@router.post("/create", response_model=StoreResponse)
async def create_store(
    request: CreateStoreRequest,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Create a new store."""
    repo = get_repository(db)
    service = StoreService(repo)
    store = service.create_store(request.name)

    return StoreResponse(id=str(store.id), name=store.name)
