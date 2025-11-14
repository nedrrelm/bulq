from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.routes.auth import require_auth
from app.api.schemas import (
    AddMorePurchaseRequest,
    CompleteShoppingResponse,
    MarkPurchasedRequest,
    MarkPurchasedResponse,
    ShoppingListItemResponse,
    SuccessResponse,
    UpdateAvailabilityPriceRequest,
)
from app.api.websocket_manager import manager
from app.core.models import User
from app.infrastructure.database import get_db
from app.infrastructure.request_context import get_logger
from app.services import ShoppingService

router = APIRouter(prefix='/shopping', tags=['shopping'])
logger = get_logger(__name__)


@router.get('/{run_id}/items', response_model=list[ShoppingListItemResponse])
async def get_shopping_list(
    run_id: str, current_user: User = Depends(require_auth), db: Session = Depends(get_db)
):
    """Get shopping list for a run."""
    service = ShoppingService(db)

    return await service.get_shopping_list(run_id, current_user)


@router.post('/{run_id}/items/{item_id}/price', response_model=SuccessResponse)
async def update_availability_price(
    run_id: str,
    item_id: str,
    request: UpdateAvailabilityPriceRequest,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Update product availability price for a shopping list item."""
    service = ShoppingService(db)

    result = await service.add_availability_price(
        run_id, item_id, request.price, request.notes, request.minimum_quantity, current_user
    )

    # Broadcast shopping item update to all connected clients for this run
    await manager.broadcast(
        f'run:{run_id}',
        {
            'type': 'shopping_item_updated',
            'data': {'run_id': run_id, 'item_id': item_id, 'action': 'price_added'},
        },
    )

    return result


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

    result = await service.mark_purchased(
        run_id, item_id, request.quantity, request.price_per_unit, request.total, current_user
    )

    # Broadcast shopping item update to all connected clients for this run
    await manager.broadcast(
        f'run:{run_id}',
        {
            'type': 'shopping_item_updated',
            'data': {'run_id': run_id, 'item_id': item_id, 'action': 'marked_purchased'},
        },
    )

    return result


@router.post('/{run_id}/items/{item_id}/add-more', response_model=SuccessResponse)
async def add_more_purchase(
    run_id: str,
    item_id: str,
    request: AddMorePurchaseRequest,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Add more purchased quantity to an already-purchased item."""
    service = ShoppingService(db)

    result = await service.add_more_purchased(
        run_id, item_id, request.quantity, request.price_per_unit, request.total, current_user
    )

    # Broadcast shopping item update to all connected clients for this run
    await manager.broadcast(
        f'run:{run_id}',
        {
            'type': 'shopping_item_updated',
            'data': {'run_id': run_id, 'item_id': item_id, 'action': 'added_more'},
        },
    )

    return result


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
