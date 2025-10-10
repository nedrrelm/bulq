from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import User
from ..routes.auth import require_auth
from ..repository import get_repository
from ..services import GroupService
from pydantic import BaseModel, validator, Field
import re
from datetime import datetime
import logging

router = APIRouter(prefix="/groups", tags=["groups"])
logger = logging.getLogger(__name__)

class CreateGroupRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)

    @validator('name')
    def validate_name(cls, v):
        v = v.strip()

        if len(v) < 2:
            raise ValueError('Group name must be at least 2 characters')

        if len(v) > 100:
            raise ValueError('Group name must be at most 100 characters')

        # Allow alphanumeric, spaces, and specific special characters: - _ & '
        if not re.match(r"^[a-zA-Z0-9\s\-_&']+$", v):
            raise ValueError('Group name contains invalid characters. Use letters, numbers, spaces, and - _ & \'')

        return v

class RunSummary(BaseModel):
    id: str
    store_name: str
    state: str

class GroupResponse(BaseModel):
    id: str
    name: str
    description: str
    member_count: int
    active_runs_count: int
    completed_runs_count: int
    active_runs: List[RunSummary]
    created_at: str

    class Config:
        from_attributes = True

class RunResponse(BaseModel):
    id: str
    group_id: str
    store_id: str
    store_name: str
    state: str
    leader_name: str
    planned_on: str | None

    class Config:
        from_attributes = True

@router.get("/my-groups", response_model=List[GroupResponse])
async def get_my_groups(
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get all groups the current user is a member of."""
    repo = get_repository(db)
    service = GroupService(repo)

    group_responses = service.get_user_groups(current_user)

    # Convert to response models, using current time for created_at since it's not in the model yet
    return [
        GroupResponse(
            id=group["id"],
            name=group["name"],
            description=group["description"],
            member_count=group["member_count"],
            active_runs_count=group["active_runs_count"],
            completed_runs_count=group["completed_runs_count"],
            active_runs=[RunSummary(**run) for run in group["active_runs"]],
            created_at=datetime.now().isoformat()
        )
        for group in group_responses
    ]

@router.post("/create")
async def create_group(
    request: CreateGroupRequest,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Create a new group."""
    repo = get_repository(db)
    service = GroupService(repo)

    return service.create_group(request.name, current_user)

@router.get("/{group_id}")
async def get_group(
    group_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get details of a specific group."""
    repo = get_repository(db)
    service = GroupService(repo)

    return service.get_group_details(group_id, current_user)

@router.get("/{group_id}/runs", response_model=List[RunResponse])
async def get_group_runs(
    group_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get all runs for a specific group."""
    repo = get_repository(db)
    service = GroupService(repo)

    run_responses = service.get_group_runs(group_id, current_user)
    return [RunResponse(**run) for run in run_responses]

@router.get("/{group_id}/runs/history", response_model=List[RunResponse])
async def get_group_completed_cancelled_runs(
    group_id: str,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get completed and cancelled runs for a specific group (paginated)."""
    repo = get_repository(db)
    service = GroupService(repo)

    run_responses = service.get_group_completed_cancelled_runs(group_id, current_user, limit, offset)
    return [RunResponse(**run) for run in run_responses]

@router.post("/{group_id}/regenerate-invite")
async def regenerate_invite_token(
    group_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Regenerate the invite token for a group."""
    repo = get_repository(db)
    service = GroupService(repo)

    return service.regenerate_invite_token(group_id, current_user)

@router.get("/preview/{invite_token}")
async def preview_group_by_invite(
    invite_token: str,
    db: Session = Depends(get_db)
):
    """Preview group information by invite token without joining."""
    repo = get_repository(db)
    service = GroupService(repo)

    return service.preview_group(invite_token)

@router.post("/join/{invite_token}")
async def join_group_by_invite(
    invite_token: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Join a group using an invite token."""
    repo = get_repository(db)
    service = GroupService(repo)

    return service.join_group(invite_token, current_user)

@router.get("/{group_id}/members")
async def get_group_members(
    group_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get all members of a group with their admin status."""
    repo = get_repository(db)
    service = GroupService(repo)

    return service.get_group_members(group_id, current_user)

@router.delete("/{group_id}/members/{member_id}")
async def remove_group_member(
    group_id: str,
    member_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Remove a member from a group (admin only)."""
    repo = get_repository(db)
    service = GroupService(repo)

    return service.remove_member(group_id, member_id, current_user)

@router.post("/{group_id}/toggle-joining")
async def toggle_group_joining(
    group_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Toggle whether a group allows joining via invite link (admin only)."""
    repo = get_repository(db)
    service = GroupService(repo)

    return service.toggle_joining_allowed(group_id, current_user)
