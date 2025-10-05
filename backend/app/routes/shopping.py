from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import User
from ..routes.auth import require_auth
from ..repository import get_repository
from pydantic import BaseModel
import uuid

router = APIRouter(prefix="/shopping", tags=["shopping"])

class EncounteredPrice(BaseModel):
    price: float
    notes: str

class ShoppingListItemResponse(BaseModel):
    id: str
    product_id: str
    product_name: str
    requested_quantity: int
    encountered_prices: List[dict]
    purchased_quantity: int | None
    purchased_price_per_unit: str | None
    purchased_total: str | None
    is_purchased: bool
    purchase_order: int | None

    class Config:
        from_attributes = True

class AddEncounteredPriceRequest(BaseModel):
    price: float
    notes: str = ""

class MarkPurchasedRequest(BaseModel):
    quantity: int
    price_per_unit: float
    total: float

@router.get("/{run_id}/items", response_model=List[ShoppingListItemResponse])
async def get_shopping_list(
    run_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get shopping list for a run."""
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

    # Only allow viewing shopping list in shopping or later states
    if run.state not in ['shopping', 'distributing', 'completed']:
        raise HTTPException(status_code=400, detail="Shopping list only available in shopping state")

    # Get shopping list items
    items = repo.get_shopping_list_items(run_uuid)

    # Convert to response format
    response_items = []
    for item in items:
        product = repo.get_products_by_store(item.product.store_id) if hasattr(item, 'product') and item.product else []
        product = next((p for p in product if p.id == item.product_id), None) if product else None

        response_items.append(ShoppingListItemResponse(
            id=str(item.id),
            product_id=str(item.product_id),
            product_name=product.name if product else "Unknown Product",
            requested_quantity=item.requested_quantity,
            encountered_prices=item.encountered_prices or [],
            purchased_quantity=item.purchased_quantity,
            purchased_price_per_unit=str(item.purchased_price_per_unit) if item.purchased_price_per_unit else None,
            purchased_total=str(item.purchased_total) if item.purchased_total else None,
            is_purchased=item.is_purchased,
            purchase_order=item.purchase_order
        ))

    # Sort: unpurchased first, then purchased by purchase order
    response_items.sort(key=lambda x: (x.is_purchased, x.purchase_order if x.purchase_order else 999))

    return response_items

@router.post("/{run_id}/items/{item_id}/encountered-price")
async def add_encountered_price(
    run_id: str,
    item_id: str,
    request: AddEncounteredPriceRequest,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Add an encountered price for a shopping list item."""
    repo = get_repository(db)

    # Validate IDs
    try:
        run_uuid = uuid.UUID(run_id)
        item_uuid = uuid.UUID(item_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    # Get the run
    run = repo.get_run_by_id(run_uuid)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # Verify user is the run leader
    participation = repo.get_participation(current_user.id, run_uuid)
    if not participation or not participation.is_leader:
        raise HTTPException(status_code=403, detail="Only the run leader can add prices")

    # Add encountered price
    item = repo.add_encountered_price(item_uuid, request.price, request.notes)
    if not item:
        raise HTTPException(status_code=404, detail="Shopping list item not found")

    return {"message": "Price added successfully"}

@router.post("/{run_id}/items/{item_id}/purchase")
async def mark_purchased(
    run_id: str,
    item_id: str,
    request: MarkPurchasedRequest,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Mark a shopping list item as purchased."""
    repo = get_repository(db)

    # Validate IDs
    try:
        run_uuid = uuid.UUID(run_id)
        item_uuid = uuid.UUID(item_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    # Get the run
    run = repo.get_run_by_id(run_uuid)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # Verify user is the run leader
    participation = repo.get_participation(current_user.id, run_uuid)
    if not participation or not participation.is_leader:
        raise HTTPException(status_code=403, detail="Only the run leader can mark items as purchased")

    # Get next purchase order number
    existing_items = repo.get_shopping_list_items(run_uuid)
    max_order = max([item.purchase_order for item in existing_items if item.purchase_order is not None], default=0)
    next_order = max_order + 1

    # Mark as purchased
    item = repo.mark_item_purchased(
        item_uuid,
        request.quantity,
        request.price_per_unit,
        request.total,
        next_order
    )
    if not item:
        raise HTTPException(status_code=404, detail="Shopping list item not found")

    return {"message": "Item marked as purchased", "purchase_order": next_order}

@router.post("/{run_id}/complete")
async def complete_shopping(
    run_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Complete shopping - transition from shopping to distributing state (leader only)."""
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
        raise HTTPException(status_code=403, detail="Only the run leader can complete shopping")

    # Only allow completing from shopping state
    if run.state != 'shopping':
        raise HTTPException(status_code=400, detail="Can only complete shopping from shopping state")

    # Transition to distributing state
    repo.update_run_state(run_uuid, "distributing")

    return {"message": "Shopping completed! Moving to distribution.", "state": "distributing"}
