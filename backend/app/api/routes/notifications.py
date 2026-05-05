"""API routes for notifications."""

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import NotificationServiceDep
from app.api.routes.auth import require_auth
from app.api.schemas import (
    MarkAllReadResponse,
    NotificationResponse,
    SuccessResponse,
    UnreadCountResponse,
)
from app.core.models import User

router = APIRouter(prefix='/notifications', tags=['notifications'])


@router.get('', response_model=list[NotificationResponse])
async def get_notifications(
    service: NotificationServiceDep,
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_auth),
):
    """Get notifications for current user (paginated, max 100 per page)."""
    return await service.get_user_notifications(current_user, limit, offset)


@router.get('/unread', response_model=list[NotificationResponse])
async def get_unread_notifications(
    service: NotificationServiceDep, current_user: User = Depends(require_auth)
):
    """Get all unread notifications for current user."""
    return await service.get_unread_notifications(current_user)


@router.get('/count', response_model=UnreadCountResponse)
async def get_unread_count(
    service: NotificationServiceDep, current_user: User = Depends(require_auth)
):
    """Get count of unread notifications for current user."""
    count = await service.get_unread_count(current_user)
    return UnreadCountResponse(count=count)


@router.post('/{notification_id}/mark-read', response_model=SuccessResponse)
async def mark_notification_read(
    notification_id: str,
    service: NotificationServiceDep,
    current_user: User = Depends(require_auth),
):
    """Mark a notification as read."""
    return await service.mark_as_read(notification_id, current_user)


@router.post('/mark-all-read', response_model=MarkAllReadResponse)
async def mark_all_notifications_read(
    service: NotificationServiceDep, current_user: User = Depends(require_auth)
):
    """Mark all notifications as read for current user."""
    return await service.mark_all_as_read(current_user)
