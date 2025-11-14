from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.routes.auth import require_auth
from app.api.schemas import (
    AvailableProductResponse,
    CancelRunResponse,
    CreateRunRequest,
    CreateRunResponse,
    MessageResponse,
    PlaceBidRequest,
    PlaceBidResponse,
    ReadyToggleResponse,
    RunDetailResponse,
    StateChangeResponse,
    SuccessResponse,
    UpdateRunCommentRequest,
)
from app.api.websocket_manager import manager
from app.core.models import User
from app.infrastructure.database import get_db
from app.infrastructure.request_context import get_logger
from app.services import RunService

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
    return service.create_run(request.group_id, request.store_id, current_user, request.comment)


@router.get('/{run_id}', response_model=RunDetailResponse)
async def get_run_details(
    run_id: str, current_user: User = Depends(require_auth), db: Session = Depends(get_db)
):
    """Get detailed information about a specific run."""
    service = RunService(db)

    return service.get_run_details(run_id, current_user)


@router.post('/{run_id}/bids', response_model=PlaceBidResponse)
async def place_bid(
    run_id: str,
    bid_request: PlaceBidRequest,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Place or update a bid on a product in a run."""
    service = RunService(db)
    result = service.place_bid(
        run_id,
        bid_request.product_id,
        bid_request.quantity,
        bid_request.interested_only,
        current_user,
        bid_request.comment,
    )
    return result


@router.delete('/{run_id}/bids/{product_id}', response_model=SuccessResponse)
async def retract_bid(
    run_id: str,
    product_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Retract a bid on a product in a run."""
    service = RunService(db)
    result = service.retract_bid(run_id, product_id, current_user)
    return MessageResponse(message=result.message)


@router.post('/{run_id}/ready', response_model=ReadyToggleResponse)
async def toggle_ready(
    run_id: str, current_user: User = Depends(require_auth), db: Session = Depends(get_db)
):
    """Toggle the current user's ready status for a run."""
    service = RunService(db)
    return service.toggle_ready(run_id, current_user)


@router.post('/{run_id}/force-confirm', response_model=StateChangeResponse)
async def force_confirm(
    run_id: str, current_user: User = Depends(require_auth), db: Session = Depends(get_db)
):
    """Force confirm run - transition from active to confirmed state without waiting for all users (leader only)."""
    service = RunService(db)
    # Set WebSocket manager for broadcasting
    service.notification_service.set_websocket_manager(manager)

    result = service.force_confirm_run(run_id, current_user)

    # Broadcast state change using notification service
    await service.notification_service.broadcast_state_change(
        result.run_id, result.group_id, result.state
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
    run_id: str,
    force: bool = False,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Finish adjusting bids - transition from adjusting to distributing state (leader only).

    Query params:
        force: If true, skip quantity verification and proceed anyway
    """
    service = RunService(db)
    # Set WebSocket manager for broadcasting
    service.notification_service.set_websocket_manager(manager)

    result = service.finish_adjusting(run_id, current_user, force)

    # Broadcast state change using notification service
    await service.notification_service.broadcast_state_change(
        result.run_id, result.group_id, result.state
    )

    return result


@router.post('/{run_id}/helpers/{user_id}', response_model=SuccessResponse)
async def toggle_helper(
    run_id: str,
    user_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Toggle helper status for a run participant (leader only)."""
    service = RunService(db)
    result = service.toggle_helper(run_id, user_id, current_user)

    # Broadcast helper status change to all participants
    await manager.broadcast(
        f'run:{run_id}', {'type': 'helper_toggled', 'data': {'run_id': run_id, 'user_id': user_id}}
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


@router.patch('/{run_id}/comment', response_model=SuccessResponse)
async def update_run_comment(
    run_id: str,
    request: UpdateRunCommentRequest,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Update the comment/description for a run (leader only)."""
    service = RunService(db)
    result = service.update_run_comment(run_id, request.comment, current_user)

    # Broadcast comment update to all participants
    await manager.broadcast(
        f'run:{run_id}',
        {'type': 'comment_updated', 'data': {'run_id': run_id, 'comment': request.comment}},
    )

    return result


@router.delete('/{run_id}', response_model=SuccessResponse)
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


@router.get('/{run_id}/export')
async def export_run_state(
    run_id: str, current_user: User = Depends(require_auth), db: Session = Depends(get_db)
):
    """Export current state of run as JSON (leader and helpers only).

    Available for runs in confirmed, shopping, adjusting, or distributing states.
    Returns structured JSON with per-product and per-user breakdowns.
    """
    service = RunService(db)
    return service.export_run_state(run_id, current_user)
