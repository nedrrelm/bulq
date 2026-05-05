"""Unit tests for ReassignmentService."""

from datetime import datetime
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from app.core.error_codes import (
    NOT_RUN_LEADER,
    REASSIGNMENT_CANNOT_TRANSFER_TO_SELF,
    REASSIGNMENT_NOT_CURRENT_LEADER,
    REASSIGNMENT_NOT_TARGET_USER,
    REASSIGNMENT_REQUEST_ALREADY_EXISTS,
    REASSIGNMENT_REQUEST_ALREADY_RESOLVED,
    REASSIGNMENT_REQUEST_NOT_FOUND,
    REASSIGNMENT_TARGET_NOT_PARTICIPANT,
    RUN_NOT_FOUND,
)
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.core.models import LeaderReassignmentRequest, Run, RunParticipation, Store, User
from app.services.reassignment_service import ReassignmentService


class TestRequestReassignment:
    """Test cases for ReassignmentService.request_reassignment()."""

    async def test_request_reassignment_success(self, test_user):
        """Test successfully requesting leader reassignment."""
        # Arrange
        mock_db = AsyncMock()
        run_id = uuid4()
        to_user_id = uuid4()
        request_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.store_id = uuid4()

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.is_leader = True

        mock_to_user = Mock(spec=User)
        mock_to_user.id = to_user_id
        mock_to_user.name = 'Target User'

        mock_store = Mock(spec=Store)
        mock_store.name = 'Test Store'

        mock_request = Mock(spec=LeaderReassignmentRequest)
        mock_request.id = request_id
        mock_request.run_id = run_id
        mock_request.from_user_id = test_user.id
        mock_request.to_user_id = to_user_id
        mock_request.status = 'pending'
        mock_request.created_at = datetime.now()

        service = ReassignmentService(mock_db)
        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(side_effect=[mock_participation, Mock()])
        service.user_repo.get_user_by_id = AsyncMock(return_value=mock_to_user)
        service.store_repo.get_store_by_id = AsyncMock(return_value=mock_store)
        service.reassignment_repo.get_pending_reassignment_for_run = AsyncMock(return_value=None)
        service.reassignment_repo.create_reassignment_request = AsyncMock(return_value=mock_request)
        mock_notification = Mock()
        mock_notification.id = uuid4()
        mock_notification.created_at = datetime.now()
        service.notification_repo.create_notification = AsyncMock(return_value=mock_notification)

        # Act
        result = await service.request_reassignment(run_id, test_user, to_user_id)

        # Assert
        assert result.run_id == str(run_id)
        assert result.from_user_id == str(test_user.id)
        assert result.to_user_id == str(to_user_id)
        assert result.status == 'pending'

    async def test_request_reassignment_run_not_found(self, test_user):
        """Test requesting reassignment for non-existent run."""
        # Arrange
        mock_db = AsyncMock()
        run_id = uuid4()
        to_user_id = uuid4()

        service = ReassignmentService(mock_db)
        service.run_repo.get_run_by_id = AsyncMock(return_value=None)

        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.request_reassignment(run_id, test_user, to_user_id)

        assert exc_info.value.code == RUN_NOT_FOUND

    async def test_request_reassignment_not_leader(self, test_user):
        """Test requesting reassignment when user is not leader."""
        # Arrange
        mock_db = AsyncMock()
        run_id = uuid4()
        to_user_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.is_leader = False

        service = ReassignmentService(mock_db)
        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(return_value=mock_participation)

        # Act & Assert
        with pytest.raises(ForbiddenError) as exc_info:
            await service.request_reassignment(run_id, test_user, to_user_id)

        assert exc_info.value.code == NOT_RUN_LEADER

    async def test_request_reassignment_to_self(self, test_user):
        """Test requesting reassignment to self."""
        # Arrange
        mock_db = AsyncMock()
        run_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.is_leader = True

        service = ReassignmentService(mock_db)
        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(return_value=mock_participation)
        service.user_repo.get_user_by_id = AsyncMock(return_value=test_user)

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await service.request_reassignment(run_id, test_user, test_user.id)

        assert exc_info.value.code == REASSIGNMENT_CANNOT_TRANSFER_TO_SELF

    async def test_request_reassignment_target_not_participant(self, test_user):
        """Test requesting reassignment to non-participant."""
        # Arrange
        mock_db = AsyncMock()
        run_id = uuid4()
        to_user_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.is_leader = True

        mock_to_user = Mock(spec=User)
        mock_to_user.id = to_user_id

        service = ReassignmentService(mock_db)
        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(side_effect=[mock_participation, None])
        service.user_repo.get_user_by_id = AsyncMock(return_value=mock_to_user)

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await service.request_reassignment(run_id, test_user, to_user_id)

        assert exc_info.value.code == REASSIGNMENT_TARGET_NOT_PARTICIPANT

    async def test_request_reassignment_already_exists(self, test_user):
        """Test requesting reassignment when pending request exists."""
        # Arrange
        mock_db = AsyncMock()
        run_id = uuid4()
        to_user_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.is_leader = True

        mock_to_user = Mock(spec=User)
        mock_to_user.id = to_user_id

        existing_request = Mock(id=uuid4())

        service = ReassignmentService(mock_db)
        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(side_effect=[mock_participation, Mock()])
        service.user_repo.get_user_by_id = AsyncMock(return_value=mock_to_user)
        service.reassignment_repo.get_pending_reassignment_for_run = AsyncMock(
            return_value=existing_request
        )

        # Act & Assert
        with pytest.raises(ConflictError) as exc_info:
            await service.request_reassignment(run_id, test_user, to_user_id)

        assert exc_info.value.code == REASSIGNMENT_REQUEST_ALREADY_EXISTS


class TestAcceptReassignment:
    """Test cases for ReassignmentService.accept_reassignment()."""

    async def test_accept_reassignment_success(self, test_user):
        """Test successfully accepting reassignment request."""
        # Arrange
        mock_db = AsyncMock()
        request_id = uuid4()
        run_id = uuid4()
        from_user_id = uuid4()

        mock_request = Mock(spec=LeaderReassignmentRequest)
        mock_request.id = request_id
        mock_request.run_id = run_id
        mock_request.from_user_id = from_user_id
        mock_request.to_user_id = test_user.id
        mock_request.status = 'pending'
        mock_request.created_at = datetime.now()
        mock_request.resolved_at = None

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.store_id = uuid4()

        mock_store = Mock(spec=Store)
        mock_store.name = 'Test Store'

        old_leader_participation = Mock(spec=RunParticipation)
        old_leader_participation.is_leader = True

        new_leader_participation = Mock(spec=RunParticipation)
        new_leader_participation.is_leader = False

        service = ReassignmentService(mock_db)
        service.reassignment_repo.get_reassignment_request_by_id = AsyncMock(
            return_value=mock_request
        )
        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.store_repo.get_store_by_id = AsyncMock(return_value=mock_store)
        service.run_repo.get_participation = AsyncMock(
            side_effect=[old_leader_participation, new_leader_participation]
        )
        service.reassignment_repo.update_reassignment_status = AsyncMock()
        mock_notification = Mock()
        mock_notification.id = uuid4()
        mock_notification.created_at = datetime.now()
        service.notification_repo.create_notification = AsyncMock(return_value=mock_notification)

        # Act
        result = await service.accept_reassignment(request_id, test_user)

        # Assert
        assert result.status == 'accepted'
        assert old_leader_participation.is_leader is False
        assert new_leader_participation.is_leader is True

    async def test_accept_reassignment_not_found(self, test_user):
        """Test accepting non-existent request."""
        # Arrange
        mock_db = AsyncMock()
        request_id = uuid4()

        service = ReassignmentService(mock_db)
        service.reassignment_repo.get_reassignment_request_by_id = AsyncMock(return_value=None)

        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.accept_reassignment(request_id, test_user)

        assert exc_info.value.code == REASSIGNMENT_REQUEST_NOT_FOUND

    async def test_accept_reassignment_not_target_user(self, test_user):
        """Test accepting when user is not the target."""
        # Arrange
        mock_db = AsyncMock()
        request_id = uuid4()
        other_user_id = uuid4()

        mock_request = Mock(spec=LeaderReassignmentRequest)
        mock_request.to_user_id = other_user_id

        service = ReassignmentService(mock_db)
        service.reassignment_repo.get_reassignment_request_by_id = AsyncMock(
            return_value=mock_request
        )

        # Act & Assert
        with pytest.raises(ForbiddenError) as exc_info:
            await service.accept_reassignment(request_id, test_user)

        assert exc_info.value.code == REASSIGNMENT_NOT_TARGET_USER

    async def test_accept_reassignment_already_resolved(self, test_user):
        """Test accepting already resolved request."""
        # Arrange
        mock_db = AsyncMock()
        request_id = uuid4()

        mock_request = Mock(spec=LeaderReassignmentRequest)
        mock_request.to_user_id = test_user.id
        mock_request.status = 'accepted'

        service = ReassignmentService(mock_db)
        service.reassignment_repo.get_reassignment_request_by_id = AsyncMock(
            return_value=mock_request
        )

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await service.accept_reassignment(request_id, test_user)

        assert exc_info.value.code == REASSIGNMENT_REQUEST_ALREADY_RESOLVED


class TestDeclineReassignment:
    """Test cases for ReassignmentService.decline_reassignment()."""

    async def test_decline_reassignment_success(self, test_user):
        """Test successfully declining reassignment request."""
        # Arrange
        mock_db = AsyncMock()
        request_id = uuid4()
        run_id = uuid4()

        mock_request = Mock(spec=LeaderReassignmentRequest)
        mock_request.id = request_id
        mock_request.run_id = run_id
        mock_request.from_user_id = uuid4()
        mock_request.to_user_id = test_user.id
        mock_request.status = 'pending'
        mock_request.created_at = datetime.now()
        mock_request.resolved_at = None

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.store_id = uuid4()

        mock_store = Mock(spec=Store)
        mock_store.name = 'Test Store'

        service = ReassignmentService(mock_db)
        service.reassignment_repo.get_reassignment_request_by_id = AsyncMock(
            return_value=mock_request
        )
        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.store_repo.get_store_by_id = AsyncMock(return_value=mock_store)
        service.reassignment_repo.update_reassignment_status = AsyncMock()
        mock_notification = Mock()
        mock_notification.id = uuid4()
        mock_notification.created_at = datetime.now()
        service.notification_repo.create_notification = AsyncMock(return_value=mock_notification)

        # Act
        result = await service.decline_reassignment(request_id, test_user)

        # Assert
        assert result.status == 'declined'


class TestCancelReassignment:
    """Test cases for ReassignmentService.cancel_reassignment()."""

    async def test_cancel_reassignment_success(self, test_user):
        """Test successfully cancelling reassignment request."""
        # Arrange
        mock_db = AsyncMock()
        request_id = uuid4()

        mock_request = Mock(spec=LeaderReassignmentRequest)
        mock_request.id = request_id
        mock_request.run_id = uuid4()
        mock_request.from_user_id = test_user.id
        mock_request.to_user_id = uuid4()
        mock_request.status = 'pending'
        mock_request.created_at = datetime.now()
        mock_request.resolved_at = None

        service = ReassignmentService(mock_db)
        service.reassignment_repo.get_reassignment_request_by_id = AsyncMock(
            return_value=mock_request
        )
        service.reassignment_repo.update_reassignment_status = AsyncMock()

        # Act
        result = await service.cancel_reassignment(request_id, test_user)

        # Assert
        assert result.status == 'cancelled'

    async def test_cancel_reassignment_not_requester(self, test_user):
        """Test cancelling when user is not the requester."""
        # Arrange
        mock_db = AsyncMock()
        request_id = uuid4()
        other_user_id = uuid4()

        mock_request = Mock(spec=LeaderReassignmentRequest)
        mock_request.from_user_id = other_user_id

        service = ReassignmentService(mock_db)
        service.reassignment_repo.get_reassignment_request_by_id = AsyncMock(
            return_value=mock_request
        )

        # Act & Assert
        with pytest.raises(ForbiddenError) as exc_info:
            await service.cancel_reassignment(request_id, test_user)

        assert exc_info.value.code == REASSIGNMENT_NOT_CURRENT_LEADER


class TestGetPendingRequestsForUser:
    """Test cases for ReassignmentService.get_pending_requests_for_user()."""

    async def test_get_pending_requests_for_user_success(self):
        """Test successfully getting pending requests."""
        # Arrange
        mock_db = AsyncMock()
        user_id = uuid4()

        sent_request = Mock(spec=LeaderReassignmentRequest)
        sent_request.id = uuid4()
        sent_request.run_id = uuid4()
        sent_request.from_user_id = user_id
        sent_request.to_user_id = uuid4()
        sent_request.status = 'pending'
        sent_request.created_at = datetime.now()

        received_request = Mock(spec=LeaderReassignmentRequest)
        received_request.id = uuid4()
        received_request.run_id = uuid4()
        received_request.from_user_id = uuid4()
        received_request.to_user_id = user_id
        received_request.status = 'pending'
        received_request.created_at = datetime.now()

        service = ReassignmentService(mock_db)
        service.reassignment_repo.get_pending_reassignments_from_user = AsyncMock(
            return_value=[sent_request]
        )
        service.reassignment_repo.get_pending_reassignments_to_user = AsyncMock(
            return_value=[received_request]
        )
        mock_user = Mock()
        mock_user.name = 'Test User'
        mock_run = Mock()
        mock_run.store_id = uuid4()
        mock_store = Mock()
        mock_store.name = 'Test Store'

        service.user_repo.get_user_by_id = AsyncMock(return_value=mock_user)
        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.store_repo.get_store_by_id = AsyncMock(return_value=mock_store)

        # Act
        result = await service.get_pending_requests_for_user(user_id)

        # Assert
        assert len(result.sent) == 1
        assert len(result.received) == 1
