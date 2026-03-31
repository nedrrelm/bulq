"""Unit tests for MemoryProductRepository.

Tests cover:
- Product creation (create_product)
- Product retrieval by ID (get_product_by_id)
- Product updates (update_product)
- Product deletion (delete_product)
- List and search products (get_all_products, search_products)
- Product availabilities (create, get, update)
- Store-product relationships (get_products_by_store)
- Bulk update operations
- Edge cases and data integrity
"""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from app.core.models import Store, User
from app.repositories.memory.product import MemoryProductRepository
from app.repositories.memory.storage import MemoryStorage


@pytest.fixture
def storage():
    """Create fresh memory storage for each test."""
    storage = MemoryStorage()
    # Clear all data
    storage.products.clear()
    storage.product_availabilities.clear()
    storage.stores.clear()
    storage.users.clear()
    storage.bids.clear()
    storage.shopping_list_items.clear()
    yield storage
    # Clean up after test
    storage.products.clear()
    storage.product_availabilities.clear()
    storage.stores.clear()
    storage.users.clear()
    storage.bids.clear()
    storage.shopping_list_items.clear()


@pytest.fixture
def repo(storage):
    """Create repository instance with fresh storage."""
    return MemoryProductRepository(storage)


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
def sample_store(storage, sample_user):
    """Create a sample store for testing."""
    store = Store(
        id=uuid4(),
        name='Test Store',
        address='123 Test St',
        chain='TestMart',
        verified=False,
        created_by=sample_user.id,
    )
    storage.stores[store.id] = store
    return store


@pytest.fixture
def sample_product_data():
    """Sample product data for testing."""
    return {
        'name': 'Organic Apples',
        'brand': 'FreshFarms',
        'unit': 'kg',
    }


class TestCreateProduct:
    """Test create_product() method."""

    def test_create_product_with_required_fields(self, repo, sample_product_data):
        """Test creating product with all required fields."""
        product = repo.create_product(**sample_product_data)

        assert product is not None
        assert product.name == sample_product_data['name']
        assert product.brand == sample_product_data['brand']
        assert product.unit == sample_product_data['unit']

    def test_create_product_with_name_only(self, repo):
        """Test creating product with name only."""
        product = repo.create_product(name='Simple Product')

        assert product is not None
        assert product.name == 'Simple Product'
        assert product.brand is None
        assert product.unit is None

    def test_created_product_has_uuid(self, repo, sample_product_data):
        """Test created product has correct ID (UUID)."""
        product = repo.create_product(**sample_product_data)

        assert product.id is not None
        assert isinstance(product.id, UUID)

    def test_created_product_is_stored_and_retrievable(self, repo, sample_product_data):
        """Test created product is stored and retrievable."""
        product = repo.create_product(**sample_product_data)

        retrieved = repo.get_product_by_id(product.id)
        assert retrieved is not None
        assert retrieved.id == product.id
        assert retrieved.name == product.name

    def test_created_product_has_default_values(self, repo, sample_product_data):
        """Test created product has default values (verified=False)."""
        product = repo.create_product(**sample_product_data)

        assert product.verified is False

    def test_created_product_has_timestamps(self, repo, sample_product_data):
        """Test created product has created_at and updated_at timestamps."""
        before = datetime.now(UTC)
        product = repo.create_product(**sample_product_data)
        after = datetime.now(UTC)

        assert product.created_at is not None
        assert product.updated_at is not None
        assert before <= product.created_at <= after
        assert before <= product.updated_at <= after

    def test_creating_multiple_products_different_ids(self, repo):
        """Test creating multiple products generates different IDs."""
        product1 = repo.create_product('Product One', 'Brand A', 'kg')
        product2 = repo.create_product('Product Two', 'Brand B', 'L')

        assert product1.id != product2.id
        assert product1.name != product2.name

    def test_create_product_without_brand(self, repo):
        """Test creating product without brand."""
        product = repo.create_product(name='Generic Product', unit='kg')

        assert product.name == 'Generic Product'
        assert product.brand is None
        assert product.unit == 'kg'


class TestGetProductById:
    """Test get_product_by_id() method."""

    def test_get_existing_product_by_id(self, repo, sample_product_data):
        """Test getting existing product by ID."""
        product = repo.create_product(**sample_product_data)

        retrieved = repo.get_product_by_id(product.id)
        assert retrieved is not None
        assert retrieved.id == product.id
        assert retrieved.name == product.name
        assert retrieved.brand == product.brand

    def test_get_nonexistent_product_returns_none(self, repo):
        """Test getting non-existent product returns None."""
        fake_id = uuid4()

        result = repo.get_product_by_id(fake_id)
        assert result is None

    def test_get_product_by_id_after_creation(self, repo, sample_product_data):
        """Test getting product immediately after creation."""
        product = repo.create_product(**sample_product_data)
        retrieved = repo.get_product_by_id(product.id)

        assert retrieved is not None
        assert retrieved.id == product.id

    def test_get_product_by_id_after_update(self, repo, sample_product_data):
        """Test getting product after update returns updated data."""
        product = repo.create_product(**sample_product_data)
        repo.update_product(product.id, name='Updated Name')

        retrieved = repo.get_product_by_id(product.id)
        assert retrieved.name == 'Updated Name'


class TestUpdateProduct:
    """Test update_product() method."""

    def test_update_product_name(self, repo, sample_product_data):
        """Test updating product name."""
        product = repo.create_product(**sample_product_data)
        new_name = 'Red Apples'

        updated = repo.update_product(product.id, name=new_name)

        assert updated is not None
        assert updated.name == new_name
        assert updated.id == product.id

    def test_update_product_brand(self, repo, sample_product_data):
        """Test updating product brand."""
        product = repo.create_product(**sample_product_data)
        new_brand = 'SuperFresh'

        updated = repo.update_product(product.id, brand=new_brand)

        assert updated.brand == new_brand

    def test_update_product_unit(self, repo, sample_product_data):
        """Test updating product unit."""
        product = repo.create_product(**sample_product_data)
        new_unit = 'lb'

        updated = repo.update_product(product.id, unit=new_unit)

        assert updated.unit == new_unit

    def test_update_product_verified(self, repo, sample_product_data, admin_user):
        """Test updating product verified flag."""
        product = repo.create_product(**sample_product_data)

        updated = repo.update_product(
            product.id,
            verified=True,
            verified_by=admin_user.id,
            verified_at=datetime.now(UTC),
        )

        assert updated.verified is True
        assert updated.verified_by == admin_user.id
        assert updated.verified_at is not None

    def test_update_nonexistent_product_returns_none(self, repo):
        """Test updating non-existent product returns None."""
        fake_id = uuid4()

        result = repo.update_product(fake_id, name='New Name')
        assert result is None

    def test_update_partial_fields(self, repo, sample_product_data):
        """Test partial updates (only some fields)."""
        product = repo.create_product(**sample_product_data)
        original_brand = product.brand

        updated = repo.update_product(product.id, name='New Name')

        assert updated.name == 'New Name'
        assert updated.brand == original_brand  # Unchanged

    def test_update_multiple_fields(self, repo, sample_product_data):
        """Test updating multiple fields at once."""
        product = repo.create_product(**sample_product_data)

        updated = repo.update_product(product.id, name='New Name', brand='New Brand', unit='L')

        assert updated.name == 'New Name'
        assert updated.brand == 'New Brand'
        assert updated.unit == 'L'

    def test_updated_fields_are_persisted(self, repo, sample_product_data):
        """Test updated fields are persisted."""
        product = repo.create_product(**sample_product_data)
        repo.update_product(product.id, name='Updated Name', verified=True)

        # Retrieve again to verify persistence
        retrieved = repo.get_product_by_id(product.id)
        assert retrieved.name == 'Updated Name'
        assert retrieved.verified is True


class TestDeleteProduct:
    """Test delete_product() method."""

    def test_delete_existing_product(self, repo, sample_product_data):
        """Test deleting existing product."""
        product = repo.create_product(**sample_product_data)

        result = repo.delete_product(product.id)

        assert result is True

    def test_product_not_retrievable_after_deletion(self, repo, sample_product_data):
        """Test product not retrievable after deletion."""
        product = repo.create_product(**sample_product_data)
        repo.delete_product(product.id)

        retrieved = repo.get_product_by_id(product.id)
        assert retrieved is None

    def test_delete_nonexistent_product_returns_false(self, repo):
        """Test deleting non-existent product returns False."""
        fake_id = uuid4()

        result = repo.delete_product(fake_id)
        assert result is False

    def test_deleting_twice_returns_false_second_time(self, repo, sample_product_data):
        """Test deleting twice returns False second time."""
        product = repo.create_product(**sample_product_data)

        first_delete = repo.delete_product(product.id)
        second_delete = repo.delete_product(product.id)

        assert first_delete is True
        assert second_delete is False


class TestGetAllProducts:
    """Test get_all_products() method."""

    def test_list_all_with_empty_repository(self, repo):
        """Test list_all with empty repository."""
        products = repo.get_all_products()

        assert products == []
        assert len(products) == 0

    def test_list_all_after_creating_multiple_products(self, repo):
        """Test list_all after creating multiple products."""
        product1 = repo.create_product('Product 1', 'Brand A', 'kg')
        product2 = repo.create_product('Product 2', 'Brand B', 'L')
        product3 = repo.create_product('Product 3', 'Brand C', 'each')

        products = repo.get_all_products()

        assert len(products) == 3
        product_ids = {p.id for p in products}
        assert product1.id in product_ids
        assert product2.id in product_ids
        assert product3.id in product_ids

    def test_list_all_returns_all_products(self, repo):
        """Test list_all returns all products."""
        created_products = []
        for i in range(5):
            product = repo.create_product(f'Product {i}', f'Brand {i}', 'kg')
            created_products.append(product)

        products = repo.get_all_products()

        assert len(products) == 5
        for created in created_products:
            assert any(p.id == created.id for p in products)

    def test_list_all_includes_all_product_fields(self, repo, sample_product_data):
        """Test list_all includes all product fields."""
        product = repo.create_product(**sample_product_data)

        products = repo.get_all_products()

        assert len(products) == 1
        retrieved = products[0]
        assert retrieved.id == product.id
        assert retrieved.name == product.name
        assert retrieved.brand == product.brand
        assert retrieved.unit == product.unit
        assert retrieved.verified == product.verified

    def test_list_all_count_matches_created(self, repo):
        """Test list_all count matches number created."""
        count = 10
        for i in range(count):
            repo.create_product(f'Product {i}', f'Brand {i}', 'kg')

        products = repo.get_all_products()

        assert len(products) == count

    def test_list_all_after_deletion(self, repo):
        """Test list_all after deletion (count decreases)."""
        product1 = repo.create_product('Product 1', 'Brand A', 'kg')
        product2 = repo.create_product('Product 2', 'Brand B', 'L')
        product3 = repo.create_product('Product 3', 'Brand C', 'each')

        assert len(repo.get_all_products()) == 3

        repo.delete_product(product2.id)

        products = repo.get_all_products()
        assert len(products) == 2
        product_ids = {p.id for p in products}
        assert product1.id in product_ids
        assert product2.id not in product_ids
        assert product3.id in product_ids


class TestSearchProducts:
    """Test search_products() method."""

    def test_search_by_name_exact_match(self, repo):
        """Test search by exact name match."""
        product = repo.create_product('Organic Apples', 'FreshFarms', 'kg')
        repo.create_product('Bananas', 'FreshFarms', 'kg')

        results = repo.search_products('Organic Apples')

        assert len(results) == 1
        assert results[0].id == product.id

    def test_search_by_name_partial_match(self, repo):
        """Test search by partial name match."""
        product1 = repo.create_product('Organic Apples', 'FreshFarms', 'kg')
        product2 = repo.create_product('Red Apple Juice', 'FreshFarms', 'L')
        repo.create_product('Bananas', 'FreshFarms', 'kg')

        results = repo.search_products('Apple')

        assert len(results) == 2
        result_ids = {p.id for p in results}
        assert product1.id in result_ids
        assert product2.id in result_ids

    def test_search_case_insensitive(self, repo):
        """Test search is case-insensitive."""
        product = repo.create_product('Organic Apples', 'FreshFarms', 'kg')

        results = repo.search_products('organic apples')

        assert len(results) == 1
        assert results[0].id == product.id

    def test_search_with_no_matches(self, repo):
        """Test search with no matches."""
        repo.create_product('Organic Apples', 'FreshFarms', 'kg')

        results = repo.search_products('Oranges')

        assert results == []

    def test_search_empty_query(self, repo):
        """Test search with empty query returns all products."""
        repo.create_product('Product 1', 'Brand A', 'kg')
        repo.create_product('Product 2', 'Brand B', 'L')

        results = repo.search_products('')

        assert len(results) == 2

    def test_search_in_empty_repository(self, repo):
        """Test search in empty repository."""
        results = repo.search_products('anything')

        assert results == []

    def test_search_by_lowercase(self, repo):
        """Test search with lowercase query matches uppercase product."""
        product = repo.create_product('UPPERCASE PRODUCT', 'Brand', 'kg')

        results = repo.search_products('uppercase')

        assert len(results) == 1
        assert results[0].id == product.id

    def test_search_by_uppercase(self, repo):
        """Test search with uppercase query matches lowercase product."""
        product = repo.create_product('lowercase product', 'Brand', 'kg')

        results = repo.search_products('LOWERCASE')

        assert len(results) == 1
        assert results[0].id == product.id


class TestProductAvailabilities:
    """Test product availability methods."""

    def test_create_product_availability(
        self, repo, sample_product_data, sample_store, sample_user
    ):
        """Test creating product availability."""
        product = repo.create_product(**sample_product_data)

        availability = repo.create_product_availability(
            product_id=product.id,
            store_id=sample_store.id,
            price=5.99,
            notes='Aisle 3',
            minimum_quantity=2,
            user_id=sample_user.id,
        )

        assert availability is not None
        assert availability.product_id == product.id
        assert availability.store_id == sample_store.id
        assert availability.price == Decimal('5.99')
        assert availability.notes == 'Aisle 3'
        assert availability.minimum_quantity == 2
        assert availability.created_by == sample_user.id

    def test_create_product_availability_without_price(
        self, repo, sample_product_data, sample_store
    ):
        """Test creating availability without price."""
        product = repo.create_product(**sample_product_data)

        availability = repo.create_product_availability(
            product_id=product.id,
            store_id=sample_store.id,
        )

        assert availability is not None
        assert availability.price is None
        assert availability.notes == ''

    def test_get_product_availabilities(self, repo, sample_product_data, sample_store, sample_user):
        """Test getting product availabilities."""
        product = repo.create_product(**sample_product_data)

        avail1 = repo.create_product_availability(
            product_id=product.id,
            store_id=sample_store.id,
            price=5.99,
            user_id=sample_user.id,
        )

        availabilities = repo.get_product_availabilities(product.id)

        assert len(availabilities) == 1
        assert availabilities[0].id == avail1.id

    def test_get_product_availabilities_by_store(
        self, repo, sample_product_data, sample_store, storage, sample_user
    ):
        """Test filtering availabilities by store."""
        product = repo.create_product(**sample_product_data)

        # Create another store
        store2 = Store(
            id=uuid4(),
            name='Store 2',
            verified=False,
            created_by=sample_user.id,
        )
        storage.stores[store2.id] = store2

        avail1 = repo.create_product_availability(
            product_id=product.id,
            store_id=sample_store.id,
            price=5.99,
            user_id=sample_user.id,
        )
        repo.create_product_availability(
            product_id=product.id,
            store_id=store2.id,
            price=6.99,
            user_id=sample_user.id,
        )

        # Get availabilities for store1
        availabilities = repo.get_product_availabilities(product.id, sample_store.id)

        assert len(availabilities) == 1
        assert availabilities[0].id == avail1.id

    def test_get_availability_by_product_and_store(
        self, repo, sample_product_data, sample_store, sample_user
    ):
        """Test getting most recent availability by product and store."""
        product = repo.create_product(**sample_product_data)

        repo.create_product_availability(
            product_id=product.id,
            store_id=sample_store.id,
            price=5.99,
            user_id=sample_user.id,
        )

        availability = repo.get_availability_by_product_and_store(product.id, sample_store.id)

        assert availability is not None

    def test_get_availability_by_product_and_store_returns_most_recent(
        self, repo, sample_product_data, sample_store, sample_user
    ):
        """Test getting most recent when multiple availabilities exist."""
        product = repo.create_product(**sample_product_data)

        repo.create_product_availability(
            product_id=product.id,
            store_id=sample_store.id,
            price=5.99,
            user_id=sample_user.id,
        )
        avail2 = repo.create_product_availability(
            product_id=product.id,
            store_id=sample_store.id,
            price=6.99,
            user_id=sample_user.id,
        )

        availability = repo.get_availability_by_product_and_store(product.id, sample_store.id)

        # Should return most recent (avail2)
        assert availability.id == avail2.id

    def test_update_product_availability_price(
        self, repo, sample_product_data, sample_store, sample_user
    ):
        """Test updating product availability price."""
        product = repo.create_product(**sample_product_data)

        availability = repo.create_product_availability(
            product_id=product.id,
            store_id=sample_store.id,
            price=5.99,
            user_id=sample_user.id,
        )

        updated = repo.update_product_availability_price(
            availability.id, price=7.99, notes='Price increased'
        )

        assert updated is not None
        assert updated.price == Decimal('7.99')
        assert updated.notes == 'Price increased'

    def test_update_product_availability_price_without_notes(
        self, repo, sample_product_data, sample_store, sample_user
    ):
        """Test updating price without changing notes."""
        product = repo.create_product(**sample_product_data)

        availability = repo.create_product_availability(
            product_id=product.id,
            store_id=sample_store.id,
            price=5.99,
            notes='Original notes',
            user_id=sample_user.id,
        )

        updated = repo.update_product_availability_price(availability.id, price=7.99)

        assert updated.price == Decimal('7.99')
        assert updated.notes == 'Original notes'  # Unchanged

    def test_get_products_by_store(self, repo, sample_product_data, sample_store, sample_user):
        """Test getting products available at a store."""
        product1 = repo.create_product('Product 1', 'Brand A', 'kg')
        product2 = repo.create_product('Product 2', 'Brand B', 'L')
        product3 = repo.create_product('Product 3', 'Brand C', 'each')

        # Add availability for products 1 and 2 at the store
        repo.create_product_availability(
            product_id=product1.id,
            store_id=sample_store.id,
            price=5.99,
            user_id=sample_user.id,
        )
        repo.create_product_availability(
            product_id=product2.id,
            store_id=sample_store.id,
            price=3.99,
            user_id=sample_user.id,
        )

        products = repo.get_products_by_store(sample_store.id)

        assert len(products) == 2
        product_ids = {p.id for p in products}
        assert product1.id in product_ids
        assert product2.id in product_ids
        assert product3.id not in product_ids

    def test_get_products_by_store_empty(self, repo, sample_store):
        """Test getting products for store with no availabilities."""
        products = repo.get_products_by_store(sample_store.id)

        assert products == []


class TestBulkUpdateOperations:
    """Test bulk update operations."""

    def test_bulk_update_product_bids(self, repo, storage):
        """Test bulk updating product bids."""
        from app.core.models import ProductBid

        old_product = repo.create_product('Old Product', 'Brand', 'kg')
        new_product = repo.create_product('New Product', 'Brand', 'kg')

        # Create product bids for old product
        participation_id = uuid4()
        bid1 = ProductBid(
            id=uuid4(),
            participation_id=participation_id,
            product_id=old_product.id,
            quantity=Decimal('5'),
        )
        bid2 = ProductBid(
            id=uuid4(),
            participation_id=participation_id,
            product_id=old_product.id,
            quantity=Decimal('10'),
        )

        storage.bids[bid1.id] = bid1
        storage.bids[bid2.id] = bid2

        count = repo.bulk_update_product_bids(old_product.id, new_product.id)

        assert count == 2
        assert storage.bids[bid1.id].product_id == new_product.id
        assert storage.bids[bid2.id].product_id == new_product.id

    def test_bulk_update_product_bids_no_matches(self, repo):
        """Test bulk update with no matching bids."""
        product1 = repo.create_product('Product 1', 'Brand', 'kg')
        product2 = repo.create_product('Product 2', 'Brand', 'kg')

        count = repo.bulk_update_product_bids(product1.id, product2.id)

        assert count == 0

    def test_bulk_update_product_availabilities(self, repo, sample_store, sample_user):
        """Test bulk updating product availabilities."""
        old_product = repo.create_product('Old Product', 'Brand', 'kg')
        new_product = repo.create_product('New Product', 'Brand', 'kg')

        # Create availabilities for old product
        avail1 = repo.create_product_availability(
            product_id=old_product.id,
            store_id=sample_store.id,
            price=5.99,
            user_id=sample_user.id,
        )

        count = repo.bulk_update_product_availabilities(old_product.id, new_product.id)

        assert count == 1
        updated_avail = repo.get_product_availabilities(new_product.id)
        assert len(updated_avail) == 1
        assert updated_avail[0].id == avail1.id

    def test_bulk_update_shopping_list_items(self, repo, storage):
        """Test bulk updating shopping list items."""
        from app.core.models import ShoppingListItem

        old_product = repo.create_product('Old Product', 'Brand', 'kg')
        new_product = repo.create_product('New Product', 'Brand', 'kg')

        # Create shopping list items for old product
        run_id = uuid4()
        item1 = ShoppingListItem(
            id=uuid4(),
            run_id=run_id,
            product_id=old_product.id,
            requested_quantity=Decimal('5'),
        )
        item2 = ShoppingListItem(
            id=uuid4(),
            run_id=run_id,
            product_id=old_product.id,
            requested_quantity=Decimal('10'),
        )

        storage.shopping_list_items[item1.id] = item1
        storage.shopping_list_items[item2.id] = item2

        count = repo.bulk_update_shopping_list_items(old_product.id, new_product.id)

        assert count == 2
        assert storage.shopping_list_items[item1.id].product_id == new_product.id
        assert storage.shopping_list_items[item2.id].product_id == new_product.id

    def test_count_product_bids(self, repo, storage):
        """Test counting product bids."""
        from app.core.models import ProductBid

        product = repo.create_product('Product', 'Brand', 'kg')

        # Create bids for product
        participation_id = uuid4()
        bid1 = ProductBid(
            id=uuid4(),
            participation_id=participation_id,
            product_id=product.id,
            quantity=Decimal('5'),
        )
        bid2 = ProductBid(
            id=uuid4(),
            participation_id=participation_id,
            product_id=product.id,
            quantity=Decimal('10'),
        )

        storage.bids[bid1.id] = bid1
        storage.bids[bid2.id] = bid2

        count = repo.count_product_bids(product.id)

        assert count == 2


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_very_long_product_name(self, repo):
        """Test with very long product name."""
        long_name = 'a' * 1000
        product = repo.create_product(long_name, 'Brand', 'kg')

        retrieved = repo.get_product_by_id(product.id)
        assert retrieved is not None
        assert retrieved.name == long_name

    def test_special_characters_in_name(self, repo):
        """Test with special characters in product name."""
        special_name = "Farmer's Choice (Organic) - Grade A+"
        product = repo.create_product(special_name, 'Brand', 'kg')

        assert product.name == special_name
        retrieved = repo.get_product_by_id(product.id)
        assert retrieved.name == special_name

    def test_unicode_characters(self, repo):
        """Test with unicode characters."""
        unicode_name = '有机苹果'
        unicode_brand = '新鲜农场'
        product = repo.create_product(unicode_name, unicode_brand, 'kg')

        assert product.name == unicode_name
        assert product.brand == unicode_brand
        retrieved = repo.get_product_by_id(product.id)
        assert retrieved is not None

    def test_concurrent_operations(self, repo):
        """Test creating multiple products (simulating concurrent operations)."""
        products = []
        for i in range(100):
            product = repo.create_product(f'Product {i}', f'Brand {i}', 'kg')
            products.append(product)

        # Verify all products exist
        all_products = repo.get_all_products()
        assert len(all_products) == 100

        # Verify all IDs are unique
        ids = [p.id for p in all_products]
        assert len(ids) == len(set(ids))

    def test_repository_isolation(self, storage):
        """Test fresh repository instance per test (via fixture)."""
        # This test verifies the fixture works correctly
        assert len(storage.products) == 0
        assert len(storage.product_availabilities) == 0

    def test_search_with_special_characters(self, repo):
        """Test search with special characters."""
        product = repo.create_product("O'Brien's Apples (Organic)", 'Brand', 'kg')

        results = repo.search_products("O'Brien")

        assert len(results) == 1
        assert results[0].id == product.id

    def test_product_availability_with_zero_price(
        self, repo, sample_product_data, sample_store, sample_user
    ):
        """Test creating availability with zero price."""
        product = repo.create_product(**sample_product_data)

        availability = repo.create_product_availability(
            product_id=product.id,
            store_id=sample_store.id,
            price=0.0,
            user_id=sample_user.id,
        )

        assert availability.price == Decimal('0.0')


class TestDataIntegrity:
    """Test data integrity and isolation."""

    def test_product_object_has_expected_fields(self, repo, sample_product_data):
        """Test product object has all expected fields."""
        product = repo.create_product(**sample_product_data)

        assert hasattr(product, 'id')
        assert hasattr(product, 'name')
        assert hasattr(product, 'brand')
        assert hasattr(product, 'unit')
        assert hasattr(product, 'verified')
        assert hasattr(product, 'created_at')
        assert hasattr(product, 'updated_at')

    def test_product_object_is_not_none(self, repo, sample_product_data):
        """Test product object is not None."""
        product = repo.create_product(**sample_product_data)

        assert product is not None
        retrieved = repo.get_product_by_id(product.id)
        assert retrieved is not None

    def test_multiple_repositories_share_storage(self, storage):
        """Test multiple repository instances share the same storage."""
        repo1 = MemoryProductRepository(storage)
        repo2 = MemoryProductRepository(storage)

        product = repo1.create_product('Product', 'Brand', 'kg')

        # Both repositories should see the same product
        assert repo2.get_product_by_id(product.id) is not None
        assert len(repo2.get_all_products()) == 1
