"""Database run repository implementation."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import case, desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

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
        """Get all runs for a group with store eagerly loaded."""
        result = await self.db.execute(
            select(Run).where(Run.group_id == group_id).options(joinedload(Run.store))
        )
        return list(result.scalars().all())

    async def get_completed_cancelled_runs_by_group(
        self, group_id: UUID, limit: int = 10, offset: int = 0
    ) -> list[Run]:
        """Get completed and cancelled runs for a group (paginated) with store eagerly loaded."""
        result = await self.db.execute(
            select(Run)
            .where(
                Run.group_id == group_id,
                Run.state.in_([RunState.COMPLETED, RunState.CANCELLED]),
            )
            .order_by(
                desc(
                    case(
                        (Run.state == RunState.COMPLETED, Run.completed_at),
                        (Run.state == RunState.CANCELLED, Run.cancelled_at),
                        else_=None,
                    )
                )
            )
            .options(joinedload(Run.store))
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_run_by_id(self, run_id: UUID) -> Run | None:
        """Get run by ID."""
        result = await self.db.execute(select(Run).where(Run.id == run_id))
        return result.scalar_one_or_none()

    async def create_run(
        self,
        group_id: UUID,
        store_id: UUID,
        leader_id: UUID,
        comment: str | None = None,
        leader_fee: float | None = None,
        sale_id: UUID | None = None,
    ) -> Run:
        """Create a new run with the leader as first participant."""
        run = Run(
            group_id=group_id,
            store_id=store_id,
            sale_id=sale_id,
            state=RunState.PLANNING,
            comment=comment,
            leader_fee=leader_fee,
        )
        self.db.add(run)
        await self.db.flush()

        participation = RunParticipation(
            user_id=leader_id, run_id=run.id, is_leader=True, is_removed=False
        )
        self.db.add(participation)
        await self.db.commit()
        await self.db.refresh(run)
        return run

    async def update_run_comment(self, run_id: UUID, comment: str | None) -> Run | None:
        """Update the comment for a run."""
        result = await self.db.execute(select(Run).where(Run.id == run_id))
        run = result.scalar_one_or_none()
        if run:
            run.comment = comment
            await self.db.commit()
            await self.db.refresh(run)
            return run
        return None

    async def update_leader_fee(self, run_id: UUID, leader_fee: float | None) -> Run | None:
        """Update the leader fee for a run."""
        result = await self.db.execute(select(Run).where(Run.id == run_id))
        run = result.scalar_one_or_none()
        if run:
            run.leader_fee = leader_fee
            await self.db.commit()
            await self.db.refresh(run)
            return run
        return None

    async def get_participation(self, user_id: UUID, run_id: UUID) -> RunParticipation | None:
        """Get a user's participation in a run."""
        result = await self.db.execute(
            select(RunParticipation).where(
                RunParticipation.user_id == user_id, RunParticipation.run_id == run_id
            )
        )
        return result.scalar_one_or_none()

    async def get_run_participations(self, run_id: UUID) -> list[RunParticipation]:
        """Get all participations for a run."""
        result = await self.db.execute(
            select(RunParticipation).where(RunParticipation.run_id == run_id)
        )
        return list(result.scalars().all())

    async def get_run_participations_with_users(self, run_id: UUID) -> list[RunParticipation]:
        """Get all participations for a run with user data eagerly loaded."""
        result = await self.db.execute(
            select(RunParticipation)
            .where(RunParticipation.run_id == run_id)
            .options(joinedload(RunParticipation.user))
        )
        return list(result.scalars().all())

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
            select(RunParticipation).where(RunParticipation.id == participation_id)
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
            select(RunParticipation).where(
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
        result = await self.db.execute(select(Run).where(Run.id == run_id))
        run = result.scalar_one_or_none()
        if run:
            current_state = RunState(run.state)
            target_state = RunState(new_state)

            is_sale_run = run.sale_id is not None
            state_machine.validate_transition(current_state, target_state, str(run_id), is_sale_run)

            run.state = new_state

            timestamp_field = f'{new_state}_at'
            setattr(run, timestamp_field, datetime.now(UTC))

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
