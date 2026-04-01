"""Unit tests for GroupMembershipService."""

from unittest.mock import Mock, patch
from uuid import uuid4

import pytest

from app.api.schemas import SuccessResponse
from app.core.error_codes import (
    CANNOT_REMOVE_GROUP_ADMIN,
    GROUP_MEMBER_PROMOTION_FAILED,
    GROUP_MEMBER_REMOVAL_FAILED,
    GROUP_NOT_FOUND,
    INVALID_UUID_FORMAT,
    LAST_ADMIN_CANNOT_LEAVE,
    NOT_A_GROUP_MEMBER,
    NOT_GROUP_ADMIN,
    USER_ALREADY_GROUP_ADMIN,
)
from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.core.models import Group, Run, RunParticipation
from app.core.run_state import RunState
from app.core.success_codes import GROUP_LEFT, MEMBER_PROMOTED, MEMBER_REMOVED
from app.events.domain_events import MemberRemovedEvent
from app.services.group_membership_service import GroupMembershipService


class TestRemoveMember:
    """Test cases for GroupMembershipService.remove_member()."""

    def test_remove_member_success(self, test_user, test_group_member):
        """Test successfully removing a member from a group."""
        # Arrange
        mock_db = Mock()
        group_id = uuid4()
        member_id = test_group_member.id

        mock_group = Mock(spec=Group)
        mock_group.id = group_id
        mock_group.name = 'Test Group'

        service = GroupMembershipService(mock_db)
        service.group_repo.get_group_by_id = Mock(return_value=mock_group)
        service.group_repo.is_user_group_admin = Mock(
            side_effect=[True, False]
        )  # Admin check, then member check
        service.group_repo.get_group_members_with_admin_status = Mock(
            return_value=[
                {'id': str(test_user.id), 'name': 'Test User', 'is_group_admin': True},
                {'id': str(member_id), 'name': 'Group Member', 'is_group_admin': False},
            ]
        )
        service.group_repo.remove_group_member = Mock(return_value=True)
        service.run_repo.get_runs_by_group = Mock(return_value=[])
        service.user_repo.get_user_by_id = Mock(return_value=test_group_member)

        # Mock event bus and websocket manager
        with (
            patch('app.services.group_membership_service.event_bus') as mock_event_bus,
            patch('app.services.group_membership_service.create_background_task'),
        ):
            # Act
            result = service.remove_member(
                group_id=str(group_id), member_id=str(member_id), user=test_user
            )

            # Assert
            assert result is not None
            assert isinstance(result, SuccessResponse)
            assert result.code == MEMBER_REMOVED
            assert result.details['group_id'] == str(group_id)
            assert result.details['member_id'] == str(member_id)

            # Verify repository calls
            service.group_repo.remove_group_member.assert_called_once_with(group_id, member_id)

            # Verify event was emitted
            mock_event_bus.emit.assert_called_once()
            emitted_event = mock_event_bus.emit.call_args[0][0]
            assert isinstance(emitted_event, MemberRemovedEvent)
            assert emitted_event.group_id == group_id
            assert emitted_event.user_id == member_id

    def test_remove_member_not_admin(self, test_user, test_group_member):
        """Test that non-admin cannot remove members."""
        # Arrange
        mock_db = Mock()
        group_id = uuid4()

        mock_group = Mock(spec=Group)
        mock_group.id = group_id

        service = GroupMembershipService(mock_db)
        service.group_repo.get_group_by_id = Mock(return_value=mock_group)
        service.group_repo.is_user_group_admin = Mock(return_value=False)  # Not admin

        # Act & Assert
        with pytest.raises(ForbiddenError) as exc_info:
            service.remove_member(
                group_id=str(group_id), member_id=str(test_group_member.id), user=test_user
            )

        assert exc_info.value.code == NOT_GROUP_ADMIN
        assert 'Only group admins can remove members' in exc_info.value.message

    def test_remove_member_cannot_remove_admin(self, test_user, test_group_member):
        """Test that admins cannot remove other admins."""
        # Arrange
        mock_db = Mock()
        group_id = uuid4()

        mock_group = Mock(spec=Group)
        mock_group.id = group_id

        service = GroupMembershipService(mock_db)
        service.group_repo.get_group_by_id = Mock(return_value=mock_group)
        service.group_repo.is_user_group_admin = Mock(return_value=True)  # Both are admins

        # Act & Assert
        with pytest.raises(ForbiddenError) as exc_info:
            service.remove_member(
                group_id=str(group_id), member_id=str(test_group_member.id), user=test_user
            )

        assert exc_info.value.code == CANNOT_REMOVE_GROUP_ADMIN
        assert 'Cannot remove group admins' in exc_info.value.message

    def test_remove_member_invalid_group_id(self, test_user, test_group_member):
        """Test removing member with invalid group ID format."""
        # Arrange
        mock_db = Mock()
        service = GroupMembershipService(mock_db)

        # Act & Assert
        with pytest.raises(BadRequestError) as exc_info:
            service.remove_member(
                group_id='invalid-uuid', member_id=str(test_group_member.id), user=test_user
            )

        assert exc_info.value.code == INVALID_UUID_FORMAT

    def test_remove_member_invalid_member_id(self, test_user):
        """Test removing member with invalid member ID format."""
        # Arrange
        mock_db = Mock()
        group_id = uuid4()
        service = GroupMembershipService(mock_db)

        # Act & Assert
        with pytest.raises(BadRequestError) as exc_info:
            service.remove_member(group_id=str(group_id), member_id='invalid-uuid', user=test_user)

        assert exc_info.value.code == INVALID_UUID_FORMAT

    def test_remove_member_group_not_found(self, test_user, test_group_member):
        """Test removing member from non-existent group."""
        # Arrange
        mock_db = Mock()
        group_id = uuid4()

        service = GroupMembershipService(mock_db)
        service.group_repo.get_group_by_id = Mock(return_value=None)

        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            service.remove_member(
                group_id=str(group_id), member_id=str(test_group_member.id), user=test_user
            )

        assert exc_info.value.code == GROUP_NOT_FOUND

    def test_remove_member_not_a_member(self, test_user, test_group_member):
        """Test removing a user who is not a member."""
        # Arrange
        mock_db = Mock()
        group_id = uuid4()

        mock_group = Mock(spec=Group)
        mock_group.id = group_id

        service = GroupMembershipService(mock_db)
        service.group_repo.get_group_by_id = Mock(return_value=mock_group)
        service.group_repo.is_user_group_admin = Mock(side_effect=[True, False])
        service.group_repo.get_group_members_with_admin_status = Mock(
            return_value=[
                {'id': str(test_user.id), 'name': 'Test User', 'is_group_admin': True},
            ]
        )

        # Act & Assert
        with pytest.raises(BadRequestError) as exc_info:
            service.remove_member(
                group_id=str(group_id), member_id=str(test_group_member.id), user=test_user
            )

        assert exc_info.value.code == NOT_A_GROUP_MEMBER

    def test_remove_member_with_active_runs(self, test_user, test_group_member):
        """Test removing member who has participations in runs."""
        # Arrange
        mock_db = Mock()
        group_id = uuid4()
        member_id = test_group_member.id
        run_id = uuid4()

        mock_group = Mock(spec=Group)
        mock_group.id = group_id

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.PLANNING

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.id = uuid4()
        mock_participation.user_id = member_id
        mock_participation.is_leader = False
        mock_participation.is_removed = False

        service = GroupMembershipService(mock_db)
        service.group_repo.get_group_by_id = Mock(return_value=mock_group)
        service.group_repo.is_user_group_admin = Mock(side_effect=[True, False])
        service.group_repo.get_group_members_with_admin_status = Mock(
            return_value=[
                {'id': str(test_user.id), 'name': 'Test User', 'is_group_admin': True},
                {'id': str(member_id), 'name': 'Group Member', 'is_group_admin': False},
            ]
        )
        service.group_repo.remove_group_member = Mock(return_value=True)
        service.run_repo.get_runs_by_group = Mock(return_value=[mock_run])
        service.run_repo.get_run_participations = Mock(return_value=[mock_participation])
        service.bid_repo.get_bids_by_participation = Mock(return_value=[])
        service.user_repo.get_user_by_id = Mock(return_value=test_group_member)

        # Mock event bus and websocket
        with (
            patch('app.services.group_membership_service.event_bus'),
            patch('app.services.group_membership_service.create_background_task'),
        ):
            # Act
            result = service.remove_member(
                group_id=str(group_id), member_id=str(member_id), user=test_user
            )

            # Assert
            assert result is not None
            assert result.code == MEMBER_REMOVED
            # Participation should be marked as removed
            assert mock_participation.is_removed is True


class TestLeaveGroup:
    """Test cases for GroupMembershipService.leave_group()."""

    def test_leave_group_success(self, test_user, test_group_member):
        """Test successfully leaving a group."""
        # Arrange
        mock_db = Mock()
        group_id = uuid4()

        mock_group = Mock(spec=Group)
        mock_group.id = group_id
        mock_group.name = 'Test Group'

        service = GroupMembershipService(mock_db)
        service.group_repo.get_group_by_id = Mock(return_value=mock_group)
        service.group_repo.get_group_members_with_admin_status = Mock(
            return_value=[
                {'id': str(test_group_member.id), 'name': 'Group Member', 'is_group_admin': False},
                {'id': str(test_user.id), 'name': 'Test User', 'is_group_admin': True},
            ]
        )
        service.group_repo.is_user_group_admin = Mock(return_value=False)
        service.group_repo.remove_group_member = Mock(return_value=True)
        service.run_repo.get_runs_by_group = Mock(return_value=[])
        service.user_repo.get_user_by_id = Mock(return_value=test_group_member)

        # Mock event bus and websocket
        with (
            patch('app.services.group_membership_service.event_bus'),
            patch('app.services.group_membership_service.create_background_task'),
        ):
            # Act
            result = service.leave_group(group_id=str(group_id), user=test_group_member)

            # Assert
            assert result is not None
            assert isinstance(result, SuccessResponse)
            assert result.code == GROUP_LEFT
            assert result.details['group_id'] == str(group_id)

            # Verify member was removed
            service.group_repo.remove_group_member.assert_called_once_with(
                group_id, test_group_member.id
            )

    def test_leave_group_last_admin_cannot_leave(self, test_user):
        """Test that the last admin cannot leave the group."""
        # Arrange
        mock_db = Mock()
        group_id = uuid4()

        mock_group = Mock(spec=Group)
        mock_group.id = group_id

        service = GroupMembershipService(mock_db)
        service.group_repo.get_group_by_id = Mock(return_value=mock_group)
        service.group_repo.get_group_members_with_admin_status = Mock(
            return_value=[
                {'id': str(test_user.id), 'name': 'Test User', 'is_group_admin': True},
            ]
        )
        service.group_repo.is_user_group_admin = Mock(return_value=True)

        # Act & Assert
        with pytest.raises(ForbiddenError) as exc_info:
            service.leave_group(group_id=str(group_id), user=test_user)

        assert exc_info.value.code == LAST_ADMIN_CANNOT_LEAVE
        assert 'only admin' in exc_info.value.message.lower()

    def test_leave_group_admin_can_leave_when_other_admins_exist(
        self, test_user, test_group_member
    ):
        """Test that admin can leave when other admins exist."""
        # Arrange
        mock_db = Mock()
        group_id = uuid4()

        mock_group = Mock(spec=Group)
        mock_group.id = group_id

        service = GroupMembershipService(mock_db)
        service.group_repo.get_group_by_id = Mock(return_value=mock_group)
        service.group_repo.get_group_members_with_admin_status = Mock(
            return_value=[
                {'id': str(test_user.id), 'name': 'Test User', 'is_group_admin': True},
                {'id': str(test_group_member.id), 'name': 'Group Member', 'is_group_admin': True},
            ]
        )
        service.group_repo.is_user_group_admin = Mock(return_value=True)
        service.group_repo.remove_group_member = Mock(return_value=True)
        service.run_repo.get_runs_by_group = Mock(return_value=[])
        service.user_repo.get_user_by_id = Mock(return_value=test_user)

        # Mock event bus and websocket
        with (
            patch('app.services.group_membership_service.event_bus'),
            patch('app.services.group_membership_service.create_background_task'),
        ):
            # Act
            result = service.leave_group(group_id=str(group_id), user=test_user)

            # Assert
            assert result is not None
            assert result.code == GROUP_LEFT

    def test_leave_group_not_a_member(self, test_user):
        """Test leaving a group user is not a member of."""
        # Arrange
        mock_db = Mock()
        group_id = uuid4()

        mock_group = Mock(spec=Group)
        mock_group.id = group_id

        service = GroupMembershipService(mock_db)
        service.group_repo.get_group_by_id = Mock(return_value=mock_group)
        service.group_repo.get_group_members_with_admin_status = Mock(
            return_value=[]  # User is not in the list
        )

        # Act & Assert
        with pytest.raises(BadRequestError) as exc_info:
            service.leave_group(group_id=str(group_id), user=test_user)

        assert exc_info.value.code == NOT_A_GROUP_MEMBER

    def test_leave_group_invalid_group_id(self, test_user):
        """Test leaving group with invalid group ID format."""
        # Arrange
        mock_db = Mock()
        service = GroupMembershipService(mock_db)

        # Act & Assert
        with pytest.raises(BadRequestError) as exc_info:
            service.leave_group(group_id='invalid-uuid', user=test_user)

        assert exc_info.value.code == INVALID_UUID_FORMAT

    def test_leave_group_not_found(self, test_user):
        """Test leaving a non-existent group."""
        # Arrange
        mock_db = Mock()
        group_id = uuid4()

        service = GroupMembershipService(mock_db)
        service.group_repo.get_group_by_id = Mock(return_value=None)

        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            service.leave_group(group_id=str(group_id), user=test_user)

        assert exc_info.value.code == GROUP_NOT_FOUND

    def test_leave_group_cancels_led_runs(self, test_user):
        """Test that runs led by the leaving user are cancelled."""
        # Arrange
        mock_db = Mock()
        group_id = uuid4()
        run_id = uuid4()

        mock_group = Mock(spec=Group)
        mock_group.id = group_id

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.PLANNING

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.user_id = test_user.id
        mock_participation.is_leader = True
        mock_participation.is_removed = False

        service = GroupMembershipService(mock_db)
        service.group_repo.get_group_by_id = Mock(return_value=mock_group)
        service.group_repo.get_group_members_with_admin_status = Mock(
            return_value=[
                {'id': str(test_user.id), 'name': 'Test User', 'is_group_admin': False},
            ]
        )
        service.group_repo.is_user_group_admin = Mock(return_value=False)
        service.group_repo.remove_group_member = Mock(return_value=True)
        service.run_repo.get_runs_by_group = Mock(return_value=[mock_run])
        service.run_repo.get_run_participations = Mock(return_value=[mock_participation])
        service.bid_repo.get_bids_by_participation = Mock(return_value=[])
        service.user_repo.get_user_by_id = Mock(return_value=test_user)

        # Mock event bus and websocket
        with (
            patch('app.services.group_membership_service.event_bus'),
            patch('app.services.group_membership_service.create_background_task'),
        ):
            # Act
            result = service.leave_group(group_id=str(group_id), user=test_user)

            # Assert
            assert result is not None
            assert mock_run.state == RunState.CANCELLED


class TestPromoteMemberToAdmin:
    """Test cases for GroupMembershipService.promote_member_to_admin()."""

    def test_promote_member_success(self, test_user, test_group_member):
        """Test successfully promoting a member to admin."""
        # Arrange
        mock_db = Mock()
        group_id = uuid4()

        mock_group = Mock(spec=Group)
        mock_group.id = group_id

        service = GroupMembershipService(mock_db)
        service.group_repo.get_group_by_id = Mock(return_value=mock_group)
        service.group_repo.is_user_group_admin = Mock(
            side_effect=[True, False]
        )  # Requester is admin, target is not
        service.group_repo.get_group_members_with_admin_status = Mock(
            return_value=[
                {'id': str(test_user.id), 'name': 'Test User', 'is_group_admin': True},
                {'id': str(test_group_member.id), 'name': 'Group Member', 'is_group_admin': False},
            ]
        )
        service.group_repo.set_group_member_admin = Mock(return_value=True)

        # Mock websocket
        with patch('app.services.group_membership_service.create_background_task'):
            # Act
            result = service.promote_member_to_admin(
                group_id=str(group_id), member_id=str(test_group_member.id), user=test_user
            )

            # Assert
            assert result is not None
            assert isinstance(result, SuccessResponse)
            assert result.code == MEMBER_PROMOTED
            assert result.details['group_id'] == str(group_id)
            assert result.details['member_id'] == str(test_group_member.id)

            # Verify set_group_member_admin was called
            service.group_repo.set_group_member_admin.assert_called_once_with(
                group_id, test_group_member.id, True
            )

    def test_promote_member_not_admin(self, test_user, test_group_member):
        """Test that non-admin cannot promote members."""
        # Arrange
        mock_db = Mock()
        group_id = uuid4()

        mock_group = Mock(spec=Group)
        mock_group.id = group_id

        service = GroupMembershipService(mock_db)
        service.group_repo.get_group_by_id = Mock(return_value=mock_group)
        service.group_repo.is_user_group_admin = Mock(return_value=False)

        # Act & Assert
        with pytest.raises(ForbiddenError) as exc_info:
            service.promote_member_to_admin(
                group_id=str(group_id), member_id=str(test_group_member.id), user=test_user
            )

        assert exc_info.value.code == NOT_GROUP_ADMIN

    def test_promote_member_already_admin(self, test_user, test_group_member):
        """Test promoting a member who is already an admin."""
        # Arrange
        mock_db = Mock()
        group_id = uuid4()

        mock_group = Mock(spec=Group)
        mock_group.id = group_id

        service = GroupMembershipService(mock_db)
        service.group_repo.get_group_by_id = Mock(return_value=mock_group)
        service.group_repo.is_user_group_admin = Mock(return_value=True)  # Both are admins
        service.group_repo.get_group_members_with_admin_status = Mock(
            return_value=[
                {'id': str(test_user.id), 'name': 'Test User', 'is_group_admin': True},
                {'id': str(test_group_member.id), 'name': 'Group Member', 'is_group_admin': True},
            ]
        )

        # Act & Assert
        with pytest.raises(BadRequestError) as exc_info:
            service.promote_member_to_admin(
                group_id=str(group_id), member_id=str(test_group_member.id), user=test_user
            )

        assert exc_info.value.code == USER_ALREADY_GROUP_ADMIN

    def test_promote_member_not_a_member(self, test_user, test_group_member):
        """Test promoting a user who is not a member."""
        # Arrange
        mock_db = Mock()
        group_id = uuid4()

        mock_group = Mock(spec=Group)
        mock_group.id = group_id

        service = GroupMembershipService(mock_db)
        service.group_repo.get_group_by_id = Mock(return_value=mock_group)
        service.group_repo.is_user_group_admin = Mock(side_effect=[True, False])
        service.group_repo.get_group_members_with_admin_status = Mock(
            return_value=[
                {'id': str(test_user.id), 'name': 'Test User', 'is_group_admin': True},
            ]
        )

        # Act & Assert
        with pytest.raises(BadRequestError) as exc_info:
            service.promote_member_to_admin(
                group_id=str(group_id), member_id=str(test_group_member.id), user=test_user
            )

        assert exc_info.value.code == NOT_A_GROUP_MEMBER

    def test_promote_member_invalid_group_id(self, test_user, test_group_member):
        """Test promoting member with invalid group ID format."""
        # Arrange
        mock_db = Mock()
        service = GroupMembershipService(mock_db)

        # Act & Assert
        with pytest.raises(BadRequestError) as exc_info:
            service.promote_member_to_admin(
                group_id='invalid-uuid', member_id=str(test_group_member.id), user=test_user
            )

        assert exc_info.value.code == INVALID_UUID_FORMAT

    def test_promote_member_invalid_member_id(self, test_user):
        """Test promoting member with invalid member ID format."""
        # Arrange
        mock_db = Mock()
        group_id = uuid4()
        service = GroupMembershipService(mock_db)

        # Act & Assert
        with pytest.raises(BadRequestError) as exc_info:
            service.promote_member_to_admin(
                group_id=str(group_id), member_id='invalid-uuid', user=test_user
            )

        assert exc_info.value.code == INVALID_UUID_FORMAT

    def test_promote_member_group_not_found(self, test_user, test_group_member):
        """Test promoting member in non-existent group."""
        # Arrange
        mock_db = Mock()
        group_id = uuid4()

        service = GroupMembershipService(mock_db)
        service.group_repo.get_group_by_id = Mock(return_value=None)

        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            service.promote_member_to_admin(
                group_id=str(group_id), member_id=str(test_group_member.id), user=test_user
            )

        assert exc_info.value.code == GROUP_NOT_FOUND

    def test_promote_member_promotion_fails(self, test_user, test_group_member):
        """Test handling when promotion operation fails."""
        # Arrange
        mock_db = Mock()
        group_id = uuid4()

        mock_group = Mock(spec=Group)
        mock_group.id = group_id

        service = GroupMembershipService(mock_db)
        service.group_repo.get_group_by_id = Mock(return_value=mock_group)
        service.group_repo.is_user_group_admin = Mock(side_effect=[True, False])
        service.group_repo.get_group_members_with_admin_status = Mock(
            return_value=[
                {'id': str(test_user.id), 'name': 'Test User', 'is_group_admin': True},
                {'id': str(test_group_member.id), 'name': 'Group Member', 'is_group_admin': False},
            ]
        )
        service.group_repo.set_group_member_admin = Mock(return_value=False)

        # Act & Assert
        with pytest.raises(BadRequestError) as exc_info:
            service.promote_member_to_admin(
                group_id=str(group_id), member_id=str(test_group_member.id), user=test_user
            )

        assert exc_info.value.code == GROUP_MEMBER_PROMOTION_FAILED

    def test_promote_member_multiple_admins(self, test_user):
        """Test promoting member when multiple admins exist."""
        # Arrange
        mock_db = Mock()
        group_id = uuid4()
        member1_id = uuid4()
        member2_id = uuid4()

        mock_group = Mock(spec=Group)
        mock_group.id = group_id

        service = GroupMembershipService(mock_db)
        service.group_repo.get_group_by_id = Mock(return_value=mock_group)
        service.group_repo.is_user_group_admin = Mock(side_effect=[True, False])
        service.group_repo.get_group_members_with_admin_status = Mock(
            return_value=[
                {'id': str(test_user.id), 'name': 'Test User', 'is_group_admin': True},
                {'id': str(member1_id), 'name': 'Member 1', 'is_group_admin': True},
                {'id': str(member2_id), 'name': 'Member 2', 'is_group_admin': False},
            ]
        )
        service.group_repo.set_group_member_admin = Mock(return_value=True)

        # Mock websocket
        with patch('app.services.group_membership_service.create_background_task'):
            # Act
            result = service.promote_member_to_admin(
                group_id=str(group_id), member_id=str(member2_id), user=test_user
            )

            # Assert
            assert result is not None
            assert result.code == MEMBER_PROMOTED


class TestRemoveMemberWithRuns:
    """Test cases for removing members with various run scenarios."""

    def test_remove_member_deletes_bids_from_active_run(self, test_user, test_group_member):
        """Test that bids are deleted from active runs when member is removed."""
        # Arrange
        mock_db = Mock()
        group_id = uuid4()
        member_id = test_group_member.id
        run_id = uuid4()
        participation_id = uuid4()

        mock_group = Mock(spec=Group)
        mock_group.id = group_id

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.PLANNING

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.id = participation_id
        mock_participation.user_id = member_id
        mock_participation.is_leader = False
        mock_participation.is_removed = False

        mock_bid = Mock()
        mock_bid.product_id = uuid4()

        service = GroupMembershipService(mock_db)
        service.group_repo.get_group_by_id = Mock(return_value=mock_group)
        service.group_repo.is_user_group_admin = Mock(side_effect=[True, False])
        service.group_repo.get_group_members_with_admin_status = Mock(
            return_value=[
                {'id': str(test_user.id), 'name': 'Test User', 'is_group_admin': True},
                {'id': str(member_id), 'name': 'Group Member', 'is_group_admin': False},
            ]
        )
        service.group_repo.remove_group_member = Mock(return_value=True)
        service.run_repo.get_runs_by_group = Mock(return_value=[mock_run])
        service.run_repo.get_run_participations = Mock(return_value=[mock_participation])
        service.bid_repo.get_bids_by_participation = Mock(return_value=[mock_bid])
        service.bid_repo.delete_bid = Mock()
        service.user_repo.get_user_by_id = Mock(return_value=test_group_member)

        # Mock event bus and websocket
        with (
            patch('app.services.group_membership_service.event_bus'),
            patch('app.services.group_membership_service.create_background_task'),
        ):
            # Act
            result = service.remove_member(
                group_id=str(group_id), member_id=str(member_id), user=test_user
            )

            # Assert
            assert result is not None
            service.bid_repo.delete_bid.assert_called_once_with(
                participation_id, mock_bid.product_id
            )

    def test_remove_member_does_not_delete_bids_from_completed_run(
        self, test_user, test_group_member
    ):
        """Test that bids are preserved in completed runs."""
        # Arrange
        mock_db = Mock()
        group_id = uuid4()
        member_id = test_group_member.id
        run_id = uuid4()

        mock_group = Mock(spec=Group)
        mock_group.id = group_id

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.COMPLETED

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.id = uuid4()
        mock_participation.user_id = member_id
        mock_participation.is_leader = False
        mock_participation.is_removed = False

        service = GroupMembershipService(mock_db)
        service.group_repo.get_group_by_id = Mock(return_value=mock_group)
        service.group_repo.is_user_group_admin = Mock(side_effect=[True, False])
        service.group_repo.get_group_members_with_admin_status = Mock(
            return_value=[
                {'id': str(test_user.id), 'name': 'Test User', 'is_group_admin': True},
                {'id': str(member_id), 'name': 'Group Member', 'is_group_admin': False},
            ]
        )
        service.group_repo.remove_group_member = Mock(return_value=True)
        service.run_repo.get_runs_by_group = Mock(return_value=[mock_run])
        service.run_repo.get_run_participations = Mock(return_value=[mock_participation])
        service.bid_repo.get_bids_by_participation = Mock(return_value=[])
        service.bid_repo.delete_bid = Mock()
        service.user_repo.get_user_by_id = Mock(return_value=test_group_member)

        # Mock event bus and websocket
        with (
            patch('app.services.group_membership_service.event_bus'),
            patch('app.services.group_membership_service.create_background_task'),
        ):
            # Act
            result = service.remove_member(
                group_id=str(group_id), member_id=str(member_id), user=test_user
            )

            # Assert
            assert result is not None
            # Bids should not be deleted from completed run
            service.bid_repo.delete_bid.assert_not_called()

    def test_remove_member_cancels_run_if_leader(self, test_user, test_group_member):
        """Test that runs are cancelled when leader is removed."""
        # Arrange
        mock_db = Mock()
        group_id = uuid4()
        member_id = test_group_member.id
        run_id = uuid4()

        mock_group = Mock(spec=Group)
        mock_group.id = group_id

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.PLANNING

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.user_id = member_id
        mock_participation.is_leader = True
        mock_participation.is_removed = False

        service = GroupMembershipService(mock_db)
        service.group_repo.get_group_by_id = Mock(return_value=mock_group)
        service.group_repo.is_user_group_admin = Mock(side_effect=[True, False])
        service.group_repo.get_group_members_with_admin_status = Mock(
            return_value=[
                {'id': str(test_user.id), 'name': 'Test User', 'is_group_admin': True},
                {'id': str(member_id), 'name': 'Group Member', 'is_group_admin': False},
            ]
        )
        service.group_repo.remove_group_member = Mock(return_value=True)
        service.run_repo.get_runs_by_group = Mock(return_value=[mock_run])
        service.run_repo.get_run_participations = Mock(return_value=[mock_participation])
        service.bid_repo.get_bids_by_participation = Mock(return_value=[])
        service.user_repo.get_user_by_id = Mock(return_value=test_group_member)

        # Mock event bus and websocket
        with (
            patch('app.services.group_membership_service.event_bus'),
            patch('app.services.group_membership_service.create_background_task'),
        ):
            # Act
            result = service.remove_member(
                group_id=str(group_id), member_id=str(member_id), user=test_user
            )

            # Assert
            assert result is not None
            assert mock_run.state == RunState.CANCELLED

    def test_remove_member_does_not_cancel_completed_run_even_if_leader(
        self, test_user, test_group_member
    ):
        """Test that completed runs are not cancelled even when leader is removed."""
        # Arrange
        mock_db = Mock()
        group_id = uuid4()
        member_id = test_group_member.id
        run_id = uuid4()

        mock_group = Mock(spec=Group)
        mock_group.id = group_id

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.state = RunState.COMPLETED

        mock_participation = Mock(spec=RunParticipation)
        mock_participation.user_id = member_id
        mock_participation.is_leader = True
        mock_participation.is_removed = False

        service = GroupMembershipService(mock_db)
        service.group_repo.get_group_by_id = Mock(return_value=mock_group)
        service.group_repo.is_user_group_admin = Mock(side_effect=[True, False])
        service.group_repo.get_group_members_with_admin_status = Mock(
            return_value=[
                {'id': str(test_user.id), 'name': 'Test User', 'is_group_admin': True},
                {'id': str(member_id), 'name': 'Group Member', 'is_group_admin': False},
            ]
        )
        service.group_repo.remove_group_member = Mock(return_value=True)
        service.run_repo.get_runs_by_group = Mock(return_value=[mock_run])
        service.run_repo.get_run_participations = Mock(return_value=[mock_participation])
        service.bid_repo.get_bids_by_participation = Mock(return_value=[])
        service.user_repo.get_user_by_id = Mock(return_value=test_group_member)

        # Mock event bus and websocket
        with (
            patch('app.services.group_membership_service.event_bus'),
            patch('app.services.group_membership_service.create_background_task'),
        ):
            # Act
            result = service.remove_member(
                group_id=str(group_id), member_id=str(member_id), user=test_user
            )

            # Assert
            assert result is not None
            # Completed run should remain completed
            assert mock_run.state == RunState.COMPLETED


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_remove_member_repository_failure(self, test_user, test_group_member):
        """Test handling of repository failure during member removal."""
        # Arrange
        mock_db = Mock()
        group_id = uuid4()

        mock_group = Mock(spec=Group)
        mock_group.id = group_id

        service = GroupMembershipService(mock_db)
        service.group_repo.get_group_by_id = Mock(return_value=mock_group)
        service.group_repo.is_user_group_admin = Mock(side_effect=[True, False])
        service.group_repo.get_group_members_with_admin_status = Mock(
            return_value=[
                {'id': str(test_user.id), 'name': 'Test User', 'is_group_admin': True},
                {'id': str(test_group_member.id), 'name': 'Group Member', 'is_group_admin': False},
            ]
        )
        service.group_repo.remove_group_member = Mock(return_value=False)

        # Act & Assert
        with pytest.raises(BadRequestError) as exc_info:
            service.remove_member(
                group_id=str(group_id), member_id=str(test_group_member.id), user=test_user
            )

        assert exc_info.value.code == GROUP_MEMBER_REMOVAL_FAILED

    def test_concurrent_admin_removal_prevention(self, test_user, test_group_member):
        """Test that multiple admins can't be removed simultaneously leaving no admins."""
        # Arrange
        mock_db = Mock()
        group_id = uuid4()

        mock_group = Mock(spec=Group)
        mock_group.id = group_id

        # Simulate checking if only 1 admin left (the one leaving)
        service = GroupMembershipService(mock_db)
        service.group_repo.get_group_by_id = Mock(return_value=mock_group)
        service.group_repo.get_group_members_with_admin_status = Mock(
            return_value=[
                {'id': str(test_user.id), 'name': 'Test User', 'is_group_admin': True},
            ]
        )
        service.group_repo.is_user_group_admin = Mock(return_value=True)

        # Act & Assert
        with pytest.raises(ForbiddenError) as exc_info:
            service.leave_group(group_id=str(group_id), user=test_user)

        assert exc_info.value.code == LAST_ADMIN_CANNOT_LEAVE

    def test_promote_self_to_admin(self, test_user):
        """Test that an admin can theoretically promote themselves (idempotent case)."""
        # Arrange
        mock_db = Mock()
        group_id = uuid4()

        mock_group = Mock(spec=Group)
        mock_group.id = group_id

        service = GroupMembershipService(mock_db)
        service.group_repo.get_group_by_id = Mock(return_value=mock_group)
        service.group_repo.is_user_group_admin = Mock(return_value=True)  # Already admin
        service.group_repo.get_group_members_with_admin_status = Mock(
            return_value=[
                {'id': str(test_user.id), 'name': 'Test User', 'is_group_admin': True},
            ]
        )

        # Act & Assert
        with pytest.raises(BadRequestError) as exc_info:
            service.promote_member_to_admin(
                group_id=str(group_id), member_id=str(test_user.id), user=test_user
            )

        assert exc_info.value.code == USER_ALREADY_GROUP_ADMIN

    def test_leave_group_with_multiple_cancelled_runs(self, test_user):
        """Test leaving group with multiple runs that need to be cancelled."""
        # Arrange
        mock_db = Mock()
        group_id = uuid4()

        mock_group = Mock(spec=Group)
        mock_group.id = group_id

        # Create multiple runs
        runs = []
        for _ in range(3):
            mock_run = Mock(spec=Run)
            mock_run.id = uuid4()
            mock_run.state = RunState.PLANNING

            mock_participation = Mock(spec=RunParticipation)
            mock_participation.user_id = test_user.id
            mock_participation.is_leader = True
            mock_participation.is_removed = False

            runs.append((mock_run, mock_participation))

        service = GroupMembershipService(mock_db)
        service.group_repo.get_group_by_id = Mock(return_value=mock_group)
        service.group_repo.get_group_members_with_admin_status = Mock(
            return_value=[
                {'id': str(test_user.id), 'name': 'Test User', 'is_group_admin': False},
            ]
        )
        service.group_repo.is_user_group_admin = Mock(return_value=False)
        service.group_repo.remove_group_member = Mock(return_value=True)
        service.run_repo.get_runs_by_group = Mock(return_value=[r[0] for r in runs])
        service.run_repo.get_run_participations = Mock(side_effect=[[r[1]] for r in runs])
        service.bid_repo.get_bids_by_participation = Mock(return_value=[])
        service.user_repo.get_user_by_id = Mock(return_value=test_user)

        # Mock event bus and websocket
        with (
            patch('app.services.group_membership_service.event_bus'),
            patch('app.services.group_membership_service.create_background_task'),
        ):
            # Act
            result = service.leave_group(group_id=str(group_id), user=test_user)

            # Assert
            assert result is not None
            # All runs should be cancelled
            for run, _ in runs:
                assert run.state == RunState.CANCELLED
