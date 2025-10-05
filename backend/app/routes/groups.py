from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import Group, User, Run, Store
from ..routes.auth import require_auth
from ..repository import get_repository
from pydantic import BaseModel
from datetime import datetime
import uuid

router = APIRouter(prefix="/groups", tags=["groups"])

class CreateGroupRequest(BaseModel):
    name: str

class GroupResponse(BaseModel):
    id: str
    name: str
    description: str
    member_count: int
    active_runs_count: int
    created_at: str

    class Config:
        from_attributes = True

class RunResponse(BaseModel):
    id: str
    group_id: str
    store_id: str
    store_name: str
    state: str

    class Config:
        from_attributes = True

@router.get("/my-groups", response_model=List[GroupResponse])
async def get_my_groups(
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get all groups the current user is a member of."""
    repo = get_repository(db)

    # Get groups where the user is a member
    groups = repo.get_user_groups(current_user)

    # Convert to response format
    group_responses = []
    for group in groups:
        # Get runs for this group and count active ones
        runs = repo.get_runs_by_group(group.id)
        active_runs = [run for run in runs if run.state not in ['completed', 'cancelled']]

        group_responses.append(GroupResponse(
            id=str(group.id),
            name=group.name,
            description=f"Group created by {group.creator.name}" if group.creator else "Group",
            member_count=len(group.members),
            active_runs_count=len(active_runs),
            created_at=datetime.now().isoformat()  # Using current time for now since we don't have created_at in model
        ))

    return group_responses

@router.post("/create")
async def create_group(
    request: CreateGroupRequest,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Create a new group."""
    repo = get_repository(db)

    # Create the group
    group = repo.create_group(request.name, current_user.id)

    # Add the creator as a member
    repo.add_group_member(group.id, current_user)

    return {
        "id": str(group.id),
        "name": group.name,
        "message": "Group created successfully"
    }

@router.get("/{group_id}")
async def get_group(
    group_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get details of a specific group."""
    repo = get_repository(db)

    # Verify group ID format
    try:
        group_uuid = uuid.UUID(group_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid group ID format")

    # Get the group
    group = repo.get_group_by_id(group_uuid)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Check if user is a member of the group
    user_groups = repo.get_user_groups(current_user)
    if not any(g.id == group_uuid for g in user_groups):
        raise HTTPException(status_code=403, detail="Not a member of this group")

    return {
        "id": str(group.id),
        "name": group.name,
        "invite_token": group.invite_token
    }

@router.get("/{group_id}/runs", response_model=List[RunResponse])
async def get_group_runs(
    group_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get all runs for a specific group."""
    repo = get_repository(db)

    # Verify user is a member of the group
    try:
        group_uuid = uuid.UUID(group_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid group ID format")

    group = repo.get_group_by_id(group_uuid)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Check if user is a member of the group
    user_groups = repo.get_user_groups(current_user)
    if not any(g.id == group_uuid for g in user_groups):
        raise HTTPException(status_code=403, detail="Not a member of this group")

    # Get runs for the group
    runs = repo.get_runs_by_group(group_uuid)

    # Convert to response format with store names
    run_responses = []
    all_stores = repo.get_all_stores()
    store_lookup = {store.id: store.name for store in all_stores}

    for run in runs:
        run_responses.append(RunResponse(
            id=str(run.id),
            group_id=str(run.group_id),
            store_id=str(run.store_id),
            store_name=store_lookup.get(run.store_id, "Unknown Store"),
            state=run.state
        ))

    return run_responses

@router.post("/{group_id}/regenerate-invite")
async def regenerate_invite_token(
    group_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Regenerate the invite token for a group."""
    repo = get_repository(db)

    # Verify group ID format
    try:
        group_uuid = uuid.UUID(group_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid group ID format")

    # Get the group
    group = repo.get_group_by_id(group_uuid)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Check if user is the creator of the group
    if group.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Only the group creator can regenerate the invite token")

    # Regenerate the token
    new_token = repo.regenerate_group_invite_token(group_uuid)
    if not new_token:
        raise HTTPException(status_code=500, detail="Failed to regenerate invite token")

    return {
        "invite_token": new_token
    }

@router.get("/preview/{invite_token}")
async def preview_group_by_invite(
    invite_token: str,
    db: Session = Depends(get_db)
):
    """Preview group information by invite token without joining."""
    repo = get_repository(db)

    # Find the group by invite token
    group = repo.get_group_by_invite_token(invite_token)
    if not group:
        raise HTTPException(status_code=404, detail="Invalid invite token")

    return {
        "id": str(group.id),
        "name": group.name,
        "member_count": len(group.members),
        "creator_name": group.creator.name if group.creator else "Unknown"
    }

@router.post("/join/{invite_token}")
async def join_group_by_invite(
    invite_token: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Join a group using an invite token."""
    repo = get_repository(db)

    # Find the group by invite token
    group = repo.get_group_by_invite_token(invite_token)
    if not group:
        raise HTTPException(status_code=404, detail="Invalid invite token")

    # Check if user is already a member
    user_groups = repo.get_user_groups(current_user)
    if any(g.id == group.id for g in user_groups):
        raise HTTPException(status_code=400, detail="Already a member of this group")

    # Add user to the group
    success = repo.add_group_member(group.id, current_user)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to join group")

    return {
        "message": "Successfully joined group",
        "group_id": str(group.id),
        "group_name": group.name
    }