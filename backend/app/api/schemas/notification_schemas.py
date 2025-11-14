"""Schemas for notification-related requests and responses."""

from typing import Any

from pydantic import BaseModel, Field


class NotificationResponse(BaseModel):
    """Response model for a single notification."""

    id: str
    type: str
    data: dict
    read: bool
    created_at: str


class UnreadCountResponse(BaseModel):
    """Response model for unread notification count."""

    count: int


class MarkAllReadResponse(BaseModel):
    """Response model for marking all notifications as read."""

    success: bool = True
    code: str  # Success code for frontend localization
    count: int
    details: dict[str, Any] = Field(default_factory=dict)
