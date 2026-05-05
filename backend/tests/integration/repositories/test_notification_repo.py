"""Integration tests for DatabaseNotificationRepository."""

import uuid

import pytest

from app.repositories.database.notification import DatabaseNotificationRepository

pytestmark = pytest.mark.integration


@pytest.fixture
def repo(db_session):
    return DatabaseNotificationRepository(db=db_session)


@pytest.fixture
def user(create_user):
    return create_user()


class TestCreateNotification:
    def test_creates_notification_with_data(self, repo, user):
        data = {'run_id': str(uuid.uuid4()), 'store_name': 'TestMart'}
        notification = repo.create_notification(user.id, 'run_state_changed', data)

        assert notification.id is not None
        assert notification.user_id == user.id
        assert notification.type == 'run_state_changed'
        assert notification.data == data
        assert notification.read is False
        assert notification.created_at is not None


class TestGetUserNotifications:
    def test_returns_notifications_newest_first(self, repo, user, db_session):
        from datetime import UTC, datetime

        n1 = repo.create_notification(user.id, 'type_a', {'order': 1})
        n1.created_at = datetime(2024, 1, 1, tzinfo=UTC)
        n2 = repo.create_notification(user.id, 'type_b', {'order': 2})
        n2.created_at = datetime(2024, 1, 2, tzinfo=UTC)
        n3 = repo.create_notification(user.id, 'type_c', {'order': 3})
        n3.created_at = datetime(2024, 1, 3, tzinfo=UTC)
        db_session.flush()

        results = repo.get_user_notifications(user.id)
        assert len(results) == 3
        # Newest first
        assert results[0].type == 'type_c'
        assert results[2].type == 'type_a'

    def test_pagination_with_limit_and_offset(self, repo, user):
        for i in range(5):
            repo.create_notification(user.id, f'type_{i}', {'i': i})

        page1 = repo.get_user_notifications(user.id, limit=2, offset=0)
        page2 = repo.get_user_notifications(user.id, limit=2, offset=2)

        assert len(page1) == 2
        assert len(page2) == 2
        assert page1[0].id != page2[0].id

    def test_returns_empty_for_user_with_no_notifications(self, repo):
        results = repo.get_user_notifications(uuid.uuid4())
        assert results == []


class TestGetUnreadNotifications:
    def test_returns_only_unread(self, repo, user):
        n1 = repo.create_notification(user.id, 'type_a', {})
        repo.create_notification(user.id, 'type_b', {})
        repo.mark_notification_as_read(n1.id)

        unread = repo.get_unread_notifications(user.id)
        assert len(unread) == 1
        assert unread[0].type == 'type_b'

    def test_returns_empty_when_all_read(self, repo, user):
        n = repo.create_notification(user.id, 'type_a', {})
        repo.mark_notification_as_read(n.id)

        assert repo.get_unread_notifications(user.id) == []


class TestGetUnreadCount:
    def test_counts_unread(self, repo, user):
        repo.create_notification(user.id, 'a', {})
        repo.create_notification(user.id, 'b', {})
        n3 = repo.create_notification(user.id, 'c', {})
        repo.mark_notification_as_read(n3.id)

        assert repo.get_unread_count(user.id) == 2

    def test_returns_zero_when_none(self, repo, user):
        assert repo.get_unread_count(user.id) == 0


class TestMarkNotificationAsRead:
    def test_marks_as_read(self, repo, user):
        n = repo.create_notification(user.id, 'type_a', {})
        result = repo.mark_notification_as_read(n.id)

        assert result is True
        fetched = repo.get_notification_by_id(n.id)
        assert fetched.read is True

    def test_returns_false_for_nonexistent(self, repo):
        result = repo.mark_notification_as_read(uuid.uuid4())
        assert result is False


class TestMarkAllNotificationsAsRead:
    def test_marks_all_unread(self, repo, user):
        repo.create_notification(user.id, 'a', {})
        repo.create_notification(user.id, 'b', {})
        repo.create_notification(user.id, 'c', {})

        count = repo.mark_all_notifications_as_read(user.id)

        assert count == 3
        assert repo.get_unread_count(user.id) == 0

    def test_returns_zero_when_none_unread(self, repo, user):
        n = repo.create_notification(user.id, 'a', {})
        repo.mark_notification_as_read(n.id)

        count = repo.mark_all_notifications_as_read(user.id)
        assert count == 0


class TestGetNotificationById:
    def test_returns_notification_when_found(self, repo, user):
        n = repo.create_notification(user.id, 'type_x', {'key': 'val'})

        found = repo.get_notification_by_id(n.id)
        assert found is not None
        assert found.id == n.id
        assert found.type == 'type_x'

    def test_returns_none_when_not_found(self, repo):
        assert repo.get_notification_by_id(uuid.uuid4()) is None
