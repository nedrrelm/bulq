"""Abstract product repository interface."""

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from app.core.models import Product


class AbstractProductRepository(ABC):
    """Abstract base class for product repository operations."""

    @abstractmethod
    async def get_products_by_store(self, store_id: UUID) -> list[Product]:
        """Get all products for a store."""
        raise NotImplementedError('Subclass must implement get_products_by_store')

    @abstractmethod
    async def search_products(self, query: str) -> list[Product]:
        """Search for products by name."""
        raise NotImplementedError('Subclass must implement search_products')

    @abstractmethod
    async def get_product_by_id(self, product_id: UUID) -> Product | None:
        """Get product by ID."""
        raise NotImplementedError('Subclass must implement get_product_by_id')

    @abstractmethod
    async def create_product(
        self, name: str, brand: str | None = None, unit: str | None = None
    ) -> Product:
        """Create a new product (store-agnostic)."""
        raise NotImplementedError('Subclass must implement create_product')

    @abstractmethod
    async def get_all_products(self) -> list[Product]:
        """Get all products."""
        raise NotImplementedError('Subclass must implement get_all_products')

    @abstractmethod
    async def update_product(self, product_id: UUID, **fields) -> Product | None:
        """Update product fields. Returns updated product or None if not found."""
        raise NotImplementedError('Subclass must implement update_product')

    @abstractmethod
    async def delete_product(self, product_id: UUID) -> bool:
        """Delete a product. Returns True if deleted, False if not found."""
        raise NotImplementedError('Subclass must implement delete_product')

    @abstractmethod
    async def get_product_availabilities(self, product_id: UUID, store_id: UUID = None) -> list:
        """Get product availabilities, optionally filtered by store."""
        raise NotImplementedError('Subclass must implement get_product_availabilities')

    @abstractmethod
    async def create_product_availability(
        self,
        product_id: UUID,
        store_id: UUID,
        price: float | None = None,
        notes: str = '',
        minimum_quantity: int | None = None,
        user_id: UUID = None,
    ) -> Any:
        """Create or update a product availability at a store."""
        raise NotImplementedError('Subclass must implement create_product_availability')

    @abstractmethod
    async def get_availability_by_product_and_store(self, product_id: UUID, store_id: UUID) -> Any | None:
        """Get a specific product availability by product and store."""
        raise NotImplementedError('Subclass must implement get_availability_by_product_and_store')

    @abstractmethod
    async def update_product_availability_price(
        self, availability_id: UUID, price: float, notes: str = ''
    ) -> Any:
        """Update the price for an existing product availability."""
        raise NotImplementedError('Subclass must implement update_product_availability_price')

    @abstractmethod
    async def bulk_update_product_bids(self, old_product_id: UUID, new_product_id: UUID) -> int:
        """Update all product bids from old product to new product. Returns count of updated records."""
        raise NotImplementedError('Subclass must implement bulk_update_product_bids')

    @abstractmethod
    async def bulk_update_product_availabilities(self, old_product_id: UUID, new_product_id: UUID) -> int:
        """Update all product availabilities from old product to new product. Returns count of updated records."""
        raise NotImplementedError('Subclass must implement bulk_update_product_availabilities')

    @abstractmethod
    async def bulk_update_shopping_list_items(self, old_product_id: UUID, new_product_id: UUID) -> int:
        """Update all shopping list items from old product to new product. Returns count of updated records."""
        raise NotImplementedError('Subclass must implement bulk_update_shopping_list_items')

    @abstractmethod
    async def count_product_bids(self, product_id: UUID) -> int:
        """Count how many bids reference this product."""
        raise NotImplementedError('Subclass must implement count_product_bids')
