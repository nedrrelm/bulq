from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Run, Store, Group, User, Product, ProductBid, RunParticipation
from ..routes.auth import require_auth
from ..repository import get_repository
from ..services import RunService
from ..websocket_manager import manager
from ..run_state import RunState
from ..request_context import get_logger
from ..schemas import (
    CreateRunRequest,
    CreateRunResponse,
    PlaceBidRequest,
    RunDetailResponse,
    MessageResponse,
    StateChangeResponse,
    ReadyToggleResponse,
    CancelRunResponse,
    AvailableProductResponse,
)

router = APIRouter(prefix="/runs", tags=["runs"])
logger = get_logger(__name__)

@router.post("/create", response_model=CreateRunResponse)
async def create_run(
    request: CreateRunRequest,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Create a new run for a group."""
    repo = get_repository(db)
    service = RunService(repo)

    result = service.create_run(request.group_id, request.store_id, current_user)

    # Broadcast to group room
    await manager.broadcast(f"group:{result.group_id}", {
        "type": "run_created",
        "data": {
            "run_id": result.id,
            "store_id": result.store_id,
            "store_name": result.store_name,
            "state": result.state,
            "leader_name": result.leader_name
        }
    })

    return result

@router.get("/{run_id}", response_model=RunDetailResponse)
async def get_run_details(
    run_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific run."""
    repo = get_repository(db)
    service = RunService(repo)

    return service.get_run_details(run_id, current_user)

@router.post("/{run_id}/bids", response_model=MessageResponse)
async def place_bid(
    run_id: str,
    bid_request: PlaceBidRequest,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Place or update a bid on a product in a run."""
    repo = get_repository(db)
    service = RunService(repo)

    result = service.place_bid(
        run_id,
        bid_request.product_id,
        bid_request.quantity,
        bid_request.interested_only,
        current_user
    )

    # Broadcast to run room
    await manager.broadcast(f"run:{result.run_id}", {
        "type": "bid_updated",
        "data": {
            "product_id": result.product_id,
            "user_id": result.user_id,
            "user_name": result.user_name,
            "quantity": result.quantity,
            "interested_only": result.interested_only,
            "new_total": result.new_total
        }
    })

    # If state changed, broadcast to both run and group
    if result.state_changed:
        await manager.broadcast(f"run:{result.run_id}", {
            "type": "state_changed",
            "data": {
                "run_id": result.run_id,
                "new_state": result.new_state
            }
        })
        await manager.broadcast(f"group:{result.group_id}", {
            "type": "run_state_changed",
            "data": {
                "run_id": result.run_id,
                "new_state": result.new_state
            }
        })

    return MessageResponse(message=result.message)

@router.delete("/{run_id}/bids/{product_id}", response_model=MessageResponse)
async def retract_bid(
    run_id: str,
    product_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Retract a bid on a product in a run."""
    repo = get_repository(db)
    service = RunService(repo)

    result = service.retract_bid(run_id, product_id, current_user)

    # Broadcast to run room
    await manager.broadcast(f"run:{result.run_id}", {
        "type": "bid_retracted",
        "data": {
            "product_id": result.product_id,
            "user_id": result.user_id,
            "new_total": result.new_total
        }
    })

    return MessageResponse(message=result.message)

@router.post("/{run_id}/ready", response_model=ReadyToggleResponse)
async def toggle_ready(
    run_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Toggle the current user's ready status for a run."""
    repo = get_repository(db)
    service = RunService(repo)

    result = service.toggle_ready(run_id, current_user)

    # Broadcast ready toggle to run room
    await manager.broadcast(f"run:{result.run_id}", {
        "type": "ready_toggled",
        "data": {
            "user_id": result.user_id,
            "is_ready": result.is_ready
        }
    })

    # If state changed, broadcast state change to both run and group
    if result.state_changed:
        await manager.broadcast(f"run:{result.run_id}", {
            "type": "state_changed",
            "data": {
                "run_id": result.run_id,
                "new_state": result.new_state
            }
        })
        await manager.broadcast(f"group:{result.group_id}", {
            "type": "run_state_changed",
            "data": {
                "run_id": result.run_id,
                "new_state": result.new_state
            }
        })

    return result

@router.post("/{run_id}/start-shopping", response_model=StateChangeResponse)
async def start_shopping(
    run_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Start shopping - transition from confirmed to shopping state (leader only)."""
    repo = get_repository(db)
    service = RunService(repo)

    result = service.start_run(run_id, current_user)

    # Broadcast state change to both run and group
    await manager.broadcast(f"run:{result.run_id}", {
        "type": "state_changed",
        "data": {
            "run_id": result.run_id,
            "new_state": result.state
        }
    })
    await manager.broadcast(f"group:{result.group_id}", {
        "type": "run_state_changed",
        "data": {
            "run_id": result.run_id,
            "new_state": result.state
        }
    })

    return result

@router.post("/{run_id}/finish-adjusting", response_model=StateChangeResponse)
async def finish_adjusting(
    run_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Finish adjusting bids - transition from adjusting to distributing state (leader only)."""
    repo = get_repository(db)
    service = RunService(repo)

    result = service.finish_adjusting(run_id, current_user)

    # Broadcast state change to both run and group
    await manager.broadcast(f"run:{result.run_id}", {
        "type": "state_changed",
        "data": {
            "run_id": result.run_id,
            "new_state": result.state
        }
    })
    await manager.broadcast(f"group:{result.group_id}", {
        "type": "run_state_changed",
        "data": {
            "run_id": result.run_id,
            "new_state": result.state
        }
    })

    return result

@router.get("/{run_id}/available-products", response_model=list[AvailableProductResponse])
async def get_available_products(
    run_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get products available for bidding (products from the store that don't have bids yet)."""
    repo = get_repository(db)
    service = RunService(repo)

    return service.get_available_products(run_id, current_user)

@router.post("/{run_id}/transition-shopping", response_model=StateChangeResponse)
async def transition_to_shopping(
    run_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Transition to shopping state (alias for start-shopping)."""
    repo = get_repository(db)
    service = RunService(repo)

    result = service.transition_to_shopping(run_id, current_user)

    # Broadcast state change to both run and group
    await manager.broadcast(f"run:{result.run_id}", {
        "type": "state_changed",
        "data": {
            "run_id": result.run_id,
            "new_state": result.state
        }
    })
    await manager.broadcast(f"group:{result.group_id}", {
        "type": "run_state_changed",
        "data": {
            "run_id": result.run_id,
            "new_state": result.state
        }
    })

    return result

@router.post("/{run_id}/cancel", response_model=CancelRunResponse)
async def cancel_run(
    run_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Cancel a run. Leader only. Can be done from any state except completed/cancelled."""
    repo = get_repository(db)
    service = RunService(repo)

    result = service.cancel_run(run_id, current_user)

    # Broadcast to group room
    await manager.broadcast(f"group:{result.group_id}", {
        "type": "run_cancelled",
        "data": {
            "run_id": result.run_id,
            "state": result.state
        }
    })

    return result

@router.delete("/{run_id}", response_model=MessageResponse)
async def delete_run(
    run_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Delete a run (cancels it). Alias for cancel_run for backward compatibility."""
    repo = get_repository(db)
    service = RunService(repo)

    result = service.delete_run(run_id, current_user)

    # Broadcast to group room
    await manager.broadcast(f"group:{result.group_id}", {
        "type": "run_cancelled",
        "data": {
            "run_id": result.run_id
        }
    })

    return MessageResponse(message=result.message)
