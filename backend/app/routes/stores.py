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
    products: List[ProductResponse]
    active_runs: List[RunResponse]

@router.get("", response_model=List[StoreResponse])
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

    try:
        data = service.get_store_page_data(store_uuid, current_user.id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Convert to response format
    store_response = StoreResponse(id=str(data["store"].id), name=data["store"].name)

    products_response = []
    for p in data["products"]:
        # Get price from product availability
        availability = repo.get_availability_by_product_and_store(p.id, UUID(store_id))
        current_price = str(availability.price) if availability and availability.price else None

        products_response.append(ProductResponse(
            id=str(p.id),
            name=p.name,
            brand=p.brand,
            unit=p.unit,
            current_price=current_price
        ))

    runs_response = []
    for r in data["active_runs"]:
        group = repo.get_group_by_id(r.group_id)
        store = repo.get_store_by_id(r.store_id)
        # Get leader from participations
        participations = repo.get_run_participations(r.id)
        leader = next((p for p in participations if p.is_leader), None)
        leader_name = leader.user.name if leader and leader.user else "Unknown"

        runs_response.append(RunResponse(
            id=str(r.id),
            state=r.state,
            group_id=str(r.group_id),
            group_name=group.name if group else "Unknown",
            store_name=store.name if store else "Unknown",
            leader_name=leader_name,
            planned_on=r.planned_on.isoformat() if r.planned_on else None
        ))

    return StorePageResponse(
        store=store_response,
        products=products_response,
        active_runs=runs_response
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
