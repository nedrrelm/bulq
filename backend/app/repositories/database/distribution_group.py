"""Database distribution group repository implementation."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import DistributionGroup, RunParticipation
from app.repositories.abstract.distribution_group import AbstractDistributionGroupRepository


class DatabaseDistributionGroupRepository(AbstractDistributionGroupRepository):
    """Database implementation of distribution group repository."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_groups_by_run(self, run_id: UUID) -> list[DistributionGroup]:
        """Get all distribution groups for a run, ordered by sort_order."""
        result = await self.db.execute(
            select(DistributionGroup)
            .where(DistributionGroup.run_id == run_id)
            .order_by(DistributionGroup.sort_order)
        )
        return list(result.scalars().all())

    async def get_group_by_id(self, group_id: UUID) -> DistributionGroup | None:
        """Get a distribution group by its ID."""
        result = await self.db.execute(
            select(DistributionGroup).where(DistributionGroup.id == group_id)
        )
        return result.scalar_one_or_none()

    async def get_default_group(self, run_id: UUID) -> DistributionGroup | None:
        """Get the default distribution group for a run."""
        result = await self.db.execute(
            select(DistributionGroup).where(
                DistributionGroup.run_id == run_id, DistributionGroup.is_default.is_(True)
            )
        )
        return result.scalar_one_or_none()

    async def create_group(
        self, run_id: UUID, name: str, is_default: bool = False, sort_order: int = 0
    ) -> DistributionGroup:
        """Create a new distribution group."""
        group = DistributionGroup(
            run_id=run_id, name=name, is_default=is_default, sort_order=sort_order
        )
        self.db.add(group)
        await self.db.commit()
        await self.db.refresh(group)
        return group

    async def delete_group(self, group_id: UUID) -> bool:
        """Delete a distribution group."""
        result = await self.db.execute(
            select(DistributionGroup).where(DistributionGroup.id == group_id)
        )
        group = result.scalar_one_or_none()
        if group:
            await self.db.delete(group)
            await self.db.commit()
            return True
        return False

    async def mark_group_done(
        self, group_id: UUID, is_done: bool = True
    ) -> DistributionGroup | None:
        """Mark a distribution group as done or not done."""
        result = await self.db.execute(
            select(DistributionGroup).where(DistributionGroup.id == group_id)
        )
        group = result.scalar_one_or_none()
        if group:
            group.is_done = is_done
            await self.db.commit()
            await self.db.refresh(group)
            return group
        return None

    async def assign_participation_to_group(self, participation_id: UUID, group_id: UUID) -> None:
        """Assign a participation to a distribution group."""
        result = await self.db.execute(
            select(RunParticipation).where(RunParticipation.id == participation_id)
        )
        participation = result.scalar_one_or_none()
        if participation:
            participation.distribution_group_id = group_id
            await self.db.commit()

    async def commit_changes(self) -> None:
        """Commit any pending changes."""
        await self.db.commit()
