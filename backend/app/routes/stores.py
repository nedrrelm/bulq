from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import User
from ..routes.auth import require_auth
from ..repository import get_repository
from pydantic import BaseModel

router = APIRouter(prefix="/stores", tags=["stores"])

class StoreResponse(BaseModel):
    id: str
    name: str

    class Config:
        from_attributes = True

@router.get("", response_model=List[StoreResponse])
async def get_stores(
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get all available stores."""
    repo = get_repository(db)
    stores = repo.get_all_stores()

    return [StoreResponse(id=str(store.id), name=store.name) for store in stores]
