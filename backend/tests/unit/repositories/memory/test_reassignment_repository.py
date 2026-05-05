"""Unit tests for MemoryReassignmentRepository.

Tests cover:
- Reassignment request creation (create_reassignment_request)
- Request retrieval by ID (get_reassignment_request_by_id)
- Pending request for run (get_pending_reassignment_for_run)
- Pending requests from user (get_pending_reassignments_from_user)
- Pending requests to user (get_pending_reassignments_to_user)
- Status updates (update_reassignment_status)
- Cancel all pending for run (cancel_all_pending_reassignments_for_run)
- Workflow scenarios and edge cases
"""

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.repositories.memory.reassignment import MemoryReassignmentRepository
from app.repositories.memory.storage import MemoryStorage


@pytest.fixture
def storage():
    """Create fresh memory storage for each test."""
    storage = MemoryStorage()
    storage.reassignment_requests.clear()
    yield storage
    storage.reassignment_requests.clear()


@pytest.fixture
def repo(storage):
    """Create repository instance with fresh storage."""
    return MemoryReassignmentRepository(storage)


@pytest.fixture
def sample_ids():
    """Sample IDs for testing."""
    return {
        'run1': uuid4(),
        'run2': uuid4(),
        'user1': uuid4(),
        'user2': uuid4(),
        'user3': uuid4(),
    }


class TestCreateReassignmentRequest:
    """Test create_reassignment_request() method."""

    async def test_create_request_with_required_fields(self, repo, sample_ids):
        """Test creating reassignment request with required fields."""
        run_id = sample_ids['run1']
        from_user_id = sample_ids['user1']
        to_user_id = sample_ids['user2']

        request = await repo.create_reassignment_request(
            run_id=run_id,
            from_user_id=from_user_id,
            to_user_id=to_user_id,
        )

        assert request is not None
        assert request.run_id == run_id
        assert request.from_user_id == from_user_id
        assert request.to_user_id == to_user_id

    async def test_created_request_has_uuid(self, repo, sample_ids):
        """Test created request has UUID."""
        request = await repo.create_reassignment_request(
            run_id=sample_ids['run1'],
            from_user_id=sample_ids['user1'],
            to_user_id=sample_ids['user2'],
        )

        assert request.id is not None
        assert isinstance(request.id, UUID)

    async def test_created_request_has_default_status_pending(self, repo, sample_ids):
        """Test created request has default status 'pending'."""
        request = await repo.create_reassignment_request(
            run_id=sample_ids['run1'],
            from_user_id=sample_ids['user1'],
            to_user_id=sample_ids['user2'],
        )

        assert request.status == 'pending'

    async def test_created_request_has_created_at_timestamp(self, repo, sample_ids):
        """Test created request has created_at timestamp."""
        before = datetime.now(UTC)
        request = await repo.create_reassignment_request(
            run_id=sample_ids['run1'],
            from_user_id=sample_ids['user1'],
            to_user_id=sample_ids['user2'],
        )
        after = datetime.now(UTC)

        assert request.created_at is not None
        assert before <= request.created_at <= after

    async def test_created_request_has_null_resolved_at(self, repo, sample_ids):
        """Test created request has resolved_at=None."""
        request = await repo.create_reassignment_request(
            run_id=sample_ids['run1'],
            from_user_id=sample_ids['user1'],
            to_user_id=sample_ids['user2'],
        )

        assert request.resolved_at is None

    async def test_create_multiple_requests_for_run(self, repo, sample_ids):
        """Test creating multiple reassignment requests for same run."""
        run_id = sample_ids['run1']

        # First request
        request1 = await repo.create_reassignment_request(
            run_id=run_id,
            from_user_id=sample_ids['user1'],
            to_user_id=sample_ids['user2'],
        )

        # Accept first request
        await repo.update_reassignment_status(request1.id, 'accepted')

        # Second request (after first was accepted)
        request2 = await repo.create_reassignment_request(
            run_id=run_id,
            from_user_id=sample_ids['user2'],
            to_user_id=sample_ids['user3'],
        )

        assert request1.id != request2.id
        assert request1.run_id == request2.run_id == run_id

    async def test_create_requests_for_different_users(self, repo, sample_ids):
        """Test creating requests with different from/to user combinations."""
        run_id = sample_ids['run1']

        request1 = await repo.create_reassignment_request(
            run_id=run_id,
            from_user_id=sample_ids['user1'],
            to_user_id=sample_ids['user2'],
        )

        request2 = await repo.create_reassignment_request(
            run_id=run_id,
            from_user_id=sample_ids['user1'],
            to_user_id=sample_ids['user3'],
        )

        assert request1.to_user_id != request2.to_user_id
        assert request1.from_user_id == request2.from_user_id


class TestGetReassignmentRequestById:
    """Test get_reassignment_request_by_id() method."""

    async def test_get_existing_request(self, repo, sample_ids):
        """Test retrieving existing request by ID."""
        created = await repo.create_reassignment_request(
            run_id=sample_ids['run1'],
            from_user_id=sample_ids['user1'],
            to_user_id=sample_ids['user2'],
        )

        retrieved = await repo.get_reassignment_request_by_id(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.run_id == sample_ids['run1']
        assert retrieved.from_user_id == sample_ids['user1']
        assert retrieved.to_user_id == sample_ids['user2']

    async def test_get_nonexistent_request_returns_none(self, repo):
        """Test retrieving non-existent request returns None."""
        nonexistent_id = uuid4()
        result = await repo.get_reassignment_request_by_id(nonexistent_id)

        assert result is None

    async def test_get_request_includes_all_fields(self, repo, sample_ids):
        """Test retrieved request includes all fields."""
        created = await repo.create_reassignment_request(
            run_id=sample_ids['run1'],
            from_user_id=sample_ids['user1'],
            to_user_id=sample_ids['user2'],
        )

        retrieved = await repo.get_reassignment_request_by_id(created.id)

        assert retrieved.id is not None
        assert retrieved.run_id == sample_ids['run1']
        assert retrieved.from_user_id == sample_ids['user1']
        assert retrieved.to_user_id == sample_ids['user2']
        assert retrieved.status == 'pending'
        assert retrieved.created_at is not None
        assert retrieved.resolved_at is None

    async def test_get_request_after_status_update(self, repo, sample_ids):
        """Test retrieving request after status update."""
        created = await repo.create_reassignment_request(
            run_id=sample_ids['run1'],
            from_user_id=sample_ids['user1'],
            to_user_id=sample_ids['user2'],
        )

        await repo.update_reassignment_status(created.id, 'accepted')

        retrieved = await repo.get_reassignment_request_by_id(created.id)

        assert retrieved.status == 'accepted'
        assert retrieved.resolved_at is not None


class TestGetPendingReassignmentForRun:
    """Test get_pending_reassignment_for_run() method."""

    async def test_get_pending_request_for_run(self, repo, sample_ids):
        """Test getting pending request for a run."""
        run_id = sample_ids['run1']

        created = await repo.create_reassignment_request(
            run_id=run_id,
            from_user_id=sample_ids['user1'],
            to_user_id=sample_ids['user2'],
        )

        pending = await repo.get_pending_reassignment_for_run(run_id)

        assert pending is not None
        assert pending.id == created.id
        assert pending.status == 'pending'

    async def test_get_pending_returns_none_when_no_requests(self, repo, sample_ids):
        """Test returns None when run has no reassignment requests."""
        run_id = sample_ids['run1']

        pending = await repo.get_pending_reassignment_for_run(run_id)

        assert pending is None

    async def test_get_pending_returns_none_when_all_resolved(self, repo, sample_ids):
        """Test returns None when all requests are resolved."""
        run_id = sample_ids['run1']

        # Create and accept request
        request = await repo.create_reassignment_request(
            run_id=run_id,
            from_user_id=sample_ids['user1'],
            to_user_id=sample_ids['user2'],
        )
        await repo.update_reassignment_status(request.id, 'accepted')

        pending = await repo.get_pending_reassignment_for_run(run_id)

        assert pending is None

    async def test_get_pending_excludes_declined(self, repo, sample_ids):
        """Test returns None when request is declined."""
        run_id = sample_ids['run1']

        # Create and decline request
        request = await repo.create_reassignment_request(
            run_id=run_id,
            from_user_id=sample_ids['user1'],
            to_user_id=sample_ids['user2'],
        )
        await repo.update_reassignment_status(request.id, 'declined')

        pending = await repo.get_pending_reassignment_for_run(run_id)

        assert pending is None

    async def test_get_pending_returns_first_pending_when_multiple(self, repo, sample_ids):
        """Test returns a pending request when multiple exist (should be only one in practice)."""
        run_id = sample_ids['run1']

        # Create multiple pending (edge case)
        request1 = await repo.create_reassignment_request(
            run_id=run_id,
            from_user_id=sample_ids['user1'],
            to_user_id=sample_ids['user2'],
        )
        request2 = await repo.create_reassignment_request(
            run_id=run_id,
            from_user_id=sample_ids['user1'],
            to_user_id=sample_ids['user3'],
        )

        pending = await repo.get_pending_reassignment_for_run(run_id)

        assert pending is not None
        assert pending.status == 'pending'
        # Should return one of them (implementation returns first found)
        assert pending.id in [request1.id, request2.id]

    async def test_get_pending_only_for_specific_run(self, repo, sample_ids):
        """Test returns request only for specific run."""
        run1_id = sample_ids['run1']
        run2_id = sample_ids['run2']

        # Create requests for different runs
        request1 = await repo.create_reassignment_request(
            run_id=run1_id,
            from_user_id=sample_ids['user1'],
            to_user_id=sample_ids['user2'],
        )
        request2 = await repo.create_reassignment_request(
            run_id=run2_id,
            from_user_id=sample_ids['user1'],
            to_user_id=sample_ids['user2'],
        )

        pending_run1 = await repo.get_pending_reassignment_for_run(run1_id)
        pending_run2 = await repo.get_pending_reassignment_for_run(run2_id)

        assert pending_run1.id == request1.id
        assert pending_run2.id == request2.id


class TestGetPendingReassignmentsFromUser:
    """Test get_pending_reassignments_from_user() method."""

    async def test_get_pending_requests_from_user(self, repo, sample_ids):
        """Test getting all pending requests created by a user."""
        from_user_id = sample_ids['user1']

        # Create requests from user1
        request1 = await repo.create_reassignment_request(
            run_id=sample_ids['run1'],
            from_user_id=from_user_id,
            to_user_id=sample_ids['user2'],
        )
        request2 = await repo.create_reassignment_request(
            run_id=sample_ids['run2'],
            from_user_id=from_user_id,
            to_user_id=sample_ids['user3'],
        )

        pending = await repo.get_pending_reassignments_from_user(from_user_id)

        assert len(pending) == 2
        pending_ids = {r.id for r in pending}
        assert {request1.id, request2.id} == pending_ids

    async def test_get_pending_from_user_empty_when_none(self, repo, sample_ids):
        """Test returns empty list when user has no pending requests."""
        user_id = sample_ids['user1']

        pending = await repo.get_pending_reassignments_from_user(user_id)

        assert pending == []

    async def test_get_pending_from_user_excludes_accepted(self, repo, sample_ids):
        """Test excludes accepted requests."""
        from_user_id = sample_ids['user1']

        # Create requests
        request1 = await repo.create_reassignment_request(
            run_id=sample_ids['run1'],
            from_user_id=from_user_id,
            to_user_id=sample_ids['user2'],
        )
        request2 = await repo.create_reassignment_request(
            run_id=sample_ids['run2'],
            from_user_id=from_user_id,
            to_user_id=sample_ids['user2'],
        )

        # Accept one
        await repo.update_reassignment_status(request1.id, 'accepted')

        pending = await repo.get_pending_reassignments_from_user(from_user_id)

        assert len(pending) == 1
        assert pending[0].id == request2.id

    async def test_get_pending_from_user_excludes_declined(self, repo, sample_ids):
        """Test excludes declined requests."""
        from_user_id = sample_ids['user1']

        # Create requests
        request1 = await repo.create_reassignment_request(
            run_id=sample_ids['run1'],
            from_user_id=from_user_id,
            to_user_id=sample_ids['user2'],
        )
        request2 = await repo.create_reassignment_request(
            run_id=sample_ids['run2'],
            from_user_id=from_user_id,
            to_user_id=sample_ids['user2'],
        )

        # Decline one
        await repo.update_reassignment_status(request1.id, 'declined')

        pending = await repo.get_pending_reassignments_from_user(from_user_id)

        assert len(pending) == 1
        assert pending[0].id == request2.id

    async def test_get_pending_from_user_excludes_cancelled(self, repo, sample_ids):
        """Test excludes cancelled requests."""
        from_user_id = sample_ids['user1']
        run_id = sample_ids['run1']

        # Create request
        await repo.create_reassignment_request(
            run_id=run_id,
            from_user_id=from_user_id,
            to_user_id=sample_ids['user2'],
        )

        # Cancel all for run
        await repo.cancel_all_pending_reassignments_for_run(run_id)

        pending = await repo.get_pending_reassignments_from_user(from_user_id)

        assert len(pending) == 0

    async def test_get_pending_from_user_only_from_specific_user(self, repo, sample_ids):
        """Test returns only requests from specific user."""
        user1_id = sample_ids['user1']
        user2_id = sample_ids['user2']

        # Create requests from different users
        request1 = await repo.create_reassignment_request(
            run_id=sample_ids['run1'],
            from_user_id=user1_id,
            to_user_id=sample_ids['user3'],
        )
        await repo.create_reassignment_request(
            run_id=sample_ids['run2'],
            from_user_id=user2_id,
            to_user_id=sample_ids['user3'],
        )

        pending_user1 = await repo.get_pending_reassignments_from_user(user1_id)

        assert len(pending_user1) == 1
        assert pending_user1[0].id == request1.id


class TestGetPendingReassignmentsToUser:
    """Test get_pending_reassignments_to_user() method."""

    async def test_get_pending_requests_to_user(self, repo, sample_ids):
        """Test getting all pending requests for user to respond to."""
        to_user_id = sample_ids['user2']

        # Create requests to user2
        request1 = await repo.create_reassignment_request(
            run_id=sample_ids['run1'],
            from_user_id=sample_ids['user1'],
            to_user_id=to_user_id,
        )
        request2 = await repo.create_reassignment_request(
            run_id=sample_ids['run2'],
            from_user_id=sample_ids['user3'],
            to_user_id=to_user_id,
        )

        pending = await repo.get_pending_reassignments_to_user(to_user_id)

        assert len(pending) == 2
        pending_ids = {r.id for r in pending}
        assert {request1.id, request2.id} == pending_ids

    async def test_get_pending_to_user_empty_when_none(self, repo, sample_ids):
        """Test returns empty list when user has no pending requests."""
        user_id = sample_ids['user2']

        pending = await repo.get_pending_reassignments_to_user(user_id)

        assert pending == []

    async def test_get_pending_to_user_excludes_accepted(self, repo, sample_ids):
        """Test excludes accepted requests."""
        to_user_id = sample_ids['user2']

        # Create requests
        request1 = await repo.create_reassignment_request(
            run_id=sample_ids['run1'],
            from_user_id=sample_ids['user1'],
            to_user_id=to_user_id,
        )
        request2 = await repo.create_reassignment_request(
            run_id=sample_ids['run2'],
            from_user_id=sample_ids['user1'],
            to_user_id=to_user_id,
        )

        # Accept one
        await repo.update_reassignment_status(request1.id, 'accepted')

        pending = await repo.get_pending_reassignments_to_user(to_user_id)

        assert len(pending) == 1
        assert pending[0].id == request2.id

    async def test_get_pending_to_user_excludes_declined(self, repo, sample_ids):
        """Test excludes declined requests."""
        to_user_id = sample_ids['user2']

        # Create requests
        request1 = await repo.create_reassignment_request(
            run_id=sample_ids['run1'],
            from_user_id=sample_ids['user1'],
            to_user_id=to_user_id,
        )
        request2 = await repo.create_reassignment_request(
            run_id=sample_ids['run2'],
            from_user_id=sample_ids['user1'],
            to_user_id=to_user_id,
        )

        # Decline one
        await repo.update_reassignment_status(request1.id, 'declined')

        pending = await repo.get_pending_reassignments_to_user(to_user_id)

        assert len(pending) == 1
        assert pending[0].id == request2.id

    async def test_get_pending_to_user_only_to_specific_user(self, repo, sample_ids):
        """Test returns only requests to specific user."""
        user2_id = sample_ids['user2']
        user3_id = sample_ids['user3']

        # Create requests to different users
        request1 = await repo.create_reassignment_request(
            run_id=sample_ids['run1'],
            from_user_id=sample_ids['user1'],
            to_user_id=user2_id,
        )
        await repo.create_reassignment_request(
            run_id=sample_ids['run2'],
            from_user_id=sample_ids['user1'],
            to_user_id=user3_id,
        )

        pending_user2 = await repo.get_pending_reassignments_to_user(user2_id)

        assert len(pending_user2) == 1
        assert pending_user2[0].id == request1.id

    async def test_get_pending_to_user_excludes_requests_from_user(self, repo, sample_ids):
        """Test excludes requests where user is sender (from_user)."""
        user_id = sample_ids['user1']

        # Create request where user1 is sender
        await repo.create_reassignment_request(
            run_id=sample_ids['run1'],
            from_user_id=user_id,
            to_user_id=sample_ids['user2'],
        )

        # Create request where user1 is recipient
        request2 = await repo.create_reassignment_request(
            run_id=sample_ids['run2'],
            from_user_id=sample_ids['user2'],
            to_user_id=user_id,
        )

        pending_to_user1 = await repo.get_pending_reassignments_to_user(user_id)

        assert len(pending_to_user1) == 1
        assert pending_to_user1[0].id == request2.id

    async def test_get_pending_to_user_multiple_pending_requests(self, repo, sample_ids):
        """Test getting multiple pending requests for user."""
        to_user_id = sample_ids['user2']

        # Create multiple requests
        request_ids = []
        for _ in range(5):
            request = await repo.create_reassignment_request(
                run_id=uuid4(),
                from_user_id=sample_ids['user1'],
                to_user_id=to_user_id,
            )
            request_ids.append(request.id)

        pending = await repo.get_pending_reassignments_to_user(to_user_id)

        assert len(pending) == 5
        assert {r.id for r in pending} == set(request_ids)


class TestUpdateReassignmentStatus:
    """Test update_reassignment_status() method."""

    async def test_update_status_to_accepted(self, repo, sample_ids):
        """Test updating request status to 'accepted'."""
        request = await repo.create_reassignment_request(
            run_id=sample_ids['run1'],
            from_user_id=sample_ids['user1'],
            to_user_id=sample_ids['user2'],
        )

        result = await repo.update_reassignment_status(request.id, 'accepted')

        assert result is True
        retrieved = await repo.get_reassignment_request_by_id(request.id)
        assert retrieved.status == 'accepted'

    async def test_update_status_to_declined(self, repo, sample_ids):
        """Test updating request status to 'declined'."""
        request = await repo.create_reassignment_request(
            run_id=sample_ids['run1'],
            from_user_id=sample_ids['user1'],
            to_user_id=sample_ids['user2'],
        )

        result = await repo.update_reassignment_status(request.id, 'declined')

        assert result is True
        retrieved = await repo.get_reassignment_request_by_id(request.id)
        assert retrieved.status == 'declined'

    async def test_update_status_sets_resolved_at_timestamp(self, repo, sample_ids):
        """Test updating status sets resolved_at timestamp."""
        request = await repo.create_reassignment_request(
            run_id=sample_ids['run1'],
            from_user_id=sample_ids['user1'],
            to_user_id=sample_ids['user2'],
        )

        assert request.resolved_at is None

        before = datetime.now(UTC)
        await repo.update_reassignment_status(request.id, 'accepted')
        after = datetime.now(UTC)

        retrieved = await repo.get_reassignment_request_by_id(request.id)
        assert retrieved.resolved_at is not None
        assert before <= retrieved.resolved_at <= after

    async def test_update_status_returns_false_for_nonexistent(self, repo):
        """Test updating nonexistent request returns False."""
        nonexistent_id = uuid4()

        result = await repo.update_reassignment_status(nonexistent_id, 'accepted')

        assert result is False

    async def test_update_status_multiple_times(self, repo, sample_ids):
        """Test updating status multiple times."""
        request = await repo.create_reassignment_request(
            run_id=sample_ids['run1'],
            from_user_id=sample_ids['user1'],
            to_user_id=sample_ids['user2'],
        )

        # First update
        await repo.update_reassignment_status(request.id, 'accepted')
        retrieved1 = await repo.get_reassignment_request_by_id(request.id)
        assert retrieved1.status == 'accepted'
        first_resolved_at = retrieved1.resolved_at

        # Second update (changing mind)
        await repo.update_reassignment_status(request.id, 'declined')
        retrieved2 = await repo.get_reassignment_request_by_id(request.id)
        assert retrieved2.status == 'declined'
        # resolved_at should be updated
        assert retrieved2.resolved_at >= first_resolved_at

    async def test_update_status_persists(self, repo, sample_ids):
        """Test status update persists across retrievals."""
        request = await repo.create_reassignment_request(
            run_id=sample_ids['run1'],
            from_user_id=sample_ids['user1'],
            to_user_id=sample_ids['user2'],
        )

        await repo.update_reassignment_status(request.id, 'accepted')

        # Retrieve multiple times
        retrieved1 = await repo.get_reassignment_request_by_id(request.id)
        retrieved2 = await repo.get_reassignment_request_by_id(request.id)

        assert retrieved1.status == 'accepted'
        assert retrieved2.status == 'accepted'

    async def test_update_status_to_custom_status(self, repo, sample_ids):
        """Test updating to custom status (e.g., 'cancelled')."""
        request = await repo.create_reassignment_request(
            run_id=sample_ids['run1'],
            from_user_id=sample_ids['user1'],
            to_user_id=sample_ids['user2'],
        )

        await repo.update_reassignment_status(request.id, 'cancelled')

        retrieved = await repo.get_reassignment_request_by_id(request.id)
        assert retrieved.status == 'cancelled'

    async def test_update_status_affects_pending_lists(self, repo, sample_ids):
        """Test status update removes from pending lists."""
        from_user_id = sample_ids['user1']
        to_user_id = sample_ids['user2']

        request = await repo.create_reassignment_request(
            run_id=sample_ids['run1'],
            from_user_id=from_user_id,
            to_user_id=to_user_id,
        )

        # Should be in pending lists
        assert len(await repo.get_pending_reassignments_from_user(from_user_id)) == 1
        assert len(await repo.get_pending_reassignments_to_user(to_user_id)) == 1

        # Update status
        await repo.update_reassignment_status(request.id, 'accepted')

        # Should no longer be in pending lists
        assert len(await repo.get_pending_reassignments_from_user(from_user_id)) == 0
        assert len(await repo.get_pending_reassignments_to_user(to_user_id)) == 0


class TestCancelAllPendingReassignmentsForRun:
    """Test cancel_all_pending_reassignments_for_run() method."""

    async def test_cancel_all_pending_for_run(self, repo, sample_ids):
        """Test cancelling all pending requests for a run."""
        run_id = sample_ids['run1']

        # Create pending request
        request = await repo.create_reassignment_request(
            run_id=run_id,
            from_user_id=sample_ids['user1'],
            to_user_id=sample_ids['user2'],
        )

        count = await repo.cancel_all_pending_reassignments_for_run(run_id)

        assert count == 1
        retrieved = await repo.get_reassignment_request_by_id(request.id)
        assert retrieved.status == 'cancelled'

    async def test_cancel_all_returns_count(self, repo, sample_ids):
        """Test cancel_all returns count of cancelled requests."""
        run_id = sample_ids['run1']

        # Create multiple pending requests (edge case)
        for _ in range(3):
            await repo.create_reassignment_request(
                run_id=run_id,
                from_user_id=sample_ids['user1'],
                to_user_id=sample_ids['user2'],
            )

        count = await repo.cancel_all_pending_reassignments_for_run(run_id)

        assert count == 3

    async def test_cancel_all_sets_resolved_at(self, repo, sample_ids):
        """Test cancel_all sets resolved_at timestamp."""
        run_id = sample_ids['run1']

        request = await repo.create_reassignment_request(
            run_id=run_id,
            from_user_id=sample_ids['user1'],
            to_user_id=sample_ids['user2'],
        )

        before = datetime.now(UTC)
        await repo.cancel_all_pending_reassignments_for_run(run_id)
        after = datetime.now(UTC)

        retrieved = await repo.get_reassignment_request_by_id(request.id)
        assert retrieved.resolved_at is not None
        assert before <= retrieved.resolved_at <= after

    async def test_cancel_all_only_cancels_pending(self, repo, sample_ids):
        """Test cancel_all only cancels pending requests."""
        run_id = sample_ids['run1']

        # Create and accept one
        request1 = await repo.create_reassignment_request(
            run_id=run_id,
            from_user_id=sample_ids['user1'],
            to_user_id=sample_ids['user2'],
        )
        await repo.update_reassignment_status(request1.id, 'accepted')

        # Create pending
        request2 = await repo.create_reassignment_request(
            run_id=run_id,
            from_user_id=sample_ids['user1'],
            to_user_id=sample_ids['user3'],
        )

        count = await repo.cancel_all_pending_reassignments_for_run(run_id)

        assert count == 1
        # First should still be accepted
        assert (await repo.get_reassignment_request_by_id(request1.id)).status == 'accepted'
        # Second should be cancelled
        assert (await repo.get_reassignment_request_by_id(request2.id)).status == 'cancelled'

    async def test_cancel_all_only_affects_specific_run(self, repo, sample_ids):
        """Test cancel_all only affects requests for specific run."""
        run1_id = sample_ids['run1']
        run2_id = sample_ids['run2']

        # Create requests for both runs
        request1 = await repo.create_reassignment_request(
            run_id=run1_id,
            from_user_id=sample_ids['user1'],
            to_user_id=sample_ids['user2'],
        )
        request2 = await repo.create_reassignment_request(
            run_id=run2_id,
            from_user_id=sample_ids['user1'],
            to_user_id=sample_ids['user2'],
        )

        count = await repo.cancel_all_pending_reassignments_for_run(run1_id)

        assert count == 1
        assert (await repo.get_reassignment_request_by_id(request1.id)).status == 'cancelled'
        assert (await repo.get_reassignment_request_by_id(request2.id)).status == 'pending'

    async def test_cancel_all_when_no_pending(self, repo, sample_ids):
        """Test cancel_all returns 0 when no pending requests."""
        run_id = sample_ids['run1']

        count = await repo.cancel_all_pending_reassignments_for_run(run_id)

        assert count == 0


class TestComplexScenarios:
    """Test complex workflow scenarios."""

    async def test_full_workflow_create_to_accept(self, repo, sample_ids):
        """Test full workflow: create → pending → accept."""
        run_id = sample_ids['run1']
        from_user_id = sample_ids['user1']
        to_user_id = sample_ids['user2']

        # Create request
        request = await repo.create_reassignment_request(
            run_id=run_id,
            from_user_id=from_user_id,
            to_user_id=to_user_id,
        )

        # Verify pending state
        assert request.status == 'pending'
        assert request.resolved_at is None
        assert (await repo.get_pending_reassignment_for_run(run_id)).id == request.id
        assert len(await repo.get_pending_reassignments_to_user(to_user_id)) == 1

        # Accept request
        await repo.update_reassignment_status(request.id, 'accepted')

        # Verify accepted state
        retrieved = await repo.get_reassignment_request_by_id(request.id)
        assert retrieved.status == 'accepted'
        assert retrieved.resolved_at is not None
        assert await repo.get_pending_reassignment_for_run(run_id) is None
        assert len(await repo.get_pending_reassignments_to_user(to_user_id)) == 0

    async def test_full_workflow_create_to_decline(self, repo, sample_ids):
        """Test full workflow: create → pending → decline."""
        run_id = sample_ids['run1']
        from_user_id = sample_ids['user1']
        to_user_id = sample_ids['user2']

        # Create request
        request = await repo.create_reassignment_request(
            run_id=run_id,
            from_user_id=from_user_id,
            to_user_id=to_user_id,
        )

        # Verify pending
        assert request.status == 'pending'
        assert len(await repo.get_pending_reassignments_from_user(from_user_id)) == 1

        # Decline request
        await repo.update_reassignment_status(request.id, 'declined')

        # Verify declined
        retrieved = await repo.get_reassignment_request_by_id(request.id)
        assert retrieved.status == 'declined'
        assert retrieved.resolved_at is not None
        assert len(await repo.get_pending_reassignments_from_user(from_user_id)) == 0

    async def test_multiple_requests_to_same_user(self, repo, sample_ids):
        """Test multiple reassignment requests to same user."""
        to_user_id = sample_ids['user2']

        # Create multiple requests from different runs
        request1 = await repo.create_reassignment_request(
            run_id=sample_ids['run1'],
            from_user_id=sample_ids['user1'],
            to_user_id=to_user_id,
        )
        request2 = await repo.create_reassignment_request(
            run_id=sample_ids['run2'],
            from_user_id=sample_ids['user3'],
            to_user_id=to_user_id,
        )

        pending_to_user = await repo.get_pending_reassignments_to_user(to_user_id)

        assert len(pending_to_user) == 2
        assert {r.id for r in pending_to_user} == {request1.id, request2.id}

    async def test_cancel_pending_request_via_delete_simulation(self, repo, sample_ids):
        """Test cancelling pending request (delete before resolution)."""
        run_id = sample_ids['run1']
        from_user_id = sample_ids['user1']

        # Create request
        request = await repo.create_reassignment_request(
            run_id=run_id,
            from_user_id=from_user_id,
            to_user_id=sample_ids['user2'],
        )

        # Cancel all pending for run (simulates deletion)
        count = await repo.cancel_all_pending_reassignments_for_run(run_id)

        assert count == 1
        assert (await repo.get_reassignment_request_by_id(request.id)).status == 'cancelled'
        assert len(await repo.get_pending_reassignments_from_user(from_user_id)) == 0

    async def test_reassignment_chain_sequence(self, repo, sample_ids):
        """Test reassignment chain: A→B→C."""
        run_id = sample_ids['run1']
        user_a = sample_ids['user1']
        user_b = sample_ids['user2']
        user_c = sample_ids['user3']

        # A requests reassignment to B
        request1 = await repo.create_reassignment_request(
            run_id=run_id,
            from_user_id=user_a,
            to_user_id=user_b,
        )

        # B accepts
        await repo.update_reassignment_status(request1.id, 'accepted')

        # B requests reassignment to C
        request2 = await repo.create_reassignment_request(
            run_id=run_id,
            from_user_id=user_b,
            to_user_id=user_c,
        )

        # C accepts
        await repo.update_reassignment_status(request2.id, 'accepted')

        # Verify chain
        assert (await repo.get_reassignment_request_by_id(request1.id)).status == 'accepted'
        assert (await repo.get_reassignment_request_by_id(request2.id)).status == 'accepted'
        assert await repo.get_pending_reassignment_for_run(run_id) is None


class TestEdgeCases:
    """Test edge cases and data integrity."""

    async def test_request_with_same_user_as_from_and_to(self, repo, sample_ids):
        """Test creating request where from_user and to_user are same (allowed by system)."""
        user_id = sample_ids['user1']
        run_id = sample_ids['run1']

        # System allows this (business logic should prevent)
        request = await repo.create_reassignment_request(
            run_id=run_id,
            from_user_id=user_id,
            to_user_id=user_id,
        )

        assert request.from_user_id == request.to_user_id == user_id

    async def test_concurrent_requests_from_same_user(self, repo, sample_ids):
        """Test multiple concurrent requests from same user to different targets."""
        from_user_id = sample_ids['user1']

        # Create multiple pending requests
        request1 = await repo.create_reassignment_request(
            run_id=sample_ids['run1'],
            from_user_id=from_user_id,
            to_user_id=sample_ids['user2'],
        )
        request2 = await repo.create_reassignment_request(
            run_id=sample_ids['run2'],
            from_user_id=from_user_id,
            to_user_id=sample_ids['user3'],
        )

        pending_from_user = await repo.get_pending_reassignments_from_user(from_user_id)

        assert len(pending_from_user) == 2
        assert {r.id for r in pending_from_user} == {request1.id, request2.id}

    async def test_storage_is_singleton(self):
        """Test that MemoryStorage is a singleton (all instances share data)."""
        storage1 = MemoryStorage()
        storage2 = MemoryStorage()

        # Both should be the same instance
        assert storage1 is storage2

    async def test_timestamp_consistency(self, repo, sample_ids):
        """Test that timestamps are consistent and logical."""
        request = await repo.create_reassignment_request(
            run_id=sample_ids['run1'],
            from_user_id=sample_ids['user1'],
            to_user_id=sample_ids['user2'],
        )

        created_at = request.created_at

        # Update status after a moment
        await repo.update_reassignment_status(request.id, 'accepted')

        retrieved = await repo.get_reassignment_request_by_id(request.id)
        resolved_at = retrieved.resolved_at

        # resolved_at should be >= created_at
        assert resolved_at >= created_at

    async def test_multiple_status_updates_timestamp_progression(self, repo, sample_ids):
        """Test that multiple status updates have progressing timestamps."""
        request = await repo.create_reassignment_request(
            run_id=sample_ids['run1'],
            from_user_id=sample_ids['user1'],
            to_user_id=sample_ids['user2'],
        )

        # First update
        await repo.update_reassignment_status(request.id, 'accepted')
        first_resolved = (await repo.get_reassignment_request_by_id(request.id)).resolved_at

        # Second update
        await repo.update_reassignment_status(request.id, 'declined')
        second_resolved = (await repo.get_reassignment_request_by_id(request.id)).resolved_at

        # Second timestamp should be >= first
        assert second_resolved >= first_resolved

    async def test_get_pending_lists_consistency(self, repo, sample_ids):
        """Test that pending lists are consistent across calls."""
        from_user_id = sample_ids['user1']
        to_user_id = sample_ids['user2']

        # Create requests
        for _ in range(3):
            await repo.create_reassignment_request(
                run_id=uuid4(),
                from_user_id=from_user_id,
                to_user_id=to_user_id,
            )

        # Get multiple times
        from_list1 = await repo.get_pending_reassignments_from_user(from_user_id)
        from_list2 = await repo.get_pending_reassignments_from_user(from_user_id)

        to_list1 = await repo.get_pending_reassignments_to_user(to_user_id)
        to_list2 = await repo.get_pending_reassignments_to_user(to_user_id)

        # Should be consistent
        assert {r.id for r in from_list1} == {r.id for r in from_list2}
        assert {r.id for r in to_list1} == {r.id for r in to_list2}
