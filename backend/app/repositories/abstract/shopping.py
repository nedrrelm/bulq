"""Abstract shopping repository interface."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.core.models import ShoppingListItem


class AbstractShoppingRepository(ABC):
    """Abstract base class for shopping repository operations."""

    @abstractmethod
    def create_shopping_list_item(
        self, run_id: UUID, product_id: UUID, requested_quantity: int
    ) -> ShoppingListItem:
        """Create a shopping list item."""
        raise NotImplementedError('Subclass must implement create_shopping_list_item')

    @abstractmethod
    def get_shopping_list_items(self, run_id: UUID) -> list[ShoppingListItem]:
        """Get all shopping list items for a run."""
        raise NotImplementedError('Subclass must implement get_shopping_list_items')

    @abstractmethod
    def get_shopping_list_items_by_product(self, product_id: UUID) -> list[ShoppingListItem]:
        """Get all shopping list items for a product across all runs."""
        raise NotImplementedError('Subclass must implement get_shopping_list_items_by_product')

    @abstractmethod
    def get_shopping_list_item(self, item_id: UUID) -> ShoppingListItem | None:
        """Get a shopping list item by ID."""
        raise NotImplementedError('Subclass must implement get_shopping_list_item')

    @abstractmethod
    def mark_item_purchased(
        self, item_id: UUID, quantity: int, price_per_unit: float, total: float, purchase_order: int
    ) -> ShoppingListItem | None:
        """Mark a shopping list item as purchased."""
        raise NotImplementedError('Subclass must implement mark_item_purchased')

    @abstractmethod
    def add_more_purchased(
        self,
        item_id: UUID,
        additional_quantity: float,
        additional_total: float,
        new_price_per_unit: float,
    ) -> ShoppingListItem | None:
        """Add more purchased quantity to an already-purchased item.

        Args:
            item_id: The shopping list item ID
            additional_quantity: Additional quantity purchased
            additional_total: Additional total cost
            new_price_per_unit: New weighted average price per unit

        Returns:
            Updated ShoppingListItem or None if not found
        """
        raise NotImplementedError('Subclass must implement add_more_purchased')

    @abstractmethod
    def update_item_purchase(
        self, item_id: UUID, quantity: float, price_per_unit: float, total: float
    ) -> ShoppingListItem | None:
        """Update an existing purchase (replaces values, doesn't accumulate).

        Args:
            item_id: The shopping list item ID
            quantity: New purchased quantity
            price_per_unit: New price per unit
            total: New total cost

        Returns:
            Updated ShoppingListItem or None if not found
        """
        raise NotImplementedError('Subclass must implement update_item_purchase')

    @abstractmethod
    def unpurchase_item(self, item_id: UUID) -> ShoppingListItem | None:
        """Reset an item to unpurchased state.

        Args:
            item_id: The shopping list item ID

        Returns:
            Updated ShoppingListItem or None if not found
        """
        raise NotImplementedError('Subclass must implement unpurchase_item')

    @abstractmethod
    def update_shopping_list_item_requested_quantity(
        self, item_id: UUID, requested_quantity: int
    ) -> None:
        """Update the requested quantity for a shopping list item."""
        raise NotImplementedError(
            'Subclass must implement update_shopping_list_item_requested_quantity'
        )
