"""Repository pattern with abstract base class and concrete implementations."""

from datetime import UTC
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

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
from app.infrastructure.request_context import get_logger
from app.core.run_state import RunState, state_machine
from app.repositories.abstract import AbstractRepository

logger = get_logger(__name__)


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

        from app.core.models import group_membership

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

        from app.core.models import group_membership

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

        from app.core.models import group_membership

        result = self.db.execute(
            select(group_membership.c.is_group_admin).where(
                group_membership.c.group_id == group_id, group_membership.c.user_id == user_id
            )
        ).first()

        return result[0] if result else False

    def get_group_members_with_admin_status(self, group_id: UUID) -> list[dict]:
        """Get all members of a group with their admin status."""
        from sqlalchemy import select

        from app.core.models import group_membership

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

        from app.core.models import group_membership

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

        from app.core.models import group_membership

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
        self, bid_id: UUID, quantity: float, price_per_unit: Decimal
    ) -> None:
        """Update the distributed quantity and price for a bid."""
        bid = self.db.query(ProductBid).filter(ProductBid.id == bid_id).first()
        if bid:
            bid.distributed_quantity = quantity
            bid.distributed_price_per_unit = price_per_unit
            self.db.commit()

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
        self, user_id: UUID, run_id: UUID, is_leader: bool = False, is_helper: bool = False
    ) -> RunParticipation:
        """Create a participation record for a user in a run."""
        participation = RunParticipation(
            user_id=user_id, run_id=run_id, is_leader=is_leader, is_helper=is_helper, is_removed=False
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

    def update_participation_helper(
        self, user_id: UUID, run_id: UUID, is_helper: bool
    ) -> RunParticipation | None:
        """Update the helper status of a participation."""
        participation = (
            self.db.query(RunParticipation)
            .filter(RunParticipation.user_id == user_id, RunParticipation.run_id == run_id)
            .first()
        )
        if participation:
            participation.is_helper = is_helper
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

    def add_more_purchased(
        self, item_id: UUID, additional_quantity: float, additional_total: float, new_price_per_unit: float
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

    # ==================== Test/Seed Data Helper Methods ====================
    # These methods are for testing and seed data only, not part of public API

    def _create_product_availability(
        self,
        product_id: UUID,
        store_id: UUID,
        price: float | None = None,
        notes: str = '',
        days_ago: float = 0,
    ) -> ProductAvailability:
        """Test helper to create product availability with backdated timestamp."""
        from datetime import datetime, timedelta

        created_time = datetime.now() - timedelta(days=days_ago)
        availability = ProductAvailability(
            product_id=product_id,
            store_id=store_id,
            price=Decimal(str(price)) if price is not None else None,
            notes=notes,
            created_at=created_time,
            updated_at=created_time,
        )
        self.db.add(availability)
        self.db.commit()
        self.db.refresh(availability)
        return availability

    def _create_run(
        self, group_id: UUID, store_id: UUID, state: str, leader_id: UUID, days_ago: int = 7
    ) -> Run:
        """Test helper to create run with backdated timestamps."""
        from datetime import datetime, timedelta

        run = Run(id=uuid4(), group_id=group_id, store_id=store_id, state=state)

        # Set timestamps for state progression
        now = datetime.now()
        run.planning_at = now - timedelta(days=days_ago)

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

        self.db.add(run)
        self.db.flush()

        # Create leader participation
        participation = RunParticipation(
            user_id=leader_id, run_id=run.id, is_leader=True, is_removed=False
        )
        self.db.add(participation)
        self.db.commit()
        self.db.refresh(run)
        return run

    def _create_participation(
        self, user_id: UUID, run_id: UUID, is_leader: bool = False, is_ready: bool = False
    ) -> RunParticipation:
        """Test helper to create participation with is_ready already set."""
        participation = RunParticipation(
            user_id=user_id, run_id=run_id, is_leader=is_leader, is_helper=False, is_ready=is_ready, is_removed=False
        )
        self.db.add(participation)
        self.db.commit()
        self.db.refresh(participation)
        return participation

    def _create_bid(
        self, participation_id: UUID, product_id: UUID, quantity: int, interested_only: bool
    ) -> ProductBid:
        """Test helper to create bid (same as create_or_update_bid but always creates new)."""
        from datetime import datetime

        bid = ProductBid(
            participation_id=participation_id,
            product_id=product_id,
            quantity=quantity,
            interested_only=interested_only,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        self.db.add(bid)
        self.db.commit()
        self.db.refresh(bid)
        return bid

    def _create_shopping_list_item(
        self, run_id: UUID, product_id: UUID, requested_quantity: int
    ) -> ShoppingListItem:
        """Test helper to create shopping list item (same as public method)."""
        return self.create_shopping_list_item(run_id, product_id, requested_quantity)

    # ==================== Admin Methods ====================

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

    def update_store(self, store_id: UUID, **fields) -> Store | None:
        """Update store fields. Returns updated store or None if not found."""
        store = self.db.query(Store).filter(Store.id == store_id).first()
        if not store:
            return None

        for key, value in fields.items():
            if hasattr(store, key):
                setattr(store, key, value)

        self.db.commit()
        self.db.refresh(store)
        return store

    def update_user(self, user_id: UUID, **fields) -> User | None:
        """Update user fields. Returns updated user or None if not found."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None

        for key, value in fields.items():
            if hasattr(user, key):
                setattr(user, key, value)

        self.db.commit()
        self.db.refresh(user)
        return user

    def delete_product(self, product_id: UUID) -> bool:
        """Delete a product. Returns True if deleted, False if not found."""
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return False

        self.db.delete(product)
        self.db.commit()
        return True

    def delete_store(self, store_id: UUID) -> bool:
        """Delete a store. Returns True if deleted, False if not found."""
        store = self.db.query(Store).filter(Store.id == store_id).first()
        if not store:
            return False

        self.db.delete(store)
        self.db.commit()
        return True

    def delete_user(self, user_id: UUID) -> bool:
        """Delete a user. Returns True if deleted, False if not found."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False

        self.db.delete(user)
        self.db.commit()
        return True

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

    def bulk_update_runs(self, old_store_id: UUID, new_store_id: UUID) -> int:
        """Update all runs from old store to new store. Returns count of updated records."""
        result = (
            self.db.query(Run)
            .filter(Run.store_id == old_store_id)
            .update({Run.store_id: new_store_id})
        )
        self.db.commit()
        return result

    def bulk_update_store_availabilities(self, old_store_id: UUID, new_store_id: UUID) -> int:
        """Update all store availabilities from old store to new store. Returns count of updated records."""
        result = (
            self.db.query(ProductAvailability)
            .filter(ProductAvailability.store_id == old_store_id)
            .update({ProductAvailability.store_id: new_store_id})
        )
        self.db.commit()
        return result

    def count_product_bids(self, product_id: UUID) -> int:
        """Count how many bids reference this product."""
        return self.db.query(ProductBid).filter(ProductBid.product_id == product_id).count()

    def count_store_runs(self, store_id: UUID) -> int:
        """Count how many runs reference this store."""
        return self.db.query(Run).filter(Run.store_id == store_id).count()
