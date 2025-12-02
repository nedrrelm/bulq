"""Memory reassignment repository implementation."""

from datetime import datetime
from uuid import UUID, uuid4

from app.core.models import LeaderReassignmentRequest
from app.repositories.abstract.reassignment import AbstractReassignmentRepository
from app.repositories.memory.storage import MemoryStorage


class MemoryReassignmentRepository(AbstractReassignmentRepository):
    """Memory implementation of reassignment repository."""

    def __init__(self, storage: MemoryStorage):
        self.storage = storage

    async def create_reassignment_request(
        self, run_id: UUID, from_user_id: UUID, to_user_id: UUID
    ) -> LeaderReassignmentRequest:
        """Create a leader reassignment request."""
        request_id = uuid4()
        request = LeaderReassignmentRequest(
            id=request_id,
            run_id=run_id,
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            status='pending',
            created_at=datetime.now(),
            resolved_at=None,
        )
        self.storage.reassignment_requests[request_id] = request
        return request

    async def get_reassignment_request_by_id(self, request_id: UUID) -> LeaderReassignmentRequest | None:
        """Get a reassignment request by ID."""
        return self.storage.reassignment_requests.get(request_id)

    async def get_pending_reassignment_for_run(self, run_id: UUID) -> LeaderReassignmentRequest | None:
        """Get pending reassignment request for a run (if any)."""
        for request in self.storage.reassignment_requests.values():
            if request.run_id == run_id and request.status == 'pending':
                return request
        return None

    async def get_pending_reassignments_from_user(self, user_id: UUID) -> list[LeaderReassignmentRequest]:
        """Get all pending reassignment requests created by a user."""
        return [
            request
            for request in self.storage.reassignment_requests.values()
            if request.from_user_id == user_id and request.status == 'pending'
        ]

    async def get_pending_reassignments_to_user(self, user_id: UUID) -> list[LeaderReassignmentRequest]:
        """Get all pending reassignment requests for a user to respond to."""
        return [
            request
            for request in self.storage.reassignment_requests.values()
            if request.to_user_id == user_id and request.status == 'pending'
        ]

    async def update_reassignment_status(self, request_id: UUID, status: str) -> bool:
        """Update the status of a reassignment request (accepted/declined)."""
        request = self.storage.reassignment_requests.get(request_id)
        if not request:
            return False

        request.status = status
        request.resolved_at = datetime.now()
        return True

    async def cancel_all_pending_reassignments_for_run(self, run_id: UUID) -> int:
        """Cancel all pending reassignment requests for a run. Returns count of cancelled requests."""
        count = 0
        for request in self.storage.reassignment_requests.values():
            if request.run_id == run_id and request.status == 'pending':
                request.status = 'cancelled'
                request.resolved_at = datetime.now()
                count += 1
        return count
