"""Schemas for seller-related requests and responses."""

from pydantic import BaseModel, ConfigDict, Field


class CreateSellerRequest(BaseModel):
    """Request model for creating a seller profile."""

    display_name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)


class UpdateSellerRequest(BaseModel):
    """Request model for updating a seller profile."""

    display_name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)


class SellerResponse(BaseModel):
    """Full seller profile response (for owner)."""

    id: str
    user_id: str
    store_id: str
    display_name: str
    description: str | None
    invite_token: str
    is_joining_allowed: bool
    is_searchable: bool
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class SellerPublicResponse(BaseModel):
    """Public seller profile response (for non-owners)."""

    id: str
    display_name: str
    description: str | None
    is_joining_allowed: bool

    model_config = ConfigDict(from_attributes=True)


class SellerSearchResult(BaseModel):
    """Seller search result."""

    id: str
    display_name: str
    description: str | None

    model_config = ConfigDict(from_attributes=True)


class SellerPreviewResponse(BaseModel):
    """Seller preview for invite token page."""

    id: str
    display_name: str
    description: str | None
    is_joining_allowed: bool

    model_config = ConfigDict(from_attributes=True)
