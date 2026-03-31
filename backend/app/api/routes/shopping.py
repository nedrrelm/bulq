from fastapi import APIRouter, Depends

from app.api.dependencies import ShoppingServiceDep
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
from app.infrastructure.request_context import get_logger

router = APIRouter(prefix='/shopping', tags=['shopping'])
logger = get_logger(__name__)


@router.get('/{run_id}/items', response_model=list[ShoppingListItemResponse])
async def get_shopping_list(
    run_id: str, service: ShoppingServiceDep, current_user: User = Depends(require_auth)
):
    """Get shopping list for a run."""
    return await service.get_shopping_list(run_id, current_user)


@router.post('/{run_id}/items/{product_id}', response_model=SuccessResponse)
async def add_product_to_shopping_list(
    run_id: str,
    product_id: str,
    service: ShoppingServiceDep,
    quantity: float = 1.0,
    current_user: User = Depends(require_auth),
):
    """Add a product to the shopping list (shopping state only, leader/helper only)."""
    result = await service.add_product_to_shopping_list(run_id, product_id, quantity, current_user)

    # Broadcast shopping list update to all connected clients for this run
    await manager.broadcast(
        f'run:{run_id}',
        {
            'type': 'shopping_item_updated',
            'data': {'run_id': run_id, 'action': 'product_added'},
        },
    )

    return result


@router.post('/{run_id}/items/{item_id}/price', response_model=SuccessResponse)
async def update_availability_price(
    run_id: str,
    item_id: str,
    request: UpdateAvailabilityPriceRequest,
    service: ShoppingServiceDep,
    current_user: User = Depends(require_auth),
):
    """Update product availability price for a shopping list item."""
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
    service: ShoppingServiceDep,
    current_user: User = Depends(require_auth),
):
    """Mark a shopping list item as purchased."""
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
    service: ShoppingServiceDep,
    current_user: User = Depends(require_auth),
):
    """Add more purchased quantity to an already-purchased item."""
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


@router.put('/{run_id}/items/{item_id}/purchase', response_model=SuccessResponse)
async def update_purchase(
    run_id: str,
    item_id: str,
    request: MarkPurchasedRequest,
    service: ShoppingServiceDep,
    current_user: User = Depends(require_auth),
):
    """Update an existing purchase (replaces values, doesn't accumulate)."""
    result = await service.update_purchase(
        run_id, item_id, request.quantity, request.price_per_unit, request.total, current_user
    )

    # Broadcast shopping item update to all connected clients for this run
    await manager.broadcast(
        f'run:{run_id}',
        {
            'type': 'shopping_item_updated',
            'data': {'run_id': run_id, 'item_id': item_id, 'action': 'purchase_updated'},
        },
    )

    return result


@router.delete('/{run_id}/items/{item_id}/purchase', response_model=SuccessResponse)
async def unpurchase_item(
    run_id: str,
    item_id: str,
    service: ShoppingServiceDep,
    current_user: User = Depends(require_auth),
):
    """Reset an item to unpurchased state."""
    result = await service.unpurchase_item(run_id, item_id, current_user)

    # Broadcast shopping item update to all connected clients for this run
    await manager.broadcast(
        f'run:{run_id}',
        {
            'type': 'shopping_item_updated',
            'data': {'run_id': run_id, 'item_id': item_id, 'action': 'unpurchased'},
        },
    )

    return result


@router.post('/{run_id}/complete', response_model=CompleteShoppingResponse)
async def complete_shopping(
    run_id: str, service: ShoppingServiceDep, current_user: User = Depends(require_auth)
):
    """Complete shopping - transition from shopping to distributing state (leader only)."""
    logger.info(
        'Completing shopping for run', extra={'user_id': str(current_user.id), 'run_id': run_id}
    )
    return await service.complete_shopping(run_id, current_user, service.db)
