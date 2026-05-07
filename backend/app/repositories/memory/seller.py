"""Memory seller repository implementation."""

from uuid import UUID

from app.core.models import Seller
from app.repositories.abstract.seller import AbstractSellerRepository
from app.repositories.memory.storage import MemoryStorage


class MemorySellerRepository(AbstractSellerRepository):
    """Memory implementation of seller repository."""

    def __init__(self, storage: MemoryStorage):
        self.storage = storage

    async def create_seller(self, seller: Seller) -> Seller:
        """Create a new seller."""
        self.storage.sellers[seller.id] = seller
        return seller

    async def get_seller_by_id(self, seller_id: UUID) -> Seller | None:
        """Get seller by ID."""
        return self.storage.sellers.get(seller_id)

    async def get_seller_by_user_id(self, user_id: UUID) -> Seller | None:
        """Get seller by user ID."""
        for seller in self.storage.sellers.values():
            if seller.user_id == user_id:
                return seller
        return None

    async def get_seller_by_invite_token(self, invite_token: str) -> Seller | None:
        """Get seller by invite token."""
        for seller in self.storage.sellers.values():
            if seller.invite_token == invite_token:
                return seller
        return None

    async def update_seller(self, seller_id: UUID, **fields) -> Seller | None:
        """Update seller fields."""
        seller = self.storage.sellers.get(seller_id)
        if not seller:
            return None

        for key, value in fields.items():
            if hasattr(seller, key):
                setattr(seller, key, value)

        return seller

    async def get_seller_by_store_id(self, store_id: UUID) -> Seller | None:
        """Get seller by their linked store ID."""
        for seller in self.storage.sellers.values():
            if seller.store_id == store_id:
                return seller
        return None

    async def search_sellers(self, query: str, limit: int = 20) -> list[Seller]:
        """Search sellers by display name. Only returns searchable sellers."""
        query_lower = query.lower()
        results = [
            seller
            for seller in self.storage.sellers.values()
            if seller.is_searchable and query_lower in seller.display_name.lower()
        ]
        return results[:limit]
