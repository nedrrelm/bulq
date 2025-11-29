"""Database store repository implementation."""

from uuid import UUID

from sqlalchemy import and_, distinct
from sqlalchemy.orm import Session

from app.core.models import Product, ProductAvailability, Run, Store
from app.core.run_state import RunState
from app.repositories.abstract.store import AbstractStoreRepository


class DatabaseStoreRepository(AbstractStoreRepository):
    """Database implementation of store repository."""

    def __init__(self, db: Session):
        self.db = db

    def search_stores(self, query: str) -> list[Store]:
        """Search stores by name."""
        return self.db.query(Store).filter(Store.name.ilike(f'%{query}%')).all()

    def get_all_stores(self, limit: int = None, offset: int = 0) -> list[Store]:
        """Get all stores (optionally paginated)."""
        query = self.db.query(Store).order_by(Store.name)
        if limit is not None:
            query = query.limit(limit).offset(offset)
        return query.all()

    def create_store(self, name: str) -> Store:
        """Create a new store."""
        store = Store(name=name)
        self.db.add(store)
        self.db.commit()
        self.db.refresh(store)
        return store

    def get_store_by_id(self, store_id: UUID) -> Store | None:
        """Get store by ID."""
        return self.db.query(Store).filter(Store.id == store_id).first()

    def get_products_by_store_from_availabilities(self, store_id: UUID) -> list[Product]:
        """Get all unique products that are available at a store."""
        product_ids = (
            self.db.query(distinct(ProductAvailability.product_id))
            .filter(ProductAvailability.store_id == store_id)
            .all()
        )
        product_ids = [pid[0] for pid in product_ids]
        return self.db.query(Product).filter(Product.id.in_(product_ids)).all()

    def get_active_runs_by_store_for_user(self, store_id: UUID, user_id: UUID) -> list[Run]:
        """Get all active runs for a store across all user's groups."""
        from sqlalchemy import select

        from app.core.models import group_membership

        active_states = [
            RunState.PLANNING,
            RunState.ACTIVE,
            RunState.CONFIRMED,
            RunState.SHOPPING,
            RunState.ADJUSTING,
            RunState.DISTRIBUTING,
        ]

        # Get user's group IDs
        user_group_ids = (
            self.db.execute(
                select(group_membership.c.group_id).where(group_membership.c.user_id == user_id)
            )
            .scalars()
            .all()
        )

        # Get runs for those groups that target this store and are active
        return (
            self.db.query(Run)
            .filter(
                and_(
                    Run.store_id == store_id,
                    Run.state.in_(active_states),
                    Run.group_id.in_(user_group_ids),
                )
            )
            .all()
        )

    def update_store(self, store_id: UUID, **fields) -> Store | None:
        """Update store fields. Returns updated store or None if not found."""
        store = self.db.query(Store).filter(Store.id == store_id).first()
        if not store:
            return None

        for key, value in fields.items():
            if hasattr(store, key):
                setattr(store, key, value)

        self.db.commit()
        self.db.refresh(store)
        return store

    def delete_store(self, store_id: UUID) -> bool:
        """Delete a store. Returns True if deleted, False if not found."""
        store = self.db.query(Store).filter(Store.id == store_id).first()
        if not store:
            return False

        self.db.delete(store)
        self.db.commit()
        return True

    def bulk_update_runs(self, old_store_id: UUID, new_store_id: UUID) -> int:
        """Update all runs from old store to new store. Returns count of updated records."""
        result = (
            self.db.query(Run)
            .filter(Run.store_id == old_store_id)
            .update({Run.store_id: new_store_id})
        )
        self.db.commit()
        return result

    def bulk_update_store_availabilities(self, old_store_id: UUID, new_store_id: UUID) -> int:
        """Update all store availabilities from old store to new store. Returns count of updated records."""
        result = (
            self.db.query(ProductAvailability)
            .filter(ProductAvailability.store_id == old_store_id)
            .update({ProductAvailability.store_id: new_store_id})
        )
        self.db.commit()
        return result

    def count_store_runs(self, store_id: UUID) -> int:
        """Count how many runs reference this store."""
        return self.db.query(Run).filter(Run.store_id == store_id).count()
