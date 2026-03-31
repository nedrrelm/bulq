from fastapi import APIRouter, Depends

from app.api.dependencies import DistributionServiceDep
from app.api.routes.auth import require_auth
from app.api.schemas import (
    DistributionUser,
    StateChangeResponse,
    SuccessResponse,
)
from app.core.models import User
from app.utils.validation import validate_uuid

router = APIRouter(prefix='/distribution', tags=['distribution'])


@router.get('/{run_id}', response_model=list[DistributionUser])
async def get_distribution_data(
    run_id: str, service: DistributionServiceDep, current_user: User = Depends(require_auth)
):
    """Get distribution data aggregated by user."""
    run_uuid = validate_uuid(run_id, 'Run')
    return service.get_distribution_summary(run_uuid, current_user)


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

    result = service.mark_picked_up(run_uuid, bid_uuid, current_user)
    return result


@router.post('/{run_id}/complete', response_model=StateChangeResponse)
async def complete_distribution(
    run_id: str, service: DistributionServiceDep, current_user: User = Depends(require_auth)
):
    """Complete distribution - transition from distributing to completed state (leader only)."""
    run_uuid = validate_uuid(run_id, 'Run')
    # Complete distribution via service (events are emitted by service)
    return service.complete_distribution(run_uuid, current_user)
