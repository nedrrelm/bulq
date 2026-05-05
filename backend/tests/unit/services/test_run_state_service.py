"""Unit tests for RunStateService."""

from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest

from app.core.error_codes import (
    BID_QUANTITY_EXCEEDS_PURCHASED,
    CANNOT_CANCEL_COMPLETED_RUN,
    INVALID_RUN_STATE_TRANSITION,
    NOT_RUN_LEADER,
    NOT_RUN_PARTICIPANT,
    PARTICIPATION_NOT_FOUND,
    RUN_ALREADY_CANCELLED,
    RUN_NOT_FOUND,
    RUN_NOT_IN_ACTIVE_STATE,
    RUN_NOT_IN_ADJUSTING_STATE,
    RUN_NOT_IN_CONFIRMED_STATE,
)
from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.core.models import ProductBid, Run, RunParticipation, ShoppingListItem, Store
from app.core.run_state import RunState
from app.events.domain_events import ReadyToggledEvent, RunCancelledEvent, RunStateChangedEvent
from app.services.run_state_service import RunStateService


class TestToggleReady:
    """Test cases for RunStateService.toggle_ready()."""

    async def test_toggle_ready_false_to_true(self, test_user):
        """Test toggling ready status from False to True."""
        # Arrange
        mock_db = AsyncMock()
        service = RunStateService(mock_db)

        run_id = uuid4()
        participation_id = uuid4()
        group_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.ACTIVE
        mock_run.group_id = group_id

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.id = participation_id
        mock_participation.user_id = test_user.id
        mock_participation.is_ready = False
        mock_participation.is_leader = False

        # Mock repositories
        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(return_value=mock_participation)
        service.run_repo.update_participation_ready = AsyncMock()
        service.user_repo.get_user_groups = AsyncMock(return_value=[Mock(id=group_id)])

        # Mock event bus
        with patch('app.services.run_state_service.event_bus') as mock_event_bus:
            # Act
            result = await service.toggle_ready(str(run_id), test_user)

            # Assert
            assert result.is_ready is True
            assert result.state_changed is False
            assert result.new_state is None
            assert result.run_id == str(run_id)
            assert result.user_id == str(test_user.id)

            # Verify repository calls
            service.run_repo.update_participation_ready.assert_called_once_with(
                participation_id, True
            )

            # Verify event was emitted
            mock_event_bus.emit.assert_called_once()
            emitted_event = mock_event_bus.emit.call_args[0][0]
            assert isinstance(emitted_event, ReadyToggledEvent)
            assert emitted_event.run_id == run_id
            assert emitted_event.user_id == test_user.id
            assert emitted_event.is_ready is True
            assert emitted_event.group_id == group_id

    async def test_toggle_ready_true_to_false(self, test_user):
        """Test toggling ready status from True to False."""
        # Arrange
        mock_db = AsyncMock()
        service = RunStateService(mock_db)

        run_id = uuid4()
        participation_id = uuid4()
        group_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.ACTIVE
        mock_run.group_id = group_id

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.id = participation_id
        mock_participation.user_id = test_user.id
        mock_participation.is_ready = True
        mock_participation.is_leader = False

        # Mock repositories
        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(return_value=mock_participation)
        service.run_repo.update_participation_ready = AsyncMock()
        service.user_repo.get_user_groups = AsyncMock(return_value=[Mock(id=group_id)])

        # Mock event bus
        with patch('app.services.run_state_service.event_bus') as mock_event_bus:
            # Act
            result = await service.toggle_ready(str(run_id), test_user)

            # Assert
            assert result.is_ready is False
            service.run_repo.update_participation_ready.assert_called_once_with(
                participation_id, False
            )

            # Verify event
            emitted_event = mock_event_bus.emit.call_args[0][0]
            assert emitted_event.is_ready is False

    async def test_toggle_ready_run_not_found(self, test_user):
        """Test toggling ready when run does not exist."""
        # Arrange
        mock_db = AsyncMock()
        service = RunStateService(mock_db)

        run_id = uuid4()
        service.run_repo.get_run_by_id = AsyncMock(return_value=None)

        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.toggle_ready(str(run_id), test_user)

        assert exc_info.value.code == RUN_NOT_FOUND

    async def test_toggle_ready_participation_not_found(self, test_user):
        """Test toggling ready when user is not participating."""
        # Arrange
        mock_db = AsyncMock()
        service = RunStateService(mock_db)

        run_id = uuid4()
        group_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.ACTIVE
        mock_run.group_id = group_id

        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(return_value=None)
        service.user_repo.get_user_groups = AsyncMock(return_value=[Mock(id=group_id)])

        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.toggle_ready(str(run_id), test_user)

        assert exc_info.value.code == PARTICIPATION_NOT_FOUND

    async def test_toggle_ready_not_authorized(self, test_user):
        """Test toggling ready when user is not in the group."""
        # Arrange
        mock_db = AsyncMock()
        service = RunStateService(mock_db)

        run_id = uuid4()
        group_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.ACTIVE
        mock_run.group_id = group_id

        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.user_repo.get_user_groups = AsyncMock(return_value=[])

        # Act & Assert
        with pytest.raises(ForbiddenError) as exc_info:
            await service.toggle_ready(str(run_id), test_user)

        assert exc_info.value.code == NOT_RUN_PARTICIPANT

    @pytest.mark.parametrize(
        'state',
        [
            RunState.PLANNING,
            RunState.CONFIRMED,
            RunState.SHOPPING,
            RunState.ADJUSTING,
            RunState.DISTRIBUTING,
            RunState.COMPLETED,
            RunState.CANCELLED,
        ],
    )
    async def test_toggle_ready_invalid_state(self, test_user, state):
        """Test toggling ready from invalid states."""
        # Arrange
        mock_db = AsyncMock()
        service = RunStateService(mock_db)

        run_id = uuid4()
        group_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = state
        mock_run.group_id = group_id

        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.user_repo.get_user_groups = AsyncMock(return_value=[Mock(id=group_id)])

        # Act & Assert
        with pytest.raises(BadRequestError) as exc_info:
            await service.toggle_ready(str(run_id), test_user)

        assert exc_info.value.code == RUN_NOT_IN_ACTIVE_STATE

    async def test_toggle_ready_invalid_uuid(self, test_user):
        """Test toggling ready with invalid UUID format."""
        # Arrange
        mock_db = AsyncMock()
        service = RunStateService(mock_db)

        # Act & Assert
        with pytest.raises(BadRequestError):
            await service.toggle_ready('not-a-uuid', test_user)


class TestForceConfirm:
    """Test cases for RunStateService.force_confirm()."""

    async def test_force_confirm_from_planning(self, test_user):
        """Test force confirming run from PLANNING state."""
        # Arrange
        mock_db = AsyncMock()
        service = RunStateService(mock_db)

        run_id = uuid4()
        group_id = uuid4()
        store_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.PLANNING
        mock_run.group_id = group_id
        mock_run.store_id = store_id

        mock_store = Mock(spec=Store)
        mock_store.name = 'Test Store'

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.is_leader = True

        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(return_value=mock_participation)
        service.run_repo.update_run_state = AsyncMock()
        service.store_repo.get_store_by_id = AsyncMock(return_value=mock_store)
        service.user_repo.get_user_groups = AsyncMock(return_value=[Mock(id=group_id)])

        # Mock event bus
        with patch('app.services.run_state_service.event_bus') as mock_event_bus:
            # Act
            result = await service.force_confirm(str(run_id), test_user)

            # Assert
            assert result.state == RunState.CONFIRMED
            assert result.run_id == str(run_id)
            assert result.group_id == str(group_id)

            # Verify repository calls
            service.run_repo.update_run_state.assert_called_once_with(run_id, RunState.CONFIRMED)

            # Verify event was emitted
            mock_event_bus.emit.assert_called_once()
            emitted_event = mock_event_bus.emit.call_args[0][0]
            assert isinstance(emitted_event, RunStateChangedEvent)
            assert emitted_event.run_id == run_id
            assert emitted_event.old_state == RunState.PLANNING
            assert emitted_event.new_state == RunState.CONFIRMED

    async def test_force_confirm_from_active(self, test_user):
        """Test force confirming run from ACTIVE state."""
        # Arrange
        mock_db = AsyncMock()
        service = RunStateService(mock_db)

        run_id = uuid4()
        group_id = uuid4()
        store_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.ACTIVE
        mock_run.group_id = group_id
        mock_run.store_id = store_id

        mock_store = Mock(spec=Store)
        mock_store.name = 'Test Store'

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.is_leader = True

        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(return_value=mock_participation)
        service.run_repo.update_run_state = AsyncMock()
        service.store_repo.get_store_by_id = AsyncMock(return_value=mock_store)
        service.user_repo.get_user_groups = AsyncMock(return_value=[Mock(id=group_id)])

        # Mock event bus
        with patch('app.services.run_state_service.event_bus'):
            # Act
            result = await service.force_confirm(str(run_id), test_user)

            # Assert
            assert result.state == RunState.CONFIRMED
            service.run_repo.update_run_state.assert_called_once_with(run_id, RunState.CONFIRMED)

    async def test_force_confirm_not_leader(self, test_user):
        """Test force confirm by non-leader fails."""
        # Arrange
        mock_db = AsyncMock()
        service = RunStateService(mock_db)

        run_id = uuid4()
        group_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.ACTIVE
        mock_run.group_id = group_id

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.is_leader = False

        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(return_value=mock_participation)
        service.user_repo.get_user_groups = AsyncMock(return_value=[Mock(id=group_id)])

        # Act & Assert
        with pytest.raises(ForbiddenError) as exc_info:
            await service.force_confirm(str(run_id), test_user)

        assert exc_info.value.code == NOT_RUN_LEADER

    async def test_force_confirm_run_not_found(self, test_user):
        """Test force confirm when run does not exist."""
        # Arrange
        mock_db = AsyncMock()
        service = RunStateService(mock_db)

        run_id = uuid4()
        service.run_repo.get_run_by_id = AsyncMock(return_value=None)

        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.force_confirm(str(run_id), test_user)

        assert exc_info.value.code == RUN_NOT_FOUND

    @pytest.mark.parametrize(
        'state',
        [
            RunState.CONFIRMED,
            RunState.SHOPPING,
            RunState.ADJUSTING,
            RunState.DISTRIBUTING,
            RunState.COMPLETED,
            RunState.CANCELLED,
        ],
    )
    async def test_force_confirm_invalid_state(self, test_user, state):
        """Test force confirm from invalid states."""
        # Arrange
        mock_db = AsyncMock()
        service = RunStateService(mock_db)

        run_id = uuid4()
        group_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = state
        mock_run.group_id = group_id

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.is_leader = True

        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(return_value=mock_participation)
        service.user_repo.get_user_groups = AsyncMock(return_value=[Mock(id=group_id)])

        # Act & Assert
        with pytest.raises(BadRequestError) as exc_info:
            await service.force_confirm(str(run_id), test_user)

        assert exc_info.value.code == RUN_NOT_IN_ACTIVE_STATE

    async def test_force_confirm_not_group_member(self, test_user):
        """Test force confirm when user is not in the group."""
        # Arrange
        mock_db = AsyncMock()
        service = RunStateService(mock_db)

        run_id = uuid4()
        group_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.ACTIVE
        mock_run.group_id = group_id

        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.user_repo.get_user_groups = AsyncMock(return_value=[])

        # Act & Assert
        with pytest.raises(ForbiddenError) as exc_info:
            await service.force_confirm(str(run_id), test_user)

        assert exc_info.value.code == NOT_RUN_PARTICIPANT


class TestStartShopping:
    """Test cases for RunStateService.start_shopping()."""

    async def test_start_shopping_success(self, test_user):
        """Test starting shopping from CONFIRMED state."""
        # Arrange
        mock_db = AsyncMock()
        service = RunStateService(mock_db)

        run_id = uuid4()
        group_id = uuid4()
        store_id = uuid4()
        product_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.CONFIRMED
        mock_run.group_id = group_id
        mock_run.store_id = store_id

        mock_store = Mock(spec=Store)
        mock_store.name = 'Test Store'

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.is_leader = True

        mock_bid = Mock(spec=ProductBid)
        mock_bid.product_id = product_id
        mock_bid.quantity = 5
        mock_bid.interested_only = False

        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(return_value=mock_participation)
        service.run_repo.update_run_state = AsyncMock()
        service.store_repo.get_store_by_id = AsyncMock(return_value=mock_store)
        service.user_repo.get_user_groups = AsyncMock(return_value=[Mock(id=group_id)])
        service.bid_repo.get_bids_by_run = AsyncMock(return_value=[mock_bid])
        service.shopping_repo.create_shopping_list_item = AsyncMock()

        # Mock event bus
        with patch('app.services.run_state_service.event_bus') as mock_event_bus:
            # Act
            result = await service.start_shopping(str(run_id), test_user)

            # Assert
            assert result.state == RunState.SHOPPING
            assert result.run_id == str(run_id)

            # Verify shopping list was created
            service.bid_repo.get_bids_by_run.assert_called_once_with(run_id)
            service.shopping_repo.create_shopping_list_item.assert_called_once_with(
                run_id, product_id, 5
            )

            # Verify state transition
            service.run_repo.update_run_state.assert_called_once_with(run_id, RunState.SHOPPING)

            # Verify event
            mock_event_bus.emit.assert_called_once()
            emitted_event = mock_event_bus.emit.call_args[0][0]
            assert isinstance(emitted_event, RunStateChangedEvent)
            assert emitted_event.new_state == RunState.SHOPPING

    async def test_start_shopping_aggregates_bids(self, test_user):
        """Test shopping list aggregates multiple bids for same product."""
        # Arrange
        mock_db = AsyncMock()
        service = RunStateService(mock_db)

        run_id = uuid4()
        group_id = uuid4()
        product_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.CONFIRMED
        mock_run.group_id = group_id
        mock_run.store_id = uuid4()

        mock_store = Mock(spec=Store)
        mock_store.name = 'Test Store'

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.is_leader = True

        # Multiple bids for same product
        mock_bid1 = Mock(spec=ProductBid)
        mock_bid1.product_id = product_id
        mock_bid1.quantity = 3
        mock_bid1.interested_only = False

        mock_bid2 = Mock(spec=ProductBid)
        mock_bid2.product_id = product_id
        mock_bid2.quantity = 7
        mock_bid2.interested_only = False

        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(return_value=mock_participation)
        service.run_repo.update_run_state = AsyncMock()
        service.store_repo.get_store_by_id = AsyncMock(return_value=mock_store)
        service.user_repo.get_user_groups = AsyncMock(return_value=[Mock(id=group_id)])
        service.bid_repo.get_bids_by_run = AsyncMock(return_value=[mock_bid1, mock_bid2])
        service.shopping_repo.create_shopping_list_item = AsyncMock()

        # Mock event bus
        with patch('app.services.run_state_service.event_bus'):
            # Act
            await service.start_shopping(str(run_id), test_user)

            # Assert - should aggregate to 10
            service.shopping_repo.create_shopping_list_item.assert_called_once_with(
                run_id, product_id, 10
            )

    async def test_start_shopping_skips_interested_only(self, test_user):
        """Test shopping list skips interested_only bids."""
        # Arrange
        mock_db = AsyncMock()
        service = RunStateService(mock_db)

        run_id = uuid4()
        group_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.CONFIRMED
        mock_run.group_id = group_id
        mock_run.store_id = uuid4()

        mock_store = Mock(spec=Store)
        mock_store.name = 'Test Store'

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.is_leader = True

        mock_bid = Mock(spec=ProductBid)
        mock_bid.product_id = uuid4()
        mock_bid.quantity = 5
        mock_bid.interested_only = True

        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(return_value=mock_participation)
        service.run_repo.update_run_state = AsyncMock()
        service.store_repo.get_store_by_id = AsyncMock(return_value=mock_store)
        service.user_repo.get_user_groups = AsyncMock(return_value=[Mock(id=group_id)])
        service.bid_repo.get_bids_by_run = AsyncMock(return_value=[mock_bid])
        service.shopping_repo.create_shopping_list_item = AsyncMock()

        # Mock event bus
        with patch('app.services.run_state_service.event_bus'):
            # Act
            await service.start_shopping(str(run_id), test_user)

            # Assert - should not create shopping list item
            service.shopping_repo.create_shopping_list_item.assert_not_called()

    async def test_start_shopping_not_leader(self, test_user):
        """Test start shopping by non-leader fails."""
        # Arrange
        mock_db = AsyncMock()
        service = RunStateService(mock_db)

        run_id = uuid4()
        group_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.CONFIRMED
        mock_run.group_id = group_id

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.is_leader = False

        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(return_value=mock_participation)
        service.user_repo.get_user_groups = AsyncMock(return_value=[Mock(id=group_id)])

        # Act & Assert
        with pytest.raises(ForbiddenError) as exc_info:
            await service.start_shopping(str(run_id), test_user)

        assert exc_info.value.code == NOT_RUN_LEADER

    async def test_start_shopping_run_not_found(self, test_user):
        """Test start shopping when run does not exist."""
        # Arrange
        mock_db = AsyncMock()
        service = RunStateService(mock_db)

        run_id = uuid4()
        service.run_repo.get_run_by_id = AsyncMock(return_value=None)

        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.start_shopping(str(run_id), test_user)

        assert exc_info.value.code == RUN_NOT_FOUND

    @pytest.mark.parametrize(
        'state',
        [
            RunState.PLANNING,
            RunState.ACTIVE,
            RunState.SHOPPING,
            RunState.ADJUSTING,
            RunState.DISTRIBUTING,
            RunState.COMPLETED,
            RunState.CANCELLED,
        ],
    )
    async def test_start_shopping_invalid_state(self, test_user, state):
        """Test start shopping from invalid states."""
        # Arrange
        mock_db = AsyncMock()
        service = RunStateService(mock_db)

        run_id = uuid4()
        group_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = state
        mock_run.group_id = group_id

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.is_leader = True

        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(return_value=mock_participation)
        service.user_repo.get_user_groups = AsyncMock(return_value=[Mock(id=group_id)])

        # Act & Assert
        with pytest.raises(BadRequestError) as exc_info:
            await service.start_shopping(str(run_id), test_user)

        assert exc_info.value.code == RUN_NOT_IN_CONFIRMED_STATE


class TestFinishAdjusting:
    """Test cases for RunStateService.finish_adjusting()."""

    async def test_finish_adjusting_success(self, test_user):
        """Test finishing adjusting phase successfully."""
        # Arrange
        mock_db = AsyncMock()
        service = RunStateService(mock_db)

        run_id = uuid4()
        group_id = uuid4()
        product_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.ADJUSTING
        mock_run.group_id = group_id
        mock_run.store_id = uuid4()

        mock_store = Mock(spec=Store)
        mock_store.name = 'Test Store'

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.is_leader = True

        mock_shopping_item = Mock(spec=ShoppingListItem)
        mock_shopping_item.product_id = product_id
        mock_shopping_item.is_purchased = True
        mock_shopping_item.purchased_quantity = 10

        mock_bid = Mock(spec=ProductBid)
        mock_bid.id = uuid4()
        mock_bid.product_id = product_id
        mock_bid.quantity = 10
        mock_bid.interested_only = False

        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(return_value=mock_participation)
        service.run_repo.update_run_state = AsyncMock()
        service.store_repo.get_store_by_id = AsyncMock(return_value=mock_store)
        service.user_repo.get_user_groups = AsyncMock(return_value=[Mock(id=group_id)])
        service.shopping_repo.get_shopping_list_items = AsyncMock(return_value=[mock_shopping_item])
        service.shopping_repo.update_shopping_list_item_requested_quantity = AsyncMock()
        service.bid_repo.get_bids_by_run = AsyncMock(return_value=[mock_bid])
        service.bid_repo.update_bid_distributed_quantities = AsyncMock()

        # Mock event bus
        with patch('app.services.run_state_service.event_bus') as mock_event_bus:
            # Act
            result = await service.finish_adjusting(str(run_id), test_user)

            # Assert
            assert result.state == RunState.DISTRIBUTING
            assert result.run_id == str(run_id)

            # Verify state transition
            service.run_repo.update_run_state.assert_called_once_with(run_id, RunState.DISTRIBUTING)

            # Verify distribution
            service.bid_repo.update_bid_distributed_quantities.assert_called_once()

            # Verify event
            mock_event_bus.emit.assert_called_once()
            emitted_event = mock_event_bus.emit.call_args[0][0]
            assert isinstance(emitted_event, RunStateChangedEvent)
            assert emitted_event.new_state == RunState.DISTRIBUTING

    async def test_finish_adjusting_quantities_mismatch(self, test_user):
        """Test finishing adjusting when quantities don't match."""
        # Arrange
        mock_db = AsyncMock()
        service = RunStateService(mock_db)

        run_id = uuid4()
        group_id = uuid4()
        product_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.ADJUSTING
        mock_run.group_id = group_id

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.is_leader = True

        mock_shopping_item = Mock(spec=ShoppingListItem)
        mock_shopping_item.product_id = product_id
        mock_shopping_item.is_purchased = True
        mock_shopping_item.purchased_quantity = 8

        mock_bid = Mock(spec=ProductBid)
        mock_bid.product_id = product_id
        mock_bid.quantity = 10
        mock_bid.interested_only = False

        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(return_value=mock_participation)
        service.user_repo.get_user_groups = AsyncMock(return_value=[Mock(id=group_id)])
        service.shopping_repo.get_shopping_list_items = AsyncMock(return_value=[mock_shopping_item])
        service.bid_repo.get_bids_by_run = AsyncMock(return_value=[mock_bid])

        # Act & Assert
        with pytest.raises(BadRequestError) as exc_info:
            await service.finish_adjusting(str(run_id), test_user)

        assert exc_info.value.code == BID_QUANTITY_EXCEEDS_PURCHASED

    async def test_finish_adjusting_force_mode(self, test_user):
        """Test finishing adjusting with force mode skips validation."""
        # Arrange
        mock_db = AsyncMock()
        service = RunStateService(mock_db)

        run_id = uuid4()
        group_id = uuid4()
        product_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.ADJUSTING
        mock_run.group_id = group_id
        mock_run.store_id = uuid4()

        mock_store = Mock(spec=Store)
        mock_store.name = 'Test Store'

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.is_leader = True

        mock_shopping_item = Mock(spec=ShoppingListItem)
        mock_shopping_item.product_id = product_id
        mock_shopping_item.is_purchased = True
        mock_shopping_item.purchased_quantity = 8

        mock_bid = Mock(spec=ProductBid)
        mock_bid.id = uuid4()
        mock_bid.product_id = product_id
        mock_bid.quantity = 10
        mock_bid.interested_only = False

        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(return_value=mock_participation)
        service.run_repo.update_run_state = AsyncMock()
        service.store_repo.get_store_by_id = AsyncMock(return_value=mock_store)
        service.user_repo.get_user_groups = AsyncMock(return_value=[Mock(id=group_id)])
        service.shopping_repo.get_shopping_list_items = AsyncMock(return_value=[mock_shopping_item])
        service.shopping_repo.update_shopping_list_item_requested_quantity = AsyncMock()
        service.bid_repo.get_bids_by_run = AsyncMock(return_value=[mock_bid])
        service.bid_repo.update_bid_distributed_quantities = AsyncMock()

        # Mock event bus
        with patch('app.services.run_state_service.event_bus'):
            # Act
            result = await service.finish_adjusting(str(run_id), test_user, force=True)

            # Assert - should succeed despite mismatch
            assert result.state == RunState.DISTRIBUTING

    async def test_finish_adjusting_not_leader(self, test_user):
        """Test finish adjusting by non-leader fails."""
        # Arrange
        mock_db = AsyncMock()
        service = RunStateService(mock_db)

        run_id = uuid4()
        group_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.ADJUSTING
        mock_run.group_id = group_id

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.is_leader = False

        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(return_value=mock_participation)
        service.user_repo.get_user_groups = AsyncMock(return_value=[Mock(id=group_id)])

        # Act & Assert
        with pytest.raises(ForbiddenError) as exc_info:
            await service.finish_adjusting(str(run_id), test_user)

        assert exc_info.value.code == NOT_RUN_LEADER

    @pytest.mark.parametrize(
        'state',
        [
            RunState.PLANNING,
            RunState.ACTIVE,
            RunState.CONFIRMED,
            RunState.SHOPPING,
            RunState.DISTRIBUTING,
            RunState.COMPLETED,
            RunState.CANCELLED,
        ],
    )
    async def test_finish_adjusting_invalid_state(self, test_user, state):
        """Test finish adjusting from invalid states."""
        # Arrange
        mock_db = AsyncMock()
        service = RunStateService(mock_db)

        run_id = uuid4()
        group_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = state
        mock_run.group_id = group_id

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.is_leader = True

        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(return_value=mock_participation)
        service.user_repo.get_user_groups = AsyncMock(return_value=[Mock(id=group_id)])

        # Act & Assert
        with pytest.raises(BadRequestError) as exc_info:
            await service.finish_adjusting(str(run_id), test_user)

        assert exc_info.value.code == RUN_NOT_IN_ADJUSTING_STATE

    async def test_finish_adjusting_run_not_found(self, test_user):
        """Test finish adjusting when run does not exist."""
        # Arrange
        mock_db = AsyncMock()
        service = RunStateService(mock_db)

        run_id = uuid4()
        service.run_repo.get_run_by_id = AsyncMock(return_value=None)

        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.finish_adjusting(str(run_id), test_user)

        assert exc_info.value.code == RUN_NOT_FOUND


class TestCancelRun:
    """Test cases for RunStateService.cancel_run()."""

    async def test_cancel_run_from_planning(self, test_user):
        """Test canceling run from PLANNING state."""
        # Arrange
        mock_db = AsyncMock()
        service = RunStateService(mock_db)

        run_id = uuid4()
        group_id = uuid4()
        store_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.PLANNING
        mock_run.group_id = group_id
        mock_run.store_id = store_id

        mock_store = Mock(spec=Store)
        mock_store.name = 'Test Store'

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.is_leader = True

        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(return_value=mock_participation)
        service.run_repo.update_run_state = AsyncMock()
        service.store_repo.get_store_by_id = AsyncMock(return_value=mock_store)
        service.user_repo.get_user_groups = AsyncMock(return_value=[Mock(id=group_id)])

        # Mock event bus
        with patch('app.services.run_state_service.event_bus') as mock_event_bus:
            # Act
            result = await service.cancel_run(str(run_id), test_user)

            # Assert
            assert result.state == RunState.CANCELLED.value
            assert result.run_id == str(run_id)
            assert result.group_id == str(group_id)

            # Verify repository calls
            service.run_repo.update_run_state.assert_called_once_with(run_id, RunState.CANCELLED)

            # Verify events were emitted (both state changed and cancelled)
            assert mock_event_bus.emit.call_count == 2

            # Check RunStateChangedEvent
            first_event = mock_event_bus.emit.call_args_list[0][0][0]
            assert isinstance(first_event, RunStateChangedEvent)
            assert first_event.old_state == RunState.PLANNING
            assert first_event.new_state == RunState.CANCELLED

            # Check RunCancelledEvent
            second_event = mock_event_bus.emit.call_args_list[1][0][0]
            assert isinstance(second_event, RunCancelledEvent)
            assert second_event.run_id == run_id

    async def test_cancel_run_from_active(self, test_user):
        """Test canceling run from ACTIVE state."""
        # Arrange
        mock_db = AsyncMock()
        service = RunStateService(mock_db)

        run_id = uuid4()
        group_id = uuid4()
        store_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.ACTIVE
        mock_run.group_id = group_id
        mock_run.store_id = store_id

        mock_store = Mock(spec=Store)
        mock_store.name = 'Test Store'

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.is_leader = True

        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(return_value=mock_participation)
        service.run_repo.update_run_state = AsyncMock()
        service.store_repo.get_store_by_id = AsyncMock(return_value=mock_store)
        service.user_repo.get_user_groups = AsyncMock(return_value=[Mock(id=group_id)])

        # Mock event bus
        with patch('app.services.run_state_service.event_bus'):
            # Act
            result = await service.cancel_run(str(run_id), test_user)

            # Assert
            assert result.state == RunState.CANCELLED.value
            service.run_repo.update_run_state.assert_called_once_with(run_id, RunState.CANCELLED)

    async def test_cancel_run_from_confirmed(self, test_user):
        """Test canceling run from CONFIRMED state."""
        # Arrange
        mock_db = AsyncMock()
        service = RunStateService(mock_db)

        run_id = uuid4()
        group_id = uuid4()
        store_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.CONFIRMED
        mock_run.group_id = group_id
        mock_run.store_id = store_id

        mock_store = Mock(spec=Store)
        mock_store.name = 'Test Store'

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.is_leader = True

        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(return_value=mock_participation)
        service.run_repo.update_run_state = AsyncMock()
        service.store_repo.get_store_by_id = AsyncMock(return_value=mock_store)
        service.user_repo.get_user_groups = AsyncMock(return_value=[Mock(id=group_id)])

        # Mock event bus
        with patch('app.services.run_state_service.event_bus'):
            # Act
            result = await service.cancel_run(str(run_id), test_user)

            # Assert
            assert result.state == RunState.CANCELLED.value

    async def test_cancel_run_from_distributing_fails(self, test_user):
        """Test canceling run from DISTRIBUTING state fails."""
        # Arrange
        mock_db = AsyncMock()
        service = RunStateService(mock_db)

        run_id = uuid4()
        group_id = uuid4()
        store_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.DISTRIBUTING
        mock_run.group_id = group_id
        mock_run.store_id = store_id

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.is_leader = True

        mock_store = Mock(spec=Store)
        mock_store.name = 'Test Store'

        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(return_value=mock_participation)
        service.run_repo.update_run_state = AsyncMock()
        service.store_repo.get_store_by_id = AsyncMock(return_value=mock_store)
        service.user_repo.get_user_groups = AsyncMock(return_value=[Mock(id=group_id)])

        # Act & Assert - DISTRIBUTING cannot transition to CANCELLED (invalid transition)
        with pytest.raises(BadRequestError) as exc_info:
            await service.cancel_run(str(run_id), test_user)

        # Should fail with invalid state transition error
        assert exc_info.value.code == INVALID_RUN_STATE_TRANSITION

    async def test_cancel_run_already_completed(self, test_user):
        """Test canceling run that is already completed."""
        # Arrange
        mock_db = AsyncMock()
        service = RunStateService(mock_db)

        run_id = uuid4()
        group_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.COMPLETED
        mock_run.group_id = group_id

        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.user_repo.get_user_groups = AsyncMock(return_value=[Mock(id=group_id)])

        # Act & Assert
        with pytest.raises(BadRequestError) as exc_info:
            await service.cancel_run(str(run_id), test_user)

        assert exc_info.value.code == CANNOT_CANCEL_COMPLETED_RUN

    async def test_cancel_run_already_cancelled(self, test_user):
        """Test canceling run that is already cancelled."""
        # Arrange
        mock_db = AsyncMock()
        service = RunStateService(mock_db)

        run_id = uuid4()
        group_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.CANCELLED
        mock_run.group_id = group_id

        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.user_repo.get_user_groups = AsyncMock(return_value=[Mock(id=group_id)])

        # Act & Assert
        with pytest.raises(BadRequestError) as exc_info:
            await service.cancel_run(str(run_id), test_user)

        assert exc_info.value.code == RUN_ALREADY_CANCELLED

    async def test_cancel_run_not_leader(self, test_user):
        """Test cancel run by non-leader fails."""
        # Arrange
        mock_db = AsyncMock()
        service = RunStateService(mock_db)

        run_id = uuid4()
        group_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.ACTIVE
        mock_run.group_id = group_id

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.is_leader = False

        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(return_value=mock_participation)
        service.user_repo.get_user_groups = AsyncMock(return_value=[Mock(id=group_id)])

        # Act & Assert
        with pytest.raises(ForbiddenError) as exc_info:
            await service.cancel_run(str(run_id), test_user)

        assert exc_info.value.code == NOT_RUN_LEADER

    async def test_cancel_run_not_found(self, test_user):
        """Test canceling non-existent run."""
        # Arrange
        mock_db = AsyncMock()
        service = RunStateService(mock_db)

        run_id = uuid4()
        service.run_repo.get_run_by_id = AsyncMock(return_value=None)

        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.cancel_run(str(run_id), test_user)

        assert exc_info.value.code == RUN_NOT_FOUND


class TestTransitionRunState:
    """Test cases for RunStateService._transition_run_state()."""

    async def test_transition_run_state_valid(self, test_user):
        """Test valid state transition."""
        # Arrange
        mock_db = AsyncMock()
        service = RunStateService(mock_db)

        run_id = uuid4()
        store_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.PLANNING
        mock_run.group_id = uuid4()
        mock_run.store_id = store_id

        mock_store = Mock(spec=Store)
        mock_store.name = 'Test Store'

        service.run_repo.update_run_state = AsyncMock()
        service.store_repo.get_store_by_id = AsyncMock(return_value=mock_store)

        # Mock event bus
        with patch('app.services.run_state_service.event_bus') as mock_event_bus:
            # Act
            old_state = await service._transition_run_state(mock_run, RunState.ACTIVE)

            # Assert
            assert old_state == RunState.PLANNING
            service.run_repo.update_run_state.assert_called_once_with(run_id, RunState.ACTIVE)

            # Verify event
            mock_event_bus.emit.assert_called_once()
            emitted_event = mock_event_bus.emit.call_args[0][0]
            assert isinstance(emitted_event, RunStateChangedEvent)
            assert emitted_event.old_state == RunState.PLANNING
            assert emitted_event.new_state == RunState.ACTIVE

    async def test_transition_run_state_invalid_raises_error(self, test_user):
        """Test invalid state transition raises BadRequestError."""
        # Arrange
        mock_db = AsyncMock()
        service = RunStateService(mock_db)

        mock_run = Mock(spec=Run)
        mock_run.id = uuid4()
        mock_run.state = RunState.COMPLETED
        mock_run.group_id = uuid4()

        # Act & Assert
        with pytest.raises(BadRequestError) as exc_info:
            await service._transition_run_state(mock_run, RunState.PLANNING)

        assert exc_info.value.code == INVALID_RUN_STATE_TRANSITION

    async def test_transition_run_state_no_notification(self, test_user):
        """Test state transition without notification."""
        # Arrange
        mock_db = AsyncMock()
        service = RunStateService(mock_db)

        run_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.PLANNING
        mock_run.group_id = uuid4()
        mock_run.store_id = uuid4()

        service.run_repo.update_run_state = AsyncMock()

        # Mock event bus
        with patch('app.services.run_state_service.event_bus') as mock_event_bus:
            # Act
            await service._transition_run_state(mock_run, RunState.ACTIVE, notify=False)

            # Assert - no event should be emitted
            mock_event_bus.emit.assert_not_called()
            service.run_repo.update_run_state.assert_called_once_with(run_id, RunState.ACTIVE)


class TestDistributeItemsToBidders:
    """Test cases for RunStateService._distribute_items_to_bidders()."""

    async def test_distribute_exact_match(self, test_user):
        """Test distribution when bid quantities exactly match purchased."""
        # Arrange
        mock_db = AsyncMock()
        service = RunStateService(mock_db)

        run_id = uuid4()
        product_id = uuid4()
        bid_id = uuid4()

        mock_shopping_item = Mock(spec=ShoppingListItem)
        mock_shopping_item.id = uuid4()
        mock_shopping_item.product_id = product_id
        mock_shopping_item.is_purchased = True
        mock_shopping_item.purchased_quantity = 10
        mock_shopping_item.purchased_price_per_unit = Decimal('5.00')

        mock_bid = Mock(spec=ProductBid)
        mock_bid.id = bid_id
        mock_bid.product_id = product_id
        mock_bid.quantity = 10
        mock_bid.interested_only = False

        service.shopping_repo.get_shopping_list_items = AsyncMock(return_value=[mock_shopping_item])
        service.shopping_repo.update_shopping_list_item_requested_quantity = AsyncMock()
        service.bid_repo.get_bids_by_run = AsyncMock(return_value=[mock_bid])
        service.bid_repo.update_bid_distributed_quantities = AsyncMock()

        # Act
        await service._distribute_items_to_bidders(run_id)

        # Assert
        service.bid_repo.update_bid_distributed_quantities.assert_called_once_with(
            bid_id, 10, Decimal('5.00')
        )

    async def test_distribute_proportional(self, test_user):
        """Test proportional distribution when purchased less than requested."""
        # Arrange
        mock_db = AsyncMock()
        service = RunStateService(mock_db)

        run_id = uuid4()
        product_id = uuid4()
        bid_id1 = uuid4()
        bid_id2 = uuid4()

        mock_shopping_item = Mock(spec=ShoppingListItem)
        mock_shopping_item.id = uuid4()
        mock_shopping_item.product_id = product_id
        mock_shopping_item.is_purchased = True
        mock_shopping_item.purchased_quantity = 8
        mock_shopping_item.purchased_price_per_unit = Decimal('5.00')

        mock_bid1 = Mock(spec=ProductBid)
        mock_bid1.id = bid_id1
        mock_bid1.product_id = product_id
        mock_bid1.quantity = 6
        mock_bid1.interested_only = False

        mock_bid2 = Mock(spec=ProductBid)
        mock_bid2.id = bid_id2
        mock_bid2.product_id = product_id
        mock_bid2.quantity = 4
        mock_bid2.interested_only = False

        service.shopping_repo.get_shopping_list_items = AsyncMock(return_value=[mock_shopping_item])
        service.shopping_repo.update_shopping_list_item_requested_quantity = AsyncMock()
        service.bid_repo.get_bids_by_run = AsyncMock(return_value=[mock_bid1, mock_bid2])
        service.bid_repo.update_bid_distributed_quantities = AsyncMock()

        # Act
        await service._distribute_items_to_bidders(run_id)

        # Assert - should be called twice (once for each bid)
        assert service.bid_repo.update_bid_distributed_quantities.call_count == 2

        # First bid should get 4.8 (6/10 * 8)
        first_call = service.bid_repo.update_bid_distributed_quantities.call_args_list[0]
        assert first_call[0][0] == bid_id1
        assert first_call[0][1] == Decimal('4.80')

        # Second bid should get remaining 3.2
        second_call = service.bid_repo.update_bid_distributed_quantities.call_args_list[1]
        assert second_call[0][0] == bid_id2
        assert second_call[0][1] == Decimal('3.20')

    async def test_distribute_skips_unpurchased(self, test_user):
        """Test distribution skips unpurchased items."""
        # Arrange
        mock_db = AsyncMock()
        service = RunStateService(mock_db)

        run_id = uuid4()
        product_id = uuid4()

        mock_shopping_item = Mock(spec=ShoppingListItem)
        mock_shopping_item.product_id = product_id
        mock_shopping_item.is_purchased = False
        mock_shopping_item.purchased_quantity = 0

        service.shopping_repo.get_shopping_list_items = AsyncMock(return_value=[mock_shopping_item])
        service.bid_repo.get_bids_by_run = AsyncMock(return_value=[])
        service.bid_repo.update_bid_distributed_quantities = AsyncMock()

        # Act
        await service._distribute_items_to_bidders(run_id)

        # Assert - should not update any bids
        service.bid_repo.update_bid_distributed_quantities.assert_not_called()

    async def test_distribute_skips_zero_quantity(self, test_user):
        """Test distribution skips items with zero purchased quantity."""
        # Arrange
        mock_db = AsyncMock()
        service = RunStateService(mock_db)

        run_id = uuid4()
        product_id = uuid4()

        mock_shopping_item = Mock(spec=ShoppingListItem)
        mock_shopping_item.product_id = product_id
        mock_shopping_item.is_purchased = True
        mock_shopping_item.purchased_quantity = 0

        service.shopping_repo.get_shopping_list_items = AsyncMock(return_value=[mock_shopping_item])
        service.bid_repo.get_bids_by_run = AsyncMock(return_value=[])
        service.bid_repo.update_bid_distributed_quantities = AsyncMock()

        # Act
        await service._distribute_items_to_bidders(run_id)

        # Assert - should not update any bids
        service.bid_repo.update_bid_distributed_quantities.assert_not_called()


class TestEdgeCases:
    """Test edge cases and error handling."""

    async def test_invalid_uuid_format(self, test_user):
        """Test operations with invalid UUID format."""
        # Arrange
        mock_db = AsyncMock()
        service = RunStateService(mock_db)

        # Act & Assert
        with pytest.raises(BadRequestError):
            await service.toggle_ready('not-a-uuid', test_user)

        with pytest.raises(BadRequestError):
            await service.force_confirm('invalid-uuid', test_user)

        with pytest.raises(BadRequestError):
            await service.start_shopping('bad-format', test_user)

    async def test_event_bus_failure_does_not_corrupt_state(self, test_user):
        """Test that event bus failure doesn't corrupt run state."""
        # Arrange
        mock_db = AsyncMock()
        service = RunStateService(mock_db)

        run_id = uuid4()
        group_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.PLANNING
        mock_run.group_id = group_id
        mock_run.store_id = uuid4()

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.is_leader = True

        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(return_value=mock_participation)
        service.run_repo.update_run_state = AsyncMock()
        service.store_repo.get_store_by_id = AsyncMock(return_value=Mock(name='Test Store'))
        service.user_repo.get_user_groups = AsyncMock(return_value=[Mock(id=group_id)])

        # Mock event bus to raise exception
        with patch('app.services.run_state_service.event_bus') as mock_event_bus:
            mock_event_bus.emit.side_effect = RuntimeError('Event bus failure')

            # Act & Assert - should raise the exception
            with pytest.raises(RuntimeError):
                await service.force_confirm(str(run_id), test_user)

            # State should have been updated before event failed
            service.run_repo.update_run_state.assert_called_once()

    async def test_repository_exception_handling(self, test_user):
        """Test handling of repository exceptions."""
        # Arrange
        mock_db = AsyncMock()
        service = RunStateService(mock_db)

        run_id = uuid4()

        # Mock repository to raise exception
        service.run_repo.get_run_by_id = AsyncMock(side_effect=RuntimeError('Database error'))

        # Act & Assert
        with pytest.raises(RuntimeError) as exc_info:
            await service.toggle_ready(str(run_id), test_user)

        assert 'Database error' in str(exc_info.value)

    async def test_verify_quantities_match_with_zero_purchased(self, test_user):
        """Test quantity verification skips items with zero purchased quantity."""
        # Arrange
        mock_db = AsyncMock()
        service = RunStateService(mock_db)

        run_id = uuid4()
        product_id = uuid4()

        mock_shopping_item = Mock(spec=ShoppingListItem)
        mock_shopping_item.product_id = product_id
        mock_shopping_item.is_purchased = True
        mock_shopping_item.purchased_quantity = 0

        mock_bid = Mock(spec=ProductBid)
        mock_bid.product_id = product_id
        mock_bid.quantity = 10
        mock_bid.interested_only = False

        service.shopping_repo.get_shopping_list_items = AsyncMock(return_value=[mock_shopping_item])
        service.bid_repo.get_bids_by_run = AsyncMock(return_value=[mock_bid])

        # Act - should not raise exception
        await service._verify_quantities_match(run_id)

        # Assert - completes without error

    async def test_verify_quantities_match_skips_interested_only(self, test_user):
        """Test quantity verification skips interested_only bids."""
        # Arrange
        mock_db = AsyncMock()
        service = RunStateService(mock_db)

        run_id = uuid4()
        product_id = uuid4()

        mock_shopping_item = Mock(spec=ShoppingListItem)
        mock_shopping_item.product_id = product_id
        mock_shopping_item.is_purchased = True
        mock_shopping_item.purchased_quantity = 5

        # Interested_only bid
        mock_bid_interested = Mock(spec=ProductBid)
        mock_bid_interested.product_id = product_id
        mock_bid_interested.quantity = 10
        mock_bid_interested.interested_only = True

        # Regular bid matching purchased quantity
        mock_bid_regular = Mock(spec=ProductBid)
        mock_bid_regular.product_id = product_id
        mock_bid_regular.quantity = 5
        mock_bid_regular.interested_only = False

        service.shopping_repo.get_shopping_list_items = AsyncMock(return_value=[mock_shopping_item])
        service.bid_repo.get_bids_by_run = AsyncMock(
            return_value=[mock_bid_interested, mock_bid_regular]
        )

        # Act - should not raise exception (interested_only bid doesn't count, only regular bid counts)
        await service._verify_quantities_match(run_id)

        # Assert - completes without error
