"""Abstract distribution group repository interface."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.core.models import DistributionGroup


class AbstractDistributionGroupRepository(ABC):
    """Abstract base class for distribution group repository operations."""

    @abstractmethod
    async def get_groups_by_run(self, run_id: UUID) -> list[DistributionGroup]:
        """Get all distribution groups for a run, ordered by sort_order."""
        raise NotImplementedError

    @abstractmethod
    async def get_group_by_id(self, group_id: UUID) -> DistributionGroup | None:
        """Get a distribution group by its ID."""
        raise NotImplementedError

    @abstractmethod
    async def get_default_group(self, run_id: UUID) -> DistributionGroup | None:
        """Get the default distribution group for a run."""
        raise NotImplementedError

    @abstractmethod
    async def create_group(
        self, run_id: UUID, name: str, is_default: bool = False, sort_order: int = 0
    ) -> DistributionGroup:
        """Create a new distribution group."""
        raise NotImplementedError

    @abstractmethod
    async def delete_group(self, group_id: UUID) -> bool:
        """Delete a distribution group."""
        raise NotImplementedError

    @abstractmethod
    async def mark_group_done(
        self, group_id: UUID, is_done: bool = True
    ) -> DistributionGroup | None:
        """Mark a distribution group as done or not done."""
        raise NotImplementedError

    @abstractmethod
    async def assign_participation_to_group(self, participation_id: UUID, group_id: UUID) -> None:
        """Assign a participation to a distribution group."""
        raise NotImplementedError

    @abstractmethod
    async def commit_changes(self) -> None:
        """Commit any pending changes."""
        raise NotImplementedError
