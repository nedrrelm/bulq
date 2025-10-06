from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import User
from ..routes.auth import require_auth
from ..repository import get_repository
from ..websocket_manager import manager
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

    # Validate run ID
    try:
        run_uuid = uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid run ID format")

    # Get the run
    run = repo.get_run_by_id(run_uuid)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # Verify user has access to this run
    user_groups = repo.get_user_groups(current_user)
    if not any(g.id == run.group_id for g in user_groups):
        raise HTTPException(status_code=403, detail="Not authorized to view this run")

    # Only allow viewing distribution in distributing or completed states
    if run.state not in ['distributing', 'completed']:
        raise HTTPException(status_code=400, detail="Distribution only available in distributing state")

    # Get all bids with participations and users eagerly loaded to avoid N+1 queries
    all_bids = repo.get_bids_by_run_with_participations(run_uuid)

    # Group bids by user
    users_data = {}

    for bid in all_bids:
        if bid.interested_only or not bid.distributed_quantity:
            continue

        # Participation and user are eagerly loaded on the bid object
        if not bid.participation or not bid.participation.user:
            continue

        user_id = str(bid.participation.user_id)

        # Initialize user data if not exists
        if user_id not in users_data:
            users_data[user_id] = {
                'user_id': user_id,
                'user_name': bid.participation.user.name,
                'products': [],
                'total_cost': 0.0
            }

        # Get product info
        product = None
        if hasattr(repo, '_products'):
            product = repo._products.get(bid.product_id)
        else:
            from ..models import Product
            product = db.query(Product).filter(Product.id == bid.product_id).first()

        if not product:
            continue

        # Calculate subtotal
        price_per_unit = float(bid.distributed_price_per_unit) if bid.distributed_price_per_unit else 0.0
        subtotal = price_per_unit * bid.distributed_quantity

        users_data[user_id]['products'].append({
            'bid_id': str(bid.id),
            'product_id': str(bid.product_id),
            'product_name': product.name,
            'requested_quantity': bid.quantity,
            'distributed_quantity': bid.distributed_quantity,
            'price_per_unit': f"{price_per_unit:.2f}",
            'subtotal': f"{subtotal:.2f}",
            'is_picked_up': bid.is_picked_up
        })

        users_data[user_id]['total_cost'] += subtotal

    # Convert to list and format
    result = []
    for user_data in users_data.values():
        all_picked_up = all(p['is_picked_up'] for p in user_data['products'])

        result.append(DistributionUser(
            user_id=user_data['user_id'],
            user_name=user_data['user_name'],
            products=[DistributionProduct(**p) for p in user_data['products']],
            total_cost=f"{user_data['total_cost']:.2f}",
            all_picked_up=all_picked_up
        ))

    # Sort: users who haven't picked up everything first, then alphabetically
    result.sort(key=lambda x: (x.all_picked_up, x.user_name))

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

    # Validate IDs
    try:
        run_uuid = uuid.UUID(run_id)
        bid_uuid = uuid.UUID(bid_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    # Get the run
    run = repo.get_run_by_id(run_uuid)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # Verify user is the run leader
    participation = repo.get_participation(current_user.id, run_uuid)
    if not participation or not participation.is_leader:
        raise HTTPException(status_code=403, detail="Only the run leader can mark items as picked up")

    # Mark as picked up
    if hasattr(repo, '_bids'):  # Memory mode
        bid = repo._bids.get(bid_uuid)
        if bid:
            bid.is_picked_up = True
        else:
            raise HTTPException(status_code=404, detail="Bid not found")
    else:  # Database mode
        from ..models import ProductBid
        bid = db.query(ProductBid).filter(ProductBid.id == bid_uuid).first()
        if bid:
            bid.is_picked_up = True
            db.commit()
        else:
            raise HTTPException(status_code=404, detail="Bid not found")

    return {"message": "Marked as picked up"}

@router.post("/{run_id}/complete")
async def complete_distribution(
    run_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Complete distribution - transition from distributing to completed state (leader only)."""
    repo = get_repository(db)

    # Validate run ID
    try:
        run_uuid = uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid run ID format")

    # Get the run
    run = repo.get_run_by_id(run_uuid)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # Verify user is the run leader
    participation = repo.get_participation(current_user.id, run_uuid)
    if not participation or not participation.is_leader:
        raise HTTPException(status_code=403, detail="Only the run leader can complete distribution")

    # Only allow completing from distributing state
    if run.state != 'distributing':
        raise HTTPException(status_code=400, detail="Can only complete distribution from distributing state")

    # Verify all items are picked up
    all_bids = repo.get_bids_by_run(run_uuid)
    unpicked_bids = [bid for bid in all_bids if not bid.interested_only and bid.distributed_quantity and not bid.is_picked_up]

    if unpicked_bids:
        raise HTTPException(status_code=400, detail="Cannot complete distribution - some items not picked up")

    # Transition to completed state
    repo.update_run_state(run_uuid, "completed")

    # Broadcast state change to both run and group
    await manager.broadcast(f"run:{run_uuid}", {
        "type": "state_changed",
        "data": {
            "run_id": str(run_uuid),
            "new_state": "completed"
        }
    })
    await manager.broadcast(f"group:{run.group_id}", {
        "type": "run_state_changed",
        "data": {
            "run_id": str(run_uuid),
            "new_state": "completed"
        }
    })

    return {"message": "Distribution completed!", "state": "completed"}
