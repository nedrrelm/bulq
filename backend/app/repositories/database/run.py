"""Database run repository implementation."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import case, desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.models import Run, RunParticipation
from app.core.run_state import RunState, state_machine
from app.infrastructure.request_context import get_logger
from app.repositories.abstract.run import AbstractRunRepository

logger = get_logger(__name__)


class DatabaseRunRepository(AbstractRunRepository):
    """Database implementation of run repository."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_runs_by_group(self, group_id: UUID) -> list[Run]:
        """Get all runs for a group."""
        result = await self.db.execute(select(Run).filter(Run.group_id == group_id))
        return list(result.scalars().all())

    async def get_completed_cancelled_runs_by_group(
        self, group_id: UUID, limit: int = 10, offset: int = 0
    ) -> list[Run]:
        """Get completed and cancelled runs for a group (paginated)."""
        # Query runs that are completed or cancelled
        query = select(Run).filter(
            Run.group_id == group_id, Run.state.in_([RunState.COMPLETED, RunState.CANCELLED])
        )

        # Order by the appropriate timestamp (completed_at or cancelled_at), most recent first
        query = query.order_by(
            desc(
                case(
                    (Run.state == RunState.COMPLETED, Run.completed_at),
                    (Run.state == RunState.CANCELLED, Run.cancelled_at),
                    else_=None,
                )
            )
        )

        result = await self.db.execute(query.limit(limit).offset(offset))
        return list(result.scalars().all())

    async def get_run_by_id(self, run_id: UUID) -> Run | None:
        """Get run by ID."""
        result = await self.db.execute(select(Run).filter(Run.id == run_id))
        return result.scalar_one_or_none()

    async def create_run(
        self, group_id: UUID, store_id: UUID, leader_id: UUID, comment: str | None = None
    ) -> Run:
        """Create a new run with the leader as first participant."""
        run = Run(group_id=group_id, store_id=store_id, state=RunState.PLANNING, comment=comment)
        self.db.add(run)
        await self.db.flush()  # Get the run ID without committing

        # Create participation for the leader
        participation = RunParticipation(
            user_id=leader_id, run_id=run.id, is_leader=True, is_removed=False
        )
        self.db.add(participation)
        await self.db.commit()
        await self.db.refresh(run)
        return run

    async def update_run_comment(self, run_id: UUID, comment: str | None) -> Run | None:
        """Update the comment for a run."""
        result = await self.db.execute(select(Run).filter(Run.id == run_id))
        run = result.scalar_one_or_none()
        if run:
            run.comment = comment
            await self.db.commit()
            await self.db.refresh(run)
            return run
        return None

    async def get_participation(self, user_id: UUID, run_id: UUID) -> RunParticipation | None:
        """Get a user's participation in a run."""
        result = await self.db.execute(
            select(RunParticipation).filter(
                RunParticipation.user_id == user_id, RunParticipation.run_id == run_id
            )
        )
        return result.scalar_one_or_none()

    async def get_run_participations(self, run_id: UUID) -> list[RunParticipation]:
        """Get all participations for a run."""
        result = await self.db.execute(
            select(RunParticipation).filter(RunParticipation.run_id == run_id)
        )
        return list(result.scalars().all())

    async def get_run_participations_with_users(self, run_id: UUID) -> list[RunParticipation]:
        """Get all participations for a run with user data eagerly loaded."""
        result = await self.db.execute(
            select(RunParticipation)
            .filter(RunParticipation.run_id == run_id)
            .options(selectinload(RunParticipation.user))
        )
        return list(result.unique().scalars().all())

    async def create_participation(
        self, user_id: UUID, run_id: UUID, is_leader: bool = False, is_helper: bool = False
    ) -> RunParticipation:
        """Create a participation record for a user in a run."""
        participation = RunParticipation(
            user_id=user_id,
            run_id=run_id,
            is_leader=is_leader,
            is_helper=is_helper,
            is_removed=False,
        )
        self.db.add(participation)
        await self.db.commit()
        await self.db.refresh(participation)
        return participation

    async def update_participation_ready(
        self, participation_id: UUID, is_ready: bool
    ) -> RunParticipation | None:
        """Update the ready status of a participation."""
        result = await self.db.execute(
            select(RunParticipation).filter(RunParticipation.id == participation_id)
        )
        participation = result.scalar_one_or_none()
        if participation:
            participation.is_ready = is_ready
            await self.db.commit()
            await self.db.refresh(participation)
            return participation
        return None

    async def update_participation_helper(
        self, user_id: UUID, run_id: UUID, is_helper: bool
    ) -> RunParticipation | None:
        """Update the helper status of a participation."""
        result = await self.db.execute(
            select(RunParticipation).filter(
                RunParticipation.user_id == user_id, RunParticipation.run_id == run_id
            )
        )
        participation = result.scalar_one_or_none()
        if participation:
            participation.is_helper = is_helper
            await self.db.commit()
            await self.db.refresh(participation)
            return participation
        return None

    async def update_run_state(self, run_id: UUID, new_state: str) -> Run | None:
        """Update the state of a run."""
        result = await self.db.execute(select(Run).filter(Run.id == run_id))
        run = result.scalar_one_or_none()
        if run:
            # Convert string states to RunState enum
            current_state = RunState(run.state)
            target_state = RunState(new_state)

            # Validate transition using state machine
            state_machine.validate_transition(current_state, target_state, str(run_id))

            # Update state
            run.state = new_state

            # Set the timestamp for the new state
            timestamp_field = f'{new_state}_at'
            setattr(run, timestamp_field, datetime.now())

            await self.db.commit()
            await self.db.refresh(run)

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
