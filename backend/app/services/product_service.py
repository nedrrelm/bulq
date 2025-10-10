"""Product service for handling product-related business logic."""

from typing import List, Dict, Any, Optional
from uuid import UUID
from ..models import Product, Store
from .base_service import BaseService
from ..exceptions import ValidationError, NotFoundError


class ProductService(BaseService):
    """Service for product operations."""

    def search_products(self, query: str) -> List[Dict[str, Any]]:
        """Search for products by name across all stores."""
        products = self.repo.search_products(query)

        result = []
        for product in products:
            # Get availabilities to show store information
            availabilities = self.repo.get_product_availabilities(product.id)
            stores_info = []
            for avail in availabilities:
                store = self.repo.get_store_by_id(avail.store_id)
                if store:
                    stores_info.append({
                        "store_id": str(store.id),
                        "store_name": store.name,
                        "price": float(avail.price) if avail.price else None
                    })

            result.append({
                "id": str(product.id),
                "name": product.name,
                "brand": product.brand,
                "stores": stores_info
            })

        return result

    def get_product_details(self, product_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get detailed product information including price history from shopping list items and availabilities.
        Shows the product across different stores with price history.
        """
        product = self.repo.get_product_by_id(product_id)
        if not product:
            return None

        # Get all availabilities for this product
        availabilities = self.repo.get_product_availabilities(product_id)

        # Group availabilities by store
        from collections import defaultdict
        stores_map = defaultdict(list)
        for avail in availabilities:
            stores_map[avail.store_id].append(avail)

        # Collect price data by store
        stores_data = []
        all_stores = {s.id: s for s in self.repo.get_all_stores()}

        for store_id, store_availabilities in stores_map.items():
            store = all_stores.get(store_id)
            if not store:
                continue

            # Get shopping list items for this product at this store
            shopping_items = self.repo.get_shopping_list_items_by_product(product.id)

            # Extract price history from all availabilities at this store
            all_prices = []

            # Add all availability prices (multiple observations over time)
            for avail in store_availabilities:
                if avail.price:
                    all_prices.append({
                        "price": float(avail.price),
                        "notes": avail.notes or "",
                        "timestamp": avail.created_at.isoformat() if hasattr(avail, 'created_at') and avail.created_at else None
                    })

            # Add purchased prices from shopping items
            for item in shopping_items:
                if item.purchased_price_per_unit:
                    # Check if this item's run was for this store
                    run = self.repo.get_run_by_id(item.run_id)
                    if run and run.store_id == store_id:
                        all_prices.append({
                            "price": float(item.purchased_price_per_unit),
                            "notes": "Purchased",
                            "run_id": str(item.run_id),
                            "timestamp": item.updated_at.isoformat() if item.updated_at else None
                        })

            # Get most recent availability for current price
            most_recent = max(store_availabilities, key=lambda a: a.created_at if a.created_at else "", default=None)
            current_price = float(most_recent.price) if most_recent and most_recent.price else None

            stores_data.append({
                "store_id": str(store_id),
                "store_name": store.name,
                "current_price": current_price,
                "price_history": all_prices,
                "notes": ""
            })

        return {
            "id": str(product.id),
            "name": product.name,
            "brand": product.brand,
            "unit": product.unit,
            "stores": stores_data
        }

    def create_product(
        self,
        name: str,
        brand: Optional[str] = None,
        unit: Optional[str] = None,
        store_id: Optional[UUID] = None,
        price: Optional[float] = None,
        user_id: Optional[UUID] = None
    ) -> tuple[Product, Optional[Any]]:
        """
        Create a new product (store-agnostic).
        Optionally create a product availability if store_id is provided.
        Returns (product, availability) tuple.
        """
        # Validate inputs
        if not name or not name.strip():
            raise ValidationError("Product name cannot be empty")

        if price is not None:
            if price < 0:
                raise ValidationError("Product price cannot be negative")
            if price == 0:
                raise ValidationError("Product price cannot be zero")

        # Verify store exists if provided
        if store_id:
            store = self.repo.get_store_by_id(store_id)
            if not store:
                raise NotFoundError("Store not found")

        # Create the product
        product = self.repo.create_product(name.strip(), brand, unit)

        # Create availability if store is provided
        availability = None
        if store_id:
            availability = self.repo.create_product_availability(
                product.id,
                store_id,
                price=price,
                user_id=user_id
            )

        return product, availability
