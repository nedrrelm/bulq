"""Database product repository implementation."""

from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import distinct, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Product, ProductAvailability, ProductBid, ShoppingListItem
from app.repositories.abstract.product import AbstractProductRepository


class DatabaseProductRepository(AbstractProductRepository):
    """Database implementation of product repository."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_products_by_store(self, store_id: UUID) -> list[Product]:
        """Get all products for a store (via product availabilities)."""
        # Get distinct product IDs
        result = await self.db.execute(
            select(distinct(ProductAvailability.product_id)).filter(
                ProductAvailability.store_id == store_id
            )
        )
        product_ids = [pid[0] for pid in result.all()]
        
        if not product_ids:
            return []
        
        # Get products by IDs
        result = await self.db.execute(select(Product).filter(Product.id.in_(product_ids)))
        return list(result.scalars().all())

    async def search_products(self, query: str) -> list[Product]:
        """Search for products by name."""
        result = await self.db.execute(
            select(Product).filter(Product.name.ilike(f'%{query}%'))
        )
        return list(result.scalars().all())

    async def get_product_by_id(self, product_id: UUID) -> Product | None:
        """Get product by ID."""
        result = await self.db.execute(select(Product).filter(Product.id == product_id))
        return result.scalar_one_or_none()

    async def create_product(
        self, name: str, brand: str | None = None, unit: str | None = None
    ) -> Product:
        """Create a new product (store-agnostic)."""
        product = Product(name=name, brand=brand, unit=unit)
        self.db.add(product)
        await self.db.commit()
        await self.db.refresh(product)
        return product

    async def get_all_products(self) -> list[Product]:
        """Get all products."""
        result = await self.db.execute(select(Product))
        return list(result.scalars().all())

    async def update_product(self, product_id: UUID, **fields) -> Product | None:
        """Update product fields. Returns updated product or None if not found."""
        result = await self.db.execute(select(Product).filter(Product.id == product_id))
        product = result.scalar_one_or_none()
        if not product:
            return None

        for key, value in fields.items():
            if hasattr(product, key):
                setattr(product, key, value)

        await self.db.commit()
        await self.db.refresh(product)
        return product

    async def delete_product(self, product_id: UUID) -> bool:
        """Delete a product. Returns True if deleted, False if not found."""
        result = await self.db.execute(select(Product).filter(Product.id == product_id))
        product = result.scalar_one_or_none()
        if not product:
            return False

        self.db.delete(product)
        await self.db.commit()
        return True

    async def get_product_availabilities(self, product_id: UUID, store_id: UUID = None) -> list:
        """Get product availabilities, optionally filtered by store."""
        query = select(ProductAvailability).filter(ProductAvailability.product_id == product_id)

        if store_id:
            query = query.filter(ProductAvailability.store_id == store_id)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_availability_by_product_and_store(
        self, product_id: UUID, store_id: UUID
    ) -> ProductAvailability | None:
        """Get the most recent product availability by product and store."""
        result = await self.db.execute(
            select(ProductAvailability)
            .filter(
                ProductAvailability.product_id == product_id,
                ProductAvailability.store_id == store_id,
            )
            .order_by(ProductAvailability.created_at.desc())
        )
        return result.scalar_one_or_none()

    async def create_product_availability(
        self,
        product_id: UUID,
        store_id: UUID,
        price: float | None = None,
        notes: str = '',
        minimum_quantity: int | None = None,
        user_id: UUID = None,
    ) -> ProductAvailability:
        """Create a new product availability record (price observation)."""
        # Always create a new record to track price history
        availability = ProductAvailability(
            product_id=product_id,
            store_id=store_id,
            price=Decimal(str(price)) if price is not None else None,
            notes=notes,
            minimum_quantity=minimum_quantity,
            created_by=user_id,
        )
        self.db.add(availability)
        await self.db.commit()
        await self.db.refresh(availability)
        return availability

    async def update_product_availability_price(
        self, availability_id: UUID, price: float, notes: str = ''
    ) -> ProductAvailability:
        """Update the price for an existing product availability."""
        result = await self.db.execute(
            select(ProductAvailability).filter(ProductAvailability.id == availability_id)
        )
        availability = result.scalar_one_or_none()

        if availability:
            availability.price = Decimal(str(price))
            if notes:
                availability.notes = notes
            await self.db.commit()
            await self.db.refresh(availability)

        return availability

    async def bulk_update_product_bids(self, old_product_id: UUID, new_product_id: UUID) -> int:
        """Update all product bids from old product to new product. Returns count of updated records."""
        result = await self.db.execute(
            update(ProductBid)
            .filter(ProductBid.product_id == old_product_id)
            .values(product_id=new_product_id)
        )
        await self.db.commit()
        return result.rowcount

    async def bulk_update_product_availabilities(self, old_product_id: UUID, new_product_id: UUID) -> int:
        """Update all product availabilities from old product to new product. Returns count of updated records."""
        result = await self.db.execute(
            update(ProductAvailability)
            .filter(ProductAvailability.product_id == old_product_id)
            .values(product_id=new_product_id)
        )
        await self.db.commit()
        return result.rowcount

    async def bulk_update_shopping_list_items(self, old_product_id: UUID, new_product_id: UUID) -> int:
        """Update all shopping list items from old product to new product. Returns count of updated records."""
        result = await self.db.execute(
            update(ShoppingListItem)
            .filter(ShoppingListItem.product_id == old_product_id)
            .values(product_id=new_product_id)
        )
        await self.db.commit()
        return result.rowcount

    async def count_product_bids(self, product_id: UUID) -> int:
        """Count how many bids reference this product."""
        result = await self.db.execute(
            select(func.count()).select_from(ProductBid).filter(ProductBid.product_id == product_id)
        )
        return result.scalar() or 0
