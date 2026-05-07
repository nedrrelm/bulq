"""Database sale repository implementation."""

from uuid import UUID

from sqlalchemy import and_, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.models import ProductBid, Run, RunParticipation, Sale, SaleProduct
from app.repositories.abstract.sale import AbstractSaleRepository


class DatabaseSaleRepository(AbstractSaleRepository):
    """Database implementation of sale repository."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_sale(self, sale: Sale) -> Sale:
        self.db.add(sale)
        await self.db.commit()
        await self.db.refresh(sale)
        return sale

    async def get_sale_by_id(self, sale_id: UUID) -> Sale | None:
        result = await self.db.execute(
            select(Sale)
            .where(Sale.id == sale_id)
            .options(
                joinedload(Sale.seller), joinedload(Sale.products).joinedload(SaleProduct.product)
            )
        )
        return result.unique().scalar_one_or_none()

    async def get_sale_by_invite_token(self, invite_token: str) -> Sale | None:
        result = await self.db.execute(select(Sale).where(Sale.invite_token == invite_token))
        return result.scalar_one_or_none()

    async def get_sales_by_seller(self, seller_id: UUID) -> list[Sale]:
        result = await self.db.execute(
            select(Sale).where(Sale.seller_id == seller_id).order_by(Sale.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_sale(self, sale_id: UUID, **fields) -> Sale | None:
        result = await self.db.execute(select(Sale).where(Sale.id == sale_id))
        sale = result.scalar_one_or_none()
        if not sale:
            return None
        for key, value in fields.items():
            if hasattr(sale, key):
                setattr(sale, key, value)
        await self.db.commit()
        await self.db.refresh(sale)
        return sale

    async def add_sale_product(self, sale_product: SaleProduct) -> SaleProduct:
        self.db.add(sale_product)
        await self.db.commit()
        await self.db.refresh(sale_product)
        return sale_product

    async def get_sale_product(self, sale_id: UUID, product_id: UUID) -> SaleProduct | None:
        result = await self.db.execute(
            select(SaleProduct).where(
                and_(SaleProduct.sale_id == sale_id, SaleProduct.product_id == product_id)
            )
        )
        return result.scalar_one_or_none()

    async def get_sale_products(self, sale_id: UUID) -> list[SaleProduct]:
        result = await self.db.execute(
            select(SaleProduct)
            .where(SaleProduct.sale_id == sale_id)
            .options(joinedload(SaleProduct.product))
            .order_by(SaleProduct.created_at)
        )
        return list(result.scalars().all())

    async def update_sale_product(self, sale_product_id: UUID, **fields) -> SaleProduct | None:
        result = await self.db.execute(select(SaleProduct).where(SaleProduct.id == sale_product_id))
        sp = result.scalar_one_or_none()
        if not sp:
            return None
        for key, value in fields.items():
            if hasattr(sp, key):
                setattr(sp, key, value)
        await self.db.commit()
        await self.db.refresh(sp)
        return sp

    async def delete_sale_product(self, sale_id: UUID, product_id: UUID) -> bool:
        result = await self.db.execute(
            delete(SaleProduct).where(
                and_(SaleProduct.sale_id == sale_id, SaleProduct.product_id == product_id)
            )
        )
        await self.db.commit()
        return result.rowcount > 0

    async def get_total_bids_for_sale_product(
        self, sale_id: UUID, product_id: UUID, exclude_bid_id: UUID | None = None
    ) -> float:
        """Get total bids across all runs for a sale product."""
        stmt = (
            select(func.coalesce(func.sum(ProductBid.quantity), 0))
            .join(RunParticipation, ProductBid.participation_id == RunParticipation.id)
            .join(Run, RunParticipation.run_id == Run.id)
            .where(
                and_(
                    Run.sale_id == sale_id,
                    ProductBid.product_id == product_id,
                    ProductBid.interested_only.is_(False),
                )
            )
        )
        if exclude_bid_id:
            stmt = stmt.where(ProductBid.id != exclude_bid_id)
        result = await self.db.execute(stmt)
        return float(result.scalar_one())

    async def get_runs_for_sale(self, sale_id: UUID) -> list[Run]:
        """Get all runs linked to a sale."""
        result = await self.db.execute(
            select(Run).where(Run.sale_id == sale_id).order_by(Run.planning_at)
        )
        return list(result.scalars().all())
