from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..request_context import get_logger
from ..routes.auth import require_auth
from ..schemas import (
    AvailableProductResponse,
    CancelRunResponse,
    CreateRunRequest,
    CreateRunResponse,
    MessageResponse,
    PlaceBidRequest,
    ReadyToggleResponse,
    RunDetailResponse,
    StateChangeResponse,
)
from ..services import RunService
from ..websocket_manager import manager

router = APIRouter(prefix='/runs', tags=['runs'])
logger = get_logger(__name__)


@router.post('/create', response_model=CreateRunResponse)
async def create_run(
    request: CreateRunRequest,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Create a new run for a group."""
    service = RunService(db)
    # Set WebSocket manager for broadcasting
    service.notification_service.set_websocket_manager(manager)

    result = service.create_run(request.group_id, request.store_id, current_user)

    # Broadcast to group room using notification service
    await service.notification_service.broadcast_run_created(
        result.group_id,
        result.id,
        result.store_id,
        result.store_name,
        result.state,
        result.leader_name,
    )

    return result


@router.get('/{run_id}', response_model=RunDetailResponse)
async def get_run_details(
    run_id: str, current_user: User = Depends(require_auth), db: Session = Depends(get_db)
):
    """Get detailed information about a specific run."""
    service = RunService(db)

    return service.get_run_details(run_id, current_user)


@router.post('/{run_id}/bids', response_model=MessageResponse)
async def place_bid(
    run_id: str,
    bid_request: PlaceBidRequest,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Place or update a bid on a product in a run."""
    service = RunService(db)
    # Set WebSocket manager for broadcasting
    service.notification_service.set_websocket_manager(manager)

    result = service.place_bid(
        run_id,
        bid_request.product_id,
        bid_request.quantity,
        bid_request.interested_only,
        current_user,
    )

    # Broadcast bid update using notification service
    await service.notification_service.broadcast_bid_update(
        result.run_id,
        result.product_id,
        result.user_id,
        result.user_name,
        result.quantity,
        result.interested_only,
        result.new_total,
    )

    # If state changed, broadcast state change
    if result.state_changed:
        await service.notification_service.broadcast_state_change(
            result.run_id, result.group_id, result.new_state
        )

    return MessageResponse(message=result.message)


@router.delete('/{run_id}/bids/{product_id}', response_model=MessageResponse)
async def retract_bid(
    run_id: str,
    product_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Retract a bid on a product in a run."""
    service = RunService(db)
    # Set WebSocket manager for broadcasting
    service.notification_service.set_websocket_manager(manager)

    result = service.retract_bid(run_id, product_id, current_user)

    # Broadcast retraction using notification service
    await service.notification_service.broadcast_bid_retraction(
        result.run_id, result.product_id, result.user_id, result.new_total
    )

    return MessageResponse(message=result.message)


@router.post('/{run_id}/ready', response_model=ReadyToggleResponse)
async def toggle_ready(
    run_id: str, current_user: User = Depends(require_auth), db: Session = Depends(get_db)
):
    """Toggle the current user's ready status for a run."""
    service = RunService(db)
    # Set WebSocket manager for broadcasting
    service.notification_service.set_websocket_manager(manager)

    result = service.toggle_ready(run_id, current_user)

    # Broadcast ready toggle using notification service
    await service.notification_service.broadcast_ready_toggle(
        result.run_id, result.user_id, result.is_ready
    )

    # If state changed, broadcast state change
    if result.state_changed:
        await service.notification_service.broadcast_state_change(
            result.run_id, result.group_id, result.new_state
        )

    return result


@router.post('/{run_id}/start-shopping', response_model=StateChangeResponse)
async def start_shopping(
    run_id: str, current_user: User = Depends(require_auth), db: Session = Depends(get_db)
):
    """Start shopping - transition from confirmed to shopping state (leader only)."""
    service = RunService(db)
    # Set WebSocket manager for broadcasting
    service.notification_service.set_websocket_manager(manager)

    result = service.start_run(run_id, current_user)

    # Broadcast state change using notification service
    await service.notification_service.broadcast_state_change(
        result.run_id, result.group_id, result.state
    )

    return result


@router.post('/{run_id}/finish-adjusting', response_model=StateChangeResponse)
async def finish_adjusting(
    run_id: str, current_user: User = Depends(require_auth), db: Session = Depends(get_db)
):
    """Finish adjusting bids - transition from adjusting to distributing state (leader only)."""
    service = RunService(db)
    # Set WebSocket manager for broadcasting
    service.notification_service.set_websocket_manager(manager)

    result = service.finish_adjusting(run_id, current_user)

    # Broadcast state change using notification service
    await service.notification_service.broadcast_state_change(
        result.run_id, result.group_id, result.state
    )

    return result


@router.get('/{run_id}/available-products', response_model=list[AvailableProductResponse])
async def get_available_products(
    run_id: str, current_user: User = Depends(require_auth), db: Session = Depends(get_db)
):
    """Get products available for bidding (products from the store that don't have bids yet)."""
    service = RunService(db)

    return service.get_available_products(run_id, current_user)


@router.post('/{run_id}/transition-shopping', response_model=StateChangeResponse)
async def transition_to_shopping(
    run_id: str, current_user: User = Depends(require_auth), db: Session = Depends(get_db)
):
    """Transition to shopping state (alias for start-shopping)."""
    service = RunService(db)
    # Set WebSocket manager for broadcasting
    service.notification_service.set_websocket_manager(manager)

    result = service.transition_to_shopping(run_id, current_user)

    # Broadcast state change using notification service
    await service.notification_service.broadcast_state_change(
        result.run_id, result.group_id, result.state
    )

    return result


@router.post('/{run_id}/cancel', response_model=CancelRunResponse)
async def cancel_run(
    run_id: str, current_user: User = Depends(require_auth), db: Session = Depends(get_db)
):
    """Cancel a run. Leader only. Can be done from any state except completed/cancelled."""
    service = RunService(db)
    # Set WebSocket manager for broadcasting (state service handles state change notifications)
    service.notification_service.set_websocket_manager(manager)

    result = service.cancel_run(run_id, current_user)

    # No additional broadcast needed - state service handles notifications

    return result


@router.delete('/{run_id}', response_model=MessageResponse)
async def delete_run(
    run_id: str, current_user: User = Depends(require_auth), db: Session = Depends(get_db)
):
    """Delete a run (cancels it). Alias for cancel_run for backward compatibility."""
    service = RunService(db)
    # Set WebSocket manager for broadcasting (state service handles state change notifications)
    service.notification_service.set_websocket_manager(manager)

    result = service.delete_run(run_id, current_user)

    # No additional broadcast needed - state service handles notifications

    return MessageResponse(message=result.message)
