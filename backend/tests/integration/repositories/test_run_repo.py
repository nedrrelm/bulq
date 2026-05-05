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

    def test_creates_run_successfully(self, repo, create_user, create_group, create_store):
        """Test creating a run with required fields."""
        leader = create_user(username='run_leader')
        group = create_group(name='Run Group', creator=leader)
        store = create_store(name='Run Store', creator=leader)

        run = repo.create_run(group_id=group.id, store_id=store.id, leader_id=leader.id)
        assert run is not None
        assert run.id is not None
        assert run.group_id == group.id
        assert run.store_id == store.id
        assert run.state == RunState.PLANNING

    def test_creates_run_with_comment(self, repo, create_user, create_group, create_store):
        """Test creating a run with a comment."""
        leader = create_user(username='run_comment')
        group = create_group(name='Comment Group', creator=leader)
        store = create_store(name='Comment Store', creator=leader)

        run = repo.create_run(
            group_id=group.id, store_id=store.id, leader_id=leader.id, comment='Going tomorrow'
        )
        assert run.comment == 'Going tomorrow'

    def test_creates_run_with_leader_fee(self, repo, create_user, create_group, create_store):
        """Test creating a run with a leader fee."""
        leader = create_user(username='run_fee')
        group = create_group(name='Fee Group', creator=leader)
        store = create_store(name='Fee Store', creator=leader)

        run = repo.create_run(
            group_id=group.id,
            store_id=store.id,
            leader_id=leader.id,
            leader_fee=5.50,
        )
        assert float(run.leader_fee) == 5.50

    def test_creates_leader_participation(self, repo, create_user, create_group, create_store):
        """Test that creating a run also creates leader participation."""
        leader = create_user(username='run_lpart')
        group = create_group(name='LP Group', creator=leader)
        store = create_store(name='LP Store', creator=leader)

        run = repo.create_run(group_id=group.id, store_id=store.id, leader_id=leader.id)
        participation = repo.get_participation(leader.id, run.id)
        assert participation is not None
        assert participation.is_leader is True


class TestGetRunById:
    """Test get_run_by_id method."""

    def test_returns_run_when_exists(self, repo, create_user, create_group, create_store):
        """Test retrieving an existing run."""
        leader = create_user(username='get_run')
        group = create_group(name='Get Group', creator=leader)
        store = create_store(name='Get Store', creator=leader)
        run = repo.create_run(group_id=group.id, store_id=store.id, leader_id=leader.id)

        found = repo.get_run_by_id(run.id)
        assert found is not None
        assert found.id == run.id

    def test_returns_none_when_not_found(self, repo):
        """Test returns None for non-existent run."""
        result = repo.get_run_by_id(uuid.uuid4())
        assert result is None


class TestGetRunsByGroup:
    """Test get_runs_by_group method."""

    def test_returns_runs_for_group(self, repo, create_user, create_group, create_store):
        """Test retrieving all runs for a group."""
        leader = create_user(username='grp_runs')
        group = create_group(name='Runs Group', creator=leader)
        store = create_store(name='Runs Store', creator=leader)
        repo.create_run(group_id=group.id, store_id=store.id, leader_id=leader.id)
        repo.create_run(group_id=group.id, store_id=store.id, leader_id=leader.id)

        runs = repo.get_runs_by_group(group.id)
        assert len(runs) == 2

    def test_returns_empty_for_group_with_no_runs(self, repo, create_group):
        """Test returns empty list for group with no runs."""
        group = create_group(name='Empty Runs')
        runs = repo.get_runs_by_group(group.id)
        assert runs == []


class TestGetCompletedCancelledRunsByGroup:
    """Test get_completed_cancelled_runs_by_group method."""

    def test_returns_only_completed_and_cancelled(
        self, repo, db_session, create_user, create_group, create_store
    ):
        """Test only returns runs in completed/cancelled states."""
        leader = create_user(username='cc_runs')
        group = create_group(name='CC Group', creator=leader)
        store = create_store(name='CC Store', creator=leader)

        # Create runs in different states
        repo.create_run(group_id=group.id, store_id=store.id, leader_id=leader.id)
        run_completed = repo.create_run(group_id=group.id, store_id=store.id, leader_id=leader.id)
        run_cancelled = repo.create_run(group_id=group.id, store_id=store.id, leader_id=leader.id)

        # Transition runs through valid states to reach completed/cancelled
        repo.update_run_state(run_completed.id, RunState.ACTIVE)
        repo.update_run_state(run_completed.id, RunState.CONFIRMED)
        repo.update_run_state(run_completed.id, RunState.SHOPPING)
        repo.update_run_state(run_completed.id, RunState.DISTRIBUTING)
        repo.update_run_state(run_completed.id, RunState.COMPLETED)

        repo.update_run_state(run_cancelled.id, RunState.CANCELLED)

        results = repo.get_completed_cancelled_runs_by_group(group.id)
        assert len(results) == 2
        states = {r.state for r in results}
        assert RunState.COMPLETED in states
        assert RunState.CANCELLED in states

    def test_pagination(self, repo, create_user, create_group, create_store):
        """Test pagination with limit and offset."""
        leader = create_user(username='pg_runs')
        group = create_group(name='PG Group', creator=leader)
        store = create_store(name='PG Store', creator=leader)

        # Create 3 cancelled runs
        for _ in range(3):
            run = repo.create_run(group_id=group.id, store_id=store.id, leader_id=leader.id)
            repo.update_run_state(run.id, RunState.CANCELLED)

        page1 = repo.get_completed_cancelled_runs_by_group(group.id, limit=2, offset=0)
        page2 = repo.get_completed_cancelled_runs_by_group(group.id, limit=2, offset=2)
        assert len(page1) == 2
        assert len(page2) == 1


class TestUpdateRunState:
    """Test update_run_state method."""

    def test_valid_transition(self, repo, create_user, create_group, create_store):
        """Test valid state transition from planning to active."""
        leader = create_user(username='state_u')
        group = create_group(name='State Group', creator=leader)
        store = create_store(name='State Store', creator=leader)
        run = repo.create_run(group_id=group.id, store_id=store.id, leader_id=leader.id)

        updated = repo.update_run_state(run.id, RunState.ACTIVE)
        assert updated is not None
        assert updated.state == RunState.ACTIVE
        assert updated.active_at is not None

    def test_invalid_transition_raises(self, repo, create_user, create_group, create_store):
        """Test invalid state transition raises error."""
        leader = create_user(username='inv_state')
        group = create_group(name='Inv Group', creator=leader)
        store = create_store(name='Inv Store', creator=leader)
        run = repo.create_run(group_id=group.id, store_id=store.id, leader_id=leader.id)

        with pytest.raises(BadRequestError):
            # Cannot go from PLANNING directly to COMPLETED
            repo.update_run_state(run.id, RunState.COMPLETED)

    def test_returns_none_for_nonexistent_run(self, repo):
        """Test returns None for non-existent run."""
        result = repo.update_run_state(uuid.uuid4(), RunState.ACTIVE)
        assert result is None


class TestUpdateRunComment:
    """Test update_run_comment method."""

    def test_updates_comment(self, repo, create_user, create_group, create_store):
        """Test updating a run's comment."""
        leader = create_user(username='comment_u')
        group = create_group(name='Comment Grp', creator=leader)
        store = create_store(name='Comment Store', creator=leader)
        run = repo.create_run(group_id=group.id, store_id=store.id, leader_id=leader.id)

        updated = repo.update_run_comment(run.id, 'New comment')
        assert updated.comment == 'New comment'

    def test_clears_comment(self, repo, create_user, create_group, create_store):
        """Test clearing a run's comment."""
        leader = create_user(username='clear_c')
        group = create_group(name='Clear Grp', creator=leader)
        store = create_store(name='Clear Store', creator=leader)
        run = repo.create_run(
            group_id=group.id, store_id=store.id, leader_id=leader.id, comment='Old'
        )
        updated = repo.update_run_comment(run.id, None)
        assert updated.comment is None

    def test_returns_none_for_nonexistent_run(self, repo):
        """Test returns None for non-existent run."""
        result = repo.update_run_comment(uuid.uuid4(), 'x')
        assert result is None


class TestUpdateLeaderFee:
    """Test update_leader_fee method."""

    def test_updates_fee(self, repo, create_user, create_group, create_store):
        """Test updating leader fee."""
        leader = create_user(username='fee_u')
        group = create_group(name='Fee Grp', creator=leader)
        store = create_store(name='Fee Store', creator=leader)
        run = repo.create_run(group_id=group.id, store_id=store.id, leader_id=leader.id)

        updated = repo.update_leader_fee(run.id, 3.75)
        assert float(updated.leader_fee) == 3.75

    def test_clears_fee(self, repo, create_user, create_group, create_store):
        """Test clearing leader fee."""
        leader = create_user(username='clear_fee')
        group = create_group(name='ClearFee Grp', creator=leader)
        store = create_store(name='ClearFee Store', creator=leader)
        run = repo.create_run(
            group_id=group.id, store_id=store.id, leader_id=leader.id, leader_fee=10.0
        )
        updated = repo.update_leader_fee(run.id, None)
        assert updated.leader_fee is None

    def test_returns_none_for_nonexistent_run(self, repo):
        """Test returns None for non-existent run."""
        result = repo.update_leader_fee(uuid.uuid4(), 5.0)
        assert result is None


class TestCreateParticipation:
    """Test create_participation method."""

    def test_creates_participation(self, repo, create_user, create_group, create_store):
        """Test creating a new participation."""
        leader = create_user(username='part_leader')
        participant = create_user(username='part_user')
        group = create_group(name='Part Group', creator=leader)
        store = create_store(name='Part Store', creator=leader)
        run = repo.create_run(group_id=group.id, store_id=store.id, leader_id=leader.id)

        participation = repo.create_participation(user_id=participant.id, run_id=run.id)
        assert participation is not None
        assert participation.user_id == participant.id
        assert participation.run_id == run.id
        assert participation.is_leader is False
        assert participation.is_helper is False

    def test_creates_helper_participation(self, repo, create_user, create_group, create_store):
        """Test creating a helper participation."""
        leader = create_user(username='help_leader')
        helper = create_user(username='help_user')
        group = create_group(name='Help Group', creator=leader)
        store = create_store(name='Help Store', creator=leader)
        run = repo.create_run(group_id=group.id, store_id=store.id, leader_id=leader.id)

        participation = repo.create_participation(user_id=helper.id, run_id=run.id, is_helper=True)
        assert participation.is_helper is True


class TestGetParticipation:
    """Test get_participation method."""

    def test_returns_participation_when_exists(self, repo, create_user, create_group, create_store):
        """Test finding an existing participation."""
        leader = create_user(username='gp_leader')
        group = create_group(name='GP Group', creator=leader)
        store = create_store(name='GP Store', creator=leader)
        run = repo.create_run(group_id=group.id, store_id=store.id, leader_id=leader.id)

        found = repo.get_participation(leader.id, run.id)
        assert found is not None
        assert found.is_leader is True

    def test_returns_none_when_not_found(self, repo, create_user, create_group, create_store):
        """Test returns None when user has no participation."""
        leader = create_user(username='gp_leader2')
        outsider = create_user(username='gp_outsider')
        group = create_group(name='GP2 Group', creator=leader)
        store = create_store(name='GP2 Store', creator=leader)
        run = repo.create_run(group_id=group.id, store_id=store.id, leader_id=leader.id)

        result = repo.get_participation(outsider.id, run.id)
        assert result is None


class TestGetRunParticipations:
    """Test get_run_participations method."""

    def test_returns_all_participations(self, repo, create_user, create_group, create_store):
        """Test returns all participations for a run."""
        leader = create_user(username='rp_leader')
        member = create_user(username='rp_member')
        group = create_group(name='RP Group', creator=leader)
        store = create_store(name='RP Store', creator=leader)
        run = repo.create_run(group_id=group.id, store_id=store.id, leader_id=leader.id)
        repo.create_participation(user_id=member.id, run_id=run.id)

        participations = repo.get_run_participations(run.id)
        assert len(participations) == 2

    def test_returns_empty_for_nonexistent_run(self, repo):
        """Test returns empty list for non-existent run."""
        result = repo.get_run_participations(uuid.uuid4())
        assert result == []


class TestGetRunParticipationsWithUsers:
    """Test get_run_participations_with_users method."""

    def test_loads_user_data(self, repo, create_user, create_group, create_store):
        """Test that user objects are eagerly loaded."""
        leader = create_user(username='rpwu_leader')
        group = create_group(name='RPWU Group', creator=leader)
        store = create_store(name='RPWU Store', creator=leader)
        run = repo.create_run(group_id=group.id, store_id=store.id, leader_id=leader.id)

        participations = repo.get_run_participations_with_users(run.id)
        assert len(participations) == 1
        assert participations[0].user is not None
        assert participations[0].user.username == 'rpwu_leader'


class TestUpdateParticipationReady:
    """Test update_participation_ready method."""

    def test_sets_ready_true(self, repo, create_user, create_group, create_store):
        """Test setting participation ready to True."""
        leader = create_user(username='ready_leader')
        group = create_group(name='Ready Group', creator=leader)
        store = create_store(name='Ready Store', creator=leader)
        run = repo.create_run(group_id=group.id, store_id=store.id, leader_id=leader.id)
        participation = repo.get_participation(leader.id, run.id)

        updated = repo.update_participation_ready(participation.id, True)
        assert updated is not None
        assert updated.is_ready is True

    def test_sets_ready_false(self, repo, create_user, create_group, create_store):
        """Test setting participation ready back to False."""
        leader = create_user(username='unready')
        group = create_group(name='Unready Group', creator=leader)
        store = create_store(name='Unready Store', creator=leader)
        run = repo.create_run(group_id=group.id, store_id=store.id, leader_id=leader.id)
        participation = repo.get_participation(leader.id, run.id)
        repo.update_participation_ready(participation.id, True)

        updated = repo.update_participation_ready(participation.id, False)
        assert updated.is_ready is False

    def test_returns_none_for_nonexistent(self, repo):
        """Test returns None for non-existent participation."""
        result = repo.update_participation_ready(uuid.uuid4(), True)
        assert result is None


class TestUpdateParticipationHelper:
    """Test update_participation_helper method."""

    def test_sets_helper_true(self, repo, create_user, create_group, create_store):
        """Test setting participation helper status to True."""
        leader = create_user(username='helper_l')
        member = create_user(username='helper_m')
        group = create_group(name='Helper Group', creator=leader)
        store = create_store(name='Helper Store', creator=leader)
        run = repo.create_run(group_id=group.id, store_id=store.id, leader_id=leader.id)
        repo.create_participation(user_id=member.id, run_id=run.id)

        updated = repo.update_participation_helper(member.id, run.id, True)
        assert updated is not None
        assert updated.is_helper is True

    def test_sets_helper_false(self, repo, create_user, create_group, create_store):
        """Test setting helper status back to False."""
        leader = create_user(username='unhelp_l')
        member = create_user(username='unhelp_m')
        group = create_group(name='Unhelp Group', creator=leader)
        store = create_store(name='Unhelp Store', creator=leader)
        run = repo.create_run(group_id=group.id, store_id=store.id, leader_id=leader.id)
        repo.create_participation(user_id=member.id, run_id=run.id, is_helper=True)

        updated = repo.update_participation_helper(member.id, run.id, False)
        assert updated.is_helper is False

    def test_returns_none_for_nonexistent(self, repo, create_user, create_group, create_store):
        """Test returns None when participation does not exist."""
        leader = create_user(username='nohelp_l')
        outsider = create_user(username='nohelp_o')
        group = create_group(name='NoHelp Group', creator=leader)
        store = create_store(name='NoHelp Store', creator=leader)
        run = repo.create_run(group_id=group.id, store_id=store.id, leader_id=leader.id)

        result = repo.update_participation_helper(outsider.id, run.id, True)
        assert result is None
