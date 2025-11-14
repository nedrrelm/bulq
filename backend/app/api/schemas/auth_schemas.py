"""Schemas for authentication-related requests and responses."""

from pydantic import BaseModel, Field, field_validator


class UserRegister(BaseModel):
    """Request model for user registration."""

    name: str = Field(min_length=1, max_length=100)
    username: str = Field(min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9_-]+$')
    password: str = Field(min_length=6, max_length=100)

    @field_validator('username')
    @classmethod
    def lowercase_username(cls, v: str) -> str:
        """Convert username to lowercase."""
        return v.lower()


class UserLogin(BaseModel):
    """Request model for user login."""

    username: str
    password: str


class UserResponse(BaseModel):
    """Response model for user information."""

    id: str
    name: str
    username: str
    is_admin: bool = False
    dark_mode: bool = False


class UserStatsResponse(BaseModel):
    """Response model for user statistics."""

    total_quantity_bought: float
    total_money_spent: float
    runs_participated: int
    runs_helped: int
    runs_led: int
    groups_count: int


class ChangePasswordRequest(BaseModel):
    """Request model for changing password."""

    current_password: str = Field(min_length=1, max_length=100)
    new_password: str = Field(min_length=6, max_length=100)


class ChangeUsernameRequest(BaseModel):
    """Request model for changing username."""

    current_password: str = Field(min_length=1, max_length=100)
    new_username: str = Field(min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9_-]+$')

    @field_validator('new_username')
    @classmethod
    def lowercase_new_username(cls, v: str) -> str:
        """Convert username to lowercase."""
        return v.lower()


class ChangeNameRequest(BaseModel):
    """Request model for changing display name."""

    current_password: str = Field(min_length=1, max_length=100)
    new_name: str = Field(min_length=1, max_length=100)
