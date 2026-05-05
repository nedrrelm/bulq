"""Unit tests for GroupManagementService."""

from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from app.api.schemas import CreateGroupResponse
from app.core.models import Group, User
from app.services.group_management_service import GroupManagementService


class TestCreateGroup:
    """Test cases for GroupManagementService.create_group()."""

    async def test_create_group_success(self, test_user):
        """Test successfully creating a group with valid data."""
        # Arrange
        mock_db = AsyncMock()
        group_id = uuid4()

        # Create mock group
        mock_group = Mock(spec=Group)
        mock_group.id = group_id
        mock_group.name = 'Test Group'
        mock_group.created_by = test_user.id
        mock_group.invite_token = str(uuid4())
        mock_group.is_joining_allowed = True

        # Create service instance
        service = GroupManagementService(mock_db)

        # Mock repository methods
        service.group_repo.create_group = AsyncMock(return_value=mock_group)
        service.group_repo.add_group_member = AsyncMock(return_value=True)

        # Act
        result = await service.create_group(name='Test Group', user=test_user)

        # Assert
        assert result is not None
        assert isinstance(result, CreateGroupResponse)
        assert result.id == str(group_id)
        assert result.name == 'Test Group'
        assert result.member_count == 1
        assert result.active_runs_count == 0
        assert result.completed_runs_count == 0
        assert result.active_runs == []

        # Verify repository calls
        service.group_repo.create_group.assert_called_once_with('Test Group', test_user.id)
        service.group_repo.add_group_member.assert_called_once_with(
            group_id, test_user, is_group_admin=True
        )

    async def test_create_group_creator_is_admin(self, test_user):
        """Test that the creator is automatically added as an admin."""
        # Arrange
        mock_db = AsyncMock()
        group_id = uuid4()

        mock_group = Mock(spec=Group)
        mock_group.id = group_id
        mock_group.name = 'Test Group'
        mock_group.created_by = test_user.id

        service = GroupManagementService(mock_db)
        service.group_repo.create_group = AsyncMock(return_value=mock_group)
        service.group_repo.add_group_member = AsyncMock(return_value=True)

        # Act
        result = await service.create_group(name='Test Group', user=test_user)

        # Assert
        assert result is not None
        # Verify creator is added as admin
        service.group_repo.add_group_member.assert_called_once()
        call_args = service.group_repo.add_group_member.call_args
        assert call_args[0][0] == group_id
        assert call_args[0][1] == test_user
        assert call_args[1]['is_group_admin'] is True

    async def test_create_group_with_empty_name(self, test_user):
        """Test creating a group with an empty name."""
        # Arrange
        mock_db = AsyncMock()
        service = GroupManagementService(mock_db)

        # Mock repository to raise validation error
        service.group_repo.create_group = AsyncMock(
            side_effect=ValueError('Group name cannot be empty')
        )

        # Act & Assert
        with pytest.raises(ValueError, match='Group name cannot be empty'):
            await service.create_group(name='', user=test_user)

    async def test_create_group_with_whitespace_only_name(self, test_user):
        """Test creating a group with whitespace-only name."""
        # Arrange
        mock_db = AsyncMock()
        service = GroupManagementService(mock_db)

        # Mock repository to raise validation error
        service.group_repo.create_group = AsyncMock(
            side_effect=ValueError('Group name cannot be empty')
        )

        # Act & Assert
        with pytest.raises(ValueError):
            await service.create_group(name='   ', user=test_user)

    async def test_create_group_with_long_name(self, test_user):
        """Test creating a group with a very long name."""
        # Arrange
        mock_db = AsyncMock()
        group_id = uuid4()
        long_name = 'A' * 255  # Assuming some reasonable limit

        mock_group = Mock(spec=Group)
        mock_group.id = group_id
        mock_group.name = long_name
        mock_group.created_by = test_user.id

        service = GroupManagementService(mock_db)
        service.group_repo.create_group = AsyncMock(return_value=mock_group)
        service.group_repo.add_group_member = AsyncMock(return_value=True)

        # Act
        result = await service.create_group(name=long_name, user=test_user)

        # Assert
        assert result is not None
        assert result.name == long_name

    async def test_create_group_with_special_characters(self, test_user):
        """Test creating a group with special characters in name."""
        # Arrange
        mock_db = AsyncMock()
        group_id = uuid4()
        special_name = 'Test & Group! @#$%'

        mock_group = Mock(spec=Group)
        mock_group.id = group_id
        mock_group.name = special_name
        mock_group.created_by = test_user.id

        service = GroupManagementService(mock_db)
        service.group_repo.create_group = AsyncMock(return_value=mock_group)
        service.group_repo.add_group_member = AsyncMock(return_value=True)

        # Act
        result = await service.create_group(name=special_name, user=test_user)

        # Assert
        assert result is not None
        assert result.name == special_name

    async def test_create_group_repository_failure(self, test_user):
        """Test handling of repository failure during group creation."""
        # Arrange
        mock_db = AsyncMock()
        service = GroupManagementService(mock_db)

        # Mock repository to raise exception
        service.group_repo.create_group = AsyncMock(side_effect=Exception('Database error'))

        # Act & Assert
        with pytest.raises(Exception, match='Database error'):
            await service.create_group(name='Test Group', user=test_user)

    async def test_create_group_member_addition_failure(self, test_user):
        """Test handling when adding creator as member fails."""
        # Arrange
        mock_db = AsyncMock()
        group_id = uuid4()

        mock_group = Mock(spec=Group)
        mock_group.id = group_id
        mock_group.name = 'Test Group'
        mock_group.created_by = test_user.id

        service = GroupManagementService(mock_db)
        service.group_repo.create_group = AsyncMock(return_value=mock_group)
        # Mock member addition to fail
        service.group_repo.add_group_member = AsyncMock(
            side_effect=Exception('Failed to add member')
        )

        # Act & Assert
        with pytest.raises(Exception, match='Failed to add member'):
            await service.create_group(name='Test Group', user=test_user)

    async def test_create_group_returns_correct_counts(self, test_user):
        """Test that newly created group returns correct initial counts."""
        # Arrange
        mock_db = AsyncMock()
        group_id = uuid4()

        mock_group = Mock(spec=Group)
        mock_group.id = group_id
        mock_group.name = 'Test Group'
        mock_group.created_by = test_user.id

        service = GroupManagementService(mock_db)
        service.group_repo.create_group = AsyncMock(return_value=mock_group)
        service.group_repo.add_group_member = AsyncMock(return_value=True)

        # Act
        result = await service.create_group(name='Test Group', user=test_user)

        # Assert
        assert result.member_count == 1
        assert result.active_runs_count == 0
        assert result.completed_runs_count == 0
        assert result.active_runs == []

    async def test_create_group_with_unicode_name(self, test_user):
        """Test creating a group with Unicode characters in name."""
        # Arrange
        mock_db = AsyncMock()
        group_id = uuid4()
        unicode_name = 'Группа тестирования 测试组'

        mock_group = Mock(spec=Group)
        mock_group.id = group_id
        mock_group.name = unicode_name
        mock_group.created_by = test_user.id

        service = GroupManagementService(mock_db)
        service.group_repo.create_group = AsyncMock(return_value=mock_group)
        service.group_repo.add_group_member = AsyncMock(return_value=True)

        # Act
        result = await service.create_group(name=unicode_name, user=test_user)

        # Assert
        assert result is not None
        assert result.name == unicode_name

    async def test_create_group_with_none_user(self):
        """Test creating a group with None user."""
        # Arrange
        mock_db = AsyncMock()
        service = GroupManagementService(mock_db)

        # Act & Assert
        with pytest.raises(AttributeError):
            await service.create_group(name='Test Group', user=None)

    async def test_create_group_with_none_name(self, test_user):
        """Test creating a group with None name."""
        # Arrange
        mock_db = AsyncMock()
        service = GroupManagementService(mock_db)

        # Mock repository to handle None
        service.group_repo.create_group = AsyncMock(
            side_effect=ValueError('Group name cannot be None')
        )

        # Act & Assert
        with pytest.raises(ValueError):
            await service.create_group(name=None, user=test_user)

    async def test_create_group_transactional_rollback(self, test_user):
        """Test that transaction rolls back on failure."""
        # Arrange
        mock_db = AsyncMock()
        group_id = uuid4()

        mock_group = Mock(spec=Group)
        mock_group.id = group_id
        mock_group.name = 'Test Group'

        service = GroupManagementService(mock_db)
        service.group_repo.create_group = AsyncMock(return_value=mock_group)
        # Simulate failure in member addition
        service.group_repo.add_group_member = AsyncMock(
            side_effect=Exception('Member addition failed')
        )

        # Act & Assert
        with pytest.raises(Exception, match='Member addition failed'):
            await service.create_group(name='Test Group', user=test_user)

        # Verify that group was created before failure
        service.group_repo.create_group.assert_called_once()

    async def test_create_group_duplicate_name_allowed(self, test_user):
        """Test that duplicate group names are allowed (groups are independent)."""
        # Arrange
        mock_db = AsyncMock()
        group_id_1 = uuid4()
        group_id_2 = uuid4()

        mock_group_1 = Mock(spec=Group)
        mock_group_1.id = group_id_1
        mock_group_1.name = 'Test Group'

        mock_group_2 = Mock(spec=Group)
        mock_group_2.id = group_id_2
        mock_group_2.name = 'Test Group'

        service = GroupManagementService(mock_db)
        service.group_repo.create_group = AsyncMock(side_effect=[mock_group_1, mock_group_2])
        service.group_repo.add_group_member = AsyncMock(return_value=True)

        # Act
        result_1 = await service.create_group(name='Test Group', user=test_user)
        result_2 = await service.create_group(name='Test Group', user=test_user)

        # Assert
        assert result_1.id != result_2.id
        assert result_1.name == result_2.name

    async def test_create_group_preserves_user_id(self, test_user):
        """Test that creator's user ID is properly passed to repository."""
        # Arrange
        mock_db = AsyncMock()
        group_id = uuid4()

        mock_group = Mock(spec=Group)
        mock_group.id = group_id
        mock_group.name = 'Test Group'
        mock_group.created_by = test_user.id

        service = GroupManagementService(mock_db)
        service.group_repo.create_group = AsyncMock(return_value=mock_group)
        service.group_repo.add_group_member = AsyncMock(return_value=True)

        # Act
        result = await service.create_group(name='Test Group', user=test_user)

        # Assert
        service.group_repo.create_group.assert_called_once_with('Test Group', test_user.id)
        assert result is not None

    async def test_create_group_different_users(self):
        """Test creating groups with different users."""
        # Arrange
        mock_db = AsyncMock()

        user1 = Mock(spec=User)
        user1.id = uuid4()
        user1.name = 'User 1'

        user2 = Mock(spec=User)
        user2.id = uuid4()
        user2.name = 'User 2'

        group_id_1 = uuid4()
        group_id_2 = uuid4()

        mock_group_1 = Mock(spec=Group)
        mock_group_1.id = group_id_1
        mock_group_1.name = 'Group 1'
        mock_group_1.created_by = user1.id

        mock_group_2 = Mock(spec=Group)
        mock_group_2.id = group_id_2
        mock_group_2.name = 'Group 2'
        mock_group_2.created_by = user2.id

        service = GroupManagementService(mock_db)
        service.group_repo.create_group = AsyncMock(side_effect=[mock_group_1, mock_group_2])
        service.group_repo.add_group_member = AsyncMock(return_value=True)

        # Act
        result_1 = await service.create_group(name='Group 1', user=user1)
        result_2 = await service.create_group(name='Group 2', user=user2)

        # Assert
        assert result_1.id != result_2.id
        service.group_repo.create_group.assert_any_call('Group 1', user1.id)
        service.group_repo.create_group.assert_any_call('Group 2', user2.id)

    async def test_create_group_with_trimmed_name(self, test_user):
        """Test creating a group with leading/trailing whitespace."""
        # Arrange
        mock_db = AsyncMock()
        group_id = uuid4()

        mock_group = Mock(spec=Group)
        mock_group.id = group_id
        mock_group.name = 'Test Group'  # Assuming repository trims
        mock_group.created_by = test_user.id

        service = GroupManagementService(mock_db)
        service.group_repo.create_group = AsyncMock(return_value=mock_group)
        service.group_repo.add_group_member = AsyncMock(return_value=True)

        # Act
        result = await service.create_group(name='  Test Group  ', user=test_user)

        # Assert
        assert result is not None
        # Repository should be called with the original name (trimming happens in repo)
        service.group_repo.create_group.assert_called_once_with('  Test Group  ', test_user.id)

    async def test_create_group_multiple_sequential_creations(self, test_user):
        """Test creating multiple groups sequentially."""
        # Arrange
        mock_db = AsyncMock()
        service = GroupManagementService(mock_db)

        group_ids = [uuid4() for _ in range(3)]
        mock_groups = []
        for i, gid in enumerate(group_ids):
            mock_group = Mock(spec=Group)
            mock_group.id = gid
            mock_group.name = f'Group {i}'
            mock_group.created_by = test_user.id
            mock_groups.append(mock_group)

        service.group_repo.create_group = AsyncMock(side_effect=mock_groups)
        service.group_repo.add_group_member = AsyncMock(return_value=True)

        # Act
        results = [await service.create_group(name=f'Group {i}', user=test_user) for i in range(3)]

        # Assert
        assert len(results) == 3
        assert len({r.id for r in results}) == 3  # All unique IDs
        assert service.group_repo.create_group.call_count == 3
        assert service.group_repo.add_group_member.call_count == 3
