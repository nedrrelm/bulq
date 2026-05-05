"""Integration tests for DatabaseProductRepository."""

from decimal import Decimal
from uuid import uuid4

import pytest

from app.repositories.database.product import DatabaseProductRepository

pytestmark = pytest.mark.integration


@pytest.fixture
def product_repo(db_session):
    return DatabaseProductRepository(db_session)


@pytest.fixture
async def store(create_store):
    return await create_store()


@pytest.fixture
async def user(create_user):
    return await create_user()


class TestCreateProduct:
    async def test_with_all_fields(self, product_repo):
        product = await product_repo.create_product(name='Olive Oil', brand='Kirkland', unit='L')
        assert product.id is not None
        assert product.name == 'Olive Oil'
        assert product.brand == 'Kirkland'
        assert product.unit == 'L'

    async def test_with_name_only(self, product_repo):
        product = await product_repo.create_product(name='Bananas')
        assert product.id is not None
        assert product.name == 'Bananas'
        assert product.brand is None
        assert product.unit is None

    async def test_with_partial_optional_fields(self, product_repo):
        product = await product_repo.create_product(name='Rice', unit='kg')
        assert product.brand is None
        assert product.unit == 'kg'


class TestGetProductById:
    async def test_found(self, product_repo):
        created = await product_repo.create_product(name='Milk')
        found = await product_repo.get_product_by_id(created.id)
        assert found is not None
        assert found.id == created.id
        assert found.name == 'Milk'

    async def test_not_found(self, product_repo):
        result = await product_repo.get_product_by_id(uuid4())
        assert result is None


class TestGetAllProducts:
    async def test_returns_all(self, product_repo):
        await product_repo.create_product(name='A')
        await product_repo.create_product(name='B')
        await product_repo.create_product(name='C')
        products = await product_repo.get_all_products()
        assert len(products) >= 3

    async def test_empty(self, product_repo):
        products = await product_repo.get_all_products()
        # May or may not be empty depending on other fixtures, but should not raise
        assert isinstance(products, list)


class TestSearchProducts:
    async def test_matching(self, product_repo):
        await product_repo.create_product(name='Organic Apples')
        await product_repo.create_product(name='Regular Apples')
        await product_repo.create_product(name='Oranges')
        results = await product_repo.search_products('apple')
        assert len(results) == 2

    async def test_no_match(self, product_repo):
        await product_repo.create_product(name='Bananas')
        results = await product_repo.search_products('zzzznotfound')
        assert results == []

    async def test_pagination(self, product_repo):
        for i in range(5):
            await product_repo.create_product(name=f'TestItem{i}')
        page1 = await product_repo.search_products('TestItem', limit=2, offset=0)
        page2 = await product_repo.search_products('TestItem', limit=2, offset=2)
        assert len(page1) == 2
        assert len(page2) == 2
        assert page1[0].id != page2[0].id


class TestUpdateProduct:
    async def test_update_fields(self, product_repo):
        product = await product_repo.create_product(name='Old Name', brand='OldBrand', unit='kg')
        updated = await product_repo.update_product(product.id, name='New Name', brand='NewBrand')
        assert updated.name == 'New Name'
        assert updated.brand == 'NewBrand'
        assert updated.unit == 'kg'  # unchanged

    async def test_not_found(self, product_repo):
        result = await product_repo.update_product(uuid4(), name='X')
        assert result is None


class TestDeleteProduct:
    async def test_delete_existing(self, product_repo):
        product = await product_repo.create_product(name='ToDelete')
        result = await product_repo.delete_product(product.id)
        assert result is True
        assert await product_repo.get_product_by_id(product.id) is None

    async def test_delete_not_found(self, product_repo):
        result = await product_repo.delete_product(uuid4())
        assert result is False


class TestGetProductAvailabilities:
    async def test_with_availabilities(self, product_repo, store, user):
        product = await product_repo.create_product(name='Cheese')
        await product_repo.create_product_availability(
            product_id=product.id,
            store_id=store.id,
            price=5.99,
            user_id=user.id,
        )
        avails = await product_repo.get_product_availabilities(product.id)
        assert len(avails) == 1
        assert avails[0].product_id == product.id

    async def test_with_store_filter(self, product_repo, store, user, create_store):
        product = await product_repo.create_product(name='Bread')
        store2 = await create_store(name='Second Store')
        await product_repo.create_product_availability(
            product_id=product.id, store_id=store.id, price=3.0, user_id=user.id
        )
        await product_repo.create_product_availability(
            product_id=product.id, store_id=store2.id, price=4.0, user_id=user.id
        )
        filtered = await product_repo.get_product_availabilities(product.id, store_id=store.id)
        assert len(filtered) == 1
        assert filtered[0].store_id == store.id

    async def test_no_availabilities(self, product_repo):
        product = await product_repo.create_product(name='NoAvail')
        avails = await product_repo.get_product_availabilities(product.id)
        assert avails == []


class TestCreateProductAvailability:
    async def test_create_with_all_fields(self, product_repo, store, user):
        product = await product_repo.create_product(name='Eggs')
        avail = await product_repo.create_product_availability(
            product_id=product.id,
            store_id=store.id,
            price=4.50,
            minimum_quantity=2,
            notes='Aisle 3',
            user_id=user.id,
        )
        assert avail.id is not None
        assert avail.price == Decimal('4.50')
        assert avail.minimum_quantity == 2
        assert avail.notes == 'Aisle 3'
        assert avail.created_by == user.id

    async def test_create_without_price(self, product_repo, store, user):
        product = await product_repo.create_product(name='Butter')
        avail = await product_repo.create_product_availability(
            product_id=product.id,
            store_id=store.id,
            user_id=user.id,
        )
        assert avail.price is None


class TestGetAvailabilityByProductAndStore:
    async def test_found(self, product_repo, store, user):
        product = await product_repo.create_product(name='Yogurt')
        await product_repo.create_product_availability(
            product_id=product.id, store_id=store.id, price=2.99, user_id=user.id
        )
        result = await product_repo.get_availability_by_product_and_store(product.id, store.id)
        assert result is not None
        assert result.product_id == product.id
        assert result.store_id == store.id

    async def test_not_found(self, product_repo, store):
        result = await product_repo.get_availability_by_product_and_store(uuid4(), store.id)
        assert result is None


class TestUpdateProductAvailabilityPrice:
    async def test_update_price(self, product_repo, store, user):
        product = await product_repo.create_product(name='Coffee')
        avail = await product_repo.create_product_availability(
            product_id=product.id, store_id=store.id, price=9.99, user_id=user.id
        )
        updated = await product_repo.update_product_availability_price(
            availability_id=avail.id, price=11.99, notes='Price went up'
        )
        assert updated.price == Decimal('11.99')
        assert updated.notes == 'Price went up'

    async def test_update_price_without_notes(self, product_repo, store, user):
        product = await product_repo.create_product(name='Tea')
        avail = await product_repo.create_product_availability(
            product_id=product.id, store_id=store.id, price=5.0, notes='Original', user_id=user.id
        )
        updated = await product_repo.update_product_availability_price(
            availability_id=avail.id, price=6.0
        )
        assert updated.price == Decimal('6.00')
        # Notes should remain unchanged when empty string passed
        assert updated.notes == 'Original'
