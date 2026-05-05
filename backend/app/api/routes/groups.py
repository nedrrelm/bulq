from fastapi import APIRouter, Depends, Query

from app.api.dependencies import (
    GroupInviteServiceDep,
    GroupManagementServiceDep,
    GroupMembershipServiceDep,
    GroupQueryServiceDep,
)
from app.api.routes.auth import require_auth
from app.api.schemas import (
    CreateGroupRequest,
    CreateGroupResponse,
    GroupDetailResponse,
    GroupResponse,
    JoinGroupResponse,
    PreviewGroupResponse,
    RegenerateTokenResponse,
    RunResponse,
    SuccessResponse,
    ToggleJoiningResponse,
)
from app.core.models import User
from app.infrastructure.request_context import get_logger

router = APIRouter(prefix='/groups', tags=['groups'])
logger = get_logger(__name__)


@router.get('/my-groups', response_model=list[GroupResponse])
async def get_my_groups(service: GroupQueryServiceDep, current_user: User = Depends(require_auth)):
    """Get all groups the current user is a member of."""
    return await service.get_user_groups(current_user)


@router.post('/create', response_model=CreateGroupResponse)
async def create_group(
    request: CreateGroupRequest,
    service: GroupManagementServiceDep,
    current_user: User = Depends(require_auth),
):
    """Create a new group."""
    return await service.create_group(request.name, current_user)


@router.get('/{group_id}', response_model=GroupDetailResponse)
async def get_group(
    group_id: str, service: GroupQueryServiceDep, current_user: User = Depends(require_auth)
):
    """Get details of a specific group."""
    return await service.get_group_details(group_id, current_user)


@router.get('/{group_id}/runs', response_model=list[RunResponse])
async def get_group_runs(
    group_id: str, service: GroupQueryServiceDep, current_user: User = Depends(require_auth)
):
    """Get all runs for a specific group."""
    return await service.get_group_runs(group_id, current_user)


@router.get('/{group_id}/runs/history', response_model=list[RunResponse])
async def get_group_completed_cancelled_runs(
    group_id: str,
    service: GroupQueryServiceDep,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_auth),
):
    """Get completed and cancelled runs for a specific group (paginated)."""
    return await service.get_group_completed_cancelled_runs(group_id, current_user, limit, offset)


@router.post('/{group_id}/regenerate-invite', response_model=RegenerateTokenResponse)
async def regenerate_invite_token(
    group_id: str, service: GroupInviteServiceDep, current_user: User = Depends(require_auth)
):
    """Regenerate the invite token for a group."""
    return await service.regenerate_invite_token(group_id, current_user)


@router.get('/preview/{invite_token}', response_model=PreviewGroupResponse)
async def preview_group_by_invite(invite_token: str, service: GroupInviteServiceDep):
    """Preview group information by invite token without joining."""
    return await service.preview_group(invite_token)


@router.post('/join/{invite_token}', response_model=JoinGroupResponse)
async def join_group_by_invite(
    invite_token: str, service: GroupInviteServiceDep, current_user: User = Depends(require_auth)
):
    """Join a group using an invite token."""
    return await service.join_group(invite_token, current_user)


@router.get('/{group_id}/members', response_model=GroupDetailResponse)
async def get_group_members(
    group_id: str, service: GroupQueryServiceDep, current_user: User = Depends(require_auth)
):
    """Get all members of a group with their admin status."""
    return await service.get_group_members(group_id, current_user)


@router.delete('/{group_id}/members/{member_id}', response_model=SuccessResponse)
async def remove_group_member(
    group_id: str,
    member_id: str,
    service: GroupMembershipServiceDep,
    current_user: User = Depends(require_auth),
):
    """Remove a member from a group (admin only)."""
    return await service.remove_member(group_id, member_id, current_user)


@router.post('/{group_id}/toggle-joining', response_model=ToggleJoiningResponse)
async def toggle_group_joining(
    group_id: str, service: GroupInviteServiceDep, current_user: User = Depends(require_auth)
):
    """Toggle whether a group allows joining via invite link (admin only)."""
    return await service.toggle_joining_allowed(group_id, current_user)


@router.post('/{group_id}/leave', response_model=SuccessResponse)
async def leave_group(
    group_id: str, service: GroupMembershipServiceDep, current_user: User = Depends(require_auth)
):
    """Leave a group."""
    return await service.leave_group(group_id, current_user)


@router.post('/{group_id}/members/{member_id}/promote', response_model=SuccessResponse)
async def promote_member_to_admin(
    group_id: str,
    member_id: str,
    service: GroupMembershipServiceDep,
    current_user: User = Depends(require_auth),
):
    """Promote a member to group admin (admin only)."""
    return await service.promote_member_to_admin(group_id, member_id, current_user)
