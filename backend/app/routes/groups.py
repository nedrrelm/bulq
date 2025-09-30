from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import Group, User
from ..routes.auth import require_auth
from ..repository import get_repository
from pydantic import BaseModel
from datetime import datetime
import uuid

router = APIRouter(prefix="/groups", tags=["groups"])

class GroupResponse(BaseModel):
    id: str
    name: str
    description: str
    member_count: int
    created_at: str

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
        group_responses.append(GroupResponse(
            id=str(group.id),
            name=group.name,
            description=f"Group created by {group.creator.name}" if group.creator else "Group",
            member_count=len(group.members),
            created_at=datetime.now().isoformat()  # Using current time for now since we don't have created_at in model
        ))

    return group_responses