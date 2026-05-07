"""Memory seller follower repository implementation."""

from uuid import UUID

from app.core.models import SellerFollower
from app.repositories.abstract.seller_follower import AbstractSellerFollowerRepository
from app.repositories.memory.storage import MemoryStorage


class MemorySellerFollowerRepository(AbstractSellerFollowerRepository):
    """Memory implementation of seller follower repository."""

    def __init__(self, storage: MemoryStorage):
        self.storage = storage

    async def create_follower(self, seller_follower: SellerFollower) -> SellerFollower:
        """Create a new seller follower record."""
        self.storage.seller_followers[seller_follower.id] = seller_follower
        return seller_follower

    async def delete_follower(self, seller_id: UUID, group_id: UUID) -> bool:
        """Delete a follower record."""
        to_delete = None
        for fid, f in self.storage.seller_followers.items():
            if f.seller_id == seller_id and f.group_id == group_id:
                to_delete = fid
                break
        if to_delete:
            del self.storage.seller_followers[to_delete]
            return True
        return False

    async def get_follower(self, seller_id: UUID, group_id: UUID) -> SellerFollower | None:
        """Get a specific follower record."""
        for f in self.storage.seller_followers.values():
            if f.seller_id == seller_id and f.group_id == group_id:
                return f
        return None

    async def get_followers_by_seller(self, seller_id: UUID) -> list[SellerFollower]:
        """Get all groups following a seller."""
        return [f for f in self.storage.seller_followers.values() if f.seller_id == seller_id]

    async def get_followed_sellers_by_group(self, group_id: UUID) -> list[SellerFollower]:
        """Get all sellers followed by a group."""
        return [f for f in self.storage.seller_followers.values() if f.group_id == group_id]
