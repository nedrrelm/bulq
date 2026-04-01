"""Base pytest fixtures for the test suite.

This module contains shared fixtures that can be used across all test modules.
It provides mock repository instances and sample test data for common models.
"""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock

import pytest

from app.core.models import Group, User


@pytest.fixture
def test_uuid() -> callable:
    """Factory fixture for generating consistent test UUIDs.

    Returns:
        callable: A function that generates a new UUID each time it's called.

    Example:
        >>> def test_something(test_uuid):
        ...     user_id = test_uuid()
        ...     group_id = test_uuid()
    """
    return lambda: uuid.uuid4()


@pytest.fixture
def fixed_uuid() -> uuid.UUID:
    """Fixture providing a fixed UUID for testing equality checks.

    Returns:
        UUID: A fixed UUID that remains constant across test runs.
    """
    return uuid.UUID('12345678-1234-5678-1234-567812345678')


@pytest.fixture
def test_user(test_uuid: callable) -> User:
    """Fixture providing a sample User instance for testing.

    Args:
        test_uuid: Factory fixture for generating UUIDs.

    Returns:
        User: A User instance with realistic test data.
    """
    user = User()
    user.id = test_uuid()
    user.name = 'Test User'
    user.username = 'testuser'
    user.password_hash = '$2b$12$KIXfP3qK8Y6Z8Y6Z8Y6Z8O9Z8Y6Z8Y6Z8Y6Z8Y6Z8Y6Z8Y6Z8Y6Z'
    user.is_admin = False
    user.verified = True
    user.dark_mode = False
    user.preferred_language = 'en'
    user.created_at = datetime.now(UTC)
    return user


@pytest.fixture
def test_admin_user(test_uuid: callable) -> User:
    """Fixture providing a sample admin User instance for testing.

    Args:
        test_uuid: Factory fixture for generating UUIDs.

    Returns:
        User: An admin User instance with realistic test data.
    """
    user = User()
    user.id = test_uuid()
    user.name = 'Admin User'
    user.username = 'adminuser'
    user.password_hash = '$2b$12$KIXfP3qK8Y6Z8Y6Z8Y6Z8O9Z8Y6Z8Y6Z8Y6Z8Y6Z8Y6Z8Y6Z8Y6Z'
    user.is_admin = True
    user.verified = True
    user.dark_mode = False
    user.preferred_language = 'en'
    user.created_at = datetime.now(UTC)
    return user


@pytest.fixture
def test_group_member(test_uuid: callable) -> User:
    """Fixture providing a sample group member User instance for testing.

    Args:
        test_uuid: Factory fixture for generating UUIDs.

    Returns:
        User: A group member User instance with realistic test data.
    """
    user = User()
    user.id = test_uuid()
    user.name = 'Group Member'
    user.username = 'groupmember'
    user.password_hash = '$2b$12$KIXfP3qK8Y6Z8Y6Z8Y6Z8O9Z8Y6Z8Y6Z8Y6Z8Y6Z8Y6Z8Y6Z8Y6Z'
    user.is_admin = False
    user.verified = True
    user.dark_mode = False
    user.preferred_language = 'en'
    user.created_at = datetime.now(UTC)
    return user


@pytest.fixture
def test_group(test_uuid: callable, test_user: User) -> Group:
    """Fixture providing a sample Group instance for testing.

    Args:
        test_uuid: Factory fixture for generating UUIDs.
        test_user: Sample user fixture to use as group creator.

    Returns:
        Group: A Group instance with realistic test data.
    """
    group = Group()
    group.id = test_uuid()
    group.name = 'Test Group'
    group.created_by = test_user.id
    group.invite_token = str(test_uuid())
    group.is_joining_allowed = True
    group.created_at = datetime.now(UTC)
    return group


@pytest.fixture
def mock_user_repo() -> AsyncMock:
    """Mock fixture for UserRepository.

    Returns:
        AsyncMock: A mock repository with common UserRepository methods.

    Common methods mocked:
        - get_by_id: Retrieve user by ID
        - get_by_username: Retrieve user by username
        - create: Create a new user
        - update: Update existing user
        - delete: Delete a user
    """
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=None)
    repo.get_by_username = AsyncMock(return_value=None)
    repo.create = AsyncMock(return_value=None)
    repo.update = AsyncMock(return_value=None)
    repo.delete = AsyncMock(return_value=None)
    return repo


@pytest.fixture
def mock_group_repo() -> AsyncMock:
    """Mock fixture for GroupRepository.

    Returns:
        AsyncMock: A mock repository with common GroupRepository methods.

    Common methods mocked:
        - get_by_id: Retrieve group by ID
        - get_by_invite_token: Retrieve group by invite token
        - create: Create a new group
        - update: Update existing group
        - delete: Delete a group
        - get_user_groups: Get all groups for a user
    """
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=None)
    repo.get_by_invite_token = AsyncMock(return_value=None)
    repo.create = AsyncMock(return_value=None)
    repo.update = AsyncMock(return_value=None)
    repo.delete = AsyncMock(return_value=None)
    repo.get_user_groups = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def mock_run_repo() -> AsyncMock:
    """Mock fixture for RunRepository.

    Returns:
        AsyncMock: A mock repository with common RunRepository methods.

    Common methods mocked:
        - get_by_id: Retrieve run by ID
        - create: Create a new run
        - update: Update existing run
        - delete: Delete a run
        - get_group_runs: Get all runs for a group
        - update_state: Update run state
    """
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=None)
    repo.create = AsyncMock(return_value=None)
    repo.update = AsyncMock(return_value=None)
    repo.delete = AsyncMock(return_value=None)
    repo.get_group_runs = AsyncMock(return_value=[])
    repo.update_state = AsyncMock(return_value=None)
    return repo


@pytest.fixture
def mock_product_repo() -> AsyncMock:
    """Mock fixture for ProductRepository.

    Returns:
        AsyncMock: A mock repository with common ProductRepository methods.

    Common methods mocked:
        - get_by_id: Retrieve product by ID
        - create: Create a new product
        - update: Update existing product
        - delete: Delete a product
        - search: Search products by name
        - get_verified: Get verified products
    """
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=None)
    repo.create = AsyncMock(return_value=None)
    repo.update = AsyncMock(return_value=None)
    repo.delete = AsyncMock(return_value=None)
    repo.search = AsyncMock(return_value=[])
    repo.get_verified = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def mock_store_repo() -> AsyncMock:
    """Mock fixture for StoreRepository.

    Returns:
        AsyncMock: A mock repository with common StoreRepository methods.

    Common methods mocked:
        - get_by_id: Retrieve store by ID
        - create: Create a new store
        - update: Update existing store
        - delete: Delete a store
        - search: Search stores by name
        - get_verified: Get verified stores
    """
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=None)
    repo.create = AsyncMock(return_value=None)
    repo.update = AsyncMock(return_value=None)
    repo.delete = AsyncMock(return_value=None)
    repo.search = AsyncMock(return_value=[])
    repo.get_verified = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def mock_bid_repo() -> AsyncMock:
    """Mock fixture for BidRepository.

    Returns:
        AsyncMock: A mock repository with common BidRepository methods.

    Common methods mocked:
        - get_by_id: Retrieve bid by ID
        - create: Create a new bid
        - update: Update existing bid
        - delete: Delete a bid
        - get_run_bids: Get all bids for a run
        - get_user_bids: Get all bids for a user in a run
    """
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=None)
    repo.create = AsyncMock(return_value=None)
    repo.update = AsyncMock(return_value=None)
    repo.delete = AsyncMock(return_value=None)
    repo.get_run_bids = AsyncMock(return_value=[])
    repo.get_user_bids = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def mock_notification_repo() -> AsyncMock:
    """Mock fixture for NotificationRepository.

    Returns:
        AsyncMock: A mock repository with common NotificationRepository methods.

    Common methods mocked:
        - get_by_id: Retrieve notification by ID
        - create: Create a new notification
        - update: Update existing notification
        - delete: Delete a notification
        - get_user_notifications: Get all notifications for a user
        - mark_as_read: Mark notification as read
    """
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=None)
    repo.create = AsyncMock(return_value=None)
    repo.update = AsyncMock(return_value=None)
    repo.delete = AsyncMock(return_value=None)
    repo.get_user_notifications = AsyncMock(return_value=[])
    repo.mark_as_read = AsyncMock(return_value=None)
    return repo


@pytest.fixture
def mock_shopping_repo() -> AsyncMock:
    """Mock fixture for ShoppingRepository.

    Returns:
        AsyncMock: A mock repository with common ShoppingRepository methods.

    Common methods mocked:
        - get_by_id: Retrieve shopping list item by ID
        - create: Create a new shopping list item
        - update: Update existing shopping list item
        - delete: Delete a shopping list item
        - get_run_items: Get all shopping list items for a run
        - mark_as_purchased: Mark item as purchased
    """
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=None)
    repo.create = AsyncMock(return_value=None)
    repo.update = AsyncMock(return_value=None)
    repo.delete = AsyncMock(return_value=None)
    repo.get_run_items = AsyncMock(return_value=[])
    repo.mark_as_purchased = AsyncMock(return_value=None)
    return repo


@pytest.fixture
def mock_reassignment_repo() -> AsyncMock:
    """Mock fixture for ReassignmentRepository.

    Returns:
        AsyncMock: A mock repository with common ReassignmentRepository methods.

    Common methods mocked:
        - get_by_id: Retrieve reassignment request by ID
        - create: Create a new reassignment request
        - update: Update existing reassignment request
        - delete: Delete a reassignment request
        - get_pending_for_user: Get pending requests for a user
        - get_pending_for_run: Get pending requests for a run
    """
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=None)
    repo.create = AsyncMock(return_value=None)
    repo.update = AsyncMock(return_value=None)
    repo.delete = AsyncMock(return_value=None)
    repo.get_pending_for_user = AsyncMock(return_value=[])
    repo.get_pending_for_run = AsyncMock(return_value=None)
    return repo


@pytest.fixture
def mock_event_bus() -> Mock:
    """Mock fixture for EventBus.

    Returns:
        Mock: A mock event bus with common EventBus methods.

    Common methods mocked:
        - subscribe: Subscribe a handler to an event type
        - emit: Emit a domain event to all subscribed handlers
        - clear_handlers: Clear all registered handlers
    """
    event_bus = Mock()
    event_bus.subscribe = Mock()
    event_bus.emit = Mock()
    event_bus.clear_handlers = Mock()
    event_bus._handlers = {}
    return event_bus


@pytest.fixture(autouse=True)
def mock_bcrypt(monkeypatch):
    """Mock bcrypt for fast tests - we test our logic, not bcrypt internals.

    This fixture automatically applies to all tests, making bcrypt operations instant.
    We're testing that our code correctly calls bcrypt, not that bcrypt works.

    Mocked functions:
        - bcrypt.hashpw: Returns a fake bcrypt-formatted hash (with randomness)
        - bcrypt.checkpw: Does simple password comparison
        - bcrypt.gensalt: Returns a fake salt (with randomness)

    Note: This speeds up auth tests from ~17s to <0.5s.
    """
    import random

    # Dictionary to store password->hash mappings for verification
    hash_storage = {}
    # Counter for unique hashes
    hash_counter = [0]

    def fake_hashpw(password: bytes, salt: bytes) -> bytes:
        """Mock hashpw that returns a unique fake hash each time."""
        # Check length limit (bcrypt max is 72 bytes)
        if len(password) > 72:
            raise ValueError('password cannot be longer than 72 bytes')

        # Create a unique fake bcrypt hash with randomness
        # Each call gets a unique hash even for the same password (simulates salt)
        hash_counter[0] += 1
        random_part = str(random.randint(100000, 999999))
        unique_part = str(hash_counter[0]).zfill(6)
        password_hash = str(hash(password))[-8:].replace('-', '0')

        fake_hash = f'$2b$12$salt{random_part}{unique_part}{password_hash}'.encode()[:60].ljust(
            60, b'x'
        )
        # Store mapping for checkpw
        hash_storage[fake_hash] = password
        return fake_hash

    def fake_checkpw(password: bytes, hashed: bytes) -> bool:
        """Mock checkpw that compares password to stored hash."""
        # If this hash is in our storage, compare passwords
        if hashed in hash_storage:
            return hash_storage[hashed] == password
        # For hashes not in storage (from fixtures), do simple check
        # This allows pre-existing password_hash fields in fixtures to work
        try:
            # Just return True for any reasonable-looking hash
            return hashed.startswith(b'$2b$') or hashed.startswith(b'$2a$')
        except AttributeError, TypeError:
            return False

    def fake_gensalt(rounds: int = 12) -> bytes:
        """Mock gensalt that returns a unique fake salt each time."""
        # Add some randomness to simulate different salts
        random_salt = str(random.randint(100000, 999999))
        return f'$2b${rounds}$salt{random_salt}'.encode()

    # Patch the bcrypt functions
    monkeypatch.setattr('bcrypt.hashpw', fake_hashpw)
    monkeypatch.setattr('bcrypt.checkpw', fake_checkpw)
    monkeypatch.setattr('bcrypt.gensalt', fake_gensalt)

    yield

    # Cleanup
    hash_storage.clear()
    hash_counter[0] = 0
