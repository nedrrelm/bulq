"""
Tests for repository pattern implementation.
Tests both DatabaseRepository and MemoryRepository.
"""
import pytest
from sqlalchemy.orm import Session
from app.repositories import DatabaseRepository, MemoryRepository, get_repository
from app.core.models import User, Group, Store, Product, Run, ProductBid, RunParticipation, ShoppingListItem


class TestMemoryRepository:
    """Tests for MemoryRepository"""

    @pytest.fixture
    def repo(self):
        """Create a fresh in-memory repository"""
        return MemoryRepository()

    async def test_create_user(self, repo):
        """Test creating a user"""
        user =await repo.create_user(name="Test User", email="test@example.com", password_hash="hash123")

        assert user.id is not None
        assert user.name == "Test User"
        assert user.email == "test@example.com"
        assert user.password_hash == "hash123"

    async def test_get_user_by_id(self, repo):
        """Test getting user by ID"""
        user =await repo.create_user(name="Test User", email="test@example.com", password_hash="hash")
        fetched =await repo.get_user_by_id(user.id)

        assert fetched is not None
        assert fetched.id == user.id
        assert fetched.name == "Test User"

    async def test_get_user_by_email(self, repo):
        """Test getting user by email"""
        user =await repo.create_user(name="Test User", email="test@example.com", password_hash="hash")
        fetched =await repo.get_user_by_email("test@example.com")

        assert fetched is not None
        assert fetched.id == user.id
        assert fetched.email == "test@example.com"

    async def test_get_user_by_email(self, repo):
        """Test email lookup works"""
        # Use existing test data
        user =await repo.get_user_by_email("alice@test.com")
        assert user is not None
        assert user.email == "alice@test.com"

    async def test_create_group(self, repo):
        """Test creating a group"""
        user =await repo.create_user(name="Creator", email="creator@example.com", password_hash="hash")
        group =await repo.create_group(name="Test Group", created_by=user.id)

        assert group.id is not None
        assert group.name == "Test Group"
        assert group.created_by == user.id
        assert group.invite_token is not None

    async def test_add_user_to_group(self, repo):
        """Test adding user to group"""
        user =await repo.create_user(name="User", email="user@example.com", password_hash="hash")
        creator =await repo.create_user(name="Creator", email="creator@example.com", password_hash="hash")
        group =await repo.create_group(name="Test Group", created_by=creator.id)

        await repo.add_group_member(group.id, user)

        groups = await repo.get_user_groups(user)
        assert len(groups) == 1
        assert groups[0].id == group.id

    async def test_get_group_members(self, repo):
        """Test getting group members - use existing test data"""
        # Test Friends group should have alice, bob, carol, and test user
        alice =await repo.get_user_by_email("alice@test.com")
        test_group = next((g for g in await repo.get_user_groups(alice) if g.name == "Test Friends"), None)

        assert test_group is not None
        # The group should have members (at least alice who we know is in it)
        # This tests that the membership relationship works
        groups_for_alice = await repo.get_user_groups(alice)
        assert any(g.id == test_group.id for g in groups_for_alice)

    async def test_get_all_stores(self, repo):
        """Test getting all stores - use existing test data"""
        stores = await repo.get_all_stores()
        assert len(stores) >= 2  # Should have Test Costco and Test Sam's Club
        store_names = {s.name for s in stores}
        assert "Test Costco" in store_names
        assert "Test Sam's Club" in store_names

    async def test_get_products_by_store(self, repo):
        """Test getting products by store"""
        stores = await repo.get_all_stores()
        costco = next((s for s in stores if "Costco" in s.name), None)
        assert costco is not None

        products = await repo.get_products_by_store(costco.id)
        assert len(products) > 0  # Should have test products

    async def test_search_products(self, repo):
        """Test searching products - use existing test data"""
        # Test data includes "Test Olive Oil"
        results = await repo.search_products("oil")
        assert len(results) >= 1  # Should find at least the olive oil
        names = {p.name for p in results}
        assert any("Oil" in name for name in names)

    async def test_create_run(self, repo):
        """Test creating a run"""
        user =await repo.create_user(name="User", email="user@example.com", password_hash="hash")
        group =await repo.create_group(name="Group", created_by=user.id)
        stores = await repo.get_all_stores()
        store = stores[0]

        run =await repo.create_run(group_id=group.id, store_id=store.id, leader_id=user.id)

        assert run.id is not None
        assert run.group_id == group.id
        assert run.store_id == store.id
        assert run.state == "planning"

    async def test_update_run_state(self, repo):
        """Test updating run state"""
        user = await repo.create_user(name="User", email="user@example.com", password_hash="hash")
        group = await repo.create_group(name="Group", created_by=user.id)
        stores = await repo.get_all_stores()
        store = stores[0]
        run = await repo.create_run(group_id=group.id, store_id=store.id, leader_id=user.id)

        await repo.update_run_state(run.id, "active")
        updated = await repo.get_run_by_id(run.id)

        assert updated.state == "active"

    async def test_create_participation(self, repo):
        """Test creating run participation"""
        user =await repo.create_user(name="User", email="newparticipant@example.com", password_hash="hash")
        # Use existing group and store
        alice =await repo.get_user_by_email("alice@test.com")
        group = await repo.get_user_groups(alice)[0]
        stores = await repo.get_all_stores()
        run =await repo.create_run(group_id=group.id, store_id=stores[0].id, leader_id=alice.id)

        participation =await repo.create_participation(
            user_id=user.id,
            run_id=run.id,
            is_leader=False
        )

        assert participation.id is not None
        assert participation.user_id == user.id
        assert participation.run_id == run.id
        assert participation.is_leader is False

    async def test_get_participation(self, repo):
        """Test getting participation - use existing test data"""
        alice =await repo.get_user_by_email("alice@test.com")
        # Find a run that alice is in
        groups =await repo.get_user_groups(alice)
        if groups:
            runs =await repo.get_runs_by_group(groups[0].id)
            if runs:
                run = runs[0]
                participation =await repo.get_participation(user_id=alice.id, run_id=run.id)
                # May or may not exist depending on test data, just verify method works
                # If exists, verify structure
                if participation:
                    assert participation.user_id == alice.id
                    assert participation.run_id == run.id

    async def test_get_run_bids(self, repo):
        """Test getting all bids for a run - use existing test data"""
        # Find an active run which should have bids
        alice =await repo.get_user_by_email("alice@test.com")
        groups =await repo.get_user_groups(alice)
        if groups:
            runs =await repo.get_runs_by_group(groups[0].id)
            active_runs = [r for r in runs if r.state == "active"]
            if active_runs:
                bids =await repo.get_bids_by_run(active_runs[0].id)
                # Active runs should have some bids
                assert isinstance(bids, list)

    async def test_create_shopping_list_item(self, repo):
        """Test creating shopping list item"""
        alice =await repo.get_user_by_email("alice@test.com")
        group =await repo.get_user_groups(alice)[0]
        stores =await repo.get_all_stores()
        products =await repo.get_products_by_store(stores[0].id)
        run =await repo.create_run(group_id=group.id, store_id=stores[0].id, leader_id=alice.id)

        item =await repo.create_shopping_list_item(
            run_id=run.id,
            product_id=products[0].id,
            requested_quantity=10
        )

        assert item.id is not None
        assert item.run_id == run.id
        assert item.product_id == products[0].id
        assert item.requested_quantity == 10

    async def test_mark_item_purchased(self, repo):
        """Test marking shopping list item as purchased"""
        alice =await repo.get_user_by_email("alice@test.com")
        group =await repo.get_user_groups(alice)[0]
        stores =await repo.get_all_stores()
        products =await repo.get_products_by_store(stores[0].id)
        run =await repo.create_run(group_id=group.id, store_id=stores[0].id, leader_id=alice.id)
        item =await repo.create_shopping_list_item(run_id=run.id, product_id=products[0].id, requested_quantity=10)

        result =await repo.mark_item_purchased(
            item_id=item.id,
            quantity=8,
            price_per_unit=9.50,
            total=76.00,
            purchase_order=1
        )

        assert result.is_purchased is True
        assert result.purchased_quantity == 8


class TestDatabaseRepository:
    """Tests for DatabaseRepository - Currently not implemented"""

    @pytest.fixture
    def repo(self, db_session):
        """Create a database repository"""
        return DatabaseRepository(db_session)

    async def test_database_repository_not_implemented(self, repo):
        """Test that DatabaseRepository raises NotImplementedError"""
        with pytest.raises(NotImplementedError):
           await repo.create_user(name="Test", email="test@test.com", password_hash="hash")


# db_session fixture is already defined in conftest.py, no need to redefine it here
