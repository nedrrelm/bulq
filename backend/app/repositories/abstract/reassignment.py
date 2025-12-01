"""Abstract reassignment repository interface."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.core.models import LeaderReassignmentRequest


class AbstractReassignmentRepository(ABC):
    """Abstract base class for reassignment repository operations."""

    @abstractmethod
    def create_reassignment_request(
        self, run_id: UUID, from_user_id: UUID, to_user_id: UUID
    ) -> LeaderReassignmentRequest:
        """Create a leader reassignment request."""
        raise NotImplementedError('Subclass must implement create_reassignment_request')

    @abstractmethod
    def get_reassignment_request_by_id(self, request_id: UUID) -> LeaderReassignmentRequest | None:
        """Get a reassignment request by ID."""
        raise NotImplementedError('Subclass must implement get_reassignment_request_by_id')

    @abstractmethod
    def get_pending_reassignment_for_run(self, run_id: UUID) -> LeaderReassignmentRequest | None:
        """Get pending reassignment request for a run (if any)."""
        raise NotImplementedError('Subclass must implement get_pending_reassignment_for_run')

    @abstractmethod
    def get_pending_reassignments_from_user(self, user_id: UUID) -> list[LeaderReassignmentRequest]:
        """Get all pending reassignment requests created by a user."""
        raise NotImplementedError('Subclass must implement get_pending_reassignments_from_user')

    @abstractmethod
    def get_pending_reassignments_to_user(self, user_id: UUID) -> list[LeaderReassignmentRequest]:
        """Get all pending reassignment requests for a user to respond to."""
        raise NotImplementedError('Subclass must implement get_pending_reassignments_to_user')

    @abstractmethod
    def update_reassignment_status(self, request_id: UUID, status: str) -> bool:
        """Update the status of a reassignment request (accepted/declined)."""
        raise NotImplementedError('Subclass must implement update_reassignment_status')

    @abstractmethod
    def cancel_all_pending_reassignments_for_run(self, run_id: UUID) -> int:
        """Cancel all pending reassignment requests for a run. Returns count of cancelled requests."""
        raise NotImplementedError(
            'Subclass must implement cancel_all_pending_reassignments_for_run'
        )
