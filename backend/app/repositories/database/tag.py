"""Database tag repository implementation."""

from uuid import UUID

from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Product, Tag, product_tags
from app.repositories.abstract.tag import AbstractTagRepository


class DatabaseTagRepository(AbstractTagRepository):
    """Database implementation of tag repository."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_tag_by_id(self, tag_id: UUID) -> Tag | None:
        """Get tag by ID."""
        result = await self.db.execute(select(Tag).where(Tag.id == tag_id))
        return result.scalar_one_or_none()

    async def get_all_tags(self) -> list[Tag]:
        """Get all tags."""
        result = await self.db.execute(select(Tag).order_by(Tag.type, Tag.value))
        return list(result.scalars().all())

    async def search_tags(
        self,
        query: str,
        tag_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Tag]:
        """Search for tags by value, optionally filtered by type."""
        stmt = select(Tag).where(Tag.value.ilike(f'%{query}%'))

        if tag_type:
            stmt = stmt.where(Tag.type == tag_type)

        stmt = stmt.order_by(Tag.value).offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_tag_by_value_and_type(self, value: str, tag_type: str) -> Tag | None:
        """Get a tag by its value and type."""
        result = await self.db.execute(select(Tag).where(Tag.value == value, Tag.type == tag_type))
        return result.scalar_one_or_none()

    async def create_tag(
        self,
        value: str,
        tag_type: str,
        created_by: UUID | None = None,
    ) -> Tag:
        """Create a new tag."""
        tag = Tag(value=value, type=tag_type, created_by=created_by)
        self.db.add(tag)
        await self.db.commit()
        await self.db.refresh(tag)
        return tag

    async def update_tag(self, tag_id: UUID, **fields) -> Tag | None:
        """Update tag fields. Returns updated tag or None if not found."""
        result = await self.db.execute(select(Tag).where(Tag.id == tag_id))
        tag = result.scalar_one_or_none()
        if not tag:
            return None

        for key, value in fields.items():
            if hasattr(tag, key):
                setattr(tag, key, value)

        await self.db.commit()
        await self.db.refresh(tag)
        return tag

    async def delete_tag(self, tag_id: UUID) -> bool:
        """Delete a tag. Returns True if deleted, False if not found."""
        result = await self.db.execute(select(Tag).where(Tag.id == tag_id))
        tag = result.scalar_one_or_none()
        if not tag:
            return False

        # Remove all product-tag links first
        await self.db.execute(delete(product_tags).where(product_tags.c.tag_id == tag_id))
        await self.db.delete(tag)
        await self.db.commit()
        return True

    async def get_tags_by_product(self, product_id: UUID) -> list[Tag]:
        """Get all tags for a product."""
        result = await self.db.execute(
            select(Tag)
            .join(product_tags, Tag.id == product_tags.c.tag_id)
            .where(product_tags.c.product_id == product_id)
            .order_by(Tag.type, Tag.value)
        )
        return list(result.scalars().all())

    async def add_tag_to_product(self, product_id: UUID, tag_id: UUID) -> None:
        """Add a tag to a product."""
        await self.db.execute(insert(product_tags).values(product_id=product_id, tag_id=tag_id))
        await self.db.commit()

    async def remove_tag_from_product(self, product_id: UUID, tag_id: UUID) -> None:
        """Remove a tag from a product."""
        await self.db.execute(
            delete(product_tags).where(
                product_tags.c.product_id == product_id,
                product_tags.c.tag_id == tag_id,
            )
        )
        await self.db.commit()

    async def is_tag_on_product(self, product_id: UUID, tag_id: UUID) -> bool:
        """Check if a tag is already on a product."""
        result = await self.db.execute(
            select(func.count())
            .select_from(product_tags)
            .where(
                product_tags.c.product_id == product_id,
                product_tags.c.tag_id == tag_id,
            )
        )
        return result.scalar_one() > 0

    async def get_products_by_tag(
        self, tag_id: UUID, limit: int = 50, offset: int = 0
    ) -> list[Product]:
        """Get all products with a given tag."""
        result = await self.db.execute(
            select(Product)
            .join(product_tags, Product.id == product_tags.c.product_id)
            .where(product_tags.c.tag_id == tag_id)
            .order_by(Product.name)
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def bulk_update_product_tags(self, old_tag_id: UUID, new_tag_id: UUID) -> int:
        """Move all product-tag links from old tag to new tag."""
        # Get products that already have the new tag to avoid duplicates
        result = await self.db.execute(
            select(product_tags.c.product_id).where(product_tags.c.tag_id == new_tag_id)
        )
        existing_product_ids = {row[0] for row in result.all()}

        # Update links that won't create duplicates
        result = await self.db.execute(
            select(product_tags.c.product_id).where(product_tags.c.tag_id == old_tag_id)
        )
        old_product_ids = {row[0] for row in result.all()}

        # Products to move (not already linked to new tag)
        to_move = old_product_ids - existing_product_ids
        count = 0

        if to_move:
            await self.db.execute(
                update(product_tags)
                .where(
                    product_tags.c.tag_id == old_tag_id,
                    product_tags.c.product_id.in_(to_move),
                )
                .values(tag_id=new_tag_id)
            )
            count = len(to_move)

        # Delete remaining links (duplicates)
        await self.db.execute(delete(product_tags).where(product_tags.c.tag_id == old_tag_id))
        await self.db.commit()
        return count

    async def count_tag_products(self, tag_id: UUID) -> int:
        """Count how many products have this tag."""
        result = await self.db.execute(
            select(func.count()).select_from(product_tags).where(product_tags.c.tag_id == tag_id)
        )
        return result.scalar_one()
