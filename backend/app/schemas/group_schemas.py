"""Schemas for group-related requests and responses."""

from pydantic import BaseModel, field_validator, Field
import re


class CreateGroupRequest(BaseModel):
    """Request model for creating a new group."""
    name: str = Field(min_length=2, max_length=100)

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
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
    """Summary of a run for group listings."""
    id: str
    store_name: str
    state: str


class GroupResponse(BaseModel):
    """Response model for a group."""
    id: str
    name: str
    description: str
    member_count: int
    active_runs_count: int
    completed_runs_count: int
    active_runs: list[RunSummary]
    created_at: str

    class Config:
        from_attributes = True


class CreateGroupResponse(BaseModel):
    """Response model for creating a group."""
    id: str
    name: str
    member_count: int
    active_runs_count: int
    completed_runs_count: int
    active_runs: list[RunSummary]


class RunResponse(BaseModel):
    """Response model for a run in group context."""
    id: str
    group_id: str
    store_id: str
    store_name: str
    state: str
    leader_name: str
    leader_is_removed: bool = False
    planned_on: str | None

    class Config:
        from_attributes = True


class GroupDetailResponse(BaseModel):
    """Response model for detailed group information."""
    id: str
    name: str
    invite_token: str
    is_joining_allowed: bool
    members: list[dict]  # Contains user info dicts
    is_current_user_admin: bool


class InviteTokenResponse(BaseModel):
    """Response model for invite token."""
    invite_token: str


class RegenerateTokenResponse(BaseModel):
    """Response model for regenerating invite token."""
    invite_token: str


class PreviewGroupResponse(BaseModel):
    """Response model for previewing a group."""
    id: str
    name: str
    member_count: int
    creator_name: str


class JoinGroupResponse(BaseModel):
    """Response model for joining a group."""
    message: str
    group_id: str
    group_name: str


class ToggleJoiningResponse(BaseModel):
    """Response model for toggling group joining."""
    is_joining_allowed: bool


class RemoveMemberResponse(BaseModel):
    """Response model for removing a member."""
    message: str
