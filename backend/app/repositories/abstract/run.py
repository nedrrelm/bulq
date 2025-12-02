"""Abstract run repository interface."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.core.models import Run, RunParticipation


class AbstractRunRepository(ABC):
    """Abstract base class for run repository operations."""

    @abstractmethod
    async def get_runs_by_group(self, group_id: UUID) -> list[Run]:
        """Get all runs for a group."""
        raise NotImplementedError('Subclass must implement get_runs_by_group')

    @abstractmethod
    async def get_completed_cancelled_runs_by_group(
        self, group_id: UUID, limit: int = 10, offset: int = 0
    ) -> list[Run]:
        """Get completed and cancelled runs for a group (paginated)."""
        raise NotImplementedError('Subclass must implement get_completed_cancelled_runs_by_group')

    @abstractmethod
    async def create_run(
        self, group_id: UUID, store_id: UUID, leader_id: UUID, comment: str | None = None
    ) -> Run:
        """Create a new run with the leader as first participant."""
        raise NotImplementedError('Subclass must implement create_run')

    @abstractmethod
    async def update_run_comment(self, run_id: UUID, comment: str | None) -> Run | None:
        """Update the comment for a run."""
        raise NotImplementedError('Subclass must implement update_run_comment')

    @abstractmethod
    async def get_participation(self, user_id: UUID, run_id: UUID) -> RunParticipation | None:
        """Get a user's participation in a run."""
        raise NotImplementedError('Subclass must implement get_participation')

    @abstractmethod
    async def get_run_participations(self, run_id: UUID) -> list[RunParticipation]:
        """Get all participations for a run."""
        raise NotImplementedError('Subclass must implement get_run_participations')

    @abstractmethod
    async def get_run_participations_with_users(self, run_id: UUID) -> list[RunParticipation]:
        """Get all participations for a run with user data eagerly loaded.

        This avoids N+1 query problems when you need to access participation.user.
        For DatabaseRepository, this should use SQLAlchemy's joinedload().
        For MemoryRepository, this pre-populates the user relationship.
        """
        raise NotImplementedError('Subclass must implement get_run_participations_with_users')

    @abstractmethod
    async def create_participation(
        self, user_id: UUID, run_id: UUID, is_leader: bool = False, is_helper: bool = False
    ) -> RunParticipation:
        """Create a participation record for a user in a run."""
        raise NotImplementedError('Subclass must implement create_participation')

    @abstractmethod
    async def update_participation_ready(
        self, participation_id: UUID, is_ready: bool
    ) -> RunParticipation | None:
        """Update the ready status of a participation."""
        raise NotImplementedError('Subclass must implement update_participation_ready')

    @abstractmethod
    async def update_participation_helper(
        self, user_id: UUID, run_id: UUID, is_helper: bool
    ) -> RunParticipation | None:
        """Update the helper status of a participation."""
        raise NotImplementedError('Subclass must implement update_participation_helper')

    @abstractmethod
    async def get_run_by_id(self, run_id: UUID) -> Run | None:
        """Get run by ID."""
        raise NotImplementedError('Subclass must implement get_run_by_id')

    @abstractmethod
    async def update_run_state(self, run_id: UUID, new_state: str) -> Run | None:
        """Update the state of a run."""
        raise NotImplementedError('Subclass must implement update_run_state')
