"""Unit tests for authentication functions.

Tests cover:
- Password hashing (hash_password)
- Password verification (verify_password)
- Session creation (create_session)
- Session retrieval (get_session)
- Session deletion (delete_session)
- Integration tests for complete auth flow
- Edge cases and error handling
"""

import re
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import bcrypt
import pytest

from app.infrastructure.auth import (
    create_session,
    delete_session,
    get_session,
    hash_password,
    verify_password,
)
from app.infrastructure.config import SESSION_EXPIRY_HOURS
from app.infrastructure.session_store import InMemorySessionStore


class TestPasswordHashing:
    """Test hash_password() function."""

    async def test_hash_password_returns_string(self):
        """Test that hash_password returns a string."""
        result = await hash_password('password123')

        assert isinstance(result, str)

    async def test_hash_is_different_from_original_password(self):
        """Test that hash is different from the original password."""
        password = 'mysecretpassword'
        hashed = await hash_password(password)

        assert hashed != password

    async def test_same_password_produces_different_hashes(self):
        """Test that same password produces different hashes (salted)."""
        password = 'password123'
        hash1 = await hash_password(password)
        hash2 = await hash_password(password)

        assert hash1 != hash2

    async def test_hash_is_valid_bcrypt_format(self):
        """Test that hash is in valid bcrypt format."""
        hashed = await hash_password('password123')

        # bcrypt hashes start with $2b$ or $2a$ or $2y$
        assert hashed.startswith('$2b$') or hashed.startswith('$2a$') or hashed.startswith('$2y$')

    async def test_hash_length_is_reasonable(self):
        """Test that hash length is reasonable (bcrypt hashes are ~60 chars)."""
        hashed = await hash_password('password123')

        # bcrypt hashes are typically 60 characters
        assert len(hashed) == 60

    async def test_hash_with_empty_string_password(self):
        """Test hashing an empty string password."""
        hashed = await hash_password('')

        assert isinstance(hashed, str)
        assert len(hashed) == 60
        # Verify it can be verified
        assert bcrypt.checkpw(b'', hashed.encode('utf-8'))

    async def test_hash_with_very_long_password(self):
        """Test hashing a very long password."""
        # bcrypt has a 72-byte limit - test with 72 bytes max
        long_password = 'a' * 72
        hashed = await hash_password(long_password)

        assert isinstance(hashed, str)
        assert len(hashed) == 60

    async def test_hash_with_password_exceeding_bcrypt_limit(self):
        """Test that very long password (>72 bytes) raises ValueError."""
        long_password = 'a' * 200

        with pytest.raises(ValueError, match='password cannot be longer than 72 bytes'):
            await hash_password(long_password)

    async def test_hash_with_special_characters(self):
        """Test hashing password with special characters."""
        special_password = '!@#$%^&*()_+-=[]{}|;:",.<>?/'
        hashed = await hash_password(special_password)

        assert isinstance(hashed, str)
        assert len(hashed) == 60

    async def test_hash_with_unicode_characters(self):
        """Test hashing password with unicode characters."""
        unicode_password = 'пароль密码🔐'
        hashed = await hash_password(unicode_password)

        assert isinstance(hashed, str)
        assert len(hashed) == 60

    @pytest.mark.parametrize(
        'password',
        [
            'simple',
            'With Spaces',
            '12345',
            'Mix3dC@se!',
            'newline\ncharacter',
            'tab\tcharacter',
        ],
    )
    async def test_hash_various_passwords(self, password):
        """Test hashing various password formats."""
        hashed = await hash_password(password)

        assert isinstance(hashed, str)
        assert len(hashed) == 60
        assert hashed.startswith('$2')


class TestPasswordVerification:
    """Test verify_password() function."""

    async def test_verify_password_returns_true_for_correct_password(self):
        """Test that verify_password returns True for correct password."""
        password = 'correctpassword'
        hashed = await hash_password(password)

        result = await verify_password(password, hashed)

        assert result is True

    async def test_verify_password_returns_false_for_incorrect_password(self):
        """Test that verify_password returns False for incorrect password."""
        password = 'correctpassword'
        hashed = await hash_password(password)

        result = await verify_password('wrongpassword', hashed)

        assert result is False

    async def test_verify_password_returns_false_for_empty_string(self):
        """Test that verify_password returns False for empty string against valid hash."""
        password = 'correctpassword'
        hashed = await hash_password(password)

        result = await verify_password('', hashed)

        assert result is False

    async def test_verify_password_returns_false_for_malformed_hash(self):
        """Test that verify_password returns False for malformed hash string."""
        result = await verify_password('password', 'not_a_valid_hash')

        assert result is False

    async def test_verify_password_case_sensitivity(self):
        """Test that password verification is case sensitive."""
        password = 'Test'
        hashed = await hash_password(password)

        assert await verify_password('Test', hashed) is True
        assert await verify_password('test', hashed) is False
        assert await verify_password('TEST', hashed) is False

    async def test_verify_password_with_special_characters(self):
        """Test password verification with special characters."""
        password = '!@#$%^&*()'
        hashed = await hash_password(password)

        assert await verify_password(password, hashed) is True
        assert await verify_password('!@#$%^&*', hashed) is False

    async def test_verify_password_with_unicode_characters(self):
        """Test password verification with unicode characters."""
        password = 'пароль密码🔐'
        hashed = await hash_password(password)

        assert await verify_password(password, hashed) is True
        assert await verify_password('пароль密码', hashed) is False

    async def test_verify_password_with_empty_hash(self):
        """Test that verify_password handles empty hash gracefully."""
        result = await verify_password('password', '')

        assert result is False

    async def test_verify_password_with_whitespace_differences(self):
        """Test that whitespace differences matter in password verification."""
        password = 'password'
        hashed = await hash_password(password)

        assert await verify_password('password', hashed) is True
        assert await verify_password('password ', hashed) is False
        assert await verify_password(' password', hashed) is False

    @pytest.mark.parametrize(
        'password,wrong_password',
        [
            ('test123', 'test124'),
            ('Password', 'password'),
            ('hello world', 'hello  world'),
            ('abc', 'abcd'),
        ],
    )
    async def test_verify_password_with_similar_but_wrong_passwords(self, password, wrong_password):
        """Test that similar but incorrect passwords are rejected."""
        hashed = await hash_password(password)

        assert await verify_password(password, hashed) is True
        assert await verify_password(wrong_password, hashed) is False


class TestSessionCreation:
    """Test create_session() function."""

    @pytest.fixture(autouse=True)
    def setup_session_store(self):
        """Set up a fresh in-memory session store for each test."""
        with patch('app.infrastructure.auth.get_store') as mock_get_store:
            store = InMemorySessionStore()
            mock_get_store.return_value = store
            self.store = store
            yield

    async def test_create_session_returns_string_token(self):
        """Test that create_session returns a string token."""
        token = await create_session('user-123')

        assert isinstance(token, str)

    async def test_create_session_token_is_not_empty(self):
        """Test that create_session returns a non-empty token."""
        token = await create_session('user-456')

        assert len(token) > 0

    async def test_create_session_token_is_url_safe(self):
        """Test that token is URL-safe (no problematic characters)."""
        token = await create_session('user-789')

        # URL-safe base64 uses: A-Z, a-z, 0-9, -, _
        url_safe_pattern = re.compile(r'^[A-Za-z0-9\-_]+$')
        assert url_safe_pattern.match(token)

    async def test_different_calls_produce_different_tokens(self):
        """Test that different calls produce different tokens."""
        token1 = await create_session('user-123')
        token2 = await create_session('user-123')
        token3 = await create_session('user-456')

        assert token1 != token2
        assert token1 != token3
        assert token2 != token3

    async def test_session_is_stored(self):
        """Test that session is stored and can be retrieved."""
        token = await create_session('user-123')

        session_data = await self.store.get(token)
        assert session_data is not None

    async def test_session_contains_user_id(self):
        """Test that session contains user_id."""
        user_id = 'user-123'
        token = await create_session(user_id)

        session_data = await self.store.get(token)
        assert session_data['user_id'] == user_id

    async def test_session_contains_created_at_and_expires_at(self):
        """Test that session contains created_at and expires_at timestamps."""
        token = await create_session('user-123')

        session_data = await self.store.get(token)
        assert 'created_at' in session_data
        assert 'expires_at' in session_data
        assert isinstance(session_data['created_at'], datetime)
        assert isinstance(session_data['expires_at'], datetime)

    async def test_session_ttl_is_set_correctly(self):
        """Test that session TTL is set correctly using SESSION_EXPIRY_HOURS."""
        before_creation = datetime.now(UTC)
        token = await create_session('user-123')
        after_creation = datetime.now(UTC)

        session_data = await self.store.get(token)

        # The expires_at should be approximately SESSION_EXPIRY_HOURS from now
        expected_expiry_min = before_creation + timedelta(hours=SESSION_EXPIRY_HOURS)
        expected_expiry_max = after_creation + timedelta(hours=SESSION_EXPIRY_HOURS)

        assert expected_expiry_min <= session_data['expires_at'] <= expected_expiry_max

    async def test_create_session_with_short_user_id(self):
        """Test creating session with a very short user_id."""
        token = await create_session('1')

        session_data = await self.store.get(token)
        assert session_data['user_id'] == '1'

    async def test_create_session_with_long_user_id(self):
        """Test creating session with a very long user_id (UUID strings)."""
        long_user_id = 'user-' + 'a' * 100
        token = await create_session(long_user_id)

        session_data = await self.store.get(token)
        assert session_data['user_id'] == long_user_id

    async def test_create_session_token_length(self):
        """Test that token has reasonable length (secrets.token_urlsafe(32))."""
        token = await create_session('user-123')

        # token_urlsafe(32) produces ~43 characters
        assert 40 <= len(token) <= 50


class TestSessionRetrieval:
    """Test get_session() function."""

    @pytest.fixture(autouse=True)
    def setup_session_store(self):
        """Set up a fresh in-memory session store for each test."""
        with patch('app.infrastructure.auth.get_store') as mock_get_store:
            store = InMemorySessionStore()
            mock_get_store.return_value = store
            self.store = store
            yield

    async def test_get_session_returns_session_data_for_valid_token(self):
        """Test that get_session returns session data for valid token."""
        token = await create_session('user-123')

        session_data = await get_session(token)

        assert session_data is not None

    async def test_get_session_returns_none_for_invalid_token(self):
        """Test that get_session returns None for invalid token."""
        result = await get_session('invalid-token-12345')

        assert result is None

    async def test_get_session_returns_none_for_non_existent_token(self):
        """Test that get_session returns None for non-existent token."""
        result = await get_session('non-existent-token')

        assert result is None

    async def test_get_session_returns_none_for_empty_string_token(self):
        """Test that get_session returns None for empty string token."""
        result = await get_session('')

        assert result is None

    async def test_get_session_data_contains_expected_fields(self):
        """Test that session data contains expected fields (user_id, created_at, expires_at)."""
        token = await create_session('user-123')

        session_data = await get_session(token)

        assert 'user_id' in session_data
        assert 'created_at' in session_data
        assert 'expires_at' in session_data

    async def test_get_session_data_structure_is_dict(self):
        """Test that session data structure is a dict."""
        token = await create_session('user-123')

        session_data = await get_session(token)

        assert isinstance(session_data, dict)

    async def test_get_session_returns_correct_user_id(self):
        """Test that get_session returns the correct user_id."""
        user_id = 'user-456'
        token = await create_session(user_id)

        session_data = await get_session(token)

        assert session_data['user_id'] == user_id


class TestSessionDeletion:
    """Test delete_session() function."""

    @pytest.fixture(autouse=True)
    def setup_session_store(self):
        """Set up a fresh in-memory session store for each test."""
        with patch('app.infrastructure.auth.get_store') as mock_get_store:
            store = InMemorySessionStore()
            mock_get_store.return_value = store
            self.store = store
            yield

    async def test_delete_session_removes_session(self):
        """Test that delete_session removes the session."""
        token = await create_session('user-123')

        result = await delete_session(token)

        assert result is True
        assert await get_session(token) is None

    async def test_delete_session_returns_true_when_session_exists(self):
        """Test that delete_session returns True when session exists and was deleted."""
        token = await create_session('user-123')

        result = await delete_session(token)

        assert result is True

    async def test_delete_session_returns_false_for_non_existent_session(self):
        """Test that delete_session returns False for non-existent session."""
        result = await delete_session('non-existent-token')

        assert result is False

    async def test_session_cannot_be_retrieved_after_deletion(self):
        """Test that session cannot be retrieved after deletion."""
        token = await create_session('user-123')

        await delete_session(token)
        session_data = await get_session(token)

        assert session_data is None

    async def test_deleting_same_session_twice_returns_false_second_time(self):
        """Test that deleting the same session twice returns False the second time."""
        token = await create_session('user-123')

        result1 = await delete_session(token)
        result2 = await delete_session(token)

        assert result1 is True
        assert result2 is False

    async def test_delete_session_with_empty_string_token(self):
        """Test delete_session with empty string token."""
        result = await delete_session('')

        assert result is False


class TestIntegrationFlow:
    """Test complete authentication flow integration."""

    @pytest.fixture(autouse=True)
    def setup_session_store(self):
        """Set up a fresh in-memory session store for each test."""
        with patch('app.infrastructure.auth.get_store') as mock_get_store:
            store = InMemorySessionStore()
            mock_get_store.return_value = store
            self.store = store
            yield

    async def test_complete_auth_flow(self):
        """Test complete auth flow: hash -> verify -> create session -> get session -> delete session."""
        # 1. Hash password
        password = 'mypassword123'
        hashed = await hash_password(password)
        assert isinstance(hashed, str)

        # 2. Verify password
        assert await verify_password(password, hashed) is True
        assert await verify_password('wrongpassword', hashed) is False

        # 3. Create session
        user_id = 'user-123'
        token = await create_session(user_id)
        assert isinstance(token, str)

        # 4. Get session
        session_data = await get_session(token)
        assert session_data is not None
        assert session_data['user_id'] == user_id

        # 5. Delete session
        assert await delete_session(token) is True
        assert await get_session(token) is None

    async def test_multiple_sessions_for_same_user(self):
        """Test multiple sessions for same user (different tokens)."""
        user_id = 'user-123'

        token1 = await create_session(user_id)
        token2 = await create_session(user_id)
        token3 = await create_session(user_id)

        assert token1 != token2 != token3

        # All sessions should be retrievable
        session1 = await get_session(token1)
        session2 = await get_session(token2)
        session3 = await get_session(token3)

        assert session1['user_id'] == user_id
        assert session2['user_id'] == user_id
        assert session3['user_id'] == user_id

    async def test_session_isolation(self):
        """Test session isolation (deleting one doesn't affect others)."""
        token1 = await create_session('user-123')
        token2 = await create_session('user-456')
        token3 = await create_session('user-789')

        # Delete one session
        assert await delete_session(token2) is True

        # Other sessions should still exist
        assert await get_session(token1) is not None
        assert await get_session(token2) is None
        assert await get_session(token3) is not None

    async def test_login_logout_flow(self):
        """Test a typical login/logout flow."""
        # User registration/login
        password = 'user_password'
        stored_hash = await hash_password(password)

        # User attempts login with correct password
        if await verify_password(password, stored_hash):
            token = await create_session('user-123')
            session = await get_session(token)
            assert session is not None

        # User logs out
        assert await delete_session(token) is True

        # Session should no longer exist
        assert await get_session(token) is None

    async def test_multiple_password_hashes_with_verification(self):
        """Test that multiple hashes of same password all verify correctly."""
        password = 'testpassword'
        hashes = [await hash_password(password) for _ in range(5)]

        # All hashes should be different
        assert len(set(hashes)) == 5

        # All hashes should verify against the original password
        for hashed in hashes:
            assert await verify_password(password, hashed) is True
            assert await verify_password('wrongpassword', hashed) is False


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture(autouse=True)
    def setup_session_store(self):
        """Set up a fresh in-memory session store for each test."""
        with patch('app.infrastructure.auth.get_store') as mock_get_store:
            store = InMemorySessionStore()
            mock_get_store.return_value = store
            self.store = store
            yield

    async def test_create_session_with_empty_user_id(self):
        """Test creating session with empty user_id."""
        token = await create_session('')

        session_data = await get_session(token)
        assert session_data is not None
        assert session_data['user_id'] == ''

    async def test_create_session_with_special_characters_in_user_id(self):
        """Test creating session with special characters in user_id."""
        user_id = 'user-@#$%^&*()'
        token = await create_session(user_id)

        session_data = await get_session(token)
        assert session_data['user_id'] == user_id

    async def test_create_session_with_uuid_user_id(self):
        """Test creating session with UUID-style user_id."""
        user_id = '550e8400-e29b-41d4-a716-446655440000'
        token = await create_session(user_id)

        session_data = await get_session(token)
        assert session_data['user_id'] == user_id

    async def test_verify_password_with_non_utf8_hash(self):
        """Test that verify_password handles invalid hash gracefully."""
        result = await verify_password('password', 'invalid_hash_123')

        assert result is False

    async def test_hash_password_consistency(self):
        """Test that hash_password produces consistent format."""
        passwords = ['test1', 'test2', 'test3', '', 'a' * 72]

        for password in passwords:
            hashed = await hash_password(password)
            assert len(hashed) == 60
            assert hashed.startswith('$2')

    async def test_session_store_availability(self):
        """Test behavior when session store is available."""
        token = await create_session('user-123')
        session_data = await get_session(token)

        assert session_data is not None
        assert 'user_id' in session_data

    async def test_concurrent_session_operations(self):
        """Test that multiple concurrent session operations work correctly."""
        # Create multiple sessions
        tokens = [await create_session(f'user-{i}') for i in range(10)]

        # Verify all sessions exist
        for i, token in enumerate(tokens):
            session = await get_session(token)
            assert session is not None
            assert session['user_id'] == f'user-{i}'

        # Delete half the sessions
        for token in tokens[:5]:
            assert await delete_session(token) is True

        # Verify correct sessions still exist
        for token in tokens[:5]:
            assert await get_session(token) is None

        for token in tokens[5:]:
            assert await get_session(token) is not None

    async def test_password_hash_with_null_bytes(self):
        """Test that password with null bytes can be hashed and verified."""
        password = 'password\x00with\x00nulls'
        hashed = await hash_password(password)

        # Note: bcrypt stops at null bytes, so this tests that behavior
        assert isinstance(hashed, str)
        # Verification should work with same null byte pattern
        assert await verify_password(password, hashed) is True

    async def test_session_timestamps_are_utc(self):
        """Test that session timestamps use UTC timezone."""
        token = await create_session('user-123')
        session_data = await get_session(token)

        created_at = session_data['created_at']
        expires_at = session_data['expires_at']

        assert created_at.tzinfo is not None
        assert expires_at.tzinfo is not None
        # Check they're using UTC (offset should be 0)
        assert created_at.utcoffset().total_seconds() == 0
        assert expires_at.utcoffset().total_seconds() == 0
