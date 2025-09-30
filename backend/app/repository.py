"""Repository pattern with abstract base class and concrete implementations."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from uuid import UUID, uuid4
from sqlalchemy.orm import Session
from decimal import Decimal

from .models import User, Group, Store, Run, Product, ProductBid
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
    def get_bids_by_run(self, run_id: UUID) -> List[ProductBid]:
        """Get all bids for a run."""
        pass

    @abstractmethod
    def verify_password(self, password: str, stored_hash: str) -> bool:
        """Verify a password."""
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

    def get_bids_by_run(self, run_id: UUID) -> List[ProductBid]:
        return self.db.query(ProductBid).filter(ProductBid.run_id == run_id).all()

    def verify_password(self, password: str, stored_hash: str) -> bool:
        from .auth import verify_password
        return verify_password(password, stored_hash)


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
            self._bids: Dict[UUID, ProductBid] = {}

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

        # Create test runs
        costco_run = self._create_run(friends_group.id, costco.id, "active")
        sams_run = self._create_run(work_group.id, sams.id, "planning")

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

    def create_group(self, name: str, created_by: UUID) -> Group:
        group = Group(id=uuid4(), name=name, created_by=created_by)
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

    def get_bids_by_run(self, run_id: UUID) -> List[ProductBid]:
        return [bid for bid in self._bids.values() if bid.run_id == run_id]

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

    def _create_run(self, group_id: UUID, store_id: UUID, state: str) -> Run:
        run = Run(id=uuid4(), group_id=group_id, store_id=store_id, state=state)
        self._runs[run.id] = run
        return run


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