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

class EncounteredPriceResponse(BaseModel):
    price: float
    notes: str
    minimum_quantity: int | None
    encountered_at: str

class ShoppingListItemResponse(BaseModel):
    id: str
    product_id: str
    product_name: str
    requested_quantity: int
    encountered_prices: List[EncounteredPriceResponse]
    purchased_quantity: int | None
    purchased_price_per_unit: str | None
    purchased_total: str | None
    is_purchased: bool
    purchase_order: int | None

    class Config:
        from_attributes = True

class AddEncounteredPriceRequest(BaseModel):
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

    try:
        items = await service.get_shopping_list(run_id, current_user)
        return [ShoppingListItemResponse(**item) for item in items]
    except BadRequestError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=str(e))

@router.post("/{run_id}/items/{item_id}/encountered-price")
async def add_encountered_price(
    run_id: str,
    item_id: str,
    request: AddEncounteredPriceRequest,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Add an encountered price for a shopping list item."""
    repo = get_repository(db)
    service = ShoppingService(repo)

    try:
        result = await service.add_encountered_price(
            run_id,
            item_id,
            request.price,
            request.notes,
            current_user
        )
        return result
    except BadRequestError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=str(e))

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

    try:
        result = await service.mark_purchased(
            run_id,
            item_id,
            request.quantity,
            request.price_per_unit,
            request.total,
            current_user
        )
        return result
    except BadRequestError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=str(e))

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

    try:
        result = await service.complete_shopping(run_id, current_user, db)
        return result
    except BadRequestError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=str(e))
