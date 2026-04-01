"""Unit tests for authentication schemas."""

import pytest
from pydantic import ValidationError

from app.api.schemas.auth_schemas import (
    ChangeLanguageRequest,
    ChangeNameRequest,
    ChangePasswordRequest,
    ChangeUsernameRequest,
    UserLogin,
    UserRegister,
    UserResponse,
    UserStatsResponse,
)


class TestUserRegister:
    """Tests for UserRegister schema."""

    def test_valid_registration(self):
        """Test creating valid user registration."""
        data = {
            'name': 'John Doe',
            'username': 'johndoe',
            'password': 'password123',
        }
        schema = UserRegister(**data)
        assert schema.name == 'John Doe'
        assert schema.username == 'johndoe'
        assert schema.password == 'password123'

    def test_username_converted_to_lowercase(self):
        """Test username is converted to lowercase."""
        data = {
            'name': 'John Doe',
            'username': 'JohnDoe123',
            'password': 'password123',
        }
        schema = UserRegister(**data)
        assert schema.username == 'johndoe123'

    def test_missing_name(self):
        """Test missing name raises ValidationError."""
        data = {'username': 'johndoe', 'password': 'password123'}
        with pytest.raises(ValidationError) as exc_info:
            UserRegister(**data)
        assert 'name' in str(exc_info.value)

    def test_missing_username(self):
        """Test missing username raises ValidationError."""
        data = {'name': 'John Doe', 'password': 'password123'}
        with pytest.raises(ValidationError) as exc_info:
            UserRegister(**data)
        assert 'username' in str(exc_info.value)

    def test_missing_password(self):
        """Test missing password raises ValidationError."""
        data = {'name': 'John Doe', 'username': 'johndoe'}
        with pytest.raises(ValidationError) as exc_info:
            UserRegister(**data)
        assert 'password' in str(exc_info.value)

    def test_name_too_short(self):
        """Test name with length 0 raises ValidationError."""
        data = {'name': '', 'username': 'johndoe', 'password': 'password123'}
        with pytest.raises(ValidationError) as exc_info:
            UserRegister(**data)
        assert 'name' in str(exc_info.value)

    def test_name_too_long(self):
        """Test name exceeding max length raises ValidationError."""
        data = {
            'name': 'a' * 101,
            'username': 'johndoe',
            'password': 'password123',
        }
        with pytest.raises(ValidationError) as exc_info:
            UserRegister(**data)
        assert 'name' in str(exc_info.value)

    def test_username_too_short(self):
        """Test username shorter than 3 characters raises ValidationError."""
        data = {'name': 'John Doe', 'username': 'ab', 'password': 'password123'}
        with pytest.raises(ValidationError) as exc_info:
            UserRegister(**data)
        assert 'username' in str(exc_info.value)

    def test_username_too_long(self):
        """Test username exceeding 50 characters raises ValidationError."""
        data = {
            'name': 'John Doe',
            'username': 'a' * 51,
            'password': 'password123',
        }
        with pytest.raises(ValidationError) as exc_info:
            UserRegister(**data)
        assert 'username' in str(exc_info.value)

    def test_username_invalid_characters(self):
        """Test username with invalid characters raises ValidationError."""
        data = {
            'name': 'John Doe',
            'username': 'john.doe@example',
            'password': 'password123',
        }
        with pytest.raises(ValidationError) as exc_info:
            UserRegister(**data)
        assert 'username' in str(exc_info.value)

    def test_password_too_short(self):
        """Test password shorter than 6 characters raises ValidationError."""
        data = {'name': 'John Doe', 'username': 'johndoe', 'password': '12345'}
        with pytest.raises(ValidationError) as exc_info:
            UserRegister(**data)
        assert 'password' in str(exc_info.value)

    def test_password_too_long(self):
        """Test password exceeding 100 characters raises ValidationError."""
        data = {
            'name': 'John Doe',
            'username': 'johndoe',
            'password': 'a' * 101,
        }
        with pytest.raises(ValidationError) as exc_info:
            UserRegister(**data)
        assert 'password' in str(exc_info.value)

    def test_serialization(self):
        """Test schema serialization."""
        schema = UserRegister(name='John Doe', username='JohnDoe', password='password123')
        data = schema.model_dump()
        assert data == {
            'name': 'John Doe',
            'username': 'johndoe',  # Lowercase
            'password': 'password123',
        }


class TestUserLogin:
    """Tests for UserLogin schema."""

    def test_valid_login(self):
        """Test creating valid login request."""
        data = {'username': 'johndoe', 'password': 'password123'}
        schema = UserLogin(**data)
        assert schema.username == 'johndoe'
        assert schema.password == 'password123'

    def test_missing_username(self):
        """Test missing username raises ValidationError."""
        data = {'password': 'password123'}
        with pytest.raises(ValidationError) as exc_info:
            UserLogin(**data)
        assert 'username' in str(exc_info.value)

    def test_missing_password(self):
        """Test missing password raises ValidationError."""
        data = {'username': 'johndoe'}
        with pytest.raises(ValidationError) as exc_info:
            UserLogin(**data)
        assert 'password' in str(exc_info.value)

    def test_serialization(self):
        """Test schema serialization."""
        schema = UserLogin(username='johndoe', password='password123')
        data = schema.model_dump()
        assert data == {'username': 'johndoe', 'password': 'password123'}


class TestUserResponse:
    """Tests for UserResponse schema."""

    def test_valid_user_response(self):
        """Test creating valid user response."""
        data = {
            'id': 'user123',
            'name': 'John Doe',
            'username': 'johndoe',
            'is_admin': True,
            'dark_mode': True,
            'preferred_language': 'ru',
        }
        schema = UserResponse(**data)
        assert schema.id == 'user123'
        assert schema.name == 'John Doe'
        assert schema.username == 'johndoe'
        assert schema.is_admin is True
        assert schema.dark_mode is True
        assert schema.preferred_language == 'ru'

    def test_default_values(self):
        """Test default values are set correctly."""
        data = {'id': 'user123', 'name': 'John Doe', 'username': 'johndoe'}
        schema = UserResponse(**data)
        assert schema.is_admin is False
        assert schema.dark_mode is False
        assert schema.preferred_language == 'en'

    def test_missing_required_fields(self):
        """Test missing required fields raise ValidationError."""
        data = {'name': 'John Doe', 'username': 'johndoe'}
        with pytest.raises(ValidationError) as exc_info:
            UserResponse(**data)
        assert 'id' in str(exc_info.value)


class TestUserStatsResponse:
    """Tests for UserStatsResponse schema."""

    def test_valid_stats_response(self):
        """Test creating valid user stats response."""
        data = {
            'total_quantity_bought': 150.5,
            'total_money_spent': 1234.56,
            'runs_participated': 10,
            'runs_helped': 5,
            'runs_led': 3,
            'groups_count': 2,
        }
        schema = UserStatsResponse(**data)
        assert schema.total_quantity_bought == 150.5
        assert schema.total_money_spent == 1234.56
        assert schema.runs_participated == 10
        assert schema.runs_helped == 5
        assert schema.runs_led == 3
        assert schema.groups_count == 2

    def test_missing_fields(self):
        """Test missing required fields raise ValidationError."""
        data = {'total_quantity_bought': 150.5}
        with pytest.raises(ValidationError):
            UserStatsResponse(**data)


class TestChangePasswordRequest:
    """Tests for ChangePasswordRequest schema."""

    def test_valid_password_change(self):
        """Test creating valid password change request."""
        data = {'current_password': 'oldpass', 'new_password': 'newpass123'}
        schema = ChangePasswordRequest(**data)
        assert schema.current_password == 'oldpass'
        assert schema.new_password == 'newpass123'

    def test_new_password_too_short(self):
        """Test new password shorter than 6 characters raises ValidationError."""
        data = {'current_password': 'oldpass', 'new_password': '12345'}
        with pytest.raises(ValidationError) as exc_info:
            ChangePasswordRequest(**data)
        assert 'new_password' in str(exc_info.value)

    def test_new_password_too_long(self):
        """Test new password exceeding 100 characters raises ValidationError."""
        data = {'current_password': 'oldpass', 'new_password': 'a' * 101}
        with pytest.raises(ValidationError) as exc_info:
            ChangePasswordRequest(**data)
        assert 'new_password' in str(exc_info.value)


class TestChangeUsernameRequest:
    """Tests for ChangeUsernameRequest schema."""

    def test_valid_username_change(self):
        """Test creating valid username change request."""
        data = {'current_password': 'password123', 'new_username': 'NewUsername'}
        schema = ChangeUsernameRequest(**data)
        assert schema.current_password == 'password123'
        assert schema.new_username == 'newusername'  # Lowercase

    def test_new_username_converted_to_lowercase(self):
        """Test new username is converted to lowercase."""
        data = {'current_password': 'password123', 'new_username': 'TESTUSER'}
        schema = ChangeUsernameRequest(**data)
        assert schema.new_username == 'testuser'

    def test_new_username_too_short(self):
        """Test new username shorter than 3 characters raises ValidationError."""
        data = {'current_password': 'password123', 'new_username': 'ab'}
        with pytest.raises(ValidationError) as exc_info:
            ChangeUsernameRequest(**data)
        assert 'new_username' in str(exc_info.value)

    def test_new_username_invalid_characters(self):
        """Test new username with invalid characters raises ValidationError."""
        data = {
            'current_password': 'password123',
            'new_username': 'user@name',
        }
        with pytest.raises(ValidationError) as exc_info:
            ChangeUsernameRequest(**data)
        assert 'new_username' in str(exc_info.value)


class TestChangeNameRequest:
    """Tests for ChangeNameRequest schema."""

    def test_valid_name_change(self):
        """Test creating valid name change request."""
        data = {'current_password': 'password123', 'new_name': 'Jane Doe'}
        schema = ChangeNameRequest(**data)
        assert schema.current_password == 'password123'
        assert schema.new_name == 'Jane Doe'

    def test_new_name_too_short(self):
        """Test new name with length 0 raises ValidationError."""
        data = {'current_password': 'password123', 'new_name': ''}
        with pytest.raises(ValidationError) as exc_info:
            ChangeNameRequest(**data)
        assert 'new_name' in str(exc_info.value)

    def test_new_name_too_long(self):
        """Test new name exceeding 100 characters raises ValidationError."""
        data = {'current_password': 'password123', 'new_name': 'a' * 101}
        with pytest.raises(ValidationError) as exc_info:
            ChangeNameRequest(**data)
        assert 'new_name' in str(exc_info.value)


class TestChangeLanguageRequest:
    """Tests for ChangeLanguageRequest schema."""

    def test_valid_language_change_en(self):
        """Test creating valid language change request with 'en'."""
        data = {'language': 'en'}
        schema = ChangeLanguageRequest(**data)
        assert schema.language == 'en'

    def test_valid_language_change_ru(self):
        """Test creating valid language change request with 'ru'."""
        data = {'language': 'ru'}
        schema = ChangeLanguageRequest(**data)
        assert schema.language == 'ru'

    def test_valid_language_change_sr(self):
        """Test creating valid language change request with 'sr'."""
        data = {'language': 'sr'}
        schema = ChangeLanguageRequest(**data)
        assert schema.language == 'sr'

    def test_invalid_language_code(self):
        """Test invalid language code raises ValidationError."""
        data = {'language': 'de'}
        with pytest.raises(ValidationError) as exc_info:
            ChangeLanguageRequest(**data)
        assert 'language' in str(exc_info.value)

    def test_language_too_short(self):
        """Test language code shorter than 2 characters raises ValidationError."""
        data = {'language': 'e'}
        with pytest.raises(ValidationError) as exc_info:
            ChangeLanguageRequest(**data)
        assert 'language' in str(exc_info.value)
