"""Integration tests for DatabaseRunRepository."""

import uuid

import pytest

from app.core.exceptions import BadRequestError
from app.core.run_state import RunState
from app.repositories.database.run import DatabaseRunRepository

pytestmark = pytest.mark.integration


@pytest.fixture
def repo(db_session):
    """Create DatabaseRunRepository with the test session."""
    return DatabaseRunRepository(db_session)


class TestCreateRun:
    """Test create_run method."""

    async def test_creates_run_successfully(self, repo, create_user, create_group, create_store):
        """Test creating a run with required fields."""
        leader = await create_user(username='run_leader')
        group = await create_group(name='Run Group', creator=leader)
        store = await create_store(name='Run Store', creator=leader)

        run = await repo.create_run(group_id=group.id, store_id=store.id, leader_id=leader.id)
        assert run is not None
        assert run.id is not None
        assert run.group_id == group.id
        assert run.store_id == store.id
        assert run.state == RunState.PLANNING

    async def test_creates_run_with_comment(self, repo, create_user, create_group, create_store):
        """Test creating a run with a comment."""
        leader = await create_user(username='run_comment')
        group = await create_group(name='Comment Group', creator=leader)
        store = await create_store(name='Comment Store', creator=leader)

        run = await repo.create_run(
            group_id=group.id, store_id=store.id, leader_id=leader.id, comment='Going tomorrow'
        )
        assert run.comment == 'Going tomorrow'

    async def test_creates_run_with_leader_fee(self, repo, create_user, create_group, create_store):
        """Test creating a run with a leader fee."""
        leader = await create_user(username='run_fee')
        group = await create_group(name='Fee Group', creator=leader)
        store = await create_store(name='Fee Store', creator=leader)

        run = await repo.create_run(
            group_id=group.id,
            store_id=store.id,
            leader_id=leader.id,
            leader_fee=5.50,
        )
        assert float(run.leader_fee) == 5.50

    async def test_creates_leader_participation(
        self, repo, create_user, create_group, create_store
    ):
        """Test that creating a run also creates leader participation."""
        leader = await create_user(username='run_lpart')
        group = await create_group(name='LP Group', creator=leader)
        store = await create_store(name='LP Store', creator=leader)

        run = await repo.create_run(group_id=group.id, store_id=store.id, leader_id=leader.id)
        participation = await repo.get_participation(leader.id, run.id)
        assert participation is not None
        assert participation.is_leader is True


class TestGetRunById:
    """Test get_run_by_id method."""

    async def test_returns_run_when_exists(self, repo, create_user, create_group, create_store):
        """Test retrieving an existing run."""
        leader = await create_user(username='get_run')
        group = await create_group(name='Get Group', creator=leader)
        store = await create_store(name='Get Store', creator=leader)
        run = await repo.create_run(group_id=group.id, store_id=store.id, leader_id=leader.id)

        found = await repo.get_run_by_id(run.id)
        assert found is not None
        assert found.id == run.id

    async def test_returns_none_when_not_found(self, repo):
        """Test returns None for non-existent run."""
        result = await repo.get_run_by_id(uuid.uuid4())
        assert result is None


class TestGetRunsByGroup:
    """Test get_runs_by_group method."""

    async def test_returns_runs_for_group(self, repo, create_user, create_group, create_store):
        """Test retrieving all runs for a group."""
        leader = await create_user(username='grp_runs')
        group = await create_group(name='Runs Group', creator=leader)
        store = await create_store(name='Runs Store', creator=leader)
        await repo.create_run(group_id=group.id, store_id=store.id, leader_id=leader.id)
        await repo.create_run(group_id=group.id, store_id=store.id, leader_id=leader.id)

        runs = await repo.get_runs_by_group(group.id)
        assert len(runs) == 2

    async def test_returns_empty_for_group_with_no_runs(self, repo, create_group):
        """Test returns empty list for group with no runs."""
        group = await create_group(name='Empty Runs')
        runs = await repo.get_runs_by_group(group.id)
        assert runs == []


class TestGetCompletedCancelledRunsByGroup:
    """Test get_completed_cancelled_runs_by_group method."""

    async def test_returns_only_completed_and_cancelled(
        self, repo, db_session, create_user, create_group, create_store
    ):
        """Test only returns runs in completed/cancelled states."""
        leader = await create_user(username='cc_runs')
        group = await create_group(name='CC Group', creator=leader)
        store = await create_store(name='CC Store', creator=leader)

        # Create runs in different states
        await repo.create_run(group_id=group.id, store_id=store.id, leader_id=leader.id)
        run_completed = await repo.create_run(
            group_id=group.id, store_id=store.id, leader_id=leader.id
        )
        run_cancelled = await repo.create_run(
            group_id=group.id, store_id=store.id, leader_id=leader.id
        )

        # Transition runs through valid states to reach completed/cancelled
        await repo.update_run_state(run_completed.id, RunState.ACTIVE)
        await repo.update_run_state(run_completed.id, RunState.CONFIRMED)
        await repo.update_run_state(run_completed.id, RunState.SHOPPING)
        await repo.update_run_state(run_completed.id, RunState.DISTRIBUTING)
        await repo.update_run_state(run_completed.id, RunState.COMPLETED)

        await repo.update_run_state(run_cancelled.id, RunState.CANCELLED)

        results = await repo.get_completed_cancelled_runs_by_group(group.id)
        assert len(results) == 2
        states = {r.state for r in results}
        assert RunState.COMPLETED in states
        assert RunState.CANCELLED in states

    async def test_pagination(self, repo, create_user, create_group, create_store):
        """Test pagination with limit and offset."""
        leader = await create_user(username='pg_runs')
        group = await create_group(name='PG Group', creator=leader)
        store = await create_store(name='PG Store', creator=leader)

        # Create 3 cancelled runs
        for _ in range(3):
            run = await repo.create_run(group_id=group.id, store_id=store.id, leader_id=leader.id)
            await repo.update_run_state(run.id, RunState.CANCELLED)

        page1 = await repo.get_completed_cancelled_runs_by_group(group.id, limit=2, offset=0)
        page2 = await repo.get_completed_cancelled_runs_by_group(group.id, limit=2, offset=2)
        assert len(page1) == 2
        assert len(page2) == 1


class TestUpdateRunState:
    """Test update_run_state method."""

    async def test_valid_transition(self, repo, create_user, create_group, create_store):
        """Test valid state transition from planning to active."""
        leader = await create_user(username='state_u')
        group = await create_group(name='State Group', creator=leader)
        store = await create_store(name='State Store', creator=leader)
        run = await repo.create_run(group_id=group.id, store_id=store.id, leader_id=leader.id)

        updated = await repo.update_run_state(run.id, RunState.ACTIVE)
        assert updated is not None
        assert updated.state == RunState.ACTIVE
        assert updated.active_at is not None

    async def test_invalid_transition_raises(self, repo, create_user, create_group, create_store):
        """Test invalid state transition raises error."""
        leader = await create_user(username='inv_state')
        group = await create_group(name='Inv Group', creator=leader)
        store = await create_store(name='Inv Store', creator=leader)
        run = await repo.create_run(group_id=group.id, store_id=store.id, leader_id=leader.id)

        with pytest.raises(BadRequestError):
            # Cannot go from PLANNING directly to COMPLETED
            await repo.update_run_state(run.id, RunState.COMPLETED)

    async def test_returns_none_for_nonexistent_run(self, repo):
        """Test returns None for non-existent run."""
        result = await repo.update_run_state(uuid.uuid4(), RunState.ACTIVE)
        assert result is None


class TestUpdateRunComment:
    """Test update_run_comment method."""

    async def test_updates_comment(self, repo, create_user, create_group, create_store):
        """Test updating a run's comment."""
        leader = await create_user(username='comment_u')
        group = await create_group(name='Comment Grp', creator=leader)
        store = await create_store(name='Comment Store', creator=leader)
        run = await repo.create_run(group_id=group.id, store_id=store.id, leader_id=leader.id)

        updated = await repo.update_run_comment(run.id, 'New comment')
        assert updated.comment == 'New comment'

    async def test_clears_comment(self, repo, create_user, create_group, create_store):
        """Test clearing a run's comment."""
        leader = await create_user(username='clear_c')
        group = await create_group(name='Clear Grp', creator=leader)
        store = await create_store(name='Clear Store', creator=leader)
        run = await repo.create_run(
            group_id=group.id, store_id=store.id, leader_id=leader.id, comment='Old'
        )
        updated = await repo.update_run_comment(run.id, None)
        assert updated.comment is None

    async def test_returns_none_for_nonexistent_run(self, repo):
        """Test returns None for non-existent run."""
        result = await repo.update_run_comment(uuid.uuid4(), 'x')
        assert result is None


class TestUpdateLeaderFee:
    """Test update_leader_fee method."""

    async def test_updates_fee(self, repo, create_user, create_group, create_store):
        """Test updating leader fee."""
        leader = await create_user(username='fee_u')
        group = await create_group(name='Fee Grp', creator=leader)
        store = await create_store(name='Fee Store', creator=leader)
        run = await repo.create_run(group_id=group.id, store_id=store.id, leader_id=leader.id)

        updated = await repo.update_leader_fee(run.id, 3.75)
        assert float(updated.leader_fee) == 3.75

    async def test_clears_fee(self, repo, create_user, create_group, create_store):
        """Test clearing leader fee."""
        leader = await create_user(username='clear_fee')
        group = await create_group(name='ClearFee Grp', creator=leader)
        store = await create_store(name='ClearFee Store', creator=leader)
        run = await repo.create_run(
            group_id=group.id, store_id=store.id, leader_id=leader.id, leader_fee=10.0
        )
        updated = await repo.update_leader_fee(run.id, None)
        assert updated.leader_fee is None

    async def test_returns_none_for_nonexistent_run(self, repo):
        """Test returns None for non-existent run."""
        result = await repo.update_leader_fee(uuid.uuid4(), 5.0)
        assert result is None


class TestCreateParticipation:
    """Test create_participation method."""

    async def test_creates_participation(self, repo, create_user, create_group, create_store):
        """Test creating a new participation."""
        leader = await create_user(username='part_leader')
        participant = await create_user(username='part_user')
        group = await create_group(name='Part Group', creator=leader)
        store = await create_store(name='Part Store', creator=leader)
        run = await repo.create_run(group_id=group.id, store_id=store.id, leader_id=leader.id)

        participation = await repo.create_participation(user_id=participant.id, run_id=run.id)
        assert participation is not None
        assert participation.user_id == participant.id
        assert participation.run_id == run.id
        assert participation.is_leader is False
        assert participation.is_helper is False

    async def test_creates_helper_participation(
        self, repo, create_user, create_group, create_store
    ):
        """Test creating a helper participation."""
        leader = await create_user(username='help_leader')
        helper = await create_user(username='help_user')
        group = await create_group(name='Help Group', creator=leader)
        store = await create_store(name='Help Store', creator=leader)
        run = await repo.create_run(group_id=group.id, store_id=store.id, leader_id=leader.id)

        participation = await repo.create_participation(
            user_id=helper.id, run_id=run.id, is_helper=True
        )
        assert participation.is_helper is True


class TestGetParticipation:
    """Test get_participation method."""

    async def test_returns_participation_when_exists(
        self, repo, create_user, create_group, create_store
    ):
        """Test finding an existing participation."""
        leader = await create_user(username='gp_leader')
        group = await create_group(name='GP Group', creator=leader)
        store = await create_store(name='GP Store', creator=leader)
        run = await repo.create_run(group_id=group.id, store_id=store.id, leader_id=leader.id)

        found = await repo.get_participation(leader.id, run.id)
        assert found is not None
        assert found.is_leader is True

    async def test_returns_none_when_not_found(self, repo, create_user, create_group, create_store):
        """Test returns None when user has no participation."""
        leader = await create_user(username='gp_leader2')
        outsider = await create_user(username='gp_outsider')
        group = await create_group(name='GP2 Group', creator=leader)
        store = await create_store(name='GP2 Store', creator=leader)
        run = await repo.create_run(group_id=group.id, store_id=store.id, leader_id=leader.id)

        result = await repo.get_participation(outsider.id, run.id)
        assert result is None


class TestGetRunParticipations:
    """Test get_run_participations method."""

    async def test_returns_all_participations(self, repo, create_user, create_group, create_store):
        """Test returns all participations for a run."""
        leader = await create_user(username='rp_leader')
        member = await create_user(username='rp_member')
        group = await create_group(name='RP Group', creator=leader)
        store = await create_store(name='RP Store', creator=leader)
        run = await repo.create_run(group_id=group.id, store_id=store.id, leader_id=leader.id)
        await repo.create_participation(user_id=member.id, run_id=run.id)

        participations = await repo.get_run_participations(run.id)
        assert len(participations) == 2

    async def test_returns_empty_for_nonexistent_run(self, repo):
        """Test returns empty list for non-existent run."""
        result = await repo.get_run_participations(uuid.uuid4())
        assert result == []


class TestGetRunParticipationsWithUsers:
    """Test get_run_participations_with_users method."""

    async def test_loads_user_data(self, repo, create_user, create_group, create_store):
        """Test that user objects are eagerly loaded."""
        leader = await create_user(username='rpwu_leader')
        group = await create_group(name='RPWU Group', creator=leader)
        store = await create_store(name='RPWU Store', creator=leader)
        run = await repo.create_run(group_id=group.id, store_id=store.id, leader_id=leader.id)

        participations = await repo.get_run_participations_with_users(run.id)
        assert len(participations) == 1
        assert participations[0].user is not None
        assert participations[0].user.username == 'rpwu_leader'


class TestUpdateParticipationReady:
    """Test update_participation_ready method."""

    async def test_sets_ready_true(self, repo, create_user, create_group, create_store):
        """Test setting participation ready to True."""
        leader = await create_user(username='ready_leader')
        group = await create_group(name='Ready Group', creator=leader)
        store = await create_store(name='Ready Store', creator=leader)
        run = await repo.create_run(group_id=group.id, store_id=store.id, leader_id=leader.id)
        participation = await repo.get_participation(leader.id, run.id)

        updated = await repo.update_participation_ready(participation.id, True)
        assert updated is not None
        assert updated.is_ready is True

    async def test_sets_ready_false(self, repo, create_user, create_group, create_store):
        """Test setting participation ready back to False."""
        leader = await create_user(username='unready')
        group = await create_group(name='Unready Group', creator=leader)
        store = await create_store(name='Unready Store', creator=leader)
        run = await repo.create_run(group_id=group.id, store_id=store.id, leader_id=leader.id)
        participation = await repo.get_participation(leader.id, run.id)
        await repo.update_participation_ready(participation.id, True)

        updated = await repo.update_participation_ready(participation.id, False)
        assert updated.is_ready is False

    async def test_returns_none_for_nonexistent(self, repo):
        """Test returns None for non-existent participation."""
        result = await repo.update_participation_ready(uuid.uuid4(), True)
        assert result is None


class TestUpdateParticipationHelper:
    """Test update_participation_helper method."""

    async def test_sets_helper_true(self, repo, create_user, create_group, create_store):
        """Test setting participation helper status to True."""
        leader = await create_user(username='helper_l')
        member = await create_user(username='helper_m')
        group = await create_group(name='Helper Group', creator=leader)
        store = await create_store(name='Helper Store', creator=leader)
        run = await repo.create_run(group_id=group.id, store_id=store.id, leader_id=leader.id)
        await repo.create_participation(user_id=member.id, run_id=run.id)

        updated = await repo.update_participation_helper(member.id, run.id, True)
        assert updated is not None
        assert updated.is_helper is True

    async def test_sets_helper_false(self, repo, create_user, create_group, create_store):
        """Test setting helper status back to False."""
        leader = await create_user(username='unhelp_l')
        member = await create_user(username='unhelp_m')
        group = await create_group(name='Unhelp Group', creator=leader)
        store = await create_store(name='Unhelp Store', creator=leader)
        run = await repo.create_run(group_id=group.id, store_id=store.id, leader_id=leader.id)
        await repo.create_participation(user_id=member.id, run_id=run.id, is_helper=True)

        updated = await repo.update_participation_helper(member.id, run.id, False)
        assert updated.is_helper is False

    async def test_returns_none_for_nonexistent(
        self, repo, create_user, create_group, create_store
    ):
        """Test returns None when participation does not exist."""
        leader = await create_user(username='nohelp_l')
        outsider = await create_user(username='nohelp_o')
        group = await create_group(name='NoHelp Group', creator=leader)
        store = await create_store(name='NoHelp Store', creator=leader)
        run = await repo.create_run(group_id=group.id, store_id=store.id, leader_id=leader.id)

        result = await repo.update_participation_helper(outsider.id, run.id, True)
        assert result is None
