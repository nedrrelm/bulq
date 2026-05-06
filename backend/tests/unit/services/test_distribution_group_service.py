"""Unit tests for DistributionGroupService."""

from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest

from app.core.error_codes import (
    CANNOT_DELETE_DEFAULT_DISTRIBUTION_GROUP,
    DISTRIBUTION_GROUP_NOT_FOUND,
    NOT_RUN_LEADER,
    NOT_RUN_LEADER_OR_HELPER,
    PARTICIPATION_NOT_FOUND,
    RUN_NOT_FOUND,
    RUN_NOT_IN_DISTRIBUTING_STATE,
)
from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.core.models import DistributionGroup, ProductBid, Run, RunParticipation
from app.core.run_state import RunState
from app.events.domain_events import DistributionUpdatedEvent
from app.services.distribution_group_service import DistributionGroupService


def _mock_run(run_id=None, state=RunState.DISTRIBUTING):
    mock = Mock(spec=Run)
    mock.id = run_id or uuid4()
    mock.state = state
    mock.group_id = uuid4()
    return mock


def _mock_participation(user_id=None, run_id=None, is_leader=True, is_helper=False, group_id=None):
    mock = Mock(spec=RunParticipation)
    mock.id = uuid4()
    mock.user_id = user_id or uuid4()
    mock.run_id = run_id or uuid4()
    mock.is_leader = is_leader
    mock.is_helper = is_helper
    mock.distribution_group_id = group_id
    return mock


def _mock_group(run_id=None, group_id=None, is_default=True, name='1'):
    mock = Mock(spec=DistributionGroup)
    mock.id = group_id or uuid4()
    mock.run_id = run_id or uuid4()
    mock.name = name
    mock.is_default = is_default
    mock.is_done = False
    mock.sort_order = 0
    return mock


def _mock_bid(
    participation_id=None, interested_only=False, distributed_quantity=5.0, is_picked_up=False
):
    mock = Mock(spec=ProductBid)
    mock.id = uuid4()
    mock.participation_id = participation_id or uuid4()
    mock.interested_only = interested_only
    mock.distributed_quantity = distributed_quantity
    mock.is_picked_up = is_picked_up
    return mock


class TestEnsureDefaultGroup:
    """Test cases for DistributionGroupService.ensure_default_group()."""

    async def test_creates_default_group_when_none_exists(self, test_user):
        """When no default group exists, create one and assign all participations."""
        mock_db = AsyncMock()
        run_id = uuid4()
        group_id = uuid4()

        mock_group = _mock_group(run_id=run_id, group_id=group_id)
        mock_part = _mock_participation(run_id=run_id, group_id=None)

        service = DistributionGroupService(mock_db)
        service.dist_group_repo.get_default_group = AsyncMock(return_value=None)
        service.dist_group_repo.create_group = AsyncMock(return_value=mock_group)
        service.dist_group_repo.assign_participation_to_group = AsyncMock()
        service.run_repo.get_run_participations = AsyncMock(return_value=[mock_part])

        await service.ensure_default_group(run_id)

        service.dist_group_repo.create_group.assert_called_once_with(
            run_id=run_id, name='1', is_default=True, sort_order=0
        )
        service.dist_group_repo.assign_participation_to_group.assert_called_once_with(
            mock_part.id, group_id
        )

    async def test_idempotent_when_default_exists(self, test_user):
        """When default group already exists, don't create another."""
        mock_db = AsyncMock()
        run_id = uuid4()
        existing_group = _mock_group(run_id=run_id)

        service = DistributionGroupService(mock_db)
        service.dist_group_repo.get_default_group = AsyncMock(return_value=existing_group)
        service.dist_group_repo.create_group = AsyncMock()
        service.run_repo.get_run_participations = AsyncMock(return_value=[])

        await service.ensure_default_group(run_id)

        service.dist_group_repo.create_group.assert_not_called()

    async def test_assigns_unassigned_participations(self, test_user):
        """Participations with no group get assigned to default."""
        mock_db = AsyncMock()
        run_id = uuid4()
        group_id = uuid4()
        existing_group = _mock_group(run_id=run_id, group_id=group_id)

        assigned_part = _mock_participation(group_id=group_id)
        unassigned_part = _mock_participation(group_id=None)

        service = DistributionGroupService(mock_db)
        service.dist_group_repo.get_default_group = AsyncMock(return_value=existing_group)
        service.dist_group_repo.assign_participation_to_group = AsyncMock()
        service.run_repo.get_run_participations = AsyncMock(
            return_value=[assigned_part, unassigned_part]
        )

        await service.ensure_default_group(run_id)

        # Only the unassigned participation should be assigned
        service.dist_group_repo.assign_participation_to_group.assert_called_once_with(
            unassigned_part.id, group_id
        )


class TestCreateGroup:
    """Test cases for DistributionGroupService.create_group()."""

    async def test_create_group_success(self, test_user):
        """Leader in distributing state can create a new group."""
        mock_db = AsyncMock()
        run_id = uuid4()
        mock_run = _mock_run(run_id=run_id)
        leader_part = _mock_participation(user_id=test_user.id, is_leader=True)
        default_group = _mock_group(run_id=run_id, name='1')
        new_group = _mock_group(run_id=run_id, name='2', is_default=False)

        service = DistributionGroupService(mock_db)
        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(return_value=leader_part)
        service.run_repo.get_run_participations = AsyncMock(return_value=[])
        service.dist_group_repo.get_default_group = AsyncMock(return_value=default_group)
        service.dist_group_repo.get_groups_by_run = AsyncMock(return_value=[default_group])
        service.dist_group_repo.create_group = AsyncMock(return_value=new_group)

        with patch('app.services.distribution_group_service.event_bus'):
            result = await service.create_group(run_id, test_user)

        assert result.code == 'DISTRIBUTION_GROUP_CREATED'
        service.dist_group_repo.create_group.assert_called_once_with(
            run_id=run_id, name='2', is_default=False, sort_order=1
        )

    async def test_create_group_not_leader(self, test_user):
        """Non-leader cannot create groups."""
        mock_db = AsyncMock()
        run_id = uuid4()
        mock_run = _mock_run(run_id=run_id)
        non_leader = _mock_participation(user_id=test_user.id, is_leader=False)

        service = DistributionGroupService(mock_db)
        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(return_value=non_leader)

        with pytest.raises(ForbiddenError) as exc_info:
            await service.create_group(run_id, test_user)

        assert exc_info.value.code == NOT_RUN_LEADER

    async def test_create_group_wrong_state(self, test_user):
        """Cannot create groups outside distributing state."""
        mock_db = AsyncMock()
        run_id = uuid4()
        mock_run = _mock_run(run_id=run_id, state=RunState.ACTIVE)
        leader_part = _mock_participation(user_id=test_user.id, is_leader=True)

        service = DistributionGroupService(mock_db)
        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(return_value=leader_part)

        with pytest.raises(BadRequestError) as exc_info:
            await service.create_group(run_id, test_user)

        assert exc_info.value.code == RUN_NOT_IN_DISTRIBUTING_STATE

    async def test_create_group_emits_event(self, test_user):
        """Creating a group emits a DistributionUpdatedEvent."""
        mock_db = AsyncMock()
        run_id = uuid4()
        mock_run = _mock_run(run_id=run_id)
        leader_part = _mock_participation(user_id=test_user.id, is_leader=True)
        default_group = _mock_group(run_id=run_id)
        new_group = _mock_group(run_id=run_id, is_default=False, name='2')

        service = DistributionGroupService(mock_db)
        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(return_value=leader_part)
        service.run_repo.get_run_participations = AsyncMock(return_value=[])
        service.dist_group_repo.get_default_group = AsyncMock(return_value=default_group)
        service.dist_group_repo.get_groups_by_run = AsyncMock(return_value=[default_group])
        service.dist_group_repo.create_group = AsyncMock(return_value=new_group)

        with patch('app.services.distribution_group_service.event_bus') as mock_event_bus:
            await service.create_group(run_id, test_user)
            mock_event_bus.emit.assert_called_once()
            event = mock_event_bus.emit.call_args[0][0]
            assert isinstance(event, DistributionUpdatedEvent)
            assert event.action == 'group_created'

    async def test_create_group_run_not_found(self, test_user):
        """Creating group for non-existent run raises NotFoundError."""
        mock_db = AsyncMock()
        run_id = uuid4()

        service = DistributionGroupService(mock_db)
        service.run_repo.get_run_by_id = AsyncMock(return_value=None)

        with pytest.raises(NotFoundError) as exc_info:
            await service.create_group(run_id, test_user)

        assert exc_info.value.code == RUN_NOT_FOUND


class TestDeleteGroup:
    """Test cases for DistributionGroupService.delete_group()."""

    async def test_delete_group_success(self, test_user):
        """Deleting a non-default group reassigns users to default."""
        mock_db = AsyncMock()
        run_id = uuid4()
        group_id = uuid4()
        default_group_id = uuid4()
        mock_run = _mock_run(run_id=run_id)
        leader_part = _mock_participation(user_id=test_user.id, is_leader=True)
        target_group = _mock_group(run_id=run_id, group_id=group_id, is_default=False, name='2')
        default_group = _mock_group(run_id=run_id, group_id=default_group_id)

        user_in_group = _mock_participation(group_id=group_id)

        service = DistributionGroupService(mock_db)
        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(return_value=leader_part)
        service.run_repo.get_run_participations = AsyncMock(return_value=[user_in_group])
        service.dist_group_repo.get_group_by_id = AsyncMock(return_value=target_group)
        service.dist_group_repo.get_default_group = AsyncMock(return_value=default_group)
        service.dist_group_repo.delete_group = AsyncMock(return_value=True)
        service.dist_group_repo.assign_participation_to_group = AsyncMock()

        with patch('app.services.distribution_group_service.event_bus'):
            result = await service.delete_group(run_id, group_id, test_user)

        assert result.code == 'DISTRIBUTION_GROUP_DELETED'
        service.dist_group_repo.assign_participation_to_group.assert_called_once_with(
            user_in_group.id, default_group_id
        )
        service.dist_group_repo.delete_group.assert_called_once_with(group_id)

    async def test_delete_group_not_found(self, test_user):
        """Deleting a non-existent group raises NotFoundError."""
        mock_db = AsyncMock()
        run_id = uuid4()
        group_id = uuid4()
        mock_run = _mock_run(run_id=run_id)
        leader_part = _mock_participation(user_id=test_user.id, is_leader=True)

        service = DistributionGroupService(mock_db)
        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(return_value=leader_part)
        service.dist_group_repo.get_group_by_id = AsyncMock(return_value=None)

        with pytest.raises(NotFoundError) as exc_info:
            await service.delete_group(run_id, group_id, test_user)

        assert exc_info.value.code == DISTRIBUTION_GROUP_NOT_FOUND

    async def test_delete_default_group_fails(self, test_user):
        """Cannot delete the default distribution group."""
        mock_db = AsyncMock()
        run_id = uuid4()
        group_id = uuid4()
        mock_run = _mock_run(run_id=run_id)
        leader_part = _mock_participation(user_id=test_user.id, is_leader=True)
        default_group = _mock_group(run_id=run_id, group_id=group_id, is_default=True)

        service = DistributionGroupService(mock_db)
        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(return_value=leader_part)
        service.dist_group_repo.get_group_by_id = AsyncMock(return_value=default_group)

        with pytest.raises(BadRequestError) as exc_info:
            await service.delete_group(run_id, group_id, test_user)

        assert exc_info.value.code == CANNOT_DELETE_DEFAULT_DISTRIBUTION_GROUP

    async def test_delete_group_not_leader(self, test_user):
        """Non-leader cannot delete groups."""
        mock_db = AsyncMock()
        run_id = uuid4()
        mock_run = _mock_run(run_id=run_id)
        non_leader = _mock_participation(user_id=test_user.id, is_leader=False)

        service = DistributionGroupService(mock_db)
        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(return_value=non_leader)

        with pytest.raises(ForbiddenError) as exc_info:
            await service.delete_group(run_id, uuid4(), test_user)

        assert exc_info.value.code == NOT_RUN_LEADER


class TestAssignUserToGroup:
    """Test cases for DistributionGroupService.assign_user_to_group()."""

    async def test_assign_user_success(self, test_user):
        """Leader can assign a user to a distribution group."""
        mock_db = AsyncMock()
        run_id = uuid4()
        group_id = uuid4()
        target_user_id = uuid4()
        mock_run = _mock_run(run_id=run_id)
        leader_part = _mock_participation(user_id=test_user.id, is_leader=True)
        target_part = _mock_participation(user_id=target_user_id)
        target_group = _mock_group(run_id=run_id, group_id=group_id, is_default=False)

        service = DistributionGroupService(mock_db)
        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(side_effect=[leader_part, target_part])
        service.dist_group_repo.get_group_by_id = AsyncMock(return_value=target_group)
        service.dist_group_repo.assign_participation_to_group = AsyncMock()

        with patch('app.services.distribution_group_service.event_bus'):
            result = await service.assign_user_to_group(run_id, group_id, target_user_id, test_user)

        assert result.code == 'USER_ASSIGNED_TO_DISTRIBUTION_GROUP'
        service.dist_group_repo.assign_participation_to_group.assert_called_once_with(
            target_part.id, group_id
        )

    async def test_assign_user_group_not_found(self, test_user):
        """Assigning to non-existent group raises NotFoundError."""
        mock_db = AsyncMock()
        run_id = uuid4()
        mock_run = _mock_run(run_id=run_id)
        leader_part = _mock_participation(user_id=test_user.id, is_leader=True)

        service = DistributionGroupService(mock_db)
        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(return_value=leader_part)
        service.dist_group_repo.get_group_by_id = AsyncMock(return_value=None)

        with pytest.raises(NotFoundError) as exc_info:
            await service.assign_user_to_group(run_id, uuid4(), uuid4(), test_user)

        assert exc_info.value.code == DISTRIBUTION_GROUP_NOT_FOUND

    async def test_assign_user_not_participant(self, test_user):
        """Assigning a non-participant raises NotFoundError."""
        mock_db = AsyncMock()
        run_id = uuid4()
        group_id = uuid4()
        mock_run = _mock_run(run_id=run_id)
        leader_part = _mock_participation(user_id=test_user.id, is_leader=True)
        target_group = _mock_group(run_id=run_id, group_id=group_id)

        service = DistributionGroupService(mock_db)
        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(side_effect=[leader_part, None])
        service.dist_group_repo.get_group_by_id = AsyncMock(return_value=target_group)

        with pytest.raises(NotFoundError) as exc_info:
            await service.assign_user_to_group(run_id, group_id, uuid4(), test_user)

        assert exc_info.value.code == PARTICIPATION_NOT_FOUND

    async def test_assign_user_not_leader(self, test_user):
        """Non-leader cannot assign users to groups."""
        mock_db = AsyncMock()
        run_id = uuid4()
        mock_run = _mock_run(run_id=run_id)
        non_leader = _mock_participation(user_id=test_user.id, is_leader=False)

        service = DistributionGroupService(mock_db)
        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(return_value=non_leader)

        with pytest.raises(ForbiddenError) as exc_info:
            await service.assign_user_to_group(run_id, uuid4(), uuid4(), test_user)

        assert exc_info.value.code == NOT_RUN_LEADER


class TestMarkGroupDone:
    """Test cases for DistributionGroupService.mark_group_done()."""

    async def test_mark_group_done_success(self, test_user):
        """Leader marks group done, all bids in group become picked up."""
        mock_db = AsyncMock()
        run_id = uuid4()
        group_id = uuid4()
        mock_run = _mock_run(run_id=run_id)
        leader_part = _mock_participation(user_id=test_user.id, is_leader=True, group_id=group_id)
        group_user_part = _mock_participation(group_id=group_id)
        other_part = _mock_participation(group_id=uuid4())

        group = _mock_group(run_id=run_id, group_id=group_id)

        bid_in_group = _mock_bid(participation_id=group_user_part.id, is_picked_up=False)
        bid_outside = _mock_bid(participation_id=other_part.id, is_picked_up=False)

        service = DistributionGroupService(mock_db)
        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(return_value=leader_part)
        service.run_repo.get_run_participations = AsyncMock(
            return_value=[group_user_part, other_part]
        )
        service.dist_group_repo.get_group_by_id = AsyncMock(return_value=group)
        service.dist_group_repo.mark_group_done = AsyncMock(return_value=group)
        service.bid_repo.get_bids_by_run = AsyncMock(return_value=[bid_in_group, bid_outside])
        service.bid_repo.commit_changes = AsyncMock()

        with patch('app.services.distribution_group_service.event_bus'):
            result = await service.mark_group_done(run_id, group_id, test_user)

        assert result.code == 'DISTRIBUTION_GROUP_MARKED_DONE'
        assert bid_in_group.is_picked_up is True
        assert bid_outside.is_picked_up is False  # not in this group
        service.dist_group_repo.mark_group_done.assert_called_once_with(group_id, is_done=True)

    async def test_mark_group_done_helper_allowed(self, test_user):
        """Helper can also mark group as done."""
        mock_db = AsyncMock()
        run_id = uuid4()
        group_id = uuid4()
        mock_run = _mock_run(run_id=run_id)
        helper_part = _mock_participation(user_id=test_user.id, is_leader=False, is_helper=True)
        group = _mock_group(run_id=run_id, group_id=group_id)

        service = DistributionGroupService(mock_db)
        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(return_value=helper_part)
        service.run_repo.get_run_participations = AsyncMock(return_value=[])
        service.dist_group_repo.get_group_by_id = AsyncMock(return_value=group)
        service.dist_group_repo.mark_group_done = AsyncMock(return_value=group)
        service.bid_repo.get_bids_by_run = AsyncMock(return_value=[])
        service.bid_repo.commit_changes = AsyncMock()

        with patch('app.services.distribution_group_service.event_bus'):
            result = await service.mark_group_done(run_id, group_id, test_user)

        assert result.code == 'DISTRIBUTION_GROUP_MARKED_DONE'

    async def test_mark_group_done_not_leader_or_helper(self, test_user):
        """Regular participant cannot mark group as done."""
        mock_db = AsyncMock()
        run_id = uuid4()
        mock_run = _mock_run(run_id=run_id)
        regular_part = _mock_participation(user_id=test_user.id, is_leader=False, is_helper=False)

        service = DistributionGroupService(mock_db)
        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(return_value=regular_part)

        with pytest.raises(ForbiddenError) as exc_info:
            await service.mark_group_done(run_id, uuid4(), test_user)

        assert exc_info.value.code == NOT_RUN_LEADER_OR_HELPER

    async def test_mark_group_done_skips_interested_only(self, test_user):
        """Interested-only bids are not marked as picked up."""
        mock_db = AsyncMock()
        run_id = uuid4()
        group_id = uuid4()
        mock_run = _mock_run(run_id=run_id)
        leader_part = _mock_participation(user_id=test_user.id, is_leader=True)
        group_part = _mock_participation(group_id=group_id)
        group = _mock_group(run_id=run_id, group_id=group_id)

        interested_bid = _mock_bid(
            participation_id=group_part.id, interested_only=True, is_picked_up=False
        )
        regular_bid = _mock_bid(
            participation_id=group_part.id, interested_only=False, is_picked_up=False
        )

        service = DistributionGroupService(mock_db)
        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(return_value=leader_part)
        service.run_repo.get_run_participations = AsyncMock(return_value=[group_part])
        service.dist_group_repo.get_group_by_id = AsyncMock(return_value=group)
        service.dist_group_repo.mark_group_done = AsyncMock(return_value=group)
        service.bid_repo.get_bids_by_run = AsyncMock(return_value=[interested_bid, regular_bid])
        service.bid_repo.commit_changes = AsyncMock()

        with patch('app.services.distribution_group_service.event_bus'):
            await service.mark_group_done(run_id, group_id, test_user)

        assert interested_bid.is_picked_up is False
        assert regular_bid.is_picked_up is True

    async def test_mark_group_done_emits_event(self, test_user):
        """Marking group done emits a DistributionUpdatedEvent."""
        mock_db = AsyncMock()
        run_id = uuid4()
        group_id = uuid4()
        mock_run = _mock_run(run_id=run_id)
        leader_part = _mock_participation(user_id=test_user.id, is_leader=True)
        group = _mock_group(run_id=run_id, group_id=group_id)

        service = DistributionGroupService(mock_db)
        service.run_repo.get_run_by_id = AsyncMock(return_value=mock_run)
        service.run_repo.get_participation = AsyncMock(return_value=leader_part)
        service.run_repo.get_run_participations = AsyncMock(return_value=[])
        service.dist_group_repo.get_group_by_id = AsyncMock(return_value=group)
        service.dist_group_repo.mark_group_done = AsyncMock(return_value=group)
        service.bid_repo.get_bids_by_run = AsyncMock(return_value=[])
        service.bid_repo.commit_changes = AsyncMock()

        with patch('app.services.distribution_group_service.event_bus') as mock_event_bus:
            await service.mark_group_done(run_id, group_id, test_user)
            mock_event_bus.emit.assert_called_once()
            event = mock_event_bus.emit.call_args[0][0]
            assert isinstance(event, DistributionUpdatedEvent)
            assert event.action == 'group_marked_done'
