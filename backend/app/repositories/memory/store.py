"""Memory store repository implementation."""

from uuid import UUID, uuid4

from app.core.models import Product, Run, Store
from app.core.run_state import RunState
from app.repositories.abstract.store import AbstractStoreRepository
from app.repositories.memory.storage import MemoryStorage


class MemoryStoreRepository(AbstractStoreRepository):
    """Memory implementation of store repository."""

    def __init__(self, storage: MemoryStorage):
        self.storage = storage

    async def search_stores(self, query: str) -> list[Store]:
        query_lower = query.lower()
        return [store for store in self.storage.stores.values() if query_lower in store.name.lower()]

    async def get_all_stores(self, limit: int = None, offset: int = 0) -> list[Store]:
        stores = list(self.storage.stores.values())
        stores.sort(key=lambda s: s.name)
        if limit is not None:
            return stores[offset : offset + limit]
        return stores

    async def create_store(self, name: str) -> Store:
        """Create a new store."""
        store = Store(id=uuid4(), name=name, verified=False)
        self.storage.stores[store.id] = store
        return store

    async def get_store_by_id(self, store_id: UUID) -> Store | None:
        return self.storage.stores.get(store_id)

    async def get_products_by_store_from_availabilities(self, store_id: UUID) -> list[Product]:
        """Get all unique products that are available at a store."""
        product_ids = {
            avail.product_id
            for avail in self.storage.product_availabilities.values()
            if avail.store_id == store_id
        }
        return [product for product in self.storage.products.values() if product.id in product_ids]

    async def get_active_runs_by_store_for_user(self, store_id: UUID, user_id: UUID) -> list[Run]:
        """Get all active runs for a store across all user's groups."""
        user_group_ids = []
        for group_id, member_ids in self.storage.group_memberships.items():
            if user_id in member_ids:
                user_group_ids.append(group_id)

        active_states = [
            RunState.PLANNING,
            RunState.ACTIVE,
            RunState.CONFIRMED,
            RunState.SHOPPING,
            RunState.ADJUSTING,
            RunState.DISTRIBUTING,
        ]
        runs = []
        for run in self.storage.runs.values():
            if (
                run.store_id == store_id
                and run.state in active_states
                and run.group_id in user_group_ids
            ):
                runs.append(run)
        return runs

    async def update_store(self, store_id: UUID, **fields) -> Store | None:
        """Update store fields. Returns updated store or None if not found."""
        store = self.storage.stores.get(store_id)
        if not store:
            return None

        for key, value in fields.items():
            if hasattr(store, key):
                setattr(store, key, value)

        return store

    async def delete_store(self, store_id: UUID) -> bool:
        """Delete a store. Returns True if deleted, False if not found."""
        if store_id not in self.storage.stores:
            return False

        del self.storage.stores[store_id]
        return True

    async def bulk_update_runs(self, old_store_id: UUID, new_store_id: UUID) -> int:
        """Update all runs from old store to new store. Returns count of updated records."""
        count = 0
        for run in self.storage.runs.values():
            if run.store_id == old_store_id:
                run.store_id = new_store_id
                count += 1
        return count

    async def bulk_update_store_availabilities(self, old_store_id: UUID, new_store_id: UUID) -> int:
        """Update all store availabilities from old store to new store. Returns count of updated records."""
        count = 0
        for avail in self.storage.product_availabilities.values():
            if avail.store_id == old_store_id:
                avail.store_id = new_store_id
                count += 1
        return count

    async def count_store_runs(self, store_id: UUID) -> int:
        """Count how many runs reference this store."""
        return sum(1 for run in self.storage.runs.values() if run.store_id == store_id)
