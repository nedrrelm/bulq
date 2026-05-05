"""Integration tests for DatabaseNotificationRepository."""

import uuid

import pytest

from app.repositories.database.notification import DatabaseNotificationRepository

pytestmark = pytest.mark.integration


@pytest.fixture
def repo(db_session):
    return DatabaseNotificationRepository(db=db_session)


@pytest.fixture
async def user(create_user):
    return await create_user()


class TestCreateNotification:
    async def test_creates_notification_with_data(self, repo, user):
        data = {'run_id': str(uuid.uuid4()), 'store_name': 'TestMart'}
        notification = await repo.create_notification(user.id, 'run_state_changed', data)

        assert notification.id is not None
        assert notification.user_id == user.id
        assert notification.type == 'run_state_changed'
        assert notification.data == data
        assert notification.read is False
        assert notification.created_at is not None


class TestGetUserNotifications:
    async def test_returns_notifications_newest_first(self, repo, user, db_session):
        from datetime import UTC, datetime

        n1 = await repo.create_notification(user.id, 'type_a', {'order': 1})
        n1.created_at = datetime(2024, 1, 1, tzinfo=UTC)
        n2 = await repo.create_notification(user.id, 'type_b', {'order': 2})
        n2.created_at = datetime(2024, 1, 2, tzinfo=UTC)
        n3 = await repo.create_notification(user.id, 'type_c', {'order': 3})
        n3.created_at = datetime(2024, 1, 3, tzinfo=UTC)
        await db_session.flush()

        results = await repo.get_user_notifications(user.id)
        assert len(results) == 3
        # Newest first
        assert results[0].type == 'type_c'
        assert results[2].type == 'type_a'

    async def test_pagination_with_limit_and_offset(self, repo, user):
        for i in range(5):
            await repo.create_notification(user.id, f'type_{i}', {'i': i})

        page1 = await repo.get_user_notifications(user.id, limit=2, offset=0)
        page2 = await repo.get_user_notifications(user.id, limit=2, offset=2)

        assert len(page1) == 2
        assert len(page2) == 2
        assert page1[0].id != page2[0].id

    async def test_returns_empty_for_user_with_no_notifications(self, repo):
        results = await repo.get_user_notifications(uuid.uuid4())
        assert results == []


class TestGetUnreadNotifications:
    async def test_returns_only_unread(self, repo, user):
        n1 = await repo.create_notification(user.id, 'type_a', {})
        await repo.create_notification(user.id, 'type_b', {})
        await repo.mark_notification_as_read(n1.id)

        unread = await repo.get_unread_notifications(user.id)
        assert len(unread) == 1
        assert unread[0].type == 'type_b'

    async def test_returns_empty_when_all_read(self, repo, user):
        n = await repo.create_notification(user.id, 'type_a', {})
        await repo.mark_notification_as_read(n.id)

        assert await repo.get_unread_notifications(user.id) == []


class TestGetUnreadCount:
    async def test_counts_unread(self, repo, user):
        await repo.create_notification(user.id, 'a', {})
        await repo.create_notification(user.id, 'b', {})
        n3 = await repo.create_notification(user.id, 'c', {})
        await repo.mark_notification_as_read(n3.id)

        assert await repo.get_unread_count(user.id) == 2

    async def test_returns_zero_when_none(self, repo, user):
        assert await repo.get_unread_count(user.id) == 0


class TestMarkNotificationAsRead:
    async def test_marks_as_read(self, repo, user):
        n = await repo.create_notification(user.id, 'type_a', {})
        result = await repo.mark_notification_as_read(n.id)

        assert result is True
        fetched = await repo.get_notification_by_id(n.id)
        assert fetched.read is True

    async def test_returns_false_for_nonexistent(self, repo):
        result = await repo.mark_notification_as_read(uuid.uuid4())
        assert result is False


class TestMarkAllNotificationsAsRead:
    async def test_marks_all_unread(self, repo, user):
        await repo.create_notification(user.id, 'a', {})
        await repo.create_notification(user.id, 'b', {})
        await repo.create_notification(user.id, 'c', {})

        count = await repo.mark_all_notifications_as_read(user.id)

        assert count == 3
        assert await repo.get_unread_count(user.id) == 0

    async def test_returns_zero_when_none_unread(self, repo, user):
        n = await repo.create_notification(user.id, 'a', {})
        await repo.mark_notification_as_read(n.id)

        count = await repo.mark_all_notifications_as_read(user.id)
        assert count == 0


class TestGetNotificationById:
    async def test_returns_notification_when_found(self, repo, user):
        n = await repo.create_notification(user.id, 'type_x', {'key': 'val'})

        found = await repo.get_notification_by_id(n.id)
        assert found is not None
        assert found.id == n.id
        assert found.type == 'type_x'

    async def test_returns_none_when_not_found(self, repo):
        assert await repo.get_notification_by_id(uuid.uuid4()) is None
