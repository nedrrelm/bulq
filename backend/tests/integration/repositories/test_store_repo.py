"""Integration tests for DatabaseStoreRepository."""

from uuid import uuid4

import pytest

from app.core.models import ProductAvailability, Run
from app.repositories.database.store import DatabaseStoreRepository

pytestmark = pytest.mark.integration


@pytest.fixture
def store_repo(db_session):
    return DatabaseStoreRepository(db_session)


class TestCreateStore:
    async def test_create(self, store_repo):
        store = await store_repo.create_store(name='Costco')
        assert store.id is not None
        assert store.name == 'Costco'


class TestGetStoreById:
    async def test_found(self, store_repo):
        created = await store_repo.create_store(name='Target')
        found = await store_repo.get_store_by_id(created.id)
        assert found is not None
        assert found.id == created.id
        assert found.name == 'Target'

    async def test_not_found(self, store_repo):
        result = await store_repo.get_store_by_id(uuid4())
        assert result is None


class TestGetAllStores:
    async def test_pagination(self, store_repo):
        for i in range(5):
            await store_repo.create_store(name=f'Store {i:02d}')
        page1 = await store_repo.get_all_stores(limit=2, offset=0)
        page2 = await store_repo.get_all_stores(limit=2, offset=2)
        assert len(page1) == 2
        assert len(page2) == 2
        assert page1[0].id != page2[0].id

    async def test_no_limit(self, store_repo):
        await store_repo.create_store(name='Unlimited Store')
        stores = await store_repo.get_all_stores()
        assert len(stores) >= 1


class TestSearchStores:
    async def test_matching(self, store_repo):
        await store_repo.create_store(name='Whole Foods Market')
        await store_repo.create_store(name="Trader Joe's")
        results = await store_repo.search_stores('whole')
        assert len(results) == 1
        assert results[0].name == 'Whole Foods Market'

    async def test_case_insensitive(self, store_repo):
        await store_repo.create_store(name='ALDI')
        results = await store_repo.search_stores('aldi')
        assert len(results) == 1

    async def test_no_match(self, store_repo):
        await store_repo.create_store(name='Kroger')
        results = await store_repo.search_stores('zzzznotfound')
        assert results == []


class TestUpdateStore:
    async def test_update_name(self, store_repo):
        store = await store_repo.create_store(name='Old Name')
        updated = await store_repo.update_store(store.id, name='New Name')
        assert updated.name == 'New Name'

    async def test_update_address(self, store_repo):
        store = await store_repo.create_store(name='MyStore')
        updated = await store_repo.update_store(store.id, address='123 Main St')
        assert updated.address == '123 Main St'
        assert updated.name == 'MyStore'

    async def test_update_chain(self, store_repo):
        store = await store_repo.create_store(name='Local Costco')
        updated = await store_repo.update_store(store.id, chain='Costco')
        assert updated.chain == 'Costco'

    async def test_not_found(self, store_repo):
        result = await store_repo.update_store(uuid4(), name='X')
        assert result is None


class TestDeleteStore:
    async def test_delete_existing(self, store_repo):
        store = await store_repo.create_store(name='ToDelete')
        result = await store_repo.delete_store(store.id)
        assert result is True
        assert await store_repo.get_store_by_id(store.id) is None

    async def test_delete_not_found(self, store_repo):
        result = await store_repo.delete_store(uuid4())
        assert result is False


class TestGetProductsByStoreFromAvailabilities:
    async def test_with_products(self, store_repo, db_session, create_product):
        store = await store_repo.create_store(name='Avail Store')
        p1 = await create_product(name='Product A')
        p2 = await create_product(name='Product B')
        db_session.add(ProductAvailability(product_id=p1.id, store_id=store.id))
        db_session.add(ProductAvailability(product_id=p2.id, store_id=store.id))
        await db_session.flush()

        products = await store_repo.get_products_by_store_from_availabilities(store.id)
        assert len(products) == 2
        product_ids = {p.id for p in products}
        assert p1.id in product_ids
        assert p2.id in product_ids

    async def test_without_products(self, store_repo):
        store = await store_repo.create_store(name='Empty Store')
        products = await store_repo.get_products_by_store_from_availabilities(store.id)
        assert products == []


class TestCountStoreRuns:
    async def test_with_runs(self, store_repo, db_session, create_group):
        store = await store_repo.create_store(name='Run Store')
        group = await create_group()
        db_session.add(Run(group_id=group.id, store_id=store.id, state='planning'))
        db_session.add(Run(group_id=group.id, store_id=store.id, state='active'))
        await db_session.flush()

        count = await store_repo.count_store_runs(store.id)
        assert count == 2

    async def test_no_runs(self, store_repo):
        store = await store_repo.create_store(name='No Runs Store')
        count = await store_repo.count_store_runs(store.id)
        assert count == 0
