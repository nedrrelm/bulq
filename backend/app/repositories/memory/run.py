"""Memory run repository implementation."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.core.models import Run, RunParticipation
from app.core.run_state import RunState, state_machine
from app.infrastructure.request_context import get_logger
from app.repositories.abstract.run import AbstractRunRepository
from app.repositories.memory.storage import MemoryStorage

logger = get_logger(__name__)


class MemoryRunRepository(AbstractRunRepository):
    """Memory implementation of run repository."""

    def __init__(self, storage: MemoryStorage):
        self.storage = storage

    async def get_runs_by_group(self, group_id: UUID) -> list[Run]:
        return [run for run in self.storage.runs.values() if run.group_id == group_id]

    async def get_completed_cancelled_runs_by_group(
        self, group_id: UUID, limit: int = 10, offset: int = 0
    ) -> list[Run]:
        """Get completed and cancelled runs for a group (paginated)."""
        runs = [
            run
            for run in self.storage.runs.values()
            if run.group_id == group_id and run.state in (RunState.COMPLETED, RunState.CANCELLED)
        ]

        async def get_timestamp(run):
            if run.state == RunState.COMPLETED and run.completed_at:
                return run.completed_at
            elif run.state == RunState.CANCELLED and run.cancelled_at:
                return run.cancelled_at
            return datetime.min.replace(tzinfo=UTC)

        runs.sort(key=get_timestamp, reverse=True)
        return runs[offset : offset + limit]

    async def get_run_by_id(self, run_id: UUID) -> Run | None:
        return self.storage.runs.get(run_id)

    async def create_run(
        self, group_id: UUID, store_id: UUID, leader_id: UUID, comment: str | None = None
    ) -> Run:
        run = Run(
            id=uuid4(),
            group_id=group_id,
            store_id=store_id,
            state=RunState.PLANNING,
            comment=comment,
        )
        run.planning_at = datetime.now()
        self.storage.runs[run.id] = run
        # Create participation for the leader
        self._create_participation_helper(leader_id, run.id, is_leader=True)
        return run

    async def update_run_comment(self, run_id: UUID, comment: str | None) -> Run | None:
        """Update the comment for a run."""
        run = self.storage.runs.get(run_id)
        if run:
            run.comment = comment
            return run
        return None

    async def get_participation(self, user_id: UUID, run_id: UUID) -> RunParticipation | None:
        for participation in self.storage.participations.values():
            if participation.user_id == user_id and participation.run_id == run_id:
                participation.user = self.storage.users.get(user_id)
                participation.run = self.storage.runs.get(run_id)
                return participation
        return None

    async def get_run_participations(self, run_id: UUID) -> list[RunParticipation]:
        participations = []
        for participation in self.storage.participations.values():
            if participation.run_id == run_id:
                participation.user = self.storage.users.get(participation.user_id)
                participation.run = self.storage.runs.get(run_id)
                participations.append(participation)
        return participations

    async def get_run_participations_with_users(self, run_id: UUID) -> list[RunParticipation]:
        """Get participations with user data eagerly loaded to avoid N+1 queries."""
        participations = []
        for participation in self.storage.participations.values():
            if participation.run_id == run_id:
                participation.user = self.storage.users.get(participation.user_id)
                participation.run = self.storage.runs.get(run_id)
                participations.append(participation)
        return participations

    async def create_participation(
        self, user_id: UUID, run_id: UUID, is_leader: bool = False, is_helper: bool = False
    ) -> RunParticipation:
        participation = RunParticipation(
            id=uuid4(),
            user_id=user_id,
            run_id=run_id,
            is_leader=is_leader,
            is_helper=is_helper,
            is_ready=False,
            is_removed=False,
        )
        participation.user = self.storage.users.get(user_id)
        participation.run = self.storage.runs.get(run_id)
        self.storage.participations[participation.id] = participation
        return participation

    async def update_participation_ready(
        self, participation_id: UUID, is_ready: bool
    ) -> RunParticipation | None:
        participation = self.storage.participations.get(participation_id)
        if participation:
            participation.is_ready = is_ready
            return participation
        return None

    async def update_participation_helper(
        self, user_id: UUID, run_id: UUID, is_helper: bool
    ) -> RunParticipation | None:
        """Update the helper status of a participation."""
        for participation in self.storage.participations.values():
            if participation.user_id == user_id and participation.run_id == run_id:
                participation.is_helper = is_helper
                return participation
        return None

    async def update_run_state(self, run_id: UUID, new_state: str) -> Run | None:
        run = self.storage.runs.get(run_id)
        if run:
            current_state = RunState(run.state)
            target_state = RunState(new_state)

            state_machine.validate_transition(current_state, target_state, str(run_id))

            run.state = new_state

            timestamp_field = f'{new_state}_at'
            setattr(run, timestamp_field, datetime.now())

            logger.info(
                'Run state transitioned',
                extra={
                    'run_id': str(run_id),
                    'from_state': str(current_state),
                    'to_state': str(target_state),
                },
            )

            return run
        return None

    async def _create_participation_helper(
        self, user_id: UUID, run_id: UUID, is_leader: bool = False, is_ready: bool = False
    ) -> RunParticipation:
        """Helper for creating participation."""
        participation = RunParticipation(
            id=uuid4(),
            user_id=user_id,
            run_id=run_id,
            is_leader=is_leader,
            is_helper=False,
            is_ready=is_ready,
            is_removed=False,
        )
        participation.user = self.storage.users.get(user_id)
        participation.run = self.storage.runs.get(run_id)
        self.storage.participations[participation.id] = participation
        return participation
