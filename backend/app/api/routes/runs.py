from fastapi import APIRouter, Depends

from app.api.dependencies import RunServiceDep
from app.api.routes.auth import require_auth
from app.api.schemas import (
    AvailableProductResponse,
    CancelRunResponse,
    CreateRunRequest,
    CreateRunResponse,
    PlaceBidRequest,
    PlaceBidResponse,
    ReadyToggleResponse,
    RetractBidResponse,
    RunDetailResponse,
    StateChangeResponse,
    SuccessResponse,
    UpdateLeaderFeeRequest,
    UpdateRunCommentRequest,
)
from app.api.websocket_manager import manager
from app.core.models import User
from app.infrastructure.request_context import get_logger

router = APIRouter(prefix='/runs', tags=['runs'])
logger = get_logger(__name__)


@router.post('/create', response_model=CreateRunResponse)
async def create_run(
    request: CreateRunRequest,
    service: RunServiceDep,
    current_user: User = Depends(require_auth),
):
    """Create a new run for a group."""
    return service.create_run(
        request.group_id,
        request.store_id,
        current_user,
        request.comment,
        float(request.leader_fee) if request.leader_fee is not None else None,
    )


@router.get('/{run_id}', response_model=RunDetailResponse)
async def get_run_details(
    run_id: str, service: RunServiceDep, current_user: User = Depends(require_auth)
):
    """Get detailed information about a specific run."""
    return service.get_run_details(run_id, current_user)


@router.post('/{run_id}/bids', response_model=PlaceBidResponse)
async def place_bid(
    run_id: str,
    bid_request: PlaceBidRequest,
    service: RunServiceDep,
    current_user: User = Depends(require_auth),
):
    """Place or update a bid on a product in a run."""
    result = service.place_bid(
        run_id,
        bid_request.product_id,
        bid_request.quantity,
        bid_request.interested_only,
        current_user,
        bid_request.comment,
    )
    return result


@router.delete('/{run_id}/bids/{product_id}', response_model=RetractBidResponse)
async def retract_bid(
    run_id: str,
    product_id: str,
    service: RunServiceDep,
    current_user: User = Depends(require_auth),
):
    """Retract a bid on a product in a run."""
    return service.retract_bid(run_id, product_id, current_user)


@router.post('/{run_id}/ready', response_model=ReadyToggleResponse)
async def toggle_ready(
    run_id: str, service: RunServiceDep, current_user: User = Depends(require_auth)
):
    """Toggle the current user's ready status for a run."""
    return service.toggle_ready(run_id, current_user)


@router.post('/{run_id}/force-confirm', response_model=StateChangeResponse)
async def force_confirm(
    run_id: str, service: RunServiceDep, current_user: User = Depends(require_auth)
):
    """Force confirm run - transition from active to confirmed state without waiting for all users (leader only)."""
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
    run_id: str, service: RunServiceDep, current_user: User = Depends(require_auth)
):
    """Start shopping - transition from confirmed to shopping state (leader only)."""
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
    service: RunServiceDep,
    force: bool = False,
    current_user: User = Depends(require_auth),
):
    """Finish adjusting bids - transition from adjusting to distributing state (leader only).

    Query params:
        force: If true, skip quantity verification and proceed anyway
    """
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
    service: RunServiceDep,
    current_user: User = Depends(require_auth),
):
    """Toggle helper status for a run participant (leader only)."""
    result = service.toggle_helper(run_id, user_id, current_user)
    return result


@router.get('/{run_id}/available-products', response_model=list[AvailableProductResponse])
async def get_available_products(
    run_id: str, service: RunServiceDep, current_user: User = Depends(require_auth)
):
    """Get products available for bidding (products from the store that don't have bids yet)."""
    return service.get_available_products(run_id, current_user)


@router.post('/{run_id}/transition-shopping', response_model=StateChangeResponse)
async def transition_to_shopping(
    run_id: str, service: RunServiceDep, current_user: User = Depends(require_auth)
):
    """Transition to shopping state (alias for start-shopping)."""
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
    run_id: str, service: RunServiceDep, current_user: User = Depends(require_auth)
):
    """Cancel a run. Leader only. Can be done from any state except completed/cancelled."""
    # Set WebSocket manager for broadcasting (state service handles state change notifications)
    service.notification_service.set_websocket_manager(manager)

    result = service.cancel_run(run_id, current_user)

    # No additional broadcast needed - state service handles notifications

    return result


@router.patch('/{run_id}/comment', response_model=SuccessResponse)
async def update_run_comment(
    run_id: str,
    request: UpdateRunCommentRequest,
    service: RunServiceDep,
    current_user: User = Depends(require_auth),
):
    """Update the comment/description for a run (leader only)."""
    result = service.update_run_comment(run_id, request.comment, current_user)
    return result


@router.patch('/{run_id}/fee', response_model=SuccessResponse)
async def update_leader_fee(
    run_id: str,
    request: UpdateLeaderFeeRequest,
    service: RunServiceDep,
    current_user: User = Depends(require_auth),
):
    """Update the leader fee for a run (leader only, planning state only)."""
    return service.update_leader_fee(
        run_id,
        float(request.leader_fee) if request.leader_fee is not None else None,
        current_user,
    )


@router.get('/{run_id}/export')
async def export_run_state(
    run_id: str, service: RunServiceDep, current_user: User = Depends(require_auth)
):
    """Export current state of run as JSON (leader and helpers only).

    Available for runs in confirmed, shopping, adjusting, or distributing states.
    Returns structured JSON with per-product and per-user breakdowns.
    """
    return service.export_run_state(run_id, current_user)
