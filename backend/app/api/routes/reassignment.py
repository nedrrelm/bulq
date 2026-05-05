"""API routes for leader reassignment."""

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
from app.utils.validation import validate_uuid

router = APIRouter(prefix='/reassignment', tags=['reassignment'])


@router.post('/request', response_model=ReassignmentResponse)
async def request_reassignment(
    data: ReassignmentRequestModel,
    service: ReassignmentServiceDep,
    current_user: User = Depends(require_auth),
):
    """Request to reassign leadership of a run."""
    run_id = validate_uuid(data.run_id, 'Run')
    to_user_id = validate_uuid(data.to_user_id, 'User')

    return await service.request_reassignment(run_id, current_user, to_user_id)


@router.post('/{request_id}/accept', response_model=ReassignmentResponse)
async def accept_reassignment(
    request_id: str, service: ReassignmentServiceDep, current_user: User = Depends(require_auth)
):
    """Accept a leader reassignment request."""
    return await service.accept_reassignment(validate_uuid(request_id, 'Request'), current_user)


@router.post('/{request_id}/decline', response_model=ReassignmentResponse)
async def decline_reassignment(
    request_id: str, service: ReassignmentServiceDep, current_user: User = Depends(require_auth)
):
    """Decline a leader reassignment request."""
    return await service.decline_reassignment(validate_uuid(request_id, 'Request'), current_user)


@router.post('/{request_id}/cancel', response_model=ReassignmentResponse)
async def cancel_reassignment(
    request_id: str, service: ReassignmentServiceDep, current_user: User = Depends(require_auth)
):
    """Cancel a pending reassignment request."""
    return await service.cancel_reassignment(validate_uuid(request_id, 'Request'), current_user)


@router.get('/my-requests', response_model=MyRequestsResponse)
async def get_my_requests(
    service: ReassignmentServiceDep, current_user: User = Depends(require_auth)
):
    """Get all pending reassignment requests for the current user."""
    return await service.get_pending_requests_for_user(current_user.id)


@router.get('/run/{run_id}', response_model=RunRequestResponse)
async def get_run_request(
    run_id: str, service: ReassignmentServiceDep, current_user: User = Depends(require_auth)
):
    """Get pending reassignment request for a specific run."""
    request = await service.get_pending_request_for_run(validate_uuid(run_id, 'Run'))
    return RunRequestResponse(request=request)
