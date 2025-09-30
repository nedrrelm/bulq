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

class ProductResponse(BaseModel):
    id: str
    name: str
    base_price: str
    total_quantity: int
    interested_count: int

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
            total_quantity = sum(bid.quantity for bid in product_bids)
            interested_count = len([bid for bid in product_bids if bid.interested_only or bid.quantity > 0])

            if interested_count > 0:  # Only include products with interest
                products_data.append(ProductResponse(
                    id=str(product.id),
                    name=product.name,
                    base_price=str(product.base_price),
                    total_quantity=total_quantity,
                    interested_count=interested_count
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