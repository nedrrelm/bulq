"""Integration tests for DatabaseDistributionGroupRepository."""

from uuid import uuid4

import pytest

from app.repositories.database.distribution_group import DatabaseDistributionGroupRepository

pytestmark = pytest.mark.integration


@pytest.fixture
def dist_group_repo(db_session):
    return DatabaseDistributionGroupRepository(db_session)


class TestCreateGroup:
    async def test_creates_group(self, dist_group_repo, create_run):
        run, leader = await create_run()
        group = await dist_group_repo.create_group(
            run_id=run.id, name='1', is_default=True, sort_order=0
        )

        assert group.id is not None
        assert group.run_id == run.id
        assert group.name == '1'
        assert group.is_default is True
        assert group.is_done is False
        assert group.sort_order == 0

    async def test_creates_with_defaults(self, dist_group_repo, create_run):
        run, leader = await create_run()
        group = await dist_group_repo.create_group(
            run_id=run.id, name='2', is_default=False, sort_order=1
        )

        assert group.is_default is False
        assert group.is_done is False


class TestGetGroupsByRun:
    async def test_returns_groups_ordered_by_sort_order(self, dist_group_repo, create_run):
        run, leader = await create_run()
        g2 = await dist_group_repo.create_group(run.id, '2', sort_order=1)
        g1 = await dist_group_repo.create_group(run.id, '1', is_default=True, sort_order=0)

        groups = await dist_group_repo.get_groups_by_run(run.id)

        assert len(groups) == 2
        assert groups[0].id == g1.id
        assert groups[1].id == g2.id

    async def test_returns_empty_for_run_with_no_groups(self, dist_group_repo, create_run):
        run, leader = await create_run()
        groups = await dist_group_repo.get_groups_by_run(run.id)
        assert groups == []


class TestGetGroupById:
    async def test_returns_group_when_found(self, dist_group_repo, create_run):
        run, leader = await create_run()
        created = await dist_group_repo.create_group(run.id, '1', is_default=True)

        found = await dist_group_repo.get_group_by_id(created.id)

        assert found is not None
        assert found.id == created.id
        assert found.name == '1'

    async def test_returns_none_when_not_found(self, dist_group_repo):
        result = await dist_group_repo.get_group_by_id(uuid4())
        assert result is None


class TestGetDefaultGroup:
    async def test_returns_default_group(self, dist_group_repo, create_run):
        run, leader = await create_run()
        default = await dist_group_repo.create_group(run.id, '1', is_default=True)
        await dist_group_repo.create_group(run.id, '2', is_default=False, sort_order=1)

        result = await dist_group_repo.get_default_group(run.id)

        assert result is not None
        assert result.id == default.id
        assert result.is_default is True

    async def test_returns_none_when_no_default(self, dist_group_repo, create_run):
        run, leader = await create_run()
        await dist_group_repo.create_group(run.id, '1', is_default=False)

        result = await dist_group_repo.get_default_group(run.id)
        assert result is None


class TestDeleteGroup:
    async def test_deletes_existing_group(self, dist_group_repo, create_run):
        run, leader = await create_run()
        group = await dist_group_repo.create_group(run.id, '1')

        result = await dist_group_repo.delete_group(group.id)

        assert result is True
        assert await dist_group_repo.get_group_by_id(group.id) is None

    async def test_returns_false_for_nonexistent(self, dist_group_repo):
        result = await dist_group_repo.delete_group(uuid4())
        assert result is False


class TestMarkGroupDone:
    async def test_marks_group_as_done(self, dist_group_repo, create_run):
        run, leader = await create_run()
        group = await dist_group_repo.create_group(run.id, '1')
        assert group.is_done is False

        updated = await dist_group_repo.mark_group_done(group.id, is_done=True)

        assert updated is not None
        assert updated.is_done is True

    async def test_returns_none_for_nonexistent(self, dist_group_repo):
        result = await dist_group_repo.mark_group_done(uuid4())
        assert result is None


class TestAssignParticipationToGroup:
    async def test_assigns_participation(
        self, dist_group_repo, create_run, create_participation, create_user
    ):
        run, leader = await create_run()
        user = await create_user()
        participation = await create_participation(user, run)
        group = await dist_group_repo.create_group(run.id, '1', is_default=True)

        await dist_group_repo.assign_participation_to_group(participation.id, group.id)

        # Verify by fetching groups for run and checking participation
        from sqlalchemy import select

        from app.core.models import RunParticipation

        result = await dist_group_repo.db.execute(
            select(RunParticipation).where(RunParticipation.id == participation.id)
        )
        updated = result.scalar_one()
        assert updated.distribution_group_id == group.id
