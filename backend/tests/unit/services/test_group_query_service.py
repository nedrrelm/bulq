"""Unit tests for GroupQueryService."""

from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from app.core.error_codes import GROUP_NOT_FOUND, INVALID_UUID_FORMAT, NOT_GROUP_MEMBER
from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.core.models import Group, Run, Store
from app.core.run_state import RunState
from app.services.group_query_service import GroupQueryService


class TestGetUserGroups:
    """Test cases for GroupQueryService.get_user_groups()."""

    async def test_get_user_groups_success(self, test_user):
        """Test successfully getting user's groups."""
        # Arrange
        mock_db = AsyncMock()
        group_id = uuid4()

        mock_creator = Mock()
        mock_creator.name = 'Creator'

        mock_group = Mock(spec=Group)
        mock_group.id = group_id
        mock_group.name = 'Test Group'
        mock_group.creator = mock_creator
        mock_group.members = [Mock(), Mock()]
        mock_group.created_at = None

        service = GroupQueryService(mock_db)
        service.user_repo.get_user_groups = AsyncMock(return_value=[mock_group])
        service.run_repo.get_runs_by_group = AsyncMock(return_value=[])

        # Act
        result = await service.get_user_groups(test_user)

        # Assert
        assert len(result) == 1
        assert result[0].id == str(group_id)
        assert result[0].name == 'Test Group'
        assert result[0].member_count == 2
        assert result[0].active_runs_count == 0
        assert result[0].completed_runs_count == 0

    async def test_get_user_groups_with_runs(self, test_user):
        """Test getting groups with active and completed runs."""
        # Arrange
        mock_db = AsyncMock()
        group_id = uuid4()
        store_id = uuid4()

        mock_group = Mock(spec=Group)
        mock_group.id = group_id
        mock_group.name = 'Test Group'
        mock_group.creator = Mock(name='Creator')
        mock_group.members = [Mock()]
        mock_group.created_at = None

        mock_store = Mock(spec=Store)
        mock_store.name = 'Test Store'

        # Create runs in different states
        active_run = Mock(spec=Run)
        active_run.id = uuid4()
        active_run.state = RunState.ACTIVE
        active_run.store_id = store_id
        active_run.store = mock_store

        completed_run = Mock(spec=Run)
        completed_run.id = uuid4()
        completed_run.state = RunState.COMPLETED
        completed_run.store_id = store_id
        completed_run.store = mock_store

        service = GroupQueryService(mock_db)
        service.user_repo.get_user_groups = AsyncMock(return_value=[mock_group])
        service.run_repo.get_runs_by_group = AsyncMock(return_value=[active_run, completed_run])

        # Act
        result = await service.get_user_groups(test_user)

        # Assert
        assert len(result) == 1
        assert result[0].active_runs_count == 1
        assert result[0].completed_runs_count == 1
        assert len(result[0].active_runs) == 1
        assert result[0].active_runs[0].store_name == 'Test Store'

    async def test_get_user_groups_empty(self, test_user):
        """Test getting groups when user has none."""
        # Arrange
        mock_db = AsyncMock()
        service = GroupQueryService(mock_db)
        service.user_repo.get_user_groups = AsyncMock(return_value=[])

        # Act
        result = await service.get_user_groups(test_user)

        # Assert
        assert result == []

    async def test_get_user_groups_sorts_by_state(self, test_user):
        """Test that runs are sorted by state priority."""
        # Arrange
        mock_db = AsyncMock()
        group_id = uuid4()
        store_id = uuid4()

        mock_group = Mock(spec=Group)
        mock_group.id = group_id
        mock_group.name = 'Test Group'
        mock_group.creator = Mock(name='Creator')
        mock_group.members = []
        mock_group.created_at = None

        mock_store = Mock(spec=Store)
        mock_store.name = 'Test Store'

        # Create runs in different states (in wrong order)
        planning_run = Mock(spec=Run)
        planning_run.id = uuid4()
        planning_run.state = RunState.PLANNING
        planning_run.store_id = store_id
        planning_run.store = mock_store

        distributing_run = Mock(spec=Run)
        distributing_run.id = uuid4()
        distributing_run.state = RunState.DISTRIBUTING
        distributing_run.store_id = store_id
        distributing_run.store = mock_store

        shopping_run = Mock(spec=Run)
        shopping_run.id = uuid4()
        shopping_run.state = RunState.SHOPPING
        shopping_run.store_id = store_id
        shopping_run.store = mock_store

        service = GroupQueryService(mock_db)
        service.user_repo.get_user_groups = AsyncMock(return_value=[mock_group])
        service.run_repo.get_runs_by_group = AsyncMock(
            return_value=[planning_run, distributing_run, shopping_run]
        )

        # Act
        result = await service.get_user_groups(test_user)

        # Assert - should be sorted: distributing > shopping > planning
        active_runs = result[0].active_runs
        assert len(active_runs) == 3
        assert active_runs[0].state == RunState.DISTRIBUTING
        assert active_runs[1].state == RunState.SHOPPING
        assert active_runs[2].state == RunState.PLANNING


class TestGetGroupDetails:
    """Test cases for GroupQueryService.get_group_details()."""

    async def test_get_group_details_success(self, test_user):
        """Test successfully getting group details."""
        # Arrange
        mock_db = AsyncMock()
        group_id = uuid4()

        mock_group = Mock(spec=Group)
        mock_group.id = group_id
        mock_group.name = 'Test Group'
        mock_group.invite_token = 'test-token'
        mock_group.is_joining_allowed = True

        mock_members = [
            {'user_id': str(test_user.id), 'user_name': test_user.name, 'is_admin': True}
        ]

        service = GroupQueryService(mock_db)
        service.group_repo.get_group_by_id = AsyncMock(return_value=mock_group)
        service._is_group_member = AsyncMock(return_value=True)
        service.group_repo.get_group_members_with_admin_status = AsyncMock(
            return_value=mock_members
        )
        service.group_repo.is_user_group_admin = AsyncMock(return_value=True)

        # Act
        result = await service.get_group_details(str(group_id), test_user)

        # Assert
        assert result.id == str(group_id)
        assert result.name == 'Test Group'
        assert result.invite_token == 'test-token'
        assert result.is_joining_allowed is True
        assert result.is_current_user_admin is True
        assert len(result.members) == 1

    async def test_get_group_details_invalid_uuid(self, test_user):
        """Test getting details with invalid UUID."""
        # Arrange
        mock_db = AsyncMock()
        service = GroupQueryService(mock_db)

        # Act & Assert
        with pytest.raises(BadRequestError) as exc_info:
            await service.get_group_details('invalid-uuid', test_user)

        assert exc_info.value.code == INVALID_UUID_FORMAT

    async def test_get_group_details_group_not_found(self, test_user):
        """Test getting details for non-existent group."""
        # Arrange
        mock_db = AsyncMock()
        group_id = uuid4()

        service = GroupQueryService(mock_db)
        service.group_repo.get_group_by_id = AsyncMock(return_value=None)

        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.get_group_details(str(group_id), test_user)

        assert exc_info.value.code == GROUP_NOT_FOUND

    async def test_get_group_details_not_member(self, test_user):
        """Test getting details when user is not a member."""
        # Arrange
        mock_db = AsyncMock()
        group_id = uuid4()

        mock_group = Mock(spec=Group)
        mock_group.id = group_id

        service = GroupQueryService(mock_db)
        service.group_repo.get_group_by_id = AsyncMock(return_value=mock_group)
        service._is_group_member = AsyncMock(return_value=False)

        # Act & Assert
        with pytest.raises(ForbiddenError) as exc_info:
            await service.get_group_details(str(group_id), test_user)

        assert exc_info.value.code == NOT_GROUP_MEMBER


class TestGetGroupRuns:
    """Test cases for GroupQueryService.get_group_runs()."""

    async def test_get_group_runs_success(self, test_user):
        """Test successfully getting group runs."""
        # Arrange
        mock_db = AsyncMock()
        group_id = uuid4()
        run_id = uuid4()
        store_id = uuid4()

        mock_group = Mock(spec=Group)
        mock_group.id = group_id

        mock_store = Mock(spec=Store)
        mock_store.name = 'Test Store'

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.group_id = group_id
        mock_run.store_id = store_id
        mock_run.state = RunState.ACTIVE
        mock_run.store = mock_store
        mock_run.planned_on = None
        mock_run.planning_at = None
        mock_run.active_at = None
        mock_run.confirmed_at = None
        mock_run.shopping_at = None
        mock_run.adjusting_at = None
        mock_run.distributing_at = None
        mock_run.completed_at = None
        mock_run.cancelled_at = None

        mock_participation = Mock()
        mock_participation.is_leader = True
        mock_participation.is_removed = False
        mock_user = Mock()
        mock_user.name = 'Leader'
        mock_participation.user = mock_user

        service = GroupQueryService(mock_db)
        service.group_repo.get_group_by_id = AsyncMock(return_value=mock_group)
        service._verify_group_membership = AsyncMock()
        service.run_repo.get_runs_by_group = AsyncMock(return_value=[mock_run])
        service.run_repo.get_run_participations = AsyncMock(return_value=[mock_participation])

        # Act
        result = await service.get_group_runs(str(group_id), test_user)

        # Assert
        assert len(result) == 1
        assert result[0].id == str(run_id)
        assert result[0].store_name == 'Test Store'
        assert result[0].leader_name == 'Leader'
        assert result[0].state == RunState.ACTIVE

    async def test_get_group_runs_invalid_uuid(self, test_user):
        """Test getting runs with invalid UUID."""
        # Arrange
        mock_db = AsyncMock()
        service = GroupQueryService(mock_db)

        # Act & Assert
        with pytest.raises(BadRequestError) as exc_info:
            await service.get_group_runs('invalid-uuid', test_user)

        assert exc_info.value.code == INVALID_UUID_FORMAT

    async def test_get_group_runs_group_not_found(self, test_user):
        """Test getting runs for non-existent group."""
        # Arrange
        mock_db = AsyncMock()
        group_id = uuid4()

        service = GroupQueryService(mock_db)
        service.group_repo.get_group_by_id = AsyncMock(return_value=None)

        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.get_group_runs(str(group_id), test_user)

        assert exc_info.value.code == GROUP_NOT_FOUND

    async def test_get_group_runs_empty(self, test_user):
        """Test getting runs when group has none."""
        # Arrange
        mock_db = AsyncMock()
        group_id = uuid4()

        mock_group = Mock(spec=Group)
        mock_group.id = group_id

        service = GroupQueryService(mock_db)
        service.group_repo.get_group_by_id = AsyncMock(return_value=mock_group)
        service._verify_group_membership = AsyncMock()
        service.run_repo.get_runs_by_group = AsyncMock(return_value=[])

        # Act
        result = await service.get_group_runs(str(group_id), test_user)

        # Assert
        assert result == []


class TestGetGroupCompletedCancelledRuns:
    """Test cases for GroupQueryService.get_group_completed_cancelled_runs()."""

    async def test_get_completed_cancelled_runs_success(self, test_user):
        """Test successfully getting completed/cancelled runs with pagination."""
        # Arrange
        mock_db = AsyncMock()
        group_id = uuid4()
        run_id = uuid4()

        mock_group = Mock(spec=Group)
        mock_group.id = group_id

        mock_store = Mock(spec=Store)
        mock_store.name = 'Test Store'

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.group_id = group_id
        mock_run.store_id = uuid4()
        mock_run.state = RunState.COMPLETED
        mock_run.store = mock_store
        mock_run.planned_on = None
        mock_run.planning_at = None
        mock_run.active_at = None
        mock_run.confirmed_at = None
        mock_run.shopping_at = None
        mock_run.adjusting_at = None
        mock_run.distributing_at = None
        mock_run.completed_at = None
        mock_run.cancelled_at = None

        mock_participation = Mock()
        mock_participation.is_leader = True
        mock_user = Mock()
        mock_user.name = 'Leader'
        mock_participation.user = mock_user

        service = GroupQueryService(mock_db)
        service.group_repo.get_group_by_id = AsyncMock(return_value=mock_group)
        service._verify_group_membership = AsyncMock()
        service.run_repo.get_completed_cancelled_runs_by_group = AsyncMock(return_value=[mock_run])
        service.run_repo.get_run_participations = AsyncMock(return_value=[mock_participation])

        # Act
        result = await service.get_group_completed_cancelled_runs(
            str(group_id), test_user, limit=10, offset=0
        )

        # Assert
        assert len(result) == 1
        assert result[0].id == str(run_id)
        assert result[0].state == RunState.COMPLETED
        assert result[0].leader_name == 'Leader'
        service.run_repo.get_completed_cancelled_runs_by_group.assert_called_once_with(
            group_id, 10, 0
        )

    async def test_get_completed_cancelled_runs_with_pagination(self, test_user):
        """Test pagination parameters are passed correctly."""
        # Arrange
        mock_db = AsyncMock()
        group_id = uuid4()

        mock_group = Mock(spec=Group)
        mock_group.id = group_id

        service = GroupQueryService(mock_db)
        service.group_repo.get_group_by_id = AsyncMock(return_value=mock_group)
        service._verify_group_membership = AsyncMock()
        service.run_repo.get_completed_cancelled_runs_by_group = AsyncMock(return_value=[])

        # Act
        await service.get_group_completed_cancelled_runs(
            str(group_id), test_user, limit=5, offset=10
        )

        # Assert
        service.run_repo.get_completed_cancelled_runs_by_group.assert_called_once_with(
            group_id, 5, 10
        )
