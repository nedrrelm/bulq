"""Abstract seller repository interface."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.core.models import Seller


class AbstractSellerRepository(ABC):
    """Abstract base class for seller repository operations."""

    @abstractmethod
    async def create_seller(self, seller: Seller) -> Seller:
        """Create a new seller."""
        raise NotImplementedError

    @abstractmethod
    async def get_seller_by_id(self, seller_id: UUID) -> Seller | None:
        """Get seller by ID."""
        raise NotImplementedError

    @abstractmethod
    async def get_seller_by_user_id(self, user_id: UUID) -> Seller | None:
        """Get seller by user ID (1-1 relationship)."""
        raise NotImplementedError

    @abstractmethod
    async def get_seller_by_invite_token(self, invite_token: str) -> Seller | None:
        """Get seller by invite token."""
        raise NotImplementedError

    @abstractmethod
    async def update_seller(self, seller_id: UUID, **fields) -> Seller | None:
        """Update seller fields. Returns updated seller or None if not found."""
        raise NotImplementedError

    @abstractmethod
    async def search_sellers(self, query: str, limit: int = 20) -> list[Seller]:
        """Search sellers by display name. Only returns searchable sellers."""
        raise NotImplementedError
