"""Unit tests for MemoryStoreRepository.

Tests cover:
- Store creation (create_store)
- Store retrieval by ID (get_store_by_id)
- Store updates (update_store)
- Store deletion (delete_store)
- List and search stores (get_all_stores, search_stores)
- Store-product relationships (get_products_by_store_from_availabilities)
- Active runs by store (get_active_runs_by_store_for_user)
- Bulk update operations
- Edge cases and data integrity
"""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from app.core.models import Group, Product, ProductAvailability, Run, Store, User
from app.core.run_state import RunState
from app.repositories.memory.storage import MemoryStorage
from app.repositories.memory.store import MemoryStoreRepository


@pytest.fixture
def storage():
    """Create fresh memory storage for each test."""
    storage = MemoryStorage()
    # Clear all data
    storage.stores.clear()
    storage.products.clear()
    storage.product_availabilities.clear()
    storage.users.clear()
    storage.groups.clear()
    storage.group_memberships.clear()
    storage.runs.clear()
    yield storage
    # Clean up after test
    storage.stores.clear()
    storage.products.clear()
    storage.product_availabilities.clear()
    storage.users.clear()
    storage.groups.clear()
    storage.group_memberships.clear()
    storage.runs.clear()


@pytest.fixture
def repo(storage):
    """Create repository instance with fresh storage."""
    return MemoryStoreRepository(storage)


@pytest.fixture
def sample_user(storage):
    """Create a sample user for testing."""
    user = User(
        id=uuid4(),
        name='Test User',
        username='testuser',
        password_hash='hashed',
        is_admin=False,
        verified=False,
    )
    storage.users[user.id] = user
    return user


@pytest.fixture
def admin_user(storage):
    """Create an admin user for testing."""
    user = User(
        id=uuid4(),
        name='Admin User',
        username='adminuser',
        password_hash='hashed',
        is_admin=True,
        verified=True,
    )
    storage.users[user.id] = user
    return user


@pytest.fixture
def sample_store_data():
    """Sample store data for testing."""
    return {
        'name': 'TestMart Downtown',
    }


class TestCreateStore:
    """Test create_store() method."""

    def test_create_store_with_required_fields(self, repo, sample_store_data):
        """Test creating store with required fields."""
        store = repo.create_store(**sample_store_data)

        assert store is not None
        assert store.name == sample_store_data['name']

    def test_create_store_with_name_only(self, repo):
        """Test creating store with name only."""
        store = repo.create_store(name='Simple Store')

        assert store is not None
        assert store.name == 'Simple Store'

    def test_created_store_has_uuid(self, repo, sample_store_data):
        """Test created store has correct ID (UUID)."""
        store = repo.create_store(**sample_store_data)

        assert store.id is not None
        assert isinstance(store.id, UUID)

    def test_created_store_is_stored_and_retrievable(self, repo, sample_store_data):
        """Test created store is stored and retrievable."""
        store = repo.create_store(**sample_store_data)

        retrieved = repo.get_store_by_id(store.id)
        assert retrieved is not None
        assert retrieved.id == store.id
        assert retrieved.name == store.name

    def test_created_store_has_default_values(self, repo, sample_store_data):
        """Test created store has default values (verified=False)."""
        store = repo.create_store(**sample_store_data)

        assert store.verified is False

    def test_creating_multiple_stores_different_ids(self, repo):
        """Test creating multiple stores generates different IDs."""
        store1 = repo.create_store('Store One')
        store2 = repo.create_store('Store Two')

        assert store1.id != store2.id
        assert store1.name != store2.name

    def test_create_store_minimal(self, repo):
        """Test creating store with minimal data."""
        store = repo.create_store(name='Minimal Store')

        assert store.name == 'Minimal Store'
        assert store.verified is False


class TestGetStoreById:
    """Test get_store_by_id() method."""

    def test_get_existing_store_by_id(self, repo, sample_store_data):
        """Test getting existing store by ID."""
        store = repo.create_store(**sample_store_data)

        retrieved = repo.get_store_by_id(store.id)
        assert retrieved is not None
        assert retrieved.id == store.id
        assert retrieved.name == store.name

    def test_get_nonexistent_store_returns_none(self, repo):
        """Test getting non-existent store returns None."""
        fake_id = uuid4()

        result = repo.get_store_by_id(fake_id)
        assert result is None

    def test_get_store_by_id_after_creation(self, repo, sample_store_data):
        """Test getting store immediately after creation."""
        store = repo.create_store(**sample_store_data)
        retrieved = repo.get_store_by_id(store.id)

        assert retrieved is not None
        assert retrieved.id == store.id

    def test_get_store_by_id_after_update(self, repo, sample_store_data):
        """Test getting store after update returns updated data."""
        store = repo.create_store(**sample_store_data)
        repo.update_store(store.id, name='Updated Name')

        retrieved = repo.get_store_by_id(store.id)
        assert retrieved.name == 'Updated Name'


class TestUpdateStore:
    """Test update_store() method."""

    def test_update_store_name(self, repo, sample_store_data):
        """Test updating store name."""
        store = repo.create_store(**sample_store_data)
        new_name = 'TestMart Uptown'

        updated = repo.update_store(store.id, name=new_name)

        assert updated is not None
        assert updated.name == new_name
        assert updated.id == store.id

    def test_update_store_address(self, repo, sample_store_data, storage, sample_user):
        """Test updating store address."""
        store = Store(
            id=uuid4(),
            name='Test Store',
            address='123 Old St',
            verified=False,
            created_by=sample_user.id,
        )
        storage.stores[store.id] = store

        updated = repo.update_store(store.id, address='456 New Ave')

        assert updated.address == '456 New Ave'

    def test_update_store_chain(self, repo, sample_store_data, storage, sample_user):
        """Test updating store chain."""
        store = Store(
            id=uuid4(),
            name='Test Store',
            chain='OldMart',
            verified=False,
            created_by=sample_user.id,
        )
        storage.stores[store.id] = store

        updated = repo.update_store(store.id, chain='NewMart')

        assert updated.chain == 'NewMart'

    def test_update_store_opening_hours(self, repo, sample_store_data, storage, sample_user):
        """Test updating store opening hours (JSON)."""
        store = Store(
            id=uuid4(),
            name='Test Store',
            verified=False,
            created_by=sample_user.id,
        )
        storage.stores[store.id] = store

        opening_hours = {
            'monday': '9:00-21:00',
            'tuesday': '9:00-21:00',
            'wednesday': '9:00-21:00',
        }
        updated = repo.update_store(store.id, opening_hours=opening_hours)

        assert updated.opening_hours == opening_hours

    def test_update_store_verified(self, repo, sample_store_data, admin_user, storage):
        """Test updating store verified flag."""
        store = repo.create_store(**sample_store_data)

        updated = repo.update_store(
            store.id,
            verified=True,
            verified_by=admin_user.id,
            verified_at=datetime.now(UTC),
        )

        assert updated.verified is True
        assert updated.verified_by == admin_user.id
        assert updated.verified_at is not None

    def test_update_nonexistent_store_returns_none(self, repo):
        """Test updating non-existent store returns None."""
        fake_id = uuid4()

        result = repo.update_store(fake_id, name='New Name')
        assert result is None

    def test_update_partial_fields(self, repo, sample_store_data, storage, sample_user):
        """Test partial updates (only some fields)."""
        store = Store(
            id=uuid4(),
            name='Test Store',
            chain='TestMart',
            verified=False,
            created_by=sample_user.id,
        )
        storage.stores[store.id] = store
        original_chain = store.chain

        updated = repo.update_store(store.id, name='New Name')

        assert updated.name == 'New Name'
        assert updated.chain == original_chain  # Unchanged

    def test_update_multiple_fields(self, repo, sample_store_data, storage, sample_user):
        """Test updating multiple fields at once."""
        store = Store(
            id=uuid4(),
            name='Test Store',
            verified=False,
            created_by=sample_user.id,
        )
        storage.stores[store.id] = store

        updated = repo.update_store(
            store.id, name='New Name', address='123 New St', chain='NewChain'
        )

        assert updated.name == 'New Name'
        assert updated.address == '123 New St'
        assert updated.chain == 'NewChain'

    def test_updated_fields_are_persisted(self, repo, sample_store_data):
        """Test updated fields are persisted."""
        store = repo.create_store(**sample_store_data)
        repo.update_store(store.id, name='Updated Name', verified=True)

        # Retrieve again to verify persistence
        retrieved = repo.get_store_by_id(store.id)
        assert retrieved.name == 'Updated Name'
        assert retrieved.verified is True


class TestDeleteStore:
    """Test delete_store() method."""

    def test_delete_existing_store(self, repo, sample_store_data):
        """Test deleting existing store."""
        store = repo.create_store(**sample_store_data)

        result = repo.delete_store(store.id)

        assert result is True

    def test_store_not_retrievable_after_deletion(self, repo, sample_store_data):
        """Test store not retrievable after deletion."""
        store = repo.create_store(**sample_store_data)
        repo.delete_store(store.id)

        retrieved = repo.get_store_by_id(store.id)
        assert retrieved is None

    def test_delete_nonexistent_store_returns_false(self, repo):
        """Test deleting non-existent store returns False."""
        fake_id = uuid4()

        result = repo.delete_store(fake_id)
        assert result is False

    def test_deleting_twice_returns_false_second_time(self, repo, sample_store_data):
        """Test deleting twice returns False second time."""
        store = repo.create_store(**sample_store_data)

        first_delete = repo.delete_store(store.id)
        second_delete = repo.delete_store(store.id)

        assert first_delete is True
        assert second_delete is False


class TestGetAllStores:
    """Test get_all_stores() method."""

    def test_list_all_with_empty_repository(self, repo):
        """Test list_all with empty repository."""
        stores = repo.get_all_stores()

        assert stores == []
        assert len(stores) == 0

    def test_list_all_after_creating_multiple_stores(self, repo):
        """Test list_all after creating multiple stores."""
        store1 = repo.create_store('Store 1')
        store2 = repo.create_store('Store 2')
        store3 = repo.create_store('Store 3')

        stores = repo.get_all_stores()

        assert len(stores) == 3
        store_ids = {s.id for s in stores}
        assert store1.id in store_ids
        assert store2.id in store_ids
        assert store3.id in store_ids

    def test_list_all_returns_all_stores(self, repo):
        """Test list_all returns all stores."""
        created_stores = []
        for i in range(5):
            store = repo.create_store(f'Store {i}')
            created_stores.append(store)

        stores = repo.get_all_stores()

        assert len(stores) == 5
        for created in created_stores:
            assert any(s.id == created.id for s in stores)

    def test_list_all_includes_all_store_fields(self, repo, sample_store_data):
        """Test list_all includes all store fields."""
        store = repo.create_store(**sample_store_data)

        stores = repo.get_all_stores()

        assert len(stores) == 1
        retrieved = stores[0]
        assert retrieved.id == store.id
        assert retrieved.name == store.name
        assert retrieved.verified == store.verified

    def test_list_all_count_matches_created(self, repo):
        """Test list_all count matches number created."""
        count = 10
        for i in range(count):
            repo.create_store(f'Store {i}')

        stores = repo.get_all_stores()

        assert len(stores) == count

    def test_list_all_after_deletion(self, repo):
        """Test list_all after deletion (count decreases)."""
        store1 = repo.create_store('Store 1')
        store2 = repo.create_store('Store 2')
        store3 = repo.create_store('Store 3')

        assert len(repo.get_all_stores()) == 3

        repo.delete_store(store2.id)

        stores = repo.get_all_stores()
        assert len(stores) == 2
        store_ids = {s.id for s in stores}
        assert store1.id in store_ids
        assert store2.id not in store_ids
        assert store3.id in store_ids

    def test_list_all_sorted_by_name(self, repo):
        """Test list_all returns stores sorted by name."""
        repo.create_store('Zebra Store')
        repo.create_store('Alpha Store')
        repo.create_store('Beta Store')

        stores = repo.get_all_stores()

        assert stores[0].name == 'Alpha Store'
        assert stores[1].name == 'Beta Store'
        assert stores[2].name == 'Zebra Store'

    def test_list_all_with_pagination(self, repo):
        """Test list_all with limit and offset."""
        for i in range(10):
            repo.create_store(f'Store {i:02d}')

        # Get first 3 stores
        stores = repo.get_all_stores(limit=3, offset=0)
        assert len(stores) == 3

        # Get next 3 stores
        stores = repo.get_all_stores(limit=3, offset=3)
        assert len(stores) == 3

        # Get last 4 stores
        stores = repo.get_all_stores(limit=10, offset=6)
        assert len(stores) == 4


class TestSearchStores:
    """Test search_stores() method."""

    def test_search_by_name_exact_match(self, repo):
        """Test search by exact name match."""
        store = repo.create_store('Downtown Costco')
        repo.create_store('Uptown Walmart')

        results = repo.search_stores('Downtown Costco')

        assert len(results) == 1
        assert results[0].id == store.id

    def test_search_by_name_partial_match(self, repo):
        """Test search by partial name match."""
        store1 = repo.create_store('Downtown Costco')
        store2 = repo.create_store('Uptown Costco')
        repo.create_store('Walmart')

        results = repo.search_stores('Costco')

        assert len(results) == 2
        result_ids = {s.id for s in results}
        assert store1.id in result_ids
        assert store2.id in result_ids

    def test_search_case_insensitive(self, repo):
        """Test search is case-insensitive."""
        store = repo.create_store('Downtown Costco')

        results = repo.search_stores('downtown costco')

        assert len(results) == 1
        assert results[0].id == store.id

    def test_search_with_no_matches(self, repo):
        """Test search with no matches."""
        repo.create_store('Downtown Costco')

        results = repo.search_stores('Walmart')

        assert results == []

    def test_search_empty_query(self, repo):
        """Test search with empty query returns all stores."""
        repo.create_store('Store 1')
        repo.create_store('Store 2')

        results = repo.search_stores('')

        assert len(results) == 2

    def test_search_in_empty_repository(self, repo):
        """Test search in empty repository."""
        results = repo.search_stores('anything')

        assert results == []

    def test_search_by_lowercase(self, repo):
        """Test search with lowercase query matches uppercase store."""
        store = repo.create_store('UPPERCASE STORE')

        results = repo.search_stores('uppercase')

        assert len(results) == 1
        assert results[0].id == store.id

    def test_search_by_uppercase(self, repo):
        """Test search with uppercase query matches lowercase store."""
        store = repo.create_store('lowercase store')

        results = repo.search_stores('LOWERCASE')

        assert len(results) == 1
        assert results[0].id == store.id


class TestGetProductsByStore:
    """Test get_products_by_store_from_availabilities() method."""

    def test_get_products_by_store(self, repo, storage, sample_user):
        """Test getting products available at a store."""
        store = repo.create_store('Test Store')

        # Create products
        product1 = Product(
            id=uuid4(),
            name='Product 1',
            brand='Brand A',
            unit='kg',
            verified=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        product2 = Product(
            id=uuid4(),
            name='Product 2',
            brand='Brand B',
            unit='L',
            verified=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        product3 = Product(
            id=uuid4(),
            name='Product 3',
            brand='Brand C',
            unit='each',
            verified=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        storage.products[product1.id] = product1
        storage.products[product2.id] = product2
        storage.products[product3.id] = product3

        # Add availabilities for products 1 and 2 at the store
        avail1 = ProductAvailability(
            id=uuid4(),
            product_id=product1.id,
            store_id=store.id,
            price=Decimal('5.99'),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            created_by=sample_user.id,
        )
        avail2 = ProductAvailability(
            id=uuid4(),
            product_id=product2.id,
            store_id=store.id,
            price=Decimal('3.99'),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            created_by=sample_user.id,
        )

        storage.product_availabilities[avail1.id] = avail1
        storage.product_availabilities[avail2.id] = avail2

        products = repo.get_products_by_store_from_availabilities(store.id)

        assert len(products) == 2
        product_ids = {p.id for p in products}
        assert product1.id in product_ids
        assert product2.id in product_ids
        assert product3.id not in product_ids

    def test_get_products_by_store_empty(self, repo):
        """Test getting products for store with no availabilities."""
        store = repo.create_store('Empty Store')

        products = repo.get_products_by_store_from_availabilities(store.id)

        assert products == []

    def test_get_products_by_store_unique_products(self, repo, storage, sample_user):
        """Test getting unique products (no duplicates) when multiple availabilities exist."""
        store = repo.create_store('Test Store')

        # Create product
        product = Product(
            id=uuid4(),
            name='Product',
            brand='Brand',
            unit='kg',
            verified=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        storage.products[product.id] = product

        # Add multiple availabilities for same product at same store
        avail1 = ProductAvailability(
            id=uuid4(),
            product_id=product.id,
            store_id=store.id,
            price=Decimal('5.99'),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            created_by=sample_user.id,
        )
        avail2 = ProductAvailability(
            id=uuid4(),
            product_id=product.id,
            store_id=store.id,
            price=Decimal('6.99'),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            created_by=sample_user.id,
        )

        storage.product_availabilities[avail1.id] = avail1
        storage.product_availabilities[avail2.id] = avail2

        products = repo.get_products_by_store_from_availabilities(store.id)

        # Should only return one instance of the product
        assert len(products) == 1
        assert products[0].id == product.id


class TestGetActiveRunsByStoreForUser:
    """Test get_active_runs_by_store_for_user() method."""

    def test_get_active_runs_by_store_for_user(self, repo, storage, sample_user):
        """Test getting active runs by store for user."""
        store = repo.create_store('Test Store')

        # Create group and add user
        group = Group(id=uuid4(), name='Test Group', created_by=sample_user.id)
        storage.groups[group.id] = group
        storage.group_memberships[group.id] = [sample_user.id]

        # Create active run
        run = Run(
            id=uuid4(),
            group_id=group.id,
            store_id=store.id,
            state=RunState.ACTIVE,
            planning_at=datetime.now(UTC),
        )
        storage.runs[run.id] = run

        runs = repo.get_active_runs_by_store_for_user(store.id, sample_user.id)

        assert len(runs) == 1
        assert runs[0].id == run.id

    def test_get_active_runs_multiple_states(self, repo, storage, sample_user):
        """Test getting runs in various active states."""
        store = repo.create_store('Test Store')

        # Create group and add user
        group = Group(id=uuid4(), name='Test Group', created_by=sample_user.id)
        storage.groups[group.id] = group
        storage.group_memberships[group.id] = [sample_user.id]

        # Create runs in different active states
        run1 = Run(
            id=uuid4(),
            group_id=group.id,
            store_id=store.id,
            state=RunState.PLANNING,
            planning_at=datetime.now(UTC),
        )
        run2 = Run(
            id=uuid4(),
            group_id=group.id,
            store_id=store.id,
            state=RunState.ACTIVE,
            planning_at=datetime.now(UTC),
        )
        run3 = Run(
            id=uuid4(),
            group_id=group.id,
            store_id=store.id,
            state=RunState.SHOPPING,
            planning_at=datetime.now(UTC),
        )

        storage.runs[run1.id] = run1
        storage.runs[run2.id] = run2
        storage.runs[run3.id] = run3

        runs = repo.get_active_runs_by_store_for_user(store.id, sample_user.id)

        assert len(runs) == 3
        run_ids = {r.id for r in runs}
        assert run1.id in run_ids
        assert run2.id in run_ids
        assert run3.id in run_ids

    def test_get_active_runs_excludes_completed(self, repo, storage, sample_user):
        """Test that completed runs are excluded."""
        store = repo.create_store('Test Store')

        # Create group and add user
        group = Group(id=uuid4(), name='Test Group', created_by=sample_user.id)
        storage.groups[group.id] = group
        storage.group_memberships[group.id] = [sample_user.id]

        # Create runs
        run1 = Run(
            id=uuid4(),
            group_id=group.id,
            store_id=store.id,
            state=RunState.ACTIVE,
            planning_at=datetime.now(UTC),
        )
        run2 = Run(
            id=uuid4(),
            group_id=group.id,
            store_id=store.id,
            state=RunState.COMPLETED,
            planning_at=datetime.now(UTC),
        )

        storage.runs[run1.id] = run1
        storage.runs[run2.id] = run2

        runs = repo.get_active_runs_by_store_for_user(store.id, sample_user.id)

        assert len(runs) == 1
        assert runs[0].id == run1.id

    def test_get_active_runs_user_not_in_group(self, repo, storage, sample_user):
        """Test that runs from groups user is not in are excluded."""
        store = repo.create_store('Test Store')

        # Create group WITHOUT adding user
        group = Group(id=uuid4(), name='Test Group', created_by=uuid4())
        storage.groups[group.id] = group
        storage.group_memberships[group.id] = [uuid4()]  # Different user

        # Create active run
        run = Run(
            id=uuid4(),
            group_id=group.id,
            store_id=store.id,
            state=RunState.ACTIVE,
            planning_at=datetime.now(UTC),
        )
        storage.runs[run.id] = run

        runs = repo.get_active_runs_by_store_for_user(store.id, sample_user.id)

        assert len(runs) == 0

    def test_get_active_runs_different_store(self, repo, storage, sample_user):
        """Test that runs at different stores are excluded."""
        store1 = repo.create_store('Store 1')
        store2 = repo.create_store('Store 2')

        # Create group and add user
        group = Group(id=uuid4(), name='Test Group', created_by=sample_user.id)
        storage.groups[group.id] = group
        storage.group_memberships[group.id] = [sample_user.id]

        # Create run at store2
        run = Run(
            id=uuid4(),
            group_id=group.id,
            store_id=store2.id,
            state=RunState.ACTIVE,
            planning_at=datetime.now(UTC),
        )
        storage.runs[run.id] = run

        # Query for store1
        runs = repo.get_active_runs_by_store_for_user(store1.id, sample_user.id)

        assert len(runs) == 0


class TestBulkUpdateOperations:
    """Test bulk update operations."""

    def test_bulk_update_runs(self, repo, storage, sample_user):
        """Test bulk updating runs."""
        old_store = repo.create_store('Old Store')
        new_store = repo.create_store('New Store')

        # Create group
        group = Group(id=uuid4(), name='Test Group', created_by=sample_user.id)
        storage.groups[group.id] = group

        # Create runs for old store
        run1 = Run(
            id=uuid4(),
            group_id=group.id,
            store_id=old_store.id,
            state=RunState.ACTIVE,
            planning_at=datetime.now(UTC),
        )
        run2 = Run(
            id=uuid4(),
            group_id=group.id,
            store_id=old_store.id,
            state=RunState.PLANNING,
            planning_at=datetime.now(UTC),
        )

        storage.runs[run1.id] = run1
        storage.runs[run2.id] = run2

        count = repo.bulk_update_runs(old_store.id, new_store.id)

        assert count == 2
        assert storage.runs[run1.id].store_id == new_store.id
        assert storage.runs[run2.id].store_id == new_store.id

    def test_bulk_update_runs_no_matches(self, repo):
        """Test bulk update with no matching runs."""
        store1 = repo.create_store('Store 1')
        store2 = repo.create_store('Store 2')

        count = repo.bulk_update_runs(store1.id, store2.id)

        assert count == 0

    def test_bulk_update_store_availabilities(self, repo, storage, sample_user):
        """Test bulk updating store availabilities."""
        old_store = repo.create_store('Old Store')
        new_store = repo.create_store('New Store')

        # Create product
        product = Product(
            id=uuid4(),
            name='Product',
            brand='Brand',
            unit='kg',
            verified=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        storage.products[product.id] = product

        # Create availabilities for old store
        avail1 = ProductAvailability(
            id=uuid4(),
            product_id=product.id,
            store_id=old_store.id,
            price=Decimal('5.99'),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            created_by=sample_user.id,
        )
        avail2 = ProductAvailability(
            id=uuid4(),
            product_id=product.id,
            store_id=old_store.id,
            price=Decimal('6.99'),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            created_by=sample_user.id,
        )

        storage.product_availabilities[avail1.id] = avail1
        storage.product_availabilities[avail2.id] = avail2

        count = repo.bulk_update_store_availabilities(old_store.id, new_store.id)

        assert count == 2
        assert storage.product_availabilities[avail1.id].store_id == new_store.id
        assert storage.product_availabilities[avail2.id].store_id == new_store.id

    def test_count_store_runs(self, repo, storage, sample_user):
        """Test counting store runs."""
        store = repo.create_store('Test Store')

        # Create group
        group = Group(id=uuid4(), name='Test Group', created_by=sample_user.id)
        storage.groups[group.id] = group

        # Create runs for store
        run1 = Run(
            id=uuid4(),
            group_id=group.id,
            store_id=store.id,
            state=RunState.ACTIVE,
            planning_at=datetime.now(UTC),
        )
        run2 = Run(
            id=uuid4(),
            group_id=group.id,
            store_id=store.id,
            state=RunState.COMPLETED,
            planning_at=datetime.now(UTC),
        )

        storage.runs[run1.id] = run1
        storage.runs[run2.id] = run2

        count = repo.count_store_runs(store.id)

        assert count == 2


class TestOpeningHours:
    """Test opening hours functionality."""

    def test_store_with_opening_hours(self, repo, storage, sample_user):
        """Test creating store with opening hours JSON."""
        opening_hours = {
            'monday': '9:00-21:00',
            'tuesday': '9:00-21:00',
            'wednesday': '9:00-21:00',
            'thursday': '9:00-21:00',
            'friday': '9:00-21:00',
            'saturday': '10:00-18:00',
            'sunday': 'Closed',
        }

        store = Store(
            id=uuid4(),
            name='Test Store',
            opening_hours=opening_hours,
            verified=False,
            created_by=sample_user.id,
        )
        storage.stores[store.id] = store

        retrieved = repo.get_store_by_id(store.id)
        assert retrieved.opening_hours == opening_hours

    def test_update_opening_hours(self, repo, storage, sample_user):
        """Test updating opening hours."""
        store = Store(
            id=uuid4(),
            name='Test Store',
            verified=False,
            created_by=sample_user.id,
        )
        storage.stores[store.id] = store

        opening_hours = {'monday': '8:00-20:00'}
        updated = repo.update_store(store.id, opening_hours=opening_hours)

        assert updated.opening_hours == opening_hours

    def test_store_without_opening_hours(self, repo):
        """Test store without opening hours (None)."""
        store = repo.create_store('Test Store')

        assert store.opening_hours is None

    def test_empty_opening_hours(self, repo, storage, sample_user):
        """Test store with empty opening hours dict."""
        store = Store(
            id=uuid4(),
            name='Test Store',
            opening_hours={},
            verified=False,
            created_by=sample_user.id,
        )
        storage.stores[store.id] = store

        retrieved = repo.get_store_by_id(store.id)
        assert retrieved.opening_hours == {}


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_very_long_store_name(self, repo):
        """Test with very long store name."""
        long_name = 'a' * 1000
        store = repo.create_store(long_name)

        retrieved = repo.get_store_by_id(store.id)
        assert retrieved is not None
        assert retrieved.name == long_name

    def test_special_characters_in_name(self, repo):
        """Test with special characters in store name."""
        special_name = "Sam's Club - Downtown (24/7)"
        store = repo.create_store(special_name)

        assert store.name == special_name
        retrieved = repo.get_store_by_id(store.id)
        assert retrieved.name == special_name

    def test_unicode_characters_in_address(self, repo, storage, sample_user):
        """Test with unicode characters in address."""
        unicode_address = '北京市朝阳区123号'
        store = Store(
            id=uuid4(),
            name='Test Store',
            address=unicode_address,
            verified=False,
            created_by=sample_user.id,
        )
        storage.stores[store.id] = store

        retrieved = repo.get_store_by_id(store.id)
        assert retrieved.address == unicode_address

    def test_concurrent_operations(self, repo):
        """Test creating multiple stores (simulating concurrent operations)."""
        stores = []
        for i in range(100):
            store = repo.create_store(f'Store {i}')
            stores.append(store)

        # Verify all stores exist
        all_stores = repo.get_all_stores()
        assert len(all_stores) == 100

        # Verify all IDs are unique
        ids = [s.id for s in all_stores]
        assert len(ids) == len(set(ids))

    def test_repository_isolation(self, storage):
        """Test fresh repository instance per test (via fixture)."""
        # This test verifies the fixture works correctly
        assert len(storage.stores) == 0
        assert len(storage.product_availabilities) == 0

    def test_search_with_special_characters(self, repo):
        """Test search with special characters."""
        store = repo.create_store("Sam's Club (Downtown)")

        results = repo.search_stores("Sam's")

        assert len(results) == 1
        assert results[0].id == store.id


class TestDataIntegrity:
    """Test data integrity and isolation."""

    def test_store_object_has_expected_fields(self, repo, sample_store_data):
        """Test store object has all expected fields."""
        store = repo.create_store(**sample_store_data)

        assert hasattr(store, 'id')
        assert hasattr(store, 'name')
        assert hasattr(store, 'verified')

    def test_store_object_is_not_none(self, repo, sample_store_data):
        """Test store object is not None."""
        store = repo.create_store(**sample_store_data)

        assert store is not None
        retrieved = repo.get_store_by_id(store.id)
        assert retrieved is not None

    def test_multiple_repositories_share_storage(self, storage):
        """Test multiple repository instances share the same storage."""
        repo1 = MemoryStoreRepository(storage)
        repo2 = MemoryStoreRepository(storage)

        store = repo1.create_store('Store')

        # Both repositories should see the same store
        assert repo2.get_store_by_id(store.id) is not None
        assert len(repo2.get_all_stores()) == 1
