"""Unit tests for BidService."""

from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest

from app.core.error_codes import (
    BID_NOT_FOUND,
    BID_QUANTITY_NEGATIVE,
    CANNOT_BID_NEW_PRODUCT_IN_ADJUSTING,
    CANNOT_JOIN_RUN_IN_ADJUSTING_STATE,
    CANNOT_RETRACT_BID_IN_ADJUSTING,
    INVALID_RUN_STATE_TRANSITION,
    NOT_RUN_PARTICIPANT,
    PARTICIPATION_NOT_FOUND,
    PRODUCT_NOT_FOUND,
    RUN_MAX_PRODUCTS_EXCEEDED,
    RUN_NOT_FOUND,
)
from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.core.models import Product, ProductBid, Run, RunParticipation
from app.core.run_state import RunState
from app.core.success_codes import BID_PLACED, BID_RETRACTED
from app.events.domain_events import BidPlacedEvent, BidRetractedEvent
from app.services.bid_service import BidService


class TestPlaceBid:
    """Test cases for BidService.place_bid()."""

    async def test_place_new_bid_with_quantity(self, test_user):
        """Test placing a new bid with quantity."""
        # Arrange
        mock_db = AsyncMock()
        service = BidService(mock_db)

        run_id = uuid4()
        product_id = uuid4()
        group_id = uuid4()
        participation_id = uuid4()
        quantity = 5.0

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.ACTIVE.value
        mock_run.group_id = group_id

        mock_product = Mock(spec=Product)
        mock_product.id = product_id
        mock_product.name = 'Test Product'

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.id = participation_id
        mock_participation.user_id = test_user.id
        mock_participation.is_leader = False

        mock_group = Mock()
        mock_group.id = group_id

        # Setup mocks
        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.product_repo.get_product_by_id = AsyncMock(return_value=mock_product)
        service.user_repo.get_user_groups = AsyncMock(return_value=[mock_group])
        service.run_repo.get_participation = AsyncMock(return_value=mock_participation)
        service.bid_repo.get_bid = AsyncMock(return_value=None)
        service.bid_repo.get_bids_by_run = AsyncMock(return_value=[])
        service.bid_repo.create_or_update_bid = AsyncMock()

        with patch('app.services.bid_service.event_bus') as mock_event_bus:
            # Act
            result = await service.place_bid(
                run_id=str(run_id),
                product_id=str(product_id),
                quantity=quantity,
                interested_only=False,
                user=test_user,
            )

            # Assert
            assert result is not None
            assert result.code == BID_PLACED
            assert result.quantity == quantity
            assert result.interested_only is False
            assert result.product_id == str(product_id)
            assert result.user_id == str(test_user.id)
            assert result.new_total == 0.0  # No existing bids

            # Verify repository calls
            service.bid_repo.create_or_update_bid.assert_called_once_with(
                participation_id, product_id, quantity, False, None
            )

            # Verify event emitted
            mock_event_bus.emit.assert_called_once()
            event = mock_event_bus.emit.call_args[0][0]
            assert isinstance(event, BidPlacedEvent)
            assert event.run_id == run_id
            assert event.product_id == product_id
            assert event.user_id == test_user.id
            assert event.quantity == quantity
            assert event.interested_only is False

    async def test_place_bid_with_interested_only(self, test_user):
        """Test placing a bid with interested_only flag."""
        # Arrange
        mock_db = AsyncMock()
        service = BidService(mock_db)

        run_id = uuid4()
        product_id = uuid4()
        group_id = uuid4()
        participation_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.PLANNING.value
        mock_run.group_id = group_id

        mock_product = Mock(spec=Product)
        mock_product.id = product_id

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.id = participation_id
        mock_participation.user_id = test_user.id
        mock_participation.is_leader = False

        mock_group = Mock()
        mock_group.id = group_id

        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.product_repo.get_product_by_id = AsyncMock(return_value=mock_product)
        service.user_repo.get_user_groups = AsyncMock(return_value=[mock_group])
        service.run_repo.get_participation = AsyncMock(return_value=mock_participation)
        service.bid_repo.get_bid = AsyncMock(return_value=None)
        service.bid_repo.get_bids_by_run = AsyncMock(return_value=[])
        service.bid_repo.create_or_update_bid = AsyncMock()

        with patch('app.services.bid_service.event_bus'):
            # Act
            result = await service.place_bid(
                run_id=str(run_id),
                product_id=str(product_id),
                quantity=0,
                interested_only=True,
                user=test_user,
            )

            # Assert
            assert result.interested_only is True
            assert result.quantity == 0

            service.bid_repo.create_or_update_bid.assert_called_once_with(
                participation_id, product_id, 0, True, None
            )

    async def test_place_bid_updates_existing_bid(self, test_user):
        """Test updating an existing bid quantity."""
        # Arrange
        mock_db = AsyncMock()
        service = BidService(mock_db)

        run_id = uuid4()
        product_id = uuid4()
        group_id = uuid4()
        participation_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.ACTIVE.value
        mock_run.group_id = group_id

        mock_product = Mock(spec=Product)
        mock_product.id = product_id

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.id = participation_id
        mock_participation.user_id = test_user.id

        mock_existing_bid = Mock(spec=ProductBid)
        mock_existing_bid.quantity = 3.0
        mock_existing_bid.interested_only = False

        mock_group = Mock()
        mock_group.id = group_id

        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.product_repo.get_product_by_id = AsyncMock(return_value=mock_product)
        service.user_repo.get_user_groups = AsyncMock(return_value=[mock_group])
        service.run_repo.get_participation = AsyncMock(return_value=mock_participation)
        service.bid_repo.get_bid = AsyncMock(return_value=mock_existing_bid)
        service.bid_repo.get_bids_by_run = AsyncMock(return_value=[mock_existing_bid])
        service.bid_repo.create_or_update_bid = AsyncMock()

        with patch('app.services.bid_service.event_bus'):
            # Act
            result = await service.place_bid(
                run_id=str(run_id),
                product_id=str(product_id),
                quantity=7.0,
                interested_only=False,
                user=test_user,
            )

            # Assert
            assert result.quantity == 7.0
            service.bid_repo.create_or_update_bid.assert_called_once()

    async def test_place_bid_creates_participation_if_needed(self, test_user):
        """Test auto-creates participation if user is not yet a participant."""
        # Arrange
        mock_db = AsyncMock()
        service = BidService(mock_db)

        run_id = uuid4()
        product_id = uuid4()
        group_id = uuid4()
        new_participation_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.ACTIVE.value
        mock_run.group_id = group_id

        mock_product = Mock(spec=Product)
        mock_product.id = product_id

        mock_new_participation = Mock(spec=RunParticipation)
        mock_new_participation.id = new_participation_id
        mock_new_participation.user_id = test_user.id
        mock_new_participation.is_leader = False

        mock_group = Mock()
        mock_group.id = group_id

        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.product_repo.get_product_by_id = AsyncMock(return_value=mock_product)
        service.user_repo.get_user_groups = AsyncMock(return_value=[mock_group])
        service.run_repo.get_participation = AsyncMock(return_value=None)
        service.run_repo.create_participation = AsyncMock(return_value=mock_new_participation)
        service.bid_repo.get_bid = AsyncMock(return_value=None)
        service.bid_repo.get_bids_by_run = AsyncMock(return_value=[])
        service.bid_repo.create_or_update_bid = AsyncMock()

        with patch('app.services.bid_service.event_bus'):
            # Act
            await service.place_bid(
                run_id=str(run_id),
                product_id=str(product_id),
                quantity=2.0,
                interested_only=False,
                user=test_user,
            )

            # Assert
            service.run_repo.create_participation.assert_called_once_with(
                test_user.id, run_id, is_leader=False
            )

    async def test_place_bid_with_existing_participation(self, test_user):
        """Test with existing participation - does not create new one."""
        # Arrange
        mock_db = AsyncMock()
        service = BidService(mock_db)

        run_id = uuid4()
        product_id = uuid4()
        group_id = uuid4()
        participation_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.ACTIVE.value
        mock_run.group_id = group_id

        mock_product = Mock(spec=Product)
        mock_product.id = product_id

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.id = participation_id
        mock_participation.user_id = test_user.id

        mock_group = Mock()
        mock_group.id = group_id

        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.product_repo.get_product_by_id = AsyncMock(return_value=mock_product)
        service.user_repo.get_user_groups = AsyncMock(return_value=[mock_group])
        service.run_repo.get_participation = AsyncMock(return_value=mock_participation)
        service.bid_repo.get_bid = AsyncMock(return_value=None)
        service.bid_repo.get_bids_by_run = AsyncMock(return_value=[])
        service.bid_repo.create_or_update_bid = AsyncMock()
        service.run_repo.create_participation = AsyncMock()

        with patch('app.services.bid_service.event_bus'):
            # Act
            await service.place_bid(
                run_id=str(run_id),
                product_id=str(product_id),
                quantity=2.0,
                interested_only=False,
                user=test_user,
            )

            # Assert
            service.run_repo.create_participation.assert_not_called()

    async def test_place_bid_emits_bid_placed_event(self, test_user):
        """Test BidPlacedEvent is emitted with correct data."""
        # Arrange
        mock_db = AsyncMock()
        service = BidService(mock_db)

        run_id = uuid4()
        product_id = uuid4()
        group_id = uuid4()
        participation_id = uuid4()
        quantity = 5.0

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.ACTIVE.value
        mock_run.group_id = group_id

        mock_product = Mock(spec=Product)
        mock_product.id = product_id

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.id = participation_id
        mock_participation.user_id = test_user.id

        mock_group = Mock()
        mock_group.id = group_id

        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.product_repo.get_product_by_id = AsyncMock(return_value=mock_product)
        service.user_repo.get_user_groups = AsyncMock(return_value=[mock_group])
        service.run_repo.get_participation = AsyncMock(return_value=mock_participation)
        service.bid_repo.get_bid = AsyncMock(return_value=None)
        service.bid_repo.get_bids_by_run = AsyncMock(return_value=[])
        service.bid_repo.create_or_update_bid = AsyncMock()

        with patch('app.services.bid_service.event_bus') as mock_event_bus:
            # Act
            await service.place_bid(
                run_id=str(run_id),
                product_id=str(product_id),
                quantity=quantity,
                interested_only=False,
                user=test_user,
            )

            # Assert
            mock_event_bus.emit.assert_called_once()
            event = mock_event_bus.emit.call_args[0][0]
            assert isinstance(event, BidPlacedEvent)
            assert event.run_id == run_id
            assert event.product_id == product_id
            assert event.user_id == test_user.id
            assert event.user_name == test_user.name
            assert event.quantity == quantity
            assert event.interested_only is False
            assert event.new_total == 0.0
            assert event.group_id == group_id

    async def test_place_bid_not_group_member(self, test_user):
        """Test authorization - user must be group member."""
        # Arrange
        mock_db = AsyncMock()
        service = BidService(mock_db)

        run_id = uuid4()
        product_id = uuid4()
        group_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.ACTIVE.value
        mock_run.group_id = group_id

        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.user_repo.get_user_groups = AsyncMock(return_value=[])  # Not a member

        # Act & Assert
        with pytest.raises(ForbiddenError) as exc_info:
            await service.place_bid(
                run_id=str(run_id),
                product_id=str(product_id),
                quantity=2.0,
                interested_only=False,
                user=test_user,
            )

        assert exc_info.value.code == NOT_RUN_PARTICIPANT

    async def test_place_bid_run_not_found(self, test_user):
        """Test placing bid on non-existent run raises NotFoundError."""
        # Arrange
        mock_db = AsyncMock()
        service = BidService(mock_db)

        run_id = uuid4()
        product_id = uuid4()

        service.run_repo.get_run_by_id = AsyncMock(return_value=None)

        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.place_bid(
                run_id=str(run_id),
                product_id=str(product_id),
                quantity=2.0,
                interested_only=False,
                user=test_user,
            )

        assert exc_info.value.code == RUN_NOT_FOUND

    async def test_place_bid_product_not_found(self, test_user):
        """Test placing bid on non-existent product raises NotFoundError."""
        # Arrange
        mock_db = AsyncMock()
        service = BidService(mock_db)

        run_id = uuid4()
        product_id = uuid4()
        group_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.ACTIVE.value
        mock_run.group_id = group_id

        mock_group = Mock()
        mock_group.id = group_id

        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.user_repo.get_user_groups = AsyncMock(return_value=[mock_group])
        service.product_repo.get_product_by_id = AsyncMock(return_value=None)

        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.place_bid(
                run_id=str(run_id),
                product_id=str(product_id),
                quantity=2.0,
                interested_only=False,
                user=test_user,
            )

        assert exc_info.value.code == PRODUCT_NOT_FOUND

    async def test_place_bid_negative_quantity(self, test_user):
        """Test placing bid with negative quantity raises ValidationError."""
        # Arrange
        mock_db = AsyncMock()
        service = BidService(mock_db)

        run_id = uuid4()
        product_id = uuid4()
        group_id = uuid4()
        participation_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.ACTIVE.value
        mock_run.group_id = group_id

        mock_product = Mock(spec=Product)
        mock_product.id = product_id

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.id = participation_id

        mock_group = Mock()
        mock_group.id = group_id

        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.product_repo.get_product_by_id = AsyncMock(return_value=mock_product)
        service.user_repo.get_user_groups = AsyncMock(return_value=[mock_group])
        service.run_repo.get_participation = AsyncMock(return_value=mock_participation)

        # Act & Assert
        with pytest.raises(BadRequestError) as exc_info:
            await service.place_bid(
                run_id=str(run_id),
                product_id=str(product_id),
                quantity=-5.0,
                interested_only=False,
                user=test_user,
            )

        assert exc_info.value.code == BID_QUANTITY_NEGATIVE

    async def test_place_bid_zero_quantity_removes_bid(self, test_user):
        """Test placing bid with quantity=0 removes existing bid."""
        # Arrange
        mock_db = AsyncMock()
        service = BidService(mock_db)

        run_id = uuid4()
        product_id = uuid4()
        group_id = uuid4()
        participation_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.ACTIVE.value
        mock_run.group_id = group_id

        mock_product = Mock(spec=Product)
        mock_product.id = product_id

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.id = participation_id
        mock_participation.user_id = test_user.id

        mock_existing_bid = Mock(spec=ProductBid)
        mock_existing_bid.quantity = 3.0

        mock_group = Mock()
        mock_group.id = group_id

        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.product_repo.get_product_by_id = AsyncMock(return_value=mock_product)
        service.user_repo.get_user_groups = AsyncMock(return_value=[mock_group])
        service.run_repo.get_participation = AsyncMock(return_value=mock_participation)
        service.bid_repo.get_bid = AsyncMock(return_value=mock_existing_bid)
        service.bid_repo.get_bids_by_run = AsyncMock(return_value=[])
        service.bid_repo.delete_bid = AsyncMock()

        with patch('app.services.bid_service.event_bus'):
            # Act
            await service.place_bid(
                run_id=str(run_id),
                product_id=str(product_id),
                quantity=0,
                interested_only=False,
                user=test_user,
            )

            # Assert
            service.bid_repo.delete_bid.assert_called_once_with(participation_id, product_id)

    async def test_place_bid_transitions_planning_to_active(self, test_user):
        """Test automatic state transition from planning to active when non-leader joins."""
        # Arrange
        mock_db = AsyncMock()
        service = BidService(mock_db)

        run_id = uuid4()
        product_id = uuid4()
        group_id = uuid4()
        participation_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.PLANNING.value
        mock_run.group_id = group_id

        mock_product = Mock(spec=Product)
        mock_product.id = product_id

        mock_new_participation = Mock(spec=RunParticipation)
        mock_new_participation.id = participation_id
        mock_new_participation.user_id = test_user.id
        mock_new_participation.is_leader = False

        mock_group = Mock()
        mock_group.id = group_id

        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.product_repo.get_product_by_id = AsyncMock(return_value=mock_product)
        service.user_repo.get_user_groups = AsyncMock(return_value=[mock_group])
        service.run_repo.get_participation = AsyncMock(return_value=None)
        service.run_repo.create_participation = AsyncMock(return_value=mock_new_participation)
        service.run_repo.update_run_state = AsyncMock()
        service.bid_repo.get_bid = AsyncMock(return_value=None)
        service.bid_repo.get_bids_by_run = AsyncMock(return_value=[])
        service.bid_repo.create_or_update_bid = AsyncMock()

        with patch('app.services.bid_service.event_bus'):
            # Act
            result = await service.place_bid(
                run_id=str(run_id),
                product_id=str(product_id),
                quantity=2.0,
                interested_only=False,
                user=test_user,
            )

            # Assert
            assert result.state_changed is True
            assert result.new_state == RunState.ACTIVE.value
            service.run_repo.update_run_state.assert_called_once_with(run_id, RunState.ACTIVE)

    async def test_place_bid_max_products_exceeded(self, test_user):
        """Test cannot add bid for new product when max products reached."""
        # Arrange
        mock_db = AsyncMock()
        service = BidService(mock_db)

        run_id = uuid4()
        product_id = uuid4()
        group_id = uuid4()
        participation_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.ACTIVE.value
        mock_run.group_id = group_id

        mock_product = Mock(spec=Product)
        mock_product.id = product_id

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.id = participation_id

        mock_group = Mock()
        mock_group.id = group_id

        # Create max number of existing bids on different products
        existing_bids = []
        for _ in range(100):  # MAX_PRODUCTS_PER_RUN = 100
            mock_bid = Mock(spec=ProductBid)
            mock_bid.product_id = uuid4()
            existing_bids.append(mock_bid)

        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.product_repo.get_product_by_id = AsyncMock(return_value=mock_product)
        service.user_repo.get_user_groups = AsyncMock(return_value=[mock_group])
        service.run_repo.get_participation = AsyncMock(return_value=mock_participation)
        service.bid_repo.get_bid = AsyncMock(return_value=None)  # New bid
        service.bid_repo.get_bids_by_run = AsyncMock(return_value=existing_bids)

        # Act & Assert
        with pytest.raises(BadRequestError) as exc_info:
            await service.place_bid(
                run_id=str(run_id),
                product_id=str(product_id),
                quantity=2.0,
                interested_only=False,
                user=test_user,
            )

        assert exc_info.value.code == RUN_MAX_PRODUCTS_EXCEEDED


class TestRetractBid:
    """Test cases for BidService.retract_bid()."""

    async def test_retract_existing_bid(self, test_user):
        """Test retracting an existing bid."""
        # Arrange
        mock_db = AsyncMock()
        service = BidService(mock_db)

        run_id = uuid4()
        product_id = uuid4()
        group_id = uuid4()
        participation_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.ACTIVE.value
        mock_run.group_id = group_id

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.id = participation_id
        mock_participation.user_id = test_user.id

        mock_bid = Mock(spec=ProductBid)
        mock_bid.product_id = product_id
        mock_bid.quantity = 5.0

        mock_group = Mock()
        mock_group.id = group_id

        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.user_repo.get_user_groups = AsyncMock(return_value=[mock_group])
        service.run_repo.get_participation = AsyncMock(return_value=mock_participation)
        service.bid_repo.get_bid = AsyncMock(return_value=mock_bid)
        service.bid_repo.delete_bid = AsyncMock()
        service.bid_repo.get_bids_by_run = AsyncMock(return_value=[])
        service.shopping_repo.get_shopping_list_items = AsyncMock(return_value=[])

        with patch('app.services.bid_service.event_bus') as mock_event_bus:
            # Act
            result = await service.retract_bid(
                run_id=str(run_id), product_id=str(product_id), user=test_user
            )

            # Assert
            assert result is not None
            assert result.code == BID_RETRACTED
            assert result.run_id == str(run_id)
            assert result.product_id == str(product_id)
            assert result.user_id == str(test_user.id)
            assert result.new_total == 0.0

            service.bid_repo.delete_bid.assert_called_once_with(participation_id, product_id)

            # Verify event emitted
            mock_event_bus.emit.assert_called_once()
            event = mock_event_bus.emit.call_args[0][0]
            assert isinstance(event, BidRetractedEvent)

    async def test_retract_bid_emits_bid_retracted_event(self, test_user):
        """Test BidRetractedEvent is emitted with correct data."""
        # Arrange
        mock_db = AsyncMock()
        service = BidService(mock_db)

        run_id = uuid4()
        product_id = uuid4()
        group_id = uuid4()
        participation_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.ACTIVE.value
        mock_run.group_id = group_id

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.id = participation_id

        mock_bid = Mock(spec=ProductBid)
        mock_bid.product_id = product_id
        mock_bid.quantity = 5.0

        mock_group = Mock()
        mock_group.id = group_id

        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.user_repo.get_user_groups = AsyncMock(return_value=[mock_group])
        service.run_repo.get_participation = AsyncMock(return_value=mock_participation)
        service.bid_repo.get_bid = AsyncMock(return_value=mock_bid)
        service.bid_repo.delete_bid = AsyncMock()
        service.bid_repo.get_bids_by_run = AsyncMock(return_value=[])
        service.shopping_repo.get_shopping_list_items = AsyncMock(return_value=[])

        with patch('app.services.bid_service.event_bus') as mock_event_bus:
            # Act
            await service.retract_bid(
                run_id=str(run_id), product_id=str(product_id), user=test_user
            )

            # Assert
            mock_event_bus.emit.assert_called_once()
            event = mock_event_bus.emit.call_args[0][0]
            assert isinstance(event, BidRetractedEvent)
            assert event.run_id == run_id
            assert event.product_id == product_id
            assert event.user_id == test_user.id
            assert event.new_total == 0.0
            assert event.group_id == group_id

    async def test_retract_bid_not_found(self, test_user):
        """Test retracting non-existent bid raises NotFoundError."""
        # Arrange
        mock_db = AsyncMock()
        service = BidService(mock_db)

        run_id = uuid4()
        product_id = uuid4()
        group_id = uuid4()
        participation_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.ACTIVE.value
        mock_run.group_id = group_id

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.id = participation_id

        mock_group = Mock()
        mock_group.id = group_id

        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.user_repo.get_user_groups = AsyncMock(return_value=[mock_group])
        service.run_repo.get_participation = AsyncMock(return_value=mock_participation)
        service.bid_repo.get_bid = AsyncMock(return_value=None)
        service.shopping_repo.get_shopping_list_items = AsyncMock(return_value=[])

        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.retract_bid(
                run_id=str(run_id), product_id=str(product_id), user=test_user
            )

        assert exc_info.value.code == BID_NOT_FOUND

    async def test_retract_bid_not_group_member(self, test_user):
        """Test only group members can retract bids."""
        # Arrange
        mock_db = AsyncMock()
        service = BidService(mock_db)

        run_id = uuid4()
        product_id = uuid4()
        group_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.ACTIVE.value
        mock_run.group_id = group_id

        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.user_repo.get_user_groups = AsyncMock(return_value=[])  # Not a member

        # Act & Assert
        with pytest.raises(ForbiddenError) as exc_info:
            await service.retract_bid(
                run_id=str(run_id), product_id=str(product_id), user=test_user
            )

        assert exc_info.value.code == NOT_RUN_PARTICIPANT

    async def test_retract_bid_run_not_found(self, test_user):
        """Test retracting bid on non-existent run."""
        # Arrange
        mock_db = AsyncMock()
        service = BidService(mock_db)

        run_id = uuid4()
        product_id = uuid4()

        service.run_repo.get_run_by_id = AsyncMock(return_value=None)

        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.retract_bid(
                run_id=str(run_id), product_id=str(product_id), user=test_user
            )

        assert exc_info.value.code == RUN_NOT_FOUND

    async def test_retract_bid_participation_not_found(self, test_user):
        """Test retracting bid when user has no participation."""
        # Arrange
        mock_db = AsyncMock()
        service = BidService(mock_db)

        run_id = uuid4()
        product_id = uuid4()
        group_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.ACTIVE.value
        mock_run.group_id = group_id

        mock_group = Mock()
        mock_group.id = group_id

        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.user_repo.get_user_groups = AsyncMock(return_value=[mock_group])
        service.run_repo.get_participation = AsyncMock(return_value=None)
        service.shopping_repo.get_shopping_list_items = AsyncMock(return_value=[])

        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.retract_bid(
                run_id=str(run_id), product_id=str(product_id), user=test_user
            )

        assert exc_info.value.code == PARTICIPATION_NOT_FOUND

    async def test_retract_bid_recalculates_totals(self, test_user):
        """Test bid retraction recalculates product totals."""
        # Arrange
        mock_db = AsyncMock()
        service = BidService(mock_db)

        run_id = uuid4()
        product_id = uuid4()
        group_id = uuid4()
        participation_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.ACTIVE.value
        mock_run.group_id = group_id

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.id = participation_id

        mock_bid = Mock(spec=ProductBid)
        mock_bid.product_id = product_id
        mock_bid.quantity = 5.0

        # Other user's bid
        mock_other_bid = Mock(spec=ProductBid)
        mock_other_bid.product_id = product_id
        mock_other_bid.quantity = 3.0
        mock_other_bid.interested_only = False

        mock_group = Mock()
        mock_group.id = group_id

        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.user_repo.get_user_groups = AsyncMock(return_value=[mock_group])
        service.run_repo.get_participation = AsyncMock(return_value=mock_participation)
        service.bid_repo.get_bid = AsyncMock(return_value=mock_bid)
        service.bid_repo.delete_bid = AsyncMock()
        service.bid_repo.get_bids_by_run = AsyncMock(return_value=[mock_other_bid])
        service.shopping_repo.get_shopping_list_items = AsyncMock(return_value=[])

        with patch('app.services.bid_service.event_bus'):
            # Act
            result = await service.retract_bid(
                run_id=str(run_id), product_id=str(product_id), user=test_user
            )

            # Assert - should reflect remaining bid
            assert result.new_total == 3.0

    async def test_retract_bid_invalid_state(self, test_user):
        """Test cannot retract bid in invalid states."""
        # Arrange
        mock_db = AsyncMock()
        service = BidService(mock_db)

        run_id = uuid4()
        product_id = uuid4()
        group_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.COMPLETED.value
        mock_run.group_id = group_id

        mock_group = Mock()
        mock_group.id = group_id

        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.user_repo.get_user_groups = AsyncMock(return_value=[mock_group])

        # Act & Assert
        with pytest.raises(BadRequestError) as exc_info:
            await service.retract_bid(
                run_id=str(run_id), product_id=str(product_id), user=test_user
            )

        assert exc_info.value.code == CANNOT_RETRACT_BID_IN_ADJUSTING


class TestStateValidation:
    """Test cases for state-based bid validation."""

    async def test_can_bid_in_planning(self, test_user):
        """Test can place bid in PLANNING state."""
        # Arrange
        mock_db = AsyncMock()
        service = BidService(mock_db)

        run_id = uuid4()
        product_id = uuid4()
        group_id = uuid4()
        participation_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.PLANNING.value
        mock_run.group_id = group_id

        mock_product = Mock(spec=Product)
        mock_product.id = product_id

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.id = participation_id

        mock_group = Mock()
        mock_group.id = group_id

        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.product_repo.get_product_by_id = AsyncMock(return_value=mock_product)
        service.user_repo.get_user_groups = AsyncMock(return_value=[mock_group])
        service.run_repo.get_participation = AsyncMock(return_value=mock_participation)
        service.bid_repo.get_bid = AsyncMock(return_value=None)
        service.bid_repo.get_bids_by_run = AsyncMock(return_value=[])
        service.bid_repo.create_or_update_bid = AsyncMock()

        with patch('app.services.bid_service.event_bus'):
            # Act - should not raise
            result = await service.place_bid(
                run_id=str(run_id),
                product_id=str(product_id),
                quantity=2.0,
                interested_only=False,
                user=test_user,
            )

            # Assert
            assert result is not None

    async def test_can_bid_in_active(self, test_user):
        """Test can place bid in ACTIVE state."""
        # Arrange
        mock_db = AsyncMock()
        service = BidService(mock_db)

        run_id = uuid4()
        product_id = uuid4()
        group_id = uuid4()
        participation_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.ACTIVE.value
        mock_run.group_id = group_id

        mock_product = Mock(spec=Product)
        mock_product.id = product_id

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.id = participation_id

        mock_group = Mock()
        mock_group.id = group_id

        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.product_repo.get_product_by_id = AsyncMock(return_value=mock_product)
        service.user_repo.get_user_groups = AsyncMock(return_value=[mock_group])
        service.run_repo.get_participation = AsyncMock(return_value=mock_participation)
        service.bid_repo.get_bid = AsyncMock(return_value=None)
        service.bid_repo.get_bids_by_run = AsyncMock(return_value=[])
        service.bid_repo.create_or_update_bid = AsyncMock()

        with patch('app.services.bid_service.event_bus'):
            # Act - should not raise
            result = await service.place_bid(
                run_id=str(run_id),
                product_id=str(product_id),
                quantity=2.0,
                interested_only=False,
                user=test_user,
            )

            # Assert
            assert result is not None

    async def test_can_bid_in_adjusting_with_existing_bid(self, test_user):
        """Test can adjust existing bid in ADJUSTING state."""
        # Arrange
        mock_db = AsyncMock()
        service = BidService(mock_db)

        run_id = uuid4()
        product_id = uuid4()
        group_id = uuid4()
        participation_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.ADJUSTING.value
        mock_run.group_id = group_id

        mock_product = Mock(spec=Product)
        mock_product.id = product_id

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.id = participation_id

        mock_existing_bid = Mock(spec=ProductBid)
        mock_existing_bid.quantity = 10.0
        mock_existing_bid.product_id = product_id

        # Mock shopping list with surplus
        mock_shopping_item = Mock()
        mock_shopping_item.product_id = product_id
        mock_shopping_item.purchased_quantity = 15.0
        mock_shopping_item.requested_quantity = 10.0  # surplus = 5

        mock_group = Mock()
        mock_group.id = group_id

        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.product_repo.get_product_by_id = AsyncMock(return_value=mock_product)
        service.user_repo.get_user_groups = AsyncMock(return_value=[mock_group])
        service.run_repo.get_participation = AsyncMock(return_value=mock_participation)
        service.bid_repo.get_bid = AsyncMock(return_value=mock_existing_bid)
        service.bid_repo.get_bids_by_run = AsyncMock(return_value=[mock_existing_bid])
        service.shopping_repo.get_shopping_list_items = AsyncMock(return_value=[mock_shopping_item])
        service.bid_repo.create_or_update_bid = AsyncMock()

        with patch('app.services.bid_service.event_bus'):
            # Act - increase bid (allowed with surplus)
            result = await service.place_bid(
                run_id=str(run_id),
                product_id=str(product_id),
                quantity=12.0,
                interested_only=False,
                user=test_user,
            )

            # Assert
            assert result is not None

    @pytest.mark.parametrize(
        'state',
        [
            RunState.CONFIRMED.value,
            RunState.SHOPPING.value,
            RunState.DISTRIBUTING.value,
            RunState.COMPLETED.value,
            RunState.CANCELLED.value,
        ],
    )
    async def test_cannot_bid_in_invalid_states(self, test_user, state):
        """Test cannot place bid in invalid states."""
        # Arrange
        mock_db = AsyncMock()
        service = BidService(mock_db)

        run_id = uuid4()
        product_id = uuid4()
        group_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = state
        mock_run.group_id = group_id

        mock_group = Mock()
        mock_group.id = group_id

        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.user_repo.get_user_groups = AsyncMock(return_value=[mock_group])

        # Act & Assert
        with pytest.raises(BadRequestError) as exc_info:
            await service.place_bid(
                run_id=str(run_id),
                product_id=str(product_id),
                quantity=2.0,
                interested_only=False,
                user=test_user,
            )

        assert exc_info.value.code == INVALID_RUN_STATE_TRANSITION

    async def test_cannot_join_run_in_adjusting(self, test_user):
        """Test cannot create new participation in ADJUSTING state."""
        # Arrange
        mock_db = AsyncMock()
        service = BidService(mock_db)

        run_id = uuid4()
        product_id = uuid4()
        group_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.ADJUSTING.value
        mock_run.group_id = group_id

        mock_product = Mock(spec=Product)
        mock_product.id = product_id

        mock_group = Mock()
        mock_group.id = group_id

        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.product_repo.get_product_by_id = AsyncMock(return_value=mock_product)
        service.user_repo.get_user_groups = AsyncMock(return_value=[mock_group])
        service.run_repo.get_participation = AsyncMock(return_value=None)  # No participation

        # Act & Assert
        with pytest.raises(BadRequestError) as exc_info:
            await service.place_bid(
                run_id=str(run_id),
                product_id=str(product_id),
                quantity=2.0,
                interested_only=False,
                user=test_user,
            )

        assert exc_info.value.code == CANNOT_JOIN_RUN_IN_ADJUSTING_STATE

    async def test_cannot_bid_new_product_in_adjusting_without_surplus(self, test_user):
        """Test cannot place bid on new product in ADJUSTING without surplus."""
        # Arrange
        mock_db = AsyncMock()
        service = BidService(mock_db)

        run_id = uuid4()
        product_id = uuid4()
        group_id = uuid4()
        participation_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.ADJUSTING.value
        mock_run.group_id = group_id

        mock_product = Mock(spec=Product)
        mock_product.id = product_id

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.id = participation_id

        # Mock shopping list with NO surplus (shortage)
        mock_shopping_item = Mock()
        mock_shopping_item.product_id = product_id
        mock_shopping_item.purchased_quantity = 8.0
        mock_shopping_item.requested_quantity = 10.0  # shortage = 2

        mock_group = Mock()
        mock_group.id = group_id

        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.product_repo.get_product_by_id = AsyncMock(return_value=mock_product)
        service.user_repo.get_user_groups = AsyncMock(return_value=[mock_group])
        service.run_repo.get_participation = AsyncMock(return_value=mock_participation)
        service.bid_repo.get_bid = AsyncMock(return_value=None)  # No existing bid
        service.bid_repo.get_bids_by_run = AsyncMock(return_value=[])
        service.shopping_repo.get_shopping_list_items = AsyncMock(return_value=[mock_shopping_item])

        # Act & Assert
        with pytest.raises(BadRequestError) as exc_info:
            await service.place_bid(
                run_id=str(run_id),
                product_id=str(product_id),
                quantity=2.0,
                interested_only=False,
                user=test_user,
            )

        assert exc_info.value.code == CANNOT_BID_NEW_PRODUCT_IN_ADJUSTING


class TestCalculateProductTotal:
    """Test cases for BidService.calculate_product_total()."""

    async def test_calculate_total_with_multiple_bids(self):
        """Test calculating total quantity for a product."""
        # Arrange
        mock_db = AsyncMock()
        service = BidService(mock_db)

        run_id = uuid4()
        product_id = uuid4()

        mock_bid1 = Mock(spec=ProductBid)
        mock_bid1.product_id = product_id
        mock_bid1.quantity = 5.0
        mock_bid1.interested_only = False

        mock_bid2 = Mock(spec=ProductBid)
        mock_bid2.product_id = product_id
        mock_bid2.quantity = 3.0
        mock_bid2.interested_only = False

        mock_bid3 = Mock(spec=ProductBid)
        mock_bid3.product_id = uuid4()  # Different product
        mock_bid3.quantity = 7.0
        mock_bid3.interested_only = False

        service.bid_repo.get_bids_by_run = AsyncMock(return_value=[mock_bid1, mock_bid2, mock_bid3])

        # Act
        total = await service.calculate_product_total(run_id, product_id)

        # Assert
        assert total == 8.0  # 5.0 + 3.0

    async def test_calculate_total_excludes_interested_only(self):
        """Test excludes interested_only from totals."""
        # Arrange
        mock_db = AsyncMock()
        service = BidService(mock_db)

        run_id = uuid4()
        product_id = uuid4()

        mock_bid1 = Mock(spec=ProductBid)
        mock_bid1.product_id = product_id
        mock_bid1.quantity = 5.0
        mock_bid1.interested_only = False

        mock_bid2 = Mock(spec=ProductBid)
        mock_bid2.product_id = product_id
        mock_bid2.quantity = 0.0
        mock_bid2.interested_only = True  # Should be excluded

        service.bid_repo.get_bids_by_run = AsyncMock(return_value=[mock_bid1, mock_bid2])

        # Act
        total = await service.calculate_product_total(run_id, product_id)

        # Assert
        assert total == 5.0  # Only the first bid

    async def test_calculate_total_includes_all_quantity_bids(self):
        """Test includes all quantity bids."""
        # Arrange
        mock_db = AsyncMock()
        service = BidService(mock_db)

        run_id = uuid4()
        product_id = uuid4()

        mock_bids = []
        for i in range(5):
            mock_bid = Mock(spec=ProductBid)
            mock_bid.product_id = product_id
            mock_bid.quantity = float(i + 1)
            mock_bid.interested_only = False
            mock_bids.append(mock_bid)

        service.bid_repo.get_bids_by_run = AsyncMock(return_value=mock_bids)

        # Act
        total = await service.calculate_product_total(run_id, product_id)

        # Assert
        assert total == 15.0  # 1+2+3+4+5

    async def test_calculate_total_zero_when_no_bids(self):
        """Test zero when no bids exist."""
        # Arrange
        mock_db = AsyncMock()
        service = BidService(mock_db)

        run_id = uuid4()
        product_id = uuid4()

        service.bid_repo.get_bids_by_run = AsyncMock(return_value=[])

        # Act
        total = await service.calculate_product_total(run_id, product_id)

        # Assert
        assert total == 0.0

    async def test_calculate_total_after_bid_retraction(self):
        """Test total recalculates correctly after bid retraction."""
        # Arrange
        mock_db = AsyncMock()
        service = BidService(mock_db)

        run_id = uuid4()
        product_id = uuid4()

        # Only one bid remains
        mock_bid = Mock(spec=ProductBid)
        mock_bid.product_id = product_id
        mock_bid.quantity = 3.0
        mock_bid.interested_only = False

        service.bid_repo.get_bids_by_run = AsyncMock(return_value=[mock_bid])

        # Act
        total = await service.calculate_product_total(run_id, product_id)

        # Assert
        assert total == 3.0


class TestParticipationManagement:
    """Test cases for participation management."""

    async def test_auto_creates_participation_on_first_bid(self, test_user):
        """Test auto-creates participation on first bid."""
        # Arrange
        mock_db = AsyncMock()
        service = BidService(mock_db)

        run_id = uuid4()
        product_id = uuid4()
        group_id = uuid4()
        new_participation_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.ACTIVE.value
        mock_run.group_id = group_id

        mock_product = Mock(spec=Product)
        mock_product.id = product_id

        mock_new_participation = Mock(spec=RunParticipation)
        mock_new_participation.id = new_participation_id
        mock_new_participation.user_id = test_user.id
        mock_new_participation.is_leader = False

        mock_group = Mock()
        mock_group.id = group_id

        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.product_repo.get_product_by_id = AsyncMock(return_value=mock_product)
        service.user_repo.get_user_groups = AsyncMock(return_value=[mock_group])
        service.run_repo.get_participation = AsyncMock(return_value=None)
        service.run_repo.create_participation = AsyncMock(return_value=mock_new_participation)
        service.bid_repo.get_bid = AsyncMock(return_value=None)
        service.bid_repo.get_bids_by_run = AsyncMock(return_value=[])
        service.bid_repo.create_or_update_bid = AsyncMock()

        with patch('app.services.bid_service.event_bus'):
            # Act
            await service.place_bid(
                run_id=str(run_id),
                product_id=str(product_id),
                quantity=2.0,
                interested_only=False,
                user=test_user,
            )

            # Assert
            service.run_repo.create_participation.assert_called_once_with(
                test_user.id, run_id, is_leader=False
            )

    async def test_reuses_existing_participation(self, test_user):
        """Test reuses existing participation."""
        # Arrange
        mock_db = AsyncMock()
        service = BidService(mock_db)

        run_id = uuid4()
        product_id = uuid4()
        group_id = uuid4()
        participation_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.ACTIVE.value
        mock_run.group_id = group_id

        mock_product = Mock(spec=Product)
        mock_product.id = product_id

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.id = participation_id
        mock_participation.user_id = test_user.id

        mock_group = Mock()
        mock_group.id = group_id

        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.product_repo.get_product_by_id = AsyncMock(return_value=mock_product)
        service.user_repo.get_user_groups = AsyncMock(return_value=[mock_group])
        service.run_repo.get_participation = AsyncMock(return_value=mock_participation)
        service.run_repo.create_participation = AsyncMock()
        service.bid_repo.get_bid = AsyncMock(return_value=None)
        service.bid_repo.get_bids_by_run = AsyncMock(return_value=[])
        service.bid_repo.create_or_update_bid = AsyncMock()

        with patch('app.services.bid_service.event_bus'):
            # Act
            await service.place_bid(
                run_id=str(run_id),
                product_id=str(product_id),
                quantity=2.0,
                interested_only=False,
                user=test_user,
            )

            # Assert
            service.run_repo.create_participation.assert_not_called()

    async def test_participation_created_as_non_leader(self, test_user):
        """Test participation created with is_leader=False."""
        # Arrange
        mock_db = AsyncMock()
        service = BidService(mock_db)

        run_id = uuid4()
        product_id = uuid4()
        group_id = uuid4()
        new_participation_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.ACTIVE.value
        mock_run.group_id = group_id

        mock_product = Mock(spec=Product)
        mock_product.id = product_id

        mock_new_participation = Mock(spec=RunParticipation)
        mock_new_participation.id = new_participation_id
        mock_new_participation.user_id = test_user.id
        mock_new_participation.is_leader = False

        mock_group = Mock()
        mock_group.id = group_id

        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.product_repo.get_product_by_id = AsyncMock(return_value=mock_product)
        service.user_repo.get_user_groups = AsyncMock(return_value=[mock_group])
        service.run_repo.get_participation = AsyncMock(return_value=None)
        service.run_repo.create_participation = AsyncMock(return_value=mock_new_participation)
        service.bid_repo.get_bid = AsyncMock(return_value=None)
        service.bid_repo.get_bids_by_run = AsyncMock(return_value=[])
        service.bid_repo.create_or_update_bid = AsyncMock()

        with patch('app.services.bid_service.event_bus'):
            # Act
            await service.place_bid(
                run_id=str(run_id),
                product_id=str(product_id),
                quantity=2.0,
                interested_only=False,
                user=test_user,
            )

            # Assert
            call_args = service.run_repo.create_participation.call_args
            assert call_args[1]['is_leader'] is False


class TestEdgeCases:
    """Test cases for edge cases."""

    async def test_with_invalid_uuid_format_run(self, test_user):
        """Test with invalid UUID format for run."""
        # Arrange
        mock_db = AsyncMock()
        service = BidService(mock_db)

        # Act & Assert
        with pytest.raises(BadRequestError):
            await service.place_bid(
                run_id='invalid-uuid',
                product_id=str(uuid4()),
                quantity=2.0,
                interested_only=False,
                user=test_user,
            )

    async def test_with_invalid_uuid_format_product(self, test_user):
        """Test with invalid UUID format for product."""
        # Arrange
        mock_db = AsyncMock()
        service = BidService(mock_db)

        # Act & Assert
        with pytest.raises(BadRequestError):
            await service.place_bid(
                run_id=str(uuid4()),
                product_id='not-a-uuid',
                quantity=2.0,
                interested_only=False,
                user=test_user,
            )

    async def test_with_zero_quantity_no_existing_bid(self, test_user):
        """Test with zero quantity when no existing bid."""
        # Arrange
        mock_db = AsyncMock()
        service = BidService(mock_db)

        run_id = uuid4()
        product_id = uuid4()
        group_id = uuid4()
        participation_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.ACTIVE.value
        mock_run.group_id = group_id

        mock_product = Mock(spec=Product)
        mock_product.id = product_id

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.id = participation_id
        mock_participation.user_id = test_user.id

        mock_group = Mock()
        mock_group.id = group_id

        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.product_repo.get_product_by_id = AsyncMock(return_value=mock_product)
        service.user_repo.get_user_groups = AsyncMock(return_value=[mock_group])
        service.run_repo.get_participation = AsyncMock(return_value=mock_participation)
        service.bid_repo.get_bid = AsyncMock(return_value=None)
        service.bid_repo.get_bids_by_run = AsyncMock(return_value=[])
        service.bid_repo.delete_bid = AsyncMock()

        with patch('app.services.bid_service.event_bus'):
            # Act - should not try to delete non-existent bid
            await service.place_bid(
                run_id=str(run_id),
                product_id=str(product_id),
                quantity=0,
                interested_only=False,
                user=test_user,
            )

            # Assert
            service.bid_repo.delete_bid.assert_not_called()

    async def test_with_very_large_quantity(self, test_user):
        """Test with very large quantity."""
        # Arrange
        mock_db = AsyncMock()
        service = BidService(mock_db)

        run_id = uuid4()
        product_id = uuid4()
        group_id = uuid4()
        participation_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.ACTIVE.value
        mock_run.group_id = group_id

        mock_product = Mock(spec=Product)
        mock_product.id = product_id

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.id = participation_id
        mock_participation.user_id = test_user.id

        mock_group = Mock()
        mock_group.id = group_id

        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.product_repo.get_product_by_id = AsyncMock(return_value=mock_product)
        service.user_repo.get_user_groups = AsyncMock(return_value=[mock_group])
        service.run_repo.get_participation = AsyncMock(return_value=mock_participation)
        service.bid_repo.get_bid = AsyncMock(return_value=None)
        service.bid_repo.get_bids_by_run = AsyncMock(return_value=[])
        service.bid_repo.create_or_update_bid = AsyncMock()

        with patch('app.services.bid_service.event_bus'):
            # Act - should handle large numbers
            result = await service.place_bid(
                run_id=str(run_id),
                product_id=str(product_id),
                quantity=999999.99,
                interested_only=False,
                user=test_user,
            )

            # Assert
            assert result.quantity == 999999.99

    async def test_with_comment(self, test_user):
        """Test placing bid with comment."""
        # Arrange
        mock_db = AsyncMock()
        service = BidService(mock_db)

        run_id = uuid4()
        product_id = uuid4()
        group_id = uuid4()
        participation_id = uuid4()
        comment = 'I really need this product'

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.ACTIVE.value
        mock_run.group_id = group_id

        mock_product = Mock(spec=Product)
        mock_product.id = product_id

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.id = participation_id
        mock_participation.user_id = test_user.id

        mock_group = Mock()
        mock_group.id = group_id

        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.product_repo.get_product_by_id = AsyncMock(return_value=mock_product)
        service.user_repo.get_user_groups = AsyncMock(return_value=[mock_group])
        service.run_repo.get_participation = AsyncMock(return_value=mock_participation)
        service.bid_repo.get_bid = AsyncMock(return_value=None)
        service.bid_repo.get_bids_by_run = AsyncMock(return_value=[])
        service.bid_repo.create_or_update_bid = AsyncMock()

        with patch('app.services.bid_service.event_bus'):
            # Act
            await service.place_bid(
                run_id=str(run_id),
                product_id=str(product_id),
                quantity=2.0,
                interested_only=False,
                user=test_user,
                comment=comment,
            )

            # Assert
            service.bid_repo.create_or_update_bid.assert_called_once_with(
                participation_id, product_id, 2.0, False, comment
            )
