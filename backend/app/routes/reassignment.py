"""API routes for leader reassignment."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from pydantic import BaseModel

from ..database import get_db
from ..models import User
from ..routes.auth import require_auth
from ..repository import get_repository
from ..services import ReassignmentService
from ..exceptions import AppException

router = APIRouter(prefix="/reassignment", tags=["reassignment"])

class ReassignmentRequestModel(BaseModel):
    run_id: str
    to_user_id: str

class ReassignmentResponse(BaseModel):
    id: str
    run_id: str
    from_user_id: str
    to_user_id: str
    status: str
    created_at: str
    resolved_at: str | None = None

class ReassignmentDetailResponse(BaseModel):
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
    sent: list[ReassignmentDetailResponse]
    received: list[ReassignmentDetailResponse]

class RunRequestResponse(BaseModel):
    request: ReassignmentDetailResponse | None


@router.post("/request", response_model=ReassignmentResponse)
async def request_reassignment(
    data: ReassignmentRequestModel,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Request to reassign leadership of a run."""
    repo = get_repository(db)
    service = ReassignmentService(repo)

    run_id = UUID(data.run_id)
    to_user_id = UUID(data.to_user_id)

    result = await service.request_reassignment(run_id, current_user, to_user_id)
    return ReassignmentResponse(**result)


@router.post("/{request_id}/accept", response_model=ReassignmentResponse)
async def accept_reassignment(
    request_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Accept a leader reassignment request."""
    repo = get_repository(db)
    service = ReassignmentService(repo)

    result = await service.accept_reassignment(UUID(request_id), current_user)
    return ReassignmentResponse(**result)


@router.post("/{request_id}/decline", response_model=ReassignmentResponse)
async def decline_reassignment(
    request_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Decline a leader reassignment request."""
    repo = get_repository(db)
    service = ReassignmentService(repo)

    result = await service.decline_reassignment(UUID(request_id), current_user)
    return ReassignmentResponse(**result)


@router.post("/{request_id}/cancel", response_model=ReassignmentResponse)
async def cancel_reassignment(
    request_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Cancel a pending reassignment request."""
    repo = get_repository(db)
    service = ReassignmentService(repo)

    result = service.cancel_reassignment(UUID(request_id), current_user)
    return ReassignmentResponse(**result)


@router.get("/my-requests", response_model=MyRequestsResponse)
async def get_my_requests(
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get all pending reassignment requests for the current user."""
    repo = get_repository(db)
    service = ReassignmentService(repo)

    result = service.get_pending_requests_for_user(current_user.id)
    return MyRequestsResponse(
        sent=[ReassignmentDetailResponse(**r) for r in result['sent']],
        received=[ReassignmentDetailResponse(**r) for r in result['received']]
    )


@router.get("/run/{run_id}", response_model=RunRequestResponse)
async def get_run_request(
    run_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get pending reassignment request for a specific run."""
    repo = get_repository(db)
    service = ReassignmentService(repo)

    request = service.get_pending_request_for_run(UUID(run_id))
    return RunRequestResponse(
        request=ReassignmentDetailResponse(**request) if request else None
    )
