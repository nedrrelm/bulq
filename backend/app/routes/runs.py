from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import Run, Store, Group, User, Product, ProductBid, RunParticipation
from ..routes.auth import require_auth
from ..repository import get_repository
from ..services import RunService
from ..websocket_manager import manager
from ..run_state import RunState
from pydantic import BaseModel, validator, Field
import logging
import uuid

router = APIRouter(prefix="/runs", tags=["runs"])
logger = logging.getLogger(__name__)

class CreateRunRequest(BaseModel):
    group_id: str
    store_id: str

class CreateRunResponse(BaseModel):
    id: str
    group_id: str
    store_id: str
    state: str

    class Config:
        from_attributes = True

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
    await manager.broadcast(f"group:{result['group_id']}", {
        "type": "run_created",
        "data": {
            "run_id": result['id'],
            "store_id": result['store_id'],
            "store_name": result['store_name'],
            "state": result['state'],
            "leader_name": result['leader_name']
        }
    })

    return CreateRunResponse(
        id=result['id'],
        group_id=result['group_id'],
        store_id=result['store_id'],
        state=result['state']
    )

class UserBidResponse(BaseModel):
    user_id: str
    user_name: str
    quantity: int
    interested_only: bool

    class Config:
        from_attributes = True

class ProductResponse(BaseModel):
    id: str
    name: str
    brand: str | None = None
    current_price: str | None
    total_quantity: int
    interested_count: int
    user_bids: list[UserBidResponse]
    current_user_bid: UserBidResponse | None
    purchased_quantity: int | None = None  # For adjusting state

    class Config:
        from_attributes = True

class ParticipantResponse(BaseModel):
    user_id: str
    user_name: str
    is_leader: bool
    is_ready: bool

    class Config:
        from_attributes = True

class RunDetailResponse(BaseModel):
    id: str
    group_id: str
    group_name: str
    store_id: str
    store_name: str
    state: str
    products: List[ProductResponse]
    participants: List[ParticipantResponse]
    current_user_is_ready: bool
    current_user_is_leader: bool
    leader_name: str

    class Config:
        from_attributes = True

@router.get("/{run_id}", response_model=RunDetailResponse)
async def get_run_details(
    run_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific run."""
    repo = get_repository(db)
    service = RunService(repo)

    result = service.get_run_details(run_id, current_user)

    # Convert dict data to Pydantic models
    products = [
        ProductResponse(
            id=p['id'],
            name=p['name'],
            brand=p.get('brand'),
            current_price=p.get('current_price'),
            total_quantity=p['total_quantity'],
            interested_count=p['interested_count'],
            user_bids=[UserBidResponse(**ub) for ub in p['user_bids']],
            current_user_bid=UserBidResponse(**p['current_user_bid']) if p['current_user_bid'] else None,
            purchased_quantity=p.get('purchased_quantity')
        )
        for p in result['products']
    ]

    participants = [
        ParticipantResponse(**p)
        for p in result['participants']
    ]

    return RunDetailResponse(
        id=result['id'],
        group_id=result['group_id'],
        group_name=result['group_name'],
        store_id=result['store_id'],
        store_name=result['store_name'],
        state=result['state'],
        products=products,
        participants=participants,
        current_user_is_ready=result['current_user_is_ready'],
        current_user_is_leader=result['current_user_is_leader'],
        leader_name=result['leader_name']
    )

class PlaceBidRequest(BaseModel):
    product_id: str
    quantity: float = Field(gt=0, le=9999)
    interested_only: bool = False

    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be greater than 0')
        # Check max 2 decimal places
        if round(v, 2) != v:
            raise ValueError('Quantity can have at most 2 decimal places')
        return v

@router.post("/{run_id}/bids")
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
    await manager.broadcast(f"run:{result['run_id']}", {
        "type": "bid_updated",
        "data": {
            "product_id": result['product_id'],
            "user_id": result['user_id'],
            "user_name": result['user_name'],
            "quantity": result['quantity'],
            "interested_only": result['interested_only'],
            "new_total": result['new_total']
        }
    })

    # If state changed, broadcast to both run and group
    if result.get('state_changed'):
        await manager.broadcast(f"run:{result['run_id']}", {
            "type": "state_changed",
            "data": {
                "run_id": result['run_id'],
                "new_state": result['new_state']
            }
        })
        await manager.broadcast(f"group:{result['group_id']}", {
            "type": "run_state_changed",
            "data": {
                "run_id": result['run_id'],
                "new_state": result['new_state']
            }
        })

    return {"message": result['message']}

@router.delete("/{run_id}/bids/{product_id}")
async def retract_bid(
    run_id: str,
    product_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Retract a bid on a product in a run."""
    repo = get_repository(db)

    # Validate IDs
    try:
        run_uuid = uuid.UUID(run_id)
        product_uuid = uuid.UUID(product_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    # Verify run exists and user has access
    runs = [run for run in repo._runs.values() if run.id == run_uuid] if hasattr(repo, '_runs') else []
    if not runs:
        raise HTTPException(status_code=404, detail="Run not found")

    run = runs[0]
    user_groups = repo.get_user_groups(current_user)
    if not any(g.id == run.group_id for g in user_groups):
        raise HTTPException(status_code=403, detail="Not authorized to modify bids on this run")

    # Check if run allows bid modification
    if run.state not in ['planning', 'active', 'adjusting']:
        raise HTTPException(status_code=400, detail="Bid modification not allowed in current run state")

    # In adjusting state, check if retraction is allowed
    if run.state == 'adjusting':
        # Get shopping list to check if this retraction is within limits
        shopping_items = repo.get_shopping_list_items(run_uuid)
        shopping_item = next((item for item in shopping_items if item.product_id == product_uuid), None)

        if shopping_item:
            purchased_qty = shopping_item.purchased_quantity or 0
            requested_qty = shopping_item.requested_quantity
            shortage = requested_qty - purchased_qty

            # Get current bid to check if full retraction is allowed
            participation = repo.get_participation(current_user.id, run_uuid)
            if participation and hasattr(repo, '_bids'):
                current_bid = None
                for bid in repo._bids.values():
                    if (bid.participation_id == participation.id and
                        bid.product_id == product_uuid):
                        current_bid = bid
                        break

                if current_bid and current_bid.quantity > shortage:
                    raise HTTPException(status_code=400, detail=f"Cannot fully retract bid. You can reduce it by at most {shortage} items.")

    if hasattr(repo, '_bids'):  # Memory mode
        # Get participation for this user in this run
        participation = repo.get_participation(current_user.id, run_uuid)
        if not participation:
            raise HTTPException(status_code=404, detail=f"You are not participating in this run (user_id: {current_user.id}, run_id: {run_uuid})")

        # Find and remove the user's bid
        bid_to_remove = None
        for bid_id, bid in repo._bids.items():
            if (bid.participation_id == participation.id and
                bid.product_id == product_uuid):
                bid_to_remove = bid_id
                break

        if bid_to_remove:
            del repo._bids[bid_to_remove]

            # Calculate new totals after retraction
            all_bids = repo.get_bids_by_run(run_uuid)
            product_bids = [bid for bid in all_bids if bid.product_id == product_uuid]
            new_total = sum(bid.quantity for bid in product_bids if not bid.interested_only)

            # Broadcast to run room
            await manager.broadcast(f"run:{run_uuid}", {
                "type": "bid_retracted",
                "data": {
                    "product_id": str(product_uuid),
                    "user_id": str(current_user.id),
                    "new_total": new_total
                }
            })

            return {"message": "Bid retracted successfully"}
        else:
            raise HTTPException(status_code=404, detail=f"No bid found for this product")

    return {"message": "Bid retracted successfully"}

class AvailableProductResponse(BaseModel):
    id: str
    name: str
    brand: str | None = None
    current_price: str | None
    has_store_availability: bool = False

    class Config:
        from_attributes = True

@router.post("/{run_id}/ready")
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
    await manager.broadcast(f"run:{result['run_id']}", {
        "type": "ready_toggled",
        "data": {
            "user_id": result['user_id'],
            "is_ready": result['is_ready']
        }
    })

    # If state changed, broadcast state change to both run and group
    if result.get('state_changed'):
        await manager.broadcast(f"run:{result['run_id']}", {
            "type": "state_changed",
            "data": {
                "run_id": result['run_id'],
                "new_state": result['new_state']
            }
        })
        await manager.broadcast(f"group:{result['group_id']}", {
            "type": "run_state_changed",
            "data": {
                "run_id": result['run_id'],
                "new_state": result['new_state']
            }
        })

    return {
        "message": result['message'],
        "is_ready": result['is_ready'],
        "state_changed": result.get('state_changed', False)
    }

@router.post("/{run_id}/start-shopping")
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
    await manager.broadcast(f"run:{result['run_id']}", {
        "type": "state_changed",
        "data": {
            "run_id": result['run_id'],
            "new_state": result['state']
        }
    })
    await manager.broadcast(f"group:{result['group_id']}", {
        "type": "run_state_changed",
        "data": {
            "run_id": result['run_id'],
            "new_state": result['state']
        }
    })

    return {"message": result['message'], "state": result['state']}

@router.post("/{run_id}/finish-adjusting")
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
    await manager.broadcast(f"run:{result['run_id']}", {
        "type": "state_changed",
        "data": {
            "run_id": result['run_id'],
            "new_state": result['state']
        }
    })
    await manager.broadcast(f"group:{result['group_id']}", {
        "type": "run_state_changed",
        "data": {
            "run_id": result['run_id'],
            "new_state": result['state']
        }
    })

    return {"message": result['message'], "state": result['state']}

@router.get("/{run_id}/available-products", response_model=List[AvailableProductResponse])
async def get_available_products(
    run_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get products available for bidding (products from the store that don't have bids yet)."""
    repo = get_repository(db)
    service = RunService(repo)

    result = service.get_available_products(run_id, current_user)

    return [
        AvailableProductResponse(
            id=p['id'],
            name=p['name'],
            brand=p.get('brand'),
            current_price=p.get('current_price'),
            has_store_availability=p.get('has_store_availability', False)
        )
        for p in result
    ]

@router.post("/{run_id}/transition-shopping")
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
    await manager.broadcast(f"run:{result['run_id']}", {
        "type": "state_changed",
        "data": {
            "run_id": result['run_id'],
            "new_state": result['state']
        }
    })
    await manager.broadcast(f"group:{result['group_id']}", {
        "type": "run_state_changed",
        "data": {
            "run_id": result['run_id'],
            "new_state": result['state']
        }
    })

    return {"message": result['message'], "state": result['state']}

@router.post("/{run_id}/cancel")
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
    await manager.broadcast(f"group:{result['group_id']}", {
        "type": "run_cancelled",
        "data": {
            "run_id": result['run_id'],
            "state": result['state']
        }
    })

    return result

@router.delete("/{run_id}")
async def delete_run(
    run_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Delete a run (cancels it). Alias for cancel_run for backward compatibility."""
    repo = get_repository(db)
    service = RunService(repo)

    result = service.delete_run(run_id, current_user)

    # Broadcast to group room (try to get from service result)
    group_id = result.get('group_id', 'unknown')
    await manager.broadcast(f"group:{group_id}", {
        "type": "run_cancelled",
        "data": {
            "run_id": result['run_id']
        }
    })

    return {"message": result['message']}
