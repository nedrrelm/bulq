"""Schemas for authentication-related requests and responses."""

import re

from pydantic import BaseModel, Field, field_validator


class UserRegister(BaseModel):
    """Request model for user registration."""

    name: str = Field(min_length=1, max_length=100)
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=100)

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username format."""
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, hyphens, and underscores')
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
