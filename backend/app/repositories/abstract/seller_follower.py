"""Abstract seller follower repository interface."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.core.models import SellerFollower


class AbstractSellerFollowerRepository(ABC):
    """Abstract base class for seller follower repository operations."""

    @abstractmethod
    async def create_follower(self, seller_follower: SellerFollower) -> SellerFollower:
        """Create a new seller follower record."""
        raise NotImplementedError

    @abstractmethod
    async def delete_follower(self, seller_id: UUID, group_id: UUID) -> bool:
        """Delete a follower record. Returns True if deleted."""
        raise NotImplementedError

    @abstractmethod
    async def get_follower(self, seller_id: UUID, group_id: UUID) -> SellerFollower | None:
        """Get a specific follower record."""
        raise NotImplementedError

    @abstractmethod
    async def get_followers_by_seller(self, seller_id: UUID) -> list[SellerFollower]:
        """Get all groups following a seller."""
        raise NotImplementedError

    @abstractmethod
    async def get_followed_sellers_by_group(self, group_id: UUID) -> list[SellerFollower]:
        """Get all sellers followed by a group."""
        raise NotImplementedError
