"""Schemas for tag-related requests and responses."""

from pydantic import BaseModel, Field


class TagBriefResponse(BaseModel):
    """Brief tag info for embedding in product responses."""

    id: str
    value: str
    type: str


class TagResponse(BaseModel):
    """Full tag response."""

    id: str
    value: str
    type: str
    verified: bool
    created_at: str | None


class TagDetailResponse(BaseModel):
    """Tag detail with associated products."""

    id: str
    value: str
    type: str
    verified: bool
    products: list[dict]
    product_count: int


class TagSearchResult(BaseModel):
    """Search result for a tag."""

    id: str
    value: str
    type: str
    product_count: int


class CreateTagRequest(BaseModel):
    """Request model for creating a new tag."""

    value: str = Field(..., min_length=1, max_length=255)
    type: str = Field(..., min_length=1, max_length=50)


class AddTagToProductRequest(BaseModel):
    """Request model for adding a tag to a product."""

    tag_id: str


class AdminTagResponse(BaseModel):
    """Admin tag response with product count."""

    id: str
    value: str
    type: str
    verified: bool
    product_count: int
    created_at: str | None


class UpdateTagRequest(BaseModel):
    """Request model for updating a tag."""

    value: str = Field(..., min_length=1, max_length=255)
    type: str = Field(..., min_length=1, max_length=50)
