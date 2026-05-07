"""Memory sale repository implementation."""

from uuid import UUID

from app.core.models import Sale, SaleProduct
from app.repositories.abstract.sale import AbstractSaleRepository
from app.repositories.memory.storage import MemoryStorage


class MemorySaleRepository(AbstractSaleRepository):
    """Memory implementation of sale repository."""

    def __init__(self, storage: MemoryStorage):
        self.storage = storage

    async def create_sale(self, sale: Sale) -> Sale:
        self.storage.sales[sale.id] = sale
        return sale

    async def get_sale_by_id(self, sale_id: UUID) -> Sale | None:
        return self.storage.sales.get(sale_id)

    async def get_sale_by_invite_token(self, invite_token: str) -> Sale | None:
        for sale in self.storage.sales.values():
            if sale.invite_token == invite_token:
                return sale
        return None

    async def get_sales_by_seller(self, seller_id: UUID) -> list[Sale]:
        return [s for s in self.storage.sales.values() if s.seller_id == seller_id]

    async def update_sale(self, sale_id: UUID, **fields) -> Sale | None:
        sale = self.storage.sales.get(sale_id)
        if not sale:
            return None
        for key, value in fields.items():
            if hasattr(sale, key):
                setattr(sale, key, value)
        return sale

    async def add_sale_product(self, sale_product: SaleProduct) -> SaleProduct:
        self.storage.sale_products[sale_product.id] = sale_product
        return sale_product

    async def get_sale_product(self, sale_id: UUID, product_id: UUID) -> SaleProduct | None:
        for sp in self.storage.sale_products.values():
            if sp.sale_id == sale_id and sp.product_id == product_id:
                return sp
        return None

    async def get_sale_products(self, sale_id: UUID) -> list[SaleProduct]:
        return [sp for sp in self.storage.sale_products.values() if sp.sale_id == sale_id]

    async def update_sale_product(self, sale_product_id: UUID, **fields) -> SaleProduct | None:
        sp = self.storage.sale_products.get(sale_product_id)
        if not sp:
            return None
        for key, value in fields.items():
            if hasattr(sp, key):
                setattr(sp, key, value)
        return sp

    async def delete_sale_product(self, sale_id: UUID, product_id: UUID) -> bool:
        to_delete = None
        for sid, sp in self.storage.sale_products.items():
            if sp.sale_id == sale_id and sp.product_id == product_id:
                to_delete = sid
                break
        if to_delete:
            del self.storage.sale_products[to_delete]
            return True
        return False

    async def get_total_bids_for_sale_product(
        self, sale_id: UUID, product_id: UUID, exclude_bid_id: UUID | None = None
    ) -> float:
        """Get total bids across all runs for a sale product."""
        # Find all runs for this sale
        sale_run_ids = {
            r.id for r in self.storage.runs.values() if getattr(r, 'sale_id', None) == sale_id
        }
        # Find all participations in those runs
        sale_participation_ids = {
            p.id for p in self.storage.participations.values() if p.run_id in sale_run_ids
        }
        # Sum bids for this product across those participations
        total = 0.0
        for bid in self.storage.bids.values():
            if (
                bid.participation_id in sale_participation_ids
                and bid.product_id == product_id
                and not bid.interested_only
                and (exclude_bid_id is None or bid.id != exclude_bid_id)
            ):
                total += float(bid.quantity)
        return total

    async def get_runs_for_sale(self, sale_id: UUID) -> list:
        """Get all runs linked to a sale."""
        return [r for r in self.storage.runs.values() if getattr(r, 'sale_id', None) == sale_id]
