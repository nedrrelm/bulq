"""Schemas for admin-related requests and responses."""

from pydantic import BaseModel, Field


class AdminUserResponse(BaseModel):
    """Admin view of user information."""

    id: str
    name: str
    email: str
    verified: bool
    is_admin: bool
    created_at: str | None


class AdminProductResponse(BaseModel):
    """Admin view of product information."""

    id: str
    name: str
    brand: str | None
    unit: str | None
    verified: bool
    created_at: str | None


class AdminStoreResponse(BaseModel):
    """Admin view of store information."""

    id: str
    name: str
    address: str | None
    chain: str | None
    verified: bool
    created_at: str | None


class VerificationToggleResponse(BaseModel):
    """Response for toggling verification status."""

    id: str
    verified: bool
    message: str


# Update/Edit Request Schemas


class UpdateProductRequest(BaseModel):
    """Request to update product fields."""

    name: str = Field(..., min_length=1, max_length=255, description="Product name")
    brand: str | None = Field(None, max_length=255, description="Product brand")
    unit: str | None = Field(None, max_length=50, description="Product unit")


class UpdateStoreRequest(BaseModel):
    """Request to update store fields."""

    name: str
    address: str | None = None
    chain: str | None = None
    opening_hours: dict | None = None


class UpdateUserRequest(BaseModel):
    """Request to update user fields."""

    name: str
    email: str
    is_admin: bool
    verified: bool


# Merge Response Schema


class MergeResponse(BaseModel):
    """Response for merge operations."""

    message: str
    source_id: str
    target_id: str
    affected_records: int


# Delete Response Schema


class DeleteResponse(BaseModel):
    """Response for delete operations."""

    message: str
    deleted_id: str
