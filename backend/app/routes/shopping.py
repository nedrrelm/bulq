from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import User
from ..routes.auth import require_auth
from ..repository import get_repository
from ..services import ShoppingService
from ..exceptions import NotFoundError, ForbiddenError, BadRequestError
from pydantic import BaseModel, validator, Field
import logging

router = APIRouter(prefix="/shopping", tags=["shopping"])
logger = logging.getLogger(__name__)

class PriceObservation(BaseModel):
    price: float
    notes: str
    created_at: str | None

class ShoppingListItemResponse(BaseModel):
    id: str
    product_id: str
    product_name: str
    requested_quantity: int
    recent_prices: List[PriceObservation]
    purchased_quantity: int | None
    purchased_price_per_unit: str | None
    purchased_total: str | None
    is_purchased: bool
    purchase_order: int | None

    class Config:
        from_attributes = True

class UpdateAvailabilityPriceRequest(BaseModel):
    price: float = Field(gt=0, le=99999.99)
    notes: str = Field(default="", max_length=200)

    @validator('price')
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError('Price must be greater than 0')
        # Check max 2 decimal places
        if round(v, 2) != v:
            raise ValueError('Price can have at most 2 decimal places')
        return v

    @validator('notes')
    def validate_notes(cls, v):
        return v.strip()[:200]

class MarkPurchasedRequest(BaseModel):
    quantity: float = Field(gt=0, le=9999)
    price_per_unit: float = Field(gt=0, le=99999.99)
    total: float = Field(gt=0, le=999999.99)

    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be greater than 0')
        # Check max 2 decimal places
        if round(v, 2) != v:
            raise ValueError('Quantity can have at most 2 decimal places')
        return v

    @validator('price_per_unit')
    def validate_price_per_unit(cls, v):
        if v <= 0:
            raise ValueError('Price per unit must be greater than 0')
        # Check max 2 decimal places
        if round(v, 2) != v:
            raise ValueError('Price per unit can have at most 2 decimal places')
        return v

    @validator('total')
    def validate_total(cls, v):
        if v <= 0:
            raise ValueError('Total must be greater than 0')
        # Check max 2 decimal places
        if round(v, 2) != v:
            raise ValueError('Total can have at most 2 decimal places')
        return v

@router.get("/{run_id}/items", response_model=List[ShoppingListItemResponse])
async def get_shopping_list(
    run_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get shopping list for a run."""
    repo = get_repository(db)
    service = ShoppingService(repo)

    items = await service.get_shopping_list(run_id, current_user)
    return [ShoppingListItemResponse(**item) for item in items]

@router.post("/{run_id}/items/{item_id}/price")
async def update_availability_price(
    run_id: str,
    item_id: str,
    request: UpdateAvailabilityPriceRequest,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Update product availability price for a shopping list item."""
    repo = get_repository(db)
    service = ShoppingService(repo)

    result = await service.add_availability_price(
        run_id,
        item_id,
        request.price,
        request.notes,
        current_user
    )
    return result

@router.post("/{run_id}/items/{item_id}/purchase")
async def mark_purchased(
    run_id: str,
    item_id: str,
    request: MarkPurchasedRequest,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Mark a shopping list item as purchased."""
    repo = get_repository(db)
    service = ShoppingService(repo)

    result = await service.mark_purchased(
        run_id,
        item_id,
        request.quantity,
        request.price_per_unit,
        request.total,
        current_user
    )
    return result

@router.post("/{run_id}/complete")
async def complete_shopping(
    run_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Complete shopping - transition from shopping to distributing state (leader only)."""
    logger.info(
        f"Completing shopping for run",
        extra={"user_id": str(current_user.id), "run_id": run_id}
    )
    repo = get_repository(db)
    service = ShoppingService(repo)

    result = await service.complete_shopping(run_id, current_user, db)
    return result
