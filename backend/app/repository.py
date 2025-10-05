"""Repository pattern with abstract base class and concrete implementations."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from uuid import UUID, uuid4
from sqlalchemy.orm import Session
from decimal import Decimal

from .models import User, Group, Store, Run, Product, ProductBid, RunParticipation, ShoppingListItem
from .config import get_repo_mode


class AbstractRepository(ABC):
    """Abstract base class defining the repository interface."""

    @abstractmethod
    def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        pass

    @abstractmethod
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        pass

    @abstractmethod
    def create_user(self, name: str, email: str, password_hash: str) -> User:
        """Create a new user."""
        pass

    @abstractmethod
    def get_user_groups(self, user: User) -> List[Group]:
        """Get all groups that a user is a member of."""
        pass

    @abstractmethod
    def get_group_by_id(self, group_id: UUID) -> Optional[Group]:
        """Get group by ID."""
        pass

    @abstractmethod
    def get_group_by_invite_token(self, invite_token: str) -> Optional[Group]:
        """Get group by invite token."""
        pass

    @abstractmethod
    def regenerate_group_invite_token(self, group_id: UUID) -> Optional[str]:
        """Regenerate invite token for a group."""
        pass

    @abstractmethod
    def create_group(self, name: str, created_by: UUID) -> Group:
        """Create a new group."""
        pass

    @abstractmethod
    def add_group_member(self, group_id: UUID, user: User) -> bool:
        """Add a user to a group."""
        pass

    @abstractmethod
    def get_all_stores(self) -> List[Store]:
        """Get all stores."""
        pass

    @abstractmethod
    def get_runs_by_group(self, group_id: UUID) -> List[Run]:
        """Get all runs for a group."""
        pass

    @abstractmethod
    def get_products_by_store(self, store_id: UUID) -> List[Product]:
        """Get all products for a store."""
        pass

    @abstractmethod
    def search_products(self, query: str) -> List[Product]:
        """Search for products by name."""
        pass

    @abstractmethod
    def get_product_by_id(self, product_id: UUID) -> Optional[Product]:
        """Get product by ID."""
        pass

    @abstractmethod
    def get_bids_by_run(self, run_id: UUID) -> List[ProductBid]:
        """Get all bids for a run."""
        pass

    @abstractmethod
    def verify_password(self, password: str, stored_hash: str) -> bool:
        """Verify a password."""
        pass

    @abstractmethod
    def create_run(self, group_id: UUID, store_id: UUID, leader_id: UUID) -> Run:
        """Create a new run with the leader as first participant."""
        pass

    @abstractmethod
    def get_participation(self, user_id: UUID, run_id: UUID) -> Optional[RunParticipation]:
        """Get a user's participation in a run."""
        pass

    @abstractmethod
    def get_run_participations(self, run_id: UUID) -> List[RunParticipation]:
        """Get all participations for a run."""
        pass

    @abstractmethod
    def create_participation(self, user_id: UUID, run_id: UUID, is_leader: bool = False) -> RunParticipation:
        """Create a participation record for a user in a run."""
        pass

    @abstractmethod
    def update_participation_ready(self, participation_id: UUID, is_ready: bool) -> Optional[RunParticipation]:
        """Update the ready status of a participation."""
        pass

    @abstractmethod
    def get_run_by_id(self, run_id: UUID) -> Optional[Run]:
        """Get run by ID."""
        pass

    @abstractmethod
    def update_run_state(self, run_id: UUID, new_state: str) -> Optional[Run]:
        """Update the state of a run."""
        pass

    @abstractmethod
    def create_shopping_list_item(self, run_id: UUID, product_id: UUID, requested_quantity: int) -> ShoppingListItem:
        """Create a shopping list item."""
        pass

    @abstractmethod
    def get_shopping_list_items(self, run_id: UUID) -> List[ShoppingListItem]:
        """Get all shopping list items for a run."""
        pass

    @abstractmethod
    def get_shopping_list_items_by_product(self, product_id: UUID) -> List[ShoppingListItem]:
        """Get all shopping list items for a product across all runs."""
        pass

    @abstractmethod
    def add_encountered_price(self, item_id: UUID, price: float, notes: str = "") -> Optional[ShoppingListItem]:
        """Add an encountered price to a shopping list item."""
        pass

    @abstractmethod
    def mark_item_purchased(self, item_id: UUID, quantity: int, price_per_unit: float, total: float, purchase_order: int) -> Optional[ShoppingListItem]:
        """Mark a shopping list item as purchased."""
        pass


class DatabaseRepository(AbstractRepository):
    """Database implementation using SQLAlchemy - Singleton."""

    _instance = None
    _db = None

    def __new__(cls, db: Session):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._db = db
        return cls._instance

    def __init__(self, db: Session):
        # Only initialize once
        if not hasattr(self, '_initialized'):
            self.db = db
            self._initialized = True

    @property
    def db(self):
        """Get the current database session."""
        return self._db

    @db.setter
    def db(self, value):
        """Update the database session."""
        DatabaseRepository._db = value

    def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def create_user(self, name: str, email: str, password_hash: str) -> User:
        user = User(name=name, email=email, password_hash=password_hash)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_user_groups(self, user: User) -> List[Group]:
        return self.db.query(Group).filter(Group.members.contains(user)).all()

    def get_group_by_id(self, group_id: UUID) -> Optional[Group]:
        return self.db.query(Group).filter(Group.id == group_id).first()

    def get_group_by_invite_token(self, invite_token: str) -> Optional[Group]:
        return self.db.query(Group).filter(Group.invite_token == invite_token).first()

    def regenerate_group_invite_token(self, group_id: UUID) -> Optional[str]:
        group = self.get_group_by_id(group_id)
        if group:
            new_token = str(uuid4())
            group.invite_token = new_token
            self.db.commit()
            return new_token
        return None

    def create_group(self, name: str, created_by: UUID) -> Group:
        group = Group(name=name, created_by=created_by)
        self.db.add(group)
        self.db.commit()
        self.db.refresh(group)
        return group

    def add_group_member(self, group_id: UUID, user: User) -> bool:
        group = self.get_group_by_id(group_id)
        if group and user not in group.members:
            group.members.append(user)
            self.db.commit()
            return True
        return False

    def get_all_stores(self) -> List[Store]:
        return self.db.query(Store).all()

    def get_runs_by_group(self, group_id: UUID) -> List[Run]:
        return self.db.query(Run).filter(Run.group_id == group_id).all()

    def get_products_by_store(self, store_id: UUID) -> List[Product]:
        return self.db.query(Product).filter(Product.store_id == store_id).all()

    def search_products(self, query: str) -> List[Product]:
        search_pattern = f"%{query}%"
        return self.db.query(Product).filter(Product.name.ilike(search_pattern)).all()

    def get_product_by_id(self, product_id: UUID) -> Optional[Product]:
        return self.db.query(Product).filter(Product.id == product_id).first()

    def get_bids_by_run(self, run_id: UUID) -> List[ProductBid]:
        # Get all participations for this run, then get their bids
        participations = self.db.query(RunParticipation).filter(RunParticipation.run_id == run_id).all()
        all_bids = []
        for participation in participations:
            all_bids.extend(participation.product_bids)
        return all_bids

    def verify_password(self, password: str, stored_hash: str) -> bool:
        from .auth import verify_password
        return verify_password(password, stored_hash)

    def create_run(self, group_id: UUID, store_id: UUID, leader_id: UUID) -> Run:
        run = Run(group_id=group_id, store_id=store_id, state="planning")
        self.db.add(run)
        self.db.flush()  # Get the run ID before creating participation

        # Create participation for the leader
        participation = RunParticipation(user_id=leader_id, run_id=run.id, is_leader=True, is_ready=False)
        self.db.add(participation)
        self.db.commit()
        self.db.refresh(run)
        return run

    def get_participation(self, user_id: UUID, run_id: UUID) -> Optional[RunParticipation]:
        return self.db.query(RunParticipation).filter(
            RunParticipation.user_id == user_id,
            RunParticipation.run_id == run_id
        ).first()

    def get_run_participations(self, run_id: UUID) -> List[RunParticipation]:
        return self.db.query(RunParticipation).filter(RunParticipation.run_id == run_id).all()

    def create_participation(self, user_id: UUID, run_id: UUID, is_leader: bool = False) -> RunParticipation:
        participation = RunParticipation(user_id=user_id, run_id=run_id, is_leader=is_leader, is_ready=False)
        self.db.add(participation)
        self.db.commit()
        self.db.refresh(participation)
        return participation

    def update_participation_ready(self, participation_id: UUID, is_ready: bool) -> Optional[RunParticipation]:
        participation = self.db.query(RunParticipation).filter(RunParticipation.id == participation_id).first()
        if participation:
            participation.is_ready = is_ready
            self.db.commit()
            self.db.refresh(participation)
            return participation
        return None

    def get_run_by_id(self, run_id: UUID) -> Optional[Run]:
        return self.db.query(Run).filter(Run.id == run_id).first()

    def update_run_state(self, run_id: UUID, new_state: str) -> Optional[Run]:
        run = self.get_run_by_id(run_id)
        if run:
            run.state = new_state
            self.db.commit()
            self.db.refresh(run)
            return run
        return None

    def create_shopping_list_item(self, run_id: UUID, product_id: UUID, requested_quantity: int) -> ShoppingListItem:
        item = ShoppingListItem(
            run_id=run_id,
            product_id=product_id,
            requested_quantity=requested_quantity,
            encountered_prices=[]
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def get_shopping_list_items(self, run_id: UUID) -> List[ShoppingListItem]:
        return self.db.query(ShoppingListItem).filter(ShoppingListItem.run_id == run_id).all()

    def get_shopping_list_items_by_product(self, product_id: UUID) -> List[ShoppingListItem]:
        return self.db.query(ShoppingListItem).filter(ShoppingListItem.product_id == product_id).all()

    def add_encountered_price(self, item_id: UUID, price: float, notes: str = "") -> Optional[ShoppingListItem]:
        item = self.db.query(ShoppingListItem).filter(ShoppingListItem.id == item_id).first()
        if item:
            if item.encountered_prices is None:
                item.encountered_prices = []
            prices = list(item.encountered_prices) if item.encountered_prices else []
            prices.append({"price": float(price), "notes": notes})
            item.encountered_prices = prices
            self.db.commit()
            self.db.refresh(item)
            return item
        return None

    def mark_item_purchased(self, item_id: UUID, quantity: int, price_per_unit: float, total: float, purchase_order: int) -> Optional[ShoppingListItem]:
        item = self.db.query(ShoppingListItem).filter(ShoppingListItem.id == item_id).first()
        if item:
            item.purchased_quantity = quantity
            item.purchased_price_per_unit = Decimal(str(price_per_unit))
            item.purchased_total = Decimal(str(total))
            item.is_purchased = True
            item.purchase_order = purchase_order

            # Add purchased price to encountered prices if not already there
            if item.encountered_prices is None:
                item.encountered_prices = []
            prices = list(item.encountered_prices) if item.encountered_prices else []
            prices.append({"price": float(price_per_unit), "notes": "purchased"})
            item.encountered_prices = prices

            self.db.commit()
            self.db.refresh(item)
            return item
        return None


class MemoryRepository(AbstractRepository):
    """In-memory implementation for testing and development - Singleton."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # Only initialize once
        if not hasattr(self, '_initialized'):
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

            # Create test data
            self._create_test_data()
            self._initialized = True

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
        run_planning = self._create_run(friends_group.id, costco.id, "planning", test_user.id)
        run_active = self._create_run(friends_group.id, sams.id, "active", test_user.id)
        run_confirmed = self._create_run(friends_group.id, costco.id, "confirmed", test_user.id)
        run_shopping = self._create_run(friends_group.id, sams.id, "shopping", test_user.id)
        run_distributing = self._create_run(friends_group.id, costco.id, "distributing", test_user.id)
        run_completed = self._create_run(friends_group.id, sams.id, "completed", test_user.id)

        # Planning run - test user is leader (no other participants yet)
        test_planning_p = self._create_participation(test_user.id, run_planning.id, is_leader=True)

        # Active run - test user is leader, others have bid
        # Multiple users bidding on same products
        test_active_p = self._create_participation(test_user.id, run_active.id, is_leader=True)
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
        test_confirmed_p = self._create_participation(test_user.id, run_confirmed.id, is_leader=True, is_ready=True)
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
        test_shopping_p = self._create_participation(test_user.id, run_shopping.id, is_leader=True)
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
        shopping_item1.encountered_prices = [{"price": 16.50, "notes": "aisle 7"}, {"price": 17.00, "notes": "end cap"}]
        shopping_item1.purchased_quantity = 4
        shopping_item1.purchased_price_per_unit = Decimal("16.50")
        shopping_item1.purchased_total = Decimal("66.00")
        shopping_item1.is_purchased = True
        shopping_item1.purchase_order = 1

        shopping_item2 = self._create_shopping_list_item(run_shopping.id, laundry_pods.id, 3)
        shopping_item2.encountered_prices = [{"price": 18.98, "notes": "front display"}]
        shopping_item2.purchased_quantity = 3
        shopping_item2.purchased_price_per_unit = Decimal("18.98")
        shopping_item2.purchased_total = Decimal("56.94")
        shopping_item2.is_purchased = True
        shopping_item2.purchase_order = 2

        # Distributing run - test user is leader, has distribution data
        # Multiple users bidding on same products
        test_dist_p = self._create_participation(test_user.id, run_distributing.id, is_leader=True)
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
        test_completed_p = self._create_participation(test_user.id, run_completed.id, is_leader=True)
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

    def get_all_stores(self) -> List[Store]:
        return list(self._stores.values())

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

    def verify_password(self, password: str, stored_hash: str) -> bool:
        # In memory mode, accept any password for ease of testing
        return True

    # Helper methods for test data creation
    def _create_store(self, name: str) -> Store:
        store = Store(id=uuid4(), name=name)
        self._stores[store.id] = store
        return store

    def _create_product(self, store_id: UUID, name: str, base_price: float) -> Product:
        product = Product(id=uuid4(), store_id=store_id, name=name, base_price=Decimal(str(base_price)))
        self._products[product.id] = product
        return product

    def _create_run(self, group_id: UUID, store_id: UUID, state: str, leader_id: UUID) -> Run:
        run = Run(id=uuid4(), group_id=group_id, store_id=store_id, state=state)
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
        bid = ProductBid(id=uuid4(), participation_id=participation_id, product_id=product_id, quantity=quantity, interested_only=interested_only)
        # Set up relationships
        bid.participation = self._participations.get(participation_id)
        bid.product = self._products.get(product_id)
        self._bids[bid.id] = bid
        return bid

    def _create_shopping_list_item(self, run_id: UUID, product_id: UUID, requested_quantity: int) -> ShoppingListItem:
        item = ShoppingListItem(
            id=uuid4(),
            run_id=run_id,
            product_id=product_id,
            requested_quantity=requested_quantity,
            encountered_prices=[],
            is_purchased=False
        )
        # Set up relationships
        item.run = self._runs.get(run_id)
        item.product = self._products.get(product_id)
        self._shopping_list_items[item.id] = item
        return item

    def create_run(self, group_id: UUID, store_id: UUID, leader_id: UUID) -> Run:
        run = Run(id=uuid4(), group_id=group_id, store_id=store_id, state="planning")
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
        run = self._runs.get(run_id)
        if run:
            run.state = new_state
            return run
        return None

    def create_shopping_list_item(self, run_id: UUID, product_id: UUID, requested_quantity: int) -> ShoppingListItem:
        item = ShoppingListItem(
            id=uuid4(),
            run_id=run_id,
            product_id=product_id,
            requested_quantity=requested_quantity,
            encountered_prices=[],
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
        item = self._shopping_list_items.get(item_id)
        if item:
            if item.encountered_prices is None:
                item.encountered_prices = []
            item.encountered_prices.append({"price": float(price), "notes": notes})
            return item
        return None

    def mark_item_purchased(self, item_id: UUID, quantity: int, price_per_unit: float, total: float, purchase_order: int) -> Optional[ShoppingListItem]:
        item = self._shopping_list_items.get(item_id)
        if item:
            item.purchased_quantity = quantity
            item.purchased_price_per_unit = Decimal(str(price_per_unit))
            item.purchased_total = Decimal(str(total))
            item.is_purchased = True
            item.purchase_order = purchase_order

            # Add purchased price to encountered prices if not already there
            if item.encountered_prices is None:
                item.encountered_prices = []
            item.encountered_prices.append({"price": float(price_per_unit), "notes": "purchased"})

            return item
        return None


def get_repository(db: Session = None) -> AbstractRepository:
    """Get the appropriate repository implementation based on config."""
    if get_repo_mode() == "memory":
        # MemoryRepository is now a singleton - just call constructor
        return MemoryRepository()
    else:
        # DatabaseRepository is now a singleton with updated db session
        if db is None:
            raise ValueError("Database session required for database mode")
        repo = DatabaseRepository(db)
        # Update the database session in case it changed
        repo.db = db
        return repo