from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import Run, Store, Group, User, Product, ProductBid
from ..routes.auth import require_auth
from ..repository import get_repository
from pydantic import BaseModel
import uuid

router = APIRouter(prefix="/runs", tags=["runs"])

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

class RunDetailResponse(BaseModel):
    id: str
    group_id: str
    group_name: str
    store_id: str
    store_name: str
    state: str
    products: List[ProductResponse]

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
                    user = repo.get_user_by_id(bid.user_id)
                    if user:
                        bid_response = UserBidResponse(
                            user_id=str(bid.user_id),
                            user_name=user.name,
                            quantity=bid.quantity,
                            interested_only=bid.interested_only
                        )
                        user_bids_data.append(bid_response)

                        # Check if this is the current user's bid
                        if bid.user_id == current_user.id:
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
        products=products_data
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
        # Check if user already has a bid for this product in this run
        existing_bid = None
        for bid in repo._bids.values():
            if (bid.user_id == current_user.id and
                bid.run_id == run_uuid and
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
                user_id=current_user.id,
                run_id=run_uuid,
                product_id=product_uuid,
                quantity=bid_request.quantity,
                interested_only=bid_request.interested_only
            )
            repo._bids[new_bid.id] = new_bid

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
        # Find and remove the user's bid
        bid_to_remove = None
        for bid_id, bid in repo._bids.items():
            if (bid.user_id == current_user.id and
                bid.run_id == run_uuid and
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