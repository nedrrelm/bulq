"""Memory bid repository implementation."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from app.core.models import ProductBid
from app.repositories.abstract.bid import AbstractBidRepository
from app.repositories.memory.storage import MemoryStorage


class MemoryBidRepository(AbstractBidRepository):
    """Memory implementation of bid repository."""

    def __init__(self, storage: MemoryStorage):
        self.storage = storage

    def get_bids_by_run(self, run_id: UUID) -> list[ProductBid]:
        participations = [p for p in self.storage.participations.values() if p.run_id == run_id]
        participation_ids = {p.id for p in participations}
        return [bid for bid in self.storage.bids.values() if bid.participation_id in participation_ids]

    def get_bids_by_run_with_participations(self, run_id: UUID) -> list[ProductBid]:
        """Get bids with participation and user data eagerly loaded to avoid N+1 queries."""
        participations = [p for p in self.storage.participations.values() if p.run_id == run_id]
        participation_ids = {p.id for p in participations}

        for participation in participations:
            participation.user = self.storage.users.get(participation.user_id)
            participation.run = self.storage.runs.get(run_id)

        bids = []
        for bid in self.storage.bids.values():
            if bid.participation_id in participation_ids:
                bid.participation = next(
                    (p for p in participations if p.id == bid.participation_id), None
                )
                bids.append(bid)

        return bids

    def create_or_update_bid(
        self,
        participation_id: UUID,
        product_id: UUID,
        quantity: int,
        interested_only: bool,
        comment: str | None = None,
    ) -> ProductBid:
        """Create or update a product bid."""
        existing_bid = self.get_bid(participation_id, product_id)
        if existing_bid:
            existing_bid.quantity = quantity
            existing_bid.interested_only = interested_only
            existing_bid.comment = comment
            existing_bid.updated_at = datetime.now()
            return existing_bid
        else:
            bid = ProductBid(
                id=uuid4(),
                participation_id=participation_id,
                product_id=product_id,
                quantity=quantity,
                interested_only=interested_only,
                comment=comment,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            bid.participation = self.storage.participations.get(participation_id)
            bid.product = self.storage.products.get(product_id)
            self.storage.bids[bid.id] = bid
            return bid

    def delete_bid(self, participation_id: UUID, product_id: UUID) -> bool:
        """Delete a product bid."""
        bid_to_delete = None
        for bid_id, bid in self.storage.bids.items():
            if bid.participation_id == participation_id and bid.product_id == product_id:
                bid_to_delete = bid_id
                break

        if bid_to_delete:
            del self.storage.bids[bid_to_delete]
            return True
        return False

    def get_bid(self, participation_id: UUID, product_id: UUID) -> ProductBid | None:
        """Get a specific bid."""
        for bid in self.storage.bids.values():
            if bid.participation_id == participation_id and bid.product_id == product_id:
                bid.participation = self.storage.participations.get(participation_id)
                bid.product = self.storage.products.get(product_id)
                return bid
        return None

    def get_bid_by_id(self, bid_id: UUID) -> ProductBid | None:
        """Get a bid by its ID."""
        return self.storage.bids.get(bid_id)

    def get_bids_by_participation(self, participation_id: UUID) -> list[ProductBid]:
        """Get all bids for a participation."""
        bids = []
        for bid in self.storage.bids.values():
            if bid.participation_id == participation_id:
                bid.participation = self.storage.participations.get(participation_id)
                bid.product = self.storage.products.get(bid.product_id)
                bids.append(bid)
        return bids

    def update_bid_distributed_quantities(
        self, bid_id: UUID, quantity: float, price_per_unit: Decimal
    ) -> None:
        """Update the distributed quantity and price for a bid."""
        bid = self.storage.bids.get(bid_id)
        if bid:
            bid.distributed_quantity = quantity
            bid.distributed_price_per_unit = price_per_unit

    def commit_changes(self) -> None:
        """Commit any pending changes (no-op for in-memory repository)."""
        pass
