"""Store service for handling store-related business logic."""

from typing import Optional, Any
from uuid import UUID
from ..models import Store, Product, Run
from .base_service import BaseService
from ..exceptions import ValidationError, NotFoundError


class StoreService(BaseService):
    """Service for store operations."""

    def get_all_stores(self, limit: int = 100, offset: int = 0) -> list[Store]:
        """Get all available stores (paginated)."""
        return self.repo.get_all_stores(limit, offset)

    def create_store(self, name: str) -> Store:
        """Create a new store."""
        if not name or not name.strip():
            raise ValidationError("Store name cannot be empty")
        return self.repo.create_store(name.strip())

    def get_store_by_id(self, store_id: UUID) -> Store:
        """Get store by ID."""
        store = self.repo.get_store_by_id(store_id)
        if not store:
            raise NotFoundError("Store", store_id)
        return store

    def get_store_page_data(self, store_id: UUID, user_id: UUID) -> dict[str, Any]:
        """
        Get all data needed for the store page with fully formatted response.

        Returns:
            Dict with store info, products with prices, and active runs with full details
        """
        store = self.get_store_by_id(store_id)
        products = self.repo.get_products_by_store_from_availabilities(store_id)
        active_runs = self.repo.get_active_runs_by_store_for_user(store_id, user_id)

        # Format products with availability prices
        products_response = []
        for p in products:
            availability = self.repo.get_availability_by_product_and_store(p.id, store_id)
            current_price = str(availability.price) if availability and availability.price else None

            products_response.append({
                "id": str(p.id),
                "name": p.name,
                "brand": p.brand,
                "unit": p.unit,
                "current_price": current_price
            })

        # Format active runs with complete details
        runs_response = []
        for r in active_runs:
            group = self.repo.get_group_by_id(r.group_id)
            store_obj = self.repo.get_store_by_id(r.store_id)

            # Get leader from participations
            participations = self.repo.get_run_participations(r.id)
            leader = next((p for p in participations if p.is_leader), None)
            leader_name = leader.user.name if leader and leader.user else "Unknown"

            runs_response.append({
                "id": str(r.id),
                "state": r.state,
                "group_id": str(r.group_id),
                "group_name": group.name if group else "Unknown",
                "store_name": store_obj.name if store_obj else "Unknown",
                "leader_name": leader_name,
                "planned_on": r.planned_on.isoformat() if r.planned_on else None
            })

        return {
            "store": {
                "id": str(store.id),
                "name": store.name
            },
            "products": products_response,
            "active_runs": runs_response
        }
