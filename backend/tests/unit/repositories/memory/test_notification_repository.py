"""Unit tests for MemoryNotificationRepository.

Tests cover:
- Notification creation (create_notification)
- Notification retrieval by ID (get_notification_by_id)
- User notifications retrieval (get_user_notifications)
- Unread notifications retrieval (get_unread_notifications)
- Unread count (get_unread_count)
- Mark notification as read (mark_notification_as_read)
- Mark all notifications as read (mark_all_notifications_as_read)
- Pagination and sorting
- Edge cases and data integrity
"""

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.repositories.memory.notification import MemoryNotificationRepository
from app.repositories.memory.storage import MemoryStorage


@pytest.fixture
def storage():
    """Create fresh memory storage for each test."""
    storage = MemoryStorage()
    storage.notifications.clear()
    yield storage
    storage.notifications.clear()


@pytest.fixture
def repo(storage):
    """Create repository instance with fresh storage."""
    return MemoryNotificationRepository(storage)


@pytest.fixture
def sample_user_ids():
    """Sample user IDs for testing."""
    return {
        'user1': uuid4(),
        'user2': uuid4(),
        'user3': uuid4(),
    }


@pytest.fixture
def sample_notification_data():
    """Sample notification data for testing."""
    return {
        'type': 'run_state_changed',
        'data': {
            'run_id': str(uuid4()),
            'store_name': 'Costco',
            'old_state': 'active',
            'new_state': 'closed',
        },
    }


class TestCreateNotification:
    """Test create_notification() method."""

    def test_create_notification_with_required_fields(
        self, repo, sample_user_ids, sample_notification_data
    ):
        """Test creating notification with required fields."""
        user_id = sample_user_ids['user1']
        notification = repo.create_notification(
            user_id=user_id,
            type=sample_notification_data['type'],
            data=sample_notification_data['data'],
        )

        assert notification is not None
        assert notification.user_id == user_id
        assert notification.type == sample_notification_data['type']
        assert notification.data == sample_notification_data['data']

    def test_created_notification_has_uuid(self, repo, sample_user_ids, sample_notification_data):
        """Test created notification has UUID."""
        user_id = sample_user_ids['user1']
        notification = repo.create_notification(
            user_id=user_id,
            type=sample_notification_data['type'],
            data=sample_notification_data['data'],
        )

        assert notification.id is not None
        assert isinstance(notification.id, UUID)

    def test_created_notification_has_default_read_false(
        self, repo, sample_user_ids, sample_notification_data
    ):
        """Test created notification has default read=False."""
        user_id = sample_user_ids['user1']
        notification = repo.create_notification(
            user_id=user_id,
            type=sample_notification_data['type'],
            data=sample_notification_data['data'],
        )

        assert notification.read is False

    def test_created_notification_has_timestamp(
        self, repo, sample_user_ids, sample_notification_data
    ):
        """Test created notification has created_at timestamp."""
        user_id = sample_user_ids['user1']
        before = datetime.now(UTC)
        notification = repo.create_notification(
            user_id=user_id,
            type=sample_notification_data['type'],
            data=sample_notification_data['data'],
        )
        after = datetime.now(UTC)

        assert notification.created_at is not None
        assert before <= notification.created_at <= after

    def test_create_multiple_notifications_for_user(self, repo, sample_user_ids):
        """Test creating multiple notifications for same user."""
        user_id = sample_user_ids['user1']

        notif1 = repo.create_notification(
            user_id=user_id, type='run_created', data={'run_id': str(uuid4())}
        )
        notif2 = repo.create_notification(
            user_id=user_id, type='run_closed', data={'run_id': str(uuid4())}
        )

        assert notif1.id != notif2.id
        assert notif1.user_id == notif2.user_id == user_id

        # Both should be retrievable
        assert repo.get_notification_by_id(notif1.id) is not None
        assert repo.get_notification_by_id(notif2.id) is not None

    def test_create_different_notification_types(self, repo, sample_user_ids):
        """Test creating notifications with different types."""
        user_id = sample_user_ids['user1']

        types = [
            'run_state_changed',
            'run_created',
            'run_closed',
            'bid_placed',
            'new_participant',
        ]

        for notif_type in types:
            notification = repo.create_notification(
                user_id=user_id, type=notif_type, data={'info': 'test'}
            )
            assert notification.type == notif_type


class TestGetNotificationById:
    """Test get_notification_by_id() method."""

    def test_get_existing_notification(self, repo, sample_user_ids, sample_notification_data):
        """Test retrieving existing notification by ID."""
        user_id = sample_user_ids['user1']
        created = repo.create_notification(
            user_id=user_id,
            type=sample_notification_data['type'],
            data=sample_notification_data['data'],
        )

        retrieved = repo.get_notification_by_id(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.user_id == user_id
        assert retrieved.type == sample_notification_data['type']
        assert retrieved.data == sample_notification_data['data']

    def test_get_nonexistent_notification_returns_none(self, repo):
        """Test retrieving non-existent notification returns None."""
        nonexistent_id = uuid4()
        result = repo.get_notification_by_id(nonexistent_id)

        assert result is None

    def test_get_notification_includes_all_fields(self, repo, sample_user_ids):
        """Test retrieved notification includes all fields."""
        user_id = sample_user_ids['user1']
        data = {'key': 'value', 'nested': {'data': 'here'}}
        created = repo.create_notification(user_id=user_id, type='test_type', data=data)

        retrieved = repo.get_notification_by_id(created.id)

        assert retrieved.id == created.id
        assert retrieved.user_id == user_id
        assert retrieved.type == 'test_type'
        assert retrieved.data == data
        assert retrieved.read is False
        assert retrieved.created_at is not None

    def test_get_notification_with_different_read_status(self, repo, sample_user_ids):
        """Test retrieving notification after marking as read."""
        user_id = sample_user_ids['user1']
        created = repo.create_notification(user_id=user_id, type='test', data={})

        # Mark as read
        repo.mark_notification_as_read(created.id)

        retrieved = repo.get_notification_by_id(created.id)
        assert retrieved.read is True


class TestGetUserNotifications:
    """Test get_user_notifications() method."""

    def test_get_all_notifications_for_user(self, repo, sample_user_ids):
        """Test retrieving all notifications for a user."""
        user_id = sample_user_ids['user1']

        # Create 3 notifications
        notif1 = repo.create_notification(user_id=user_id, type='type1', data={'n': 1})
        notif2 = repo.create_notification(user_id=user_id, type='type2', data={'n': 2})
        notif3 = repo.create_notification(user_id=user_id, type='type3', data={'n': 3})

        notifications = repo.get_user_notifications(user_id)

        assert len(notifications) == 3
        notification_ids = {n.id for n in notifications}
        assert {notif1.id, notif2.id, notif3.id} == notification_ids

    def test_get_notifications_empty_for_user_with_none(self, repo, sample_user_ids):
        """Test getting notifications returns empty list for user with none."""
        user_id = sample_user_ids['user1']

        notifications = repo.get_user_notifications(user_id)

        assert notifications == []

    def test_get_notifications_multiple_users(self, repo, sample_user_ids):
        """Test notifications are isolated by user."""
        user1_id = sample_user_ids['user1']
        user2_id = sample_user_ids['user2']

        # Create notifications for both users
        notif1 = repo.create_notification(user_id=user1_id, type='test', data={})
        notif2 = repo.create_notification(user_id=user2_id, type='test', data={})
        notif3 = repo.create_notification(user_id=user1_id, type='test', data={})

        user1_notifications = repo.get_user_notifications(user1_id)
        user2_notifications = repo.get_user_notifications(user2_id)

        assert len(user1_notifications) == 2
        assert len(user2_notifications) == 1
        assert notif1.id in [n.id for n in user1_notifications]
        assert notif3.id in [n.id for n in user1_notifications]
        assert notif2.id in [n.id for n in user2_notifications]

    def test_get_notifications_sorted_by_created_at_newest_first(self, repo, sample_user_ids):
        """Test notifications are sorted by created_at (newest first)."""
        user_id = sample_user_ids['user1']

        # Create notifications with small time gaps
        notif1 = repo.create_notification(user_id=user_id, type='first', data={})
        notif2 = repo.create_notification(user_id=user_id, type='second', data={})
        notif3 = repo.create_notification(user_id=user_id, type='third', data={})

        notifications = repo.get_user_notifications(user_id)

        # Should be in reverse order (newest first)
        assert notifications[0].id == notif3.id
        assert notifications[1].id == notif2.id
        assert notifications[2].id == notif1.id

    def test_get_notifications_excludes_other_users(self, repo, sample_user_ids):
        """Test that getting notifications excludes other users' notifications."""
        user1_id = sample_user_ids['user1']
        user2_id = sample_user_ids['user2']
        user3_id = sample_user_ids['user3']

        # Create notifications for all users
        repo.create_notification(user_id=user1_id, type='test', data={})
        repo.create_notification(user_id=user2_id, type='test', data={})
        repo.create_notification(user_id=user3_id, type='test', data={})
        repo.create_notification(user_id=user1_id, type='test', data={})

        user1_notifications = repo.get_user_notifications(user1_id)

        # Should only have user1's notifications
        assert len(user1_notifications) == 2
        assert all(n.user_id == user1_id for n in user1_notifications)

    def test_get_notifications_pagination_limit(self, repo, sample_user_ids):
        """Test pagination with limit parameter."""
        user_id = sample_user_ids['user1']

        # Create 5 notifications
        for i in range(5):
            repo.create_notification(user_id=user_id, type=f'type{i}', data={'n': i})

        # Get only first 3
        notifications = repo.get_user_notifications(user_id, limit=3)

        assert len(notifications) == 3

    def test_get_notifications_pagination_offset(self, repo, sample_user_ids):
        """Test pagination with offset parameter."""
        user_id = sample_user_ids['user1']

        # Create 5 notifications
        notifs = []
        for i in range(5):
            notifs.append(repo.create_notification(user_id=user_id, type=f'type{i}', data={'n': i}))

        # Get with offset
        notifications = repo.get_user_notifications(user_id, limit=2, offset=2)

        assert len(notifications) == 2
        # Should get the 3rd and 4th (0-indexed: 2 and 3) newest notifications
        assert notifications[0].id == notifs[2].id
        assert notifications[1].id == notifs[1].id

    def test_get_notifications_pagination_limit_and_offset(self, repo, sample_user_ids):
        """Test pagination with both limit and offset."""
        user_id = sample_user_ids['user1']

        # Create 10 notifications
        for i in range(10):
            repo.create_notification(user_id=user_id, type=f'type{i}', data={'n': i})

        # Get page 2 (skip 3, take 3)
        page2 = repo.get_user_notifications(user_id, limit=3, offset=3)

        assert len(page2) == 3


class TestGetUnreadNotifications:
    """Test get_unread_notifications() method."""

    def test_get_only_unread_notifications(self, repo, sample_user_ids):
        """Test getting only unread notifications."""
        user_id = sample_user_ids['user1']

        # Create notifications, mark some as read
        notif1 = repo.create_notification(user_id=user_id, type='test', data={})
        notif2 = repo.create_notification(user_id=user_id, type='test', data={})
        notif3 = repo.create_notification(user_id=user_id, type='test', data={})

        repo.mark_notification_as_read(notif2.id)

        unread = repo.get_unread_notifications(user_id)

        assert len(unread) == 2
        unread_ids = {n.id for n in unread}
        assert notif1.id in unread_ids
        assert notif3.id in unread_ids
        assert notif2.id not in unread_ids

    def test_get_unread_empty_when_all_read(self, repo, sample_user_ids):
        """Test getting unread returns empty when all are read."""
        user_id = sample_user_ids['user1']

        # Create and mark all as read
        notif1 = repo.create_notification(user_id=user_id, type='test', data={})
        notif2 = repo.create_notification(user_id=user_id, type='test', data={})

        repo.mark_notification_as_read(notif1.id)
        repo.mark_notification_as_read(notif2.id)

        unread = repo.get_unread_notifications(user_id)

        assert unread == []

    def test_get_unread_empty_when_no_notifications(self, repo, sample_user_ids):
        """Test getting unread returns empty when user has no notifications."""
        user_id = sample_user_ids['user1']

        unread = repo.get_unread_notifications(user_id)

        assert unread == []

    def test_get_unread_excludes_read_notifications(self, repo, sample_user_ids):
        """Test unread list excludes read notifications."""
        user_id = sample_user_ids['user1']

        # Create mix of read and unread
        unread1 = repo.create_notification(user_id=user_id, type='test', data={'n': 1})
        read1 = repo.create_notification(user_id=user_id, type='test', data={'n': 2})
        unread2 = repo.create_notification(user_id=user_id, type='test', data={'n': 3})
        read2 = repo.create_notification(user_id=user_id, type='test', data={'n': 4})

        repo.mark_notification_as_read(read1.id)
        repo.mark_notification_as_read(read2.id)

        unread = repo.get_unread_notifications(user_id)

        assert len(unread) == 2
        assert all(not n.read for n in unread)
        assert {n.id for n in unread} == {unread1.id, unread2.id}

    def test_get_unread_sorted_by_newest_first(self, repo, sample_user_ids):
        """Test unread notifications sorted by newest first."""
        user_id = sample_user_ids['user1']

        # Create notifications
        notif1 = repo.create_notification(user_id=user_id, type='first', data={})
        notif2 = repo.create_notification(user_id=user_id, type='second', data={})
        notif3 = repo.create_notification(user_id=user_id, type='third', data={})

        unread = repo.get_unread_notifications(user_id)

        # Newest first
        assert unread[0].id == notif3.id
        assert unread[1].id == notif2.id
        assert unread[2].id == notif1.id

    def test_get_unread_multiple_unread(self, repo, sample_user_ids):
        """Test getting multiple unread notifications."""
        user_id = sample_user_ids['user1']

        # Create many unread
        created_ids = []
        for i in range(5):
            notif = repo.create_notification(user_id=user_id, type=f'type{i}', data={'n': i})
            created_ids.append(notif.id)

        unread = repo.get_unread_notifications(user_id)

        assert len(unread) == 5
        assert {n.id for n in unread} == set(created_ids)


class TestMarkNotificationAsRead:
    """Test mark_notification_as_read() method."""

    def test_mark_notification_as_read_sets_read_true(self, repo, sample_user_ids):
        """Test marking notification as read sets read=True."""
        user_id = sample_user_ids['user1']
        notification = repo.create_notification(user_id=user_id, type='test', data={})

        assert notification.read is False

        result = repo.mark_notification_as_read(notification.id)

        assert result is True
        retrieved = repo.get_notification_by_id(notification.id)
        assert retrieved.read is True

    def test_mark_notification_as_read_returns_true_on_success(self, repo, sample_user_ids):
        """Test marking as read returns True on success."""
        user_id = sample_user_ids['user1']
        notification = repo.create_notification(user_id=user_id, type='test', data={})

        result = repo.mark_notification_as_read(notification.id)

        assert result is True

    def test_mark_notification_as_read_returns_false_on_nonexistent(self, repo):
        """Test marking nonexistent notification returns False."""
        nonexistent_id = uuid4()

        result = repo.mark_notification_as_read(nonexistent_id)

        assert result is False

    def test_mark_already_read_notification(self, repo, sample_user_ids):
        """Test marking already read notification (idempotent)."""
        user_id = sample_user_ids['user1']
        notification = repo.create_notification(user_id=user_id, type='test', data={})

        # Mark twice
        repo.mark_notification_as_read(notification.id)
        result = repo.mark_notification_as_read(notification.id)

        assert result is True
        retrieved = repo.get_notification_by_id(notification.id)
        assert retrieved.read is True

    def test_mark_as_read_persists(self, repo, sample_user_ids):
        """Test marking as read persists across retrievals."""
        user_id = sample_user_ids['user1']
        notification = repo.create_notification(user_id=user_id, type='test', data={})

        repo.mark_notification_as_read(notification.id)

        # Retrieve multiple times
        retrieved1 = repo.get_notification_by_id(notification.id)
        retrieved2 = repo.get_notification_by_id(notification.id)

        assert retrieved1.read is True
        assert retrieved2.read is True

    def test_mark_as_read_affects_unread_list(self, repo, sample_user_ids):
        """Test marking as read removes from unread list."""
        user_id = sample_user_ids['user1']
        notification = repo.create_notification(user_id=user_id, type='test', data={})

        # Should be in unread
        unread_before = repo.get_unread_notifications(user_id)
        assert len(unread_before) == 1

        repo.mark_notification_as_read(notification.id)

        # Should not be in unread
        unread_after = repo.get_unread_notifications(user_id)
        assert len(unread_after) == 0


class TestMarkAllNotificationsAsRead:
    """Test mark_all_notifications_as_read() method."""

    def test_mark_all_notifications_as_read_for_user(self, repo, sample_user_ids):
        """Test marking all notifications as read for a user."""
        user_id = sample_user_ids['user1']

        # Create multiple unread notifications
        notif1 = repo.create_notification(user_id=user_id, type='test', data={})
        notif2 = repo.create_notification(user_id=user_id, type='test', data={})
        notif3 = repo.create_notification(user_id=user_id, type='test', data={})

        count = repo.mark_all_notifications_as_read(user_id)

        assert count == 3

        # All should be read
        assert repo.get_notification_by_id(notif1.id).read is True
        assert repo.get_notification_by_id(notif2.id).read is True
        assert repo.get_notification_by_id(notif3.id).read is True

    def test_mark_all_notifications_returns_count(self, repo, sample_user_ids):
        """Test mark_all returns count of marked notifications."""
        user_id = sample_user_ids['user1']

        # Create 5 notifications
        for _ in range(5):
            repo.create_notification(user_id=user_id, type='test', data={})

        count = repo.mark_all_notifications_as_read(user_id)

        assert count == 5

    def test_mark_all_notifications_only_affects_target_user(self, repo, sample_user_ids):
        """Test marking all only affects target user's notifications."""
        user1_id = sample_user_ids['user1']
        user2_id = sample_user_ids['user2']

        # Create notifications for both users
        user1_notif = repo.create_notification(user_id=user1_id, type='test', data={})
        user2_notif = repo.create_notification(user_id=user2_id, type='test', data={})

        count = repo.mark_all_notifications_as_read(user1_id)

        assert count == 1
        assert repo.get_notification_by_id(user1_notif.id).read is True
        assert repo.get_notification_by_id(user2_notif.id).read is False

    def test_mark_all_notifications_when_none_exist(self, repo, sample_user_ids):
        """Test marking all when user has no notifications."""
        user_id = sample_user_ids['user1']

        count = repo.mark_all_notifications_as_read(user_id)

        assert count == 0

    def test_mark_all_notifications_when_already_read(self, repo, sample_user_ids):
        """Test marking all when notifications already read."""
        user_id = sample_user_ids['user1']

        # Create and mark as read
        notif = repo.create_notification(user_id=user_id, type='test', data={})
        repo.mark_notification_as_read(notif.id)

        # Try to mark all again
        count = repo.mark_all_notifications_as_read(user_id)

        assert count == 0  # No unread to mark

    def test_mark_all_notifications_affects_unread_count(self, repo, sample_user_ids):
        """Test marking all affects unread count."""
        user_id = sample_user_ids['user1']

        # Create notifications
        for _ in range(3):
            repo.create_notification(user_id=user_id, type='test', data={})

        assert repo.get_unread_count(user_id) == 3

        repo.mark_all_notifications_as_read(user_id)

        assert repo.get_unread_count(user_id) == 0


class TestGetUnreadCount:
    """Test get_unread_count() method."""

    def test_get_unread_count_for_user(self, repo, sample_user_ids):
        """Test getting unread count for user."""
        user_id = sample_user_ids['user1']

        # Create notifications
        for _ in range(4):
            repo.create_notification(user_id=user_id, type='test', data={})

        count = repo.get_unread_count(user_id)

        assert count == 4

    def test_get_unread_count_zero_when_all_read(self, repo, sample_user_ids):
        """Test count is zero when all notifications are read."""
        user_id = sample_user_ids['user1']

        # Create and mark all as read
        for _ in range(3):
            notif = repo.create_notification(user_id=user_id, type='test', data={})
            repo.mark_notification_as_read(notif.id)

        count = repo.get_unread_count(user_id)

        assert count == 0

    def test_get_unread_count_zero_when_no_notifications(self, repo, sample_user_ids):
        """Test count is zero when user has no notifications."""
        user_id = sample_user_ids['user1']

        count = repo.get_unread_count(user_id)

        assert count == 0

    def test_get_unread_count_after_marking_read(self, repo, sample_user_ids):
        """Test count updates after marking notifications as read."""
        user_id = sample_user_ids['user1']

        # Create 5 notifications
        notifs = [repo.create_notification(user_id=user_id, type='test', data={}) for _ in range(5)]

        assert repo.get_unread_count(user_id) == 5

        # Mark 2 as read
        repo.mark_notification_as_read(notifs[0].id)
        repo.mark_notification_as_read(notifs[1].id)

        assert repo.get_unread_count(user_id) == 3

    def test_get_unread_count_after_creating_new_notification(self, repo, sample_user_ids):
        """Test count updates after creating new notification."""
        user_id = sample_user_ids['user1']

        assert repo.get_unread_count(user_id) == 0

        repo.create_notification(user_id=user_id, type='test', data={})
        assert repo.get_unread_count(user_id) == 1

        repo.create_notification(user_id=user_id, type='test', data={})
        assert repo.get_unread_count(user_id) == 2

    def test_get_unread_count_multiple_users(self, repo, sample_user_ids):
        """Test unread count is isolated by user."""
        user1_id = sample_user_ids['user1']
        user2_id = sample_user_ids['user2']

        # Create different amounts for each user
        for _ in range(3):
            repo.create_notification(user_id=user1_id, type='test', data={})
        for _ in range(5):
            repo.create_notification(user_id=user2_id, type='test', data={})

        assert repo.get_unread_count(user1_id) == 3
        assert repo.get_unread_count(user2_id) == 5


class TestEdgeCases:
    """Test edge cases and data integrity."""

    def test_notification_with_large_data_payload(self, repo, sample_user_ids):
        """Test notification with large JSON data payload."""
        user_id = sample_user_ids['user1']
        large_data = {
            'run_id': str(uuid4()),
            'participants': [{'id': str(uuid4()), 'name': f'User {i}'} for i in range(100)],
            'history': [
                {'action': 'state_change', 'timestamp': datetime.now(UTC).isoformat()}
                for _ in range(50)
            ],
        }

        notification = repo.create_notification(user_id=user_id, type='complex', data=large_data)

        retrieved = repo.get_notification_by_id(notification.id)
        assert retrieved.data == large_data
        assert len(retrieved.data['participants']) == 100

    def test_notification_with_unicode_in_data(self, repo, sample_user_ids):
        """Test notification with unicode characters in data."""
        user_id = sample_user_ids['user1']
        unicode_data = {
            'message': 'Hello 世界 🌍',
            'emoji': '🎉🎊✨',
            'special': 'Caf\u00e9',
        }

        notification = repo.create_notification(user_id=user_id, type='unicode', data=unicode_data)

        retrieved = repo.get_notification_by_id(notification.id)
        assert retrieved.data == unicode_data
        assert retrieved.data['message'] == 'Hello 世界 🌍'

    def test_notification_with_empty_data(self, repo, sample_user_ids):
        """Test notification with empty data dict."""
        user_id = sample_user_ids['user1']

        notification = repo.create_notification(user_id=user_id, type='empty', data={})

        assert notification.data == {}
        retrieved = repo.get_notification_by_id(notification.id)
        assert retrieved.data == {}

    def test_notification_with_nested_data_structures(self, repo, sample_user_ids):
        """Test notification with deeply nested data."""
        user_id = sample_user_ids['user1']
        nested_data = {
            'level1': {
                'level2': {
                    'level3': {
                        'level4': {
                            'value': 'deep',
                            'list': [1, 2, 3],
                        }
                    }
                }
            }
        }

        notification = repo.create_notification(user_id=user_id, type='nested', data=nested_data)

        retrieved = repo.get_notification_by_id(notification.id)
        assert retrieved.data['level1']['level2']['level3']['level4']['value'] == 'deep'

    def test_storage_is_singleton(self):
        """Test that MemoryStorage is a singleton (all instances share data)."""
        storage1 = MemoryStorage()
        storage2 = MemoryStorage()

        # Both should be the same instance
        assert storage1 is storage2

    def test_notification_ordering_consistency(self, repo, sample_user_ids):
        """Test notification ordering is consistent across calls."""
        user_id = sample_user_ids['user1']

        # Create notifications
        for i in range(5):
            repo.create_notification(user_id=user_id, type=f'type{i}', data={'n': i})

        # Get multiple times
        result1 = repo.get_user_notifications(user_id)
        result2 = repo.get_user_notifications(user_id)
        result3 = repo.get_user_notifications(user_id)

        # Order should be consistent
        assert [n.id for n in result1] == [n.id for n in result2]
        assert [n.id for n in result2] == [n.id for n in result3]

    def test_notification_type_with_special_characters(self, repo, sample_user_ids):
        """Test notification type with special characters."""
        user_id = sample_user_ids['user1']

        special_types = [
            'run:state:changed',
            'user.joined.group',
            'bid_placed_by_user',
            'notification-type-with-dashes',
        ]

        for notif_type in special_types:
            notification = repo.create_notification(user_id=user_id, type=notif_type, data={})
            assert notification.type == notif_type

    def test_mark_as_read_multiple_times_idempotent(self, repo, sample_user_ids):
        """Test marking as read multiple times is idempotent."""
        user_id = sample_user_ids['user1']
        notification = repo.create_notification(user_id=user_id, type='test', data={})

        # Mark multiple times
        for _ in range(5):
            result = repo.mark_notification_as_read(notification.id)
            assert result is True

        retrieved = repo.get_notification_by_id(notification.id)
        assert retrieved.read is True

    def test_pagination_beyond_available_notifications(self, repo, sample_user_ids):
        """Test pagination with offset beyond available notifications."""
        user_id = sample_user_ids['user1']

        # Create 3 notifications
        for i in range(3):
            repo.create_notification(user_id=user_id, type=f'type{i}', data={})

        # Try to get with large offset
        notifications = repo.get_user_notifications(user_id, limit=10, offset=100)

        assert notifications == []

    def test_concurrent_notification_creation(self, repo, sample_user_ids):
        """Test creating notifications for multiple users concurrently."""
        user1_id = sample_user_ids['user1']
        user2_id = sample_user_ids['user2']
        user3_id = sample_user_ids['user3']

        # Create notifications for all users
        all_notifs = []
        for i in range(10):
            if i % 3 == 0:
                all_notifs.append(
                    repo.create_notification(user_id=user1_id, type='test', data={'n': i})
                )
            elif i % 3 == 1:
                all_notifs.append(
                    repo.create_notification(user_id=user2_id, type='test', data={'n': i})
                )
            else:
                all_notifs.append(
                    repo.create_notification(user_id=user3_id, type='test', data={'n': i})
                )

        # Verify each user gets only their notifications
        user1_notifs = repo.get_user_notifications(user1_id)
        user2_notifs = repo.get_user_notifications(user2_id)
        user3_notifs = repo.get_user_notifications(user3_id)

        assert len(user1_notifs) == 4  # indices 0, 3, 6, 9
        assert len(user2_notifs) == 3  # indices 1, 4, 7
        assert len(user3_notifs) == 3  # indices 2, 5, 8
