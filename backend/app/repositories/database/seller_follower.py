"""Database seller follower repository implementation."""

from uuid import UUID

from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.models import SellerFollower
from app.repositories.abstract.seller_follower import AbstractSellerFollowerRepository


class DatabaseSellerFollowerRepository(AbstractSellerFollowerRepository):
    """Database implementation of seller follower repository."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_follower(self, seller_follower: SellerFollower) -> SellerFollower:
        """Create a new seller follower record."""
        self.db.add(seller_follower)
        await self.db.commit()
        await self.db.refresh(seller_follower)
        return seller_follower

    async def delete_follower(self, seller_id: UUID, group_id: UUID) -> bool:
        """Delete a follower record."""
        result = await self.db.execute(
            delete(SellerFollower).where(
                and_(
                    SellerFollower.seller_id == seller_id,
                    SellerFollower.group_id == group_id,
                )
            )
        )
        await self.db.commit()
        return result.rowcount > 0

    async def get_follower(self, seller_id: UUID, group_id: UUID) -> SellerFollower | None:
        """Get a specific follower record."""
        result = await self.db.execute(
            select(SellerFollower).where(
                and_(
                    SellerFollower.seller_id == seller_id,
                    SellerFollower.group_id == group_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_followers_by_seller(self, seller_id: UUID) -> list[SellerFollower]:
        """Get all groups following a seller."""
        result = await self.db.execute(
            select(SellerFollower)
            .where(SellerFollower.seller_id == seller_id)
            .options(joinedload(SellerFollower.group))
            .order_by(SellerFollower.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_followed_sellers_by_group(self, group_id: UUID) -> list[SellerFollower]:
        """Get all sellers followed by a group."""
        result = await self.db.execute(
            select(SellerFollower)
            .where(SellerFollower.group_id == group_id)
            .options(joinedload(SellerFollower.seller))
            .order_by(SellerFollower.created_at.desc())
        )
        return list(result.scalars().all())
