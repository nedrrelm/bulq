"""Memory product repository implementation."""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from app.core.models import Product, ProductAvailability
from app.repositories.abstract.product import AbstractProductRepository
from app.repositories.memory.storage import MemoryStorage


class MemoryProductRepository(AbstractProductRepository):
    """Memory implementation of product repository."""

    def __init__(self, storage: MemoryStorage):
        self.storage = storage

    def get_products_by_store(self, store_id: UUID) -> list[Product]:
        """Get all products for a store (via product availabilities)."""
        product_ids = {
            avail.product_id
            for avail in self.storage.product_availabilities.values()
            if avail.store_id == store_id
        }
        return [product for product in self.storage.products.values() if product.id in product_ids]

    def search_products(self, query: str) -> list[Product]:
        query_lower = query.lower()
        return [
            product for product in self.storage.products.values() if query_lower in product.name.lower()
        ]

    def get_product_by_id(self, product_id: UUID) -> Product | None:
        return self.storage.products.get(product_id)

    def create_product(
        self, name: str, brand: str | None = None, unit: str | None = None
    ) -> Product:
        """Create a new product (store-agnostic)."""
        product = Product(
            id=uuid4(),
            name=name,
            brand=brand,
            unit=unit,
            verified=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        self.storage.products[product.id] = product
        return product

    def get_all_products(self) -> list[Product]:
        return list(self.storage.products.values())

    def update_product(self, product_id: UUID, **fields) -> Product | None:
        """Update product fields. Returns updated product or None if not found."""
        product = self.storage.products.get(product_id)
        if not product:
            return None

        for key, value in fields.items():
            if hasattr(product, key):
                setattr(product, key, value)

        return product

    def delete_product(self, product_id: UUID) -> bool:
        """Delete a product. Returns True if deleted, False if not found."""
        if product_id not in self.storage.products:
            return False

        del self.storage.products[product_id]
        return True

    def get_product_availabilities(self, product_id: UUID, store_id: UUID = None) -> list:
        """Get product availabilities, optionally filtered by store."""
        results = []
        for avail in self.storage.product_availabilities.values():
            if avail.product_id == product_id and (store_id is None or avail.store_id == store_id):
                results.append(avail)
        return results

    def get_availability_by_product_and_store(
        self, product_id: UUID, store_id: UUID
    ) -> ProductAvailability | None:
        """Get the most recent product availability by product and store."""
        matches = []
        for avail in self.storage.product_availabilities.values():
            if avail.product_id == product_id and avail.store_id == store_id:
                matches.append(avail)

        if not matches:
            return None

        return sorted(matches, key=lambda x: x.created_at if x.created_at else '', reverse=True)[0]

    def create_product_availability(
        self,
        product_id: UUID,
        store_id: UUID,
        price: float | None = None,
        notes: str = '',
        minimum_quantity: int | None = None,
        user_id: UUID = None,
    ) -> ProductAvailability:
        """Create a new product availability record (price observation)."""
        availability = ProductAvailability(
            id=uuid4(),
            product_id=product_id,
            store_id=store_id,
            price=Decimal(str(price)) if price is not None else None,
            notes=notes,
            minimum_quantity=minimum_quantity,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            created_by=user_id,
        )
        self.storage.product_availabilities[availability.id] = availability
        return availability

    def update_product_availability_price(
        self, availability_id: UUID, price: float, notes: str = ''
    ) -> ProductAvailability:
        """Update the price for an existing product availability."""
        availability = self.storage.product_availabilities.get(availability_id)

        if availability:
            availability.price = Decimal(str(price))
            if notes:
                availability.notes = notes

        return availability

    def bulk_update_product_bids(self, old_product_id: UUID, new_product_id: UUID) -> int:
        """Update all product bids from old product to new product. Returns count of updated records."""
        count = 0
        for bid in self.storage.bids.values():
            if bid.product_id == old_product_id:
                bid.product_id = new_product_id
                count += 1
        return count

    def bulk_update_product_availabilities(self, old_product_id: UUID, new_product_id: UUID) -> int:
        """Update all product availabilities from old product to new product. Returns count of updated records."""
        count = 0
        for avail in self.storage.product_availabilities.values():
            if avail.product_id == old_product_id:
                avail.product_id = new_product_id
                count += 1
        return count

    def bulk_update_shopping_list_items(self, old_product_id: UUID, new_product_id: UUID) -> int:
        """Update all shopping list items from old product to new product. Returns count of updated records."""
        count = 0
        for item in self.storage.shopping_list_items.values():
            if item.product_id == old_product_id:
                item.product_id = new_product_id
                count += 1
        return count

    def count_product_bids(self, product_id: UUID) -> int:
        """Count how many bids reference this product."""
        return sum(1 for bid in self.storage.bids.values() if bid.product_id == product_id)
