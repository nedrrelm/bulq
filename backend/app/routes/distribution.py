from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..routes.auth import require_auth
from ..services import DistributionService
from ..websocket_manager import manager
from ..run_state import RunState
from ..exceptions import BadRequestError, NotFoundError, ForbiddenError
from ..schemas import (
    DistributionUser,
    MessageResponse,
    StateChangeResponse,
)
from uuid import UUID

router = APIRouter(prefix="/distribution", tags=["distribution"])

@router.get("/{run_id}", response_model=list[DistributionUser])
async def get_distribution_data(
    run_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get distribution data aggregated by user."""
    service = DistributionService(db)

    # Validate run ID
    try:
        run_uuid = UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid run ID format")

    return service.get_distribution_summary(run_uuid, current_user)

@router.post("/{run_id}/pickup/{bid_id}", response_model=MessageResponse)
async def mark_picked_up(
    run_id: str,
    bid_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Mark a product as picked up by a user."""
    service = DistributionService(db)

    # Validate IDs
    try:
        run_uuid = UUID(run_id)
        bid_uuid = UUID(bid_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    return service.mark_picked_up(run_uuid, bid_uuid, current_user)

@router.post("/{run_id}/complete", response_model=StateChangeResponse)
async def complete_distribution(
    run_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Complete distribution - transition from distributing to completed state (leader only)."""
    service = DistributionService(db)

    # Validate run ID
    try:
        run_uuid = UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid run ID format")

    # Complete distribution via service
    result = service.complete_distribution(run_uuid, current_user)

    # Broadcast state change to both run and group (using data from service)
    await manager.broadcast(f"run:{result.run_id}", {
        "type": "state_changed",
        "data": {
            "run_id": result.run_id,
            "new_state": RunState.COMPLETED
        }
    })
    await manager.broadcast(f"group:{result.group_id}", {
        "type": "run_state_changed",
        "data": {
            "run_id": result.run_id,
            "new_state": RunState.COMPLETED
        }
    })

    return result
