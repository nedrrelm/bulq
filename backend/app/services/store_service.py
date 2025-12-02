"""Store service for handling store-related business logic."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import StorePageResponse, StoreProductResponse, StoreResponse, StoreRunResponse
from app.core.error_codes import STORE_NAME_EMPTY, STORE_NOT_FOUND
from app.core.exceptions import NotFoundError, ValidationError
from app.core.models import Store
from app.repositories import (
    get_group_repository,
    get_product_repository,
    get_run_repository,
    get_store_repository,
    get_user_repository,
)

from .base_service import BaseService


class StoreService(BaseService):
    """Service for store operations."""

    def __init__(self, db: AsyncSession):
        """Initialize service with necessary repositories."""
        super().__init__(db)
        self.group_repo = get_group_repository(db)
        self.product_repo = get_product_repository(db)
        self.run_repo = get_run_repository(db)
        self.user_repo = get_user_repository(db)
        self.store_repo = get_store_repository(db)

    async def get_all_stores(self, limit: int = 100, offset: int = 0) -> list[Store]:
        """Get all available stores (paginated)."""
        return await self.store_repo.get_all_stores(limit, offset)

    async def get_similar_stores(self, name: str, limit: int = 5) -> list[Store]:
        """Get stores with similar names for duplicate detection.

        Uses case-insensitive search to find stores with names similar to the input.
        Returns up to `limit` results, ordered by similarity.
        """
        if not name or not name.strip():
            return []

        # Use the search_stores method which does case-insensitive matching
        results = await self.store_repo.search_stores(name.strip())

        # Limit results
        return results[:limit]

    async def create_store(self, name: str) -> Store:
        """Create a new store."""
        if not name or not name.strip():
            raise ValidationError(code=STORE_NAME_EMPTY, message='Store name cannot be empty')
        return await self.store_repo.create_store(name.strip())

    async def get_store_by_id(self, store_id: UUID) -> Store:
        """Get store by ID."""
        store = await self.store_repo.get_store_by_id(store_id)
        if not store:
            raise NotFoundError(
                code=STORE_NOT_FOUND, message='Store not found', store_id=str(store_id)
            )
        return store

    async def get_store_page_data(self, store_id: UUID, user_id: UUID) -> StorePageResponse:
        """Get all data needed for the store page with fully formatted response.

        Returns:
            StorePageResponse with store info, products with prices, and active runs with full details
        """
        store = await self.get_store_by_id(store_id)
        products = await self.store_repo.get_products_by_store_from_availabilities(store_id)
        active_runs = await self.store_repo.get_active_runs_by_store_for_user(store_id, user_id)

        # Format products with availability prices
        products_response = []
        for p in products:
            availability = await self.product_repo.get_availability_by_product_and_store(p.id, store_id)
            current_price = str(availability.price) if availability and availability.price else None

            products_response.append(
                StoreProductResponse(
                    id=str(p.id),
                    name=p.name,
                    brand=p.brand,
                    unit=p.unit,
                    current_price=current_price,
                )
            )

        # Format active runs with complete details
        runs_response = []
        for r in active_runs:
            group = await self.group_repo.get_group_by_id(r.group_id)
            store_obj = await self.store_repo.get_store_by_id(r.store_id)

            # Get leader from participations
            participations = await self.run_repo.get_run_participations(r.id)
            leader = next((p for p in participations if p.is_leader), None)
            if leader:
                leader_user = await self.user_repo.get_user_by_id(leader.user_id)
                leader_name = leader_user.name if leader_user else 'Unknown'
            else:
                leader_name = 'Unknown'

            runs_response.append(
                StoreRunResponse(
                    id=str(r.id),
                    state=r.state,
                    group_id=str(r.group_id),
                    group_name=group.name if group else 'Unknown',
                    store_name=store_obj.name if store_obj else 'Unknown',
                    leader_name=leader_name,
                    planned_on=r.planned_on.isoformat() if r.planned_on else None,
                )
            )

        return StorePageResponse(
            store=StoreResponse(id=str(store.id), name=store.name),
            products=products_response,
            active_runs=runs_response,
        )
