"""
Tests for authentication and authorization functionality.
"""
import pytest
from app.infrastructure.auth import hash_password, verify_password, create_session, get_session, delete_session
from app.core.models import User


def test_hash_password():
    """Test password hashing"""
    password = "testpassword123"
    hashed = hash_password(password)

    assert hashed != password
    assert len(hashed) > 0
    assert hashed.startswith("$2b$")  # bcrypt hash format


def test_verify_password():
    """Test password verification"""
    password = "testpassword123"
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False
    assert verify_password("", hashed) is False


def test_verify_password_with_different_hashes():
    """Test that same password produces different hashes (salt)"""
    password = "testpassword123"
    hash1 = hash_password(password)
    hash2 = hash_password(password)

    assert hash1 != hash2
    assert verify_password(password, hash1) is True
    assert verify_password(password, hash2) is True


def test_create_session():
    """Test session creation"""
    user_id = "test-user-id-123"
    session_token = create_session(user_id)

    assert session_token is not None
    assert len(session_token) > 0

    # Verify session can be retrieved
    session = get_session(session_token)
    assert session is not None
    assert session["user_id"] == user_id


def test_create_multiple_sessions():
    """Test creating multiple sessions for same user"""
    user_id = "test-user-id-123"
    token1 = create_session(user_id)
    token2 = create_session(user_id)

    assert token1 != token2
    assert get_session(token1)["user_id"] == user_id
    assert get_session(token2)["user_id"] == user_id


def test_get_session_nonexistent():
    """Test getting non-existent session"""
    session = get_session("nonexistent-token")
    assert session is None


def test_delete_session():
    """Test session deletion"""
    user_id = "test-user-id-123"
    session_token = create_session(user_id)

    # Session should exist
    assert get_session(session_token) is not None

    # Delete session
    delete_session(session_token)

    # Session should no longer exist
    assert get_session(session_token) is None


def test_delete_nonexistent_session():
    """Test deleting non-existent session doesn't error"""
    delete_session("nonexistent-token")  # Should not raise


class TestAuthIntegration:
    """Integration tests for authentication endpoints"""

    def test_register_success(self, client):
        """Test successful user registration"""
        response = client.post("/auth/register", json={
            "name": "New Test User",
            "email": "newtest@example.com",
            "password": "password123"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Test User"
        assert data["email"] == "newtest@example.com"
        assert "id" in data
        assert "password" not in data  # Password should not be returned

    def test_register_duplicate_email(self, client):
        """Test registration with duplicate email"""
        # Register first user
        client.post("/auth/register", json={
            "name": "User One",
            "email": "duplicate@example.com",
            "password": "password123"
        })

        # Try to register with same email
        response = client.post("/auth/register", json={
            "name": "User Two",
            "email": "duplicate@example.com",
            "password": "password456"
        })

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_register_invalid_email(self, client):
        """Test registration with invalid email format"""
        response = client.post("/auth/register", json={
            "name": "Invalid Email User",
            "email": "not-an-email",
            "password": "password123"
        })

        assert response.status_code == 422  # Validation error

    def test_register_missing_fields(self, client):
        """Test registration with missing fields"""
        response = client.post("/auth/register", json={
            "email": "test@example.com"
        })

        assert response.status_code == 422

    def test_login_success(self, client):
        """Test successful login"""
        # Register user
        client.post("/auth/register", json={
            "name": "Login User",
            "email": "login@example.com",
            "password": "password123"
        })

        # Login
        response = client.post("/auth/login", json={
            "email": "login@example.com",
            "password": "password123"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "login@example.com"
        assert "session" in response.cookies

    def test_login_wrong_password(self, client):
        """Test login with wrong password"""
        # Register user
        client.post("/auth/register", json={
            "name": "Wrong Password User",
            "email": "wrongpw@example.com",
            "password": "correctpassword"
        })

        # Try to login with wrong password
        response = client.post("/auth/login", json={
            "email": "wrongpw@example.com",
            "password": "wrongpassword"
        })

        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user"""
        response = client.post("/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "password123"
        })

        assert response.status_code == 401

    def test_logout(self, client):
        """Test logout"""
        # Register and login
        client.post("/auth/register", json={
            "name": "Logout User",
            "email": "logout@example.com",
            "password": "password123"
        })
        login_response = client.post("/auth/login", json={
            "email": "logout@example.com",
            "password": "password123"
        })

        session_cookie = login_response.cookies.get("session")

        # Logout
        response = client.post("/auth/logout")
        assert response.status_code == 200

        # Try to access protected endpoint with old session
        response = client.get("/auth/me", cookies={"session": session_cookie})
        assert response.status_code == 401

    def test_get_current_user(self, client):
        """Test getting current user info"""
        # Register and login
        client.post("/auth/register", json={
            "name": "Current User",
            "email": "current@example.com",
            "password": "password123"
        })
        login_response = client.post("/auth/login", json={
            "email": "current@example.com",
            "password": "password123"
        })

        # Get current user
        response = client.get("/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Current User"
        assert data["email"] == "current@example.com"

    def test_get_current_user_without_auth(self, client):
        """Test getting current user without authentication"""
        response = client.get("/auth/me")
        assert response.status_code == 401

    def test_session_persistence_across_requests(self, client):
        """Test that session persists across multiple requests"""
        # Register and login
        client.post("/auth/register", json={
            "name": "Session User",
            "email": "session@example.com",
            "password": "password123"
        })
        client.post("/auth/login", json={
            "email": "session@example.com",
            "password": "password123"
        })

        # Make multiple authenticated requests
        response1 = client.get("/auth/me")
        response2 = client.get("/auth/me")
        response3 = client.get("/auth/me")

        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response3.status_code == 200

        # All should return same user
        assert response1.json()["email"] == "test@example.com"
        assert response2.json()["email"] == "test@example.com"
        assert response3.json()["email"] == "test@example.com"
