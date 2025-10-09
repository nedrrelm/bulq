from fastapi import APIRouter, Depends, HTTPException
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
    base_price: str | None

    class Config:
        from_attributes = True

class RunResponse(BaseModel):
    id: str
    state: str
    group_id: str
    group_name: str

    class Config:
        from_attributes = True

class StorePageResponse(BaseModel):
    store: StoreResponse
    products: List[ProductResponse]
    active_runs: List[RunResponse]

@router.get("", response_model=List[StoreResponse])
async def get_stores(
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get all available stores."""
    repo = get_repository(db)
    service = StoreService(repo)
    stores = service.get_all_stores()

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

    products_response = [
        ProductResponse(
            id=str(p.id),
            name=p.name,
            brand=p.brand,
            unit=p.unit,
            base_price=str(p.base_price) if p.base_price else None
        )
        for p in data["products"]
    ]

    runs_response = [
        RunResponse(
            id=str(r.id),
            state=r.state,
            group_id=str(r.group_id),
            group_name=repo.get_group_by_id(r.group_id).name
        )
        for r in data["active_runs"]
    ]

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
