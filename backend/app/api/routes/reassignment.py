"""API routes for leader reassignment."""

from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.dependencies import ReassignmentServiceDep
from app.api.routes.auth import require_auth
from app.api.schemas import (
    MyRequestsResponse,
    ReassignmentRequestModel,
    ReassignmentResponse,
    RunRequestResponse,
)
from app.core.models import User

router = APIRouter(prefix='/reassignment', tags=['reassignment'])


@router.post('/request', response_model=ReassignmentResponse)
async def request_reassignment(
    data: ReassignmentRequestModel,
    service: ReassignmentServiceDep,
    current_user: User = Depends(require_auth),
):
    """Request to reassign leadership of a run."""
    run_id = UUID(data.run_id)
    to_user_id = UUID(data.to_user_id)

    return await service.request_reassignment(run_id, current_user, to_user_id)


@router.post('/{request_id}/accept', response_model=ReassignmentResponse)
async def accept_reassignment(
    request_id: str, service: ReassignmentServiceDep, current_user: User = Depends(require_auth)
):
    """Accept a leader reassignment request."""
    return await service.accept_reassignment(UUID(request_id), current_user)


@router.post('/{request_id}/decline', response_model=ReassignmentResponse)
async def decline_reassignment(
    request_id: str, service: ReassignmentServiceDep, current_user: User = Depends(require_auth)
):
    """Decline a leader reassignment request."""
    return await service.decline_reassignment(UUID(request_id), current_user)


@router.post('/{request_id}/cancel', response_model=ReassignmentResponse)
async def cancel_reassignment(
    request_id: str, service: ReassignmentServiceDep, current_user: User = Depends(require_auth)
):
    """Cancel a pending reassignment request."""
    return service.cancel_reassignment(UUID(request_id), current_user)


@router.get('/my-requests', response_model=MyRequestsResponse)
async def get_my_requests(
    service: ReassignmentServiceDep, current_user: User = Depends(require_auth)
):
    """Get all pending reassignment requests for the current user."""
    return service.get_pending_requests_for_user(current_user.id)


@router.get('/run/{run_id}', response_model=RunRequestResponse)
async def get_run_request(
    run_id: str, service: ReassignmentServiceDep, current_user: User = Depends(require_auth)
):
    """Get pending reassignment request for a specific run."""
    request = service.get_pending_request_for_run(UUID(run_id))
    return RunRequestResponse(request=request)
