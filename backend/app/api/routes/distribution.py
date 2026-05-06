from fastapi import APIRouter, Depends

from app.api.dependencies import DistributionGroupServiceDep, DistributionServiceDep
from app.api.routes.auth import require_auth
from app.api.schemas import (
    AssignUserToGroupRequest,
    DistributionSummary,
    StateChangeResponse,
    SuccessResponse,
)
from app.core.models import User
from app.utils.validation import validate_uuid

router = APIRouter(prefix='/distribution', tags=['distribution'])


@router.get('/{run_id}', response_model=DistributionSummary)
async def get_distribution_data(
    run_id: str, service: DistributionServiceDep, current_user: User = Depends(require_auth)
):
    """Get distribution data organized by groups, then by user."""
    run_uuid = validate_uuid(run_id, 'Run')
    return await service.get_distribution_summary(run_uuid, current_user)


@router.post('/{run_id}/pickup/{bid_id}', response_model=SuccessResponse)
async def mark_picked_up(
    run_id: str,
    bid_id: str,
    service: DistributionServiceDep,
    current_user: User = Depends(require_auth),
):
    """Mark a product as picked up by a user."""
    run_uuid = validate_uuid(run_id, 'Run')
    bid_uuid = validate_uuid(bid_id, 'Bid')

    result = await service.mark_picked_up(run_uuid, bid_uuid, current_user)
    return result


@router.post('/{run_id}/complete', response_model=StateChangeResponse)
async def complete_distribution(
    run_id: str, service: DistributionServiceDep, current_user: User = Depends(require_auth)
):
    """Complete distribution - transition from distributing to completed state (leader only)."""
    run_uuid = validate_uuid(run_id, 'Run')
    return await service.complete_distribution(run_uuid, current_user)


@router.post('/{run_id}/groups', response_model=SuccessResponse)
async def create_distribution_group(
    run_id: str,
    service: DistributionGroupServiceDep,
    current_user: User = Depends(require_auth),
):
    """Create a new numbered distribution group for a run (leader only)."""
    run_uuid = validate_uuid(run_id, 'Run')
    return await service.create_group(run_uuid, current_user)


@router.delete('/{run_id}/groups/{group_id}', response_model=SuccessResponse)
async def delete_distribution_group(
    run_id: str,
    group_id: str,
    service: DistributionGroupServiceDep,
    current_user: User = Depends(require_auth),
):
    """Delete a distribution group (leader only, cannot delete default)."""
    run_uuid = validate_uuid(run_id, 'Run')
    group_uuid = validate_uuid(group_id, 'DistributionGroup')
    return await service.delete_group(run_uuid, group_uuid, current_user)


@router.post('/{run_id}/groups/{group_id}/assign', response_model=SuccessResponse)
async def assign_user_to_group(
    run_id: str,
    group_id: str,
    request: AssignUserToGroupRequest,
    service: DistributionGroupServiceDep,
    current_user: User = Depends(require_auth),
):
    """Assign a user to a distribution group (leader only)."""
    run_uuid = validate_uuid(run_id, 'Run')
    group_uuid = validate_uuid(group_id, 'DistributionGroup')
    user_uuid = validate_uuid(request.user_id, 'User')
    return await service.assign_user_to_group(run_uuid, group_uuid, user_uuid, current_user)


@router.post('/{run_id}/groups/{group_id}/done', response_model=SuccessResponse)
async def mark_group_done(
    run_id: str,
    group_id: str,
    service: DistributionGroupServiceDep,
    current_user: User = Depends(require_auth),
):
    """Mark all items in a distribution group as picked up (leader/helper only)."""
    run_uuid = validate_uuid(run_id, 'Run')
    group_uuid = validate_uuid(group_id, 'DistributionGroup')
    return await service.mark_group_done(run_uuid, group_uuid, current_user)
