"""Abstract bid repository interface."""

from abc import ABC, abstractmethod
from decimal import Decimal
from uuid import UUID

from app.core.models import ProductBid


class AbstractBidRepository(ABC):
    """Abstract base class for bid repository operations."""

    @abstractmethod
    async def get_bids_by_run(self, run_id: UUID) -> list[ProductBid]:
        """Get all bids for a run."""
        raise NotImplementedError('Subclass must implement get_bids_by_run')

    @abstractmethod
    async def get_bids_by_run_with_participations(self, run_id: UUID) -> list[ProductBid]:
        """Get all bids for a run with participation and user data eagerly loaded.

        This avoids N+1 query problems when you need to access bid.participation.user.
        Each bid will have its participation object populated, and each participation
        will have its user object populated.
        """
        raise NotImplementedError('Subclass must implement get_bids_by_run_with_participations')

    @abstractmethod
    async def create_or_update_bid(
        self,
        participation_id: UUID,
        product_id: UUID,
        quantity: int,
        interested_only: bool,
        comment: str | None = None,
    ) -> ProductBid:
        """Create or update a product bid."""
        raise NotImplementedError('Subclass must implement create_or_update_bid')

    @abstractmethod
    async def delete_bid(self, participation_id: UUID, product_id: UUID) -> bool:
        """Delete a product bid."""
        raise NotImplementedError('Subclass must implement delete_bid')

    @abstractmethod
    async def get_bid(self, participation_id: UUID, product_id: UUID) -> ProductBid | None:
        """Get a specific bid."""
        raise NotImplementedError('Subclass must implement get_bid')

    @abstractmethod
    async def get_bid_by_id(self, bid_id: UUID) -> ProductBid | None:
        """Get a bid by its ID."""
        raise NotImplementedError('Subclass must implement get_bid_by_id')

    @abstractmethod
    async def get_bids_by_participation(self, participation_id: UUID) -> list[ProductBid]:
        """Get all bids for a participation."""
        raise NotImplementedError('Subclass must implement get_bids_by_participation')

    @abstractmethod
    async def update_bid_distributed_quantities(
        self, bid_id: UUID, quantity: float, price_per_unit: Decimal
    ) -> None:
        """Update the distributed quantity and price for a bid."""
        raise NotImplementedError('Subclass must implement update_bid_distributed_quantities')

    @abstractmethod
    async def commit_changes(self) -> None:
        """Commit any pending changes (no-op for memory repository, commits transaction for database repository)."""
        raise NotImplementedError('Subclass must implement commit_changes')
