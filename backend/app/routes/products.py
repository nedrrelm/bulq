from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..routes.auth import require_auth
from ..models import User, Product, ShoppingListItem, Run
from ..repository import get_repository

router = APIRouter(prefix="/products", tags=["products"])

@router.get("/search")
async def search_products(
    q: str = Query(..., min_length=1, description="Search query"),
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Search for products by name across all stores.
    Returns products matching the search query.
    """
    repo = get_repository(db)
    products = repo.search_products(q)

    result = []
    for product in products:
        # Get the store for this product
        store = repo.get_all_stores()
        store_name = next((s.name for s in store if s.id == product.store_id), "Unknown")

        result.append({
            "id": str(product.id),
            "name": product.name,
            "store_id": str(product.store_id),
            "store_name": store_name,
            "base_price": float(product.base_price) if product.base_price else None
        })

    return result

@router.get("/{product_id}")
async def get_product_details(
    product_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Get detailed product information including price history from shopping list items.
    Shows the product across different stores and historical prices encountered during shopping.
    """
    from uuid import UUID
    repo = get_repository(db)

    # Get the main product
    product = repo.get_product_by_id(UUID(product_id))
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Find all products with the same name across different stores
    all_products = repo.search_products(product.name)
    similar_products = [p for p in all_products if p.name.lower() == product.name.lower()]

    # Collect price data from shopping list items
    stores_data = []
    seen_store_ids = set()
    all_stores = {s.id: s for s in repo.get_all_stores()}

    for prod in similar_products:
        if str(prod.store_id) in seen_store_ids:
            continue
        seen_store_ids.add(str(prod.store_id))

        # Get shopping list items for this product
        shopping_items = repo.get_shopping_list_items_by_product(prod.id)

        # Extract all encountered prices
        all_prices = []
        for item in shopping_items:
            if item.encountered_prices:
                for price_entry in item.encountered_prices:
                    if isinstance(price_entry, dict) and "price" in price_entry:
                        all_prices.append({
                            "price": float(price_entry["price"]),
                            "notes": price_entry.get("notes", ""),
                            "run_id": str(item.run_id),
                            "timestamp": item.updated_at.isoformat() if item.updated_at else None
                        })

            # Add purchased price if available
            if item.purchased_price_per_unit:
                all_prices.append({
                    "price": float(item.purchased_price_per_unit),
                    "notes": "Purchased",
                    "run_id": str(item.run_id),
                    "timestamp": item.updated_at.isoformat() if item.updated_at else None
                })

        store = all_stores.get(prod.store_id)
        stores_data.append({
            "store_id": str(prod.store_id),
            "store_name": store.name if store else "Unknown",
            "base_price": float(prod.base_price) if prod.base_price else None,
            "encountered_prices": all_prices,
            "product_id": str(prod.id)
        })

    return {
        "id": str(product.id),
        "name": product.name,
        "stores": stores_data
    }
