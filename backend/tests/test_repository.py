"""Tests for domain-specific repository implementations.

Tests both DatabaseRepository and MemoryRepository implementations for each domain.
"""

from uuid import uuid4

import pytest

from app.repositories import (
    get_bid_repository,
    get_group_repository,
    get_product_repository,
    get_run_repository,
    get_shopping_repository,
    get_store_repository,
    get_user_repository,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def user_repo(db_session):
    """Get UserRepository instance."""
    return get_user_repository(db_session)


@pytest.fixture
def group_repo(db_session):
    """Get GroupRepository instance."""
    return get_group_repository(db_session)


@pytest.fixture
def store_repo(db_session):
    """Get StoreRepository instance."""
    return get_store_repository(db_session)


@pytest.fixture
def product_repo(db_session):
    """Get ProductRepository instance."""
    return get_product_repository(db_session)


@pytest.fixture
def run_repo(db_session):
    """Get RunRepository instance."""
    return get_run_repository(db_session)


@pytest.fixture
def bid_repo(db_session):
    """Get BidRepository instance."""
    return get_bid_repository(db_session)


@pytest.fixture
def shopping_repo(db_session):
    """Get ShoppingRepository instance."""
    return get_shopping_repository(db_session)


# =============================================================================
# UserRepository Tests
# =============================================================================


class TestUserRepository:
    """Tests for UserRepository operations."""

    def test_create_user(self, user_repo):
        """Test creating a user."""
        user = user_repo.create_user(name='Test User', username='testuser', password_hash='hash123')

        assert user.id is not None
        assert user.name == 'Test User'
        assert user.username == 'testuser'
        assert user.password_hash == 'hash123'
        assert user.is_admin is False
        assert user.verified is False

    def test_get_user_by_id(self, user_repo):
        """Test getting user by ID."""
        user = user_repo.create_user(name='Test User', username='testuser', password_hash='hash')
        fetched = user_repo.get_user_by_id(user.id)

        assert fetched is not None
        assert fetched.id == user.id
        assert fetched.name == 'Test User'
        assert fetched.username == 'testuser'

    def test_get_user_by_id_not_found(self, user_repo):
        """Test getting user by ID when user doesn't exist."""
        fake_id = uuid4()
        fetched = user_repo.get_user_by_id(fake_id)
        assert fetched is None

    def test_get_user_by_username(self, user_repo):
        """Test getting user by username."""
        user = user_repo.create_user(name='Test User', username='testuser', password_hash='hash')
        fetched = user_repo.get_user_by_username('testuser')

        assert fetched is not None
        assert fetched.id == user.id
        assert fetched.username == 'testuser'

    def test_get_user_by_username_not_found(self, user_repo):
        """Test getting user by username when user doesn't exist."""
        fetched = user_repo.get_user_by_username('nonexistent')
        assert fetched is None

    def test_get_all_users(self, user_repo):
        """Test getting all users."""
        user1 = user_repo.create_user(name='User 1', username='user1', password_hash='hash')
        user2 = user_repo.create_user(name='User 2', username='user2', password_hash='hash')

        all_users = user_repo.get_all_users()
        assert len(all_users) >= 2
        user_ids = {u.id for u in all_users}
        assert user1.id in user_ids
        assert user2.id in user_ids

    def test_update_user(self, user_repo):
        """Test updating user fields."""
        user = user_repo.create_user(
            name='Original Name', username='originaluser', password_hash='hash'
        )

        updated = user_repo.update_user(user.id, name='Updated Name', is_admin=True)

        assert updated is not None
        assert updated.id == user.id
        assert updated.name == 'Updated Name'
        assert updated.username == 'originaluser'  # Unchanged
        assert updated.is_admin is True

    def test_update_user_not_found(self, user_repo):
        """Test updating non-existent user."""
        fake_id = uuid4()
        updated = user_repo.update_user(fake_id, name='New Name')
        assert updated is None

    def test_delete_user(self, user_repo):
        """Test deleting a user."""
        user = user_repo.create_user(name='To Delete', username='deleteme', password_hash='hash')

        result = user_repo.delete_user(user.id)
        assert result is True

        # Verify deletion
        fetched = user_repo.get_user_by_id(user.id)
        assert fetched is None

    def test_delete_user_not_found(self, user_repo):
        """Test deleting non-existent user."""
        fake_id = uuid4()
        result = user_repo.delete_user(fake_id)
        assert result is False

    def test_get_user_groups(self, user_repo, group_repo):
        """Test getting all groups that a user is a member of."""
        user = user_repo.create_user(name='User', username='user', password_hash='hash')
        group1 = group_repo.create_group(name='Group 1', created_by=user.id)
        group2 = group_repo.create_group(name='Group 2', created_by=user.id)

        # Add user to both groups
        group_repo.add_group_member(group1.id, user, is_group_admin=False)
        group_repo.add_group_member(group2.id, user, is_group_admin=False)

        user_groups = user_repo.get_user_groups(user)
        assert len(user_groups) == 2
        group_ids = {g.id for g in user_groups}
        assert group1.id in group_ids
        assert group2.id in group_ids


# =============================================================================
# GroupRepository Tests
# =============================================================================


class TestGroupRepository:
    """Tests for GroupRepository operations."""

    def test_create_group(self, group_repo, user_repo):
        """Test creating a group."""
        user = user_repo.create_user(name='Creator', username='creator', password_hash='hash')
        group = group_repo.create_group(name='Test Group', created_by=user.id)

        assert group.id is not None
        assert group.name == 'Test Group'
        assert group.created_by == user.id
        assert group.invite_token is not None
        assert len(group.invite_token) > 0

    def test_get_group_by_id(self, group_repo, user_repo):
        """Test getting group by ID."""
        user = user_repo.create_user(name='User', username='user', password_hash='hash')
        group = group_repo.create_group(name='Test Group', created_by=user.id)

        fetched = group_repo.get_group_by_id(group.id)
        assert fetched is not None
        assert fetched.id == group.id
        assert fetched.name == 'Test Group'

    def test_get_group_by_id_not_found(self, group_repo):
        """Test getting non-existent group."""
        fake_id = uuid4()
        fetched = group_repo.get_group_by_id(fake_id)
        assert fetched is None

    def test_add_group_member(self, group_repo, user_repo):
        """Test adding user to group."""
        creator = user_repo.create_user(name='Creator', username='creator', password_hash='hash')
        member = user_repo.create_user(name='Member', username='member', password_hash='hash')
        group = group_repo.create_group(name='Test Group', created_by=creator.id)

        result = group_repo.add_group_member(group.id, member, is_group_admin=False)
        assert result is True

        # Verify membership
        groups = user_repo.get_user_groups(member)
        assert len(groups) == 1
        assert groups[0].id == group.id

    def test_add_group_member_as_admin(self, group_repo, user_repo):
        """Test adding user to group with admin status."""
        creator = user_repo.create_user(name='Creator', username='creator', password_hash='hash')
        admin = user_repo.create_user(name='Admin', username='admin', password_hash='hash')
        group = group_repo.create_group(name='Test Group', created_by=creator.id)

        result = group_repo.add_group_member(group.id, admin, is_group_admin=True)
        assert result is True

        # Verify admin status
        is_admin = group_repo.is_user_group_admin(group.id, admin.id)
        assert is_admin is True

    def test_get_group_members_with_admin_status(self, group_repo, user_repo):
        """Test getting all members of a group with their admin status."""
        creator = user_repo.create_user(name='Creator', username='creator', password_hash='hash')
        member = user_repo.create_user(name='Member', username='member', password_hash='hash')
        admin = user_repo.create_user(name='Admin', username='admin', password_hash='hash')

        group = group_repo.create_group(name='Test Group', created_by=creator.id)
        group_repo.add_group_member(group.id, creator, is_group_admin=True)
        group_repo.add_group_member(group.id, member, is_group_admin=False)
        group_repo.add_group_member(group.id, admin, is_group_admin=True)

        members = group_repo.get_group_members_with_admin_status(group.id)
        assert len(members) >= 2  # At least creator and member

        # Find our test users in the members list (returns dicts with id, name, username, is_group_admin)
        member_dict = {m['id']: m for m in members}
        assert str(creator.id) in member_dict
        assert str(member.id) in member_dict
        assert str(admin.id) in member_dict

        # Check admin status
        assert member_dict[str(creator.id)]['is_group_admin'] is True
        assert member_dict[str(member.id)]['is_group_admin'] is False
        assert member_dict[str(admin.id)]['is_group_admin'] is True

    def test_remove_group_member(self, group_repo, user_repo):
        """Test removing user from group."""
        creator = user_repo.create_user(name='Creator', username='creator', password_hash='hash')
        member = user_repo.create_user(name='Member', username='member', password_hash='hash')
        group = group_repo.create_group(name='Test Group', created_by=creator.id)
        group_repo.add_group_member(group.id, member, is_group_admin=False)

        result = group_repo.remove_group_member(group.id, member.id)
        assert result is True

        # Verify removal
        groups = user_repo.get_user_groups(member)
        assert len(groups) == 0

    def test_get_group_by_invite_token(self, group_repo, user_repo):
        """Test getting group by invite token."""
        user = user_repo.create_user(name='User', username='user', password_hash='hash')
        group = group_repo.create_group(name='Test Group', created_by=user.id)

        fetched = group_repo.get_group_by_invite_token(group.invite_token)
        assert fetched is not None
        assert fetched.id == group.id
        assert fetched.name == 'Test Group'

    def test_is_user_group_admin(self, group_repo, user_repo):
        """Test checking if user is group admin."""
        creator = user_repo.create_user(name='Creator', username='creator', password_hash='hash')
        member = user_repo.create_user(name='Member', username='member', password_hash='hash')
        group = group_repo.create_group(name='Test Group', created_by=creator.id)

        group_repo.add_group_member(group.id, creator, is_group_admin=True)
        group_repo.add_group_member(group.id, member, is_group_admin=False)

        assert group_repo.is_user_group_admin(group.id, creator.id) is True
        assert group_repo.is_user_group_admin(group.id, member.id) is False


# =============================================================================
# StoreRepository Tests
# =============================================================================


class TestStoreRepository:
    """Tests for StoreRepository operations."""

    def test_create_store(self, store_repo):
        """Test creating a store."""
        store = store_repo.create_store(name='Test Store')

        assert store.id is not None
        assert store.name == 'Test Store'

    def test_get_store_by_id(self, store_repo):
        """Test getting store by ID."""
        store = store_repo.create_store(name='Test Store')

        fetched = store_repo.get_store_by_id(store.id)
        assert fetched is not None
        assert fetched.id == store.id
        assert fetched.name == 'Test Store'

    def test_get_store_by_id_not_found(self, store_repo):
        """Test getting non-existent store."""
        fake_id = uuid4()
        fetched = store_repo.get_store_by_id(fake_id)
        assert fetched is None

    def test_get_all_stores(self, store_repo):
        """Test getting all stores."""
        store1 = store_repo.create_store(name='Store 1')
        store2 = store_repo.create_store(name='Store 2')

        stores = store_repo.get_all_stores()
        assert len(stores) >= 2
        store_ids = {s.id for s in stores}
        assert store1.id in store_ids
        assert store2.id in store_ids

    def test_get_all_stores_with_pagination(self, store_repo):
        """Test getting all stores with limit and offset."""
        store_repo.create_store(name='Store 1')
        store_repo.create_store(name='Store 2')
        store_repo.create_store(name='Store 3')

        # Get first 2
        stores = store_repo.get_all_stores(limit=2, offset=0)
        assert len(stores) == 2

        # Get next page
        stores_page2 = store_repo.get_all_stores(limit=2, offset=2)
        assert len(stores_page2) >= 1

    def test_search_stores(self, store_repo):
        """Test searching stores by name."""
        store_repo.create_store(name='Costco')
        store_repo.create_store(name='Walmart')
        store_repo.create_store(name='Target')

        results = store_repo.search_stores('cost')
        assert len(results) >= 1
        names = {s.name for s in results}
        assert any('Costco' in name for name in names)

    def test_update_store(self, store_repo):
        """Test updating store fields."""
        store = store_repo.create_store(name='Original Store')

        updated = store_repo.update_store(store.id, name='Updated Store', verified=True)
        assert updated is not None
        assert updated.name == 'Updated Store'
        assert updated.verified is True

    def test_delete_store(self, store_repo):
        """Test deleting a store."""
        store = store_repo.create_store(name='To Delete')

        result = store_repo.delete_store(store.id)
        assert result is True

        fetched = store_repo.get_store_by_id(store.id)
        assert fetched is None


# =============================================================================
# ProductRepository Tests
# =============================================================================


class TestProductRepository:
    """Tests for ProductRepository operations."""

    def test_create_product(self, product_repo):
        """Test creating a product."""
        product = product_repo.create_product(name='Test Product', brand='Test Brand', unit='kg')

        assert product.id is not None
        assert product.name == 'Test Product'
        assert product.brand == 'Test Brand'
        assert product.unit == 'kg'

    def test_create_product_minimal(self, product_repo):
        """Test creating a product with minimal fields."""
        product = product_repo.create_product(name='Simple Product')

        assert product.id is not None
        assert product.name == 'Simple Product'
        assert product.brand is None
        assert product.unit is None

    def test_get_product_by_id(self, product_repo):
        """Test getting product by ID."""
        product = product_repo.create_product(name='Test Product')

        fetched = product_repo.get_product_by_id(product.id)
        assert fetched is not None
        assert fetched.id == product.id
        assert fetched.name == 'Test Product'

    def test_get_product_by_id_not_found(self, product_repo):
        """Test getting non-existent product."""
        fake_id = uuid4()
        fetched = product_repo.get_product_by_id(fake_id)
        assert fetched is None

    def test_get_all_products(self, product_repo):
        """Test getting all products."""
        product1 = product_repo.create_product(name='Product 1')
        product2 = product_repo.create_product(name='Product 2')

        products = product_repo.get_all_products()
        assert len(products) >= 2
        product_ids = {p.id for p in products}
        assert product1.id in product_ids
        assert product2.id in product_ids

    def test_search_products(self, product_repo):
        """Test searching products by name."""
        product_repo.create_product(name='Olive Oil', brand='Brand A')
        product_repo.create_product(name='Coconut Oil', brand='Brand B')
        product_repo.create_product(name='Rice', brand='Brand C')

        results = product_repo.search_products('oil')
        assert len(results) >= 2
        names = {p.name for p in results}
        assert any('Oil' in name for name in names)

    def test_create_product_availability(self, product_repo, store_repo):
        """Test creating product availability at a store."""
        product = product_repo.create_product(name='Test Product')
        store = store_repo.create_store(name='Test Store')

        availability = product_repo.create_product_availability(
            product_id=product.id, store_id=store.id, price=19.99, notes='On aisle 5'
        )

        assert availability is not None
        assert availability.product_id == product.id
        assert availability.store_id == store.id
        assert float(availability.price) == 19.99
        assert availability.notes == 'On aisle 5'

    def test_get_products_by_store(self, product_repo, store_repo):
        """Test getting all products available at a store."""
        store = store_repo.create_store(name='Test Store')
        product1 = product_repo.create_product(name='Product 1')
        product2 = product_repo.create_product(name='Product 2')

        # Add availability for both products at the store
        product_repo.create_product_availability(product1.id, store.id, price=10.00)
        product_repo.create_product_availability(product2.id, store.id, price=20.00)

        products = product_repo.get_products_by_store(store.id)
        assert len(products) >= 2
        product_ids = {p.id for p in products}
        assert product1.id in product_ids
        assert product2.id in product_ids

    def test_get_availability_by_product_and_store(self, product_repo, store_repo):
        """Test getting specific product availability."""
        product = product_repo.create_product(name='Test Product')
        store = store_repo.create_store(name='Test Store')

        product_repo.create_product_availability(product.id, store.id, price=15.50)

        fetched = product_repo.get_availability_by_product_and_store(product.id, store.id)
        assert fetched is not None
        assert fetched.product_id == product.id
        assert fetched.store_id == store.id
        assert float(fetched.price) == 15.50

    def test_update_product(self, product_repo):
        """Test updating product fields."""
        product = product_repo.create_product(name='Original Product')

        updated = product_repo.update_product(
            product.id, name='Updated Product', brand='New Brand', verified=True
        )

        assert updated is not None
        assert updated.name == 'Updated Product'
        assert updated.brand == 'New Brand'
        assert updated.verified is True

    def test_delete_product(self, product_repo):
        """Test deleting a product."""
        product = product_repo.create_product(name='To Delete')

        result = product_repo.delete_product(product.id)
        assert result is True

        fetched = product_repo.get_product_by_id(product.id)
        assert fetched is None


# =============================================================================
# RunRepository Tests
# =============================================================================


class TestRunRepository:
    """Tests for RunRepository operations."""

    def test_create_run(self, run_repo, group_repo, store_repo, user_repo):
        """Test creating a run."""
        user = user_repo.create_user(name='User', username='user', password_hash='hash')
        group = group_repo.create_group(name='Test Group', created_by=user.id)
        store = store_repo.create_store(name='Test Store')

        run = run_repo.create_run(group_id=group.id, store_id=store.id, leader_id=user.id)

        assert run.id is not None
        assert run.group_id == group.id
        assert run.store_id == store.id
        assert run.state == 'planning'

    def test_get_run_by_id(self, run_repo, group_repo, store_repo, user_repo):
        """Test getting run by ID."""
        user = user_repo.create_user(name='User', username='user', password_hash='hash')
        group = group_repo.create_group(name='Test Group', created_by=user.id)
        store = store_repo.create_store(name='Test Store')
        run = run_repo.create_run(group.id, store.id, user.id)

        fetched = run_repo.get_run_by_id(run.id)
        assert fetched is not None
        assert fetched.id == run.id
        assert fetched.state == 'planning'

    def test_get_run_by_id_not_found(self, run_repo):
        """Test getting non-existent run."""
        fake_id = uuid4()
        fetched = run_repo.get_run_by_id(fake_id)
        assert fetched is None

    def test_update_run_state(self, run_repo, group_repo, store_repo, user_repo):
        """Test updating run state."""
        user = user_repo.create_user(name='User', username='user', password_hash='hash')
        group = group_repo.create_group(name='Test Group', created_by=user.id)
        store = store_repo.create_store(name='Test Store')
        run = run_repo.create_run(group.id, store.id, user.id)

        updated = run_repo.update_run_state(run.id, 'active')
        assert updated is not None
        assert updated.state == 'active'
        assert updated.active_at is not None

    def test_get_runs_by_group(self, run_repo, group_repo, store_repo, user_repo):
        """Test getting all runs for a group."""
        user = user_repo.create_user(name='User', username='user', password_hash='hash')
        group = group_repo.create_group(name='Test Group', created_by=user.id)
        store = store_repo.create_store(name='Test Store')

        run1 = run_repo.create_run(group.id, store.id, user.id)
        run2 = run_repo.create_run(group.id, store.id, user.id)

        runs = run_repo.get_runs_by_group(group.id)
        assert len(runs) >= 2
        run_ids = {r.id for r in runs}
        assert run1.id in run_ids
        assert run2.id in run_ids

    def test_create_participation(self, run_repo, group_repo, store_repo, user_repo):
        """Test creating run participation."""
        user = user_repo.create_user(name='User', username='user', password_hash='hash')
        group = group_repo.create_group(name='Test Group', created_by=user.id)
        store = store_repo.create_store(name='Test Store')
        run = run_repo.create_run(group.id, store.id, user.id)

        # Create another user to participate
        participant = user_repo.create_user(
            name='Participant', username='participant', password_hash='hash'
        )

        participation = run_repo.create_participation(
            user_id=participant.id, run_id=run.id, is_leader=False
        )

        assert participation.id is not None
        assert participation.user_id == participant.id
        assert participation.run_id == run.id
        assert participation.is_leader is False

    def test_get_participation(self, run_repo, group_repo, store_repo, user_repo):
        """Test getting a user's participation in a run."""
        user = user_repo.create_user(name='User', username='user', password_hash='hash')
        group = group_repo.create_group(name='Test Group', created_by=user.id)
        store = store_repo.create_store(name='Test Store')
        run = run_repo.create_run(group.id, store.id, user.id)

        # The leader participation should be created automatically
        participation = run_repo.get_participation(user.id, run.id)
        assert participation is not None
        assert participation.user_id == user.id
        assert participation.run_id == run.id
        assert participation.is_leader is True

    def test_get_run_participations(self, run_repo, group_repo, store_repo, user_repo):
        """Test getting all participations for a run."""
        user1 = user_repo.create_user(name='User 1', username='user1', password_hash='hash')
        user2 = user_repo.create_user(name='User 2', username='user2', password_hash='hash')
        group = group_repo.create_group(name='Test Group', created_by=user1.id)
        store = store_repo.create_store(name='Test Store')
        run = run_repo.create_run(group.id, store.id, user1.id)

        # Add second participant
        run_repo.create_participation(user2.id, run.id, is_leader=False)

        participations = run_repo.get_run_participations(run.id)
        assert len(participations) >= 2
        user_ids = {p.user_id for p in participations}
        assert user1.id in user_ids
        assert user2.id in user_ids

    def test_update_participation_ready(self, run_repo, group_repo, store_repo, user_repo):
        """Test updating participation ready status."""
        user = user_repo.create_user(name='User', username='user', password_hash='hash')
        group = group_repo.create_group(name='Test Group', created_by=user.id)
        store = store_repo.create_store(name='Test Store')
        run = run_repo.create_run(group.id, store.id, user.id)

        participation = run_repo.get_participation(user.id, run.id)
        assert participation.is_ready is False

        updated = run_repo.update_participation_ready(participation.id, True)
        assert updated is not None
        assert updated.is_ready is True


# =============================================================================
# BidRepository Tests
# =============================================================================


class TestBidRepository:
    """Tests for BidRepository operations."""

    def test_create_or_update_bid(
        self, bid_repo, run_repo, product_repo, group_repo, store_repo, user_repo
    ):
        """Test creating a product bid."""
        user = user_repo.create_user(name='User', username='user', password_hash='hash')
        group = group_repo.create_group(name='Test Group', created_by=user.id)
        store = store_repo.create_store(name='Test Store')
        product = product_repo.create_product(name='Test Product')
        run = run_repo.create_run(group.id, store.id, user.id)
        participation = run_repo.get_participation(user.id, run.id)

        bid = bid_repo.create_or_update_bid(
            participation_id=participation.id,
            product_id=product.id,
            quantity=5,
            interested_only=False,
        )

        assert bid.id is not None
        assert bid.participation_id == participation.id
        assert bid.product_id == product.id
        assert bid.quantity == 5
        assert bid.interested_only is False

    def test_update_existing_bid(
        self, bid_repo, run_repo, product_repo, group_repo, store_repo, user_repo
    ):
        """Test updating an existing bid."""
        user = user_repo.create_user(name='User', username='user', password_hash='hash')
        group = group_repo.create_group(name='Test Group', created_by=user.id)
        store = store_repo.create_store(name='Test Store')
        product = product_repo.create_product(name='Test Product')
        run = run_repo.create_run(group.id, store.id, user.id)
        participation = run_repo.get_participation(user.id, run.id)

        # Create initial bid
        bid = bid_repo.create_or_update_bid(
            participation.id, product.id, quantity=5, interested_only=False
        )
        initial_bid_id = bid.id

        # Update the bid
        updated_bid = bid_repo.create_or_update_bid(
            participation.id, product.id, quantity=10, interested_only=False
        )

        assert updated_bid.id == initial_bid_id  # Same bid object
        assert updated_bid.quantity == 10

    def test_get_bids_by_run(
        self, bid_repo, run_repo, product_repo, group_repo, store_repo, user_repo
    ):
        """Test getting all bids for a run."""
        user = user_repo.create_user(name='User', username='user', password_hash='hash')
        group = group_repo.create_group(name='Test Group', created_by=user.id)
        store = store_repo.create_store(name='Test Store')
        product1 = product_repo.create_product(name='Product 1')
        product2 = product_repo.create_product(name='Product 2')
        run = run_repo.create_run(group.id, store.id, user.id)
        participation = run_repo.get_participation(user.id, run.id)

        bid1 = bid_repo.create_or_update_bid(participation.id, product1.id, 5, False)
        bid2 = bid_repo.create_or_update_bid(participation.id, product2.id, 3, False)

        bids = bid_repo.get_bids_by_run(run.id)
        assert len(bids) >= 2
        bid_ids = {b.id for b in bids}
        assert bid1.id in bid_ids
        assert bid2.id in bid_ids

    def test_get_bid(self, bid_repo, run_repo, product_repo, group_repo, store_repo, user_repo):
        """Test getting a specific bid."""
        user = user_repo.create_user(name='User', username='user', password_hash='hash')
        group = group_repo.create_group(name='Test Group', created_by=user.id)
        store = store_repo.create_store(name='Test Store')
        product = product_repo.create_product(name='Test Product')
        run = run_repo.create_run(group.id, store.id, user.id)
        participation = run_repo.get_participation(user.id, run.id)

        bid = bid_repo.create_or_update_bid(participation.id, product.id, 5, False)

        fetched = bid_repo.get_bid(participation.id, product.id)
        assert fetched is not None
        assert fetched.id == bid.id
        assert fetched.quantity == 5

    def test_get_bid_not_found(self, bid_repo):
        """Test getting non-existent bid."""
        fake_participation_id = uuid4()
        fake_product_id = uuid4()

        fetched = bid_repo.get_bid(fake_participation_id, fake_product_id)
        assert fetched is None

    def test_delete_bid(self, bid_repo, run_repo, product_repo, group_repo, store_repo, user_repo):
        """Test deleting a bid."""
        user = user_repo.create_user(name='User', username='user', password_hash='hash')
        group = group_repo.create_group(name='Test Group', created_by=user.id)
        store = store_repo.create_store(name='Test Store')
        product = product_repo.create_product(name='Test Product')
        run = run_repo.create_run(group.id, store.id, user.id)
        participation = run_repo.get_participation(user.id, run.id)

        bid_repo.create_or_update_bid(participation.id, product.id, 5, False)

        result = bid_repo.delete_bid(participation.id, product.id)
        assert result is True

        # Verify deletion
        fetched = bid_repo.get_bid(participation.id, product.id)
        assert fetched is None

    def test_get_bids_by_participation(
        self, bid_repo, run_repo, product_repo, group_repo, store_repo, user_repo
    ):
        """Test getting all bids for a participation."""
        user = user_repo.create_user(name='User', username='user', password_hash='hash')
        group = group_repo.create_group(name='Test Group', created_by=user.id)
        store = store_repo.create_store(name='Test Store')
        product1 = product_repo.create_product(name='Product 1')
        product2 = product_repo.create_product(name='Product 2')
        run = run_repo.create_run(group.id, store.id, user.id)
        participation = run_repo.get_participation(user.id, run.id)

        bid1 = bid_repo.create_or_update_bid(participation.id, product1.id, 5, False)
        bid2 = bid_repo.create_or_update_bid(participation.id, product2.id, 3, False)

        bids = bid_repo.get_bids_by_participation(participation.id)
        assert len(bids) >= 2
        bid_ids = {b.id for b in bids}
        assert bid1.id in bid_ids
        assert bid2.id in bid_ids


# =============================================================================
# ShoppingRepository Tests
# =============================================================================


class TestShoppingRepository:
    """Tests for ShoppingRepository operations."""

    def test_create_shopping_list_item(
        self, shopping_repo, run_repo, product_repo, group_repo, store_repo, user_repo
    ):
        """Test creating a shopping list item."""
        user = user_repo.create_user(name='User', username='user', password_hash='hash')
        group = group_repo.create_group(name='Test Group', created_by=user.id)
        store = store_repo.create_store(name='Test Store')
        product = product_repo.create_product(name='Test Product')
        run = run_repo.create_run(group.id, store.id, user.id)

        item = shopping_repo.create_shopping_list_item(
            run_id=run.id, product_id=product.id, requested_quantity=10
        )

        assert item.id is not None
        assert item.run_id == run.id
        assert item.product_id == product.id
        assert item.requested_quantity == 10
        assert item.is_purchased is False

    def test_get_shopping_list_items(
        self, shopping_repo, run_repo, product_repo, group_repo, store_repo, user_repo
    ):
        """Test getting all shopping list items for a run."""
        user = user_repo.create_user(name='User', username='user', password_hash='hash')
        group = group_repo.create_group(name='Test Group', created_by=user.id)
        store = store_repo.create_store(name='Test Store')
        product1 = product_repo.create_product(name='Product 1')
        product2 = product_repo.create_product(name='Product 2')
        run = run_repo.create_run(group.id, store.id, user.id)

        item1 = shopping_repo.create_shopping_list_item(run.id, product1.id, 5)
        item2 = shopping_repo.create_shopping_list_item(run.id, product2.id, 8)

        items = shopping_repo.get_shopping_list_items(run.id)
        assert len(items) >= 2
        item_ids = {i.id for i in items}
        assert item1.id in item_ids
        assert item2.id in item_ids

    def test_get_shopping_list_item(
        self, shopping_repo, run_repo, product_repo, group_repo, store_repo, user_repo
    ):
        """Test getting a specific shopping list item."""
        user = user_repo.create_user(name='User', username='user', password_hash='hash')
        group = group_repo.create_group(name='Test Group', created_by=user.id)
        store = store_repo.create_store(name='Test Store')
        product = product_repo.create_product(name='Test Product')
        run = run_repo.create_run(group.id, store.id, user.id)

        item = shopping_repo.create_shopping_list_item(run.id, product.id, 10)

        fetched = shopping_repo.get_shopping_list_item(item.id)
        assert fetched is not None
        assert fetched.id == item.id
        assert fetched.requested_quantity == 10

    def test_mark_item_purchased(
        self, shopping_repo, run_repo, product_repo, group_repo, store_repo, user_repo
    ):
        """Test marking a shopping list item as purchased."""
        user = user_repo.create_user(name='User', username='user', password_hash='hash')
        group = group_repo.create_group(name='Test Group', created_by=user.id)
        store = store_repo.create_store(name='Test Store')
        product = product_repo.create_product(name='Test Product')
        run = run_repo.create_run(group.id, store.id, user.id)

        item = shopping_repo.create_shopping_list_item(run.id, product.id, 10)

        result = shopping_repo.mark_item_purchased(
            item_id=item.id, quantity=8, price_per_unit=9.50, total=76.00, purchase_order=1
        )

        assert result is not None
        assert result.is_purchased is True
        assert result.purchased_quantity == 8
        assert float(result.purchased_price_per_unit) == 9.50
        assert float(result.purchased_total) == 76.00
        assert result.purchase_order == 1

    def test_unpurchase_item(
        self, shopping_repo, run_repo, product_repo, group_repo, store_repo, user_repo
    ):
        """Test resetting an item to unpurchased state."""
        user = user_repo.create_user(name='User', username='user', password_hash='hash')
        group = group_repo.create_group(name='Test Group', created_by=user.id)
        store = store_repo.create_store(name='Test Store')
        product = product_repo.create_product(name='Test Product')
        run = run_repo.create_run(group.id, store.id, user.id)

        item = shopping_repo.create_shopping_list_item(run.id, product.id, 10)
        shopping_repo.mark_item_purchased(item.id, 8, 9.50, 76.00, 1)

        # Now unpurchase it
        result = shopping_repo.unpurchase_item(item.id)
        assert result is not None
        assert result.is_purchased is False
        assert result.purchased_quantity is None
        assert result.purchased_price_per_unit is None
        assert result.purchased_total is None
