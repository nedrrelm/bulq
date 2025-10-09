"""API routes for notifications."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import User
from ..routes.auth import require_auth
from ..repository import get_repository
from ..services import NotificationService
from ..exceptions import NotFoundError, ForbiddenError, BadRequestError, AppException

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("")
async def get_notifications(
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get notifications for current user (paginated, max 100 per page)."""
    repo = get_repository(db)
    service = NotificationService(repo)

    try:
        notifications = service.get_user_notifications(current_user, limit, offset)
        return notifications
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/unread")
async def get_unread_notifications(
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get all unread notifications for current user."""
    repo = get_repository(db)
    service = NotificationService(repo)

    try:
        notifications = service.get_unread_notifications(current_user)
        return notifications
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/count")
async def get_unread_count(
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get count of unread notifications for current user."""
    repo = get_repository(db)
    service = NotificationService(repo)

    try:
        count = service.get_unread_count(current_user)
        return {"count": count}
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/{notification_id}/mark-read")
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Mark a notification as read."""
    repo = get_repository(db)
    service = NotificationService(repo)

    try:
        return service.mark_as_read(notification_id, current_user)
    except BadRequestError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=e.message)
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/mark-all-read")
async def mark_all_notifications_read(
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Mark all notifications as read for current user."""
    repo = get_repository(db)
    service = NotificationService(repo)

    try:
        return service.mark_all_as_read(current_user)
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
