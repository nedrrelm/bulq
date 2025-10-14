"""
Advanced tests for SQLAlchemy models including validation, relationships, and constraints.
"""
import pytest
from decimal import Decimal
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.core.models import (
    User, Group, Store, Product, Run,
    RunParticipation, ProductBid, ShoppingListItem, ProductAvailability, group_membership
)


class TestUserModel:
    """Tests for User model"""

    def test_user_creation_with_all_fields(self, db_session):
        """Test creating user with all fields"""
        user = User(
            name="John Doe",
            email="john@example.com",
            password_hash="hashed_password_123"
        )
        db_session.add(user)
        db_session.commit()

        assert user.id is not None
        assert user.name == "John Doe"
        assert user.email == "john@example.com"
        assert user.password_hash == "hashed_password_123"

    def test_user_email_unique_constraint(self, db_session):
        """Test that email must be unique"""
        user1 = User(name="User 1", email="same@example.com", password_hash="hash1")
        db_session.add(user1)
        db_session.commit()

        user2 = User(name="User 2", email="same@example.com", password_hash="hash2")
        db_session.add(user2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_user_relationships_groups(self, db_session):
        """Test user-group many-to-many relationship"""
        user = User(name="User", email="user@example.com", password_hash="hash")
        group = Group(name="Group", created_by=user.id, invite_token="token123")
        db_session.add_all([user, group])
        db_session.commit()

        # Add membership using relationship
        user.groups.append(group)
        db_session.commit()

        # Query through relationship
        user_groups = db_session.query(Group).join(group_membership).filter(
            group_membership.c.user_id == user.id
        ).all()

        assert len(user_groups) == 1
        assert user_groups[0].name == "Group"


class TestGroupModel:
    """Tests for Group model"""

    def test_group_creation(self, db_session):
        """Test creating a group"""
        user = User(name="Creator", email="creator@example.com", password_hash="hash")
        db_session.add(user)
        db_session.commit()

        group = Group(
            name="Test Group",
            created_by=user.id,
            invite_token="unique_token_123"
        )
        db_session.add(group)
        db_session.commit()

        assert group.id is not None
        assert group.name == "Test Group"
        assert group.created_by == user.id
        assert group.invite_token == "unique_token_123"

    def test_group_invite_token_unique(self, db_session):
        """Test that invite tokens must be unique"""
        user = User(name="User", email="user@example.com", password_hash="hash")
        db_session.add(user)
        db_session.commit()

        group1 = Group(name="Group 1", created_by=user.id, invite_token="same_token")
        db_session.add(group1)
        db_session.commit()

        group2 = Group(name="Group 2", created_by=user.id, invite_token="same_token")
        db_session.add(group2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_group_members_relationship(self, db_session):
        """Test accessing group members"""
        user1 = User(name="User 1", email="user1@example.com", password_hash="hash")
        user2 = User(name="User 2", email="user2@example.com", password_hash="hash")
        db_session.add_all([user1, user2])
        db_session.commit()

        group = Group(name="Group", created_by=user1.id, invite_token="token")
        db_session.add(group)
        db_session.commit()

        # Add members using relationship
        group.members.extend([user1, user2])
        db_session.commit()

        # Query members
        members = db_session.query(User).join(group_membership).filter(
            group_membership.c.group_id == group.id
        ).all()

        assert len(members) == 2


class TestStoreModel:
    """Tests for Store model"""

    def test_store_creation(self, db_session):
        """Test creating a store"""
        store = Store(name="Costco")
        db_session.add(store)
        db_session.commit()

        assert store.id is not None
        assert store.name == "Costco"

    def test_store_products_relationship(self, db_session):
        """Test store-products relationship"""
        store = Store(name="Store")
        db_session.add(store)
        db_session.commit()

        product1 = Product(store_id=store.id, name="Product 1", base_price=Decimal("10.99"))
        product2 = Product(store_id=store.id, name="Product 2", base_price=Decimal("20.99"))
        db_session.add_all([product1, product2])
        db_session.commit()

        # Query products for store
        products = db_session.query(Product).filter(Product.store_id == store.id).all()

        assert len(products) == 2


class TestProductModel:
    """Tests for Product model"""

    def test_product_creation(self, db_session):
        """Test creating a product"""
        store = Store(name="Store")
        db_session.add(store)
        db_session.commit()

        product = Product(
            store_id=store.id,
            name="Olive Oil",
            base_price=Decimal("24.99")
        )
        db_session.add(product)
        db_session.commit()

        assert product.id is not None
        assert product.name == "Olive Oil"
        assert product.base_price == Decimal("24.99")
        assert product.created_at is not None
        assert product.updated_at is not None

    def test_product_timestamps(self, db_session):
        """Test that product timestamps are set automatically"""
        store = Store(name="Store")
        db_session.add(store)
        db_session.commit()

        product = Product(store_id=store.id, name="Product", base_price=Decimal("10.00"))
        db_session.add(product)
        db_session.commit()

        assert isinstance(product.created_at, datetime)
        assert isinstance(product.updated_at, datetime)
        assert product.created_at <= product.updated_at

    def test_product_price_precision(self, db_session):
        """Test that product prices maintain precision"""
        store = Store(name="Store")
        db_session.add(store)
        db_session.commit()

        product = Product(store_id=store.id, name="Product", base_price=Decimal("19.995"))
        db_session.add(product)
        db_session.commit()

        # Retrieve and check precision
        retrieved = db_session.query(Product).filter(Product.id == product.id).first()
        assert retrieved.base_price == Decimal("19.995")


class TestRunModel:
    """Tests for Run model"""

    def test_run_creation(self, db_session):
        """Test creating a run"""
        user = User(name="User", email="user@example.com", password_hash="hash")
        group = Group(name="Group", created_by=user.id, invite_token="token")
        store = Store(name="Store")
        db_session.add_all([user, group, store])
        db_session.commit()

        run = Run(
            group_id=group.id,
            store_id=store.id,
            state="planning"
        )
        db_session.add(run)
        db_session.commit()

        assert run.id is not None
        assert run.state == "planning"
        assert run.planning_at is not None

    def test_run_state_transitions(self, db_session):
        """Test run state field updates"""
        user = User(name="User", email="user@example.com", password_hash="hash")
        group = Group(name="Group", created_by=user.id, invite_token="token")
        store = Store(name="Store")
        db_session.add_all([user, group, store])
        db_session.commit()

        run = Run(group_id=group.id, store_id=store.id, state="planning")
        db_session.add(run)
        db_session.commit()

        # Update state
        run.state = "active"
        run.active_at = datetime.utcnow()
        db_session.commit()

        assert run.state == "active"
        assert run.active_at is not None

    def test_run_timestamps(self, db_session):
        """Test run timestamp fields"""
        user = User(name="User", email="user@example.com", password_hash="hash")
        group = Group(name="Group", created_by=user.id, invite_token="token")
        store = Store(name="Store")
        db_session.add_all([user, group, store])
        db_session.commit()

        run = Run(group_id=group.id, store_id=store.id, state="planning")
        db_session.add(run)
        db_session.commit()

        # Set various timestamps
        now = datetime.utcnow()
        run.active_at = now
        run.confirmed_at = now
        run.shopping_at = now
        db_session.commit()

        retrieved = db_session.query(Run).filter(Run.id == run.id).first()
        assert retrieved.active_at is not None
        assert retrieved.confirmed_at is not None
        assert retrieved.shopping_at is not None


class TestRunParticipationModel:
    """Tests for RunParticipation model"""

    def test_participation_creation(self, db_session):
        """Test creating participation"""
        user = User(name="User", email="user@example.com", password_hash="hash")
        group = Group(name="Group", created_by=user.id, invite_token="token")
        store = Store(name="Store")
        run = Run(group_id=group.id, store_id=store.id, state="planning")
        db_session.add_all([user, group, store, run])
        db_session.commit()

        participation = RunParticipation(
            user_id=user.id,
            run_id=run.id,
            is_leader=True,
            is_ready=False
        )
        db_session.add(participation)
        db_session.commit()

        assert participation.id is not None
        assert participation.is_leader is True
        assert participation.is_ready is False

    def test_participation_unique_constraint(self, db_session):
        """Test that user can only have one participation per run"""
        user = User(name="User", email="user@example.com", password_hash="hash")
        group = Group(name="Group", created_by=user.id, invite_token="token")
        store = Store(name="Store")
        run = Run(group_id=group.id, store_id=store.id, state="planning")
        db_session.add_all([user, group, store, run])
        db_session.commit()

        p1 = RunParticipation(user_id=user.id, run_id=run.id, is_leader=True)
        db_session.add(p1)
        db_session.commit()

        p2 = RunParticipation(user_id=user.id, run_id=run.id, is_leader=False)
        db_session.add(p2)

        with pytest.raises(IntegrityError):
            db_session.commit()


class TestProductBidModel:
    """Tests for ProductBid model"""

    def test_bid_creation(self, db_session):
        """Test creating a product bid"""
        user = User(name="User", email="user@example.com", password_hash="hash")
        group = Group(name="Group", created_by=user.id, invite_token="token")
        store = Store(name="Store")
        product = Product(store_id=store.id, name="Product", base_price=Decimal("10.00"))
        run = Run(group_id=group.id, store_id=store.id, state="planning")
        db_session.add_all([user, group, store, product, run])
        db_session.commit()

        participation = RunParticipation(user_id=user.id, run_id=run.id, is_leader=True)
        db_session.add(participation)
        db_session.commit()

        bid = ProductBid(
            participation_id=participation.id,
            product_id=product.id,
            quantity=5,
            interested_only=False
        )
        db_session.add(bid)
        db_session.commit()

        assert bid.id is not None
        assert bid.quantity == 5
        assert bid.interested_only is False
        assert bid.created_at is not None

    def test_bid_distribution_fields(self, db_session):
        """Test bid distribution tracking fields"""
        user = User(name="User", email="user@example.com", password_hash="hash")
        group = Group(name="Group", created_by=user.id, invite_token="token")
        store = Store(name="Store")
        product = Product(store_id=store.id, name="Product", base_price=Decimal("10.00"))
        run = Run(group_id=group.id, store_id=store.id, state="distributing")
        participation = RunParticipation(user_id=user.id, run_id=run.id, is_leader=True)
        db_session.add_all([user, group, store, product, run, participation])
        db_session.commit()

        bid = ProductBid(
            participation_id=participation.id,
            product_id=product.id,
            quantity=5,
            interested_only=False,
            distributed_quantity=4,
            distributed_price_per_unit=Decimal("9.50"),
            is_picked_up=True
        )
        db_session.add(bid)
        db_session.commit()

        assert bid.distributed_quantity == 4
        assert bid.distributed_price_per_unit == Decimal("9.50")
        assert bid.is_picked_up is True


class TestShoppingListItemModel:
    """Tests for ShoppingListItem model"""

    def test_shopping_list_item_creation(self, db_session):
        """Test creating shopping list item"""
        user = User(name="User", email="user@example.com", password_hash="hash")
        group = Group(name="Group", created_by=user.id, invite_token="token")
        store = Store(name="Store")
        product = Product(store_id=store.id, name="Product", base_price=Decimal("10.00"))
        run = Run(group_id=group.id, store_id=store.id, state="shopping")
        db_session.add_all([user, group, store, product, run])
        db_session.commit()

        item = ShoppingListItem(
            run_id=run.id,
            product_id=product.id,
            requested_quantity=10
        )
        db_session.add(item)
        db_session.commit()

        assert item.id is not None
        assert item.requested_quantity == 10
        assert item.is_purchased is False

    def test_shopping_list_item_purchase_tracking(self, db_session):
        """Test purchase tracking fields"""
        user = User(name="User", email="user@example.com", password_hash="hash")
        group = Group(name="Group", created_by=user.id, invite_token="token")
        store = Store(name="Store")
        product = Product(store_id=store.id, name="Product", base_price=Decimal("10.00"))
        run = Run(group_id=group.id, store_id=store.id, state="shopping")
        db_session.add_all([user, group, store, product, run])
        db_session.commit()

        item = ShoppingListItem(
            run_id=run.id,
            product_id=product.id,
            requested_quantity=10,
            purchased_quantity=8,
            purchased_price_per_unit=Decimal("9.75"),
            purchased_total=Decimal("78.00"),
            is_purchased=True,
            purchase_order=1
        )
        db_session.add(item)
        db_session.commit()

        assert item.purchased_quantity == 8
        assert item.purchased_price_per_unit == Decimal("9.75")
        assert item.purchased_total == Decimal("78.00")
        assert item.is_purchased is True
        assert item.purchase_order == 1

    def test_product_availability(self, db_session):
        """Test product availability records"""
        user = User(name="User", email="user@example.com", password_hash="hash")
        group = Group(name="Group", created_by=user.id, invite_token="token")
        store = Store(name="Store")
        product = Product(name="Product", brand="Brand")
        db_session.add_all([user, group, store, product])
        db_session.commit()

        # Create product availability at store
        availability = ProductAvailability(
            product_id=product.id,
            store_id=store.id,
            price=Decimal("9.99"),
            notes="Aisle 3",
            created_by=user.id
        )
        db_session.add(availability)
        db_session.commit()

        # Retrieve and verify
        retrieved = db_session.query(ProductAvailability).filter(
            ProductAvailability.product_id == product.id,
            ProductAvailability.store_id == store.id
        ).first()

        assert retrieved is not None
        assert retrieved.price == Decimal("9.99")
        assert retrieved.notes == "Aisle 3"
        assert retrieved.created_by == user.id


# db_session fixture is already defined in conftest.py, no need to redefine it here
