"""Unit tests for MemoryRunRepository.

Tests cover:
- Run creation (create_run)
- Run retrieval by ID (get_run_by_id)
- Run state updates (update_run_state)
- Run comment updates (update_run_comment)
- Get runs by group (get_runs_by_group)
- Get completed/cancelled runs (get_completed_cancelled_runs_by_group)
- Participation management (create_participation, get_participation)
- Get run participations (get_run_participations, get_run_participations_with_users)
- Update participation ready status (update_participation_ready)
- Update participation helper status (update_participation_helper)
- State transitions and timestamp management
- Edge cases and data integrity
"""

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.core.exceptions import BadRequestError
from app.core.run_state import RunState
from app.repositories.memory.group import MemoryGroupRepository
from app.repositories.memory.run import MemoryRunRepository
from app.repositories.memory.storage import MemoryStorage
from app.repositories.memory.store import MemoryStoreRepository
from app.repositories.memory.user import MemoryUserRepository


@pytest.fixture
def storage():
    """Create fresh memory storage for each test."""
    storage = MemoryStorage()
    # Clear all data
    storage.users.clear()
    storage.users_by_username.clear()
    storage.groups.clear()
    storage.group_memberships.clear()
    storage.group_admin_status.clear()
    storage.stores.clear()
    storage.runs.clear()
    storage.participations.clear()
    storage.bids.clear()
    yield storage
    # Clean up after test
    storage.users.clear()
    storage.users_by_username.clear()
    storage.groups.clear()
    storage.group_memberships.clear()
    storage.group_admin_status.clear()
    storage.stores.clear()
    storage.runs.clear()
    storage.participations.clear()
    storage.bids.clear()


@pytest.fixture
def repo(storage):
    """Create run repository instance with fresh storage."""
    return MemoryRunRepository(storage)


@pytest.fixture
def user_repo(storage):
    """Create user repository instance with fresh storage."""
    return MemoryUserRepository(storage)


@pytest.fixture
def group_repo(storage):
    """Create group repository instance with fresh storage."""
    return MemoryGroupRepository(storage)


@pytest.fixture
def store_repo(storage):
    """Create store repository instance with fresh storage."""
    return MemoryStoreRepository(storage)


@pytest.fixture
def sample_user(user_repo):
    """Create a sample user for testing."""
    return user_repo.create_user('Test User', 'testuser', 'hashed_password')


@pytest.fixture
def sample_users(user_repo):
    """Create multiple sample users for testing."""
    return [user_repo.create_user(f'User {i}', f'user{i}', f'hash{i}') for i in range(1, 5)]


@pytest.fixture
def sample_group(group_repo, sample_user):
    """Create a sample group for testing."""
    return group_repo.create_group('Test Group', sample_user.id)


@pytest.fixture
def sample_store(store_repo):
    """Create a sample store for testing."""
    return store_repo.create_store('Test Store')


class TestCreateRun:
    """Test create_run() method."""

    def test_create_run_with_required_fields(self, repo, sample_group, sample_store, sample_user):
        """Test creating run with all required fields."""
        run = repo.create_run(sample_group.id, sample_store.id, sample_user.id)

        assert run is not None
        assert run.group_id == sample_group.id
        assert run.store_id == sample_store.id
        assert run.state == RunState.PLANNING

    def test_created_run_has_uuid(self, repo, sample_group, sample_store, sample_user):
        """Test created run has correct ID (UUID)."""
        run = repo.create_run(sample_group.id, sample_store.id, sample_user.id)

        assert run.id is not None
        assert isinstance(run.id, UUID)

    def test_default_state_is_planning(self, repo, sample_group, sample_store, sample_user):
        """Test default state is PLANNING."""
        run = repo.create_run(sample_group.id, sample_store.id, sample_user.id)

        assert run.state == RunState.PLANNING
        assert run.state == 'planning'

    def test_planning_at_timestamp_is_set(self, repo, sample_group, sample_store, sample_user):
        """Test planning_at timestamp is set on creation."""
        before = datetime.now(UTC)
        run = repo.create_run(sample_group.id, sample_store.id, sample_user.id)
        after = datetime.now(UTC)

        assert run.planning_at is not None
        assert before <= run.planning_at <= after

    def test_run_is_retrievable_after_creation(self, repo, sample_group, sample_store, sample_user):
        """Test run is retrievable after creation."""
        run = repo.create_run(sample_group.id, sample_store.id, sample_user.id)

        retrieved = repo.get_run_by_id(run.id)
        assert retrieved is not None
        assert retrieved.id == run.id
        assert retrieved.group_id == run.group_id
        assert retrieved.store_id == run.store_id

    def test_creating_multiple_runs_for_same_group(
        self, repo, sample_group, sample_store, sample_user
    ):
        """Test creating multiple runs for the same group."""
        run1 = repo.create_run(sample_group.id, sample_store.id, sample_user.id)
        run2 = repo.create_run(sample_group.id, sample_store.id, sample_user.id)
        run3 = repo.create_run(sample_group.id, sample_store.id, sample_user.id)

        assert run1.id != run2.id
        assert run2.id != run3.id
        assert run1.id != run3.id
        assert run1.group_id == run2.group_id == run3.group_id == sample_group.id

    def test_creating_run_with_initial_leader(self, repo, sample_group, sample_store, sample_user):
        """Test creating run creates leader participation."""
        run = repo.create_run(sample_group.id, sample_store.id, sample_user.id)

        participation = repo.get_participation(sample_user.id, run.id)
        assert participation is not None
        assert participation.user_id == sample_user.id
        assert participation.run_id == run.id
        assert participation.is_leader is True

    def test_creating_run_with_comment(self, repo, sample_group, sample_store, sample_user):
        """Test creating run with optional comment."""
        comment = 'Going shopping this weekend'
        run = repo.create_run(sample_group.id, sample_store.id, sample_user.id, comment=comment)

        assert run.comment == comment

    def test_creating_run_without_comment(self, repo, sample_group, sample_store, sample_user):
        """Test creating run without comment."""
        run = repo.create_run(sample_group.id, sample_store.id, sample_user.id)

        assert run.comment is None


class TestGetRunById:
    """Test get_run_by_id() method."""

    def test_get_existing_run(self, repo, sample_group, sample_store, sample_user):
        """Test getting existing run by ID."""
        run = repo.create_run(sample_group.id, sample_store.id, sample_user.id)

        retrieved = repo.get_run_by_id(run.id)
        assert retrieved is not None
        assert retrieved.id == run.id
        assert retrieved.group_id == run.group_id
        assert retrieved.store_id == run.store_id
        assert retrieved.state == run.state

    def test_get_nonexistent_run_returns_none(self, repo):
        """Test getting non-existent run returns None."""
        fake_id = uuid4()

        result = repo.get_run_by_id(fake_id)
        assert result is None

    def test_get_run_with_invalid_uuid(self, repo):
        """Test getting run with None ID."""
        result = repo.get_run_by_id(None)
        assert result is None


class TestUpdateRunState:
    """Test update_run_state() method."""

    def test_update_state_planning_to_active(self, repo, sample_group, sample_store, sample_user):
        """Test updating state from PLANNING to ACTIVE."""
        run = repo.create_run(sample_group.id, sample_store.id, sample_user.id)

        before = datetime.now(UTC)
        updated = repo.update_run_state(run.id, RunState.ACTIVE)
        after = datetime.now(UTC)

        assert updated is not None
        assert updated.state == RunState.ACTIVE
        assert updated.active_at is not None
        assert before <= updated.active_at <= after

    def test_update_state_active_to_confirmed(self, repo, sample_group, sample_store, sample_user):
        """Test updating state from ACTIVE to CONFIRMED."""
        run = repo.create_run(sample_group.id, sample_store.id, sample_user.id)
        repo.update_run_state(run.id, RunState.ACTIVE)

        before = datetime.now(UTC)
        updated = repo.update_run_state(run.id, RunState.CONFIRMED)
        after = datetime.now(UTC)

        assert updated.state == RunState.CONFIRMED
        assert updated.confirmed_at is not None
        assert before <= updated.confirmed_at <= after

    def test_update_state_confirmed_to_shopping(
        self, repo, sample_group, sample_store, sample_user
    ):
        """Test updating state from CONFIRMED to SHOPPING."""
        run = repo.create_run(sample_group.id, sample_store.id, sample_user.id)
        repo.update_run_state(run.id, RunState.ACTIVE)
        repo.update_run_state(run.id, RunState.CONFIRMED)

        before = datetime.now(UTC)
        updated = repo.update_run_state(run.id, RunState.SHOPPING)
        after = datetime.now(UTC)

        assert updated.state == RunState.SHOPPING
        assert updated.shopping_at is not None
        assert before <= updated.shopping_at <= after

    def test_update_state_to_cancelled(self, repo, sample_group, sample_store, sample_user):
        """Test updating state to CANCELLED."""
        run = repo.create_run(sample_group.id, sample_store.id, sample_user.id)

        before = datetime.now(UTC)
        updated = repo.update_run_state(run.id, RunState.CANCELLED)
        after = datetime.now(UTC)

        assert updated.state == RunState.CANCELLED
        assert updated.cancelled_at is not None
        assert before <= updated.cancelled_at <= after

    def test_state_timestamp_is_set_correctly(self, repo, sample_group, sample_store, sample_user):
        """Test state timestamp field is set correctly based on state."""
        run = repo.create_run(sample_group.id, sample_store.id, sample_user.id)

        # Transition through multiple states
        repo.update_run_state(run.id, RunState.ACTIVE)
        repo.update_run_state(run.id, RunState.CONFIRMED)
        repo.update_run_state(run.id, RunState.SHOPPING)

        retrieved = repo.get_run_by_id(run.id)
        assert retrieved.planning_at is not None
        assert retrieved.active_at is not None
        assert retrieved.confirmed_at is not None
        assert retrieved.shopping_at is not None

    def test_state_persistence(self, repo, sample_group, sample_store, sample_user):
        """Test state is persisted after update."""
        run = repo.create_run(sample_group.id, sample_store.id, sample_user.id)
        repo.update_run_state(run.id, RunState.ACTIVE)

        # Retrieve again to verify persistence
        retrieved = repo.get_run_by_id(run.id)
        assert retrieved.state == RunState.ACTIVE

    def test_update_nonexistent_run_returns_none(self, repo):
        """Test updating non-existent run returns None."""
        fake_id = uuid4()

        result = repo.update_run_state(fake_id, RunState.ACTIVE)
        assert result is None

    def test_invalid_state_transition_raises_error(
        self, repo, sample_group, sample_store, sample_user
    ):
        """Test invalid state transition raises BadRequestError."""
        run = repo.create_run(sample_group.id, sample_store.id, sample_user.id)

        # PLANNING -> SHOPPING is not valid (must go through ACTIVE and CONFIRMED)
        with pytest.raises(BadRequestError):
            repo.update_run_state(run.id, RunState.SHOPPING)

    def test_state_transition_from_completed_not_allowed(
        self, repo, sample_group, sample_store, sample_user
    ):
        """Test state transitions from COMPLETED are not allowed."""
        run = repo.create_run(sample_group.id, sample_store.id, sample_user.id)
        repo.update_run_state(run.id, RunState.ACTIVE)
        repo.update_run_state(run.id, RunState.CONFIRMED)
        repo.update_run_state(run.id, RunState.SHOPPING)
        repo.update_run_state(run.id, RunState.DISTRIBUTING)
        repo.update_run_state(run.id, RunState.COMPLETED)

        # COMPLETED is a terminal state
        with pytest.raises(BadRequestError):
            repo.update_run_state(run.id, RunState.ACTIVE)


class TestUpdateRunComment:
    """Test update_run_comment() method."""

    def test_update_run_comment(self, repo, sample_group, sample_store, sample_user):
        """Test updating run comment."""
        run = repo.create_run(sample_group.id, sample_store.id, sample_user.id)
        new_comment = 'Updated shopping plan'

        updated = repo.update_run_comment(run.id, new_comment)

        assert updated is not None
        assert updated.comment == new_comment

    def test_update_comment_is_persisted(self, repo, sample_group, sample_store, sample_user):
        """Test updated comment is persisted."""
        run = repo.create_run(sample_group.id, sample_store.id, sample_user.id)
        new_comment = 'Shopping at 2pm'

        repo.update_run_comment(run.id, new_comment)

        # Retrieve again to verify persistence
        retrieved = repo.get_run_by_id(run.id)
        assert retrieved.comment == new_comment

    def test_update_comment_to_none(self, repo, sample_group, sample_store, sample_user):
        """Test updating comment to None (clearing it)."""
        run = repo.create_run(
            sample_group.id, sample_store.id, sample_user.id, comment='Initial comment'
        )

        updated = repo.update_run_comment(run.id, None)

        assert updated.comment is None

    def test_update_nonexistent_run_comment_returns_none(self, repo):
        """Test updating comment for non-existent run returns None."""
        fake_id = uuid4()

        result = repo.update_run_comment(fake_id, 'Some comment')
        assert result is None


class TestGetRunsByGroup:
    """Test get_runs_by_group() method."""

    def test_get_runs_for_group(self, repo, sample_group, sample_store, sample_user):
        """Test getting all runs for a group."""
        run1 = repo.create_run(sample_group.id, sample_store.id, sample_user.id)
        run2 = repo.create_run(sample_group.id, sample_store.id, sample_user.id)

        runs = repo.get_runs_by_group(sample_group.id)

        assert len(runs) == 2
        run_ids = {r.id for r in runs}
        assert run1.id in run_ids
        assert run2.id in run_ids

    def test_empty_list_for_group_with_no_runs(self, repo, sample_group):
        """Test empty list for group with no runs."""
        runs = repo.get_runs_by_group(sample_group.id)

        assert runs == []
        assert len(runs) == 0

    def test_multiple_runs_returned(
        self, repo, sample_group, sample_store, sample_user, sample_users
    ):
        """Test multiple runs are returned."""
        runs_created = []
        for _ in range(5):
            run = repo.create_run(sample_group.id, sample_store.id, sample_user.id)
            runs_created.append(run)

        runs = repo.get_runs_by_group(sample_group.id)

        assert len(runs) == 5
        for run in runs_created:
            assert run.id in [r.id for r in runs]

    def test_runs_include_all_fields(self, repo, sample_group, sample_store, sample_user):
        """Test runs include all fields."""
        run = repo.create_run(
            sample_group.id, sample_store.id, sample_user.id, comment='Test comment'
        )

        runs = repo.get_runs_by_group(sample_group.id)

        assert len(runs) == 1
        retrieved = runs[0]
        assert retrieved.id == run.id
        assert retrieved.group_id == run.group_id
        assert retrieved.store_id == run.store_id
        assert retrieved.state == run.state
        assert retrieved.comment == run.comment

    def test_only_returns_runs_for_specific_group(
        self, repo, group_repo, sample_store, sample_user
    ):
        """Test only returns runs for specific group."""
        group1 = group_repo.create_group('Group 1', sample_user.id)
        group2 = group_repo.create_group('Group 2', sample_user.id)

        run1 = repo.create_run(group1.id, sample_store.id, sample_user.id)
        run2 = repo.create_run(group2.id, sample_store.id, sample_user.id)

        runs_group1 = repo.get_runs_by_group(group1.id)
        runs_group2 = repo.get_runs_by_group(group2.id)

        assert len(runs_group1) == 1
        assert len(runs_group2) == 1
        assert runs_group1[0].id == run1.id
        assert runs_group2[0].id == run2.id


class TestGetCompletedCancelledRunsByGroup:
    """Test get_completed_cancelled_runs_by_group() method."""

    def test_get_completed_runs_only(self, repo, sample_group, sample_store, sample_user):
        """Test getting only completed runs."""
        run1 = repo.create_run(sample_group.id, sample_store.id, sample_user.id)
        run2 = repo.create_run(sample_group.id, sample_store.id, sample_user.id)

        # Complete both runs
        repo.update_run_state(run1.id, RunState.ACTIVE)
        repo.update_run_state(run1.id, RunState.CONFIRMED)
        repo.update_run_state(run1.id, RunState.SHOPPING)
        repo.update_run_state(run1.id, RunState.DISTRIBUTING)
        repo.update_run_state(run1.id, RunState.COMPLETED)

        repo.update_run_state(run2.id, RunState.ACTIVE)
        repo.update_run_state(run2.id, RunState.CONFIRMED)
        repo.update_run_state(run2.id, RunState.SHOPPING)
        repo.update_run_state(run2.id, RunState.DISTRIBUTING)
        repo.update_run_state(run2.id, RunState.COMPLETED)

        runs = repo.get_completed_cancelled_runs_by_group(sample_group.id)

        assert len(runs) == 2
        for run in runs:
            assert run.state == RunState.COMPLETED

    def test_get_cancelled_runs_only(self, repo, sample_group, sample_store, sample_user):
        """Test getting only cancelled runs."""
        run1 = repo.create_run(sample_group.id, sample_store.id, sample_user.id)
        run2 = repo.create_run(sample_group.id, sample_store.id, sample_user.id)

        repo.update_run_state(run1.id, RunState.CANCELLED)
        repo.update_run_state(run2.id, RunState.CANCELLED)

        runs = repo.get_completed_cancelled_runs_by_group(sample_group.id)

        assert len(runs) == 2
        for run in runs:
            assert run.state == RunState.CANCELLED

    def test_get_both_completed_and_cancelled(self, repo, sample_group, sample_store, sample_user):
        """Test getting both completed and cancelled runs."""
        run1 = repo.create_run(sample_group.id, sample_store.id, sample_user.id)
        run2 = repo.create_run(sample_group.id, sample_store.id, sample_user.id)

        # Complete run1
        repo.update_run_state(run1.id, RunState.ACTIVE)
        repo.update_run_state(run1.id, RunState.CONFIRMED)
        repo.update_run_state(run1.id, RunState.SHOPPING)
        repo.update_run_state(run1.id, RunState.DISTRIBUTING)
        repo.update_run_state(run1.id, RunState.COMPLETED)

        # Cancel run2
        repo.update_run_state(run2.id, RunState.CANCELLED)

        runs = repo.get_completed_cancelled_runs_by_group(sample_group.id)

        assert len(runs) == 2
        states = {run.state for run in runs}
        assert RunState.COMPLETED in states
        assert RunState.CANCELLED in states

    def test_excludes_active_runs(self, repo, sample_group, sample_store, sample_user):
        """Test excludes active runs (non-terminal states)."""
        run1 = repo.create_run(sample_group.id, sample_store.id, sample_user.id)
        # Create additional runs that remain in PLANNING state
        repo.create_run(sample_group.id, sample_store.id, sample_user.id)
        repo.create_run(sample_group.id, sample_store.id, sample_user.id)

        # Complete run1
        repo.update_run_state(run1.id, RunState.ACTIVE)
        repo.update_run_state(run1.id, RunState.CONFIRMED)
        repo.update_run_state(run1.id, RunState.SHOPPING)
        repo.update_run_state(run1.id, RunState.DISTRIBUTING)
        repo.update_run_state(run1.id, RunState.COMPLETED)

        runs = repo.get_completed_cancelled_runs_by_group(sample_group.id)

        assert len(runs) == 1
        assert runs[0].id == run1.id

    def test_pagination_with_limit(self, repo, sample_group, sample_store, sample_user):
        """Test pagination with limit parameter."""
        # Create 5 completed runs
        for _ in range(5):
            run = repo.create_run(sample_group.id, sample_store.id, sample_user.id)
            repo.update_run_state(run.id, RunState.ACTIVE)
            repo.update_run_state(run.id, RunState.CONFIRMED)
            repo.update_run_state(run.id, RunState.SHOPPING)
            repo.update_run_state(run.id, RunState.DISTRIBUTING)
            repo.update_run_state(run.id, RunState.COMPLETED)

        runs = repo.get_completed_cancelled_runs_by_group(sample_group.id, limit=3)

        assert len(runs) == 3

    def test_pagination_with_offset(self, repo, sample_group, sample_store, sample_user):
        """Test pagination with offset parameter."""
        # Create 5 completed runs
        for _ in range(5):
            run = repo.create_run(sample_group.id, sample_store.id, sample_user.id)
            repo.update_run_state(run.id, RunState.ACTIVE)
            repo.update_run_state(run.id, RunState.CONFIRMED)
            repo.update_run_state(run.id, RunState.SHOPPING)
            repo.update_run_state(run.id, RunState.DISTRIBUTING)
            repo.update_run_state(run.id, RunState.COMPLETED)

        runs = repo.get_completed_cancelled_runs_by_group(sample_group.id, offset=2)

        assert len(runs) == 3

    def test_sorted_by_completion_timestamp(self, repo, sample_group, sample_store, sample_user):
        """Test runs are sorted by completion timestamp (newest first)."""
        run1 = repo.create_run(sample_group.id, sample_store.id, sample_user.id)
        run2 = repo.create_run(sample_group.id, sample_store.id, sample_user.id)

        # Complete run1 first
        repo.update_run_state(run1.id, RunState.ACTIVE)
        repo.update_run_state(run1.id, RunState.CONFIRMED)
        repo.update_run_state(run1.id, RunState.SHOPPING)
        repo.update_run_state(run1.id, RunState.DISTRIBUTING)
        repo.update_run_state(run1.id, RunState.COMPLETED)

        # Complete run2 later
        repo.update_run_state(run2.id, RunState.ACTIVE)
        repo.update_run_state(run2.id, RunState.CONFIRMED)
        repo.update_run_state(run2.id, RunState.SHOPPING)
        repo.update_run_state(run2.id, RunState.DISTRIBUTING)
        repo.update_run_state(run2.id, RunState.COMPLETED)

        runs = repo.get_completed_cancelled_runs_by_group(sample_group.id)

        # run2 should come first (newer)
        assert runs[0].id == run2.id
        assert runs[1].id == run1.id


class TestCreateParticipation:
    """Test create_participation() method."""

    def test_create_participation(
        self, repo, sample_group, sample_store, sample_user, sample_users
    ):
        """Test creating participation."""
        run = repo.create_run(sample_group.id, sample_store.id, sample_user.id)
        user = sample_users[0]

        participation = repo.create_participation(user.id, run.id)

        assert participation is not None
        assert participation.user_id == user.id
        assert participation.run_id == run.id
        assert participation.is_leader is False
        assert participation.is_ready is False

    def test_create_participation_with_leader_flag(
        self, repo, sample_group, sample_store, sample_user, sample_users
    ):
        """Test creating participation with is_leader flag."""
        run = repo.create_run(sample_group.id, sample_store.id, sample_user.id)
        user = sample_users[0]

        participation = repo.create_participation(user.id, run.id, is_leader=True)

        assert participation.is_leader is True

    def test_create_participation_with_helper_flag(
        self, repo, sample_group, sample_store, sample_user, sample_users
    ):
        """Test creating participation with is_helper flag."""
        run = repo.create_run(sample_group.id, sample_store.id, sample_user.id)
        user = sample_users[0]

        participation = repo.create_participation(user.id, run.id, is_helper=True)

        assert participation.is_helper is True

    def test_participation_has_uuid(
        self, repo, sample_group, sample_store, sample_user, sample_users
    ):
        """Test participation has UUID."""
        run = repo.create_run(sample_group.id, sample_store.id, sample_user.id)
        user = sample_users[0]

        participation = repo.create_participation(user.id, run.id)

        assert participation.id is not None
        assert isinstance(participation.id, UUID)

    def test_participation_includes_user_relationship(
        self, repo, sample_group, sample_store, sample_user, sample_users
    ):
        """Test participation includes user relationship."""
        run = repo.create_run(sample_group.id, sample_store.id, sample_user.id)
        user = sample_users[0]

        participation = repo.create_participation(user.id, run.id)

        assert participation.user is not None
        assert participation.user.id == user.id
        assert participation.user.name == user.name

    def test_participation_includes_run_relationship(
        self, repo, sample_group, sample_store, sample_user, sample_users
    ):
        """Test participation includes run relationship."""
        run = repo.create_run(sample_group.id, sample_store.id, sample_user.id)
        user = sample_users[0]

        participation = repo.create_participation(user.id, run.id)

        assert participation.run is not None
        assert participation.run.id == run.id


class TestGetParticipation:
    """Test get_participation() method."""

    def test_get_existing_participation(
        self, repo, sample_group, sample_store, sample_user, sample_users
    ):
        """Test getting existing participation."""
        run = repo.create_run(sample_group.id, sample_store.id, sample_user.id)
        user = sample_users[0]
        created = repo.create_participation(user.id, run.id)

        retrieved = repo.get_participation(user.id, run.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.user_id == user.id
        assert retrieved.run_id == run.id

    def test_get_nonexistent_participation_returns_none(
        self, repo, sample_group, sample_store, sample_user, sample_users
    ):
        """Test getting non-existent participation returns None."""
        run = repo.create_run(sample_group.id, sample_store.id, sample_user.id)
        user = sample_users[0]

        result = repo.get_participation(user.id, run.id)

        assert result is None

    def test_get_leader_participation(self, repo, sample_group, sample_store, sample_user):
        """Test getting leader participation."""
        run = repo.create_run(sample_group.id, sample_store.id, sample_user.id)

        participation = repo.get_participation(sample_user.id, run.id)

        assert participation is not None
        assert participation.is_leader is True

    def test_participation_includes_relationships(
        self, repo, sample_group, sample_store, sample_user, sample_users
    ):
        """Test participation includes user and run relationships."""
        run = repo.create_run(sample_group.id, sample_store.id, sample_user.id)
        user = sample_users[0]
        repo.create_participation(user.id, run.id)

        participation = repo.get_participation(user.id, run.id)

        assert participation.user is not None
        assert participation.user.id == user.id
        assert participation.run is not None
        assert participation.run.id == run.id


class TestGetRunParticipations:
    """Test get_run_participations() method."""

    def test_get_all_participations_for_run(
        self, repo, sample_group, sample_store, sample_user, sample_users
    ):
        """Test getting all participations for a run."""
        run = repo.create_run(sample_group.id, sample_store.id, sample_user.id)

        # Add more participants
        for user in sample_users[:3]:
            repo.create_participation(user.id, run.id)

        participations = repo.get_run_participations(run.id)

        # Should include leader + 3 participants
        assert len(participations) == 4

    def test_empty_list_for_run_with_only_leader(
        self, repo, sample_group, sample_store, sample_user
    ):
        """Test participations include the leader."""
        run = repo.create_run(sample_group.id, sample_store.id, sample_user.id)

        participations = repo.get_run_participations(run.id)

        # Should have 1 participation (the leader)
        assert len(participations) == 1
        assert participations[0].user_id == sample_user.id
        assert participations[0].is_leader is True

    def test_participations_include_leader_flag(
        self, repo, sample_group, sample_store, sample_user, sample_users
    ):
        """Test participations include leader flag."""
        run = repo.create_run(sample_group.id, sample_store.id, sample_user.id)

        # Add non-leader participant
        user = sample_users[0]
        repo.create_participation(user.id, run.id)

        participations = repo.get_run_participations(run.id)

        # Find leader and non-leader
        leader_p = next(p for p in participations if p.user_id == sample_user.id)
        user_p = next(p for p in participations if p.user_id == user.id)

        assert leader_p.is_leader is True
        assert user_p.is_leader is False

    def test_participations_include_user_details(
        self, repo, sample_group, sample_store, sample_user, sample_users
    ):
        """Test participations include user details."""
        run = repo.create_run(sample_group.id, sample_store.id, sample_user.id)
        user = sample_users[0]
        repo.create_participation(user.id, run.id)

        participations = repo.get_run_participations(run.id)

        for participation in participations:
            assert participation.user is not None
            assert participation.user.name is not None

    def test_get_participations_for_nonexistent_run(self, repo):
        """Test getting participations for non-existent run returns empty list."""
        fake_id = uuid4()

        participations = repo.get_run_participations(fake_id)

        assert participations == []


class TestGetRunParticipationsWithUsers:
    """Test get_run_participations_with_users() method."""

    def test_get_participations_with_users(
        self, repo, sample_group, sample_store, sample_user, sample_users
    ):
        """Test getting participations with users eagerly loaded."""
        run = repo.create_run(sample_group.id, sample_store.id, sample_user.id)

        for user in sample_users[:3]:
            repo.create_participation(user.id, run.id)

        participations = repo.get_run_participations_with_users(run.id)

        assert len(participations) == 4
        for participation in participations:
            assert participation.user is not None
            assert participation.run is not None

    def test_users_eagerly_loaded(
        self, repo, sample_group, sample_store, sample_user, sample_users
    ):
        """Test users are eagerly loaded (relationship pre-populated)."""
        run = repo.create_run(sample_group.id, sample_store.id, sample_user.id)
        user = sample_users[0]
        repo.create_participation(user.id, run.id)

        participations = repo.get_run_participations_with_users(run.id)

        # User should be accessible without additional queries
        for participation in participations:
            assert hasattr(participation, 'user')
            assert participation.user is not None


class TestUpdateParticipationReady:
    """Test update_participation_ready() method."""

    def test_update_participation_to_ready(
        self, repo, sample_group, sample_store, sample_user, sample_users
    ):
        """Test updating participation to ready."""
        run = repo.create_run(sample_group.id, sample_store.id, sample_user.id)
        user = sample_users[0]
        participation = repo.create_participation(user.id, run.id)

        updated = repo.update_participation_ready(participation.id, True)

        assert updated is not None
        assert updated.is_ready is True

    def test_update_participation_to_not_ready(
        self, repo, sample_group, sample_store, sample_user, sample_users
    ):
        """Test updating participation to not ready."""
        run = repo.create_run(sample_group.id, sample_store.id, sample_user.id)
        user = sample_users[0]
        participation = repo.create_participation(user.id, run.id)
        repo.update_participation_ready(participation.id, True)

        updated = repo.update_participation_ready(participation.id, False)

        assert updated is not None
        assert updated.is_ready is False

    def test_ready_flag_is_persisted(
        self, repo, storage, sample_group, sample_store, sample_user, sample_users
    ):
        """Test ready flag is persisted."""
        run = repo.create_run(sample_group.id, sample_store.id, sample_user.id)
        user = sample_users[0]
        participation = repo.create_participation(user.id, run.id)

        repo.update_participation_ready(participation.id, True)

        # Retrieve from storage
        stored = storage.participations[participation.id]
        assert stored.is_ready is True

    def test_update_nonexistent_participation_returns_none(self, repo):
        """Test updating non-existent participation returns None."""
        fake_id = uuid4()

        result = repo.update_participation_ready(fake_id, True)

        assert result is None


class TestUpdateParticipationHelper:
    """Test update_participation_helper() method."""

    def test_update_participation_to_helper(
        self, repo, sample_group, sample_store, sample_user, sample_users
    ):
        """Test updating participation to helper."""
        run = repo.create_run(sample_group.id, sample_store.id, sample_user.id)
        user = sample_users[0]
        repo.create_participation(user.id, run.id)

        updated = repo.update_participation_helper(user.id, run.id, True)

        assert updated is not None
        assert updated.is_helper is True

    def test_update_participation_to_not_helper(
        self, repo, sample_group, sample_store, sample_user, sample_users
    ):
        """Test updating participation to not helper."""
        run = repo.create_run(sample_group.id, sample_store.id, sample_user.id)
        user = sample_users[0]
        repo.create_participation(user.id, run.id, is_helper=True)

        updated = repo.update_participation_helper(user.id, run.id, False)

        assert updated is not None
        assert updated.is_helper is False

    def test_helper_flag_is_persisted(
        self, repo, sample_group, sample_store, sample_user, sample_users
    ):
        """Test helper flag is persisted."""
        run = repo.create_run(sample_group.id, sample_store.id, sample_user.id)
        user = sample_users[0]
        repo.create_participation(user.id, run.id)

        repo.update_participation_helper(user.id, run.id, True)

        # Retrieve again
        participation = repo.get_participation(user.id, run.id)
        assert participation.is_helper is True

    def test_update_nonexistent_participation_returns_none(self, repo, sample_users):
        """Test updating non-existent participation returns None."""
        fake_run_id = uuid4()
        user = sample_users[0]

        result = repo.update_participation_helper(user.id, fake_run_id, True)

        assert result is None


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_very_long_comment(self, repo, sample_group, sample_store, sample_user):
        """Test with very long comment (1000+ chars)."""
        long_comment = 'a' * 1500
        run = repo.create_run(
            sample_group.id, sample_store.id, sample_user.id, comment=long_comment
        )

        assert run.comment == long_comment
        retrieved = repo.get_run_by_id(run.id)
        assert retrieved.comment == long_comment

    def test_unicode_in_comment(self, repo, sample_group, sample_store, sample_user):
        """Test with unicode characters in comment."""
        unicode_comment = '今天去购物 🛒 Shopping trip today!'
        run = repo.create_run(
            sample_group.id, sample_store.id, sample_user.id, comment=unicode_comment
        )

        assert run.comment == unicode_comment
        retrieved = repo.get_run_by_id(run.id)
        assert retrieved.comment == unicode_comment

    def test_concurrent_operations(self, repo, sample_group, sample_store, sample_user):
        """Test creating multiple runs (simulating concurrent operations)."""
        runs = []
        for _ in range(50):
            run = repo.create_run(sample_group.id, sample_store.id, sample_user.id)
            runs.append(run)

        # Verify all runs exist
        all_runs = repo.get_runs_by_group(sample_group.id)
        assert len(all_runs) == 50

        # Verify all IDs are unique
        ids = [r.id for r in all_runs]
        assert len(ids) == len(set(ids))

    def test_run_with_no_additional_participants(
        self, repo, sample_group, sample_store, sample_user
    ):
        """Test run with only leader (no additional participants)."""
        run = repo.create_run(sample_group.id, sample_store.id, sample_user.id)

        participations = repo.get_run_participations(run.id)

        # Should only have leader
        assert len(participations) == 1
        assert participations[0].is_leader is True

    def test_repository_isolation(self, storage):
        """Test fresh repository instance per test (via fixture)."""
        # This test verifies the fixture works correctly
        assert len(storage.runs) == 0
        assert len(storage.participations) == 0


class TestDataIntegrity:
    """Test data integrity and relationships."""

    def test_run_object_has_expected_fields(self, repo, sample_group, sample_store, sample_user):
        """Test run object has expected fields."""
        run = repo.create_run(sample_group.id, sample_store.id, sample_user.id)

        assert hasattr(run, 'id')
        assert hasattr(run, 'group_id')
        assert hasattr(run, 'store_id')
        assert hasattr(run, 'state')
        assert hasattr(run, 'comment')
        assert hasattr(run, 'planning_at')
        assert hasattr(run, 'active_at')
        assert hasattr(run, 'confirmed_at')
        assert hasattr(run, 'shopping_at')
        assert hasattr(run, 'adjusting_at')
        assert hasattr(run, 'distributing_at')
        assert hasattr(run, 'completed_at')
        assert hasattr(run, 'cancelled_at')

    def test_timestamps_are_in_order(self, repo, sample_group, sample_store, sample_user):
        """Test state timestamps are in chronological order."""
        run = repo.create_run(sample_group.id, sample_store.id, sample_user.id)

        # Transition through states
        repo.update_run_state(run.id, RunState.ACTIVE)
        repo.update_run_state(run.id, RunState.CONFIRMED)
        repo.update_run_state(run.id, RunState.SHOPPING)

        retrieved = repo.get_run_by_id(run.id)

        assert retrieved.planning_at <= retrieved.active_at
        assert retrieved.active_at <= retrieved.confirmed_at
        assert retrieved.confirmed_at <= retrieved.shopping_at

    def test_participation_object_has_expected_fields(
        self, repo, sample_group, sample_store, sample_user, sample_users
    ):
        """Test participation object has expected fields."""
        run = repo.create_run(sample_group.id, sample_store.id, sample_user.id)
        user = sample_users[0]
        participation = repo.create_participation(user.id, run.id)

        assert hasattr(participation, 'id')
        assert hasattr(participation, 'user_id')
        assert hasattr(participation, 'run_id')
        assert hasattr(participation, 'is_leader')
        assert hasattr(participation, 'is_helper')
        assert hasattr(participation, 'is_ready')
        assert hasattr(participation, 'is_removed')

    def test_multiple_repositories_share_storage(
        self, storage, sample_group, sample_store, sample_user
    ):
        """Test multiple repository instances share the same storage."""
        repo1 = MemoryRunRepository(storage)
        repo2 = MemoryRunRepository(storage)

        run = repo1.create_run(sample_group.id, sample_store.id, sample_user.id)

        # Both repositories should see the same run
        assert repo2.get_run_by_id(run.id) is not None


class TestStateTransitions:
    """Test all valid state transitions."""

    @pytest.mark.parametrize(
        'from_state,to_state',
        [
            (RunState.PLANNING, RunState.ACTIVE),
            (RunState.PLANNING, RunState.CONFIRMED),
            (RunState.PLANNING, RunState.CANCELLED),
            (RunState.ACTIVE, RunState.CONFIRMED),
            (RunState.ACTIVE, RunState.PLANNING),
            (RunState.ACTIVE, RunState.CANCELLED),
            (RunState.CONFIRMED, RunState.SHOPPING),
            (RunState.CONFIRMED, RunState.ACTIVE),
            (RunState.CONFIRMED, RunState.CANCELLED),
            (RunState.SHOPPING, RunState.ADJUSTING),
            (RunState.SHOPPING, RunState.DISTRIBUTING),
            (RunState.SHOPPING, RunState.CANCELLED),
            (RunState.ADJUSTING, RunState.DISTRIBUTING),
            (RunState.ADJUSTING, RunState.CANCELLED),
            (RunState.DISTRIBUTING, RunState.COMPLETED),
        ],
    )
    def test_valid_state_transitions(
        self, repo, sample_group, sample_store, sample_user, from_state, to_state
    ):
        """Test all valid state transitions succeed."""
        run = repo.create_run(sample_group.id, sample_store.id, sample_user.id)

        # Set initial state if not PLANNING
        if from_state != RunState.PLANNING:
            # Navigate to the from_state
            if from_state == RunState.ACTIVE:
                repo.update_run_state(run.id, RunState.ACTIVE)
            elif from_state == RunState.CONFIRMED:
                repo.update_run_state(run.id, RunState.ACTIVE)
                repo.update_run_state(run.id, RunState.CONFIRMED)
            elif from_state == RunState.SHOPPING:
                repo.update_run_state(run.id, RunState.ACTIVE)
                repo.update_run_state(run.id, RunState.CONFIRMED)
                repo.update_run_state(run.id, RunState.SHOPPING)
            elif from_state == RunState.ADJUSTING:
                repo.update_run_state(run.id, RunState.ACTIVE)
                repo.update_run_state(run.id, RunState.CONFIRMED)
                repo.update_run_state(run.id, RunState.SHOPPING)
                repo.update_run_state(run.id, RunState.ADJUSTING)
            elif from_state == RunState.DISTRIBUTING:
                repo.update_run_state(run.id, RunState.ACTIVE)
                repo.update_run_state(run.id, RunState.CONFIRMED)
                repo.update_run_state(run.id, RunState.SHOPPING)
                repo.update_run_state(run.id, RunState.DISTRIBUTING)

        # Now transition to target state
        updated = repo.update_run_state(run.id, to_state)

        assert updated is not None
        assert updated.state == to_state

    @pytest.mark.parametrize(
        'from_state,invalid_to_state',
        [
            (RunState.PLANNING, RunState.SHOPPING),
            (RunState.PLANNING, RunState.DISTRIBUTING),
            (RunState.PLANNING, RunState.COMPLETED),
            (RunState.ACTIVE, RunState.SHOPPING),
            (RunState.ACTIVE, RunState.DISTRIBUTING),
            (RunState.CONFIRMED, RunState.PLANNING),
            (RunState.CONFIRMED, RunState.DISTRIBUTING),
            (RunState.COMPLETED, RunState.ACTIVE),
            (RunState.COMPLETED, RunState.CANCELLED),
            (RunState.CANCELLED, RunState.ACTIVE),
            (RunState.CANCELLED, RunState.COMPLETED),
        ],
    )
    def test_invalid_state_transitions(
        self, repo, sample_group, sample_store, sample_user, from_state, invalid_to_state
    ):
        """Test invalid state transitions raise BadRequestError."""
        run = repo.create_run(sample_group.id, sample_store.id, sample_user.id)

        # Set initial state if not PLANNING
        if from_state != RunState.PLANNING:
            if from_state == RunState.ACTIVE:
                repo.update_run_state(run.id, RunState.ACTIVE)
            elif from_state == RunState.CONFIRMED:
                repo.update_run_state(run.id, RunState.ACTIVE)
                repo.update_run_state(run.id, RunState.CONFIRMED)
            elif from_state == RunState.COMPLETED:
                repo.update_run_state(run.id, RunState.ACTIVE)
                repo.update_run_state(run.id, RunState.CONFIRMED)
                repo.update_run_state(run.id, RunState.SHOPPING)
                repo.update_run_state(run.id, RunState.DISTRIBUTING)
                repo.update_run_state(run.id, RunState.COMPLETED)
            elif from_state == RunState.CANCELLED:
                repo.update_run_state(run.id, RunState.CANCELLED)

        # Try invalid transition
        with pytest.raises(BadRequestError):
            repo.update_run_state(run.id, invalid_to_state)


class TestComplexScenarios:
    """Test complex scenarios involving multiple operations."""

    def test_multiple_participants_in_run(
        self, repo, sample_group, sample_store, sample_user, sample_users
    ):
        """Test run with multiple participants."""
        run = repo.create_run(sample_group.id, sample_store.id, sample_user.id)

        # Add multiple participants
        for user in sample_users:
            repo.create_participation(user.id, run.id)

        participations = repo.get_run_participations(run.id)

        # Should include leader + all sample users
        assert len(participations) == len(sample_users) + 1

    def test_full_run_lifecycle(self, repo, sample_group, sample_store, sample_user):
        """Test full run lifecycle from planning to completion."""
        run = repo.create_run(sample_group.id, sample_store.id, sample_user.id)

        # PLANNING -> ACTIVE
        repo.update_run_state(run.id, RunState.ACTIVE)
        assert repo.get_run_by_id(run.id).state == RunState.ACTIVE

        # ACTIVE -> CONFIRMED
        repo.update_run_state(run.id, RunState.CONFIRMED)
        assert repo.get_run_by_id(run.id).state == RunState.CONFIRMED

        # CONFIRMED -> SHOPPING
        repo.update_run_state(run.id, RunState.SHOPPING)
        assert repo.get_run_by_id(run.id).state == RunState.SHOPPING

        # SHOPPING -> DISTRIBUTING
        repo.update_run_state(run.id, RunState.DISTRIBUTING)
        assert repo.get_run_by_id(run.id).state == RunState.DISTRIBUTING

        # DISTRIBUTING -> COMPLETED
        repo.update_run_state(run.id, RunState.COMPLETED)
        final_run = repo.get_run_by_id(run.id)

        assert final_run.state == RunState.COMPLETED
        assert final_run.planning_at is not None
        assert final_run.active_at is not None
        assert final_run.confirmed_at is not None
        assert final_run.shopping_at is not None
        assert final_run.distributing_at is not None
        assert final_run.completed_at is not None

    def test_run_cancellation_from_various_states(
        self, repo, sample_group, sample_store, sample_user
    ):
        """Test run can be cancelled from various states."""
        # Cancel from PLANNING
        run1 = repo.create_run(sample_group.id, sample_store.id, sample_user.id)
        repo.update_run_state(run1.id, RunState.CANCELLED)
        assert repo.get_run_by_id(run1.id).state == RunState.CANCELLED

        # Cancel from ACTIVE
        run2 = repo.create_run(sample_group.id, sample_store.id, sample_user.id)
        repo.update_run_state(run2.id, RunState.ACTIVE)
        repo.update_run_state(run2.id, RunState.CANCELLED)
        assert repo.get_run_by_id(run2.id).state == RunState.CANCELLED

        # Cancel from CONFIRMED
        run3 = repo.create_run(sample_group.id, sample_store.id, sample_user.id)
        repo.update_run_state(run3.id, RunState.ACTIVE)
        repo.update_run_state(run3.id, RunState.CONFIRMED)
        repo.update_run_state(run3.id, RunState.CANCELLED)
        assert repo.get_run_by_id(run3.id).state == RunState.CANCELLED

    def test_updating_comment_multiple_times(self, repo, sample_group, sample_store, sample_user):
        """Test updating comment multiple times."""
        run = repo.create_run(sample_group.id, sample_store.id, sample_user.id)

        comments = ['First comment', 'Updated comment', 'Final comment', None, 'Back again']

        for comment in comments:
            repo.update_run_comment(run.id, comment)
            retrieved = repo.get_run_by_id(run.id)
            assert retrieved.comment == comment

    def test_multiple_leaders_allowed(
        self, repo, sample_group, sample_store, sample_user, sample_users
    ):
        """Test multiple participants can be leaders (if system allows)."""
        run = repo.create_run(sample_group.id, sample_store.id, sample_user.id)

        # Add another leader
        user = sample_users[0]
        repo.create_participation(user.id, run.id, is_leader=True)

        participations = repo.get_run_participations(run.id)
        leaders = [p for p in participations if p.is_leader]

        # Should have 2 leaders
        assert len(leaders) == 2
