"""Database store repository implementation."""

from uuid import UUID

from sqlalchemy import and_, distinct, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Product, ProductAvailability, Run, Store, group_membership
from app.core.run_state import RunState
from app.repositories.abstract.store import AbstractStoreRepository


class DatabaseStoreRepository(AbstractStoreRepository):
    """Database implementation of store repository."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def search_stores(self, query: str) -> list[Store]:
        """Search stores by name."""
        result = await self.db.execute(select(Store).filter(Store.name.ilike(f'%{query}%')))
        return list(result.scalars().all())

    async def get_all_stores(self, limit: int = None, offset: int = 0) -> list[Store]:
        """Get all stores (optionally paginated)."""
        query = select(Store).order_by(Store.name)
        if limit is not None:
            query = query.limit(limit).offset(offset)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_store(self, name: str) -> Store:
        """Create a new store."""
        store = Store(name=name)
        self.db.add(store)
        await self.db.commit()
        await self.db.refresh(store)
        return store

    async def get_store_by_id(self, store_id: UUID) -> Store | None:
        """Get store by ID."""
        result = await self.db.execute(select(Store).filter(Store.id == store_id))
        return result.scalar_one_or_none()

    async def get_products_by_store_from_availabilities(self, store_id: UUID) -> list[Product]:
        """Get all unique products that are available at a store."""
        result = await self.db.execute(
            select(distinct(ProductAvailability.product_id)).filter(
                ProductAvailability.store_id == store_id
            )
        )
        product_ids = [pid[0] for pid in result.all()]
        
        if not product_ids:
            return []
        
        result = await self.db.execute(select(Product).filter(Product.id.in_(product_ids)))
        return list(result.scalars().all())

    async def get_active_runs_by_store_for_user(self, store_id: UUID, user_id: UUID) -> list[Run]:
        """Get all active runs for a store across all user's groups."""
        active_states = [
            RunState.PLANNING,
            RunState.ACTIVE,
            RunState.CONFIRMED,
            RunState.SHOPPING,
            RunState.ADJUSTING,
            RunState.DISTRIBUTING,
        ]

        # Get user's group IDs
        result = await self.db.execute(
            select(group_membership.c.group_id).where(group_membership.c.user_id == user_id)
        )
        user_group_ids = list(result.scalars().all())

        if not user_group_ids:
            return []

        # Get runs for those groups that target this store and are active
        result = await self.db.execute(
            select(Run).filter(
                and_(
                    Run.store_id == store_id,
                    Run.state.in_(active_states),
                    Run.group_id.in_(user_group_ids),
                )
            )
        )
        return list(result.scalars().all())

    async def update_store(self, store_id: UUID, **fields) -> Store | None:
        """Update store fields. Returns updated store or None if not found."""
        result = await self.db.execute(select(Store).filter(Store.id == store_id))
        store = result.scalar_one_or_none()
        if not store:
            return None

        for key, value in fields.items():
            if hasattr(store, key):
                setattr(store, key, value)

        await self.db.commit()
        await self.db.refresh(store)
        return store

    async def delete_store(self, store_id: UUID) -> bool:
        """Delete a store. Returns True if deleted, False if not found."""
        result = await self.db.execute(select(Store).filter(Store.id == store_id))
        store = result.scalar_one_or_none()
        if not store:
            return False

        self.db.delete(store)
        await self.db.commit()
        return True

    async def bulk_update_runs(self, old_store_id: UUID, new_store_id: UUID) -> int:
        """Update all runs from old store to new store. Returns count of updated records."""
        result = await self.db.execute(
            update(Run).filter(Run.store_id == old_store_id).values(store_id=new_store_id)
        )
        await self.db.commit()
        return result.rowcount

    async def bulk_update_store_availabilities(self, old_store_id: UUID, new_store_id: UUID) -> int:
        """Update all store availabilities from old store to new store. Returns count of updated records."""
        result = await self.db.execute(
            update(ProductAvailability)
            .filter(ProductAvailability.store_id == old_store_id)
            .values(store_id=new_store_id)
        )
        await self.db.commit()
        return result.rowcount

    async def count_store_runs(self, store_id: UUID) -> int:
        """Count how many runs reference this store."""
        result = await self.db.execute(
            select(func.count()).select_from(Run).filter(Run.store_id == store_id)
        )
        return result.scalar() or 0
