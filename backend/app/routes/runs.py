from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import Run, Store, Group, User, Product, ProductBid, RunParticipation
from ..routes.auth import require_auth
from ..repository import get_repository
from pydantic import BaseModel
import uuid

router = APIRouter(prefix="/runs", tags=["runs"])

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

    # Validate IDs
    try:
        group_uuid = uuid.UUID(request.group_id)
        store_uuid = uuid.UUID(request.store_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    # Verify group exists and user is a member
    group = repo.get_group_by_id(group_uuid)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    user_groups = repo.get_user_groups(current_user)
    if not any(g.id == group_uuid for g in user_groups):
        raise HTTPException(status_code=403, detail="Not authorized to create runs for this group")

    # Verify store exists
    all_stores = repo.get_all_stores()
    store = next((s for s in all_stores if s.id == store_uuid), None)
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")

    # Create the run with current user as leader
    run = repo.create_run(group_uuid, store_uuid, current_user.id)

    return CreateRunResponse(
        id=str(run.id),
        group_id=str(run.group_id),
        store_id=str(run.store_id),
        state=run.state
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
    base_price: str
    total_quantity: int
    interested_count: int
    user_bids: list[UserBidResponse]
    current_user_bid: UserBidResponse | None

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

    # Validate run ID format
    try:
        run_uuid = uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid run ID format")

    # Find the run
    runs = [run for run in repo._runs.values() if run.id == run_uuid] if hasattr(repo, '_runs') else []
    if not runs:
        # Try database if using database mode
        run = db.query(Run).filter(Run.id == run_uuid).first() if hasattr(db, 'query') else None
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        runs = [run]

    run = runs[0]

    # Verify user has access to this run (member of the group)
    user_groups = repo.get_user_groups(current_user)
    if not any(g.id == run.group_id for g in user_groups):
        raise HTTPException(status_code=403, detail="Not authorized to view this run")

    # Get group and store information
    group = repo.get_group_by_id(run.group_id)
    all_stores = repo.get_all_stores()
    store = next((s for s in all_stores if s.id == run.store_id), None)

    if not group or not store:
        raise HTTPException(status_code=404, detail="Group or store not found")

    # Get participants
    participants_data = []
    current_user_is_ready = False
    current_user_is_leader = False
    participations = repo.get_run_participations(run.id)

    for participation in participations:
        user = repo.get_user_by_id(participation.user_id)
        if user:
            participants_data.append(ParticipantResponse(
                user_id=str(participation.user_id),
                user_name=user.name,
                is_leader=participation.is_leader,
                is_ready=participation.is_ready
            ))
            if participation.user_id == current_user.id:
                current_user_is_ready = participation.is_ready
                current_user_is_leader = participation.is_leader

    # Get products and bids for this run
    if hasattr(repo, '_runs'):  # Memory mode
        # Get all products for the store
        store_products = repo.get_products_by_store(run.store_id)
        run_bids = repo.get_bids_by_run(run.id)

        # Calculate product statistics
        products_data = []
        for product in store_products:
            product_bids = [bid for bid in run_bids if bid.product_id == product.id]

            if len(product_bids) > 0:  # Only include products with bids
                total_quantity = sum(bid.quantity for bid in product_bids)
                interested_count = len([bid for bid in product_bids if bid.interested_only or bid.quantity > 0])

                # Get user details for each bid
                user_bids_data = []
                current_user_bid = None

                for bid in product_bids:
                    # Get participation to find user
                    participation = repo._participations.get(bid.participation_id) if hasattr(repo, '_participations') else None
                    if participation:
                        user = repo.get_user_by_id(participation.user_id)
                        if user:
                            bid_response = UserBidResponse(
                                user_id=str(participation.user_id),
                                user_name=user.name,
                                quantity=bid.quantity,
                                interested_only=bid.interested_only
                            )
                            user_bids_data.append(bid_response)

                            # Check if this is the current user's bid
                            if participation.user_id == current_user.id:
                                current_user_bid = bid_response

                products_data.append(ProductResponse(
                    id=str(product.id),
                    name=product.name,
                    base_price=str(product.base_price),
                    total_quantity=total_quantity,
                    interested_count=interested_count,
                    user_bids=user_bids_data,
                    current_user_bid=current_user_bid
                ))
    else:
        # Database mode - would need proper joins
        products_data = []

    return RunDetailResponse(
        id=str(run.id),
        group_id=str(run.group_id),
        group_name=group.name,
        store_id=str(run.store_id),
        store_name=store.name,
        state=run.state,
        products=products_data,
        participants=participants_data,
        current_user_is_ready=current_user_is_ready,
        current_user_is_leader=current_user_is_leader
    )

class PlaceBidRequest(BaseModel):
    product_id: str
    quantity: int
    interested_only: bool = False

@router.post("/{run_id}/bids")
async def place_bid(
    run_id: str,
    bid_request: PlaceBidRequest,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Place or update a bid on a product in a run."""
    repo = get_repository(db)

    # Validate IDs
    try:
        run_uuid = uuid.UUID(run_id)
        product_uuid = uuid.UUID(bid_request.product_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    # Verify run exists and user has access
    runs = [run for run in repo._runs.values() if run.id == run_uuid] if hasattr(repo, '_runs') else []
    if not runs:
        raise HTTPException(status_code=404, detail="Run not found")

    run = runs[0]
    user_groups = repo.get_user_groups(current_user)
    if not any(g.id == run.group_id for g in user_groups):
        raise HTTPException(status_code=403, detail="Not authorized to bid on this run")

    # Check if run allows bidding
    if run.state not in ['planning', 'active']:
        raise HTTPException(status_code=400, detail="Bidding not allowed in current run state")

    # Verify product exists
    store_products = repo.get_products_by_store(run.store_id)
    product = next((p for p in store_products if p.id == product_uuid), None)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Validate quantity
    if bid_request.quantity < 0:
        raise HTTPException(status_code=400, detail="Quantity cannot be negative")

    if hasattr(repo, '_bids'):  # Memory mode
        # Get or create participation for this user in this run
        participation = repo.get_participation(current_user.id, run_uuid)
        is_new_participant = False
        if not participation:
            # Create participation (not as leader)
            participation = repo.create_participation(current_user.id, run_uuid, is_leader=False)
            is_new_participant = True

        # Check if user already has a bid for this product
        existing_bid = None
        for bid in repo._bids.values():
            if (bid.participation_id == participation.id and
                bid.product_id == product_uuid):
                existing_bid = bid
                break

        if existing_bid:
            # Update existing bid
            existing_bid.quantity = bid_request.quantity
            existing_bid.interested_only = bid_request.interested_only
        else:
            # Create new bid
            from uuid import uuid4
            new_bid = ProductBid(
                id=uuid4(),
                participation_id=participation.id,
                product_id=product_uuid,
                quantity=bid_request.quantity,
                interested_only=bid_request.interested_only
            )
            # Set up relationships
            new_bid.participation = participation
            new_bid.product = product
            repo._bids[new_bid.id] = new_bid

        # Automatic state transition: planning → active
        # When a non-leader places their first bid, transition from planning to active
        if is_new_participant and not participation.is_leader and run.state == "planning":
            repo.update_run_state(run_uuid, "active")

    return {"message": "Bid placed successfully"}

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
    if run.state not in ['planning', 'active']:
        raise HTTPException(status_code=400, detail="Bid modification not allowed in current run state")

    if hasattr(repo, '_bids'):  # Memory mode
        # Get participation for this user in this run
        participation = repo.get_participation(current_user.id, run_uuid)
        if not participation:
            raise HTTPException(status_code=404, detail="No bid found to retract")

        # Find and remove the user's bid
        bid_to_remove = None
        for bid_id, bid in repo._bids.items():
            if (bid.participation_id == participation.id and
                bid.product_id == product_uuid):
                bid_to_remove = bid_id
                break

        if bid_to_remove:
            del repo._bids[bid_to_remove]
            return {"message": "Bid retracted successfully"}
        else:
            raise HTTPException(status_code=404, detail="No bid found to retract")

    return {"message": "Bid retracted successfully"}

class AvailableProductResponse(BaseModel):
    id: str
    name: str
    base_price: str

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

    # Validate run ID
    try:
        run_uuid = uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid run ID format")

    # Get the run
    run = repo.get_run_by_id(run_uuid)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # Verify user has access to this run (member of the group)
    user_groups = repo.get_user_groups(current_user)
    if not any(g.id == run.group_id for g in user_groups):
        raise HTTPException(status_code=403, detail="Not authorized to modify this run")

    # Only allow toggling ready in active state
    if run.state != 'active':
        raise HTTPException(status_code=400, detail="Can only mark ready in active state")

    # Get user's participation
    participation = repo.get_participation(current_user.id, run_uuid)
    if not participation:
        raise HTTPException(status_code=404, detail="You are not participating in this run")

    # Toggle ready status
    new_ready_status = not participation.is_ready
    repo.update_participation_ready(participation.id, new_ready_status)

    # Check if all participants are ready
    all_participations = repo.get_run_participations(run_uuid)
    all_ready = all(p.is_ready for p in all_participations)

    # Automatic state transition: active → confirmed
    # When all participants mark themselves as ready
    if all_ready and len(all_participations) > 0:
        repo.update_run_state(run_uuid, "confirmed")
        return {"message": "All participants ready! Run confirmed.", "is_ready": new_ready_status, "state_changed": True}

    return {"message": f"Ready status updated to {new_ready_status}", "is_ready": new_ready_status, "state_changed": False}

@router.post("/{run_id}/start-shopping")
async def start_shopping(
    run_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Start shopping - transition from confirmed to shopping state (leader only)."""
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

    # Verify user has access to this run (member of the group)
    user_groups = repo.get_user_groups(current_user)
    if not any(g.id == run.group_id for g in user_groups):
        raise HTTPException(status_code=403, detail="Not authorized to modify this run")

    # Only allow starting shopping from confirmed state
    if run.state != 'confirmed':
        raise HTTPException(status_code=400, detail="Can only start shopping from confirmed state")

    # Check if user is the run leader
    participation = repo.get_participation(current_user.id, run_uuid)
    if not participation or not participation.is_leader:
        raise HTTPException(status_code=403, detail="Only the run leader can start shopping")

    # Transition to shopping state
    repo.update_run_state(run_uuid, "shopping")

    return {"message": "Shopping started!", "state": "shopping"}

@router.get("/{run_id}/available-products", response_model=List[AvailableProductResponse])
async def get_available_products(
    run_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get products available for bidding (products from the store that don't have bids yet)."""
    repo = get_repository(db)

    # Validate run ID
    try:
        run_uuid = uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid run ID format")

    # Verify run exists and user has access
    runs = [run for run in repo._runs.values() if run.id == run_uuid] if hasattr(repo, '_runs') else []
    if not runs:
        raise HTTPException(status_code=404, detail="Run not found")

    run = runs[0]
    user_groups = repo.get_user_groups(current_user)
    if not any(g.id == run.group_id for g in user_groups):
        raise HTTPException(status_code=403, detail="Not authorized to view this run")

    if hasattr(repo, '_runs'):  # Memory mode
        # Get all products for the store
        store_products = repo.get_products_by_store(run.store_id)
        run_bids = repo.get_bids_by_run(run.id)

        # Get products that have bids
        products_with_bids = set(bid.product_id for bid in run_bids)

        # Return products that don't have bids
        available_products = []
        for product in store_products:
            if product.id not in products_with_bids:
                available_products.append(AvailableProductResponse(
                    id=str(product.id),
                    name=product.name,
                    base_price=str(product.base_price)
                ))

        return available_products
    else:
        # Database mode - would need proper joins
        return []