"""Integration tests for DatabaseShoppingRepository."""

import uuid
from decimal import Decimal

import pytest

from app.repositories.database.shopping import DatabaseShoppingRepository

pytestmark = pytest.mark.integration


@pytest.fixture
def repo(db_session):
    return DatabaseShoppingRepository(db=db_session)


@pytest.fixture
async def run_and_product(create_run, create_product):
    run, _ = await create_run()
    product = await create_product()
    return run, product


class TestCreateShoppingListItem:
    async def test_creates_item(self, repo, run_and_product):
        run, product = run_and_product
        item = await repo.create_shopping_list_item(run.id, product.id, 5)

        assert item.id is not None
        assert item.run_id == run.id
        assert item.product_id == product.id
        assert item.requested_quantity == 5
        assert item.is_purchased is False
        assert item.purchased_quantity is None
        assert item.purchased_price_per_unit is None
        assert item.purchased_total is None
        assert item.purchase_order is None


class TestGetShoppingListItems:
    async def test_returns_items_for_run(self, repo, run_and_product):
        run, product = run_and_product
        await repo.create_shopping_list_item(run.id, product.id, 3)
        await repo.create_shopping_list_item(run.id, product.id, 7)

        items = await repo.get_shopping_list_items(run.id)
        assert len(items) == 2

    async def test_returns_empty_list_for_run_with_no_items(self, repo):
        items = await repo.get_shopping_list_items(uuid.uuid4())
        assert items == []


class TestGetShoppingListItem:
    async def test_returns_item_when_found(self, repo, run_and_product):
        run, product = run_and_product
        created = await repo.create_shopping_list_item(run.id, product.id, 2)

        found = await repo.get_shopping_list_item(created.id)
        assert found is not None
        assert found.id == created.id

    async def test_returns_none_when_not_found(self, repo):
        assert await repo.get_shopping_list_item(uuid.uuid4()) is None


class TestMarkItemPurchased:
    async def test_marks_item_as_purchased(self, repo, run_and_product):
        run, product = run_and_product
        item = await repo.create_shopping_list_item(run.id, product.id, 5)

        result = await repo.mark_item_purchased(item.id, 5, 2.50, 12.50, 1)

        assert result is not None
        assert result.is_purchased is True
        assert result.purchased_quantity == 5
        assert result.purchased_price_per_unit == Decimal('2.50')
        assert result.purchased_total == Decimal('12.50')
        assert result.purchase_order == 1

    async def test_returns_none_for_nonexistent_item(self, repo):
        result = await repo.mark_item_purchased(uuid.uuid4(), 1, 1.0, 1.0, 1)
        assert result is None


class TestUnpurchaseItem:
    async def test_resets_item_to_unpurchased(self, repo, run_and_product):
        run, product = run_and_product
        item = await repo.create_shopping_list_item(run.id, product.id, 5)
        await repo.mark_item_purchased(item.id, 5, 2.50, 12.50, 1)

        result = await repo.unpurchase_item(item.id)

        assert result is not None
        assert result.is_purchased is False
        assert result.purchased_quantity is None
        assert result.purchased_price_per_unit is None
        assert result.purchased_total is None
        assert result.purchase_order is None

    async def test_returns_none_for_nonexistent_item(self, repo):
        result = await repo.unpurchase_item(uuid.uuid4())
        assert result is None


class TestUpdateItemPurchase:
    async def test_updates_purchase_values(self, repo, run_and_product):
        run, product = run_and_product
        item = await repo.create_shopping_list_item(run.id, product.id, 5)
        await repo.mark_item_purchased(item.id, 5, 2.50, 12.50, 1)

        result = await repo.update_item_purchase(item.id, 3, 3.00, 9.00)

        assert result is not None
        assert result.purchased_quantity == 3
        assert result.purchased_price_per_unit == Decimal('3.00')
        assert result.purchased_total == Decimal('9.00')
        assert result.is_purchased is True
        assert result.purchase_order == 1  # unchanged

    async def test_returns_none_for_unpurchased_item(self, repo, run_and_product):
        run, product = run_and_product
        item = await repo.create_shopping_list_item(run.id, product.id, 5)

        result = await repo.update_item_purchase(item.id, 3, 3.00, 9.00)
        assert result is None

    async def test_returns_none_for_nonexistent_item(self, repo):
        result = await repo.update_item_purchase(uuid.uuid4(), 3, 3.00, 9.00)
        assert result is None


class TestAddMorePurchased:
    async def test_adds_to_existing_purchase(self, repo, run_and_product):
        run, product = run_and_product
        item = await repo.create_shopping_list_item(run.id, product.id, 10)
        await repo.mark_item_purchased(item.id, 5, 2.00, 10.00, 1)

        result = await repo.add_more_purchased(item.id, 3, 6.00, 2.00)

        assert result is not None
        assert float(result.purchased_quantity) == 8.0
        assert result.purchased_total == Decimal('16.00')
        assert result.purchased_price_per_unit == Decimal('2.00')

    async def test_returns_none_for_unpurchased_item(self, repo, run_and_product):
        run, product = run_and_product
        item = await repo.create_shopping_list_item(run.id, product.id, 5)

        result = await repo.add_more_purchased(item.id, 2, 4.00, 2.00)
        assert result is None

    async def test_returns_none_for_nonexistent_item(self, repo):
        result = await repo.add_more_purchased(uuid.uuid4(), 2, 4.00, 2.00)
        assert result is None


class TestUpdateShoppingListItemRequestedQuantity:
    async def test_updates_requested_quantity(self, repo, run_and_product):
        run, product = run_and_product
        item = await repo.create_shopping_list_item(run.id, product.id, 5)

        await repo.update_shopping_list_item_requested_quantity(item.id, 10)

        updated = await repo.get_shopping_list_item(item.id)
        assert updated.requested_quantity == 10


class TestGetShoppingListItemsByProduct:
    async def test_returns_items_across_runs(self, repo, create_run, create_product):
        product = await create_product()
        run1, _ = await create_run()
        run2, _ = await create_run()

        await repo.create_shopping_list_item(run1.id, product.id, 3)
        await repo.create_shopping_list_item(run2.id, product.id, 7)

        items = await repo.get_shopping_list_items_by_product(product.id)
        assert len(items) == 2

    async def test_returns_empty_for_unused_product(self, repo):
        items = await repo.get_shopping_list_items_by_product(uuid.uuid4())
        assert items == []
