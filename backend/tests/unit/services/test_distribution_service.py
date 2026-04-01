"""Unit tests for DistributionService."""

from unittest.mock import Mock, patch
from uuid import uuid4

import pytest

from app.core.error_codes import (
    BID_NOT_FOUND,
    CANNOT_COMPLETE_DISTRIBUTION_UNPURCHASED_ITEMS,
    NOT_RUN_LEADER,
    NOT_RUN_LEADER_OR_HELPER,
    RUN_NOT_FOUND,
    RUN_NOT_IN_DISTRIBUTING_STATE,
)
from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.core.models import Product, ProductBid, Run, RunParticipation, User
from app.core.run_state import RunState
from app.services.distribution_service import DistributionService


class TestGetDistributionSummary:
    """Test cases for DistributionService.get_distribution_summary()."""

    def test_get_distribution_summary_success(self, test_user):
        """Test successfully getting distribution summary."""
        # Arrange
        mock_db = Mock()
        run_id = uuid4()
        bid_id = uuid4()
        product_id = uuid4()
        user_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.DISTRIBUTING

        mock_user = Mock(spec=User)
        mock_user.id = user_id
        mock_user.name = 'Test User'

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.user_id = user_id
        mock_participation.user = mock_user

        mock_product = Mock(spec=Product)
        mock_product.id = product_id
        mock_product.name = 'Apple'
        mock_product.unit = 'kg'

        mock_bid = Mock(spec=ProductBid)
        mock_bid.id = bid_id
        mock_bid.product_id = product_id
        mock_bid.interested_only = False
        mock_bid.distributed_quantity = 5.0
        mock_bid.distributed_price_per_unit = 1.99
        mock_bid.quantity = 5
        mock_bid.is_picked_up = False
        mock_bid.participation = mock_participation

        service = DistributionService(mock_db)
        service._validate_distribution_access = Mock()
        service.bid_repo.get_bids_by_run_with_participations = Mock(return_value=[mock_bid])
        service.product_repo.get_product_by_id = Mock(return_value=mock_product)

        # Act
        result = service.get_distribution_summary(run_id, test_user)

        # Assert
        assert len(result) == 1
        assert result[0].user_name == 'Test User'
        assert len(result[0].products) == 1
        assert result[0].products[0].product_name == 'Apple'
        assert result[0].all_picked_up is False

    def test_get_distribution_summary_skips_interested_only(self, test_user):
        """Test that interested-only bids are skipped."""
        # Arrange
        mock_db = Mock()
        run_id = uuid4()

        mock_bid = Mock(spec=ProductBid)
        mock_bid.interested_only = True

        service = DistributionService(mock_db)
        service._validate_distribution_access = Mock()
        service.bid_repo.get_bids_by_run_with_participations = Mock(return_value=[mock_bid])

        # Act
        result = service.get_distribution_summary(run_id, test_user)

        # Assert
        assert result == []

    def test_get_distribution_summary_run_not_found(self, test_user):
        """Test getting distribution for non-existent run."""
        # Arrange
        mock_db = Mock()
        run_id = uuid4()

        service = DistributionService(mock_db)
        service.run_repo.get_run_by_id = Mock(return_value=None)

        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            service.get_distribution_summary(run_id, test_user)

        assert exc_info.value.code == RUN_NOT_FOUND


class TestMarkPickedUp:
    """Test cases for DistributionService.mark_picked_up()."""

    def test_mark_picked_up_success(self, test_user):
        """Test successfully marking bid as picked up."""
        # Arrange
        mock_db = Mock()
        run_id = uuid4()
        bid_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.is_leader = True
        mock_participation.is_helper = False
        mock_participation.run_id = run_id
        mock_participation.user_id = test_user.id

        mock_bid = Mock(spec=ProductBid)
        mock_bid.id = bid_id
        mock_bid.is_picked_up = False
        mock_bid.participation = mock_participation

        service = DistributionService(mock_db)
        service.run_repo.get_run_by_id = Mock(return_value=mock_run)
        service.run_repo.get_participation = Mock(return_value=mock_participation)
        service.bid_repo.get_bid_by_id = Mock(return_value=mock_bid)
        service.bid_repo.commit_changes = Mock()

        with patch('app.services.distribution_service.event_bus'):
            # Act
            result = service.mark_picked_up(run_id, bid_id, test_user)

            # Assert
            assert mock_bid.is_picked_up is True
            assert result.details['bid_id'] == str(bid_id)

    def test_mark_picked_up_not_leader_or_helper(self, test_user):
        """Test marking picked up when user is not leader or helper."""
        # Arrange
        mock_db = Mock()
        run_id = uuid4()
        bid_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.is_leader = False
        mock_participation.is_helper = False

        service = DistributionService(mock_db)
        service.run_repo.get_run_by_id = Mock(return_value=mock_run)
        service.run_repo.get_participation = Mock(return_value=mock_participation)

        # Act & Assert
        with pytest.raises(ForbiddenError) as exc_info:
            service.mark_picked_up(run_id, bid_id, test_user)

        assert exc_info.value.code == NOT_RUN_LEADER_OR_HELPER

    def test_mark_picked_up_bid_not_found(self, test_user):
        """Test marking picked up for non-existent bid."""
        # Arrange
        mock_db = Mock()
        run_id = uuid4()
        bid_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.is_leader = True
        mock_participation.is_helper = False

        service = DistributionService(mock_db)
        service.run_repo.get_run_by_id = Mock(return_value=mock_run)
        service.run_repo.get_participation = Mock(return_value=mock_participation)
        service.bid_repo.get_bid_by_id = Mock(return_value=None)

        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            service.mark_picked_up(run_id, bid_id, test_user)

        assert exc_info.value.code == BID_NOT_FOUND


class TestCompleteDistribution:
    """Test cases for DistributionService.complete_distribution()."""

    def test_complete_distribution_not_leader(self, test_user):
        """Test completing distribution when user is not leader."""
        # Arrange
        mock_db = Mock()
        run_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.is_leader = False

        service = DistributionService(mock_db)
        service.run_repo.get_run_by_id = Mock(return_value=mock_run)
        service.run_repo.get_participation = Mock(return_value=mock_participation)

        # Act & Assert
        with pytest.raises(ForbiddenError) as exc_info:
            service.complete_distribution(run_id, test_user)

        assert exc_info.value.code == NOT_RUN_LEADER

    def test_complete_distribution_wrong_state(self, test_user):
        """Test completing distribution from wrong state."""
        # Arrange
        mock_db = Mock()
        run_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.SHOPPING

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.is_leader = True

        service = DistributionService(mock_db)
        service.run_repo.get_run_by_id = Mock(return_value=mock_run)
        service.run_repo.get_participation = Mock(return_value=mock_participation)

        # Act & Assert
        with pytest.raises(BadRequestError) as exc_info:
            service.complete_distribution(run_id, test_user)

        assert exc_info.value.code == RUN_NOT_IN_DISTRIBUTING_STATE

    def test_complete_distribution_items_not_picked_up(self, test_user):
        """Test completing distribution when items are not picked up."""
        # Arrange
        mock_db = Mock()
        run_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.DISTRIBUTING

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.is_leader = True

        mock_bid = Mock(spec=ProductBid)
        mock_bid.interested_only = False
        mock_bid.distributed_quantity = 5.0
        mock_bid.is_picked_up = False

        service = DistributionService(mock_db)
        service.run_repo.get_run_by_id = Mock(return_value=mock_run)
        service.run_repo.get_participation = Mock(return_value=mock_participation)
        service.bid_repo.get_bids_by_run = Mock(return_value=[mock_bid])

        # Act & Assert
        with pytest.raises(BadRequestError) as exc_info:
            service.complete_distribution(run_id, test_user)

        assert exc_info.value.code == CANNOT_COMPLETE_DISTRIBUTION_UNPURCHASED_ITEMS
