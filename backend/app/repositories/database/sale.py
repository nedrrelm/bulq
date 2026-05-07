"""Database sale repository implementation."""

from uuid import UUID

from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.models import Sale, SaleProduct
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
