from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.routes.auth import require_auth
from app.api.schemas import (
    DistributionUser,
    StateChangeResponse,
    SuccessResponse,
)
from app.api.websocket_manager import manager
from app.core.error_codes import INVALID_ID_FORMAT
from app.core.exceptions import BadRequestError
from app.core.models import User
from app.infrastructure.database import get_db
from app.services import DistributionService

router = APIRouter(prefix='/distribution', tags=['distribution'])


@router.get('/{run_id}', response_model=list[DistributionUser])
async def get_distribution_data(
    run_id: str, current_user: User = Depends(require_auth), db: Session = Depends(get_db)
):
    """Get distribution data aggregated by user."""
    service = DistributionService(db)

    # Validate run ID
    try:
        run_uuid = UUID(run_id)
    except ValueError as e:
        raise BadRequestError(code=INVALID_ID_FORMAT, message='Invalid ID format') from e

    return service.get_distribution_summary(run_uuid, current_user)


@router.post('/{run_id}/pickup/{bid_id}', response_model=SuccessResponse)
async def mark_picked_up(
    run_id: str,
    bid_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Mark a product as picked up by a user."""
    service = DistributionService(db)

    # Validate IDs
    try:
        run_uuid = UUID(run_id)
        bid_uuid = UUID(bid_id)
    except ValueError as e:
        raise BadRequestError(code=INVALID_ID_FORMAT, message='Invalid ID format') from e

    result = service.mark_picked_up(run_uuid, bid_uuid, current_user)

    # Broadcast distribution update to all connected clients for this run
    await manager.broadcast(
        f'run:{run_id}',
        {
            'type': 'distribution_updated',
            'data': {'run_id': run_id, 'bid_id': bid_id, 'action': 'marked_picked_up'},
        },
    )

    return result


@router.post('/{run_id}/complete', response_model=StateChangeResponse)
async def complete_distribution(
    run_id: str, current_user: User = Depends(require_auth), db: Session = Depends(get_db)
):
    """Complete distribution - transition from distributing to completed state (leader only)."""
    service = DistributionService(db)

    # Validate run ID
    try:
        run_uuid = UUID(run_id)
    except ValueError as e:
        raise BadRequestError(code=INVALID_ID_FORMAT, message='Invalid ID format') from e

    # Complete distribution via service (events are emitted by service)
    return service.complete_distribution(run_uuid, current_user)
