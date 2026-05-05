"""Unit tests for session store implementations.

Tests cover:
- InMemorySessionStore basic operations (set, get, delete)
- Session TTL (time-to-live) expiration
- Data integrity and type handling
- Edge cases and error handling
- Session isolation and concurrency
"""

import time
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.infrastructure.session_store import (
    InMemorySessionStore,
    RedisSessionStore,
    get_session_store,
    get_store,
    init_session_store,
)


class TestInMemorySessionStoreBasicOperations:
    """Test basic operations of InMemorySessionStore."""

    @pytest.fixture
    def store(self):
        """Create a fresh InMemorySessionStore for each test."""
        return InMemorySessionStore()

    async def test_set_stores_session_data(self, store):
        """Test that set() stores session data."""
        session_token = 'test-token-123'
        session_data = {'user_id': 'user-456', 'role': 'admin'}
        ttl_seconds = 3600

        await store.set(session_token, session_data, ttl_seconds)

        # Verify session is stored
        result = await store.get(session_token)
        assert result is not None

    async def test_get_retrieves_stored_data(self, store):
        """Test that get() retrieves stored session data."""
        session_token = 'test-token-123'
        session_data = {'user_id': 'user-456', 'role': 'admin'}
        ttl_seconds = 3600

        await store.set(session_token, session_data, ttl_seconds)
        result = await store.get(session_token)

        assert result['user_id'] == 'user-456'
        assert result['role'] == 'admin'

    async def test_get_returns_none_for_non_existent_key(self, store):
        """Test that get() returns None for non-existent key."""
        result = await store.get('non-existent-token')

        assert result is None

    async def test_delete_removes_session(self, store):
        """Test that delete() removes session."""
        session_token = 'test-token-123'
        session_data = {'user_id': 'user-456'}
        ttl_seconds = 3600

        await store.set(session_token, session_data, ttl_seconds)
        await store.delete(session_token)

        result = await store.get(session_token)
        assert result is None

    async def test_delete_returns_true_when_successful(self, store):
        """Test that delete() returns True when successful."""
        session_token = 'test-token-123'
        session_data = {'user_id': 'user-456'}
        ttl_seconds = 3600

        await store.set(session_token, session_data, ttl_seconds)
        result = await store.delete(session_token)

        assert result is True

    async def test_delete_returns_false_for_non_existent_key(self, store):
        """Test that delete() returns False for non-existent key."""
        result = await store.delete('non-existent-token')

        assert result is False

    async def test_session_contains_expires_at(self, store):
        """Test that stored session contains expires_at timestamp."""
        session_token = 'test-token-123'
        session_data = {'user_id': 'user-456'}
        ttl_seconds = 3600

        await store.set(session_token, session_data, ttl_seconds)
        result = await store.get(session_token)

        assert 'expires_at' in result
        assert isinstance(result['expires_at'], datetime)


class TestInMemorySessionStoreTTL:
    """Test TTL (time-to-live) functionality."""

    @pytest.fixture
    def store(self):
        """Create a fresh InMemorySessionStore for each test."""
        return InMemorySessionStore()

    async def test_session_with_ttl_is_stored(self, store):
        """Test that session with TTL is stored correctly."""
        session_token = 'test-token-123'
        session_data = {'user_id': 'user-456'}
        ttl_seconds = 3600

        await store.set(session_token, session_data, ttl_seconds)
        result = await store.get(session_token)

        assert result is not None

    async def test_session_can_be_retrieved_before_ttl_expires(self, store):
        """Test that session can be retrieved before TTL expires."""
        session_token = 'test-token-123'
        session_data = {'user_id': 'user-456'}
        ttl_seconds = 3600

        await store.set(session_token, session_data, ttl_seconds)

        # Retrieve immediately (well before expiration)
        result = await store.get(session_token)
        assert result is not None
        assert result['user_id'] == 'user-456'

    async def test_session_expires_at_is_calculated_correctly(self, store):
        """Test that expires_at is calculated correctly based on TTL."""
        session_token = 'test-token-123'
        session_data = {'user_id': 'user-456'}
        ttl_seconds = 3600

        before_set = datetime.now(UTC)
        await store.set(session_token, session_data, ttl_seconds)
        after_set = datetime.now(UTC)

        result = await store.get(session_token)

        expected_min = before_set + timedelta(seconds=ttl_seconds)
        expected_max = after_set + timedelta(seconds=ttl_seconds)

        assert expected_min <= result['expires_at'] <= expected_max

    @pytest.mark.parametrize(
        'ttl_seconds',
        [
            1,
            10,
            60,
            3600,
            86400,
        ],
    )
    async def test_session_with_different_ttl_values(self, store, ttl_seconds):
        """Test session storage with different TTL values."""
        session_token = f'test-token-{ttl_seconds}'
        session_data = {'user_id': 'user-456'}

        await store.set(session_token, session_data, ttl_seconds)
        result = await store.get(session_token)

        assert result is not None
        assert result['user_id'] == 'user-456'

    async def test_expired_session_returns_none(self, store):
        """Test that expired session returns None and is cleaned up."""
        session_token = 'test-token-123'
        session_data = {'user_id': 'user-456'}
        ttl_seconds = 1

        await store.set(session_token, session_data, ttl_seconds)

        # Wait for session to expire
        time.sleep(1.1)

        result = await store.get(session_token)
        assert result is None

    async def test_expired_session_is_removed_from_store(self, store):
        """Test that expired session is removed from internal storage."""
        session_token = 'test-token-123'
        session_data = {'user_id': 'user-456'}
        ttl_seconds = 1

        await store.set(session_token, session_data, ttl_seconds)
        assert session_token in store.sessions

        # Wait for expiration and try to get
        time.sleep(1.1)
        await store.get(session_token)

        # Should be removed from internal storage
        assert session_token not in store.sessions

    async def test_zero_ttl_session(self, store):
        """Test session with 0 TTL expires immediately."""
        session_token = 'test-token-123'
        session_data = {'user_id': 'user-456'}
        ttl_seconds = 0

        await store.set(session_token, session_data, ttl_seconds)

        # Even without sleep, should be expired
        result = await store.get(session_token)
        assert result is None

    async def test_negative_ttl_session(self, store):
        """Test session with negative TTL expires immediately."""
        session_token = 'test-token-123'
        session_data = {'user_id': 'user-456'}
        ttl_seconds = -100

        await store.set(session_token, session_data, ttl_seconds)

        result = await store.get(session_token)
        assert result is None


class TestInMemorySessionStoreDataIntegrity:
    """Test data integrity and type handling."""

    @pytest.fixture
    def store(self):
        """Create a fresh InMemorySessionStore for each test."""
        return InMemorySessionStore()

    async def test_storing_dict_data(self, store):
        """Test storing dictionary data."""
        session_token = 'test-token-123'
        session_data = {'user_id': 'user-456', 'role': 'admin', 'permissions': ['read', 'write']}
        ttl_seconds = 3600

        await store.set(session_token, session_data, ttl_seconds)
        result = await store.get(session_token)

        assert result['user_id'] == 'user-456'
        assert result['role'] == 'admin'
        assert result['permissions'] == ['read', 'write']

    async def test_storing_complex_nested_dicts(self, store):
        """Test storing complex nested dictionaries."""
        session_token = 'test-token-123'
        session_data = {
            'user_id': 'user-456',
            'profile': {
                'name': 'John Doe',
                'email': 'john@example.com',
                'settings': {'theme': 'dark', 'notifications': True},
            },
        }
        ttl_seconds = 3600

        await store.set(session_token, session_data, ttl_seconds)
        result = await store.get(session_token)

        assert result['user_id'] == 'user-456'
        assert result['profile']['name'] == 'John Doe'
        assert result['profile']['settings']['theme'] == 'dark'
        assert result['profile']['settings']['notifications'] is True

    async def test_storing_empty_dict(self, store):
        """Test storing empty dictionary."""
        session_token = 'test-token-123'
        session_data = {}
        ttl_seconds = 3600

        await store.set(session_token, session_data, ttl_seconds)
        result = await store.get(session_token)

        assert result is not None
        assert 'expires_at' in result

    async def test_overwriting_existing_key(self, store):
        """Test overwriting existing session key."""
        session_token = 'test-token-123'
        session_data_1 = {'user_id': 'user-456', 'version': 1}
        session_data_2 = {'user_id': 'user-789', 'version': 2}
        ttl_seconds = 3600

        await store.set(session_token, session_data_1, ttl_seconds)
        await store.set(session_token, session_data_2, ttl_seconds)

        result = await store.get(session_token)
        assert result['user_id'] == 'user-789'
        assert result['version'] == 2

    async def test_storing_string_values(self, store):
        """Test storing string values in session data."""
        session_token = 'test-token-123'
        session_data = {
            'user_id': 'user-456',
            'name': 'John Doe',
            'email': 'john@example.com',
        }
        ttl_seconds = 3600

        await store.set(session_token, session_data, ttl_seconds)
        result = await store.get(session_token)

        assert result['name'] == 'John Doe'
        assert result['email'] == 'john@example.com'

    async def test_storing_integer_values(self, store):
        """Test storing integer values in session data."""
        session_token = 'test-token-123'
        session_data = {'user_id': 'user-456', 'age': 30, 'count': 42}
        ttl_seconds = 3600

        await store.set(session_token, session_data, ttl_seconds)
        result = await store.get(session_token)

        assert result['age'] == 30
        assert result['count'] == 42

    async def test_storing_list_values(self, store):
        """Test storing list values in session data."""
        session_token = 'test-token-123'
        session_data = {'user_id': 'user-456', 'roles': ['admin', 'user', 'moderator']}
        ttl_seconds = 3600

        await store.set(session_token, session_data, ttl_seconds)
        result = await store.get(session_token)

        assert result['roles'] == ['admin', 'user', 'moderator']

    async def test_storing_boolean_values(self, store):
        """Test storing boolean values in session data."""
        session_token = 'test-token-123'
        session_data = {'user_id': 'user-456', 'is_active': True, 'is_verified': False}
        ttl_seconds = 3600

        await store.set(session_token, session_data, ttl_seconds)
        result = await store.get(session_token)

        assert result['is_active'] is True
        assert result['is_verified'] is False

    async def test_storing_none_value(self, store):
        """Test storing None values in session data."""
        session_token = 'test-token-123'
        session_data = {'user_id': 'user-456', 'optional_field': None}
        ttl_seconds = 3600

        await store.set(session_token, session_data, ttl_seconds)
        result = await store.get(session_token)

        assert 'optional_field' in result
        assert result['optional_field'] is None

    async def test_storing_uuid_in_data(self, store):
        """Test storing UUID strings in session data."""
        session_token = 'test-token-123'
        session_data = {
            'user_id': '550e8400-e29b-41d4-a716-446655440000',
            'session_id': 'abc-def-123',
        }
        ttl_seconds = 3600

        await store.set(session_token, session_data, ttl_seconds)
        result = await store.get(session_token)

        assert result['user_id'] == '550e8400-e29b-41d4-a716-446655440000'

    async def test_data_is_not_corrupted_after_retrieval(self, store):
        """Test that data is not corrupted after retrieval."""
        session_token = 'test-token-123'
        session_data = {'user_id': 'user-456', 'data': {'key': 'value'}}
        ttl_seconds = 3600

        await store.set(session_token, session_data, ttl_seconds)

        # Get multiple times
        result1 = await store.get(session_token)
        result2 = await store.get(session_token)

        assert result1['user_id'] == result2['user_id']
        assert result1['data'] == result2['data']


class TestInMemorySessionStoreEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def store(self):
        """Create a fresh InMemorySessionStore for each test."""
        return InMemorySessionStore()

    async def test_empty_string_key(self, store):
        """Test with empty string session token."""
        session_token = ''
        session_data = {'user_id': 'user-456'}
        ttl_seconds = 3600

        await store.set(session_token, session_data, ttl_seconds)
        result = await store.get(session_token)

        assert result is not None
        assert result['user_id'] == 'user-456'

    async def test_very_long_key(self, store):
        """Test with very long session token."""
        session_token = 'a' * 1000
        session_data = {'user_id': 'user-456'}
        ttl_seconds = 3600

        await store.set(session_token, session_data, ttl_seconds)
        result = await store.get(session_token)

        assert result is not None
        assert result['user_id'] == 'user-456'

    async def test_special_characters_in_key(self, store):
        """Test storing session with special characters in token."""
        session_token = 'token-@#$%^&*()_+-=[]{}|;:,.<>?/'
        session_data = {'user_id': 'user-456'}
        ttl_seconds = 3600

        await store.set(session_token, session_data, ttl_seconds)
        result = await store.get(session_token)

        assert result is not None

    async def test_unicode_in_key(self, store):
        """Test storing session with unicode characters in token."""
        session_token = 'token-密码🔐'
        session_data = {'user_id': 'user-456'}
        ttl_seconds = 3600

        await store.set(session_token, session_data, ttl_seconds)
        result = await store.get(session_token)

        assert result is not None

    async def test_multiple_concurrent_operations(self, store):
        """Test multiple concurrent session operations."""
        # Create multiple sessions
        for i in range(100):
            session_token = f'token-{i}'
            session_data = {'user_id': f'user-{i}'}
            await store.set(session_token, session_data, 3600)

        # Verify all sessions exist
        for i in range(100):
            session_token = f'token-{i}'
            result = await store.get(session_token)
            assert result is not None
            assert result['user_id'] == f'user-{i}'

    async def test_session_isolation(self, store):
        """Test that different sessions are isolated."""
        await store.set('token-1', {'user_id': 'user-1'}, 3600)
        await store.set('token-2', {'user_id': 'user-2'}, 3600)
        await store.set('token-3', {'user_id': 'user-3'}, 3600)

        # Delete one session
        await store.delete('token-2')

        # Other sessions should still exist
        assert await store.get('token-1') is not None
        assert await store.get('token-2') is None
        assert await store.get('token-3') is not None

    async def test_delete_non_existent_multiple_times(self, store):
        """Test deleting non-existent session multiple times."""
        result1 = await store.delete('non-existent')
        result2 = await store.delete('non-existent')
        result3 = await store.delete('non-existent')

        assert result1 is False
        assert result2 is False
        assert result3 is False

    async def test_get_after_delete(self, store):
        """Test getting session after deletion."""
        session_token = 'test-token-123'
        session_data = {'user_id': 'user-456'}

        await store.set(session_token, session_data, 3600)
        assert await store.get(session_token) is not None

        await store.delete(session_token)
        assert await store.get(session_token) is None

    async def test_multiple_stores_are_independent(self):
        """Test that multiple store instances are independent."""
        store1 = InMemorySessionStore()
        store2 = InMemorySessionStore()

        await store1.set('token-1', {'user_id': 'user-1'}, 3600)
        await store2.set('token-2', {'user_id': 'user-2'}, 3600)

        # Each store should only have its own session
        assert await store1.get('token-1') is not None
        assert await store1.get('token-2') is None

        assert await store2.get('token-1') is None
        assert await store2.get('token-2') is not None


class TestRedisSessionStore:
    """Test RedisSessionStore implementation."""

    def test_redis_store_initialization_success(self):
        """Test successful Redis connection initialization."""
        mock_redis_module = MagicMock()
        mock_redis_client = MagicMock()
        mock_redis_module.from_url.return_value = mock_redis_client
        mock_redis_parent = MagicMock()
        mock_redis_parent.asyncio = mock_redis_module

        with patch.dict(
            'sys.modules', {'redis': mock_redis_parent, 'redis.asyncio': mock_redis_module}
        ):
            store = RedisSessionStore('redis://localhost:6379/0')

            assert store.redis == mock_redis_client

    def test_redis_store_initialization_failure(self):
        """Test Redis connection failure raises exception."""
        mock_redis_module = MagicMock()
        mock_redis_module.from_url.side_effect = Exception('Connection failed')
        mock_redis_parent = MagicMock()
        mock_redis_parent.asyncio = mock_redis_module

        with (
            patch.dict(
                'sys.modules', {'redis': mock_redis_parent, 'redis.asyncio': mock_redis_module}
            ),
            pytest.raises(Exception, match='Connection failed'),
        ):
            RedisSessionStore('redis://localhost:6379/0')

    async def test_redis_set_stores_data(self):
        """Test that set() stores data in Redis."""
        mock_redis_module = MagicMock()
        mock_redis_client = AsyncMock()
        mock_redis_module.from_url.return_value = mock_redis_client
        mock_redis_parent = MagicMock()
        mock_redis_parent.asyncio = mock_redis_module

        with patch.dict(
            'sys.modules', {'redis': mock_redis_parent, 'redis.asyncio': mock_redis_module}
        ):
            store = RedisSessionStore('redis://localhost:6379/0')
            session_data = {'user_id': 'user-456', 'role': 'admin'}

            await store.set('test-token', session_data, 3600)

            mock_redis_client.hset.assert_called_once()
            mock_redis_client.expire.assert_called_once_with('session:test-token', 3600)

    async def test_redis_set_serializes_datetime(self):
        """Test that set() serializes datetime objects to ISO format."""
        mock_redis_module = MagicMock()
        mock_redis_client = AsyncMock()
        mock_redis_module.from_url.return_value = mock_redis_client
        mock_redis_parent = MagicMock()
        mock_redis_parent.asyncio = mock_redis_module

        with patch.dict(
            'sys.modules', {'redis': mock_redis_parent, 'redis.asyncio': mock_redis_module}
        ):
            store = RedisSessionStore('redis://localhost:6379/0')
            now = datetime.now(UTC)
            session_data = {'user_id': 'user-456', 'created_at': now}

            await store.set('test-token', session_data, 3600)

            # Check that hset was called with serialized datetime
            call_args = mock_redis_client.hset.call_args
            assert 'created_at' in call_args[1]['mapping']

    async def test_redis_get_returns_data(self):
        """Test that get() retrieves data from Redis."""
        mock_redis_module = MagicMock()
        mock_redis_client = AsyncMock()
        mock_redis_client.hgetall.return_value = {'user_id': 'user-456', 'role': 'admin'}
        mock_redis_module.from_url.return_value = mock_redis_client
        mock_redis_parent = MagicMock()
        mock_redis_parent.asyncio = mock_redis_module

        with patch.dict(
            'sys.modules', {'redis': mock_redis_parent, 'redis.asyncio': mock_redis_module}
        ):
            store = RedisSessionStore('redis://localhost:6379/0')

            result = await store.get('test-token')

            assert result is not None
            assert result['user_id'] == 'user-456'
            mock_redis_client.hgetall.assert_called_once_with('session:test-token')

    async def test_redis_get_returns_none_for_empty_data(self):
        """Test that get() returns None when Redis returns empty data."""
        mock_redis_module = MagicMock()
        mock_redis_client = AsyncMock()
        mock_redis_client.hgetall.return_value = {}
        mock_redis_module.from_url.return_value = mock_redis_client
        mock_redis_parent = MagicMock()
        mock_redis_parent.asyncio = mock_redis_module

        with patch.dict(
            'sys.modules', {'redis': mock_redis_parent, 'redis.asyncio': mock_redis_module}
        ):
            store = RedisSessionStore('redis://localhost:6379/0')

            result = await store.get('test-token')

            assert result is None

    async def test_redis_get_deserializes_datetime(self):
        """Test that get() deserializes ISO datetime strings."""
        mock_redis_module = MagicMock()
        mock_redis_client = AsyncMock()
        now = datetime.now(UTC)
        mock_redis_client.hgetall.return_value = {
            'user_id': 'user-456',
            'created_at': now.isoformat(),
            'expires_at': now.isoformat(),
        }
        mock_redis_module.from_url.return_value = mock_redis_client
        mock_redis_parent = MagicMock()
        mock_redis_parent.asyncio = mock_redis_module

        with patch.dict(
            'sys.modules', {'redis': mock_redis_parent, 'redis.asyncio': mock_redis_module}
        ):
            store = RedisSessionStore('redis://localhost:6379/0')

            result = await store.get('test-token')

            assert isinstance(result['created_at'], datetime)
            assert isinstance(result['expires_at'], datetime)

    async def test_redis_get_handles_exception(self):
        """Test that get() handles exceptions gracefully."""
        mock_redis_module = MagicMock()
        mock_redis_client = AsyncMock()
        mock_redis_client.hgetall.side_effect = Exception('Redis error')
        mock_redis_module.from_url.return_value = mock_redis_client
        mock_redis_parent = MagicMock()
        mock_redis_parent.asyncio = mock_redis_module

        with patch.dict(
            'sys.modules', {'redis': mock_redis_parent, 'redis.asyncio': mock_redis_module}
        ):
            store = RedisSessionStore('redis://localhost:6379/0')

            result = await store.get('test-token')

            assert result is None

    async def test_redis_delete_removes_session(self):
        """Test that delete() removes session from Redis."""
        mock_redis_module = MagicMock()
        mock_redis_client = AsyncMock()
        mock_redis_client.delete.return_value = 1
        mock_redis_module.from_url.return_value = mock_redis_client
        mock_redis_parent = MagicMock()
        mock_redis_parent.asyncio = mock_redis_module

        with patch.dict(
            'sys.modules', {'redis': mock_redis_parent, 'redis.asyncio': mock_redis_module}
        ):
            store = RedisSessionStore('redis://localhost:6379/0')

            result = await store.delete('test-token')

            assert result is True
            mock_redis_client.delete.assert_called_once_with('session:test-token')

    async def test_redis_delete_returns_false_for_non_existent(self):
        """Test that delete() returns False for non-existent session."""
        mock_redis_module = MagicMock()
        mock_redis_client = AsyncMock()
        mock_redis_client.delete.return_value = 0
        mock_redis_module.from_url.return_value = mock_redis_client
        mock_redis_parent = MagicMock()
        mock_redis_parent.asyncio = mock_redis_module

        with patch.dict(
            'sys.modules', {'redis': mock_redis_parent, 'redis.asyncio': mock_redis_module}
        ):
            store = RedisSessionStore('redis://localhost:6379/0')

            result = await store.delete('test-token')

            assert result is False

    async def test_redis_delete_handles_exception(self):
        """Test that delete() handles exceptions gracefully."""
        mock_redis_module = MagicMock()
        mock_redis_client = AsyncMock()
        mock_redis_client.delete.side_effect = Exception('Redis error')
        mock_redis_module.from_url.return_value = mock_redis_client
        mock_redis_parent = MagicMock()
        mock_redis_parent.asyncio = mock_redis_module

        with patch.dict(
            'sys.modules', {'redis': mock_redis_parent, 'redis.asyncio': mock_redis_module}
        ):
            store = RedisSessionStore('redis://localhost:6379/0')

            result = await store.delete('test-token')

            assert result is False


class TestSessionStoreFactory:
    """Test session store factory functions."""

    async def test_get_session_store_returns_memory_by_default(self):
        """Test that get_session_store returns InMemorySessionStore by default."""
        with patch('app.infrastructure.config.SESSION_STORE_TYPE', 'memory'):
            store = await get_session_store()

            assert isinstance(store, InMemorySessionStore)

    async def test_get_session_store_returns_redis_when_configured(self):
        """Test that get_session_store returns RedisSessionStore when configured."""
        mock_redis_module = MagicMock()
        mock_redis_client = AsyncMock()
        mock_redis_client.ping.return_value = True
        mock_redis_module.from_url.return_value = mock_redis_client
        mock_redis_parent = MagicMock()
        mock_redis_parent.asyncio = mock_redis_module

        with (
            patch('app.infrastructure.config.SESSION_STORE_TYPE', 'redis'),
            patch('app.infrastructure.config.REDIS_URL', 'redis://localhost:6379/0'),
            patch.dict(
                'sys.modules', {'redis': mock_redis_parent, 'redis.asyncio': mock_redis_module}
            ),
        ):
            store = await get_session_store()

            assert isinstance(store, RedisSessionStore)

    async def test_get_session_store_falls_back_to_memory_when_redis_url_missing(self):
        """Test fallback to memory store when REDIS_URL is not configured."""
        with (
            patch('app.infrastructure.config.SESSION_STORE_TYPE', 'redis'),
            patch('app.infrastructure.config.REDIS_URL', None),
        ):
            store = await get_session_store()

            assert isinstance(store, InMemorySessionStore)

    async def test_get_session_store_falls_back_to_memory_on_redis_error(self):
        """Test fallback to memory store when Redis initialization fails."""
        mock_redis_module = MagicMock()
        mock_redis_module.from_url.side_effect = Exception('Connection failed')
        mock_redis_parent = MagicMock()
        mock_redis_parent.asyncio = mock_redis_module

        with (
            patch('app.infrastructure.config.SESSION_STORE_TYPE', 'redis'),
            patch('app.infrastructure.config.REDIS_URL', 'redis://localhost:6379/0'),
            patch.dict(
                'sys.modules', {'redis': mock_redis_parent, 'redis.asyncio': mock_redis_module}
            ),
        ):
            store = await get_session_store()

            assert isinstance(store, InMemorySessionStore)

    async def test_init_session_store_creates_global_instance(self):
        """Test that init_session_store creates global instance."""
        with (
            patch('app.infrastructure.config.SESSION_STORE_TYPE', 'memory'),
            patch('app.infrastructure.session_store._session_store', None),
        ):
            store = await init_session_store()

            assert isinstance(store, InMemorySessionStore)

    def test_get_store_returns_existing_instance(self):
        """Test that get_store returns existing global instance."""
        mock_store = InMemorySessionStore()

        with patch('app.infrastructure.session_store._session_store', mock_store):
            store = get_store()

            assert store is mock_store

    def test_get_store_raises_if_not_initialized(self):
        """Test that get_store raises RuntimeError if not initialized."""
        with (
            patch('app.infrastructure.session_store._session_store', None),
            pytest.raises(RuntimeError),
        ):
            get_store()
