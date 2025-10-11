from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..routes.auth import require_auth
from ..repository import get_repository
from ..services import GroupService
from ..request_context import get_logger
from ..schemas import (
    CreateGroupRequest,
    CreateGroupResponse,
    GroupResponse,
    GroupDetailResponse,
    RunResponse,
    RegenerateTokenResponse,
    PreviewGroupResponse,
    JoinGroupResponse,
    MessageResponse,
    ToggleJoiningResponse,
)

router = APIRouter(prefix="/groups", tags=["groups"])
logger = get_logger(__name__)

@router.get("/my-groups", response_model=list[GroupResponse])
async def get_my_groups(
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get all groups the current user is a member of."""
    repo = get_repository(db)
    service = GroupService(repo)

    return service.get_user_groups(current_user)

@router.post("/create", response_model=CreateGroupResponse)
async def create_group(
    request: CreateGroupRequest,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Create a new group."""
    repo = get_repository(db)
    service = GroupService(repo)

    return service.create_group(request.name, current_user)

@router.get("/{group_id}", response_model=GroupDetailResponse)
async def get_group(
    group_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get details of a specific group."""
    repo = get_repository(db)
    service = GroupService(repo)

    return service.get_group_details(group_id, current_user)

@router.get("/{group_id}/runs", response_model=list[RunResponse])
async def get_group_runs(
    group_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get all runs for a specific group."""
    repo = get_repository(db)
    service = GroupService(repo)

    return service.get_group_runs(group_id, current_user)

@router.get("/{group_id}/runs/history", response_model=list[RunResponse])
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

    return service.get_group_completed_cancelled_runs(group_id, current_user, limit, offset)

@router.post("/{group_id}/regenerate-invite", response_model=RegenerateTokenResponse)
async def regenerate_invite_token(
    group_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Regenerate the invite token for a group."""
    repo = get_repository(db)
    service = GroupService(repo)

    return service.regenerate_invite_token(group_id, current_user)

@router.get("/preview/{invite_token}", response_model=PreviewGroupResponse)
async def preview_group_by_invite(
    invite_token: str,
    db: Session = Depends(get_db)
):
    """Preview group information by invite token without joining."""
    repo = get_repository(db)
    service = GroupService(repo)

    return service.preview_group(invite_token)

@router.post("/join/{invite_token}", response_model=JoinGroupResponse)
async def join_group_by_invite(
    invite_token: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Join a group using an invite token."""
    repo = get_repository(db)
    service = GroupService(repo)

    return service.join_group(invite_token, current_user)

@router.get("/{group_id}/members", response_model=GroupDetailResponse)
async def get_group_members(
    group_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get all members of a group with their admin status."""
    repo = get_repository(db)
    service = GroupService(repo)

    return service.get_group_members(group_id, current_user)

@router.delete("/{group_id}/members/{member_id}", response_model=MessageResponse)
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

@router.post("/{group_id}/toggle-joining", response_model=ToggleJoiningResponse)
async def toggle_group_joining(
    group_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Toggle whether a group allows joining via invite link (admin only)."""
    repo = get_repository(db)
    service = GroupService(repo)

    return service.toggle_joining_allowed(group_id, current_user)
