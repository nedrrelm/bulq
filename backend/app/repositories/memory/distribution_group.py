"""Memory distribution group repository implementation."""

from uuid import UUID, uuid4

from app.core.models import DistributionGroup
from app.repositories.abstract.distribution_group import AbstractDistributionGroupRepository
from app.repositories.memory.storage import MemoryStorage


class MemoryDistributionGroupRepository(AbstractDistributionGroupRepository):
    """Memory implementation of distribution group repository."""

    def __init__(self, storage: MemoryStorage):
        self.storage = storage

    async def get_groups_by_run(self, run_id: UUID) -> list[DistributionGroup]:
        """Get all distribution groups for a run, ordered by sort_order."""
        groups = [g for g in self.storage.distribution_groups.values() if g.run_id == run_id]
        groups.sort(key=lambda g: g.sort_order)
        return groups

    async def get_group_by_id(self, group_id: UUID) -> DistributionGroup | None:
        """Get a distribution group by its ID."""
        return self.storage.distribution_groups.get(group_id)

    async def get_default_group(self, run_id: UUID) -> DistributionGroup | None:
        """Get the default distribution group for a run."""
        for g in self.storage.distribution_groups.values():
            if g.run_id == run_id and g.is_default:
                return g
        return None

    async def create_group(
        self, run_id: UUID, name: str, is_default: bool = False, sort_order: int = 0
    ) -> DistributionGroup:
        """Create a new distribution group."""
        group = DistributionGroup(
            id=uuid4(),
            run_id=run_id,
            name=name,
            is_default=is_default,
            is_done=False,
            sort_order=sort_order,
        )
        self.storage.distribution_groups[group.id] = group
        return group

    async def delete_group(self, group_id: UUID) -> bool:
        """Delete a distribution group."""
        if group_id in self.storage.distribution_groups:
            del self.storage.distribution_groups[group_id]
            return True
        return False

    async def mark_group_done(
        self, group_id: UUID, is_done: bool = True
    ) -> DistributionGroup | None:
        """Mark a distribution group as done or not done."""
        group = self.storage.distribution_groups.get(group_id)
        if group:
            group.is_done = is_done
            return group
        return None

    async def assign_participation_to_group(self, participation_id: UUID, group_id: UUID) -> None:
        """Assign a participation to a distribution group."""
        participation = self.storage.participations.get(participation_id)
        if participation:
            participation.distribution_group_id = group_id
            participation.distribution_group = self.storage.distribution_groups.get(group_id)

    async def commit_changes(self) -> None:
        """Commit any pending changes (no-op for in-memory repository)."""
        pass
