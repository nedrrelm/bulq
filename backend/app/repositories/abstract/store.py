"""Abstract store repository interface."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.core.models import Product, Run, Store


class AbstractStoreRepository(ABC):
    """Abstract base class for store repository operations."""

    @abstractmethod
    async def search_stores(self, query: str) -> list[Store]:
        """Search stores by name."""
        raise NotImplementedError('Subclass must implement search_stores')

    @abstractmethod
    async def get_all_stores(self, limit: int = None, offset: int = 0) -> list[Store]:
        """Get all stores (optionally paginated)."""
        raise NotImplementedError('Subclass must implement get_all_stores')

    @abstractmethod
    async def create_store(self, name: str) -> Store:
        """Create a new store."""
        raise NotImplementedError('Subclass must implement create_store')

    @abstractmethod
    async def get_store_by_id(self, store_id: UUID) -> Store | None:
        """Get store by ID."""
        raise NotImplementedError('Subclass must implement get_store_by_id')

    @abstractmethod
    async def get_products_by_store_from_availabilities(self, store_id: UUID) -> list[Product]:
        """Get all unique products that are available at a store."""
        raise NotImplementedError(
            'Subclass must implement get_products_by_store_from_availabilities'
        )

    @abstractmethod
    async def get_active_runs_by_store_for_user(self, store_id: UUID, user_id: UUID) -> list[Run]:
        """Get all active runs for a store across all user's groups."""
        raise NotImplementedError('Subclass must implement get_active_runs_by_store_for_user')

    @abstractmethod
    async def update_store(self, store_id: UUID, **fields) -> Store | None:
        """Update store fields. Returns updated store or None if not found."""
        raise NotImplementedError('Subclass must implement update_store')

    @abstractmethod
    async def delete_store(self, store_id: UUID) -> bool:
        """Delete a store. Returns True if deleted, False if not found."""
        raise NotImplementedError('Subclass must implement delete_store')

    @abstractmethod
    async def bulk_update_runs(self, old_store_id: UUID, new_store_id: UUID) -> int:
        """Update all runs from old store to new store. Returns count of updated records."""
        raise NotImplementedError('Subclass must implement bulk_update_runs')

    @abstractmethod
    async def bulk_update_store_availabilities(self, old_store_id: UUID, new_store_id: UUID) -> int:
        """Update all store availabilities from old store to new store. Returns count of updated records."""
        raise NotImplementedError('Subclass must implement bulk_update_store_availabilities')

    @abstractmethod
    async def count_store_runs(self, store_id: UUID) -> int:
        """Count how many runs reference this store."""
        raise NotImplementedError('Subclass must implement count_store_runs')
