from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import User
from ..routes.auth import require_auth
from ..repository import get_repository
from ..services import StoreService
from pydantic import BaseModel

router = APIRouter(prefix="/stores", tags=["stores"])

class StoreResponse(BaseModel):
    id: str
    name: str

    class Config:
        from_attributes = True

class CreateStoreRequest(BaseModel):
    name: str

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
