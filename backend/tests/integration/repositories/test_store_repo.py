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
    def test_create(self, store_repo):
        store = store_repo.create_store(name='Costco')
        assert store.id is not None
        assert store.name == 'Costco'


class TestGetStoreById:
    def test_found(self, store_repo):
        created = store_repo.create_store(name='Target')
        found = store_repo.get_store_by_id(created.id)
        assert found is not None
        assert found.id == created.id
        assert found.name == 'Target'

    def test_not_found(self, store_repo):
        result = store_repo.get_store_by_id(uuid4())
        assert result is None


class TestGetAllStores:
    def test_pagination(self, store_repo):
        for i in range(5):
            store_repo.create_store(name=f'Store {i:02d}')
        page1 = store_repo.get_all_stores(limit=2, offset=0)
        page2 = store_repo.get_all_stores(limit=2, offset=2)
        assert len(page1) == 2
        assert len(page2) == 2
        assert page1[0].id != page2[0].id

    def test_no_limit(self, store_repo):
        store_repo.create_store(name='Unlimited Store')
        stores = store_repo.get_all_stores()
        assert len(stores) >= 1


class TestSearchStores:
    def test_matching(self, store_repo):
        store_repo.create_store(name='Whole Foods Market')
        store_repo.create_store(name="Trader Joe's")
        results = store_repo.search_stores('whole')
        assert len(results) == 1
        assert results[0].name == 'Whole Foods Market'

    def test_case_insensitive(self, store_repo):
        store_repo.create_store(name='ALDI')
        results = store_repo.search_stores('aldi')
        assert len(results) == 1

    def test_no_match(self, store_repo):
        store_repo.create_store(name='Kroger')
        results = store_repo.search_stores('zzzznotfound')
        assert results == []


class TestUpdateStore:
    def test_update_name(self, store_repo):
        store = store_repo.create_store(name='Old Name')
        updated = store_repo.update_store(store.id, name='New Name')
        assert updated.name == 'New Name'

    def test_update_address(self, store_repo):
        store = store_repo.create_store(name='MyStore')
        updated = store_repo.update_store(store.id, address='123 Main St')
        assert updated.address == '123 Main St'
        assert updated.name == 'MyStore'

    def test_update_chain(self, store_repo):
        store = store_repo.create_store(name='Local Costco')
        updated = store_repo.update_store(store.id, chain='Costco')
        assert updated.chain == 'Costco'

    def test_not_found(self, store_repo):
        result = store_repo.update_store(uuid4(), name='X')
        assert result is None


class TestDeleteStore:
    def test_delete_existing(self, store_repo):
        store = store_repo.create_store(name='ToDelete')
        result = store_repo.delete_store(store.id)
        assert result is True
        assert store_repo.get_store_by_id(store.id) is None

    def test_delete_not_found(self, store_repo):
        result = store_repo.delete_store(uuid4())
        assert result is False


class TestGetProductsByStoreFromAvailabilities:
    def test_with_products(self, store_repo, db_session, create_product):
        store = store_repo.create_store(name='Avail Store')
        p1 = create_product(name='Product A')
        p2 = create_product(name='Product B')
        db_session.add(ProductAvailability(product_id=p1.id, store_id=store.id))
        db_session.add(ProductAvailability(product_id=p2.id, store_id=store.id))
        db_session.flush()

        products = store_repo.get_products_by_store_from_availabilities(store.id)
        assert len(products) == 2
        product_ids = {p.id for p in products}
        assert p1.id in product_ids
        assert p2.id in product_ids

    def test_without_products(self, store_repo):
        store = store_repo.create_store(name='Empty Store')
        products = store_repo.get_products_by_store_from_availabilities(store.id)
        assert products == []


class TestCountStoreRuns:
    def test_with_runs(self, store_repo, db_session, create_group):
        store = store_repo.create_store(name='Run Store')
        group = create_group()
        db_session.add(Run(group_id=group.id, store_id=store.id, state='planning'))
        db_session.add(Run(group_id=group.id, store_id=store.id, state='active'))
        db_session.flush()

        count = store_repo.count_store_runs(store.id)
        assert count == 2

    def test_no_runs(self, store_repo):
        store = store_repo.create_store(name='No Runs Store')
        count = store_repo.count_store_runs(store.id)
        assert count == 0
