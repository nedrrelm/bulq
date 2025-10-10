from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import User
from ..routes.auth import require_auth
from ..repository import get_repository
from ..services import DistributionService
from ..websocket_manager import manager
from ..run_state import RunState
from ..exceptions import BadRequestError, NotFoundError, ForbiddenError
from pydantic import BaseModel
import uuid

router = APIRouter(prefix="/distribution", tags=["distribution"])

class DistributionProduct(BaseModel):
    bid_id: str
    product_id: str
    product_name: str
    requested_quantity: int
    distributed_quantity: int
    price_per_unit: str
    subtotal: str
    is_picked_up: bool

class DistributionUser(BaseModel):
    user_id: str
    user_name: str
    products: List[DistributionProduct]
    total_cost: str
    all_picked_up: bool

@router.get("/{run_id}", response_model=List[DistributionUser])
async def get_distribution_data(
    run_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get distribution data aggregated by user."""
    repo = get_repository(db)
    service = DistributionService(repo)

    # Validate run ID
    try:
        run_uuid = uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid run ID format")

    # Get distribution summary from service
    users_data = service.get_distribution_summary(run_uuid, current_user)

    # Convert to Pydantic models
    result = [
        DistributionUser(
            user_id=user_data['user_id'],
            user_name=user_data['user_name'],
            products=[DistributionProduct(**p) for p in user_data['products']],
            total_cost=user_data['total_cost'],
            all_picked_up=user_data['all_picked_up']
        )
        for user_data in users_data
    ]

    return result

@router.post("/{run_id}/pickup/{bid_id}")
async def mark_picked_up(
    run_id: str,
    bid_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Mark a product as picked up by a user."""
    repo = get_repository(db)
    service = DistributionService(repo)

    # Validate IDs
    try:
        run_uuid = uuid.UUID(run_id)
        bid_uuid = uuid.UUID(bid_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    # Mark as picked up via service
    result = service.mark_picked_up(run_uuid, bid_uuid, current_user)

    return result

@router.post("/{run_id}/complete")
async def complete_distribution(
    run_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Complete distribution - transition from distributing to completed state (leader only)."""
    repo = get_repository(db)
    service = DistributionService(repo)

    # Validate run ID
    try:
        run_uuid = uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid run ID format")

    # Complete distribution via service
    result = service.complete_distribution(run_uuid, current_user)

    # Broadcast state change to both run and group (using data from service)
    await manager.broadcast(f"run:{result['run_id']}", {
        "type": "state_changed",
        "data": {
            "run_id": result['run_id'],
            "new_state": RunState.COMPLETED
        }
    })
    await manager.broadcast(f"group:{result['group_id']}", {
        "type": "run_state_changed",
        "data": {
            "run_id": result['run_id'],
            "new_state": RunState.COMPLETED
        }
    })

    return {"message": result['message'], "state": result['state']}
