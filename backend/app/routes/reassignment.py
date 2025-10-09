"""API routes for leader reassignment."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any
from uuid import UUID

from ..database import get_db
from ..models import User
from ..routes.auth import require_auth
from ..repository import get_repository
from ..services import ReassignmentService
from ..exceptions import AppException

router = APIRouter(prefix="/reassignment", tags=["reassignment"])


@router.post("/request")
async def request_reassignment(
    data: Dict[str, str],
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Request to reassign leadership of a run."""
    repo = get_repository(db)
    service = ReassignmentService(repo)

    run_id = UUID(data["run_id"])
    to_user_id = UUID(data["to_user_id"])

    return await service.request_reassignment(run_id, current_user, to_user_id)


@router.post("/{request_id}/accept")
async def accept_reassignment(
    request_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Accept a leader reassignment request."""
    repo = get_repository(db)
    service = ReassignmentService(repo)

    return await service.accept_reassignment(UUID(request_id), current_user)


@router.post("/{request_id}/decline")
async def decline_reassignment(
    request_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Decline a leader reassignment request."""
    repo = get_repository(db)
    service = ReassignmentService(repo)

    return await service.decline_reassignment(UUID(request_id), current_user)


@router.post("/{request_id}/cancel")
async def cancel_reassignment(
    request_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Cancel a pending reassignment request."""
    repo = get_repository(db)
    service = ReassignmentService(repo)

    return service.cancel_reassignment(UUID(request_id), current_user)


@router.get("/my-requests")
async def get_my_requests(
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get all pending reassignment requests for the current user."""
    repo = get_repository(db)
    service = ReassignmentService(repo)

    return service.get_pending_requests_for_user(current_user.id)


@router.get("/run/{run_id}")
async def get_run_request(
    run_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get pending reassignment request for a specific run."""
    repo = get_repository(db)
    service = ReassignmentService(repo)

    request = service.get_pending_request_for_run(UUID(run_id))
    return {"request": request}
