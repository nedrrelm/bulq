"""Schemas for admin-related requests and responses."""

from pydantic import BaseModel


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
    verified: bool
    created_at: str | None


class VerificationToggleResponse(BaseModel):
    """Response for toggling verification status."""

    id: str
    verified: bool
    message: str
