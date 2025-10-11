from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..routes.auth import require_auth
from ..repository import get_repository
from ..services import ShoppingService
from ..exceptions import NotFoundError, ForbiddenError, BadRequestError
from ..request_context import get_logger
from ..schemas import (
    ShoppingListItemResponse,
    UpdateAvailabilityPriceRequest,
    MarkPurchasedRequest,
    MessageResponse,
    MarkPurchasedResponse,
    CompleteShoppingResponse,
)

router = APIRouter(prefix="/shopping", tags=["shopping"])
logger = get_logger(__name__)

@router.get("/{run_id}/items", response_model=list[ShoppingListItemResponse])
async def get_shopping_list(
    run_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get shopping list for a run."""
    repo = get_repository(db)
    service = ShoppingService(repo)

    return await service.get_shopping_list(run_id, current_user)

@router.post("/{run_id}/items/{item_id}/price", response_model=MessageResponse)
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

    return await service.add_availability_price(
        run_id,
        item_id,
        request.price,
        request.notes,
        current_user
    )

@router.post("/{run_id}/items/{item_id}/purchase", response_model=MarkPurchasedResponse)
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

    return await service.mark_purchased(
        run_id,
        item_id,
        request.quantity,
        request.price_per_unit,
        request.total,
        current_user
    )

@router.post("/{run_id}/complete", response_model=CompleteShoppingResponse)
async def complete_shopping(
    run_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Complete shopping - transition from shopping to distributing state (leader only)."""
    logger.info(
        "Completing shopping for run",
        extra={"user_id": str(current_user.id), "run_id": run_id}
    )
    repo = get_repository(db)
    service = ShoppingService(repo)

    return await service.complete_shopping(run_id, current_user, db)
