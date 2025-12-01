"""Database shopping repository implementation."""

from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.models import ShoppingListItem
from app.repositories.abstract.shopping import AbstractShoppingRepository


class DatabaseShoppingRepository(AbstractShoppingRepository):
    """Database implementation of shopping repository."""

    def __init__(self, db: Session):
        self.db = db

    def create_shopping_list_item(
        self, run_id: UUID, product_id: UUID, requested_quantity: int
    ) -> ShoppingListItem:
        """Create a shopping list item."""
        item = ShoppingListItem(
            run_id=run_id,
            product_id=product_id,
            requested_quantity=requested_quantity,
            is_purchased=False,
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def get_shopping_list_items(self, run_id: UUID) -> list[ShoppingListItem]:
        """Get all shopping list items for a run."""
        return self.db.query(ShoppingListItem).filter(ShoppingListItem.run_id == run_id).all()

    def get_shopping_list_items_by_product(self, product_id: UUID) -> list[ShoppingListItem]:
        """Get all shopping list items for a product across all runs."""
        return (
            self.db.query(ShoppingListItem).filter(ShoppingListItem.product_id == product_id).all()
        )

    def get_shopping_list_item(self, item_id: UUID) -> ShoppingListItem | None:
        """Get a shopping list item by ID."""
        return self.db.query(ShoppingListItem).filter(ShoppingListItem.id == item_id).first()

    def mark_item_purchased(
        self, item_id: UUID, quantity: int, price_per_unit: float, total: float, purchase_order: int
    ) -> ShoppingListItem | None:
        """Mark a shopping list item as purchased."""
        item = self.db.query(ShoppingListItem).filter(ShoppingListItem.id == item_id).first()
        if item:
            item.purchased_quantity = quantity
            item.purchased_price_per_unit = Decimal(str(price_per_unit))
            item.purchased_total = Decimal(str(total))
            item.is_purchased = True
            item.purchase_order = purchase_order
            self.db.commit()
            self.db.refresh(item)
            return item
        return None

    def add_more_purchased(
        self,
        item_id: UUID,
        additional_quantity: float,
        additional_total: float,
        new_price_per_unit: float,
    ) -> ShoppingListItem | None:
        """Add more purchased quantity to an already-purchased item."""
        item = self.db.query(ShoppingListItem).filter(ShoppingListItem.id == item_id).first()
        if item and item.is_purchased:
            item.purchased_quantity = float(item.purchased_quantity or 0) + additional_quantity
            item.purchased_total = Decimal(str(float(item.purchased_total or 0) + additional_total))
            item.purchased_price_per_unit = Decimal(str(new_price_per_unit))
            self.db.commit()
            self.db.refresh(item)
            return item
        return None

    def update_shopping_list_item_requested_quantity(
        self, item_id: UUID, requested_quantity: int
    ) -> None:
        """Update the requested quantity for a shopping list item."""
        item = self.db.query(ShoppingListItem).filter(ShoppingListItem.id == item_id).first()
        if item:
            item.requested_quantity = requested_quantity
            self.db.commit()
