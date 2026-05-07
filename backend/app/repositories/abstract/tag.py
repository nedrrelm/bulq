"""Abstract tag repository interface."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.core.models import Product, Tag


class AbstractTagRepository(ABC):
    """Abstract base class for tag repository operations."""

    @abstractmethod
    async def get_tag_by_id(self, tag_id: UUID) -> Tag | None:
        """Get tag by ID."""
        raise NotImplementedError('Subclass must implement get_tag_by_id')

    @abstractmethod
    async def get_all_tags(self) -> list[Tag]:
        """Get all tags."""
        raise NotImplementedError('Subclass must implement get_all_tags')

    @abstractmethod
    async def search_tags(
        self,
        query: str,
        tag_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Tag]:
        """Search for tags by value, optionally filtered by type."""
        raise NotImplementedError('Subclass must implement search_tags')

    @abstractmethod
    async def get_tag_by_value_and_type(self, value: str, tag_type: str) -> Tag | None:
        """Get a tag by its value and type. Used for duplicate checking."""
        raise NotImplementedError('Subclass must implement get_tag_by_value_and_type')

    @abstractmethod
    async def create_tag(
        self,
        value: str,
        tag_type: str,
        created_by: UUID | None = None,
    ) -> Tag:
        """Create a new tag."""
        raise NotImplementedError('Subclass must implement create_tag')

    @abstractmethod
    async def update_tag(self, tag_id: UUID, **fields) -> Tag | None:
        """Update tag fields. Returns updated tag or None if not found."""
        raise NotImplementedError('Subclass must implement update_tag')

    @abstractmethod
    async def delete_tag(self, tag_id: UUID) -> bool:
        """Delete a tag. Returns True if deleted, False if not found."""
        raise NotImplementedError('Subclass must implement delete_tag')

    @abstractmethod
    async def get_tags_by_product(self, product_id: UUID) -> list[Tag]:
        """Get all tags for a product."""
        raise NotImplementedError('Subclass must implement get_tags_by_product')

    @abstractmethod
    async def add_tag_to_product(self, product_id: UUID, tag_id: UUID) -> None:
        """Add a tag to a product."""
        raise NotImplementedError('Subclass must implement add_tag_to_product')

    @abstractmethod
    async def remove_tag_from_product(self, product_id: UUID, tag_id: UUID) -> None:
        """Remove a tag from a product."""
        raise NotImplementedError('Subclass must implement remove_tag_from_product')

    @abstractmethod
    async def is_tag_on_product(self, product_id: UUID, tag_id: UUID) -> bool:
        """Check if a tag is already on a product."""
        raise NotImplementedError('Subclass must implement is_tag_on_product')

    @abstractmethod
    async def get_products_by_tag(
        self, tag_id: UUID, limit: int = 50, offset: int = 0
    ) -> list[Product]:
        """Get all products with a given tag."""
        raise NotImplementedError('Subclass must implement get_products_by_tag')

    @abstractmethod
    async def bulk_update_product_tags(self, old_tag_id: UUID, new_tag_id: UUID) -> int:
        """Move all product-tag links from old tag to new tag. Returns count of updated records."""
        raise NotImplementedError('Subclass must implement bulk_update_product_tags')

    @abstractmethod
    async def count_tag_products(self, tag_id: UUID) -> int:
        """Count how many products have this tag."""
        raise NotImplementedError('Subclass must implement count_tag_products')
