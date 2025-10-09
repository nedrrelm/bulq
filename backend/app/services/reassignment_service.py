"""Leader reassignment service for managing run leader transfers."""

from typing import Optional, List, Dict, Any
from uuid import UUID
import logging
import asyncio

from ..repository import AbstractRepository
from ..models import User, Run, LeaderReassignmentRequest
from ..exceptions import NotFoundError, ForbiddenError, ValidationError, ConflictError
from ..websocket_manager import manager as ws_manager

logger = logging.getLogger(__name__)


class ReassignmentService:
    """Service for handling leader reassignment requests."""

    def __init__(self, repo: AbstractRepository):
        self.repo = repo

    async def request_reassignment(self, run_id: UUID, from_user: User, to_user_id: UUID) -> Dict[str, Any]:
        """
        Create a leader reassignment request.

        Args:
            run_id: Run to reassign
            from_user: Current leader requesting reassignment
            to_user_id: User to become new leader

        Returns:
            Dict with request details

        Raises:
            NotFoundError: Run or target user not found
            ForbiddenError: Requesting user is not the leader
            ValidationError: Invalid request (same user, user not in run, etc.)
            ConflictError: Pending request already exists
        """
        # Get run
        run = self.repo.get_run_by_id(run_id)
        if not run:
            raise NotFoundError("Run", run_id)

        # Check if requesting user is the leader
        participation = self.repo.get_participation(from_user.id, run_id)
        if not participation or not participation.is_leader:
            raise ForbiddenError("Only the run leader can request reassignment")

        # Check if target user exists
        to_user = self.repo.get_user_by_id(to_user_id)
        if not to_user:
            raise NotFoundError("User", to_user_id)

        # Can't reassign to yourself
        if from_user.id == to_user_id:
            raise ValidationError("Cannot reassign leadership to yourself")

        # Check if target user is participating in the run
        target_participation = self.repo.get_participation(to_user_id, run_id)
        if not target_participation:
            raise ValidationError("Target user is not participating in this run")

        # Check for existing pending request
        existing_request = self.repo.get_pending_reassignment_for_run(run_id)
        if existing_request:
            raise ConflictError("A pending reassignment request already exists for this run")

        # Create request
        request = self.repo.create_reassignment_request(run_id, from_user.id, to_user_id)

        # Get store name
        store = self.repo.get_store_by_id(run.store_id)
        store_name = store.name if store else "Unknown Store"

        # Create notification for target user
        notification_data = {
            "run_id": str(run_id),
            "from_user_id": str(from_user.id),
            "from_user_name": from_user.name,
            "request_id": str(request.id),
            "store_name": store_name
        }
        notification = self.repo.create_notification(
            to_user_id,
            "leader_reassignment_request",
            notification_data
        )

        # Broadcast to user's WebSocket for immediate notification
        try:
            await ws_manager.broadcast(
                f"user:{to_user_id}",
                {
                    "type": "new_notification",
                    "data": {
                        "id": str(notification.id),
                        "type": "leader_reassignment_request",
                        "data": notification_data,
                        "read": False,
                        "created_at": notification.created_at.isoformat() + 'Z' if notification.created_at else None
                    }
                }
            )
        except Exception as e:
            logger.warning(f"Failed to broadcast notification to user: {e}")

        # Broadcast to run participants
        try:
            await ws_manager.broadcast(
                f"run:{run_id}",
                {
                    "type": "reassignment_requested",
                    "data": {
                        "run_id": str(run_id),
                        "from_user_id": str(from_user.id),
                        "to_user_id": str(to_user_id),
                        "request_id": str(request.id)
                    }
                }
            )
        except Exception as e:
            logger.warning(f"Failed to broadcast reassignment request: {e}")

        logger.info(
            f"Leader reassignment requested",
            extra={
                "run_id": str(run_id),
                "from_user_id": str(from_user.id),
                "to_user_id": str(to_user_id),
                "request_id": str(request.id)
            }
        )

        return {
            "id": str(request.id),
            "run_id": str(request.run_id),
            "from_user_id": str(request.from_user_id),
            "to_user_id": str(request.to_user_id),
            "status": request.status,
            "created_at": request.created_at.isoformat()
        }

    async def accept_reassignment(self, request_id: UUID, accepting_user: User) -> Dict[str, Any]:
        """
        Accept a leader reassignment request.

        Args:
            request_id: Request to accept
            accepting_user: User accepting the request

        Returns:
            Dict with updated request details

        Raises:
            NotFoundError: Request not found
            ForbiddenError: User is not the target of the request
            ValidationError: Request is not pending
        """
        # Get request
        request = self.repo.get_reassignment_request_by_id(request_id)
        if not request:
            raise NotFoundError("Reassignment request", request_id)

        # Check if user is the target
        if request.to_user_id != accepting_user.id:
            raise ForbiddenError("Only the target user can accept this request")

        # Check if request is still pending
        if request.status != "pending":
            raise ValidationError(f"Request is {request.status}, cannot accept")

        # Get run
        run = self.repo.get_run_by_id(request.run_id)
        if not run:
            raise NotFoundError("Run", request.run_id)

        # Update participations
        old_leader_participation = self.repo.get_participation(request.from_user_id, request.run_id)
        new_leader_participation = self.repo.get_participation(request.to_user_id, request.run_id)

        if not old_leader_participation or not new_leader_participation:
            raise ValidationError("Invalid participation status")

        # Transfer leadership
        old_leader_participation.is_leader = False
        new_leader_participation.is_leader = True

        # Update request status
        self.repo.update_reassignment_status(request_id, "accepted")

        # Get store name
        store = self.repo.get_store_by_id(run.store_id)
        store_name = store.name if store else "Unknown Store"

        # Create notification for old leader
        notification_data = {
            "run_id": str(request.run_id),
            "new_leader_id": str(accepting_user.id),
            "new_leader_name": accepting_user.name,
            "store_name": store_name
        }
        notification = self.repo.create_notification(
            request.from_user_id,
            "leader_reassignment_accepted",
            notification_data
        )

        # Broadcast to user's WebSocket for immediate notification
        try:
            await ws_manager.broadcast(
                f"user:{request.from_user_id}",
                {
                    "type": "new_notification",
                    "data": {
                        "id": str(notification.id),
                        "type": "leader_reassignment_accepted",
                        "data": notification_data,
                        "read": False,
                        "created_at": notification.created_at.isoformat() + 'Z' if notification.created_at else None
                    }
                }
            )
        except Exception as e:
            logger.warning(f"Failed to broadcast notification to user: {e}")

        # Broadcast to run participants
        try:
            await ws_manager.broadcast(
                f"run:{request.run_id}",
                {
                    "type": "reassignment_accepted",
                    "data": {
                        "run_id": str(request.run_id),
                        "old_leader_id": str(request.from_user_id),
                        "new_leader_id": str(accepting_user.id),
                        "request_id": str(request_id)
                    }
                }
            )
        except Exception as e:
            logger.warning(f"Failed to broadcast reassignment acceptance: {e}")

        logger.info(
            f"Leader reassignment accepted",
            extra={
                "run_id": str(request.run_id),
                "old_leader_id": str(request.from_user_id),
                "new_leader_id": str(accepting_user.id),
                "request_id": str(request_id)
            }
        )

        return {
            "id": str(request.id),
            "run_id": str(request.run_id),
            "from_user_id": str(request.from_user_id),
            "to_user_id": str(request.to_user_id),
            "status": "accepted",
            "resolved_at": request.resolved_at.isoformat() if request.resolved_at else None
        }

    async def decline_reassignment(self, request_id: UUID, declining_user: User) -> Dict[str, Any]:
        """
        Decline a leader reassignment request.

        Args:
            request_id: Request to decline
            declining_user: User declining the request

        Returns:
            Dict with updated request details

        Raises:
            NotFoundError: Request not found
            ForbiddenError: User is not the target of the request
            ValidationError: Request is not pending
        """
        # Get request
        request = self.repo.get_reassignment_request_by_id(request_id)
        if not request:
            raise NotFoundError("Reassignment request", request_id)

        # Check if user is the target
        if request.to_user_id != declining_user.id:
            raise ForbiddenError("Only the target user can decline this request")

        # Check if request is still pending
        if request.status != "pending":
            raise ValidationError(f"Request is {request.status}, cannot decline")

        # Get run
        run = self.repo.get_run_by_id(request.run_id)
        if not run:
            raise NotFoundError("Run", request.run_id)

        # Update request status
        self.repo.update_reassignment_status(request_id, "declined")

        # Get store name
        store = self.repo.get_store_by_id(run.store_id)
        store_name = store.name if store else "Unknown Store"

        # Create notification for old leader
        notification_data = {
            "run_id": str(request.run_id),
            "declined_by_id": str(declining_user.id),
            "declined_by_name": declining_user.name,
            "store_name": store_name
        }
        notification = self.repo.create_notification(
            request.from_user_id,
            "leader_reassignment_declined",
            notification_data
        )

        # Broadcast to user's WebSocket for immediate notification
        try:
            await ws_manager.broadcast(
                f"user:{request.from_user_id}",
                {
                    "type": "new_notification",
                    "data": {
                        "id": str(notification.id),
                        "type": "leader_reassignment_declined",
                        "data": notification_data,
                        "read": False,
                        "created_at": notification.created_at.isoformat() + 'Z' if notification.created_at else None
                    }
                }
            )
        except Exception as e:
            logger.warning(f"Failed to broadcast notification to user: {e}")

        # Broadcast to run participants
        try:
            await ws_manager.broadcast(
                f"run:{request.run_id}",
                {
                    "type": "reassignment_declined",
                    "data": {
                        "run_id": str(request.run_id),
                        "from_user_id": str(request.from_user_id),
                        "declined_by_id": str(declining_user.id),
                        "request_id": str(request_id)
                    }
                }
            )
        except Exception as e:
            logger.warning(f"Failed to broadcast reassignment decline: {e}")

        logger.info(
            f"Leader reassignment declined",
            extra={
                "run_id": str(request.run_id),
                "from_user_id": str(request.from_user_id),
                "declined_by_id": str(declining_user.id),
                "request_id": str(request_id)
            }
        )

        return {
            "id": str(request.id),
            "run_id": str(request.run_id),
            "from_user_id": str(request.from_user_id),
            "to_user_id": str(request.to_user_id),
            "status": "declined",
            "resolved_at": request.resolved_at.isoformat() if request.resolved_at else None
        }

    def cancel_reassignment(self, request_id: UUID, cancelling_user: User) -> Dict[str, Any]:
        """
        Cancel a pending reassignment request.

        Args:
            request_id: Request to cancel
            cancelling_user: User cancelling the request

        Returns:
            Dict with updated request details

        Raises:
            NotFoundError: Request not found
            ForbiddenError: User is not the requester
            ValidationError: Request is not pending
        """
        # Get request
        request = self.repo.get_reassignment_request_by_id(request_id)
        if not request:
            raise NotFoundError("Reassignment request", request_id)

        # Check if user is the requester
        if request.from_user_id != cancelling_user.id:
            raise ForbiddenError("Only the requesting user can cancel this request")

        # Check if request is still pending
        if request.status != "pending":
            raise ValidationError(f"Request is {request.status}, cannot cancel")

        # Update request status
        self.repo.update_reassignment_status(request_id, "cancelled")

        logger.info(
            f"Leader reassignment cancelled",
            extra={
                "run_id": str(request.run_id),
                "from_user_id": str(cancelling_user.id),
                "request_id": str(request_id)
            }
        )

        return {
            "id": str(request.id),
            "run_id": str(request.run_id),
            "from_user_id": str(request.from_user_id),
            "to_user_id": str(request.to_user_id),
            "status": "cancelled",
            "resolved_at": request.resolved_at.isoformat() if request.resolved_at else None
        }

    def get_pending_requests_for_user(self, user_id: UUID) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all pending reassignment requests involving a user.

        Args:
            user_id: User to check

        Returns:
            Dict with 'sent' and 'received' lists of requests
        """
        sent_requests = self.repo.get_pending_reassignments_from_user(user_id)
        received_requests = self.repo.get_pending_reassignments_to_user(user_id)

        return {
            "sent": [self._format_request(r) for r in sent_requests],
            "received": [self._format_request(r) for r in received_requests]
        }

    def get_pending_request_for_run(self, run_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get pending reassignment request for a run (if any).

        Args:
            run_id: Run to check

        Returns:
            Request details or None
        """
        request = self.repo.get_pending_reassignment_for_run(run_id)
        return self._format_request(request) if request else None

    def _format_request(self, request: LeaderReassignmentRequest) -> Dict[str, Any]:
        """Format a reassignment request for API response."""
        # Get user names
        from_user = self.repo.get_user_by_id(request.from_user_id)
        to_user = self.repo.get_user_by_id(request.to_user_id)

        # Get run details
        run = self.repo.get_run_by_id(request.run_id)

        # Get store name
        store_name = "Unknown Store"
        if run:
            store = self.repo.get_store_by_id(run.store_id)
            store_name = store.name if store else "Unknown Store"

        return {
            "id": str(request.id),
            "run_id": str(request.run_id),
            "from_user_id": str(request.from_user_id),
            "from_user_name": from_user.name if from_user else "Unknown",
            "to_user_id": str(request.to_user_id),
            "to_user_name": to_user.name if to_user else "Unknown",
            "store_name": store_name,
            "status": request.status,
            "created_at": request.created_at.isoformat()
        }
