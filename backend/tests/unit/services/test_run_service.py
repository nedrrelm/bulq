"""Unit tests for RunService."""

from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest

from app.core.error_codes import (
    GROUP_NOT_FOUND,
    INVALID_UUID_FORMAT,
    NOT_GROUP_MEMBER,
    NOT_RUN_LEADER,
    RUN_NOT_FOUND,
    STORE_NOT_FOUND,
)
from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.core.models import Group, Run, RunParticipation, Store
from app.core.run_state import RunState
from app.events.domain_events import CommentUpdatedEvent, RunCreatedEvent
from app.services.run_service import RunService


class TestCreateRun:
    """Test cases for RunService.create_run()."""

    async def test_create_run_success(self, test_user):
        """Test successfully creating a run with valid data."""
        # Arrange
        mock_db = AsyncMock()
        group_id = uuid4()
        store_id = uuid4()
        run_id = uuid4()

        # Create mock group and store
        mock_group = Mock(spec=Group)
        mock_group.id = group_id
        mock_group.name = 'Test Group'

        mock_store = Mock(spec=Store)
        mock_store.id = store_id
        mock_store.name = 'Test Store'

        # Create mock run
        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.group_id = group_id
        mock_run.store_id = store_id
        mock_run.state = RunState.PLANNING.value
        mock_run.comment = None
        mock_run.leader_fee = None

        # Create service instance
        service = RunService(mock_db)

        # Mock repository methods
        service.group_repo.get_group_by_id = AsyncMock(return_value=mock_group)
        service.store_repo.get_store_by_id = AsyncMock(return_value=mock_store)
        service.run_repo.create_run = AsyncMock(return_value=mock_run)
        service.run_repo.get_runs_by_group = AsyncMock(return_value=[])
        service.user_repo.get_user_groups = AsyncMock(return_value=[mock_group])

        # Mock event bus
        with patch('app.services.run_service.event_bus') as mock_event_bus:
            # Act
            result = await service.create_run(
                group_id=str(group_id), store_id=str(store_id), user=test_user
            )

            # Assert
            assert result is not None
            assert result.id == str(run_id)
            assert result.group_id == str(group_id)
            assert result.store_id == str(store_id)
            assert result.state == RunState.PLANNING.value
            assert result.store_name == 'Test Store'
            assert result.leader_name == test_user.name

            # Verify repository calls
            service.group_repo.get_group_by_id.assert_called_once_with(group_id)
            service.store_repo.get_store_by_id.assert_called_once_with(store_id)
            service.run_repo.create_run.assert_called_once_with(
                group_id, store_id, test_user.id, None, None, None
            )

            # Verify event was emitted
            mock_event_bus.emit.assert_called_once()
            emitted_event = mock_event_bus.emit.call_args[0][0]
            assert isinstance(emitted_event, RunCreatedEvent)
            assert emitted_event.run_id == run_id
            assert emitted_event.group_id == group_id
            assert emitted_event.store_id == store_id
            assert emitted_event.store_name == 'Test Store'
            assert emitted_event.state == RunState.PLANNING.value
            assert emitted_event.leader_name == test_user.name

    async def test_create_run_with_comment(self, test_user):
        """Test creating a run with a comment."""
        # Arrange
        mock_db = AsyncMock()
        group_id = uuid4()
        store_id = uuid4()
        comment = 'Shopping for weekend party'

        mock_group = Mock(spec=Group)
        mock_group.id = group_id
        mock_group.name = 'Test Group'

        mock_store = Mock(spec=Store)
        mock_store.id = store_id
        mock_store.name = 'Test Store'

        mock_run = Mock(spec=Run)
        mock_run.id = uuid4()
        mock_run.group_id = group_id
        mock_run.store_id = store_id
        mock_run.state = RunState.PLANNING.value
        mock_run.comment = comment
        mock_run.leader_fee = None

        service = RunService(mock_db)
        service.group_repo.get_group_by_id = AsyncMock(return_value=mock_group)
        service.store_repo.get_store_by_id = AsyncMock(return_value=mock_store)
        service.run_repo.create_run = AsyncMock(return_value=mock_run)
        service.run_repo.get_runs_by_group = AsyncMock(return_value=[])
        service.user_repo.get_user_groups = AsyncMock(return_value=[mock_group])

        # Act
        with patch('app.services.run_service.event_bus'):
            await service.create_run(
                group_id=str(group_id), store_id=str(store_id), user=test_user, comment=comment
            )

            # Assert
            service.run_repo.create_run.assert_called_once_with(
                group_id, store_id, test_user.id, comment, None, None
            )

    async def test_create_run_invalid_group_id_format(self, test_user):
        """Test creating run with invalid group ID format raises BadRequestError."""
        # Arrange
        mock_db = AsyncMock()
        service = RunService(mock_db)

        # Act & Assert
        with pytest.raises(BadRequestError) as exc_info:
            await service.create_run(group_id='invalid-uuid', store_id=str(uuid4()), user=test_user)

        assert exc_info.value.code == INVALID_UUID_FORMAT

    async def test_create_run_invalid_store_id_format(self, test_user):
        """Test creating run with invalid store ID format raises BadRequestError."""
        # Arrange
        mock_db = AsyncMock()
        group_id = uuid4()
        service = RunService(mock_db)

        mock_group = Mock(spec=Group)
        mock_group.id = group_id
        service.group_repo.get_group_by_id = AsyncMock(return_value=mock_group)
        service.user_repo.get_user_groups = AsyncMock(return_value=[mock_group])

        # Act & Assert
        with pytest.raises(BadRequestError) as exc_info:
            await service.create_run(
                group_id=str(group_id), store_id='invalid-uuid', user=test_user
            )

        assert exc_info.value.code == INVALID_UUID_FORMAT

    async def test_create_run_group_not_found(self, test_user):
        """Test creating run with non-existent group raises NotFoundError."""
        # Arrange
        mock_db = AsyncMock()
        group_id = uuid4()
        store_id = uuid4()

        service = RunService(mock_db)
        service.group_repo.get_group_by_id = AsyncMock(return_value=None)

        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.create_run(group_id=str(group_id), store_id=str(store_id), user=test_user)

        assert exc_info.value.code == GROUP_NOT_FOUND
        service.group_repo.get_group_by_id.assert_called_once_with(group_id)

    async def test_create_run_user_not_group_member(self, test_user):
        """Test creating run when user is not a group member raises ForbiddenError."""
        # Arrange
        mock_db = AsyncMock()
        group_id = uuid4()
        store_id = uuid4()

        mock_group = Mock(spec=Group)
        mock_group.id = group_id
        mock_group.name = 'Test Group'

        service = RunService(mock_db)
        service.group_repo.get_group_by_id = AsyncMock(return_value=mock_group)
        service.user_repo.get_user_groups = AsyncMock(return_value=[])  # User not in group

        # Act & Assert
        with pytest.raises(ForbiddenError) as exc_info:
            await service.create_run(group_id=str(group_id), store_id=str(store_id), user=test_user)

        assert exc_info.value.code == NOT_GROUP_MEMBER

    async def test_create_run_store_not_found(self, test_user):
        """Test creating run with non-existent store raises NotFoundError."""
        # Arrange
        mock_db = AsyncMock()
        group_id = uuid4()
        store_id = uuid4()

        mock_group = Mock(spec=Group)
        mock_group.id = group_id
        mock_group.name = 'Test Group'

        service = RunService(mock_db)
        service.group_repo.get_group_by_id = AsyncMock(return_value=mock_group)
        service.store_repo.get_store_by_id = AsyncMock(return_value=None)
        service.user_repo.get_user_groups = AsyncMock(return_value=[mock_group])

        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.create_run(group_id=str(group_id), store_id=str(store_id), user=test_user)

        assert exc_info.value.code == STORE_NOT_FOUND
        service.store_repo.get_store_by_id.assert_called_once_with(store_id)

    async def test_create_run_max_active_runs_exceeded(self, test_user):
        """Test creating run when group has reached max active runs limit."""
        # Arrange
        mock_db = AsyncMock()
        group_id = uuid4()
        store_id = uuid4()

        mock_group = Mock(spec=Group)
        mock_group.id = group_id
        mock_group.name = 'Test Group'

        mock_store = Mock(spec=Store)
        mock_store.id = store_id
        mock_store.name = 'Test Store'

        # Create mock active runs (MAX_ACTIVE_RUNS_PER_GROUP default is 100)
        active_runs = []
        for _ in range(100):
            mock_run = Mock(spec=Run)
            mock_run.state = RunState.PLANNING.value
            active_runs.append(mock_run)

        service = RunService(mock_db)
        service.group_repo.get_group_by_id = AsyncMock(return_value=mock_group)
        service.store_repo.get_store_by_id = AsyncMock(return_value=mock_store)
        service.run_repo.get_runs_by_group = AsyncMock(return_value=active_runs)
        service.user_repo.get_user_groups = AsyncMock(return_value=[mock_group])

        # Act & Assert
        with pytest.raises(BadRequestError) as exc_info:
            await service.create_run(group_id=str(group_id), store_id=str(store_id), user=test_user)

        assert exc_info.value.code == 'GROUP_MAX_ACTIVE_RUNS_EXCEEDED'

    async def test_create_run_ignores_completed_runs_in_limit(self, test_user):
        """Test that completed/cancelled runs don't count toward active run limit."""
        # Arrange
        mock_db = AsyncMock()
        group_id = uuid4()
        store_id = uuid4()

        mock_group = Mock(spec=Group)
        mock_group.id = group_id
        mock_group.name = 'Test Group'

        mock_store = Mock(spec=Store)
        mock_store.id = store_id
        mock_store.name = 'Test Store'

        # Create mix of active and completed runs
        mock_active_run = Mock(spec=Run)
        mock_active_run.state = RunState.PLANNING.value

        mock_completed_run = Mock(spec=Run)
        mock_completed_run.state = RunState.COMPLETED.value

        mock_cancelled_run = Mock(spec=Run)
        mock_cancelled_run.state = RunState.CANCELLED.value

        mock_new_run = Mock(spec=Run)
        mock_new_run.id = uuid4()
        mock_new_run.group_id = group_id
        mock_new_run.store_id = store_id
        mock_new_run.state = RunState.PLANNING.value

        service = RunService(mock_db)
        service.group_repo.get_group_by_id = AsyncMock(return_value=mock_group)
        service.store_repo.get_store_by_id = AsyncMock(return_value=mock_store)
        service.run_repo.get_runs_by_group = AsyncMock(
            return_value=[mock_active_run, mock_completed_run, mock_cancelled_run]
        )
        service.run_repo.create_run = AsyncMock(return_value=mock_new_run)
        service.user_repo.get_user_groups = AsyncMock(return_value=[mock_group])

        # Act - Should succeed because only 1 active run exists
        with patch('app.services.run_service.event_bus'):
            result = await service.create_run(
                group_id=str(group_id), store_id=str(store_id), user=test_user
            )

            # Assert
            assert result is not None
            service.run_repo.create_run.assert_called_once()


class TestGetRunDetails:
    """Test cases for RunService.get_run_details()."""

    async def test_get_run_details_success(self, test_user):
        """Test successfully getting run details."""
        # Arrange
        mock_db = AsyncMock()
        run_id = uuid4()
        group_id = uuid4()
        store_id = uuid4()

        mock_group = Mock(spec=Group)
        mock_group.id = group_id
        mock_group.name = 'Test Group'

        mock_store = Mock(spec=Store)
        mock_store.id = store_id
        mock_store.name = 'Test Store'

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.group_id = group_id
        mock_run.store_id = store_id
        mock_run.state = RunState.PLANNING.value
        mock_run.comment = 'Test comment'
        mock_run.leader_fee = None

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.user_id = test_user.id
        mock_participation.is_ready = False
        mock_participation.is_leader = True
        mock_participation.is_helper = False
        mock_participation.is_removed = False
        mock_participation.user = test_user

        service = RunService(mock_db)
        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.group_repo.get_group_by_id = AsyncMock(return_value=mock_group)
        service.store_repo.get_store_by_id = AsyncMock(return_value=mock_store)
        service.run_repo.get_run_participations_with_users = AsyncMock(
            return_value=[mock_participation]
        )
        service.user_repo.get_user_groups = AsyncMock(return_value=[mock_group])
        service.bid_repo.get_bids_by_run_with_participations = AsyncMock(return_value=[])

        # Act
        result = await service.get_run_details(run_id=str(run_id), user=test_user)

        # Assert
        assert result is not None
        assert result.id == str(run_id)
        assert result.group_id == str(group_id)
        assert result.group_name == 'Test Group'
        assert result.store_id == str(store_id)
        assert result.store_name == 'Test Store'
        assert result.state == RunState.PLANNING.value
        assert result.comment == 'Test comment'
        assert result.current_user_is_leader is True
        assert result.current_user_is_ready is False
        assert result.current_user_is_helper is False
        assert result.leader_name == test_user.name

    async def test_get_run_details_invalid_run_id_format(self, test_user):
        """Test getting run details with invalid run ID format."""
        # Arrange
        mock_db = AsyncMock()
        service = RunService(mock_db)

        # Act & Assert
        with pytest.raises(BadRequestError) as exc_info:
            await service.get_run_details(run_id='invalid-uuid', user=test_user)

        assert exc_info.value.code == INVALID_UUID_FORMAT

    async def test_get_run_details_run_not_found(self, test_user):
        """Test getting details for non-existent run."""
        # Arrange
        mock_db = AsyncMock()
        run_id = uuid4()

        service = RunService(mock_db)
        service.run_repo.get_run_by_id = AsyncMock(return_value=None)

        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.get_run_details(run_id=str(run_id), user=test_user)

        assert exc_info.value.code == RUN_NOT_FOUND

    async def test_get_run_details_user_not_group_member(self, test_user):
        """Test getting run details when user is not a group member."""
        # Arrange
        mock_db = AsyncMock()
        run_id = uuid4()
        group_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.group_id = group_id
        mock_run.state = RunState.PLANNING.value

        service = RunService(mock_db)
        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.user_repo.get_user_groups = AsyncMock(return_value=[])  # User not in group

        # Act & Assert
        with pytest.raises(ForbiddenError):
            await service.get_run_details(run_id=str(run_id), user=test_user)

    async def test_get_run_details_with_multiple_participants(self, test_user, test_group_member):
        """Test getting run details with multiple participants."""
        # Arrange
        mock_db = AsyncMock()
        run_id = uuid4()
        group_id = uuid4()
        store_id = uuid4()

        mock_group = Mock(spec=Group)
        mock_group.id = group_id
        mock_group.name = 'Test Group'

        mock_store = Mock(spec=Store)
        mock_store.id = store_id
        mock_store.name = 'Test Store'

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.group_id = group_id
        mock_run.store_id = store_id
        mock_run.state = RunState.ACTIVE.value
        mock_run.comment = None
        mock_run.leader_fee = None

        # Create participations for leader and member
        leader_participation = Mock(spec=RunParticipation)
        leader_participation.user_id = test_user.id
        leader_participation.is_ready = True
        leader_participation.is_leader = True
        leader_participation.is_helper = False
        leader_participation.is_removed = False
        leader_participation.user = test_user

        member_participation = Mock(spec=RunParticipation)
        member_participation.user_id = test_group_member.id
        member_participation.is_ready = False
        member_participation.is_leader = False
        member_participation.is_helper = False
        member_participation.is_removed = False
        member_participation.user = test_group_member

        service = RunService(mock_db)
        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.group_repo.get_group_by_id = AsyncMock(return_value=mock_group)
        service.store_repo.get_store_by_id = AsyncMock(return_value=mock_store)
        service.run_repo.get_run_participations_with_users = AsyncMock(
            return_value=[leader_participation, member_participation]
        )
        service.user_repo.get_user_groups = AsyncMock(return_value=[mock_group])
        service.bid_repo.get_bids_by_run_with_participations = AsyncMock(return_value=[])

        # Act
        result = await service.get_run_details(run_id=str(run_id), user=test_user)

        # Assert
        assert len(result.participants) == 2
        assert result.leader_name == test_user.name


class TestUpdateRunComment:
    """Test cases for RunService.update_run_comment()."""

    async def test_update_run_comment_success(self, test_user):
        """Test successfully updating run comment as leader."""
        # Arrange
        mock_db = AsyncMock()
        run_id = uuid4()
        group_id = uuid4()
        new_comment = 'Updated shopping list details'

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.group_id = group_id
        mock_run.state = RunState.PLANNING.value

        mock_group = Mock(spec=Group)
        mock_group.id = group_id

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.user_id = test_user.id
        mock_participation.is_leader = True

        mock_updated_run = Mock(spec=Run)
        mock_updated_run.id = run_id
        mock_updated_run.comment = new_comment

        service = RunService(mock_db)
        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(return_value=mock_participation)
        service.run_repo.update_run_comment = AsyncMock(return_value=mock_updated_run)
        service.user_repo.get_user_groups = AsyncMock(return_value=[mock_group])

        # Act
        with patch('app.services.run_service.event_bus') as mock_event_bus:
            result = await service.update_run_comment(
                run_id=str(run_id), comment=new_comment, user=test_user
            )

            # Assert
            assert result is not None
            service.run_repo.update_run_comment.assert_called_once_with(run_id, new_comment)

            # Verify event was emitted
            mock_event_bus.emit.assert_called_once()
            emitted_event = mock_event_bus.emit.call_args[0][0]
            assert isinstance(emitted_event, CommentUpdatedEvent)
            assert emitted_event.run_id == run_id
            assert emitted_event.comment == new_comment

    async def test_update_run_comment_clear_comment(self, test_user):
        """Test clearing run comment by setting to None."""
        # Arrange
        mock_db = AsyncMock()
        run_id = uuid4()
        group_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.group_id = group_id

        mock_group = Mock(spec=Group)
        mock_group.id = group_id

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.is_leader = True

        mock_updated_run = Mock(spec=Run)
        mock_updated_run.id = run_id
        mock_updated_run.comment = None

        service = RunService(mock_db)
        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(return_value=mock_participation)
        service.run_repo.update_run_comment = AsyncMock(return_value=mock_updated_run)
        service.user_repo.get_user_groups = AsyncMock(return_value=[mock_group])

        # Act
        with patch('app.services.run_service.event_bus') as mock_event_bus:
            result = await service.update_run_comment(
                run_id=str(run_id), comment=None, user=test_user
            )

            # Assert
            assert result is not None
            service.run_repo.update_run_comment.assert_called_once_with(run_id, None)
            emitted_event = mock_event_bus.emit.call_args[0][0]
            assert emitted_event.comment is None

    async def test_update_run_comment_invalid_run_id(self, test_user):
        """Test updating comment with invalid run ID format."""
        # Arrange
        mock_db = AsyncMock()
        service = RunService(mock_db)

        # Act & Assert
        with pytest.raises(BadRequestError) as exc_info:
            await service.update_run_comment(run_id='invalid-uuid', comment='test', user=test_user)

        assert exc_info.value.code == INVALID_UUID_FORMAT

    async def test_update_run_comment_run_not_found(self, test_user):
        """Test updating comment for non-existent run."""
        # Arrange
        mock_db = AsyncMock()
        run_id = uuid4()

        service = RunService(mock_db)
        service.run_repo.get_run_by_id = AsyncMock(return_value=None)

        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.update_run_comment(run_id=str(run_id), comment='test', user=test_user)

        assert exc_info.value.code == RUN_NOT_FOUND

    async def test_update_run_comment_user_not_leader(self, test_user):
        """Test updating comment when user is not the run leader."""
        # Arrange
        mock_db = AsyncMock()
        run_id = uuid4()
        group_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.group_id = group_id

        mock_group = Mock(spec=Group)
        mock_group.id = group_id

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.is_leader = False  # Not a leader

        service = RunService(mock_db)
        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(return_value=mock_participation)
        service.user_repo.get_user_groups = AsyncMock(return_value=[mock_group])

        # Act & Assert
        with pytest.raises(ForbiddenError) as exc_info:
            await service.update_run_comment(run_id=str(run_id), comment='test', user=test_user)

        assert exc_info.value.code == NOT_RUN_LEADER

    async def test_update_run_comment_no_participation(self, test_user):
        """Test updating comment when user has no participation record."""
        # Arrange
        mock_db = AsyncMock()
        run_id = uuid4()
        group_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.group_id = group_id

        mock_group = Mock(spec=Group)
        mock_group.id = group_id

        service = RunService(mock_db)
        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(return_value=None)  # No participation
        service.user_repo.get_user_groups = AsyncMock(return_value=[mock_group])

        # Act & Assert
        with pytest.raises(ForbiddenError) as exc_info:
            await service.update_run_comment(run_id=str(run_id), comment='test', user=test_user)

        assert exc_info.value.code == NOT_RUN_LEADER

    async def test_update_run_comment_repository_returns_none(self, test_user):
        """Test handling when repository update returns None."""
        # Arrange
        mock_db = AsyncMock()
        run_id = uuid4()
        group_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.group_id = group_id

        mock_group = Mock(spec=Group)
        mock_group.id = group_id

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.is_leader = True

        service = RunService(mock_db)
        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(return_value=mock_participation)
        service.run_repo.update_run_comment = AsyncMock(return_value=None)  # Update failed
        service.user_repo.get_user_groups = AsyncMock(return_value=[mock_group])

        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.update_run_comment(run_id=str(run_id), comment='test', user=test_user)

        assert exc_info.value.code == RUN_NOT_FOUND


class TestGetAvailableProducts:
    """Test cases for RunService.get_available_products()."""

    async def test_get_available_products_success(self, test_user):
        """Test successfully getting available products for a run."""
        # Arrange
        mock_db = AsyncMock()
        run_id = uuid4()
        group_id = uuid4()
        store_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.group_id = group_id
        mock_run.store_id = store_id

        mock_group = Mock(spec=Group)
        mock_group.id = group_id

        # Create mock products
        product1 = Mock()
        product1.id = uuid4()
        product1.name = 'Product A'
        product1.brand = 'Brand A'

        product2 = Mock()
        product2.id = uuid4()
        product2.name = 'Product B'
        product2.brand = 'Brand B'

        service = RunService(mock_db)
        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.user_repo.get_user_groups = AsyncMock(return_value=[mock_group])
        service.product_repo.get_all_products = AsyncMock(return_value=[product1, product2])
        service.bid_repo.get_bids_by_run = AsyncMock(return_value=[])  # No bids yet
        service.product_repo.get_availability_by_product_and_store = AsyncMock(return_value=None)

        # Act
        result = await service.get_available_products(run_id=str(run_id), user=test_user)

        # Assert
        assert len(result) == 2
        assert result[0].id == str(product1.id)
        assert result[0].name == 'Product A'
        assert result[1].id == str(product2.id)
        assert result[1].name == 'Product B'

    async def test_get_available_products_excludes_products_with_bids(self, test_user):
        """Test that products with existing bids are excluded."""
        # Arrange
        mock_db = AsyncMock()
        run_id = uuid4()
        group_id = uuid4()
        store_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.group_id = group_id
        mock_run.store_id = store_id

        mock_group = Mock(spec=Group)
        mock_group.id = group_id

        product1_id = uuid4()
        product2_id = uuid4()

        product1 = Mock()
        product1.id = product1_id
        product1.name = 'Product A'
        product1.brand = 'Brand A'

        product2 = Mock()
        product2.id = product2_id
        product2.name = 'Product B'
        product2.brand = 'Brand B'

        # Mock bid for product1
        mock_bid = Mock()
        mock_bid.product_id = product1_id

        service = RunService(mock_db)
        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.user_repo.get_user_groups = AsyncMock(return_value=[mock_group])
        service.product_repo.get_all_products = AsyncMock(return_value=[product1, product2])
        service.bid_repo.get_bids_by_run = AsyncMock(
            return_value=[mock_bid]
        )  # Bid exists for product1
        service.product_repo.get_availability_by_product_and_store = AsyncMock(return_value=None)

        # Act
        result = await service.get_available_products(run_id=str(run_id), user=test_user)

        # Assert - Only product2 should be returned
        assert len(result) == 1
        assert result[0].id == str(product2_id)
        assert result[0].name == 'Product B'

    async def test_get_available_products_invalid_run_id(self, test_user):
        """Test getting available products with invalid run ID."""
        # Arrange
        mock_db = AsyncMock()
        service = RunService(mock_db)

        # Act & Assert
        with pytest.raises(BadRequestError) as exc_info:
            await service.get_available_products(run_id='invalid-uuid', user=test_user)

        assert exc_info.value.code == INVALID_UUID_FORMAT

    async def test_get_available_products_run_not_found(self, test_user):
        """Test getting available products for non-existent run."""
        # Arrange
        mock_db = AsyncMock()
        run_id = uuid4()

        service = RunService(mock_db)
        service.run_repo.get_run_by_id = AsyncMock(return_value=None)

        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.get_available_products(run_id=str(run_id), user=test_user)

        assert exc_info.value.code == RUN_NOT_FOUND


class TestToggleHelper:
    """Test cases for RunService.toggle_helper()."""

    async def test_toggle_helper_add_helper_success(self, test_user, test_group_member):
        """Test successfully adding a helper to a run."""
        # Arrange
        mock_db = AsyncMock()
        run_id = uuid4()
        group_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.group_id = group_id

        mock_leader_participation = Mock(spec=RunParticipation)
        mock_leader_participation.is_leader = True

        # No existing participation for target user
        mock_new_participation = Mock(spec=RunParticipation)
        mock_new_participation.user_id = test_group_member.id
        mock_new_participation.is_helper = True

        mock_group = Mock(spec=Group)
        mock_group.id = group_id

        service = RunService(mock_db)
        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(
            side_effect=[mock_leader_participation, None]  # Leader exists, target user doesn't
        )
        service.run_repo.create_participation = AsyncMock(return_value=mock_new_participation)
        service.user_repo.get_user_by_id = AsyncMock(return_value=test_group_member)
        service.user_repo.get_user_groups = AsyncMock(return_value=[mock_group])

        # Act
        with patch('app.services.run_service.event_bus') as mock_event_bus:
            result = await service.toggle_helper(
                run_id=str(run_id), target_user_id=str(test_group_member.id), current_user=test_user
            )

            # Assert
            assert result is not None
            service.run_repo.create_participation.assert_called_once_with(
                user_id=test_group_member.id, run_id=run_id, is_leader=False, is_helper=True
            )

            # Verify event was emitted
            mock_event_bus.emit.assert_called_once()

    async def test_toggle_helper_remove_helper_success(self, test_user, test_group_member):
        """Test successfully removing helper status from a user."""
        # Arrange
        mock_db = AsyncMock()
        run_id = uuid4()
        group_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.group_id = group_id

        mock_leader_participation = Mock(spec=RunParticipation)
        mock_leader_participation.is_leader = True

        mock_helper_participation = Mock(spec=RunParticipation)
        mock_helper_participation.is_leader = False
        mock_helper_participation.is_helper = True  # Currently a helper

        mock_group = Mock(spec=Group)
        mock_group.id = group_id

        service = RunService(mock_db)
        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(
            side_effect=[
                mock_leader_participation,
                mock_helper_participation,
            ]  # Leader and existing helper
        )
        service.run_repo.update_participation_helper = AsyncMock()
        service.user_repo.get_user_by_id = AsyncMock(return_value=test_group_member)
        service.user_repo.get_user_groups = AsyncMock(return_value=[mock_group])

        # Act
        with patch('app.services.run_service.event_bus'):
            result = await service.toggle_helper(
                run_id=str(run_id), target_user_id=str(test_group_member.id), current_user=test_user
            )

            # Assert
            assert result is not None
            service.run_repo.update_participation_helper.assert_called_once_with(
                test_group_member.id, run_id, False
            )

    async def test_toggle_helper_cannot_make_leader_helper(self, test_user):
        """Test that leader cannot be made a helper."""
        # Arrange
        mock_db = AsyncMock()
        run_id = uuid4()
        group_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.group_id = group_id

        mock_leader_participation = Mock(spec=RunParticipation)
        mock_leader_participation.is_leader = True

        mock_group = Mock(spec=Group)
        mock_group.id = group_id

        service = RunService(mock_db)
        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(
            side_effect=[
                mock_leader_participation,
                mock_leader_participation,
            ]  # Both are leader participation
        )
        service.user_repo.get_user_by_id = AsyncMock(return_value=test_user)
        service.user_repo.get_user_groups = AsyncMock(return_value=[mock_group])

        # Act & Assert
        with pytest.raises(BadRequestError):
            await service.toggle_helper(
                run_id=str(run_id), target_user_id=str(test_user.id), current_user=test_user
            )

    async def test_toggle_helper_not_leader(self, test_user, test_group_member):
        """Test that non-leader cannot toggle helper status."""
        # Arrange
        mock_db = AsyncMock()
        run_id = uuid4()
        group_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.group_id = group_id

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.is_leader = False  # Not a leader

        service = RunService(mock_db)
        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(return_value=mock_participation)

        # Act & Assert
        with pytest.raises(ForbiddenError) as exc_info:
            await service.toggle_helper(
                run_id=str(run_id), target_user_id=str(test_group_member.id), current_user=test_user
            )

        assert exc_info.value.code == NOT_RUN_LEADER


class TestDelegatedMethods:
    """Test cases for methods that delegate to sub-services."""

    async def test_place_bid_delegates_to_bid_service(self, test_user):
        """Test that place_bid delegates to BidService."""
        # Arrange
        mock_db = AsyncMock()
        mock_bid_service = AsyncMock()
        mock_response = Mock()
        mock_bid_service.place_bid = AsyncMock(return_value=mock_response)

        service = RunService(mock_db, bid_service=mock_bid_service)

        # Act
        result = await service.place_bid(
            run_id='run-123',
            product_id='product-456',
            quantity=5.0,
            interested_only=False,
            user=test_user,
            comment='test comment',
        )

        # Assert
        mock_bid_service.place_bid.assert_called_once_with(
            'run-123', 'product-456', 5.0, False, test_user, 'test comment'
        )
        assert result == mock_response

    async def test_retract_bid_delegates_to_bid_service(self, test_user):
        """Test that retract_bid delegates to BidService."""
        # Arrange
        mock_db = AsyncMock()
        mock_bid_service = AsyncMock()
        mock_response = Mock()
        mock_bid_service.retract_bid = AsyncMock(return_value=mock_response)

        service = RunService(mock_db, bid_service=mock_bid_service)

        # Act
        result = await service.retract_bid(
            run_id='run-123', product_id='product-456', user=test_user
        )

        # Assert
        mock_bid_service.retract_bid.assert_called_once_with('run-123', 'product-456', test_user)
        assert result == mock_response

    async def test_toggle_ready_delegates_to_state_service(self, test_user):
        """Test that toggle_ready delegates to RunStateService."""
        # Arrange
        mock_db = AsyncMock()
        mock_state_service = AsyncMock()
        mock_response = Mock()
        mock_state_service.toggle_ready = AsyncMock(return_value=mock_response)

        service = RunService(mock_db, state_service=mock_state_service)

        # Act
        result = await service.toggle_ready(run_id='run-123', user=test_user)

        # Assert
        mock_state_service.toggle_ready.assert_called_once_with('run-123', test_user)
        assert result == mock_response

    async def test_force_confirm_run_delegates_to_state_service(self, test_user):
        """Test that force_confirm_run delegates to RunStateService."""
        # Arrange
        mock_db = AsyncMock()
        mock_state_service = AsyncMock()
        mock_response = Mock()
        mock_state_service.force_confirm = AsyncMock(return_value=mock_response)

        service = RunService(mock_db, state_service=mock_state_service)

        # Act
        result = await service.force_confirm_run(run_id='run-123', user=test_user)

        # Assert
        mock_state_service.force_confirm.assert_called_once_with('run-123', test_user)
        assert result == mock_response

    async def test_start_run_delegates_to_state_service(self, test_user):
        """Test that start_run delegates to RunStateService."""
        # Arrange
        mock_db = AsyncMock()
        mock_state_service = AsyncMock()
        mock_response = Mock()
        mock_state_service.start_shopping = AsyncMock(return_value=mock_response)

        service = RunService(mock_db, state_service=mock_state_service)

        # Act
        result = await service.start_run(run_id='run-123', user=test_user)

        # Assert
        mock_state_service.start_shopping.assert_called_once_with('run-123', test_user)
        assert result == mock_response

    async def test_transition_to_shopping_aliases_start_run(self, test_user):
        """Test that transition_to_shopping is an alias for start_run."""
        # Arrange
        mock_db = AsyncMock()
        mock_state_service = AsyncMock()
        mock_response = Mock()
        mock_state_service.start_shopping = AsyncMock(return_value=mock_response)

        service = RunService(mock_db, state_service=mock_state_service)

        # Act
        result = await service.transition_to_shopping(run_id='run-123', user=test_user)

        # Assert
        mock_state_service.start_shopping.assert_called_once_with('run-123', test_user)
        assert result == mock_response

    async def test_finish_adjusting_delegates_to_state_service(self, test_user):
        """Test that finish_adjusting delegates to RunStateService."""
        # Arrange
        mock_db = AsyncMock()
        mock_state_service = AsyncMock()
        mock_response = Mock()
        mock_state_service.finish_adjusting = AsyncMock(return_value=mock_response)

        service = RunService(mock_db, state_service=mock_state_service)

        # Act
        result = await service.finish_adjusting(run_id='run-123', user=test_user, force=True)

        # Assert
        mock_state_service.finish_adjusting.assert_called_once_with('run-123', test_user, True)
        assert result == mock_response

    async def test_cancel_run_delegates_to_state_service(self, test_user):
        """Test that cancel_run delegates to RunStateService."""
        # Arrange
        mock_db = AsyncMock()
        mock_state_service = AsyncMock()
        mock_response = Mock()
        mock_state_service.cancel_run = AsyncMock(return_value=mock_response)

        service = RunService(mock_db, state_service=mock_state_service)

        # Act
        result = await service.cancel_run(run_id='run-123', user=test_user)

        # Assert
        mock_state_service.cancel_run.assert_called_once_with('run-123', test_user)
        assert result == mock_response


class TestAuthorizationHelpers:
    """Test cases for authorization helper methods."""

    async def test_is_group_member_returns_true_when_member(self, test_user):
        """Test _is_group_member returns True when user is a member."""
        # Arrange
        mock_db = AsyncMock()
        group_id = uuid4()

        mock_group = Mock(spec=Group)
        mock_group.id = group_id

        service = RunService(mock_db)
        service.user_repo.get_user_groups = AsyncMock(return_value=[mock_group])

        # Act
        result = await service._is_group_member(test_user, group_id)

        # Assert
        assert result is True

    async def test_is_group_member_returns_false_when_not_member(self, test_user):
        """Test _is_group_member returns False when user is not a member."""
        # Arrange
        mock_db = AsyncMock()
        group_id = uuid4()

        service = RunService(mock_db)
        service.user_repo.get_user_groups = AsyncMock(return_value=[])  # No groups

        # Act
        result = await service._is_group_member(test_user, group_id)

        # Assert
        assert result is False

    async def test_verify_group_membership_raises_when_not_member(self, test_user):
        """Test _verify_group_membership raises ForbiddenError when not a member."""
        # Arrange
        mock_db = AsyncMock()
        group_id = uuid4()

        service = RunService(mock_db)
        service.user_repo.get_user_groups = AsyncMock(return_value=[])

        # Act & Assert
        with pytest.raises(ForbiddenError) as exc_info:
            await service._verify_group_membership(test_user, group_id)

        assert exc_info.value.code == NOT_GROUP_MEMBER

    async def test_verify_run_access_allows_group_member(self, test_user):
        """Test _verify_run_access allows group members."""
        # Arrange
        mock_db = AsyncMock()
        group_id = uuid4()

        mock_group = Mock(spec=Group)
        mock_group.id = group_id

        mock_run = Mock(spec=Run)
        mock_run.group_id = group_id

        service = RunService(mock_db)
        service.user_repo.get_user_groups = AsyncMock(return_value=[mock_group])

        # Act - Should not raise
        await service._verify_run_access(test_user, mock_run)

    async def test_verify_run_access_denies_non_member(self, test_user):
        """Test _verify_run_access denies non-group members."""
        # Arrange
        mock_db = AsyncMock()
        group_id = uuid4()

        mock_run = Mock(spec=Run)
        mock_run.group_id = group_id

        service = RunService(mock_db)
        service.user_repo.get_user_groups = AsyncMock(return_value=[])

        # Act & Assert
        with pytest.raises(ForbiddenError):
            await service._verify_run_access(test_user, mock_run)
