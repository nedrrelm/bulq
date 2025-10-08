"""Product service for handling product-related business logic."""

from typing import List, Dict, Any, Optional
from uuid import UUID
from ..models import Product, Store
from .base_service import BaseService


class ProductService(BaseService):
    """Service for product operations."""

    def search_products(self, query: str) -> List[Dict[str, Any]]:
        """Search for products by name across all stores."""
        products = self.repo.search_products(query)
        stores = {s.id: s for s in self.repo.get_all_stores()}

        result = []
        for product in products:
            store = stores.get(product.store_id)
            result.append({
                "id": str(product.id),
                "name": product.name,
                "store_id": str(product.store_id),
                "store_name": store.name if store else "Unknown",
                "base_price": float(product.base_price) if product.base_price else None
            })

        return result

    def get_product_details(self, product_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get detailed product information including price history from shopping list items.
        Shows the product across different stores and historical prices encountered during shopping.
        """
        product = self.repo.get_product_by_id(product_id)
        if not product:
            return None

        # Find all products with the same name across different stores
        all_products = self.repo.search_products(product.name)
        similar_products = [p for p in all_products if p.name.lower() == product.name.lower()]

        # Collect price data from shopping list items
        stores_data = []
        seen_store_ids = set()
        all_stores = {s.id: s for s in self.repo.get_all_stores()}

        for prod in similar_products:
            if str(prod.store_id) in seen_store_ids:
                continue
            seen_store_ids.add(str(prod.store_id))

            # Get shopping list items for this product
            shopping_items = self.repo.get_shopping_list_items_by_product(prod.id)

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
