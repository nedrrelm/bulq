"""Database seller repository implementation."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.models import Seller
from app.repositories.abstract.seller import AbstractSellerRepository


class DatabaseSellerRepository(AbstractSellerRepository):
    """Database implementation of seller repository."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_seller(self, seller: Seller) -> Seller:
        """Create a new seller."""
        self.db.add(seller)
        await self.db.commit()
        await self.db.refresh(seller)
        return seller

    async def get_seller_by_id(self, seller_id: UUID) -> Seller | None:
        """Get seller by ID."""
        result = await self.db.execute(
            select(Seller)
            .where(Seller.id == seller_id)
            .options(joinedload(Seller.user), joinedload(Seller.store))
        )
        return result.scalar_one_or_none()

    async def get_seller_by_user_id(self, user_id: UUID) -> Seller | None:
        """Get seller by user ID."""
        result = await self.db.execute(
            select(Seller)
            .where(Seller.user_id == user_id)
            .options(joinedload(Seller.user), joinedload(Seller.store))
        )
        return result.scalar_one_or_none()

    async def get_seller_by_invite_token(self, invite_token: str) -> Seller | None:
        """Get seller by invite token."""
        result = await self.db.execute(
            select(Seller)
            .where(Seller.invite_token == invite_token)
            .options(joinedload(Seller.user), joinedload(Seller.store))
        )
        return result.scalar_one_or_none()

    async def update_seller(self, seller_id: UUID, **fields) -> Seller | None:
        """Update seller fields."""
        result = await self.db.execute(select(Seller).where(Seller.id == seller_id))
        seller = result.scalar_one_or_none()
        if not seller:
            return None

        for key, value in fields.items():
            if hasattr(seller, key):
                setattr(seller, key, value)

        await self.db.commit()
        await self.db.refresh(seller)
        return seller

    async def get_seller_by_store_id(self, store_id: UUID) -> Seller | None:
        """Get seller by their linked store ID."""
        result = await self.db.execute(
            select(Seller).where(Seller.store_id == store_id).options(joinedload(Seller.user))
        )
        return result.scalar_one_or_none()

    async def search_sellers(self, query: str, limit: int = 20) -> list[Seller]:
        """Search sellers by display name. Only returns searchable sellers."""
        result = await self.db.execute(
            select(Seller)
            .where(Seller.is_searchable.is_(True), Seller.display_name.ilike(f'%{query}%'))
            .options(joinedload(Seller.user))
            .limit(limit)
        )
        return list(result.scalars().all())
