"""Schemas for authentication-related requests and responses."""

import re

from pydantic import BaseModel, Field, field_validator


class UserRegister(BaseModel):
    """Request model for user registration."""

    name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=6, max_length=100)

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Invalid email format')
        return v.lower()


class UserLogin(BaseModel):
    """Request model for user login."""

    email: str
    password: str


class UserResponse(BaseModel):
    """Response model for user information."""

    id: str
    name: str
    email: str
    is_admin: bool = False
