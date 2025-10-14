"""Schemas for notification-related requests and responses."""

from pydantic import BaseModel


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

    message: str
    count: int
