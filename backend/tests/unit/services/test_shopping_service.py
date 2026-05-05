"""Unit tests for ShoppingService."""

from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest

from app.core.error_codes import (
    INVALID_UUID_FORMAT,
    NOT_RUN_LEADER,
    NOT_RUN_LEADER_OR_HELPER,
    RUN_NOT_FOUND,
    RUN_NOT_IN_SHOPPING_STATE,
    SHOPPING_ITEM_NOT_PURCHASED,
)
from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.core.models import Product, Run, RunParticipation, ShoppingListItem
from app.core.run_state import RunState
from app.services.shopping_service import ShoppingService


class TestGetShoppingList:
    """Test cases for ShoppingService.get_shopping_list()."""

    async def test_get_shopping_list_success(self, test_user):
        """Test successfully getting shopping list."""
        # Arrange
        mock_db = AsyncMock()
        run_id = uuid4()
        product_id = uuid4()
        item_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.SHOPPING
        mock_run.store_id = uuid4()

        mock_product = Mock(spec=Product)
        mock_product.id = product_id
        mock_product.name = 'Apple'
        mock_product.unit = 'kg'

        mock_item = Mock(spec=ShoppingListItem)
        mock_item.id = item_id
        mock_item.product_id = product_id
        mock_item.requested_quantity = 5
        mock_item.is_purchased = False
        mock_item.purchased_quantity = None
        mock_item.purchased_price_per_unit = None
        mock_item.purchased_total = None
        mock_item.purchase_order = None

        service = ShoppingService(mock_db)
        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service._verify_run_access = AsyncMock()
        service.shopping_repo.get_shopping_list_items = AsyncMock(return_value=[mock_item])
        service.product_repo.get_product_by_id = AsyncMock(return_value=mock_product)
        service.product_repo.get_product_availabilities = AsyncMock(return_value=[])

        # Act
        result = await service.get_shopping_list(str(run_id), test_user)

        # Assert
        assert len(result) == 1
        assert result[0].product_name == 'Apple'
        assert result[0].requested_quantity == 5
        assert result[0].is_purchased is False

    async def test_get_shopping_list_invalid_run_id(self, test_user):
        """Test getting shopping list with invalid run ID."""
        # Arrange
        mock_db = AsyncMock()
        service = ShoppingService(mock_db)

        # Act & Assert
        with pytest.raises(BadRequestError) as exc_info:
            await service.get_shopping_list('invalid-uuid', test_user)

        assert exc_info.value.code == INVALID_UUID_FORMAT

    async def test_get_shopping_list_run_not_found(self, test_user):
        """Test getting shopping list for non-existent run."""
        # Arrange
        mock_db = AsyncMock()
        run_id = uuid4()

        service = ShoppingService(mock_db)
        service.run_repo.get_run_by_id = AsyncMock(return_value=None)

        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.get_shopping_list(str(run_id), test_user)

        assert exc_info.value.code == RUN_NOT_FOUND


class TestMarkPurchased:
    """Test cases for ShoppingService.mark_purchased()."""

    async def test_mark_purchased_success(self, test_user):
        """Test successfully marking item as purchased."""
        # Arrange
        mock_db = AsyncMock()
        run_id = uuid4()
        item_id = uuid4()
        product_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.store_id = uuid4()

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.is_leader = True
        mock_participation.is_helper = False

        mock_item = Mock(spec=ShoppingListItem)
        mock_item.id = item_id
        mock_item.product_id = product_id

        service = ShoppingService(mock_db)
        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(return_value=mock_participation)
        service.shopping_repo.get_shopping_list_items = AsyncMock(return_value=[])
        service.shopping_repo.mark_item_purchased = AsyncMock(return_value=mock_item)
        service._update_product_availability_if_needed = AsyncMock()

        with patch('app.services.shopping_service.event_bus'):
            # Act
            result = await service.mark_purchased(
                str(run_id), str(item_id), 5.0, 1.99, 9.95, test_user
            )

            # Assert
            assert result.purchase_order == 1

    async def test_mark_purchased_not_leader_or_helper(self, test_user):
        """Test marking purchased when user is not leader or helper."""
        # Arrange
        mock_db = AsyncMock()
        run_id = uuid4()
        item_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.is_leader = False
        mock_participation.is_helper = False

        service = ShoppingService(mock_db)
        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(return_value=mock_participation)

        # Act & Assert
        with pytest.raises(ForbiddenError) as exc_info:
            await service.mark_purchased(str(run_id), str(item_id), 5.0, 1.99, 9.95, test_user)

        assert exc_info.value.code == NOT_RUN_LEADER_OR_HELPER


class TestAddMorePurchased:
    """Test cases for ShoppingService.add_more_purchased()."""

    async def test_add_more_purchased_success(self, test_user):
        """Test successfully adding more purchased quantity."""
        # Arrange
        mock_db = AsyncMock()
        run_id = uuid4()
        item_id = uuid4()
        product_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.store_id = uuid4()

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.is_leader = True
        mock_participation.is_helper = False

        mock_item = Mock(spec=ShoppingListItem)
        mock_item.id = item_id
        mock_item.product_id = product_id
        mock_item.is_purchased = True
        mock_item.purchased_quantity = 5.0
        mock_item.purchased_total = 10.0

        service = ShoppingService(mock_db)
        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(return_value=mock_participation)
        service.shopping_repo.get_shopping_list_item = AsyncMock(return_value=mock_item)
        service.shopping_repo.add_more_purchased = AsyncMock(return_value=mock_item)
        service._update_product_availability_if_needed = AsyncMock()

        with patch('app.services.shopping_service.event_bus'):
            # Act
            result = await service.add_more_purchased(
                str(run_id), str(item_id), 2.0, 1.99, 3.98, test_user
            )

            # Assert
            assert result is not None

    async def test_add_more_purchased_item_not_purchased(self, test_user):
        """Test adding more when item is not yet purchased."""
        # Arrange
        mock_db = AsyncMock()
        run_id = uuid4()
        item_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.is_leader = True
        mock_participation.is_helper = False

        mock_item = Mock(spec=ShoppingListItem)
        mock_item.is_purchased = False

        service = ShoppingService(mock_db)
        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(return_value=mock_participation)
        service.shopping_repo.get_shopping_list_item = AsyncMock(return_value=mock_item)

        # Act & Assert
        with pytest.raises(BadRequestError) as exc_info:
            await service.add_more_purchased(str(run_id), str(item_id), 2.0, 1.99, 3.98, test_user)

        assert exc_info.value.code == SHOPPING_ITEM_NOT_PURCHASED


class TestUnpurchaseItem:
    """Test cases for ShoppingService.unpurchase_item()."""

    async def test_unpurchase_item_success(self, test_user):
        """Test successfully unpurchasing an item."""
        # Arrange
        mock_db = AsyncMock()
        run_id = uuid4()
        item_id = uuid4()
        product_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.is_leader = True
        mock_participation.is_helper = False

        mock_item = Mock(spec=ShoppingListItem)
        mock_item.id = item_id
        mock_item.product_id = product_id

        service = ShoppingService(mock_db)
        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(return_value=mock_participation)
        service.shopping_repo.get_shopping_list_item = AsyncMock(return_value=mock_item)
        service.shopping_repo.unpurchase_item = AsyncMock(return_value=mock_item)

        with patch('app.services.shopping_service.event_bus'):
            # Act
            result = await service.unpurchase_item(str(run_id), str(item_id), test_user)

            # Assert
            assert result is not None


class TestCompleteShoppingAssertions:
    """Test essential assertions for ShoppingService.complete_shopping()."""

    async def test_complete_shopping_not_leader(self, test_user):
        """Test completing shopping when user is not leader."""
        # Arrange
        mock_db = AsyncMock()
        run_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.SHOPPING

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.is_leader = False

        service = ShoppingService(mock_db)
        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(return_value=mock_participation)

        # Act & Assert
        with pytest.raises(ForbiddenError) as exc_info:
            await service.complete_shopping(str(run_id), test_user)

        assert exc_info.value.code == NOT_RUN_LEADER

    async def test_complete_shopping_wrong_state(self, test_user):
        """Test completing shopping from wrong state."""
        # Arrange
        mock_db = AsyncMock()
        run_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.ACTIVE

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.is_leader = True

        service = ShoppingService(mock_db)
        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(return_value=mock_participation)

        # Act & Assert
        with pytest.raises(BadRequestError) as exc_info:
            await service.complete_shopping(str(run_id), test_user)

        assert exc_info.value.code == RUN_NOT_IN_SHOPPING_STATE
