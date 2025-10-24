"""Repository pattern with abstract base class and concrete implementations."""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.core.models import (
    Group,
    LeaderReassignmentRequest,
    Notification,
    Product,
    ProductAvailability,
    ProductBid,
    Run,
    RunParticipation,
    ShoppingListItem,
    Store,
    User,
)


class AbstractRepository(ABC):
    """Abstract base class defining the repository interface."""

    # ==================== User Methods ====================

    @abstractmethod
    def get_user_by_id(self, user_id: UUID) -> User | None:
        """Get user by ID."""
        raise NotImplementedError('Subclass must implement get_user_by_id')

    @abstractmethod
    def get_user_by_email(self, email: str) -> User | None:
        """Get user by email."""
        raise NotImplementedError('Subclass must implement get_user_by_email')

    @abstractmethod
    def create_user(self, name: str, email: str, password_hash: str) -> User:
        """Create a new user."""
        raise NotImplementedError('Subclass must implement create_user')

    @abstractmethod
    def get_user_groups(self, user: User) -> list[Group]:
        """Get all groups that a user is a member of."""
        raise NotImplementedError('Subclass must implement get_user_groups')

    @abstractmethod
    def get_all_users(self) -> list[User]:
        """Get all users."""
        raise NotImplementedError('Subclass must implement get_all_users')

    # ==================== Group Methods ====================

    @abstractmethod
    def get_group_by_id(self, group_id: UUID) -> Group | None:
        """Get group by ID."""
        raise NotImplementedError('Subclass must implement get_group_by_id')

    @abstractmethod
    def get_group_by_invite_token(self, invite_token: str) -> Group | None:
        """Get group by invite token."""
        raise NotImplementedError('Subclass must implement get_group_by_invite_token')

    @abstractmethod
    def regenerate_group_invite_token(self, group_id: UUID) -> str | None:
        """Regenerate invite token for a group."""
        raise NotImplementedError('Subclass must implement regenerate_group_invite_token')

    @abstractmethod
    def create_group(self, name: str, created_by: UUID) -> Group:
        """Create a new group."""
        raise NotImplementedError('Subclass must implement create_group')

    @abstractmethod
    def add_group_member(self, group_id: UUID, user: User, is_group_admin: bool = False) -> bool:
        """Add a user to a group."""
        raise NotImplementedError('Subclass must implement add_group_member')

    @abstractmethod
    def remove_group_member(self, group_id: UUID, user_id: UUID) -> bool:
        """Remove a user from a group."""
        raise NotImplementedError('Subclass must implement remove_group_member')

    @abstractmethod
    def is_user_group_admin(self, group_id: UUID, user_id: UUID) -> bool:
        """Check if a user is an admin of a group."""
        raise NotImplementedError('Subclass must implement is_user_group_admin')

    @abstractmethod
    def get_group_members_with_admin_status(self, group_id: UUID) -> list[dict]:
        """Get all members of a group with their admin status."""
        raise NotImplementedError('Subclass must implement get_group_members_with_admin_status')

    @abstractmethod
    def update_group_joining_allowed(
        self, group_id: UUID, is_joining_allowed: bool
    ) -> Group | None:
        """Update whether a group allows joining via invite link."""
        raise NotImplementedError('Subclass must implement update_group_joining_allowed')

    @abstractmethod
    def set_group_member_admin(self, group_id: UUID, user_id: UUID, is_admin: bool) -> bool:
        """Set the admin status of a group member."""
        raise NotImplementedError('Subclass must implement set_group_member_admin')

    # ==================== Store Methods ====================

    @abstractmethod
    def search_stores(self, query: str) -> list[Store]:
        """Search stores by name."""
        raise NotImplementedError('Subclass must implement search_stores')

    @abstractmethod
    def get_all_stores(self, limit: int = None, offset: int = 0) -> list[Store]:
        """Get all stores (optionally paginated)."""
        raise NotImplementedError('Subclass must implement get_all_stores')

    @abstractmethod
    def create_store(self, name: str) -> Store:
        """Create a new store."""
        raise NotImplementedError('Subclass must implement create_store')

    @abstractmethod
    def get_store_by_id(self, store_id: UUID) -> Store | None:
        """Get store by ID."""
        raise NotImplementedError('Subclass must implement get_store_by_id')

    @abstractmethod
    def get_products_by_store_from_availabilities(self, store_id: UUID) -> list[Product]:
        """Get all unique products that are available at a store."""
        raise NotImplementedError(
            'Subclass must implement get_products_by_store_from_availabilities'
        )

    @abstractmethod
    def get_active_runs_by_store_for_user(self, store_id: UUID, user_id: UUID) -> list[Run]:
        """Get all active runs for a store across all user's groups."""
        raise NotImplementedError('Subclass must implement get_active_runs_by_store_for_user')

    # ==================== Run Methods ====================

    @abstractmethod
    def get_runs_by_group(self, group_id: UUID) -> list[Run]:
        """Get all runs for a group."""
        raise NotImplementedError('Subclass must implement get_runs_by_group')

    @abstractmethod
    def get_completed_cancelled_runs_by_group(
        self, group_id: UUID, limit: int = 10, offset: int = 0
    ) -> list[Run]:
        """Get completed and cancelled runs for a group (paginated)."""
        raise NotImplementedError('Subclass must implement get_completed_cancelled_runs_by_group')

    # ==================== Product Methods ====================

    @abstractmethod
    def get_products_by_store(self, store_id: UUID) -> list[Product]:
        """Get all products for a store."""
        raise NotImplementedError('Subclass must implement get_products_by_store')

    @abstractmethod
    def search_products(self, query: str) -> list[Product]:
        """Search for products by name."""
        raise NotImplementedError('Subclass must implement search_products')

    @abstractmethod
    def get_product_by_id(self, product_id: UUID) -> Product | None:
        """Get product by ID."""
        raise NotImplementedError('Subclass must implement get_product_by_id')

    @abstractmethod
    def create_product(
        self, name: str, brand: str | None = None, unit: str | None = None
    ) -> Product:
        """Create a new product (store-agnostic)."""
        raise NotImplementedError('Subclass must implement create_product')

    @abstractmethod
    def get_all_products(self) -> list[Product]:
        """Get all products."""
        raise NotImplementedError('Subclass must implement get_all_products')

    # ==================== Product Bid Methods ====================

    @abstractmethod
    def get_bids_by_run(self, run_id: UUID) -> list[ProductBid]:
        """Get all bids for a run."""
        raise NotImplementedError('Subclass must implement get_bids_by_run')

    @abstractmethod
    def get_bids_by_run_with_participations(self, run_id: UUID) -> list[ProductBid]:
        """Get all bids for a run with participation and user data eagerly loaded.

        This avoids N+1 query problems when you need to access bid.participation.user.
        Each bid will have its participation object populated, and each participation
        will have its user object populated.
        """
        raise NotImplementedError('Subclass must implement get_bids_by_run_with_participations')

    @abstractmethod
    def create_or_update_bid(
        self, participation_id: UUID, product_id: UUID, quantity: int, interested_only: bool
    ) -> ProductBid:
        """Create or update a product bid."""
        raise NotImplementedError('Subclass must implement create_or_update_bid')

    @abstractmethod
    def delete_bid(self, participation_id: UUID, product_id: UUID) -> bool:
        """Delete a product bid."""
        raise NotImplementedError('Subclass must implement delete_bid')

    @abstractmethod
    def get_bid(self, participation_id: UUID, product_id: UUID) -> ProductBid | None:
        """Get a specific bid."""
        raise NotImplementedError('Subclass must implement get_bid')

    @abstractmethod
    def get_bid_by_id(self, bid_id: UUID) -> ProductBid | None:
        """Get a bid by its ID."""
        raise NotImplementedError('Subclass must implement get_bid_by_id')

    @abstractmethod
    def get_bids_by_participation(self, participation_id: UUID) -> list[ProductBid]:
        """Get all bids for a participation."""
        raise NotImplementedError('Subclass must implement get_bids_by_participation')

    @abstractmethod
    def update_bid_distributed_quantities(
        self, bid_id: UUID, quantity: int, price_per_unit: Decimal
    ) -> None:
        """Update the distributed quantity and price for a bid."""
        raise NotImplementedError('Subclass must implement update_bid_distributed_quantities')

    @abstractmethod
    def commit_changes(self) -> None:
        """Commit any pending changes (no-op for memory repository, commits transaction for database repository)."""
        raise NotImplementedError('Subclass must implement commit_changes')

    # ==================== Auth Methods ====================

    @abstractmethod
    def verify_password(self, password: str, stored_hash: str) -> bool:
        """Verify a password."""
        raise NotImplementedError('Subclass must implement verify_password')

    # ==================== Run & Participation Methods ====================

    @abstractmethod
    def create_run(self, group_id: UUID, store_id: UUID, leader_id: UUID) -> Run:
        """Create a new run with the leader as first participant."""
        raise NotImplementedError('Subclass must implement create_run')

    @abstractmethod
    def get_participation(self, user_id: UUID, run_id: UUID) -> RunParticipation | None:
        """Get a user's participation in a run."""
        raise NotImplementedError('Subclass must implement get_participation')

    @abstractmethod
    def get_run_participations(self, run_id: UUID) -> list[RunParticipation]:
        """Get all participations for a run."""
        raise NotImplementedError('Subclass must implement get_run_participations')

    @abstractmethod
    def get_run_participations_with_users(self, run_id: UUID) -> list[RunParticipation]:
        """Get all participations for a run with user data eagerly loaded.

        This avoids N+1 query problems when you need to access participation.user.
        For DatabaseRepository, this should use SQLAlchemy's joinedload().
        For MemoryRepository, this pre-populates the user relationship.
        """
        raise NotImplementedError('Subclass must implement get_run_participations_with_users')

    @abstractmethod
    def create_participation(
        self, user_id: UUID, run_id: UUID, is_leader: bool = False
    ) -> RunParticipation:
        """Create a participation record for a user in a run."""
        raise NotImplementedError('Subclass must implement create_participation')

    @abstractmethod
    def update_participation_ready(
        self, participation_id: UUID, is_ready: bool
    ) -> RunParticipation | None:
        """Update the ready status of a participation."""
        raise NotImplementedError('Subclass must implement update_participation_ready')

    @abstractmethod
    def update_participation_helper(
        self, user_id: UUID, run_id: UUID, is_helper: bool
    ) -> RunParticipation | None:
        """Update the helper status of a participation."""
        raise NotImplementedError('Subclass must implement update_participation_helper')

    @abstractmethod
    def get_run_by_id(self, run_id: UUID) -> Run | None:
        """Get run by ID."""
        raise NotImplementedError('Subclass must implement get_run_by_id')

    @abstractmethod
    def update_run_state(self, run_id: UUID, new_state: str) -> Run | None:
        """Update the state of a run."""
        raise NotImplementedError('Subclass must implement update_run_state')

    # ==================== Shopping List Methods ====================

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
    def update_shopping_list_item_requested_quantity(
        self, item_id: UUID, requested_quantity: int
    ) -> None:
        """Update the requested quantity for a shopping list item."""
        raise NotImplementedError(
            'Subclass must implement update_shopping_list_item_requested_quantity'
        )

    # ==================== ProductAvailability Methods ====================

    @abstractmethod
    def get_product_availabilities(self, product_id: UUID, store_id: UUID = None) -> list:
        """Get product availabilities, optionally filtered by store."""
        raise NotImplementedError('Subclass must implement get_product_availabilities')

    @abstractmethod
    def create_product_availability(
        self,
        product_id: UUID,
        store_id: UUID,
        price: float | None = None,
        notes: str = '',
        minimum_quantity: int | None = None,
        user_id: UUID = None,
    ) -> Any:
        """Create or update a product availability at a store."""
        raise NotImplementedError('Subclass must implement create_product_availability')

    @abstractmethod
    def get_availability_by_product_and_store(self, product_id: UUID, store_id: UUID) -> Any | None:
        """Get a specific product availability by product and store."""
        raise NotImplementedError('Subclass must implement get_availability_by_product_and_store')

    @abstractmethod
    def update_product_availability_price(
        self, availability_id: UUID, price: float, notes: str = ''
    ) -> Any:
        """Update the price for an existing product availability."""
        raise NotImplementedError('Subclass must implement update_product_availability_price')

    # ==================== Notification Methods ====================

    @abstractmethod
    def create_notification(self, user_id: UUID, type: str, data: dict[str, Any]) -> Notification:
        """Create a new notification for a user."""
        raise NotImplementedError('Subclass must implement create_notification')

    @abstractmethod
    def get_user_notifications(
        self, user_id: UUID, limit: int = 20, offset: int = 0
    ) -> list[Notification]:
        """Get notifications for a user (paginated)."""
        raise NotImplementedError('Subclass must implement get_user_notifications')

    @abstractmethod
    def get_unread_notifications(self, user_id: UUID) -> list[Notification]:
        """Get all unread notifications for a user."""
        raise NotImplementedError('Subclass must implement get_unread_notifications')

    @abstractmethod
    def get_unread_count(self, user_id: UUID) -> int:
        """Get count of unread notifications for a user."""
        raise NotImplementedError('Subclass must implement get_unread_count')

    @abstractmethod
    def mark_notification_as_read(self, notification_id: UUID) -> bool:
        """Mark a notification as read."""
        raise NotImplementedError('Subclass must implement mark_notification_as_read')

    @abstractmethod
    def mark_all_notifications_as_read(self, user_id: UUID) -> int:
        """Mark all notifications as read for a user. Returns count of marked notifications."""
        raise NotImplementedError('Subclass must implement mark_all_notifications_as_read')

    @abstractmethod
    def get_notification_by_id(self, notification_id: UUID) -> Notification | None:
        """Get a notification by ID."""
        raise NotImplementedError('Subclass must implement get_notification_by_id')

    # ==================== Leader Reassignment Methods ====================

    @abstractmethod
    def create_reassignment_request(
        self, run_id: UUID, from_user_id: UUID, to_user_id: UUID
    ) -> LeaderReassignmentRequest:
        """Create a leader reassignment request."""
        raise NotImplementedError('Subclass must implement create_reassignment_request')

    @abstractmethod
    def get_reassignment_request_by_id(self, request_id: UUID) -> LeaderReassignmentRequest | None:
        """Get a reassignment request by ID."""
        raise NotImplementedError('Subclass must implement get_reassignment_request_by_id')

    @abstractmethod
    def get_pending_reassignment_for_run(self, run_id: UUID) -> LeaderReassignmentRequest | None:
        """Get pending reassignment request for a run (if any)."""
        raise NotImplementedError('Subclass must implement get_pending_reassignment_for_run')

    @abstractmethod
    def get_pending_reassignments_from_user(self, user_id: UUID) -> list[LeaderReassignmentRequest]:
        """Get all pending reassignment requests created by a user."""
        raise NotImplementedError('Subclass must implement get_pending_reassignments_from_user')

    @abstractmethod
    def get_pending_reassignments_to_user(self, user_id: UUID) -> list[LeaderReassignmentRequest]:
        """Get all pending reassignment requests for a user to respond to."""
        raise NotImplementedError('Subclass must implement get_pending_reassignments_to_user')

    @abstractmethod
    def update_reassignment_status(self, request_id: UUID, status: str) -> bool:
        """Update the status of a reassignment request (accepted/declined)."""
        raise NotImplementedError('Subclass must implement update_reassignment_status')

    @abstractmethod
    def cancel_all_pending_reassignments_for_run(self, run_id: UUID) -> int:
        """Cancel all pending reassignment requests for a run. Returns count of cancelled requests."""
        raise NotImplementedError(
            'Subclass must implement cancel_all_pending_reassignments_for_run'
        )
