"""API routes for leader reassignment."""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.routes.auth import require_auth
from app.api.schemas import (
    MyRequestsResponse,
    ReassignmentRequestModel,
    ReassignmentResponse,
    RunRequestResponse,
)
from app.core.models import User
from app.infrastructure.database import get_db
from app.services import ReassignmentService

router = APIRouter(prefix='/reassignment', tags=['reassignment'])


@router.post('/request', response_model=ReassignmentResponse)
async def request_reassignment(
    data: ReassignmentRequestModel,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Request to reassign leadership of a run."""
    service = ReassignmentService(db)

    run_id = UUID(data.run_id)
    to_user_id = UUID(data.to_user_id)

    return await service.request_reassignment(run_id, current_user, to_user_id)


@router.post('/{request_id}/accept', response_model=ReassignmentResponse)
async def accept_reassignment(
    request_id: str, current_user: User = Depends(require_auth), db: Session = Depends(get_db)
):
    """Accept a leader reassignment request."""
    service = ReassignmentService(db)
    return await service.accept_reassignment(UUID(request_id), current_user)


@router.post('/{request_id}/decline', response_model=ReassignmentResponse)
async def decline_reassignment(
    request_id: str, current_user: User = Depends(require_auth), db: Session = Depends(get_db)
):
    """Decline a leader reassignment request."""
    service = ReassignmentService(db)
    return await service.decline_reassignment(UUID(request_id), current_user)


@router.post('/{request_id}/cancel', response_model=ReassignmentResponse)
async def cancel_reassignment(
    request_id: str, current_user: User = Depends(require_auth), db: Session = Depends(get_db)
):
    """Cancel a pending reassignment request."""
    service = ReassignmentService(db)
    return service.cancel_reassignment(UUID(request_id), current_user)


@router.get('/my-requests', response_model=MyRequestsResponse)
async def get_my_requests(
    current_user: User = Depends(require_auth), db: Session = Depends(get_db)
):
    """Get all pending reassignment requests for the current user."""
    service = ReassignmentService(db)
    return service.get_pending_requests_for_user(current_user.id)


@router.get('/run/{run_id}', response_model=RunRequestResponse)
async def get_run_request(
    run_id: str, current_user: User = Depends(require_auth), db: Session = Depends(get_db)
):
    """Get pending reassignment request for a specific run."""
    service = ReassignmentService(db)
    request = service.get_pending_request_for_run(UUID(run_id))
    return RunRequestResponse(request=request)
