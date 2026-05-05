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
def run_and_product(create_run, create_product):
    run, _ = create_run()
    product = create_product()
    return run, product


class TestCreateShoppingListItem:
    def test_creates_item(self, repo, run_and_product):
        run, product = run_and_product
        item = repo.create_shopping_list_item(run.id, product.id, 5)

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
    def test_returns_items_for_run(self, repo, run_and_product):
        run, product = run_and_product
        repo.create_shopping_list_item(run.id, product.id, 3)
        repo.create_shopping_list_item(run.id, product.id, 7)

        items = repo.get_shopping_list_items(run.id)
        assert len(items) == 2

    def test_returns_empty_list_for_run_with_no_items(self, repo):
        items = repo.get_shopping_list_items(uuid.uuid4())
        assert items == []


class TestGetShoppingListItem:
    def test_returns_item_when_found(self, repo, run_and_product):
        run, product = run_and_product
        created = repo.create_shopping_list_item(run.id, product.id, 2)

        found = repo.get_shopping_list_item(created.id)
        assert found is not None
        assert found.id == created.id

    def test_returns_none_when_not_found(self, repo):
        assert repo.get_shopping_list_item(uuid.uuid4()) is None


class TestMarkItemPurchased:
    def test_marks_item_as_purchased(self, repo, run_and_product):
        run, product = run_and_product
        item = repo.create_shopping_list_item(run.id, product.id, 5)

        result = repo.mark_item_purchased(item.id, 5, 2.50, 12.50, 1)

        assert result is not None
        assert result.is_purchased is True
        assert result.purchased_quantity == 5
        assert result.purchased_price_per_unit == Decimal('2.50')
        assert result.purchased_total == Decimal('12.50')
        assert result.purchase_order == 1

    def test_returns_none_for_nonexistent_item(self, repo):
        result = repo.mark_item_purchased(uuid.uuid4(), 1, 1.0, 1.0, 1)
        assert result is None


class TestUnpurchaseItem:
    def test_resets_item_to_unpurchased(self, repo, run_and_product):
        run, product = run_and_product
        item = repo.create_shopping_list_item(run.id, product.id, 5)
        repo.mark_item_purchased(item.id, 5, 2.50, 12.50, 1)

        result = repo.unpurchase_item(item.id)

        assert result is not None
        assert result.is_purchased is False
        assert result.purchased_quantity is None
        assert result.purchased_price_per_unit is None
        assert result.purchased_total is None
        assert result.purchase_order is None

    def test_returns_none_for_nonexistent_item(self, repo):
        result = repo.unpurchase_item(uuid.uuid4())
        assert result is None


class TestUpdateItemPurchase:
    def test_updates_purchase_values(self, repo, run_and_product):
        run, product = run_and_product
        item = repo.create_shopping_list_item(run.id, product.id, 5)
        repo.mark_item_purchased(item.id, 5, 2.50, 12.50, 1)

        result = repo.update_item_purchase(item.id, 3, 3.00, 9.00)

        assert result is not None
        assert result.purchased_quantity == 3
        assert result.purchased_price_per_unit == Decimal('3.00')
        assert result.purchased_total == Decimal('9.00')
        assert result.is_purchased is True
        assert result.purchase_order == 1  # unchanged

    def test_returns_none_for_unpurchased_item(self, repo, run_and_product):
        run, product = run_and_product
        item = repo.create_shopping_list_item(run.id, product.id, 5)

        result = repo.update_item_purchase(item.id, 3, 3.00, 9.00)
        assert result is None

    def test_returns_none_for_nonexistent_item(self, repo):
        result = repo.update_item_purchase(uuid.uuid4(), 3, 3.00, 9.00)
        assert result is None


class TestAddMorePurchased:
    def test_adds_to_existing_purchase(self, repo, run_and_product):
        run, product = run_and_product
        item = repo.create_shopping_list_item(run.id, product.id, 10)
        repo.mark_item_purchased(item.id, 5, 2.00, 10.00, 1)

        result = repo.add_more_purchased(item.id, 3, 6.00, 2.00)

        assert result is not None
        assert float(result.purchased_quantity) == 8.0
        assert result.purchased_total == Decimal('16.00')
        assert result.purchased_price_per_unit == Decimal('2.00')

    def test_returns_none_for_unpurchased_item(self, repo, run_and_product):
        run, product = run_and_product
        item = repo.create_shopping_list_item(run.id, product.id, 5)

        result = repo.add_more_purchased(item.id, 2, 4.00, 2.00)
        assert result is None

    def test_returns_none_for_nonexistent_item(self, repo):
        result = repo.add_more_purchased(uuid.uuid4(), 2, 4.00, 2.00)
        assert result is None


class TestUpdateShoppingListItemRequestedQuantity:
    def test_updates_requested_quantity(self, repo, run_and_product):
        run, product = run_and_product
        item = repo.create_shopping_list_item(run.id, product.id, 5)

        repo.update_shopping_list_item_requested_quantity(item.id, 10)

        updated = repo.get_shopping_list_item(item.id)
        assert updated.requested_quantity == 10


class TestGetShoppingListItemsByProduct:
    def test_returns_items_across_runs(self, repo, create_run, create_product):
        product = create_product()
        run1, _ = create_run()
        run2, _ = create_run()

        repo.create_shopping_list_item(run1.id, product.id, 3)
        repo.create_shopping_list_item(run2.id, product.id, 7)

        items = repo.get_shopping_list_items_by_product(product.id)
        assert len(items) == 2

    def test_returns_empty_for_unused_product(self, repo):
        items = repo.get_shopping_list_items_by_product(uuid.uuid4())
        assert items == []
