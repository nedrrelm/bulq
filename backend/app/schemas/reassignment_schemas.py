"""Schemas for leader reassignment requests and responses."""

from pydantic import BaseModel


class ReassignmentRequestModel(BaseModel):
    """Request model for creating a reassignment request."""
    run_id: str
    to_user_id: str


class ReassignmentResponse(BaseModel):
    """Response model for reassignment request."""
    id: str
    run_id: str
    from_user_id: str
    to_user_id: str
    status: str
    created_at: str
    resolved_at: str | None = None


class ReassignmentDetailResponse(BaseModel):
    """Detailed response for reassignment request with user and store names."""
    id: str
    run_id: str
    from_user_id: str
    from_user_name: str
    to_user_id: str
    to_user_name: str
    store_name: str
    status: str
    created_at: str


class MyRequestsResponse(BaseModel):
    """Response model for user's sent and received reassignment requests."""
    sent: list[ReassignmentDetailResponse]
    received: list[ReassignmentDetailResponse]


class RunRequestResponse(BaseModel):
    """Response model for active reassignment request for a specific run."""
    request: ReassignmentDetailResponse | None
