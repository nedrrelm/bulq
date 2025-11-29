"""Database reassignment repository implementation."""

from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.models import LeaderReassignmentRequest
from app.repositories.abstract.reassignment import AbstractReassignmentRepository


class DatabaseReassignmentRepository(AbstractReassignmentRepository):
    """Database implementation of reassignment repository."""

    def __init__(self, db: Session):
        self.db = db

    def create_reassignment_request(
        self, run_id: UUID, from_user_id: UUID, to_user_id: UUID
    ) -> LeaderReassignmentRequest:
        """Create a leader reassignment request."""
        request = LeaderReassignmentRequest(
            run_id=run_id, from_user_id=from_user_id, to_user_id=to_user_id, status='pending'
        )
        self.db.add(request)
        self.db.commit()
        self.db.refresh(request)
        return request

    def get_reassignment_request_by_id(self, request_id: UUID) -> LeaderReassignmentRequest | None:
        """Get a reassignment request by ID."""
        return (
            self.db.query(LeaderReassignmentRequest)
            .filter(LeaderReassignmentRequest.id == request_id)
            .first()
        )

    def get_pending_reassignment_for_run(self, run_id: UUID) -> LeaderReassignmentRequest | None:
        """Get pending reassignment request for a run (if any)."""
        return (
            self.db.query(LeaderReassignmentRequest)
            .filter(
                LeaderReassignmentRequest.run_id == run_id,
                LeaderReassignmentRequest.status == 'pending',
            )
            .first()
        )

    def get_pending_reassignments_from_user(self, user_id: UUID) -> list[LeaderReassignmentRequest]:
        """Get all pending reassignment requests created by a user."""
        return (
            self.db.query(LeaderReassignmentRequest)
            .filter(
                LeaderReassignmentRequest.from_user_id == user_id,
                LeaderReassignmentRequest.status == 'pending',
            )
            .all()
        )

    def get_pending_reassignments_to_user(self, user_id: UUID) -> list[LeaderReassignmentRequest]:
        """Get all pending reassignment requests for a user to respond to."""
        return (
            self.db.query(LeaderReassignmentRequest)
            .filter(
                LeaderReassignmentRequest.to_user_id == user_id,
                LeaderReassignmentRequest.status == 'pending',
            )
            .all()
        )

    def update_reassignment_status(self, request_id: UUID, status: str) -> bool:
        """Update the status of a reassignment request (accepted/declined)."""
        request = (
            self.db.query(LeaderReassignmentRequest)
            .filter(LeaderReassignmentRequest.id == request_id)
            .first()
        )
        if not request:
            return False

        request.status = status
        request.resolved_at = datetime.now()
        self.db.commit()
        return True

    def cancel_all_pending_reassignments_for_run(self, run_id: UUID) -> int:
        """Cancel all pending reassignment requests for a run. Returns count of cancelled requests."""
        count = (
            self.db.query(LeaderReassignmentRequest)
            .filter(
                LeaderReassignmentRequest.run_id == run_id,
                LeaderReassignmentRequest.status == 'pending',
            )
            .update(
                {
                    LeaderReassignmentRequest.status: 'cancelled',
                    LeaderReassignmentRequest.resolved_at: datetime.now(),
                }
            )
        )
        self.db.commit()
        return count
