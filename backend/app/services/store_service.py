"""Store service for handling store-related business logic."""

from typing import List, Optional, Dict, Any
from uuid import UUID
from ..models import Store, Product, Run
from .base_service import BaseService
from ..exceptions import ValidationError, NotFoundError


class StoreService(BaseService):
    """Service for store operations."""

    def get_all_stores(self) -> List[Store]:
        """Get all available stores."""
        return self.repo.get_all_stores()

    def create_store(self, name: str) -> Store:
        """Create a new store."""
        if not name or not name.strip():
            raise ValidationError("Store name cannot be empty")
        return self.repo.create_store(name.strip())

    def get_store_by_id(self, store_id: UUID) -> Store:
        """Get store by ID."""
        store = self.repo.get_store_by_id(store_id)
        if not store:
            raise NotFoundError(f"Store with ID {store_id} not found")
        return store

    def get_store_page_data(self, store_id: UUID, user_id: UUID) -> Dict[str, Any]:
        """Get all data needed for the store page."""
        store = self.get_store_by_id(store_id)
        products = self.repo.get_products_by_store_from_encountered_prices(store_id)
        active_runs = self.repo.get_active_runs_by_store_for_user(store_id, user_id)

        return {
            "store": store,
            "products": products,
            "active_runs": active_runs
        }
