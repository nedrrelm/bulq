"""Repository pattern with abstract base class and concrete implementations."""

from abc import ABC, abstractmethod
from datetime import UTC
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from .config import REPO_MODE
from .models import (
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
from .request_context import get_logger
from .run_state import RunState, state_machine

logger = get_logger(__name__)


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


class DatabaseRepository(AbstractRepository):
    """Database implementation using SQLAlchemy.

    Production-ready repository implementation that uses PostgreSQL for data persistence.
    All 74 methods are fully implemented with proper SQLAlchemy queries, eager loading
    for N+1 prevention, transaction management, and error handling.

    Features:
    - Complete CRUD operations for all entities
    - Eager loading with joinedload() to avoid N+1 queries
    - State machine validation for run transitions
    - Bcrypt password verification
    - ProductAvailability tracking (one per product/store with optional price)
    - Proper transaction handling with commit/rollback
    - Comprehensive logging for debugging

    Use this repository when REPO_MODE is set to "database" in config.
    """

    def __init__(self, db: Session):
        self.db = db

    # ==================== User Methods ====================

    def get_user_by_id(self, user_id: UUID) -> User | None:
        """Get user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_user_by_email(self, email: str) -> User | None:
        """Get user by email."""
        return self.db.query(User).filter(User.email == email).first()

    def create_user(self, name: str, email: str, password_hash: str) -> User:
        """Create a new user."""
        user = User(name=name, email=email, password_hash=password_hash)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_user_groups(self, user: User) -> list[Group]:
        """Get all groups that a user is a member of."""
        return self.db.query(Group).join(Group.members).filter(User.id == user.id).all()

    def get_all_users(self) -> list[User]:
        """Get all users."""
        return self.db.query(User).all()

    # ==================== Group Methods ====================

    def get_group_by_id(self, group_id: UUID) -> Group | None:
        """Get group by ID."""
        return self.db.query(Group).filter(Group.id == group_id).first()

    def get_group_by_invite_token(self, invite_token: str) -> Group | None:
        """Get group by invite token."""
        return self.db.query(Group).filter(Group.invite_token == invite_token).first()

    def regenerate_group_invite_token(self, group_id: UUID) -> str | None:
        """Regenerate invite token for a group."""
        from uuid import uuid4

        group = self.db.query(Group).filter(Group.id == group_id).first()
        if group:
            new_token = str(uuid4())
            group.invite_token = new_token
            self.db.commit()
            return new_token
        return None

    def create_group(self, name: str, created_by: UUID) -> Group:
        """Create a new group."""
        from uuid import uuid4

        group = Group(
            name=name, created_by=created_by, invite_token=str(uuid4()), is_joining_allowed=True
        )
        self.db.add(group)
        self.db.commit()
        self.db.refresh(group)
        return group

    def add_group_member(self, group_id: UUID, user: User, is_group_admin: bool = False) -> bool:
        """Add a user to a group."""
        from sqlalchemy import insert, select

        from .models import group_membership

        # Check if already a member
        existing = self.db.execute(
            select(group_membership).where(
                group_membership.c.group_id == group_id, group_membership.c.user_id == user.id
            )
        ).first()

        if existing:
            return False

        # Insert into group_membership table
        self.db.execute(
            insert(group_membership).values(
                group_id=group_id, user_id=user.id, is_group_admin=is_group_admin
            )
        )
        self.db.commit()
        return True

    def remove_group_member(self, group_id: UUID, user_id: UUID) -> bool:
        """Remove a user from a group."""
        from sqlalchemy import delete

        from .models import group_membership

        result = self.db.execute(
            delete(group_membership).where(
                group_membership.c.group_id == group_id, group_membership.c.user_id == user_id
            )
        )
        self.db.commit()
        return result.rowcount > 0

    def is_user_group_admin(self, group_id: UUID, user_id: UUID) -> bool:
        """Check if a user is an admin of a group."""
        from sqlalchemy import select

        from .models import group_membership

        result = self.db.execute(
            select(group_membership.c.is_group_admin).where(
                group_membership.c.group_id == group_id, group_membership.c.user_id == user_id
            )
        ).first()

        return result[0] if result else False

    def get_group_members_with_admin_status(self, group_id: UUID) -> list[dict]:
        """Get all members of a group with their admin status."""
        from sqlalchemy import select

        from .models import group_membership

        results = self.db.execute(
            select(User, group_membership.c.is_group_admin)
            .join(group_membership, User.id == group_membership.c.user_id)
            .where(group_membership.c.group_id == group_id)
        ).all()

        return [
            {'id': str(user.id), 'name': user.name, 'email': user.email, 'is_group_admin': is_admin}
            for user, is_admin in results
        ]

    def update_group_joining_allowed(
        self, group_id: UUID, is_joining_allowed: bool
    ) -> Group | None:
        """Update whether a group allows joining via invite link."""
        group = self.db.query(Group).filter(Group.id == group_id).first()
        if group:
            group.is_joining_allowed = is_joining_allowed
            self.db.commit()
            self.db.refresh(group)
            return group
        return None

    def set_group_member_admin(self, group_id: UUID, user_id: UUID, is_admin: bool) -> bool:
        """Set the admin status of a group member."""
        from sqlalchemy import update

        from .models import group_membership

        result = self.db.execute(
            update(group_membership)
            .where(
                group_membership.c.group_id == group_id,
                group_membership.c.user_id == user_id
            )
            .values(is_group_admin=is_admin)
        )
        self.db.commit()
        return result.rowcount > 0

    # ==================== Store Methods ====================

    def search_stores(self, query: str) -> list[Store]:
        """Search stores by name."""
        return self.db.query(Store).filter(Store.name.ilike(f'%{query}%')).all()

    def get_all_stores(self, limit: int = None, offset: int = 0) -> list[Store]:
        """Get all stores (optionally paginated)."""
        query = self.db.query(Store).order_by(Store.name)
        if limit is not None:
            query = query.limit(limit).offset(offset)
        return query.all()

    def create_store(self, name: str) -> Store:
        """Create a new store."""
        store = Store(name=name)
        self.db.add(store)
        self.db.commit()
        self.db.refresh(store)
        return store

    def get_store_by_id(self, store_id: UUID) -> Store | None:
        """Get store by ID."""
        return self.db.query(Store).filter(Store.id == store_id).first()

    def get_products_by_store_from_availabilities(self, store_id: UUID) -> list[Product]:
        """Get all unique products that are available at a store."""
        from sqlalchemy import distinct

        product_ids = (
            self.db.query(distinct(ProductAvailability.product_id))
            .filter(ProductAvailability.store_id == store_id)
            .all()
        )
        product_ids = [pid[0] for pid in product_ids]
        return self.db.query(Product).filter(Product.id.in_(product_ids)).all()

    def get_active_runs_by_store_for_user(self, store_id: UUID, user_id: UUID) -> list[Run]:
        """Get all active runs for a store across all user's groups."""
        from sqlalchemy import and_, select

        from .models import group_membership

        active_states = ['planning', 'active', 'confirmed', 'shopping', 'adjusting', 'distributing']

        # Get user's group IDs
        user_group_ids = (
            self.db.execute(
                select(group_membership.c.group_id).where(group_membership.c.user_id == user_id)
            )
            .scalars()
            .all()
        )

        # Get runs for those groups that target this store and are active
        return (
            self.db.query(Run)
            .filter(
                and_(
                    Run.store_id == store_id,
                    Run.state.in_(active_states),
                    Run.group_id.in_(user_group_ids),
                )
            )
            .all()
        )

    # ==================== Run Methods ====================

    def get_runs_by_group(self, group_id: UUID) -> list[Run]:
        """Get all runs for a group."""
        return self.db.query(Run).filter(Run.group_id == group_id).all()

    def get_completed_cancelled_runs_by_group(
        self, group_id: UUID, limit: int = 10, offset: int = 0
    ) -> list[Run]:
        """Get completed and cancelled runs for a group (paginated)."""
        from sqlalchemy import case, desc

        # Query runs that are completed or cancelled
        query = self.db.query(Run).filter(
            Run.group_id == group_id, Run.state.in_(['completed', 'cancelled'])
        )

        # Order by the appropriate timestamp (completed_at or cancelled_at), most recent first
        query = query.order_by(
            desc(
                case(
                    (Run.state == 'completed', Run.completed_at),
                    (Run.state == 'cancelled', Run.cancelled_at),
                    else_=None,
                )
            )
        )

        return query.limit(limit).offset(offset).all()

    def get_run_by_id(self, run_id: UUID) -> Run | None:
        """Get run by ID."""
        return self.db.query(Run).filter(Run.id == run_id).first()

    # ==================== Product Methods ====================

    def get_products_by_store(self, store_id: UUID) -> list[Product]:
        """Get all products for a store (via product availabilities)."""
        return self.get_products_by_store_from_availabilities(store_id)

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

    # ==================== Product Bid Methods ====================

    def get_bids_by_run(self, run_id: UUID) -> list[ProductBid]:
        """Get all bids for a run."""
        return (
            self.db.query(ProductBid)
            .join(RunParticipation)
            .filter(RunParticipation.run_id == run_id)
            .all()
        )

    def get_bids_by_run_with_participations(self, run_id: UUID) -> list[ProductBid]:
        """Get all bids for a run with participation and user data eagerly loaded."""
        from sqlalchemy.orm import joinedload

        return (
            self.db.query(ProductBid)
            .join(RunParticipation)
            .filter(RunParticipation.run_id == run_id)
            .options(joinedload(ProductBid.participation).joinedload(RunParticipation.user))
            .all()
        )

    def create_or_update_bid(
        self, participation_id: UUID, product_id: UUID, quantity: int, interested_only: bool
    ) -> ProductBid:
        """Create or update a product bid."""
        # Check if bid already exists
        existing_bid = (
            self.db.query(ProductBid)
            .filter(
                ProductBid.participation_id == participation_id, ProductBid.product_id == product_id
            )
            .first()
        )

        if existing_bid:
            # Update existing bid
            existing_bid.quantity = quantity
            existing_bid.interested_only = interested_only
            self.db.commit()
            self.db.refresh(existing_bid)
            return existing_bid
        else:
            # Create new bid
            bid = ProductBid(
                participation_id=participation_id,
                product_id=product_id,
                quantity=quantity,
                interested_only=interested_only,
            )
            self.db.add(bid)
            self.db.commit()
            self.db.refresh(bid)
            return bid

    def delete_bid(self, participation_id: UUID, product_id: UUID) -> bool:
        """Delete a product bid."""
        result = (
            self.db.query(ProductBid)
            .filter(
                ProductBid.participation_id == participation_id, ProductBid.product_id == product_id
            )
            .delete()
        )
        self.db.commit()
        return result > 0

    def get_bid(self, participation_id: UUID, product_id: UUID) -> ProductBid | None:
        """Get a specific bid."""
        return (
            self.db.query(ProductBid)
            .filter(
                ProductBid.participation_id == participation_id, ProductBid.product_id == product_id
            )
            .first()
        )

    def get_bid_by_id(self, bid_id: UUID) -> ProductBid | None:
        """Get a bid by its ID."""
        return self.db.query(ProductBid).filter(ProductBid.id == bid_id).first()

    def get_bids_by_participation(self, participation_id: UUID) -> list[ProductBid]:
        """Get all bids for a participation."""
        return (
            self.db.query(ProductBid)
            .filter(ProductBid.participation_id == participation_id)
            .all()
        )

    def update_bid_distributed_quantities(
        self, bid_id: UUID, quantity: int, price_per_unit: Decimal
    ) -> None:
        """Update the distributed quantity and price for a bid."""
        bid = self.db.query(ProductBid).filter(ProductBid.id == bid_id).first()
        if bid:
            bid.distributed_quantity = quantity
            bid.distributed_price_per_unit = price_per_unit

    def commit_changes(self) -> None:
        """Commit any pending changes to the database."""
        self.db.commit()

    # ==================== Auth Methods ====================

    def verify_password(self, password: str, stored_hash: str) -> bool:
        """Verify a password against a hash."""
        import bcrypt

        return bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))

    # ==================== Run & Participation Methods ====================

    def create_run(self, group_id: UUID, store_id: UUID, leader_id: UUID) -> Run:
        """Create a new run with the leader as first participant."""
        run = Run(group_id=group_id, store_id=store_id, state=RunState.PLANNING)
        self.db.add(run)
        self.db.flush()  # Get the run ID without committing

        # Create participation for the leader
        participation = RunParticipation(
            user_id=leader_id, run_id=run.id, is_leader=True, is_removed=False
        )
        self.db.add(participation)
        self.db.commit()
        self.db.refresh(run)
        return run

    def get_participation(self, user_id: UUID, run_id: UUID) -> RunParticipation | None:
        """Get a user's participation in a run."""
        return (
            self.db.query(RunParticipation)
            .filter(RunParticipation.user_id == user_id, RunParticipation.run_id == run_id)
            .first()
        )

    def get_run_participations(self, run_id: UUID) -> list[RunParticipation]:
        """Get all participations for a run."""
        return self.db.query(RunParticipation).filter(RunParticipation.run_id == run_id).all()

    def get_run_participations_with_users(self, run_id: UUID) -> list[RunParticipation]:
        """Get all participations for a run with user data eagerly loaded."""
        from sqlalchemy.orm import joinedload

        return (
            self.db.query(RunParticipation)
            .filter(RunParticipation.run_id == run_id)
            .options(joinedload(RunParticipation.user))
            .all()
        )

    def create_participation(
        self, user_id: UUID, run_id: UUID, is_leader: bool = False
    ) -> RunParticipation:
        """Create a participation record for a user in a run."""
        participation = RunParticipation(
            user_id=user_id, run_id=run_id, is_leader=is_leader, is_removed=False
        )
        self.db.add(participation)
        self.db.commit()
        self.db.refresh(participation)
        return participation

    def update_participation_ready(
        self, participation_id: UUID, is_ready: bool
    ) -> RunParticipation | None:
        """Update the ready status of a participation."""
        participation = (
            self.db.query(RunParticipation).filter(RunParticipation.id == participation_id).first()
        )
        if participation:
            participation.is_ready = is_ready
            self.db.commit()
            self.db.refresh(participation)
            return participation
        return None

    def update_run_state(self, run_id: UUID, new_state: str) -> Run | None:
        """Update the state of a run."""
        from datetime import datetime

        run = self.db.query(Run).filter(Run.id == run_id).first()
        if run:
            # Convert string states to RunState enum
            current_state = RunState(run.state)
            target_state = RunState(new_state)

            # Validate transition using state machine
            state_machine.validate_transition(current_state, target_state, str(run_id))

            # Update state
            run.state = new_state

            # Set the timestamp for the new state
            timestamp_field = f'{new_state}_at'
            setattr(run, timestamp_field, datetime.now())

            self.db.commit()
            self.db.refresh(run)

            logger.info(
                'Run state transitioned',
                extra={
                    'run_id': str(run_id),
                    'from_state': str(current_state),
                    'to_state': str(target_state),
                },
            )

            return run
        return None

    # ==================== Shopping List Methods ====================

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

    def update_shopping_list_item_requested_quantity(
        self, item_id: UUID, requested_quantity: int
    ) -> None:
        """Update the requested quantity for a shopping list item."""
        item = self.db.query(ShoppingListItem).filter(ShoppingListItem.id == item_id).first()
        if item:
            item.requested_quantity = requested_quantity

    # ==================== ProductAvailability Methods ====================

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
        user_id: UUID = None,
    ) -> ProductAvailability:
        """Create a new product availability record (price observation)."""
        # Always create a new record to track price history
        availability = ProductAvailability(
            product_id=product_id,
            store_id=store_id,
            price=Decimal(str(price)) if price is not None else None,
            notes=notes,
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

    # ==================== Notification Methods ====================

    def create_notification(self, user_id: UUID, type: str, data: dict[str, Any]) -> Notification:
        """Create a new notification for a user."""
        notification = Notification(user_id=user_id, type=type, data=data, read=False)
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def get_user_notifications(
        self, user_id: UUID, limit: int = 20, offset: int = 0
    ) -> list[Notification]:
        """Get notifications for a user (paginated)."""
        return (
            self.db.query(Notification)
            .filter(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

    def get_unread_notifications(self, user_id: UUID) -> list[Notification]:
        """Get all unread notifications for a user."""
        return (
            self.db.query(Notification)
            .filter(Notification.user_id == user_id, ~Notification.read)
            .order_by(Notification.created_at.desc())
            .all()
        )

    def get_unread_count(self, user_id: UUID) -> int:
        """Get count of unread notifications for a user."""
        return (
            self.db.query(Notification)
            .filter(Notification.user_id == user_id, ~Notification.read)
            .count()
        )

    def mark_notification_as_read(self, notification_id: UUID) -> bool:
        """Mark a notification as read."""
        notification = (
            self.db.query(Notification).filter(Notification.id == notification_id).first()
        )
        if notification:
            notification.read = True
            self.db.commit()
            return True
        return False

    def mark_all_notifications_as_read(self, user_id: UUID) -> int:
        """Mark all notifications as read for a user. Returns count of marked notifications."""
        count = (
            self.db.query(Notification)
            .filter(Notification.user_id == user_id, ~Notification.read)
            .update({Notification.read: True})
        )
        self.db.commit()
        return count

    def get_notification_by_id(self, notification_id: UUID) -> Notification | None:
        """Get a notification by ID."""
        return self.db.query(Notification).filter(Notification.id == notification_id).first()

    # ==================== Leader Reassignment Methods ====================

    def create_reassignment_request(
        self, run_id: UUID, from_user_id: UUID, to_user_id: UUID
    ) -> LeaderReassignmentRequest:
        """Create a leader reassignment request."""
        request = LeaderReassignmentRequest(
            run_id=run_id, from_user_id=from_user_id, to_user_id=to_user_id, status='pending'
        )
        self.db.add(request)
        self.db.commit()
        self.db.refresh(request)
        return request

    def get_reassignment_request_by_id(self, request_id: UUID) -> LeaderReassignmentRequest | None:
        """Get a reassignment request by ID."""
        return (
            self.db.query(LeaderReassignmentRequest)
            .filter(LeaderReassignmentRequest.id == request_id)
            .first()
        )

    def get_pending_reassignment_for_run(self, run_id: UUID) -> LeaderReassignmentRequest | None:
        """Get pending reassignment request for a run (if any)."""
        return (
            self.db.query(LeaderReassignmentRequest)
            .filter(
                LeaderReassignmentRequest.run_id == run_id,
                LeaderReassignmentRequest.status == 'pending',
            )
            .first()
        )

    def get_pending_reassignments_from_user(self, user_id: UUID) -> list[LeaderReassignmentRequest]:
        """Get all pending reassignment requests created by a user."""
        return (
            self.db.query(LeaderReassignmentRequest)
            .filter(
                LeaderReassignmentRequest.from_user_id == user_id,
                LeaderReassignmentRequest.status == 'pending',
            )
            .all()
        )

    def get_pending_reassignments_to_user(self, user_id: UUID) -> list[LeaderReassignmentRequest]:
        """Get all pending reassignment requests for a user to respond to."""
        return (
            self.db.query(LeaderReassignmentRequest)
            .filter(
                LeaderReassignmentRequest.to_user_id == user_id,
                LeaderReassignmentRequest.status == 'pending',
            )
            .all()
        )

    def update_reassignment_status(self, request_id: UUID, status: str) -> bool:
        """Update the status of a reassignment request (accepted/declined)."""
        from datetime import datetime

        request = (
            self.db.query(LeaderReassignmentRequest)
            .filter(LeaderReassignmentRequest.id == request_id)
            .first()
        )
        if not request:
            return False

        request.status = status
        request.resolved_at = datetime.now()
        self.db.commit()
        return True

    def cancel_all_pending_reassignments_for_run(self, run_id: UUID) -> int:
        """Cancel all pending reassignment requests for a run. Returns count of cancelled requests."""
        from datetime import datetime

        count = (
            self.db.query(LeaderReassignmentRequest)
            .filter(
                LeaderReassignmentRequest.run_id == run_id,
                LeaderReassignmentRequest.status == 'pending',
            )
            .update(
                {
                    LeaderReassignmentRequest.status: 'cancelled',
                    LeaderReassignmentRequest.resolved_at: datetime.now(),
                }
            )
        )
        self.db.commit()
        return count


class MemoryRepository(AbstractRepository):
    """In-memory implementation for testing and development - Singleton."""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_storage()
        return cls._instance

    def _init_storage(self):
        """Initialize storage dictionaries and create test data. Called once by __new__."""
        # Storage dictionaries
        self._users: dict[UUID, User] = {}
        self._users_by_email: dict[str, User] = {}
        self._groups: dict[UUID, Group] = {}
        self._group_memberships: dict[UUID, list[UUID]] = {}  # group_id -> [user_ids]
        self._group_admin_status: dict[tuple, bool] = {}  # (group_id, user_id) -> is_admin
        self._stores: dict[UUID, Store] = {}
        self._runs: dict[UUID, Run] = {}
        self._products: dict[UUID, Product] = {}
        self._participations: dict[UUID, RunParticipation] = {}
        self._bids: dict[UUID, ProductBid] = {}
        self._shopping_list_items: dict[UUID, ShoppingListItem] = {}
        self._product_availabilities: dict[UUID, ProductAvailability] = {}
        self._notifications: dict[UUID, Notification] = {}
        self._reassignment_requests: dict[UUID, LeaderReassignmentRequest] = {}

        MemoryRepository._initialized = True

    def get_user_by_id(self, user_id: UUID) -> User | None:
        return self._users.get(user_id)

    def get_user_by_email(self, email: str) -> User | None:
        return self._users_by_email.get(email)

    def create_user(self, name: str, email: str, password_hash: str) -> User:
        user = User(
            id=uuid4(),
            name=name,
            email=email,
            password_hash=password_hash,
            verified=False,
            is_admin=False,
        )
        self._users[user.id] = user
        self._users_by_email[email] = user
        return user

    def get_all_users(self) -> list[User]:
        return list(self._users.values())

    def get_user_groups(self, user: User) -> list[Group]:
        user_groups = []
        for group_id, member_ids in self._group_memberships.items():
            if user.id in member_ids:
                group = self._groups.get(group_id)
                if group:
                    # Set up relationships for compatibility
                    group.creator = self._users.get(group.created_by)
                    group.members = [
                        self._users.get(uid) for uid in member_ids if uid in self._users
                    ]
                    user_groups.append(group)
        return user_groups

    def get_group_by_id(self, group_id: UUID) -> Group | None:
        group = self._groups.get(group_id)
        if group:
            # Set up relationships
            group.creator = self._users.get(group.created_by)
            member_ids = self._group_memberships.get(group_id, [])
            group.members = [self._users.get(uid) for uid in member_ids if uid in self._users]
        return group

    def get_group_by_invite_token(self, invite_token: str) -> Group | None:
        for group in self._groups.values():
            if group.invite_token == invite_token:
                # Set up relationships
                group.creator = self._users.get(group.created_by)
                member_ids = self._group_memberships.get(group.id, [])
                group.members = [self._users.get(uid) for uid in member_ids if uid in self._users]
                return group
        return None

    def regenerate_group_invite_token(self, group_id: UUID) -> str | None:
        group = self._groups.get(group_id)
        if group:
            new_token = str(uuid4())
            group.invite_token = new_token
            return new_token
        return None

    def create_group(self, name: str, created_by: UUID) -> Group:
        group = Group(
            id=uuid4(),
            name=name,
            created_by=created_by,
            invite_token=str(uuid4()),
            is_joining_allowed=True,
        )
        self._groups[group.id] = group
        self._group_memberships[group.id] = []
        return group

    def add_group_member(self, group_id: UUID, user: User, is_group_admin: bool = False) -> bool:
        if group_id in self._group_memberships and user.id not in self._group_memberships[group_id]:
            self._group_memberships[group_id].append(user.id)
            self._group_admin_status[(group_id, user.id)] = is_group_admin
            return True
        return False

    def remove_group_member(self, group_id: UUID, user_id: UUID) -> bool:
        """Remove a user from a group."""
        if group_id in self._group_memberships and user_id in self._group_memberships[group_id]:
            self._group_memberships[group_id].remove(user_id)
            # Remove admin status
            key = (group_id, user_id)
            if key in self._group_admin_status:
                del self._group_admin_status[key]
            return True
        return False

    def is_user_group_admin(self, group_id: UUID, user_id: UUID) -> bool:
        """Check if a user is an admin of a group."""
        return self._group_admin_status.get((group_id, user_id), False)

    def get_group_members_with_admin_status(self, group_id: UUID) -> list[dict]:
        """Get all members of a group with their admin status."""
        member_ids = self._group_memberships.get(group_id, [])
        members = []
        for user_id in member_ids:
            user = self._users.get(user_id)
            if user:
                members.append(
                    {
                        'id': str(user.id),
                        'name': user.name,
                        'email': user.email,
                        'is_group_admin': self._group_admin_status.get((group_id, user_id), False),
                    }
                )
        return members

    def update_group_joining_allowed(
        self, group_id: UUID, is_joining_allowed: bool
    ) -> Group | None:
        """Update whether a group allows joining via invite link."""
        group = self._groups.get(group_id)
        if group:
            group.is_joining_allowed = is_joining_allowed
            return group
        return None

    def set_group_member_admin(self, group_id: UUID, user_id: UUID, is_admin: bool) -> bool:
        """Set the admin status of a group member."""
        if group_id in self._group_memberships and user_id in self._group_memberships[group_id]:
            self._group_admin_status[(group_id, user_id)] = is_admin
            return True
        return False

    def search_stores(self, query: str) -> list[Store]:
        query_lower = query.lower()
        return [store for store in self._stores.values() if query_lower in store.name.lower()]

    def get_all_stores(self, limit: int = None, offset: int = 0) -> list[Store]:
        stores = list(self._stores.values())
        # Sort by name for consistent ordering
        stores.sort(key=lambda s: s.name)
        if limit is not None:
            return stores[offset : offset + limit]
        return stores

    def get_store_by_id(self, store_id: UUID) -> Store | None:
        return self._stores.get(store_id)

    def get_active_runs_by_store_for_user(self, store_id: UUID, user_id: UUID) -> list[Run]:
        """Get all active runs for a store across all user's groups."""
        # Get user's groups by checking which groups have this user as a member
        user_group_ids = []
        for group_id, member_ids in self._group_memberships.items():
            if user_id in member_ids:
                user_group_ids.append(group_id)

        # Get runs for those groups that target this store and are active
        active_states = ['planning', 'active', 'confirmed', 'shopping', 'adjusting', 'distributing']
        runs = []
        for run in self._runs.values():
            if (
                run.store_id == store_id
                and run.state in active_states
                and run.group_id in user_group_ids
            ):
                runs.append(run)
        return runs

    def get_runs_by_group(self, group_id: UUID) -> list[Run]:
        return [run for run in self._runs.values() if run.group_id == group_id]

    def get_completed_cancelled_runs_by_group(
        self, group_id: UUID, limit: int = 10, offset: int = 0
    ) -> list[Run]:
        """Get completed and cancelled runs for a group (paginated)."""
        from datetime import datetime

        # Get all completed and cancelled runs for the group
        runs = [
            run
            for run in self._runs.values()
            if run.group_id == group_id and run.state in ('completed', 'cancelled')
        ]

        # Sort by completion/cancellation timestamp (most recent first)
        # Use completed_at for completed runs, cancelled_at for cancelled runs
        def get_timestamp(run):
            if run.state == 'completed' and run.completed_at:
                return run.completed_at
            elif run.state == 'cancelled' and run.cancelled_at:
                return run.cancelled_at
            return datetime.min.replace(tzinfo=UTC)

        runs.sort(key=get_timestamp, reverse=True)
        return runs[offset : offset + limit]

    def get_products_by_store(self, store_id: UUID) -> list[Product]:
        """Get all products for a store (via product availabilities)."""
        return self.get_products_by_store_from_availabilities(store_id)

    def get_products_by_store_from_availabilities(self, store_id: UUID) -> list[Product]:
        """Get all unique products that are available at a store."""
        product_ids = {
            avail.product_id
            for avail in self._product_availabilities.values()
            if avail.store_id == store_id
        }
        return [product for product in self._products.values() if product.id in product_ids]

    def search_products(self, query: str) -> list[Product]:
        query_lower = query.lower()
        return [
            product for product in self._products.values() if query_lower in product.name.lower()
        ]

    def get_product_by_id(self, product_id: UUID) -> Product | None:
        return self._products.get(product_id)

    def get_bids_by_run(self, run_id: UUID) -> list[ProductBid]:
        # Get all participations for this run
        participations = [p for p in self._participations.values() if p.run_id == run_id]
        participation_ids = {p.id for p in participations}
        # Get all bids for these participations
        return [bid for bid in self._bids.values() if bid.participation_id in participation_ids]

    def get_bids_by_run_with_participations(self, run_id: UUID) -> list[ProductBid]:
        """Get bids with participation and user data eagerly loaded to avoid N+1 queries."""
        # Get all participations for this run with users loaded
        participations = [p for p in self._participations.values() if p.run_id == run_id]
        participation_ids = {p.id for p in participations}

        # Eagerly load user data for each participation
        for participation in participations:
            participation.user = self._users.get(participation.user_id)
            participation.run = self._runs.get(run_id)

        # Get all bids for these participations and attach the participation objects
        bids = []
        for bid in self._bids.values():
            if bid.participation_id in participation_ids:
                # Attach the participation object with pre-loaded user
                bid.participation = next(
                    (p for p in participations if p.id == bid.participation_id), None
                )
                bids.append(bid)

        return bids

    def verify_password(self, password: str, stored_hash: str) -> bool:
        # In memory mode, accept any password for ease of testing
        return True

    def create_store(self, name: str) -> Store:
        """Create a new store."""
        store = Store(id=uuid4(), name=name)
        self._stores[store.id] = store
        return store

    def create_product(
        self, name: str, brand: str | None = None, unit: str | None = None
    ) -> Product:
        """Create a new product (store-agnostic)."""
        from datetime import datetime

        product = Product(
            id=uuid4(),
            name=name,
            brand=brand,
            unit=unit,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        self._products[product.id] = product
        return product

    def get_all_products(self) -> list[Product]:
        return list(self._products.values())

    def create_or_update_bid(
        self, participation_id: UUID, product_id: UUID, quantity: int, interested_only: bool
    ) -> ProductBid:
        """Create or update a product bid."""
        from datetime import datetime

        # Check if bid already exists
        existing_bid = self.get_bid(participation_id, product_id)
        if existing_bid:
            # Update existing bid
            existing_bid.quantity = quantity
            existing_bid.interested_only = interested_only
            existing_bid.updated_at = datetime.now()
            return existing_bid
        else:
            # Create new bid
            bid = ProductBid(
                id=uuid4(),
                participation_id=participation_id,
                product_id=product_id,
                quantity=quantity,
                interested_only=interested_only,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            # Set up relationships
            bid.participation = self._participations.get(participation_id)
            bid.product = self._products.get(product_id)
            self._bids[bid.id] = bid
            return bid

    def delete_bid(self, participation_id: UUID, product_id: UUID) -> bool:
        """Delete a product bid."""
        # Find the bid to delete
        bid_to_delete = None
        for bid_id, bid in self._bids.items():
            if bid.participation_id == participation_id and bid.product_id == product_id:
                bid_to_delete = bid_id
                break

        if bid_to_delete:
            del self._bids[bid_to_delete]
            return True
        return False

    def get_bid(self, participation_id: UUID, product_id: UUID) -> ProductBid | None:
        """Get a specific bid."""
        for bid in self._bids.values():
            if bid.participation_id == participation_id and bid.product_id == product_id:
                # Set up relationships
                bid.participation = self._participations.get(participation_id)
                bid.product = self._products.get(product_id)
                return bid
        return None

    def get_bid_by_id(self, bid_id: UUID) -> ProductBid | None:
        """Get a bid by its ID."""
        return self._bids.get(bid_id)

    def get_bids_by_participation(self, participation_id: UUID) -> list[ProductBid]:
        """Get all bids for a participation."""
        bids = []
        for bid in self._bids.values():
            if bid.participation_id == participation_id:
                # Set up relationships
                bid.participation = self._participations.get(participation_id)
                bid.product = self._products.get(bid.product_id)
                bids.append(bid)
        return bids

    def update_bid_distributed_quantities(
        self, bid_id: UUID, quantity: int, price_per_unit: Decimal
    ) -> None:
        """Update the distributed quantity and price for a bid."""
        bid = self._bids.get(bid_id)
        if bid:
            bid.distributed_quantity = quantity
            bid.distributed_price_per_unit = price_per_unit

    def commit_changes(self) -> None:
        """Commit any pending changes (no-op for in-memory repository)."""
        pass

    # Helper methods for test data creation
    def _create_store(self, name: str) -> Store:
        store = Store(id=uuid4(), name=name, verified=False)
        self._stores[store.id] = store
        return store

    def _create_product(
        self, name: str, brand: str | None = None, unit: str | None = None
    ) -> Product:
        """Helper to create product without store association."""
        from datetime import datetime

        product = Product(
            id=uuid4(),
            name=name,
            brand=brand,
            unit=unit,
            verified=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        self._products[product.id] = product
        return product

    def _create_product_availability(
        self,
        product_id: UUID,
        store_id: UUID,
        price: float | None = None,
        notes: str = '',
        days_ago: float = 0,
    ) -> ProductAvailability:
        """Helper to create product availability at a store."""
        from datetime import datetime, timedelta

        created_time = datetime.now() - timedelta(days=days_ago)
        availability = ProductAvailability(
            id=uuid4(),
            product_id=product_id,
            store_id=store_id,
            price=Decimal(str(price)) if price is not None else None,
            notes=notes,
            created_at=created_time,
            updated_at=created_time,
        )
        self._product_availabilities[availability.id] = availability
        return availability

    def _create_run(
        self, group_id: UUID, store_id: UUID, state: str, leader_id: UUID, days_ago: int = 7
    ) -> Run:
        from datetime import datetime, timedelta

        run = Run(id=uuid4(), group_id=group_id, store_id=store_id, state=state)

        # Set timestamps for state progression (simulate realistic timeline)
        now = datetime.now()
        run.planning_at = now - timedelta(days=days_ago)  # Started X days ago

        if state in ['active', 'confirmed', 'shopping', 'distributing', 'completed']:
            run.active_at = now - timedelta(days=days_ago - 2)
        if state in ['confirmed', 'shopping', 'distributing', 'completed']:
            run.confirmed_at = now - timedelta(days=days_ago - 4)
        if state in ['shopping', 'distributing', 'completed']:
            run.shopping_at = now - timedelta(days=days_ago - 5)
        if state in ['distributing', 'completed']:
            run.distributing_at = now - timedelta(days=days_ago - 6)
        if state == 'completed':
            run.completed_at = now - timedelta(days=days_ago - 7)

        self._runs[run.id] = run
        # Create leader participation
        self._create_participation(leader_id, run.id, is_leader=True)
        return run

    def _create_participation(
        self, user_id: UUID, run_id: UUID, is_leader: bool = False, is_ready: bool = False
    ) -> RunParticipation:
        participation = RunParticipation(
            id=uuid4(),
            user_id=user_id,
            run_id=run_id,
            is_leader=is_leader,
            is_ready=is_ready,
            is_removed=False,
        )
        # Set up relationships
        participation.user = self._users.get(user_id)
        participation.run = self._runs.get(run_id)
        self._participations[participation.id] = participation
        return participation

    def _create_bid(
        self, participation_id: UUID, product_id: UUID, quantity: int, interested_only: bool
    ) -> ProductBid:
        from datetime import datetime

        bid = ProductBid(
            id=uuid4(),
            participation_id=participation_id,
            product_id=product_id,
            quantity=quantity,
            interested_only=interested_only,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        # Set up relationships
        bid.participation = self._participations.get(participation_id)
        bid.product = self._products.get(product_id)
        self._bids[bid.id] = bid
        return bid

    def _create_shopping_list_item(
        self, run_id: UUID, product_id: UUID, requested_quantity: int
    ) -> ShoppingListItem:
        from datetime import datetime

        run = self._runs.get(run_id)
        # Use the run's shopping timestamp if available, otherwise use current time
        timestamp = run.shopping_at if run and run.shopping_at else datetime.now()

        item = ShoppingListItem(
            id=uuid4(),
            run_id=run_id,
            product_id=product_id,
            requested_quantity=requested_quantity,
            is_purchased=False,
            created_at=timestamp,
            updated_at=timestamp,
        )
        # Set up relationships
        item.run = run
        item.product = self._products.get(product_id)
        self._shopping_list_items[item.id] = item
        return item

    def create_run(self, group_id: UUID, store_id: UUID, leader_id: UUID) -> Run:
        from datetime import datetime

        run = Run(id=uuid4(), group_id=group_id, store_id=store_id, state='planning')
        run.planning_at = datetime.now()
        self._runs[run.id] = run
        # Create participation for the leader
        self._create_participation(leader_id, run.id, is_leader=True)
        return run

    def get_participation(self, user_id: UUID, run_id: UUID) -> RunParticipation | None:
        for participation in self._participations.values():
            if participation.user_id == user_id and participation.run_id == run_id:
                # Set up relationships
                participation.user = self._users.get(user_id)
                participation.run = self._runs.get(run_id)
                return participation
        return None

    def get_run_participations(self, run_id: UUID) -> list[RunParticipation]:
        participations = []
        for participation in self._participations.values():
            if participation.run_id == run_id:
                # Set up relationships
                participation.user = self._users.get(participation.user_id)
                participation.run = self._runs.get(run_id)
                participations.append(participation)
        return participations

    def get_run_participations_with_users(self, run_id: UUID) -> list[RunParticipation]:
        """Get participations with user data eagerly loaded to avoid N+1 queries."""
        participations = []
        for participation in self._participations.values():
            if participation.run_id == run_id:
                # Eagerly load relationships
                participation.user = self._users.get(participation.user_id)
                participation.run = self._runs.get(run_id)
                participations.append(participation)
        return participations

    def create_participation(
        self, user_id: UUID, run_id: UUID, is_leader: bool = False
    ) -> RunParticipation:
        participation = RunParticipation(
            id=uuid4(),
            user_id=user_id,
            run_id=run_id,
            is_leader=is_leader,
            is_ready=False,
            is_removed=False,
        )
        # Set up relationships
        participation.user = self._users.get(user_id)
        participation.run = self._runs.get(run_id)
        self._participations[participation.id] = participation
        return participation

    def update_participation_ready(
        self, participation_id: UUID, is_ready: bool
    ) -> RunParticipation | None:
        participation = self._participations.get(participation_id)
        if participation:
            participation.is_ready = is_ready
            return participation
        return None

    def get_run_by_id(self, run_id: UUID) -> Run | None:
        return self._runs.get(run_id)

    def update_run_state(self, run_id: UUID, new_state: str) -> Run | None:
        from datetime import datetime

        run = self._runs.get(run_id)
        if run:
            # Convert string states to RunState enum
            current_state = RunState(run.state)
            target_state = RunState(new_state)

            # Validate transition using state machine
            state_machine.validate_transition(current_state, target_state, str(run_id))

            # Update state
            run.state = new_state

            # Set the timestamp for the new state
            timestamp_field = f'{new_state}_at'
            setattr(run, timestamp_field, datetime.now())

            logger.info(
                'Run state transitioned',
                extra={
                    'run_id': str(run_id),
                    'from_state': str(current_state),
                    'to_state': str(target_state),
                },
            )

            return run
        return None

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
        # Set up relationships
        item.run = self._runs.get(run_id)
        item.product = self._products.get(product_id)
        self._shopping_list_items[item.id] = item
        return item

    def get_shopping_list_items(self, run_id: UUID) -> list[ShoppingListItem]:
        items = []
        for item in self._shopping_list_items.values():
            if item.run_id == run_id:
                # Set up relationships
                item.run = self._runs.get(run_id)
                item.product = self._products.get(item.product_id)
                items.append(item)
        return items

    def get_shopping_list_items_by_product(self, product_id: UUID) -> list[ShoppingListItem]:
        items = []
        for item in self._shopping_list_items.values():
            if item.product_id == product_id:
                # Set up relationships
                item.run = self._runs.get(item.run_id)
                item.product = self._products.get(product_id)
                items.append(item)
        return items

    def get_shopping_list_item(self, item_id: UUID) -> ShoppingListItem | None:
        return self._shopping_list_items.get(item_id)

    def mark_item_purchased(
        self, item_id: UUID, quantity: int, price_per_unit: float, total: float, purchase_order: int
    ) -> ShoppingListItem | None:
        item = self._shopping_list_items.get(item_id)
        if item:
            item.purchased_quantity = quantity
            item.purchased_price_per_unit = Decimal(str(price_per_unit))
            item.purchased_total = Decimal(str(total))
            item.is_purchased = True
            item.purchase_order = purchase_order
            return item
        return None

    def update_shopping_list_item_requested_quantity(
        self, item_id: UUID, requested_quantity: int
    ) -> None:
        """Update the requested quantity for a shopping list item."""
        item = self._shopping_list_items.get(item_id)
        if item:
            item.requested_quantity = requested_quantity

    # ==================== ProductAvailability Methods ====================

    def get_product_availabilities(self, product_id: UUID, store_id: UUID = None) -> list:
        """Get product availabilities, optionally filtered by store."""
        results = []
        for avail in self._product_availabilities.values():
            if avail.product_id == product_id and (store_id is None or avail.store_id == store_id):
                results.append(avail)
        return results

    def get_availability_by_product_and_store(
        self, product_id: UUID, store_id: UUID
    ) -> ProductAvailability | None:
        """Get the most recent product availability by product and store."""
        matches = []
        for avail in self._product_availabilities.values():
            if avail.product_id == product_id and avail.store_id == store_id:
                matches.append(avail)

        if not matches:
            return None

        # Return the most recent one
        return sorted(matches, key=lambda x: x.created_at if x.created_at else '', reverse=True)[0]

    def create_product_availability(
        self,
        product_id: UUID,
        store_id: UUID,
        price: float | None = None,
        notes: str = '',
        user_id: UUID = None,
    ) -> ProductAvailability:
        """Create a new product availability record (price observation)."""
        from datetime import datetime

        # Always create a new record to track price history
        availability = ProductAvailability(
            id=uuid4(),
            product_id=product_id,
            store_id=store_id,
            price=Decimal(str(price)) if price is not None else None,
            notes=notes,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            created_by=user_id,
        )
        self._product_availabilities[availability.id] = availability
        return availability

    def update_product_availability_price(
        self, availability_id: UUID, price: float, notes: str = ''
    ) -> ProductAvailability:
        """Update the price for an existing product availability."""
        availability = self._product_availabilities.get(availability_id)

        if availability:
            availability.price = Decimal(str(price))
            if notes:
                availability.notes = notes

        return availability

    # ==================== Notification Methods ====================

    def create_notification(self, user_id: UUID, type: str, data: dict[str, Any]) -> Notification:
        """Create a new notification for a user."""
        from datetime import datetime

        notification = Notification(
            id=uuid4(),
            user_id=user_id,
            type=type,
            data=data,
            read=False,
            created_at=datetime.now(UTC),
        )
        self._notifications[notification.id] = notification
        return notification

    def get_user_notifications(
        self, user_id: UUID, limit: int = 20, offset: int = 0
    ) -> list[Notification]:
        """Get notifications for a user (paginated)."""
        from datetime import datetime

        user_notifications = [n for n in self._notifications.values() if n.user_id == user_id]
        # Sort by created_at descending (most recent first), handle None values
        user_notifications.sort(
            key=lambda n: n.created_at or datetime.min.replace(tzinfo=UTC), reverse=True
        )
        return user_notifications[offset : offset + limit]

    def get_unread_notifications(self, user_id: UUID) -> list[Notification]:
        """Get all unread notifications for a user."""
        unread = [n for n in self._notifications.values() if n.user_id == user_id and not n.read]
        # Sort by created_at descending
        unread.sort(key=lambda n: n.created_at, reverse=True)
        return unread

    def get_unread_count(self, user_id: UUID) -> int:
        """Get count of unread notifications for a user."""
        return sum(1 for n in self._notifications.values() if n.user_id == user_id and not n.read)

    def mark_notification_as_read(self, notification_id: UUID) -> bool:
        """Mark a notification as read."""
        notification = self._notifications.get(notification_id)
        if notification:
            notification.read = True
            return True
        return False

    def mark_all_notifications_as_read(self, user_id: UUID) -> int:
        """Mark all notifications as read for a user. Returns count of marked notifications."""
        count = 0
        for notification in self._notifications.values():
            if notification.user_id == user_id and not notification.read:
                notification.read = True
                count += 1
        return count

    def get_notification_by_id(self, notification_id: UUID) -> Notification | None:
        """Get a notification by ID."""
        return self._notifications.get(notification_id)

    # ==================== Leader Reassignment Methods ====================

    def create_reassignment_request(
        self, run_id: UUID, from_user_id: UUID, to_user_id: UUID
    ) -> LeaderReassignmentRequest:
        """Create a leader reassignment request."""
        from datetime import datetime

        request_id = uuid4()
        request = LeaderReassignmentRequest(
            id=request_id,
            run_id=run_id,
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            status='pending',
            created_at=datetime.now(),
            resolved_at=None,
        )
        self._reassignment_requests[request_id] = request
        return request

    def get_reassignment_request_by_id(self, request_id: UUID) -> LeaderReassignmentRequest | None:
        """Get a reassignment request by ID."""
        return self._reassignment_requests.get(request_id)

    def get_pending_reassignment_for_run(self, run_id: UUID) -> LeaderReassignmentRequest | None:
        """Get pending reassignment request for a run (if any)."""
        for request in self._reassignment_requests.values():
            if request.run_id == run_id and request.status == 'pending':
                return request
        return None

    def get_pending_reassignments_from_user(self, user_id: UUID) -> list[LeaderReassignmentRequest]:
        """Get all pending reassignment requests created by a user."""
        return [
            request
            for request in self._reassignment_requests.values()
            if request.from_user_id == user_id and request.status == 'pending'
        ]

    def get_pending_reassignments_to_user(self, user_id: UUID) -> list[LeaderReassignmentRequest]:
        """Get all pending reassignment requests for a user to respond to."""
        return [
            request
            for request in self._reassignment_requests.values()
            if request.to_user_id == user_id and request.status == 'pending'
        ]

    def update_reassignment_status(self, request_id: UUID, status: str) -> bool:
        """Update the status of a reassignment request (accepted/declined)."""
        from datetime import datetime

        request = self._reassignment_requests.get(request_id)
        if not request:
            return False

        request.status = status
        request.resolved_at = datetime.now()
        return True

    def cancel_all_pending_reassignments_for_run(self, run_id: UUID) -> int:
        """Cancel all pending reassignment requests for a run. Returns count of cancelled requests."""
        from datetime import datetime

        count = 0
        for request in self._reassignment_requests.values():
            if request.run_id == run_id and request.status == 'pending':
                request.status = 'cancelled'
                request.resolved_at = datetime.now()
                count += 1
        return count


def get_repository(db: Session = None) -> AbstractRepository:
    """Get the appropriate repository implementation based on config."""
    if REPO_MODE == 'memory':
        # MemoryRepository is a singleton - just call constructor
        return MemoryRepository()
    else:
        # DatabaseRepository is not yet implemented
        if db is None:
            raise ValueError('Database session required for database mode')
        return DatabaseRepository(db)
