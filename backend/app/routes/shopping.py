from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..request_context import get_logger
from ..routes.auth import require_auth
from ..schemas import (
    CompleteShoppingResponse,
    MarkPurchasedRequest,
    MarkPurchasedResponse,
    MessageResponse,
    ShoppingListItemResponse,
    UpdateAvailabilityPriceRequest,
)
from ..services import ShoppingService

router = APIRouter(prefix='/shopping', tags=['shopping'])
logger = get_logger(__name__)


@router.get('/{run_id}/items', response_model=list[ShoppingListItemResponse])
async def get_shopping_list(
    run_id: str, current_user: User = Depends(require_auth), db: Session = Depends(get_db)
):
    """Get shopping list for a run."""
    service = ShoppingService(db)

    return await service.get_shopping_list(run_id, current_user)


@router.post('/{run_id}/items/{item_id}/price', response_model=MessageResponse)
async def update_availability_price(
    run_id: str,
    item_id: str,
    request: UpdateAvailabilityPriceRequest,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Update product availability price for a shopping list item."""
    service = ShoppingService(db)

    return await service.add_availability_price(
        run_id, item_id, request.price, request.notes, current_user
    )


@router.post('/{run_id}/items/{item_id}/purchase', response_model=MarkPurchasedResponse)
async def mark_purchased(
    run_id: str,
    item_id: str,
    request: MarkPurchasedRequest,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Mark a shopping list item as purchased."""
    service = ShoppingService(db)

    return await service.mark_purchased(
        run_id, item_id, request.quantity, request.price_per_unit, request.total, current_user
    )


@router.post('/{run_id}/complete', response_model=CompleteShoppingResponse)
async def complete_shopping(
    run_id: str, current_user: User = Depends(require_auth), db: Session = Depends(get_db)
):
    """Complete shopping - transition from shopping to distributing state (leader only)."""
    logger.info(
        'Completing shopping for run', extra={'user_id': str(current_user.id), 'run_id': run_id}
    )
    service = ShoppingService(db)

    return await service.complete_shopping(run_id, current_user, db)
