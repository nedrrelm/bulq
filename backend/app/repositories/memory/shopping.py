"""Memory shopping repository implementation."""

from decimal import Decimal
from uuid import UUID, uuid4

from app.core.models import ShoppingListItem
from app.repositories.abstract.shopping import AbstractShoppingRepository
from app.repositories.memory.storage import MemoryStorage


class MemoryShoppingRepository(AbstractShoppingRepository):
    """Memory implementation of shopping repository."""

    def __init__(self, storage: MemoryStorage):
        self.storage = storage

    def create_shopping_list_item(
        self, run_id: UUID, product_id: UUID, requested_quantity: int
    ) -> ShoppingListItem:
        item = ShoppingListItem(
            id=uuid4(),
            run_id=run_id,
            product_id=product_id,
            requested_quantity=requested_quantity,
            is_purchased=False,
        )
        item.run = self.storage.runs.get(run_id)
        item.product = self.storage.products.get(product_id)
        self.storage.shopping_list_items[item.id] = item
        return item

    def get_shopping_list_items(self, run_id: UUID) -> list[ShoppingListItem]:
        items = []
        for item in self.storage.shopping_list_items.values():
            if item.run_id == run_id:
                item.run = self.storage.runs.get(run_id)
                item.product = self.storage.products.get(item.product_id)
                items.append(item)
        return items

    def get_shopping_list_items_by_product(self, product_id: UUID) -> list[ShoppingListItem]:
        items = []
        for item in self.storage.shopping_list_items.values():
            if item.product_id == product_id:
                item.run = self.storage.runs.get(item.run_id)
                item.product = self.storage.products.get(product_id)
                items.append(item)
        return items

    def get_shopping_list_item(self, item_id: UUID) -> ShoppingListItem | None:
        return self.storage.shopping_list_items.get(item_id)

    def mark_item_purchased(
        self, item_id: UUID, quantity: int, price_per_unit: float, total: float, purchase_order: int
    ) -> ShoppingListItem | None:
        item = self.storage.shopping_list_items.get(item_id)
        if item:
            item.purchased_quantity = quantity
            item.purchased_price_per_unit = Decimal(str(price_per_unit))
            item.purchased_total = Decimal(str(total))
            item.is_purchased = True
            item.purchase_order = purchase_order
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
        item = self.storage.shopping_list_items.get(item_id)
        if item and item.is_purchased:
            item.purchased_quantity = float(item.purchased_quantity or 0) + additional_quantity
            item.purchased_total = Decimal(str(float(item.purchased_total or 0) + additional_total))
            item.purchased_price_per_unit = Decimal(str(new_price_per_unit))
            return item
        return None

    def update_item_purchase(
        self, item_id: UUID, quantity: float, price_per_unit: float, total: float
    ) -> ShoppingListItem | None:
        """Update an existing purchase (replaces values, doesn't accumulate)."""
        item = self.storage.shopping_list_items.get(item_id)
        if item and item.is_purchased:
            item.purchased_quantity = quantity
            item.purchased_price_per_unit = Decimal(str(price_per_unit))
            item.purchased_total = Decimal(str(total))
            # Keep is_purchased = True and purchase_order unchanged
            return item
        return None

    def unpurchase_item(self, item_id: UUID) -> ShoppingListItem | None:
        """Reset an item to unpurchased state."""
        item = self.storage.shopping_list_items.get(item_id)
        if item:
            item.is_purchased = False
            item.purchased_quantity = None
            item.purchased_price_per_unit = None
            item.purchased_total = None
            item.purchase_order = None
            return item
        return None

    def update_shopping_list_item_requested_quantity(
        self, item_id: UUID, requested_quantity: int
    ) -> None:
        """Update the requested quantity for a shopping list item."""
        item = self.storage.shopping_list_items.get(item_id)
        if item:
            item.requested_quantity = requested_quantity
