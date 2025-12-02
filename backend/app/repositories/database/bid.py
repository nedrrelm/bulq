"""Database bid repository implementation."""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.models import ProductBid, RunParticipation
from app.repositories.abstract.bid import AbstractBidRepository


class DatabaseBidRepository(AbstractBidRepository):
    """Database implementation of bid repository."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_bids_by_run(self, run_id: UUID) -> list[ProductBid]:
        """Get all bids for a run."""
        result = await self.db.execute(
            select(ProductBid)
            .join(RunParticipation)
            .filter(RunParticipation.run_id == run_id)
        )
        return list(result.scalars().all())

    async def get_bids_by_run_with_participations(self, run_id: UUID) -> list[ProductBid]:
        """Get all bids for a run with participation and user data eagerly loaded."""
        result = await self.db.execute(
            select(ProductBid)
            .join(RunParticipation)
            .filter(RunParticipation.run_id == run_id)
            .options(selectinload(ProductBid.participation).selectinload(RunParticipation.user)
            ).distinct()
        )
        return list(result.unique().scalars().all())

    async def create_or_update_bid(
        self,
        participation_id: UUID,
        product_id: UUID,
        quantity: int,
        interested_only: bool,
        comment: str | None = None,
    ) -> ProductBid:
        """Create or update a product bid."""
        # Check if bid already exists
        result = await self.db.execute(
            select(ProductBid).filter(
                ProductBid.participation_id == participation_id, ProductBid.product_id == product_id
            )
        )
        existing_bid = result.scalar_one_or_none()

        if existing_bid:
            # Update existing bid
            existing_bid.quantity = quantity
            existing_bid.interested_only = interested_only
            existing_bid.comment = comment
            await self.db.commit()
            await self.db.refresh(existing_bid)
            return existing_bid
        else:
            # Create new bid
            bid = ProductBid(
                participation_id=participation_id,
                product_id=product_id,
                quantity=quantity,
                interested_only=interested_only,
                comment=comment,
            )
            self.db.add(bid)
            await self.db.commit()
            await self.db.refresh(bid)
            return bid

    async def delete_bid(self, participation_id: UUID, product_id: UUID) -> bool:
        """Delete a product bid."""
        result = await self.db.execute(
            delete(ProductBid).filter(
                ProductBid.participation_id == participation_id, ProductBid.product_id == product_id
            )
        )
        await self.db.commit()
        return result.rowcount > 0

    async def get_bid(self, participation_id: UUID, product_id: UUID) -> ProductBid | None:
        """Get a specific bid."""
        result = await self.db.execute(
            select(ProductBid).filter(
                ProductBid.participation_id == participation_id, ProductBid.product_id == product_id
            )
        )
        return result.scalar_one_or_none()

    async def get_bid_by_id(self, bid_id: UUID) -> ProductBid | None:
        """Get a bid by its ID."""
        result = await self.db.execute(select(ProductBid).filter(ProductBid.id == bid_id))
        return result.scalar_one_or_none()

    async def get_bids_by_participation(self, participation_id: UUID) -> list[ProductBid]:
        """Get all bids for a participation."""
        result = await self.db.execute(
            select(ProductBid).filter(ProductBid.participation_id == participation_id)
        )
        return list(result.scalars().all())

    async def update_bid_distributed_quantities(
        self, bid_id: UUID, quantity: float, price_per_unit: Decimal
    ) -> None:
        """Update the distributed quantity and price for a bid."""
        result = await self.db.execute(select(ProductBid).filter(ProductBid.id == bid_id))
        bid = result.scalar_one_or_none()
        if bid:
            bid.distributed_quantity = quantity
            bid.distributed_price_per_unit = price_per_unit
            await self.db.commit()

    async def commit_changes(self) -> None:
        """Commit any pending changes to the database."""
        await self.db.commit()
