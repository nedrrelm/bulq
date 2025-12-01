"""Database product repository implementation."""

from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.models import Product, ProductAvailability, ProductBid, ShoppingListItem
from app.repositories.abstract.product import AbstractProductRepository


class DatabaseProductRepository(AbstractProductRepository):
    """Database implementation of product repository."""

    def __init__(self, db: Session):
        self.db = db

    def get_products_by_store(self, store_id: UUID) -> list[Product]:
        """Get all products for a store (via product availabilities)."""
        from sqlalchemy import distinct

        product_ids = (
            self.db.query(distinct(ProductAvailability.product_id))
            .filter(ProductAvailability.store_id == store_id)
            .all()
        )
        product_ids = [pid[0] for pid in product_ids]
        return self.db.query(Product).filter(Product.id.in_(product_ids)).all()

    def search_products(self, query: str) -> list[Product]:
        """Search for products by name."""
        return self.db.query(Product).filter(Product.name.ilike(f'%{query}%')).all()

    def get_product_by_id(self, product_id: UUID) -> Product | None:
        """Get product by ID."""
        return self.db.query(Product).filter(Product.id == product_id).first()

    def create_product(
        self, name: str, brand: str | None = None, unit: str | None = None
    ) -> Product:
        """Create a new product (store-agnostic)."""
        product = Product(name=name, brand=brand, unit=unit)
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product

    def get_all_products(self) -> list[Product]:
        """Get all products."""
        return self.db.query(Product).all()

    def update_product(self, product_id: UUID, **fields) -> Product | None:
        """Update product fields. Returns updated product or None if not found."""
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return None

        for key, value in fields.items():
            if hasattr(product, key):
                setattr(product, key, value)

        self.db.commit()
        self.db.refresh(product)
        return product

    def delete_product(self, product_id: UUID) -> bool:
        """Delete a product. Returns True if deleted, False if not found."""
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return False

        self.db.delete(product)
        self.db.commit()
        return True

    def get_product_availabilities(self, product_id: UUID, store_id: UUID = None) -> list:
        """Get product availabilities, optionally filtered by store."""
        query = self.db.query(ProductAvailability).filter(
            ProductAvailability.product_id == product_id
        )

        if store_id:
            query = query.filter(ProductAvailability.store_id == store_id)

        return query.all()

    def get_availability_by_product_and_store(
        self, product_id: UUID, store_id: UUID
    ) -> ProductAvailability | None:
        """Get the most recent product availability by product and store."""
        return (
            self.db.query(ProductAvailability)
            .filter(
                ProductAvailability.product_id == product_id,
                ProductAvailability.store_id == store_id,
            )
            .order_by(ProductAvailability.created_at.desc())
            .first()
        )

    def create_product_availability(
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
        self.db.commit()
        self.db.refresh(availability)
        return availability

    def update_product_availability_price(
        self, availability_id: UUID, price: float, notes: str = ''
    ) -> ProductAvailability:
        """Update the price for an existing product availability."""
        availability = (
            self.db.query(ProductAvailability)
            .filter(ProductAvailability.id == availability_id)
            .first()
        )

        if availability:
            availability.price = Decimal(str(price))
            if notes:
                availability.notes = notes
            self.db.commit()
            self.db.refresh(availability)

        return availability

    def bulk_update_product_bids(self, old_product_id: UUID, new_product_id: UUID) -> int:
        """Update all product bids from old product to new product. Returns count of updated records."""
        result = (
            self.db.query(ProductBid)
            .filter(ProductBid.product_id == old_product_id)
            .update({ProductBid.product_id: new_product_id})
        )
        self.db.commit()
        return result

    def bulk_update_product_availabilities(self, old_product_id: UUID, new_product_id: UUID) -> int:
        """Update all product availabilities from old product to new product. Returns count of updated records."""
        result = (
            self.db.query(ProductAvailability)
            .filter(ProductAvailability.product_id == old_product_id)
            .update({ProductAvailability.product_id: new_product_id})
        )
        self.db.commit()
        return result

    def bulk_update_shopping_list_items(self, old_product_id: UUID, new_product_id: UUID) -> int:
        """Update all shopping list items from old product to new product. Returns count of updated records."""
        result = (
            self.db.query(ShoppingListItem)
            .filter(ShoppingListItem.product_id == old_product_id)
            .update({ShoppingListItem.product_id: new_product_id})
        )
        self.db.commit()
        return result

    def count_product_bids(self, product_id: UUID) -> int:
        """Count how many bids reference this product."""
        return self.db.query(ProductBid).filter(ProductBid.product_id == product_id).count()
