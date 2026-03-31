"""Unit tests for MemoryShoppingRepository.

Tests cover:
- Shopping list item creation (create_shopping_list_item)
- Item retrieval by ID (get_shopping_list_item)
- Get items by run (get_shopping_list_items)
- Get items by product (get_shopping_list_items_by_product)
- Mark item purchased (mark_item_purchased)
- Update item purchase (update_item_purchase)
- Add more purchased (add_more_purchased)
- Unpurchase item (unpurchase_item)
- Update requested quantity (update_shopping_list_item_requested_quantity)
- Purchase order management
- UUID generation and default values
- Edge cases and data integrity
"""

from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from app.repositories.memory.group import MemoryGroupRepository
from app.repositories.memory.product import MemoryProductRepository
from app.repositories.memory.run import MemoryRunRepository
from app.repositories.memory.shopping import MemoryShoppingRepository
from app.repositories.memory.storage import MemoryStorage
from app.repositories.memory.store import MemoryStoreRepository
from app.repositories.memory.user import MemoryUserRepository


@pytest.fixture
def storage():
    """Create fresh memory storage for each test."""
    storage = MemoryStorage()
    # Clear all data
    storage.users.clear()
    storage.users_by_username.clear()
    storage.groups.clear()
    storage.group_memberships.clear()
    storage.group_admin_status.clear()
    storage.stores.clear()
    storage.runs.clear()
    storage.participations.clear()
    storage.bids.clear()
    storage.products.clear()
    storage.shopping_list_items.clear()
    yield storage
    # Clean up after test
    storage.users.clear()
    storage.users_by_username.clear()
    storage.groups.clear()
    storage.group_memberships.clear()
    storage.group_admin_status.clear()
    storage.stores.clear()
    storage.runs.clear()
    storage.participations.clear()
    storage.bids.clear()
    storage.products.clear()
    storage.shopping_list_items.clear()


@pytest.fixture
def repo(storage):
    """Create shopping repository instance with fresh storage."""
    return MemoryShoppingRepository(storage)


@pytest.fixture
def user_repo(storage):
    """Create user repository instance with fresh storage."""
    return MemoryUserRepository(storage)


@pytest.fixture
def group_repo(storage):
    """Create group repository instance with fresh storage."""
    return MemoryGroupRepository(storage)


@pytest.fixture
def store_repo(storage):
    """Create store repository instance with fresh storage."""
    return MemoryStoreRepository(storage)


@pytest.fixture
def run_repo(storage):
    """Create run repository instance with fresh storage."""
    return MemoryRunRepository(storage)


@pytest.fixture
def product_repo(storage):
    """Create product repository instance with fresh storage."""
    return MemoryProductRepository(storage)


@pytest.fixture
def sample_user(user_repo):
    """Create a sample user for testing."""
    return user_repo.create_user('Test User', 'testuser', 'hashed_password')


@pytest.fixture
def sample_users(user_repo):
    """Create multiple sample users for testing."""
    return [user_repo.create_user(f'User {i}', f'user{i}', f'hash{i}') for i in range(1, 5)]


@pytest.fixture
def sample_group(group_repo, sample_user):
    """Create a sample group for testing."""
    return group_repo.create_group('Test Group', sample_user.id)


@pytest.fixture
def sample_store(store_repo):
    """Create a sample store for testing."""
    return store_repo.create_store('Test Store')


@pytest.fixture
def sample_run(run_repo, sample_group, sample_store, sample_user):
    """Create a sample run for testing."""
    return run_repo.create_run(sample_group.id, sample_store.id, sample_user.id)


@pytest.fixture
def sample_product(product_repo):
    """Create a sample product for testing."""
    return product_repo.create_product('Test Product', brand='Test Brand', unit='kg')


@pytest.fixture
def sample_products(product_repo):
    """Create multiple sample products for testing."""
    return [
        product_repo.create_product(f'Product {i}', brand=f'Brand {i}', unit='kg')
        for i in range(1, 5)
    ]


class TestCreateShoppingListItem:
    """Test create_shopping_list_item() method."""

    def test_create_item_with_required_fields(self, repo, sample_run, sample_product):
        """Test creating shopping list item with all required fields."""
        item = repo.create_shopping_list_item(
            run_id=sample_run.id, product_id=sample_product.id, requested_quantity=10
        )

        assert item is not None
        assert item.run_id == sample_run.id
        assert item.product_id == sample_product.id
        assert item.requested_quantity == 10

    def test_created_item_has_uuid(self, repo, sample_run, sample_product):
        """Test created item has correct ID (UUID)."""
        item = repo.create_shopping_list_item(
            run_id=sample_run.id, product_id=sample_product.id, requested_quantity=5
        )

        assert item.id is not None
        assert isinstance(item.id, UUID)

    def test_default_is_purchased_is_false(self, repo, sample_run, sample_product):
        """Test default is_purchased is False."""
        item = repo.create_shopping_list_item(
            run_id=sample_run.id, product_id=sample_product.id, requested_quantity=10
        )

        assert item.is_purchased is False

    def test_default_purchased_quantity_is_none(self, repo, sample_run, sample_product):
        """Test default purchased_quantity is None."""
        item = repo.create_shopping_list_item(
            run_id=sample_run.id, product_id=sample_product.id, requested_quantity=10
        )

        assert item.purchased_quantity is None
        assert item.purchased_price_per_unit is None
        assert item.purchased_total is None

    def test_item_includes_run_relationship(self, repo, sample_run, sample_product):
        """Test item includes run relationship."""
        item = repo.create_shopping_list_item(
            run_id=sample_run.id, product_id=sample_product.id, requested_quantity=10
        )

        assert item.run is not None
        assert item.run.id == sample_run.id

    def test_item_includes_product_relationship(self, repo, sample_run, sample_product):
        """Test item includes product relationship."""
        item = repo.create_shopping_list_item(
            run_id=sample_run.id, product_id=sample_product.id, requested_quantity=10
        )

        assert item.product is not None
        assert item.product.id == sample_product.id

    def test_create_multiple_items_for_run(self, repo, sample_run, sample_products):
        """Test creating multiple items for the same run."""
        items = []
        for product in sample_products[:3]:
            item = repo.create_shopping_list_item(
                run_id=sample_run.id, product_id=product.id, requested_quantity=5
            )
            items.append(item)

        # All items should have unique IDs
        item_ids = [i.id for i in items]
        assert len(item_ids) == len(set(item_ids))

        # All items should be for same run
        for item in items:
            assert item.run_id == sample_run.id


class TestGetShoppingListItem:
    """Test get_shopping_list_item() method."""

    def test_get_existing_item(self, repo, sample_run, sample_product):
        """Test getting existing shopping list item by ID."""
        item = repo.create_shopping_list_item(
            run_id=sample_run.id, product_id=sample_product.id, requested_quantity=10
        )

        retrieved = repo.get_shopping_list_item(item.id)

        assert retrieved is not None
        assert retrieved.id == item.id
        assert retrieved.run_id == item.run_id
        assert retrieved.product_id == item.product_id
        assert retrieved.requested_quantity == item.requested_quantity

    def test_get_nonexistent_item_returns_none(self, repo):
        """Test getting non-existent item returns None."""
        fake_id = uuid4()

        result = repo.get_shopping_list_item(fake_id)

        assert result is None

    def test_get_item_with_invalid_uuid(self, repo):
        """Test getting item with None ID."""
        result = repo.get_shopping_list_item(None)

        assert result is None


class TestGetShoppingListItems:
    """Test get_shopping_list_items() method."""

    def test_get_all_items_for_run(self, repo, sample_run, sample_products):
        """Test getting all shopping list items for a run."""
        # Create multiple items
        for product in sample_products[:3]:
            repo.create_shopping_list_item(
                run_id=sample_run.id, product_id=product.id, requested_quantity=5
            )

        items = repo.get_shopping_list_items(sample_run.id)

        assert len(items) == 3
        for item in items:
            assert item.run_id == sample_run.id

    def test_empty_list_for_run_with_no_items(self, repo, sample_run):
        """Test empty list for run with no shopping list items."""
        items = repo.get_shopping_list_items(sample_run.id)

        assert items == []
        assert len(items) == 0

    def test_multiple_items_returned(self, repo, sample_run, sample_products):
        """Test multiple items are returned."""
        for product in sample_products:
            repo.create_shopping_list_item(
                run_id=sample_run.id, product_id=product.id, requested_quantity=10
            )

        items = repo.get_shopping_list_items(sample_run.id)

        assert len(items) == len(sample_products)

    def test_items_include_product_details(self, repo, sample_run, sample_products):
        """Test items include product details."""
        for product in sample_products[:2]:
            repo.create_shopping_list_item(
                run_id=sample_run.id, product_id=product.id, requested_quantity=5
            )

        items = repo.get_shopping_list_items(sample_run.id)

        for item in items:
            assert item.product is not None
            assert item.product.name is not None

    def test_only_returns_items_for_specific_run(
        self, repo, run_repo, group_repo, store_repo, sample_user, sample_product, sample_store
    ):
        """Test only returns items for specific run."""
        # Create two groups and two runs
        group1 = group_repo.create_group('Group 1', sample_user.id)
        group2 = group_repo.create_group('Group 2', sample_user.id)

        run1 = run_repo.create_run(group1.id, sample_store.id, sample_user.id)
        run2 = run_repo.create_run(group2.id, sample_store.id, sample_user.id)

        # Create item for run1
        repo.create_shopping_list_item(
            run_id=run1.id, product_id=sample_product.id, requested_quantity=10
        )

        # Create item for run2
        repo.create_shopping_list_item(
            run_id=run2.id, product_id=sample_product.id, requested_quantity=20
        )

        items_run1 = repo.get_shopping_list_items(run1.id)
        items_run2 = repo.get_shopping_list_items(run2.id)

        assert len(items_run1) == 1
        assert len(items_run2) == 1
        assert items_run1[0].requested_quantity == 10
        assert items_run2[0].requested_quantity == 20


class TestGetShoppingListItemsByProduct:
    """Test get_shopping_list_items_by_product() method."""

    def test_get_items_for_product_across_runs(
        self, repo, run_repo, group_repo, store_repo, sample_user, sample_product, sample_store
    ):
        """Test getting shopping list items for a product across all runs."""
        # Create multiple runs
        group = group_repo.create_group('Test Group', sample_user.id)
        runs = [run_repo.create_run(group.id, sample_store.id, sample_user.id) for _ in range(3)]

        # Create items for same product in different runs
        for run in runs:
            repo.create_shopping_list_item(
                run_id=run.id, product_id=sample_product.id, requested_quantity=10
            )

        items = repo.get_shopping_list_items_by_product(sample_product.id)

        assert len(items) == 3
        for item in items:
            assert item.product_id == sample_product.id

    def test_empty_list_for_product_with_no_items(self, repo, sample_product):
        """Test empty list for product with no items."""
        items = repo.get_shopping_list_items_by_product(sample_product.id)

        assert items == []

    def test_items_include_run_and_product_relationships(
        self, repo, run_repo, group_repo, sample_user, sample_store, sample_product
    ):
        """Test items include run and product relationships."""
        group = group_repo.create_group('Test Group', sample_user.id)
        run = run_repo.create_run(group.id, sample_store.id, sample_user.id)

        repo.create_shopping_list_item(
            run_id=run.id, product_id=sample_product.id, requested_quantity=10
        )

        items = repo.get_shopping_list_items_by_product(sample_product.id)

        assert len(items) == 1
        item = items[0]
        assert item.run is not None
        assert item.run.id == run.id
        assert item.product is not None
        assert item.product.id == sample_product.id


class TestMarkItemPurchased:
    """Test mark_item_purchased() method."""

    def test_mark_item_as_purchased(self, repo, sample_run, sample_product):
        """Test marking an item as purchased."""
        item = repo.create_shopping_list_item(
            run_id=sample_run.id, product_id=sample_product.id, requested_quantity=10
        )

        updated_item = repo.mark_item_purchased(
            item_id=item.id, quantity=10, price_per_unit=2.5, total=25.0, purchase_order=1
        )

        assert updated_item is not None
        assert updated_item.is_purchased is True
        assert updated_item.purchased_quantity == 10
        assert updated_item.purchased_price_per_unit == Decimal('2.5')
        assert updated_item.purchased_total == Decimal('25.0')
        assert updated_item.purchase_order == 1

    def test_mark_item_purchased_sets_is_purchased_flag(self, repo, sample_run, sample_product):
        """Test mark_item_purchased sets is_purchased to True."""
        item = repo.create_shopping_list_item(
            run_id=sample_run.id, product_id=sample_product.id, requested_quantity=10
        )

        repo.mark_item_purchased(
            item_id=item.id, quantity=10, price_per_unit=2.5, total=25.0, purchase_order=1
        )

        retrieved = repo.get_shopping_list_item(item.id)
        assert retrieved.is_purchased is True

    def test_mark_item_purchased_with_decimal_precision(self, repo, sample_run, sample_product):
        """Test mark_item_purchased with decimal precision."""
        item = repo.create_shopping_list_item(
            run_id=sample_run.id, product_id=sample_product.id, requested_quantity=10
        )

        updated_item = repo.mark_item_purchased(
            item_id=item.id, quantity=8, price_per_unit=3.75, total=30.0, purchase_order=1
        )

        assert updated_item.purchased_quantity == 8
        assert updated_item.purchased_price_per_unit == Decimal('3.75')
        assert updated_item.purchased_total == Decimal('30.0')

    def test_mark_item_purchased_updates_purchase_order(self, repo, sample_run, sample_product):
        """Test mark_item_purchased updates purchase_order."""
        item = repo.create_shopping_list_item(
            run_id=sample_run.id, product_id=sample_product.id, requested_quantity=10
        )

        repo.mark_item_purchased(
            item_id=item.id, quantity=10, price_per_unit=2.5, total=25.0, purchase_order=5
        )

        retrieved = repo.get_shopping_list_item(item.id)
        assert retrieved.purchase_order == 5

    def test_mark_nonexistent_item_purchased_returns_none(self, repo):
        """Test marking non-existent item returns None."""
        fake_id = uuid4()

        result = repo.mark_item_purchased(
            item_id=fake_id, quantity=10, price_per_unit=2.5, total=25.0, purchase_order=1
        )

        assert result is None

    def test_mark_multiple_items_purchased(self, repo, sample_run, sample_products):
        """Test marking multiple items as purchased."""
        items = []
        for i, product in enumerate(sample_products[:3], start=1):
            item = repo.create_shopping_list_item(
                run_id=sample_run.id, product_id=product.id, requested_quantity=10
            )
            items.append(item)

            repo.mark_item_purchased(
                item_id=item.id,
                quantity=10,
                price_per_unit=2.5 * i,
                total=25.0 * i,
                purchase_order=i,
            )

        # Verify all items are marked as purchased
        for i, item in enumerate(items, start=1):
            retrieved = repo.get_shopping_list_item(item.id)
            assert retrieved.is_purchased is True
            assert retrieved.purchase_order == i


class TestUpdateItemPurchase:
    """Test update_item_purchase() method."""

    def test_update_existing_purchase(self, repo, sample_run, sample_product):
        """Test updating an existing purchase."""
        item = repo.create_shopping_list_item(
            run_id=sample_run.id, product_id=sample_product.id, requested_quantity=10
        )

        # Mark as purchased
        repo.mark_item_purchased(
            item_id=item.id, quantity=10, price_per_unit=2.5, total=25.0, purchase_order=1
        )

        # Update purchase
        updated_item = repo.update_item_purchase(
            item_id=item.id, quantity=12, price_per_unit=3.0, total=36.0
        )

        assert updated_item is not None
        assert updated_item.purchased_quantity == 12
        assert updated_item.purchased_price_per_unit == Decimal('3.0')
        assert updated_item.purchased_total == Decimal('36.0')
        assert updated_item.is_purchased is True
        assert updated_item.purchase_order == 1  # Should remain unchanged

    def test_update_purchase_keeps_is_purchased_flag(self, repo, sample_run, sample_product):
        """Test update_item_purchase keeps is_purchased flag."""
        item = repo.create_shopping_list_item(
            run_id=sample_run.id, product_id=sample_product.id, requested_quantity=10
        )

        repo.mark_item_purchased(
            item_id=item.id, quantity=10, price_per_unit=2.5, total=25.0, purchase_order=1
        )

        repo.update_item_purchase(item_id=item.id, quantity=8, price_per_unit=2.0, total=16.0)

        retrieved = repo.get_shopping_list_item(item.id)
        assert retrieved.is_purchased is True

    def test_update_unpurchased_item_returns_none(self, repo, sample_run, sample_product):
        """Test updating unpurchased item returns None."""
        item = repo.create_shopping_list_item(
            run_id=sample_run.id, product_id=sample_product.id, requested_quantity=10
        )

        result = repo.update_item_purchase(
            item_id=item.id, quantity=10, price_per_unit=2.5, total=25.0
        )

        assert result is None

    def test_update_nonexistent_item_returns_none(self, repo):
        """Test updating non-existent item returns None."""
        fake_id = uuid4()

        result = repo.update_item_purchase(
            item_id=fake_id, quantity=10, price_per_unit=2.5, total=25.0
        )

        assert result is None


class TestAddMorePurchased:
    """Test add_more_purchased() method."""

    def test_add_more_purchased_to_item(self, repo, sample_run, sample_product):
        """Test adding more purchased quantity to an item."""
        item = repo.create_shopping_list_item(
            run_id=sample_run.id, product_id=sample_product.id, requested_quantity=20
        )

        # Initial purchase
        repo.mark_item_purchased(
            item_id=item.id, quantity=10, price_per_unit=2.5, total=25.0, purchase_order=1
        )

        # Add more
        updated_item = repo.add_more_purchased(
            item_id=item.id,
            additional_quantity=5.0,
            additional_total=15.0,
            new_price_per_unit=2.67,
        )

        assert updated_item is not None
        assert updated_item.purchased_quantity == 15.0
        assert updated_item.purchased_total == Decimal('40.0')
        assert updated_item.purchased_price_per_unit == Decimal('2.67')

    def test_add_more_purchased_accumulates_quantity(self, repo, sample_run, sample_product):
        """Test add_more_purchased accumulates quantity."""
        item = repo.create_shopping_list_item(
            run_id=sample_run.id, product_id=sample_product.id, requested_quantity=20
        )

        repo.mark_item_purchased(
            item_id=item.id, quantity=8, price_per_unit=2.0, total=16.0, purchase_order=1
        )

        repo.add_more_purchased(
            item_id=item.id,
            additional_quantity=4.0,
            additional_total=10.0,
            new_price_per_unit=2.17,
        )

        retrieved = repo.get_shopping_list_item(item.id)
        assert retrieved.purchased_quantity == 12.0

    def test_add_more_purchased_accumulates_total(self, repo, sample_run, sample_product):
        """Test add_more_purchased accumulates total."""
        item = repo.create_shopping_list_item(
            run_id=sample_run.id, product_id=sample_product.id, requested_quantity=20
        )

        repo.mark_item_purchased(
            item_id=item.id, quantity=10, price_per_unit=2.0, total=20.0, purchase_order=1
        )

        repo.add_more_purchased(
            item_id=item.id,
            additional_quantity=5.0,
            additional_total=12.5,
            new_price_per_unit=2.17,
        )

        retrieved = repo.get_shopping_list_item(item.id)
        assert retrieved.purchased_total == Decimal('32.5')

    def test_add_more_purchased_updates_price_per_unit(self, repo, sample_run, sample_product):
        """Test add_more_purchased updates price_per_unit to weighted average."""
        item = repo.create_shopping_list_item(
            run_id=sample_run.id, product_id=sample_product.id, requested_quantity=20
        )

        repo.mark_item_purchased(
            item_id=item.id, quantity=10, price_per_unit=2.0, total=20.0, purchase_order=1
        )

        new_price = 2.5
        repo.add_more_purchased(
            item_id=item.id,
            additional_quantity=10.0,
            additional_total=25.0,
            new_price_per_unit=new_price,
        )

        retrieved = repo.get_shopping_list_item(item.id)
        assert retrieved.purchased_price_per_unit == Decimal('2.5')

    def test_add_more_to_unpurchased_item_returns_none(self, repo, sample_run, sample_product):
        """Test adding more to unpurchased item returns None."""
        item = repo.create_shopping_list_item(
            run_id=sample_run.id, product_id=sample_product.id, requested_quantity=10
        )

        result = repo.add_more_purchased(
            item_id=item.id,
            additional_quantity=5.0,
            additional_total=12.5,
            new_price_per_unit=2.5,
        )

        assert result is None

    def test_add_more_to_nonexistent_item_returns_none(self, repo):
        """Test adding more to non-existent item returns None."""
        fake_id = uuid4()

        result = repo.add_more_purchased(
            item_id=fake_id,
            additional_quantity=5.0,
            additional_total=12.5,
            new_price_per_unit=2.5,
        )

        assert result is None


class TestUnpurchaseItem:
    """Test unpurchase_item() method."""

    def test_unpurchase_purchased_item(self, repo, sample_run, sample_product):
        """Test resetting item to unpurchased state."""
        item = repo.create_shopping_list_item(
            run_id=sample_run.id, product_id=sample_product.id, requested_quantity=10
        )

        # Mark as purchased
        repo.mark_item_purchased(
            item_id=item.id, quantity=10, price_per_unit=2.5, total=25.0, purchase_order=1
        )

        # Unpurchase
        updated_item = repo.unpurchase_item(item.id)

        assert updated_item is not None
        assert updated_item.is_purchased is False
        assert updated_item.purchased_quantity is None
        assert updated_item.purchased_price_per_unit is None
        assert updated_item.purchased_total is None
        assert updated_item.purchase_order is None

    def test_unpurchase_clears_is_purchased_flag(self, repo, sample_run, sample_product):
        """Test unpurchase_item clears is_purchased flag."""
        item = repo.create_shopping_list_item(
            run_id=sample_run.id, product_id=sample_product.id, requested_quantity=10
        )

        repo.mark_item_purchased(
            item_id=item.id, quantity=10, price_per_unit=2.5, total=25.0, purchase_order=1
        )

        repo.unpurchase_item(item.id)

        retrieved = repo.get_shopping_list_item(item.id)
        assert retrieved.is_purchased is False

    def test_unpurchase_clears_all_purchase_fields(self, repo, sample_run, sample_product):
        """Test unpurchase_item clears all purchase fields."""
        item = repo.create_shopping_list_item(
            run_id=sample_run.id, product_id=sample_product.id, requested_quantity=10
        )

        repo.mark_item_purchased(
            item_id=item.id, quantity=10, price_per_unit=2.5, total=25.0, purchase_order=1
        )

        repo.unpurchase_item(item.id)

        retrieved = repo.get_shopping_list_item(item.id)
        assert retrieved.purchased_quantity is None
        assert retrieved.purchased_price_per_unit is None
        assert retrieved.purchased_total is None
        assert retrieved.purchase_order is None

    def test_unpurchase_keeps_requested_quantity(self, repo, sample_run, sample_product):
        """Test unpurchase_item keeps requested_quantity."""
        item = repo.create_shopping_list_item(
            run_id=sample_run.id, product_id=sample_product.id, requested_quantity=15
        )

        repo.mark_item_purchased(
            item_id=item.id, quantity=10, price_per_unit=2.5, total=25.0, purchase_order=1
        )

        repo.unpurchase_item(item.id)

        retrieved = repo.get_shopping_list_item(item.id)
        assert retrieved.requested_quantity == 15

    def test_unpurchase_nonexistent_item_returns_none(self, repo):
        """Test unpurchasing non-existent item returns None."""
        fake_id = uuid4()

        result = repo.unpurchase_item(fake_id)

        assert result is None

    def test_unpurchase_already_unpurchased_item(self, repo, sample_run, sample_product):
        """Test unpurchasing already unpurchased item."""
        item = repo.create_shopping_list_item(
            run_id=sample_run.id, product_id=sample_product.id, requested_quantity=10
        )

        # Item is not purchased, but unpurchase should still work
        updated_item = repo.unpurchase_item(item.id)

        assert updated_item is not None
        assert updated_item.is_purchased is False


class TestUpdateRequestedQuantity:
    """Test update_shopping_list_item_requested_quantity() method."""

    def test_update_requested_quantity(self, repo, sample_run, sample_product):
        """Test updating requested quantity."""
        item = repo.create_shopping_list_item(
            run_id=sample_run.id, product_id=sample_product.id, requested_quantity=10
        )

        repo.update_shopping_list_item_requested_quantity(item.id, 20)

        retrieved = repo.get_shopping_list_item(item.id)
        assert retrieved.requested_quantity == 20

    def test_update_requested_quantity_is_persisted(self, repo, sample_run, sample_product):
        """Test updated requested quantity is persisted."""
        item = repo.create_shopping_list_item(
            run_id=sample_run.id, product_id=sample_product.id, requested_quantity=10
        )

        repo.update_shopping_list_item_requested_quantity(item.id, 15)

        # Retrieve again to verify persistence
        retrieved = repo.get_shopping_list_item(item.id)
        assert retrieved.requested_quantity == 15

    def test_update_requested_quantity_for_nonexistent_item(self, repo):
        """Test updating requested quantity for non-existent item."""
        fake_id = uuid4()

        # Should not raise error, just no-op
        repo.update_shopping_list_item_requested_quantity(fake_id, 10)

    def test_update_requested_quantity_multiple_times(self, repo, sample_run, sample_product):
        """Test updating requested quantity multiple times."""
        item = repo.create_shopping_list_item(
            run_id=sample_run.id, product_id=sample_product.id, requested_quantity=10
        )

        repo.update_shopping_list_item_requested_quantity(item.id, 15)
        retrieved1 = repo.get_shopping_list_item(item.id)
        assert retrieved1.requested_quantity == 15

        repo.update_shopping_list_item_requested_quantity(item.id, 20)
        retrieved2 = repo.get_shopping_list_item(item.id)
        assert retrieved2.requested_quantity == 20


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_very_large_quantities(self, repo, sample_run, sample_product):
        """Test with very large quantities."""
        large_quantity = 10000
        item = repo.create_shopping_list_item(
            run_id=sample_run.id, product_id=sample_product.id, requested_quantity=large_quantity
        )

        assert item.requested_quantity == large_quantity

        repo.mark_item_purchased(
            item_id=item.id,
            quantity=large_quantity,
            price_per_unit=1.0,
            total=float(large_quantity),
            purchase_order=1,
        )

        retrieved = repo.get_shopping_list_item(item.id)
        assert retrieved.purchased_quantity == large_quantity

    def test_price_precision_with_many_decimals(self, repo, sample_run, sample_product):
        """Test price precision with decimal values."""
        item = repo.create_shopping_list_item(
            run_id=sample_run.id, product_id=sample_product.id, requested_quantity=10
        )

        # Use precise decimal values
        price_per_unit = 3.333333
        total = 33.333333

        repo.mark_item_purchased(
            item_id=item.id,
            quantity=10,
            price_per_unit=price_per_unit,
            total=total,
            purchase_order=1,
        )

        retrieved = repo.get_shopping_list_item(item.id)
        # Values should be stored as Decimal
        assert isinstance(retrieved.purchased_price_per_unit, Decimal)
        assert isinstance(retrieved.purchased_total, Decimal)

    def test_zero_prices(self, repo, sample_run, sample_product):
        """Test with zero prices."""
        item = repo.create_shopping_list_item(
            run_id=sample_run.id, product_id=sample_product.id, requested_quantity=10
        )

        repo.mark_item_purchased(
            item_id=item.id, quantity=10, price_per_unit=0.0, total=0.0, purchase_order=1
        )

        retrieved = repo.get_shopping_list_item(item.id)
        assert retrieved.purchased_price_per_unit == Decimal('0.0')
        assert retrieved.purchased_total == Decimal('0.0')

    def test_concurrent_shopping_operations(self, repo, sample_run, sample_products):
        """Test creating multiple items (simulating concurrent operations)."""
        items = []
        for product in sample_products:
            item = repo.create_shopping_list_item(
                run_id=sample_run.id, product_id=product.id, requested_quantity=5
            )
            items.append(item)

        # Verify all items exist
        retrieved_items = repo.get_shopping_list_items(sample_run.id)
        assert len(retrieved_items) == len(sample_products)

        # Verify all IDs are unique
        item_ids = [i.id for i in retrieved_items]
        assert len(item_ids) == len(set(item_ids))

    def test_repository_isolation(self, storage):
        """Test fresh repository instance per test (via fixture)."""
        # This test verifies the fixture works correctly
        assert len(storage.shopping_list_items) == 0


class TestDataIntegrity:
    """Test data integrity and relationships."""

    def test_shopping_list_item_has_expected_fields(self, repo, sample_run, sample_product):
        """Test shopping list item object has expected fields."""
        item = repo.create_shopping_list_item(
            run_id=sample_run.id, product_id=sample_product.id, requested_quantity=10
        )

        assert hasattr(item, 'id')
        assert hasattr(item, 'run_id')
        assert hasattr(item, 'product_id')
        assert hasattr(item, 'requested_quantity')
        assert hasattr(item, 'purchased_quantity')
        assert hasattr(item, 'purchased_price_per_unit')
        assert hasattr(item, 'purchased_total')
        assert hasattr(item, 'is_purchased')
        assert hasattr(item, 'purchase_order')

    def test_multiple_repositories_share_storage(self, storage, sample_run, sample_product):
        """Test multiple repository instances share the same storage."""
        repo1 = MemoryShoppingRepository(storage)
        repo2 = MemoryShoppingRepository(storage)

        item = repo1.create_shopping_list_item(
            run_id=sample_run.id, product_id=sample_product.id, requested_quantity=10
        )

        # Both repositories should see the same item
        assert repo2.get_shopping_list_item(item.id) is not None


class TestComplexScenarios:
    """Test complex scenarios involving multiple operations."""

    def test_full_shopping_lifecycle(self, repo, sample_run, sample_product):
        """Test full shopping lifecycle from creation to purchase."""
        # Create shopping list item
        item = repo.create_shopping_list_item(
            run_id=sample_run.id, product_id=sample_product.id, requested_quantity=20
        )

        assert item.is_purchased is False
        assert item.purchased_quantity is None

        # Update requested quantity
        repo.update_shopping_list_item_requested_quantity(item.id, 25)
        updated_item = repo.get_shopping_list_item(item.id)
        assert updated_item.requested_quantity == 25

        # Mark as purchased
        repo.mark_item_purchased(
            item_id=item.id, quantity=20, price_per_unit=2.5, total=50.0, purchase_order=1
        )
        purchased_item = repo.get_shopping_list_item(item.id)
        assert purchased_item.is_purchased is True
        assert purchased_item.purchased_quantity == 20

        # Add more purchased
        repo.add_more_purchased(
            item_id=item.id,
            additional_quantity=5.0,
            additional_total=15.0,
            new_price_per_unit=2.6,
        )
        final_item = repo.get_shopping_list_item(item.id)
        assert final_item.purchased_quantity == 25.0
        assert final_item.purchased_total == Decimal('65.0')

    def test_purchase_workflow_with_multiple_items(self, repo, sample_run, sample_products):
        """Test purchase workflow with multiple items."""
        # Create shopping list
        items = []
        for i, product in enumerate(sample_products, start=1):
            item = repo.create_shopping_list_item(
                run_id=sample_run.id, product_id=product.id, requested_quantity=i * 5
            )
            items.append(item)

        # Purchase items in order
        for i, item in enumerate(items, start=1):
            repo.mark_item_purchased(
                item_id=item.id,
                quantity=i * 5,
                price_per_unit=2.0 * i,
                total=float(i * 5 * 2.0 * i),
                purchase_order=i,
            )

        # Verify all items are purchased
        all_items = repo.get_shopping_list_items(sample_run.id)
        for item in all_items:
            assert item.is_purchased is True
            assert item.purchase_order is not None

    def test_repurchase_workflow(self, repo, sample_run, sample_product):
        """Test unpurchasing and repurchasing an item."""
        # Create and purchase
        item = repo.create_shopping_list_item(
            run_id=sample_run.id, product_id=sample_product.id, requested_quantity=10
        )

        repo.mark_item_purchased(
            item_id=item.id, quantity=10, price_per_unit=2.5, total=25.0, purchase_order=1
        )

        # Unpurchase
        repo.unpurchase_item(item.id)
        unpurchased = repo.get_shopping_list_item(item.id)
        assert unpurchased.is_purchased is False

        # Repurchase with different values
        repo.mark_item_purchased(
            item_id=item.id, quantity=12, price_per_unit=3.0, total=36.0, purchase_order=2
        )

        repurchased = repo.get_shopping_list_item(item.id)
        assert repurchased.is_purchased is True
        assert repurchased.purchased_quantity == 12
        assert repurchased.purchase_order == 2

    def test_shopping_list_for_multiple_runs(
        self, repo, run_repo, group_repo, sample_user, sample_store, sample_products
    ):
        """Test shopping lists for multiple runs."""
        group = group_repo.create_group('Test Group', sample_user.id)

        # Create multiple runs
        runs = [run_repo.create_run(group.id, sample_store.id, sample_user.id) for _ in range(3)]

        # Create shopping list items for each run
        for run in runs:
            for product in sample_products[:2]:
                repo.create_shopping_list_item(
                    run_id=run.id, product_id=product.id, requested_quantity=10
                )

        # Verify each run has correct items
        for run in runs:
            items = repo.get_shopping_list_items(run.id)
            assert len(items) == 2
