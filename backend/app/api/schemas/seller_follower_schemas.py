"""Schemas for seller follower-related requests and responses."""

from pydantic import BaseModel, ConfigDict, Field


class FollowSellerRequest(BaseModel):
    """Request model for following a seller."""

    group_id: str = Field(description='ID of the group to follow with')


class SellerFollowerResponse(BaseModel):
    """Seller follower response (for seller's followers list)."""

    id: str
    seller_id: str
    group_id: str
    group_name: str
    member_count: int
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class FollowedSellerResponse(BaseModel):
    """Followed seller response (for group's followed sellers list)."""

    seller_id: str
    display_name: str
    description: str | None
    is_joining_allowed: bool

    model_config = ConfigDict(from_attributes=True)
