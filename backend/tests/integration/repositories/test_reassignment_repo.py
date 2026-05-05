"""Integration tests for DatabaseReassignmentRepository."""

import uuid

import pytest

from app.repositories.database.reassignment import DatabaseReassignmentRepository

pytestmark = pytest.mark.integration


@pytest.fixture
def repo(db_session):
    return DatabaseReassignmentRepository(db=db_session)


@pytest.fixture
def run_with_participants(create_run, create_user, create_participation):
    """Create a run with a leader and an additional participant."""
    run, leader = create_run()
    to_user = create_user()
    create_participation(to_user, run)
    return run, leader.id, to_user.id


class TestCreateReassignmentRequest:
    def test_creates_request(self, repo, run_with_participants):
        run, from_user_id, to_user_id = run_with_participants

        request = repo.create_reassignment_request(run.id, from_user_id, to_user_id)

        assert request.id is not None
        assert request.run_id == run.id
        assert request.from_user_id == from_user_id
        assert request.to_user_id == to_user_id
        assert request.status == 'pending'
        assert request.created_at is not None
        assert request.resolved_at is None


class TestGetReassignmentRequestById:
    def test_returns_request_when_found(self, repo, run_with_participants):
        run, from_user_id, to_user_id = run_with_participants
        created = repo.create_reassignment_request(run.id, from_user_id, to_user_id)

        found = repo.get_reassignment_request_by_id(created.id)
        assert found is not None
        assert found.id == created.id

    def test_returns_none_when_not_found(self, repo):
        assert repo.get_reassignment_request_by_id(uuid.uuid4()) is None


class TestGetPendingReassignmentForRun:
    def test_returns_pending_request(self, repo, run_with_participants):
        run, from_user_id, to_user_id = run_with_participants
        repo.create_reassignment_request(run.id, from_user_id, to_user_id)

        found = repo.get_pending_reassignment_for_run(run.id)
        assert found is not None
        assert found.run_id == run.id
        assert found.status == 'pending'

    def test_returns_none_when_no_pending(self, repo, run_with_participants):
        run, from_user_id, to_user_id = run_with_participants
        req = repo.create_reassignment_request(run.id, from_user_id, to_user_id)
        repo.update_reassignment_status(req.id, 'accepted')

        found = repo.get_pending_reassignment_for_run(run.id)
        assert found is None

    def test_returns_none_for_run_without_requests(self, repo):
        found = repo.get_pending_reassignment_for_run(uuid.uuid4())
        assert found is None


class TestGetPendingReassignmentsFromUser:
    def test_returns_pending_from_user(self, repo, run_with_participants):
        run, from_user_id, to_user_id = run_with_participants
        repo.create_reassignment_request(run.id, from_user_id, to_user_id)

        results = repo.get_pending_reassignments_from_user(from_user_id)
        assert len(results) == 1
        assert results[0].from_user_id == from_user_id

    def test_excludes_non_pending(self, repo, run_with_participants):
        run, from_user_id, to_user_id = run_with_participants
        req = repo.create_reassignment_request(run.id, from_user_id, to_user_id)
        repo.update_reassignment_status(req.id, 'declined')

        results = repo.get_pending_reassignments_from_user(from_user_id)
        assert results == []


class TestGetPendingReassignmentsToUser:
    def test_returns_pending_to_user(self, repo, run_with_participants):
        run, from_user_id, to_user_id = run_with_participants
        repo.create_reassignment_request(run.id, from_user_id, to_user_id)

        results = repo.get_pending_reassignments_to_user(to_user_id)
        assert len(results) == 1
        assert results[0].to_user_id == to_user_id

    def test_excludes_non_pending(self, repo, run_with_participants):
        run, from_user_id, to_user_id = run_with_participants
        req = repo.create_reassignment_request(run.id, from_user_id, to_user_id)
        repo.update_reassignment_status(req.id, 'cancelled')

        results = repo.get_pending_reassignments_to_user(to_user_id)
        assert results == []


class TestUpdateReassignmentStatus:
    def test_accepts_request(self, repo, run_with_participants):
        run, from_user_id, to_user_id = run_with_participants
        req = repo.create_reassignment_request(run.id, from_user_id, to_user_id)

        result = repo.update_reassignment_status(req.id, 'accepted')
        assert result is True

        updated = repo.get_reassignment_request_by_id(req.id)
        assert updated.status == 'accepted'
        assert updated.resolved_at is not None

    def test_declines_request(self, repo, run_with_participants):
        run, from_user_id, to_user_id = run_with_participants
        req = repo.create_reassignment_request(run.id, from_user_id, to_user_id)

        result = repo.update_reassignment_status(req.id, 'declined')
        assert result is True

        updated = repo.get_reassignment_request_by_id(req.id)
        assert updated.status == 'declined'
        assert updated.resolved_at is not None

    def test_cancels_request(self, repo, run_with_participants):
        run, from_user_id, to_user_id = run_with_participants
        req = repo.create_reassignment_request(run.id, from_user_id, to_user_id)

        result = repo.update_reassignment_status(req.id, 'cancelled')
        assert result is True

        updated = repo.get_reassignment_request_by_id(req.id)
        assert updated.status == 'cancelled'

    def test_returns_false_for_nonexistent(self, repo):
        result = repo.update_reassignment_status(uuid.uuid4(), 'accepted')
        assert result is False


class TestCancelAllPendingReassignmentsForRun:
    def test_cancels_all_pending(self, repo, create_run, create_user, create_participation):
        run, leader = create_run()
        user2 = create_user()
        user3 = create_user()
        create_participation(user2, run)
        create_participation(user3, run)

        repo.create_reassignment_request(run.id, leader.id, user2.id)
        repo.create_reassignment_request(run.id, leader.id, user3.id)

        count = repo.cancel_all_pending_reassignments_for_run(run.id)
        assert count == 2

        assert repo.get_pending_reassignment_for_run(run.id) is None

    def test_returns_zero_when_no_pending(self, repo):
        count = repo.cancel_all_pending_reassignments_for_run(uuid.uuid4())
        assert count == 0
