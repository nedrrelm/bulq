"""Database reassignment repository implementation."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import LeaderReassignmentRequest
from app.repositories.abstract.reassignment import AbstractReassignmentRepository


class DatabaseReassignmentRepository(AbstractReassignmentRepository):
    """Database implementation of reassignment repository."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_reassignment_request(
        self, run_id: UUID, from_user_id: UUID, to_user_id: UUID
    ) -> LeaderReassignmentRequest:
        """Create a leader reassignment request."""
        request = LeaderReassignmentRequest(
            run_id=run_id, from_user_id=from_user_id, to_user_id=to_user_id, status='pending'
        )
        self.db.add(request)
        await self.db.commit()
        await self.db.refresh(request)
        return request

    async def get_reassignment_request_by_id(self, request_id: UUID) -> LeaderReassignmentRequest | None:
        """Get a reassignment request by ID."""
        result = await self.db.execute(
            select(LeaderReassignmentRequest).filter(LeaderReassignmentRequest.id == request_id)
        )
        return result.scalar_one_or_none()

    async def get_pending_reassignment_for_run(self, run_id: UUID) -> LeaderReassignmentRequest | None:
        """Get pending reassignment request for a run (if any)."""
        result = await self.db.execute(
            select(LeaderReassignmentRequest).filter(
                LeaderReassignmentRequest.run_id == run_id,
                LeaderReassignmentRequest.status == 'pending',
            )
        )
        return result.scalar_one_or_none()

    async def get_pending_reassignments_from_user(self, user_id: UUID) -> list[LeaderReassignmentRequest]:
        """Get all pending reassignment requests created by a user."""
        result = await self.db.execute(
            select(LeaderReassignmentRequest).filter(
                LeaderReassignmentRequest.from_user_id == user_id,
                LeaderReassignmentRequest.status == 'pending',
            )
        )
        return list(result.scalars().all())

    async def get_pending_reassignments_to_user(self, user_id: UUID) -> list[LeaderReassignmentRequest]:
        """Get all pending reassignment requests for a user to respond to."""
        result = await self.db.execute(
            select(LeaderReassignmentRequest).filter(
                LeaderReassignmentRequest.to_user_id == user_id,
                LeaderReassignmentRequest.status == 'pending',
            )
        )
        return list(result.scalars().all())

    async def update_reassignment_status(self, request_id: UUID, status: str) -> bool:
        """Update the status of a reassignment request (accepted/declined)."""
        result = await self.db.execute(
            select(LeaderReassignmentRequest).filter(LeaderReassignmentRequest.id == request_id)
        )
        request = result.scalar_one_or_none()
        if not request:
            return False

        request.status = status
        request.resolved_at = datetime.now()
        await self.db.commit()
        return True

    async def cancel_all_pending_reassignments_for_run(self, run_id: UUID) -> int:
        """Cancel all pending reassignment requests for a run. Returns count of cancelled requests."""
        result = await self.db.execute(
            update(LeaderReassignmentRequest)
            .filter(
                LeaderReassignmentRequest.run_id == run_id,
                LeaderReassignmentRequest.status == 'pending',
            )
            .values(status='cancelled', resolved_at=datetime.now())
        )
        await self.db.commit()
        return result.rowcount
