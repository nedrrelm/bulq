"""Repository pattern with abstract base class and concrete implementations."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from sqlalchemy.orm import Session
from decimal import Decimal
import logging

from .models import User, Group, Store, Run, Product, ProductBid, RunParticipation, ShoppingListItem, EncounteredPrice
from .config import get_repo_mode
from .run_state import RunState, state_machine

logger = logging.getLogger(__name__)


class AbstractRepository(ABC):
    """Abstract base class defining the repository interface."""

    # ==================== User Methods ====================

    @abstractmethod
    def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        raise NotImplementedError("Subclass must implement get_user_by_id")

    @abstractmethod
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        raise NotImplementedError("Subclass must implement get_user_by_email")

    @abstractmethod
    def create_user(self, name: str, email: str, password_hash: str) -> User:
        """Create a new user."""
        raise NotImplementedError("Subclass must implement create_user")

    @abstractmethod
    def get_user_groups(self, user: User) -> List[Group]:
        """Get all groups that a user is a member of."""
        raise NotImplementedError("Subclass must implement get_user_groups")

    # ==================== Group Methods ====================

    @abstractmethod
    def get_group_by_id(self, group_id: UUID) -> Optional[Group]:
        """Get group by ID."""
        raise NotImplementedError("Subclass must implement get_group_by_id")

    @abstractmethod
    def get_group_by_invite_token(self, invite_token: str) -> Optional[Group]:
        """Get group by invite token."""
        raise NotImplementedError("Subclass must implement get_group_by_invite_token")

    @abstractmethod
    def regenerate_group_invite_token(self, group_id: UUID) -> Optional[str]:
        """Regenerate invite token for a group."""
        raise NotImplementedError("Subclass must implement regenerate_group_invite_token")

    @abstractmethod
    def create_group(self, name: str, created_by: UUID) -> Group:
        """Create a new group."""
        raise NotImplementedError("Subclass must implement create_group")

    @abstractmethod
    def add_group_member(self, group_id: UUID, user: User) -> bool:
        """Add a user to a group."""
        raise NotImplementedError("Subclass must implement add_group_member")

    # ==================== Store Methods ====================

    @abstractmethod
    def search_stores(self, query: str) -> List[Store]:
        """Search stores by name."""
        raise NotImplementedError("Subclass must implement search_stores")

    @abstractmethod
    def get_all_stores(self) -> List[Store]:
        """Get all stores."""
        raise NotImplementedError("Subclass must implement get_all_stores")

    @abstractmethod
    def create_store(self, name: str) -> Store:
        """Create a new store."""
        raise NotImplementedError("Subclass must implement create_store")

    @abstractmethod
    def get_store_by_id(self, store_id: UUID) -> Optional[Store]:
        """Get store by ID."""
        raise NotImplementedError("Subclass must implement get_store_by_id")

    @abstractmethod
    def get_products_by_store_from_encountered_prices(self, store_id: UUID) -> List[Product]:
        """Get all unique products that have encountered prices at a store."""
        raise NotImplementedError("Subclass must implement get_products_by_store_from_encountered_prices")

    @abstractmethod
    def get_active_runs_by_store_for_user(self, store_id: UUID, user_id: UUID) -> List[Run]:
        """Get all active runs for a store across all user's groups."""
        raise NotImplementedError("Subclass must implement get_active_runs_by_store_for_user")

    # ==================== Run Methods ====================

    @abstractmethod
    def get_runs_by_group(self, group_id: UUID) -> List[Run]:
        """Get all runs for a group."""
        raise NotImplementedError("Subclass must implement get_runs_by_group")

    # ==================== Product Methods ====================

    @abstractmethod
    def get_products_by_store(self, store_id: UUID) -> List[Product]:
        """Get all products for a store."""
        raise NotImplementedError("Subclass must implement get_products_by_store")

    @abstractmethod
    def search_products(self, query: str) -> List[Product]:
        """Search for products by name."""
        raise NotImplementedError("Subclass must implement search_products")

    @abstractmethod
    def get_product_by_id(self, product_id: UUID) -> Optional[Product]:
        """Get product by ID."""
        raise NotImplementedError("Subclass must implement get_product_by_id")

    @abstractmethod
    def create_product(self, store_id: UUID, name: str, base_price: float) -> Product:
        """Create a new product."""
        raise NotImplementedError("Subclass must implement create_product")

    # ==================== Product Bid Methods ====================

    @abstractmethod
    def get_bids_by_run(self, run_id: UUID) -> List[ProductBid]:
        """Get all bids for a run."""
        raise NotImplementedError("Subclass must implement get_bids_by_run")

    @abstractmethod
    def get_bids_by_run_with_participations(self, run_id: UUID) -> List[ProductBid]:
        """
        Get all bids for a run with participation and user data eagerly loaded.

        This avoids N+1 query problems when you need to access bid.participation.user.
        Each bid will have its participation object populated, and each participation
        will have its user object populated.
        """
        raise NotImplementedError("Subclass must implement get_bids_by_run_with_participations")

    @abstractmethod
    def create_or_update_bid(self, participation_id: UUID, product_id: UUID, quantity: int, interested_only: bool) -> ProductBid:
        """Create or update a product bid."""
        raise NotImplementedError("Subclass must implement create_or_update_bid")

    @abstractmethod
    def delete_bid(self, participation_id: UUID, product_id: UUID) -> bool:
        """Delete a product bid."""
        raise NotImplementedError("Subclass must implement delete_bid")

    @abstractmethod
    def get_bid(self, participation_id: UUID, product_id: UUID) -> Optional[ProductBid]:
        """Get a specific bid."""
        raise NotImplementedError("Subclass must implement get_bid")

    # ==================== Auth Methods ====================

    @abstractmethod
    def verify_password(self, password: str, stored_hash: str) -> bool:
        """Verify a password."""
        raise NotImplementedError("Subclass must implement verify_password")

    # ==================== Run & Participation Methods ====================

    @abstractmethod
    def create_run(self, group_id: UUID, store_id: UUID, leader_id: UUID) -> Run:
        """Create a new run with the leader as first participant."""
        raise NotImplementedError("Subclass must implement create_run")

    @abstractmethod
    def get_participation(self, user_id: UUID, run_id: UUID) -> Optional[RunParticipation]:
        """Get a user's participation in a run."""
        raise NotImplementedError("Subclass must implement get_participation")

    @abstractmethod
    def get_run_participations(self, run_id: UUID) -> List[RunParticipation]:
        """Get all participations for a run."""
        raise NotImplementedError("Subclass must implement get_run_participations")

    @abstractmethod
    def get_run_participations_with_users(self, run_id: UUID) -> List[RunParticipation]:
        """
        Get all participations for a run with user data eagerly loaded.

        This avoids N+1 query problems when you need to access participation.user.
        For DatabaseRepository, this should use SQLAlchemy's joinedload().
        For MemoryRepository, this pre-populates the user relationship.
        """
        raise NotImplementedError("Subclass must implement get_run_participations_with_users")

    @abstractmethod
    def create_participation(self, user_id: UUID, run_id: UUID, is_leader: bool = False) -> RunParticipation:
        """Create a participation record for a user in a run."""
        raise NotImplementedError("Subclass must implement create_participation")

    @abstractmethod
    def update_participation_ready(self, participation_id: UUID, is_ready: bool) -> Optional[RunParticipation]:
        """Update the ready status of a participation."""
        raise NotImplementedError("Subclass must implement update_participation_ready")

    @abstractmethod
    def get_run_by_id(self, run_id: UUID) -> Optional[Run]:
        """Get run by ID."""
        raise NotImplementedError("Subclass must implement get_run_by_id")

    @abstractmethod
    def update_run_state(self, run_id: UUID, new_state: str) -> Optional[Run]:
        """Update the state of a run."""
        raise NotImplementedError("Subclass must implement update_run_state")

    # ==================== Shopping List Methods ====================

    @abstractmethod
    def create_shopping_list_item(self, run_id: UUID, product_id: UUID, requested_quantity: int) -> ShoppingListItem:
        """Create a shopping list item."""
        raise NotImplementedError("Subclass must implement create_shopping_list_item")

    @abstractmethod
    def get_shopping_list_items(self, run_id: UUID) -> List[ShoppingListItem]:
        """Get all shopping list items for a run."""
        raise NotImplementedError("Subclass must implement get_shopping_list_items")

    @abstractmethod
    def get_shopping_list_items_by_product(self, product_id: UUID) -> List[ShoppingListItem]:
        """Get all shopping list items for a product across all runs."""
        raise NotImplementedError("Subclass must implement get_shopping_list_items_by_product")

    @abstractmethod
    def get_shopping_list_item(self, item_id: UUID) -> Optional[ShoppingListItem]:
        """Get a shopping list item by ID."""
        raise NotImplementedError("Subclass must implement get_shopping_list_item")

    @abstractmethod
    def add_encountered_price(self, item_id: UUID, price: float, notes: str = "") -> Optional[ShoppingListItem]:
        """Add an encountered price to a shopping list item."""
        raise NotImplementedError("Subclass must implement add_encountered_price")

    @abstractmethod
    def mark_item_purchased(self, item_id: UUID, quantity: int, price_per_unit: float, total: float, purchase_order: int) -> Optional[ShoppingListItem]:
        """Mark a shopping list item as purchased."""
        raise NotImplementedError("Subclass must implement mark_item_purchased")

    # ==================== EncounteredPrice Methods ====================

    @abstractmethod
    def get_encountered_prices(self, product_id: UUID, store_id: UUID, start_date: Any = None, end_date: Any = None) -> List:
        """Get encountered prices for a product at a store, optionally filtered by date range."""
        raise NotImplementedError("Subclass must implement get_encountered_prices")

    @abstractmethod
    def create_encountered_price(self, product_id: UUID, store_id: UUID, price: Any, notes: str = "", user_id: UUID = None) -> Any:
        """Create a new encountered price."""
        raise NotImplementedError("Subclass must implement create_encountered_price")


class DatabaseRepository(AbstractRepository):
    """
    Database implementation using SQLAlchemy.

    NOTE: This implementation is intentionally gutted and left as a stub.

    Why? We're currently only using MemoryRepository for development and testing.
    When we eventually need database persistence, we'll build this from scratch
    based on the working MemoryRepository implementation. This approach:

    1. Makes it clear we're only using MemoryRepository right now
    2. Avoids maintaining unused code
    3. Eliminates route anti-patterns (hasattr checks, direct private attribute access)
    4. Provides a clear interface to implement when database mode is needed

    When implementing this later, use MemoryRepository as the reference implementation.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        raise NotImplementedError("DatabaseRepository not yet implemented")

    def get_user_by_email(self, email: str) -> Optional[User]:
        raise NotImplementedError("DatabaseRepository not yet implemented")

    def create_user(self, name: str, email: str, password_hash: str) -> User:
        raise NotImplementedError("DatabaseRepository not yet implemented")

    def get_user_groups(self, user: User) -> List[Group]:
        raise NotImplementedError("DatabaseRepository not yet implemented")

    def get_group_by_id(self, group_id: UUID) -> Optional[Group]:
        raise NotImplementedError("DatabaseRepository not yet implemented")

    def get_group_by_invite_token(self, invite_token: str) -> Optional[Group]:
        raise NotImplementedError("DatabaseRepository not yet implemented")

    def regenerate_group_invite_token(self, group_id: UUID) -> Optional[str]:
        raise NotImplementedError("DatabaseRepository not yet implemented")

    def create_group(self, name: str, created_by: UUID) -> Group:
        raise NotImplementedError("DatabaseRepository not yet implemented")

    def add_group_member(self, group_id: UUID, user: User) -> bool:
        raise NotImplementedError("DatabaseRepository not yet implemented")

    def search_stores(self, query: str) -> List[Store]:
        raise NotImplementedError("DatabaseRepository not yet implemented")

    def get_all_stores(self) -> List[Store]:
        raise NotImplementedError("DatabaseRepository not yet implemented")

    def create_store(self, name: str) -> Store:
        raise NotImplementedError("DatabaseRepository not yet implemented")

    def get_store_by_id(self, store_id: UUID) -> Optional[Store]:
        raise NotImplementedError("DatabaseRepository not yet implemented")

    def get_products_by_store_from_encountered_prices(self, store_id: UUID) -> List[Product]:
        raise NotImplementedError("DatabaseRepository not yet implemented")

    def get_active_runs_by_store_for_user(self, store_id: UUID, user_id: UUID) -> List[Run]:
        raise NotImplementedError("DatabaseRepository not yet implemented")

    def get_runs_by_group(self, group_id: UUID) -> List[Run]:
        raise NotImplementedError("DatabaseRepository not yet implemented")

    def get_products_by_store(self, store_id: UUID) -> List[Product]:
        raise NotImplementedError("DatabaseRepository not yet implemented")

    def search_products(self, query: str) -> List[Product]:
        raise NotImplementedError("DatabaseRepository not yet implemented")

    def get_product_by_id(self, product_id: UUID) -> Optional[Product]:
        raise NotImplementedError("DatabaseRepository not yet implemented")

    def create_product(self, store_id: UUID, name: str, base_price: float) -> Product:
        raise NotImplementedError("DatabaseRepository not yet implemented")

    def get_bids_by_run(self, run_id: UUID) -> List[ProductBid]:
        raise NotImplementedError("DatabaseRepository not yet implemented")

    def get_bids_by_run_with_participations(self, run_id: UUID) -> List[ProductBid]:
        raise NotImplementedError("DatabaseRepository not yet implemented")

    def create_or_update_bid(self, participation_id: UUID, product_id: UUID, quantity: int, interested_only: bool) -> ProductBid:
        raise NotImplementedError("DatabaseRepository not yet implemented")

    def delete_bid(self, participation_id: UUID, product_id: UUID) -> bool:
        raise NotImplementedError("DatabaseRepository not yet implemented")

    def get_bid(self, participation_id: UUID, product_id: UUID) -> Optional[ProductBid]:
        raise NotImplementedError("DatabaseRepository not yet implemented")

    def verify_password(self, password: str, stored_hash: str) -> bool:
        raise NotImplementedError("DatabaseRepository not yet implemented")

    def create_run(self, group_id: UUID, store_id: UUID, leader_id: UUID) -> Run:
        raise NotImplementedError("DatabaseRepository not yet implemented")

    def get_participation(self, user_id: UUID, run_id: UUID) -> Optional[RunParticipation]:
        raise NotImplementedError("DatabaseRepository not yet implemented")

    def get_run_participations(self, run_id: UUID) -> List[RunParticipation]:
        raise NotImplementedError("DatabaseRepository not yet implemented")

    def get_run_participations_with_users(self, run_id: UUID) -> List[RunParticipation]:
        raise NotImplementedError("DatabaseRepository not yet implemented")

    def create_participation(self, user_id: UUID, run_id: UUID, is_leader: bool = False) -> RunParticipation:
        raise NotImplementedError("DatabaseRepository not yet implemented")

    def update_participation_ready(self, participation_id: UUID, is_ready: bool) -> Optional[RunParticipation]:
        raise NotImplementedError("DatabaseRepository not yet implemented")

    def get_run_by_id(self, run_id: UUID) -> Optional[Run]:
        raise NotImplementedError("DatabaseRepository not yet implemented")

    def update_run_state(self, run_id: UUID, new_state: str) -> Optional[Run]:
        raise NotImplementedError("DatabaseRepository not yet implemented")

    def create_shopping_list_item(self, run_id: UUID, product_id: UUID, requested_quantity: int) -> ShoppingListItem:
        raise NotImplementedError("DatabaseRepository not yet implemented")

    def get_shopping_list_items(self, run_id: UUID) -> List[ShoppingListItem]:
        raise NotImplementedError("DatabaseRepository not yet implemented")

    def get_shopping_list_items_by_product(self, product_id: UUID) -> List[ShoppingListItem]:
        raise NotImplementedError("DatabaseRepository not yet implemented")

    def get_shopping_list_item(self, item_id: UUID) -> Optional[ShoppingListItem]:
        raise NotImplementedError("DatabaseRepository not yet implemented")

    def add_encountered_price(self, item_id: UUID, price: float, notes: str = "") -> Optional[ShoppingListItem]:
        raise NotImplementedError("DatabaseRepository not yet implemented")

    def mark_item_purchased(self, item_id: UUID, quantity: int, price_per_unit: float, total: float, purchase_order: int) -> Optional[ShoppingListItem]:
        raise NotImplementedError("DatabaseRepository not yet implemented")

    def get_encountered_prices(self, product_id: UUID, store_id: UUID, start_date: Any = None, end_date: Any = None) -> List:
        raise NotImplementedError("DatabaseRepository not yet implemented")

    def create_encountered_price(self, product_id: UUID, store_id: UUID, price: Any, notes: str = "", user_id: UUID = None) -> Any:
        raise NotImplementedError("DatabaseRepository not yet implemented")


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
        self._users: Dict[UUID, User] = {}
        self._users_by_email: Dict[str, User] = {}
        self._groups: Dict[UUID, Group] = {}
        self._group_memberships: Dict[UUID, List[UUID]] = {}  # group_id -> [user_ids]
        self._stores: Dict[UUID, Store] = {}
        self._runs: Dict[UUID, Run] = {}
        self._products: Dict[UUID, Product] = {}
        self._participations: Dict[UUID, RunParticipation] = {}
        self._bids: Dict[UUID, ProductBid] = {}
        self._shopping_list_items: Dict[UUID, ShoppingListItem] = {}
        self._encountered_prices: Dict[UUID, EncounteredPrice] = {}

        # Create test data
        self._create_test_data()
        MemoryRepository._initialized = True

    def _create_test_data(self):
        """Create test data for memory mode."""
        # Create test users
        alice = self.create_user("Alice Johnson", "alice@test.com", "hashed_password")
        bob = self.create_user("Bob Smith", "bob@test.com", "hashed_password")
        carol = self.create_user("Carol Davis", "carol@test.com", "hashed_password")
        test_user = self.create_user("Test User", "test@example.com", "hashed_password")

        # Create test groups
        friends_group = self.create_group("Test Friends", alice.id)
        work_group = self.create_group("Work Lunch", bob.id)

        # Add members to groups
        self.add_group_member(friends_group.id, alice)
        self.add_group_member(friends_group.id, bob)
        self.add_group_member(friends_group.id, carol)
        self.add_group_member(friends_group.id, test_user)

        self.add_group_member(work_group.id, bob)
        self.add_group_member(work_group.id, carol)

        # Create test stores
        costco = self._create_store("Test Costco")
        sams = self._create_store("Test Sam's Club")

        # Create test products
        olive_oil = self._create_product(costco.id, "Test Olive Oil", 24.99)
        quinoa = self._create_product(costco.id, "Test Quinoa", 18.99)
        detergent = self._create_product(sams.id, "Test Detergent", 16.98)

        # Add more products for Costco (some without bids)
        paper_towels = self._create_product(costco.id, "Kirkland Paper Towels 12-pack", 19.99)
        rotisserie_chicken = self._create_product(costco.id, "Rotisserie Chicken", 4.99)
        almond_butter = self._create_product(costco.id, "Kirkland Almond Butter", 9.99)
        frozen_berries = self._create_product(costco.id, "Organic Frozen Berry Mix", 12.99)
        toilet_paper = self._create_product(costco.id, "Charmin Ultra Soft 24-pack", 22.99)
        coffee_beans = self._create_product(costco.id, "Kirkland Colombian Coffee", 14.99)

        # Add more products for Sam's Club
        laundry_pods = self._create_product(sams.id, "Tide Pods 81-count", 18.98)
        ground_beef = self._create_product(sams.id, "93/7 Ground Beef 3lbs", 16.48)
        bananas = self._create_product(sams.id, "Organic Bananas 3lbs", 4.98)
        cheese_sticks = self._create_product(sams.id, "String Cheese 48-pack", 8.98)

        # Create test runs - one for each state with test user as leader
        run_planning = self._create_run(friends_group.id, costco.id, "planning", test_user.id, days_ago=7)
        run_active = self._create_run(friends_group.id, sams.id, "active", test_user.id, days_ago=5)
        run_confirmed = self._create_run(friends_group.id, costco.id, "confirmed", test_user.id, days_ago=3)
        run_shopping = self._create_run(friends_group.id, sams.id, "shopping", test_user.id, days_ago=2)
        run_adjusting = self._create_run(friends_group.id, costco.id, "adjusting", test_user.id, days_ago=1.5)
        run_distributing = self._create_run(friends_group.id, costco.id, "distributing", test_user.id, days_ago=1)
        run_completed = self._create_run(friends_group.id, sams.id, "completed", test_user.id, days_ago=14)

        # Add more completed runs with different dates for better price history
        run_completed_2 = self._create_run(friends_group.id, costco.id, "completed", test_user.id, days_ago=30)
        run_completed_3 = self._create_run(friends_group.id, sams.id, "completed", alice.id, days_ago=45)
        run_completed_4 = self._create_run(friends_group.id, costco.id, "completed", bob.id, days_ago=60)
        run_completed_5 = self._create_run(work_group.id, sams.id, "completed", bob.id, days_ago=75)

        # Planning run - test user is leader (no other participants yet)
        # Leader participation already created by _create_run()
        test_planning_p = next((p for p in self._participations.values() if p.user_id == test_user.id and p.run_id == run_planning.id), None)

        # Active run - test user is leader, others have bid
        # Multiple users bidding on same products
        # Leader participation already created by _create_run()
        test_active_p = next((p for p in self._participations.values() if p.user_id == test_user.id and p.run_id == run_active.id), None)
        alice_active_p = self._create_participation(alice.id, run_active.id, is_leader=False)
        bob_active_p = self._create_participation(bob.id, run_active.id, is_leader=False)
        carol_active_p = self._create_participation(carol.id, run_active.id, is_leader=False)

        # Detergent - multiple users want it
        self._create_bid(test_active_p.id, detergent.id, 2, False)
        self._create_bid(alice_active_p.id, detergent.id, 1, False)
        self._create_bid(bob_active_p.id, detergent.id, 1, False)

        # Laundry Pods - just bob
        self._create_bid(bob_active_p.id, laundry_pods.id, 2, False)

        # Ground Beef - test user and carol
        self._create_bid(test_active_p.id, ground_beef.id, 1, False)
        self._create_bid(carol_active_p.id, ground_beef.id, 2, False)

        # Bananas - interested only from alice
        self._create_bid(alice_active_p.id, bananas.id, 0, True)

        # Confirmed run - test user is leader, all are ready
        # Leader participation already created by _create_run(), just update ready status
        test_confirmed_p = next((p for p in self._participations.values() if p.user_id == test_user.id and p.run_id == run_confirmed.id), None)
        test_confirmed_p.is_ready = True
        alice_confirmed_p = self._create_participation(alice.id, run_confirmed.id, is_leader=False, is_ready=True)
        carol_confirmed_p = self._create_participation(carol.id, run_confirmed.id, is_leader=False, is_ready=True)
        bob_confirmed_p = self._create_participation(bob.id, run_confirmed.id, is_leader=False, is_ready=True)

        # Olive Oil - everyone wants it
        self._create_bid(test_confirmed_p.id, olive_oil.id, 3, False)
        self._create_bid(alice_confirmed_p.id, olive_oil.id, 1, False)
        self._create_bid(bob_confirmed_p.id, olive_oil.id, 2, False)

        # Quinoa - carol and test user
        self._create_bid(test_confirmed_p.id, quinoa.id, 1, False)
        self._create_bid(carol_confirmed_p.id, quinoa.id, 2, False)

        # Paper Towels - everyone needs them
        self._create_bid(test_confirmed_p.id, paper_towels.id, 1, False)
        self._create_bid(alice_confirmed_p.id, paper_towels.id, 1, False)
        self._create_bid(bob_confirmed_p.id, paper_towels.id, 1, False)
        self._create_bid(carol_confirmed_p.id, paper_towels.id, 2, False)

        # Shopping run - test user is leader, has shopping list
        # Leader participation already created by _create_run()
        test_shopping_p = next((p for p in self._participations.values() if p.user_id == test_user.id and p.run_id == run_shopping.id), None)
        alice_shopping_p = self._create_participation(alice.id, run_shopping.id, is_leader=False)
        bob_shopping_p = self._create_participation(bob.id, run_shopping.id, is_leader=False)

        # Detergent - multiple users
        self._create_bid(test_shopping_p.id, detergent.id, 2, False)
        self._create_bid(alice_shopping_p.id, detergent.id, 1, False)
        self._create_bid(bob_shopping_p.id, detergent.id, 1, False)

        # Laundry Pods - test user and bob
        self._create_bid(test_shopping_p.id, laundry_pods.id, 1, False)
        self._create_bid(bob_shopping_p.id, laundry_pods.id, 2, False)

        # Create shopping list items
        shopping_item1 = self._create_shopping_list_item(run_shopping.id, detergent.id, 4)
        shopping_item1.purchased_quantity = 4
        shopping_item1.purchased_price_per_unit = Decimal("16.50")
        shopping_item1.purchased_total = Decimal("66.00")
        shopping_item1.is_purchased = True
        shopping_item1.purchase_order = 1

        shopping_item2 = self._create_shopping_list_item(run_shopping.id, laundry_pods.id, 3)
        shopping_item2.purchased_quantity = 3
        shopping_item2.purchased_price_per_unit = Decimal("18.98")
        shopping_item2.purchased_total = Decimal("56.94")
        shopping_item2.is_purchased = True
        shopping_item2.purchase_order = 2

        # Adjusting run - Test user is leader (friends group with Alice, Bob, Carol)
        # 3 products: 2 fully purchased, 1 with shortage (3 out of 6 bought, 3 bids of 2 each)
        # Note: test_adj_p is already created by _create_run as leader
        test_adj_p = next((p for p in self._participations.values() if p.user_id == test_user.id and p.run_id == run_adjusting.id), None)
        alice_adj_p = self._create_participation(alice.id, run_adjusting.id, is_leader=False)
        bob_adj_p = self._create_participation(bob.id, run_adjusting.id, is_leader=False)

        # Product 1: Olive Oil - fully purchased (3 requested, 3 bought)
        adj_bid1 = self._create_bid(test_adj_p.id, olive_oil.id, 1, False)
        adj_bid2 = self._create_bid(alice_adj_p.id, olive_oil.id, 2, False)

        # Product 2: Quinoa - fully purchased (4 requested, 4 bought)
        adj_bid3 = self._create_bid(bob_adj_p.id, quinoa.id, 2, False)
        adj_bid4 = self._create_bid(alice_adj_p.id, quinoa.id, 2, False)

        # Product 3: Paper Towels - SHORTAGE (6 requested, 3 bought) - 3 bids of 2 each
        adj_bid5 = self._create_bid(test_adj_p.id, paper_towels.id, 2, False)
        adj_bid6 = self._create_bid(alice_adj_p.id, paper_towels.id, 2, False)
        adj_bid7 = self._create_bid(bob_adj_p.id, paper_towels.id, 2, False)

        # Create shopping list items (as if shopping was completed)
        adj_item1 = self._create_shopping_list_item(run_adjusting.id, olive_oil.id, 3)
        adj_item1.purchased_quantity = 3  # Fully purchased
        adj_item1.purchased_price_per_unit = Decimal("24.99")
        adj_item1.purchased_total = Decimal("74.97")
        adj_item1.is_purchased = True
        adj_item1.purchase_order = 1

        adj_item2 = self._create_shopping_list_item(run_adjusting.id, quinoa.id, 4)
        adj_item2.purchased_quantity = 4  # Fully purchased
        adj_item2.purchased_price_per_unit = Decimal("18.99")
        adj_item2.purchased_total = Decimal("75.96")
        adj_item2.is_purchased = True
        adj_item2.purchase_order = 2

        adj_item3 = self._create_shopping_list_item(run_adjusting.id, paper_towels.id, 6)
        adj_item3.purchased_quantity = 3  # SHORTAGE: only 3 out of 6 bought
        adj_item3.purchased_price_per_unit = Decimal("19.99")
        adj_item3.purchased_total = Decimal("59.97")
        adj_item3.is_purchased = True
        adj_item3.purchase_order = 3

        # Distributing run - test user is leader, has distribution data
        # Multiple users bidding on same products
        # Leader participation already created by _create_run()
        test_dist_p = next((p for p in self._participations.values() if p.user_id == test_user.id and p.run_id == run_distributing.id), None)
        alice_dist_p = self._create_participation(alice.id, run_distributing.id, is_leader=False)
        bob_dist_p = self._create_participation(bob.id, run_distributing.id, is_leader=False)
        carol_dist_p = self._create_participation(carol.id, run_distributing.id, is_leader=False)

        # Olive Oil - multiple users ordered, test user picked up, others haven't
        bid1 = self._create_bid(test_dist_p.id, olive_oil.id, 2, False)
        bid1.distributed_quantity = 2
        bid1.distributed_price_per_unit = Decimal("23.99")
        bid1.is_picked_up = True

        bid2 = self._create_bid(alice_dist_p.id, olive_oil.id, 1, False)
        bid2.distributed_quantity = 1
        bid2.distributed_price_per_unit = Decimal("23.99")
        bid2.is_picked_up = False

        bid3 = self._create_bid(bob_dist_p.id, olive_oil.id, 3, False)
        bid3.distributed_quantity = 3
        bid3.distributed_price_per_unit = Decimal("23.99")
        bid3.is_picked_up = False

        # Quinoa - multiple users, some picked up
        bid4 = self._create_bid(test_dist_p.id, quinoa.id, 1, False)
        bid4.distributed_quantity = 1
        bid4.distributed_price_per_unit = Decimal("18.50")
        bid4.is_picked_up = True

        bid5 = self._create_bid(carol_dist_p.id, quinoa.id, 2, False)
        bid5.distributed_quantity = 2
        bid5.distributed_price_per_unit = Decimal("18.50")
        bid5.is_picked_up = True

        # Paper Towels - only Alice ordered, hasn't picked up yet
        bid6 = self._create_bid(alice_dist_p.id, paper_towels.id, 2, False)
        bid6.distributed_quantity = 2
        bid6.distributed_price_per_unit = Decimal("19.49")
        bid6.is_picked_up = False

        # Rotisserie Chicken - multiple users, none picked up
        bid7 = self._create_bid(bob_dist_p.id, rotisserie_chicken.id, 2, False)
        bid7.distributed_quantity = 2
        bid7.distributed_price_per_unit = Decimal("4.99")
        bid7.is_picked_up = False

        bid8 = self._create_bid(carol_dist_p.id, rotisserie_chicken.id, 1, False)
        bid8.distributed_quantity = 1
        bid8.distributed_price_per_unit = Decimal("4.99")
        bid8.is_picked_up = False

        # Almond Butter - only test user, already picked up
        bid9 = self._create_bid(test_dist_p.id, almond_butter.id, 1, False)
        bid9.distributed_quantity = 1
        bid9.distributed_price_per_unit = Decimal("9.99")
        bid9.is_picked_up = True

        # Completed run - test user is leader, all picked up
        # Leader participation already created by _create_run()
        test_completed_p = next((p for p in self._participations.values() if p.user_id == test_user.id and p.run_id == run_completed.id), None)
        alice_completed_p = self._create_participation(alice.id, run_completed.id, is_leader=False)
        carol_completed_p = self._create_participation(carol.id, run_completed.id, is_leader=False)

        # Detergent - test user and alice, both picked up
        bid10 = self._create_bid(test_completed_p.id, detergent.id, 2, False)
        bid10.distributed_quantity = 2
        bid10.distributed_price_per_unit = Decimal("16.48")
        bid10.is_picked_up = True

        bid11 = self._create_bid(alice_completed_p.id, detergent.id, 1, False)
        bid11.distributed_quantity = 1
        bid11.distributed_price_per_unit = Decimal("16.48")
        bid11.is_picked_up = True

        # Laundry Pods - carol and test user, all picked up
        bid12 = self._create_bid(test_completed_p.id, laundry_pods.id, 1, False)
        bid12.distributed_quantity = 1
        bid12.distributed_price_per_unit = Decimal("18.98")
        bid12.is_picked_up = True

        bid13 = self._create_bid(carol_completed_p.id, laundry_pods.id, 2, False)
        bid13.distributed_quantity = 2
        bid13.distributed_price_per_unit = Decimal("18.98")
        bid13.is_picked_up = True

        # Cheese Sticks - alice only, picked up
        bid14 = self._create_bid(alice_completed_p.id, cheese_sticks.id, 1, False)
        bid14.distributed_quantity = 1
        bid14.distributed_price_per_unit = Decimal("8.98")
        bid14.is_picked_up = True

        # Completed run 2 (30 days ago) - Costco run with different prices
        # Leader participation already created by _create_run()
        test_completed2_p = next((p for p in self._participations.values() if p.user_id == test_user.id and p.run_id == run_completed_2.id), None)
        alice_completed2_p = self._create_participation(alice.id, run_completed_2.id, is_leader=False)
        bob_completed2_p = self._create_participation(bob.id, run_completed_2.id, is_leader=False)

        # Olive Oil - price was higher 30 days ago
        bid15 = self._create_bid(test_completed2_p.id, olive_oil.id, 2, False)
        bid15.distributed_quantity = 2
        bid15.distributed_price_per_unit = Decimal("25.99")
        bid15.is_picked_up = True

        bid16 = self._create_bid(alice_completed2_p.id, olive_oil.id, 1, False)
        bid16.distributed_quantity = 1
        bid16.distributed_price_per_unit = Decimal("25.99")
        bid16.is_picked_up = True

        # Quinoa - different price
        bid17 = self._create_bid(bob_completed2_p.id, quinoa.id, 3, False)
        bid17.distributed_quantity = 3
        bid17.distributed_price_per_unit = Decimal("19.49")
        bid17.is_picked_up = True

        # Paper Towels
        bid18 = self._create_bid(test_completed2_p.id, paper_towels.id, 2, False)
        bid18.distributed_quantity = 2
        bid18.distributed_price_per_unit = Decimal("20.99")
        bid18.is_picked_up = True

        # Create shopping list for run_completed_2
        shopping_item3 = self._create_shopping_list_item(run_completed_2.id, olive_oil.id, 3)
        shopping_item3.purchased_quantity = 3
        shopping_item3.purchased_price_per_unit = Decimal("25.99")
        shopping_item3.purchased_total = Decimal("77.97")
        shopping_item3.is_purchased = True
        shopping_item3.purchase_order = 1

        shopping_item4 = self._create_shopping_list_item(run_completed_2.id, quinoa.id, 3)
        shopping_item4.purchased_quantity = 3
        shopping_item4.purchased_price_per_unit = Decimal("19.49")
        shopping_item4.purchased_total = Decimal("58.47")
        shopping_item4.is_purchased = True
        shopping_item4.purchase_order = 2

        shopping_item5 = self._create_shopping_list_item(run_completed_2.id, paper_towels.id, 2)
        shopping_item5.purchased_quantity = 2
        shopping_item5.purchased_price_per_unit = Decimal("20.99")
        shopping_item5.purchased_total = Decimal("41.98")
        shopping_item5.is_purchased = True
        shopping_item5.purchase_order = 3

        # Completed run 3 (45 days ago) - Sam's Club run led by alice
        # Leader participation already created by _create_run()
        alice_completed3_p = next((p for p in self._participations.values() if p.user_id == alice.id and p.run_id == run_completed_3.id), None)
        bob_completed3_p = self._create_participation(bob.id, run_completed_3.id, is_leader=False)
        carol_completed3_p = self._create_participation(carol.id, run_completed_3.id, is_leader=False)

        # Detergent - lower price 45 days ago
        bid19 = self._create_bid(alice_completed3_p.id, detergent.id, 2, False)
        bid19.distributed_quantity = 2
        bid19.distributed_price_per_unit = Decimal("15.98")
        bid19.is_picked_up = True

        bid20 = self._create_bid(bob_completed3_p.id, detergent.id, 1, False)
        bid20.distributed_quantity = 1
        bid20.distributed_price_per_unit = Decimal("15.98")
        bid20.is_picked_up = True

        # Laundry Pods - different price
        bid21 = self._create_bid(carol_completed3_p.id, laundry_pods.id, 2, False)
        bid21.distributed_quantity = 2
        bid21.distributed_price_per_unit = Decimal("17.98")
        bid21.is_picked_up = True

        # Ground Beef
        bid22 = self._create_bid(alice_completed3_p.id, ground_beef.id, 2, False)
        bid22.distributed_quantity = 2
        bid22.distributed_price_per_unit = Decimal("15.99")
        bid22.is_picked_up = True

        # Create shopping list for run_completed_3
        shopping_item6 = self._create_shopping_list_item(run_completed_3.id, detergent.id, 3)
        shopping_item6.purchased_quantity = 3
        shopping_item6.purchased_price_per_unit = Decimal("15.98")
        shopping_item6.purchased_total = Decimal("47.94")
        shopping_item6.is_purchased = True
        shopping_item6.purchase_order = 1

        shopping_item7 = self._create_shopping_list_item(run_completed_3.id, laundry_pods.id, 2)
        shopping_item7.purchased_quantity = 2
        shopping_item7.purchased_price_per_unit = Decimal("17.98")
        shopping_item7.purchased_total = Decimal("35.96")
        shopping_item7.is_purchased = True
        shopping_item7.purchase_order = 2

        shopping_item8 = self._create_shopping_list_item(run_completed_3.id, ground_beef.id, 2)
        shopping_item8.purchased_quantity = 2
        shopping_item8.purchased_price_per_unit = Decimal("15.99")
        shopping_item8.purchased_total = Decimal("31.98")
        shopping_item8.is_purchased = True
        shopping_item8.purchase_order = 3

        # Completed run 4 (60 days ago) - Costco run led by bob
        # Leader participation already created by _create_run()
        bob_completed4_p = next((p for p in self._participations.values() if p.user_id == bob.id and p.run_id == run_completed_4.id), None)
        alice_completed4_p = self._create_participation(alice.id, run_completed_4.id, is_leader=False)
        test_completed4_p = self._create_participation(test_user.id, run_completed_4.id, is_leader=False)

        # Olive Oil - even higher price 60 days ago
        bid23 = self._create_bid(bob_completed4_p.id, olive_oil.id, 1, False)
        bid23.distributed_quantity = 1
        bid23.distributed_price_per_unit = Decimal("26.99")
        bid23.is_picked_up = True

        bid24 = self._create_bid(alice_completed4_p.id, olive_oil.id, 2, False)
        bid24.distributed_quantity = 2
        bid24.distributed_price_per_unit = Decimal("26.99")
        bid24.is_picked_up = True

        # Quinoa
        bid25 = self._create_bid(test_completed4_p.id, quinoa.id, 1, False)
        bid25.distributed_quantity = 1
        bid25.distributed_price_per_unit = Decimal("20.99")
        bid25.is_picked_up = True

        # Coffee Beans
        bid26 = self._create_bid(bob_completed4_p.id, coffee_beans.id, 3, False)
        bid26.distributed_quantity = 3
        bid26.distributed_price_per_unit = Decimal("15.49")
        bid26.is_picked_up = True

        bid27 = self._create_bid(alice_completed4_p.id, coffee_beans.id, 1, False)
        bid27.distributed_quantity = 1
        bid27.distributed_price_per_unit = Decimal("15.49")
        bid27.is_picked_up = True

        # Create shopping list for run_completed_4
        shopping_item9 = self._create_shopping_list_item(run_completed_4.id, olive_oil.id, 3)
        shopping_item9.purchased_quantity = 3
        shopping_item9.purchased_price_per_unit = Decimal("26.99")
        shopping_item9.purchased_total = Decimal("80.97")
        shopping_item9.is_purchased = True
        shopping_item9.purchase_order = 1

        shopping_item10 = self._create_shopping_list_item(run_completed_4.id, quinoa.id, 1)
        shopping_item10.purchased_quantity = 1
        shopping_item10.purchased_price_per_unit = Decimal("20.99")
        shopping_item10.purchased_total = Decimal("20.99")
        shopping_item10.is_purchased = True
        shopping_item10.purchase_order = 2

        shopping_item11 = self._create_shopping_list_item(run_completed_4.id, coffee_beans.id, 4)
        shopping_item11.purchased_quantity = 4
        shopping_item11.purchased_price_per_unit = Decimal("15.49")
        shopping_item11.purchased_total = Decimal("61.96")
        shopping_item11.is_purchased = True
        shopping_item11.purchase_order = 3

        # Completed run 5 (75 days ago) - Sam's Club run for work group
        # Leader participation already created by _create_run()
        bob_completed5_p = next((p for p in self._participations.values() if p.user_id == bob.id and p.run_id == run_completed_5.id), None)
        carol_completed5_p = self._create_participation(carol.id, run_completed_5.id, is_leader=False)

        # Detergent - different price 75 days ago
        bid28 = self._create_bid(bob_completed5_p.id, detergent.id, 3, False)
        bid28.distributed_quantity = 3
        bid28.distributed_price_per_unit = Decimal("17.48")
        bid28.is_picked_up = True

        # Cheese Sticks
        bid29 = self._create_bid(carol_completed5_p.id, cheese_sticks.id, 2, False)
        bid29.distributed_quantity = 2
        bid29.distributed_price_per_unit = Decimal("9.48")
        bid29.is_picked_up = True

        # Bananas
        bid30 = self._create_bid(bob_completed5_p.id, bananas.id, 1, False)
        bid30.distributed_quantity = 1
        bid30.distributed_price_per_unit = Decimal("4.48")
        bid30.is_picked_up = True

        # Create shopping list for run_completed_5
        shopping_item12 = self._create_shopping_list_item(run_completed_5.id, detergent.id, 3)
        shopping_item12.purchased_quantity = 3
        shopping_item12.purchased_price_per_unit = Decimal("17.48")
        shopping_item12.purchased_total = Decimal("52.44")
        shopping_item12.is_purchased = True
        shopping_item12.purchase_order = 1

        shopping_item13 = self._create_shopping_list_item(run_completed_5.id, cheese_sticks.id, 2)
        shopping_item13.purchased_quantity = 2
        shopping_item13.purchased_price_per_unit = Decimal("9.48")
        shopping_item13.purchased_total = Decimal("18.96")
        shopping_item13.is_purchased = True
        shopping_item13.purchase_order = 2

        shopping_item14 = self._create_shopping_list_item(run_completed_5.id, bananas.id, 1)
        shopping_item14.purchased_quantity = 1
        shopping_item14.purchased_price_per_unit = Decimal("4.48")
        shopping_item14.purchased_total = Decimal("4.48")
        shopping_item14.is_purchased = True
        shopping_item14.purchase_order = 3

        # Create EncounteredPrice entities for products at stores
        # These show up on the store page
        from datetime import datetime, timedelta

        # Costco prices
        self.create_encountered_price(olive_oil.id, costco.id, Decimal("24.99"), "aisle 12", alice.id)
        self.create_encountered_price(quinoa.id, costco.id, Decimal("18.99"), "organic section", test_user.id)
        self.create_encountered_price(paper_towels.id, costco.id, Decimal("19.99"), "household", bob.id)
        self.create_encountered_price(rotisserie_chicken.id, costco.id, Decimal("4.99"), "deli section", alice.id)
        self.create_encountered_price(almond_butter.id, costco.id, Decimal("9.99"), "aisle 8", test_user.id)
        self.create_encountered_price(frozen_berries.id, costco.id, Decimal("12.99"), "frozen section", carol.id)
        self.create_encountered_price(toilet_paper.id, costco.id, Decimal("22.99"), "aisle 2", bob.id)
        self.create_encountered_price(coffee_beans.id, costco.id, Decimal("14.99"), "aisle 10", alice.id)

        # Sam's Club prices
        self.create_encountered_price(detergent.id, sams.id, Decimal("16.98"), "aisle 7", test_user.id)
        self.create_encountered_price(laundry_pods.id, sams.id, Decimal("18.98"), "front display", bob.id)
        self.create_encountered_price(ground_beef.id, sams.id, Decimal("16.48"), "meat department", alice.id)
        self.create_encountered_price(bananas.id, sams.id, Decimal("4.98"), "produce", carol.id)
        self.create_encountered_price(cheese_sticks.id, sams.id, Decimal("8.98"), "dairy section", test_user.id)

    def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        return self._users.get(user_id)

    def get_user_by_email(self, email: str) -> Optional[User]:
        return self._users_by_email.get(email)

    def create_user(self, name: str, email: str, password_hash: str) -> User:
        user = User(id=uuid4(), name=name, email=email, password_hash=password_hash)
        self._users[user.id] = user
        self._users_by_email[email] = user
        return user

    def get_user_groups(self, user: User) -> List[Group]:
        user_groups = []
        for group_id, member_ids in self._group_memberships.items():
            if user.id in member_ids:
                group = self._groups.get(group_id)
                if group:
                    # Set up relationships for compatibility
                    group.creator = self._users.get(group.created_by)
                    group.members = [self._users.get(uid) for uid in member_ids if uid in self._users]
                    user_groups.append(group)
        return user_groups

    def get_group_by_id(self, group_id: UUID) -> Optional[Group]:
        group = self._groups.get(group_id)
        if group:
            # Set up relationships
            group.creator = self._users.get(group.created_by)
            member_ids = self._group_memberships.get(group_id, [])
            group.members = [self._users.get(uid) for uid in member_ids if uid in self._users]
        return group

    def get_group_by_invite_token(self, invite_token: str) -> Optional[Group]:
        for group in self._groups.values():
            if group.invite_token == invite_token:
                # Set up relationships
                group.creator = self._users.get(group.created_by)
                member_ids = self._group_memberships.get(group.id, [])
                group.members = [self._users.get(uid) for uid in member_ids if uid in self._users]
                return group
        return None

    def regenerate_group_invite_token(self, group_id: UUID) -> Optional[str]:
        group = self._groups.get(group_id)
        if group:
            new_token = str(uuid4())
            group.invite_token = new_token
            return new_token
        return None

    def create_group(self, name: str, created_by: UUID) -> Group:
        group = Group(id=uuid4(), name=name, created_by=created_by, invite_token=str(uuid4()))
        self._groups[group.id] = group
        self._group_memberships[group.id] = []
        return group

    def add_group_member(self, group_id: UUID, user: User) -> bool:
        if group_id in self._group_memberships and user.id not in self._group_memberships[group_id]:
            self._group_memberships[group_id].append(user.id)
            return True
        return False

    def search_stores(self, query: str) -> List[Store]:
        query_lower = query.lower()
        return [
            store for store in self._stores.values()
            if query_lower in store.name.lower()
        ]

    def get_all_stores(self) -> List[Store]:
        return list(self._stores.values())

    def get_store_by_id(self, store_id: UUID) -> Optional[Store]:
        return self._stores.get(store_id)

    def get_products_by_store_from_encountered_prices(self, store_id: UUID) -> List[Product]:
        """Get all unique products that have encountered prices at a store."""
        product_ids = set()
        for ep in self._encountered_prices.values():
            if ep.store_id == store_id:
                product_ids.add(ep.product_id)
        return [self._products[pid] for pid in product_ids if pid in self._products]

    def get_active_runs_by_store_for_user(self, store_id: UUID, user_id: UUID) -> List[Run]:
        """Get all active runs for a store across all user's groups."""
        # Get user's groups
        user_group_ids = self._group_memberships.get(user_id, [])

        # Get runs for those groups that target this store and are active
        active_states = ['planning', 'active', 'confirmed', 'shopping', 'adjusting', 'distributing']
        runs = []
        for run in self._runs.values():
            if run.store_id == store_id and run.state in active_states and run.group_id in user_group_ids:
                runs.append(run)
        return runs

    def get_runs_by_group(self, group_id: UUID) -> List[Run]:
        return [run for run in self._runs.values() if run.group_id == group_id]

    def get_products_by_store(self, store_id: UUID) -> List[Product]:
        return [product for product in self._products.values() if product.store_id == store_id]

    def search_products(self, query: str) -> List[Product]:
        query_lower = query.lower()
        return [product for product in self._products.values() if query_lower in product.name.lower()]

    def get_product_by_id(self, product_id: UUID) -> Optional[Product]:
        return self._products.get(product_id)

    def get_bids_by_run(self, run_id: UUID) -> List[ProductBid]:
        # Get all participations for this run
        participations = [p for p in self._participations.values() if p.run_id == run_id]
        participation_ids = {p.id for p in participations}
        # Get all bids for these participations
        return [bid for bid in self._bids.values() if bid.participation_id in participation_ids]

    def get_bids_by_run_with_participations(self, run_id: UUID) -> List[ProductBid]:
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
                bid.participation = next((p for p in participations if p.id == bid.participation_id), None)
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

    def create_product(self, store_id: UUID, name: str, base_price: float) -> Product:
        """Create a new product."""
        from datetime import datetime
        product = Product(
            id=uuid4(),
            store_id=store_id,
            name=name,
            base_price=Decimal(str(base_price)),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self._products[product.id] = product
        return product

    def create_or_update_bid(self, participation_id: UUID, product_id: UUID, quantity: int, interested_only: bool) -> ProductBid:
        """Create or update a product bid."""
        from datetime import datetime
        # Check if bid already exists
        existing_bid = self.get_bid(participation_id, product_id)
        if existing_bid:
            # Update existing bid
            existing_bid.quantity = quantity
            existing_bid.interested_only = interested_only
            existing_bid.updated_at = datetime.utcnow()
            return existing_bid
        else:
            # Create new bid
            bid = ProductBid(
                id=uuid4(),
                participation_id=participation_id,
                product_id=product_id,
                quantity=quantity,
                interested_only=interested_only,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
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

    def get_bid(self, participation_id: UUID, product_id: UUID) -> Optional[ProductBid]:
        """Get a specific bid."""
        for bid in self._bids.values():
            if bid.participation_id == participation_id and bid.product_id == product_id:
                # Set up relationships
                bid.participation = self._participations.get(participation_id)
                bid.product = self._products.get(product_id)
                return bid
        return None

    # Helper methods for test data creation
    def _create_store(self, name: str) -> Store:
        store = Store(id=uuid4(), name=name)
        self._stores[store.id] = store
        return store

    def _create_product(self, store_id: UUID, name: str, base_price: float) -> Product:
        from datetime import datetime
        product = Product(
            id=uuid4(),
            store_id=store_id,
            name=name,
            base_price=Decimal(str(base_price)),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self._products[product.id] = product
        return product

    def _create_run(self, group_id: UUID, store_id: UUID, state: str, leader_id: UUID, days_ago: int = 7) -> Run:
        from datetime import datetime, timedelta
        run = Run(id=uuid4(), group_id=group_id, store_id=store_id, state=state)

        # Set timestamps for state progression (simulate realistic timeline)
        now = datetime.utcnow()
        run.planning_at = now - timedelta(days=days_ago)  # Started X days ago

        if state in ["active", "confirmed", "shopping", "distributing", "completed"]:
            run.active_at = now - timedelta(days=days_ago - 2)
        if state in ["confirmed", "shopping", "distributing", "completed"]:
            run.confirmed_at = now - timedelta(days=days_ago - 4)
        if state in ["shopping", "distributing", "completed"]:
            run.shopping_at = now - timedelta(days=days_ago - 5)
        if state in ["distributing", "completed"]:
            run.distributing_at = now - timedelta(days=days_ago - 6)
        if state == "completed":
            run.completed_at = now - timedelta(days=days_ago - 7)

        self._runs[run.id] = run
        # Create leader participation
        self._create_participation(leader_id, run.id, is_leader=True)
        return run

    def _create_participation(self, user_id: UUID, run_id: UUID, is_leader: bool = False, is_ready: bool = False) -> RunParticipation:
        participation = RunParticipation(id=uuid4(), user_id=user_id, run_id=run_id, is_leader=is_leader, is_ready=is_ready)
        # Set up relationships
        participation.user = self._users.get(user_id)
        participation.run = self._runs.get(run_id)
        self._participations[participation.id] = participation
        return participation

    def _create_bid(self, participation_id: UUID, product_id: UUID, quantity: int, interested_only: bool) -> ProductBid:
        from datetime import datetime
        bid = ProductBid(
            id=uuid4(),
            participation_id=participation_id,
            product_id=product_id,
            quantity=quantity,
            interested_only=interested_only,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        # Set up relationships
        bid.participation = self._participations.get(participation_id)
        bid.product = self._products.get(product_id)
        self._bids[bid.id] = bid
        return bid

    def _create_shopping_list_item(self, run_id: UUID, product_id: UUID, requested_quantity: int) -> ShoppingListItem:
        from datetime import datetime
        run = self._runs.get(run_id)
        # Use the run's shopping timestamp if available, otherwise use current time
        timestamp = run.shopping_at if run and run.shopping_at else datetime.utcnow()

        item = ShoppingListItem(
            id=uuid4(),
            run_id=run_id,
            product_id=product_id,
            requested_quantity=requested_quantity,
            is_purchased=False,
            created_at=timestamp,
            updated_at=timestamp
        )
        # Set up relationships
        item.run = run
        item.product = self._products.get(product_id)
        self._shopping_list_items[item.id] = item
        return item

    def create_run(self, group_id: UUID, store_id: UUID, leader_id: UUID) -> Run:
        from datetime import datetime
        run = Run(id=uuid4(), group_id=group_id, store_id=store_id, state="planning")
        run.planning_at = datetime.utcnow()
        self._runs[run.id] = run
        # Create participation for the leader
        self._create_participation(leader_id, run.id, is_leader=True)
        return run

    def get_participation(self, user_id: UUID, run_id: UUID) -> Optional[RunParticipation]:
        for participation in self._participations.values():
            if participation.user_id == user_id and participation.run_id == run_id:
                # Set up relationships
                participation.user = self._users.get(user_id)
                participation.run = self._runs.get(run_id)
                return participation
        return None

    def get_run_participations(self, run_id: UUID) -> List[RunParticipation]:
        participations = []
        for participation in self._participations.values():
            if participation.run_id == run_id:
                # Set up relationships
                participation.user = self._users.get(participation.user_id)
                participation.run = self._runs.get(run_id)
                participations.append(participation)
        return participations

    def get_run_participations_with_users(self, run_id: UUID) -> List[RunParticipation]:
        """Get participations with user data eagerly loaded to avoid N+1 queries."""
        participations = []
        for participation in self._participations.values():
            if participation.run_id == run_id:
                # Eagerly load relationships
                participation.user = self._users.get(participation.user_id)
                participation.run = self._runs.get(run_id)
                participations.append(participation)
        return participations

    def create_participation(self, user_id: UUID, run_id: UUID, is_leader: bool = False) -> RunParticipation:
        participation = RunParticipation(id=uuid4(), user_id=user_id, run_id=run_id, is_leader=is_leader, is_ready=False)
        # Set up relationships
        participation.user = self._users.get(user_id)
        participation.run = self._runs.get(run_id)
        self._participations[participation.id] = participation
        return participation

    def update_participation_ready(self, participation_id: UUID, is_ready: bool) -> Optional[RunParticipation]:
        participation = self._participations.get(participation_id)
        if participation:
            participation.is_ready = is_ready
            return participation
        return None

    def get_run_by_id(self, run_id: UUID) -> Optional[Run]:
        return self._runs.get(run_id)

    def update_run_state(self, run_id: UUID, new_state: str) -> Optional[Run]:
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
            timestamp_field = f"{new_state}_at"
            if hasattr(run, timestamp_field):
                setattr(run, timestamp_field, datetime.utcnow())

            logger.info(
                f"Run state transitioned",
                extra={
                    "run_id": str(run_id),
                    "from_state": str(current_state),
                    "to_state": str(target_state)
                }
            )

            return run
        return None

    def create_shopping_list_item(self, run_id: UUID, product_id: UUID, requested_quantity: int) -> ShoppingListItem:
        item = ShoppingListItem(
            id=uuid4(),
            run_id=run_id,
            product_id=product_id,
            requested_quantity=requested_quantity,
            is_purchased=False
        )
        # Set up relationships
        item.run = self._runs.get(run_id)
        item.product = self._products.get(product_id)
        self._shopping_list_items[item.id] = item
        return item

    def get_shopping_list_items(self, run_id: UUID) -> List[ShoppingListItem]:
        items = []
        for item in self._shopping_list_items.values():
            if item.run_id == run_id:
                # Set up relationships
                item.run = self._runs.get(run_id)
                item.product = self._products.get(item.product_id)
                items.append(item)
        return items

    def get_shopping_list_items_by_product(self, product_id: UUID) -> List[ShoppingListItem]:
        items = []
        for item in self._shopping_list_items.values():
            if item.product_id == product_id:
                # Set up relationships
                item.run = self._runs.get(item.run_id)
                item.product = self._products.get(product_id)
                items.append(item)
        return items

    def add_encountered_price(self, item_id: UUID, price: float, notes: str = "") -> Optional[ShoppingListItem]:
        """
        DEPRECATED: This method used to add encountered prices to shopping list items.
        Now use create_encountered_price() to create proper EncounteredPrice entities instead.
        This method is kept for backwards compatibility but does nothing.
        """
        item = self._shopping_list_items.get(item_id)
        return item

    def get_shopping_list_item(self, item_id: UUID) -> Optional[ShoppingListItem]:
        return self._shopping_list_items.get(item_id)

    def mark_item_purchased(self, item_id: UUID, quantity: int, price_per_unit: float, total: float, purchase_order: int) -> Optional[ShoppingListItem]:
        item = self._shopping_list_items.get(item_id)
        if item:
            item.purchased_quantity = quantity
            item.purchased_price_per_unit = Decimal(str(price_per_unit))
            item.purchased_total = Decimal(str(total))
            item.is_purchased = True
            item.purchase_order = purchase_order
            return item
        return None

    # ==================== EncounteredPrice Methods ====================

    def get_encountered_prices(self, product_id: UUID, store_id: UUID, start_date: Any = None, end_date: Any = None) -> List:
        """Get encountered prices for a product at a store, optionally filtered by date range."""
        results = []
        for ep in self._encountered_prices.values():
            if ep.product_id == product_id and ep.store_id == store_id:
                if start_date and end_date:
                    if start_date <= ep.encountered_at < end_date:
                        results.append(ep)
                else:
                    results.append(ep)
        return results

    def create_encountered_price(self, product_id: UUID, store_id: UUID, price: Any, notes: str = "", user_id: UUID = None) -> Any:
        """Create a new encountered price."""
        from datetime import datetime

        ep = EncounteredPrice(
            id=uuid4(),
            product_id=product_id,
            store_id=store_id,
            price=price,
            notes=notes,
            encountered_at=datetime.now(),
            encountered_by=user_id
        )
        self._encountered_prices[ep.id] = ep
        return ep


def get_repository(db: Session = None) -> AbstractRepository:
    """Get the appropriate repository implementation based on config."""
    if get_repo_mode() == "memory":
        # MemoryRepository is a singleton - just call constructor
        return MemoryRepository()
    else:
        # DatabaseRepository is not yet implemented
        if db is None:
            raise ValueError("Database session required for database mode")
        return DatabaseRepository(db)