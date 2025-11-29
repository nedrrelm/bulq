"""Database bid repository implementation."""

from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from app.core.models import ProductBid, RunParticipation
from app.repositories.abstract.bid import AbstractBidRepository


class DatabaseBidRepository(AbstractBidRepository):
    """Database implementation of bid repository."""

    def __init__(self, db: Session):
        self.db = db

    def get_bids_by_run(self, run_id: UUID) -> list[ProductBid]:
        """Get all bids for a run."""
        return (
            self.db.query(ProductBid)
            .join(RunParticipation)
            .filter(RunParticipation.run_id == run_id)
            .all()
        )

    def get_bids_by_run_with_participations(self, run_id: UUID) -> list[ProductBid]:
        """Get all bids for a run with participation and user data eagerly loaded."""
        return (
            self.db.query(ProductBid)
            .join(RunParticipation)
            .filter(RunParticipation.run_id == run_id)
            .options(joinedload(ProductBid.participation).joinedload(RunParticipation.user))
            .all()
        )

    def create_or_update_bid(
        self,
        participation_id: UUID,
        product_id: UUID,
        quantity: int,
        interested_only: bool,
        comment: str | None = None,
    ) -> ProductBid:
        """Create or update a product bid."""
        # Check if bid already exists
        existing_bid = (
            self.db.query(ProductBid)
            .filter(
                ProductBid.participation_id == participation_id, ProductBid.product_id == product_id
            )
            .first()
        )

        if existing_bid:
            # Update existing bid
            existing_bid.quantity = quantity
            existing_bid.interested_only = interested_only
            existing_bid.comment = comment
            self.db.commit()
            self.db.refresh(existing_bid)
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
            self.db.commit()
            self.db.refresh(bid)
            return bid

    def delete_bid(self, participation_id: UUID, product_id: UUID) -> bool:
        """Delete a product bid."""
        result = (
            self.db.query(ProductBid)
            .filter(
                ProductBid.participation_id == participation_id, ProductBid.product_id == product_id
            )
            .delete()
        )
        self.db.commit()
        return result > 0

    def get_bid(self, participation_id: UUID, product_id: UUID) -> ProductBid | None:
        """Get a specific bid."""
        return (
            self.db.query(ProductBid)
            .filter(
                ProductBid.participation_id == participation_id, ProductBid.product_id == product_id
            )
            .first()
        )

    def get_bid_by_id(self, bid_id: UUID) -> ProductBid | None:
        """Get a bid by its ID."""
        return self.db.query(ProductBid).filter(ProductBid.id == bid_id).first()

    def get_bids_by_participation(self, participation_id: UUID) -> list[ProductBid]:
        """Get all bids for a participation."""
        return (
            self.db.query(ProductBid).filter(ProductBid.participation_id == participation_id).all()
        )

    def update_bid_distributed_quantities(
        self, bid_id: UUID, quantity: float, price_per_unit: Decimal
    ) -> None:
        """Update the distributed quantity and price for a bid."""
        bid = self.db.query(ProductBid).filter(ProductBid.id == bid_id).first()
        if bid:
            bid.distributed_quantity = quantity
            bid.distributed_price_per_unit = price_per_unit
            self.db.commit()

    def commit_changes(self) -> None:
        """Commit any pending changes to the database."""
        self.db.commit()
