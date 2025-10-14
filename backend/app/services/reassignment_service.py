"""Leader reassignment service for managing run leader transfers."""

from typing import Any
from uuid import UUID

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.core.models import LeaderReassignmentRequest, Run, User
from app.repositories import AbstractRepository
from app.infrastructure.request_context import get_logger
from app.api.schemas import MyRequestsResponse, ReassignmentDetailResponse, ReassignmentResponse
from app.infrastructure.transaction import transaction
from app.api.websocket_manager import manager as ws_manager
from .base_service import BaseService

logger = get_logger(__name__)


class ReassignmentService(BaseService):
    """Service for handling leader reassignment requests."""

    async def request_reassignment(
        self, run_id: UUID, from_user: User, to_user_id: UUID
    ) -> ReassignmentResponse:
        """Create a leader reassignment request.

        Creates request and notification atomically.

        Args:
            run_id: Run to reassign
            from_user: Current leader requesting reassignment
            to_user_id: User to become new leader

        Returns:
            ReassignmentResponse with request details

        Raises:
            NotFoundError: Run or target user not found
            ForbiddenError: Requesting user is not the leader
            ValidationError: Invalid request (same user, user not in run, etc.)
            ConflictError: Pending request already exists
        """
        run, to_user = self._validate_reassignment_eligibility(run_id, from_user, to_user_id)
        self._check_reassignment_permissions(from_user, to_user_id, run_id)
        store_name = self._get_store_name(run.store_id)

        # Wrap request creation and notification in transaction
        if self.db:
            with transaction(self.db, "create reassignment request"):
                request = self._create_reassignment_record(run_id, from_user.id, to_user_id)
                await self._notify_reassignment_participants(
                    run_id, from_user, to_user_id, request.id, store_name
                )
        else:
            # Fallback for when db session not available
            request = self._create_reassignment_record(run_id, from_user.id, to_user_id)
            await self._notify_reassignment_participants(
                run_id, from_user, to_user_id, request.id, store_name
            )

        logger.info(
            'Leader reassignment requested',
            extra={
                'run_id': str(run_id),
                'from_user_id': str(from_user.id),
                'to_user_id': str(to_user_id),
                'request_id': str(request.id),
            },
        )

        return ReassignmentResponse(
            id=str(request.id),
            run_id=str(request.run_id),
            from_user_id=str(request.from_user_id),
            to_user_id=str(request.to_user_id),
            status=request.status,
            created_at=request.created_at.isoformat(),
            resolved_at=None,
        )

    def _validate_reassignment_eligibility(
        self, run_id: UUID, from_user: User, to_user_id: UUID
    ) -> tuple[Run, User]:
        """Validate that run and users exist."""
        run = self.repo.get_run_by_id(run_id)
        if not run:
            raise NotFoundError('Run', run_id)

        participation = self.repo.get_participation(from_user.id, run_id)
        if not participation or not participation.is_leader:
            raise ForbiddenError('Only the run leader can request reassignment')

        to_user = self.repo.get_user_by_id(to_user_id)
        if not to_user:
            raise NotFoundError('User', to_user_id)

        return run, to_user

    def _check_reassignment_permissions(
        self, from_user: User, to_user_id: UUID, run_id: UUID
    ) -> None:
        """Check if reassignment is allowed."""
        if from_user.id == to_user_id:
            raise ValidationError('Cannot reassign leadership to yourself')

        target_participation = self.repo.get_participation(to_user_id, run_id)
        if not target_participation:
            raise ValidationError('Target user is not participating in this run')

        existing_request = self.repo.get_pending_reassignment_for_run(run_id)
        if existing_request:
            raise ConflictError('A pending reassignment request already exists for this run')

    def _create_reassignment_record(
        self, run_id: UUID, from_user_id: UUID, to_user_id: UUID
    ) -> LeaderReassignmentRequest:
        """Create reassignment request in database."""
        return self.repo.create_reassignment_request(run_id, from_user_id, to_user_id)

    def _get_store_name(self, store_id: UUID) -> str:
        """Get store name or return default."""
        store = self.repo.get_store_by_id(store_id)
        return store.name if store else 'Unknown Store'

    async def _notify_reassignment_participants(
        self, run_id: UUID, from_user: User, to_user_id: UUID, request_id: UUID, store_name: str
    ) -> None:
        """Create notification and broadcast to participants."""
        notification_data = {
            'run_id': str(run_id),
            'from_user_id': str(from_user.id),
            'from_user_name': from_user.name,
            'request_id': str(request_id),
            'store_name': store_name,
        }

        notification = self.repo.create_notification(
            to_user_id, 'leader_reassignment_request', notification_data
        )

        # Broadcast to target user
        try:
            await ws_manager.broadcast(
                f'user:{to_user_id}',
                {
                    'type': 'new_notification',
                    'data': {
                        'id': str(notification.id),
                        'type': 'leader_reassignment_request',
                        'data': notification_data,
                        'read': False,
                        'created_at': notification.created_at.isoformat() + 'Z'
                        if notification.created_at
                        else None,
                    },
                },
            )
        except Exception as e:
            logger.warning(
                'Failed to broadcast notification to user',
                extra={'error': str(e), 'user_id': str(to_user_id), 'run_id': str(run_id)},
            )

        # Broadcast to run participants
        try:
            await ws_manager.broadcast(
                f'run:{run_id}',
                {
                    'type': 'reassignment_requested',
                    'data': {
                        'run_id': str(run_id),
                        'from_user_id': str(from_user.id),
                        'to_user_id': str(to_user_id),
                        'request_id': str(request_id),
                    },
                },
            )
        except Exception as e:
            logger.warning(
                'Failed to broadcast reassignment request',
                extra={
                    'error': str(e),
                    'run_id': str(run_id),
                    'from_user_id': str(from_user.id),
                    'to_user_id': str(to_user_id),
                },
            )

    async def accept_reassignment(self, request_id: UUID, accepting_user: User) -> ReassignmentResponse:
        """Accept a leader reassignment request.

        Transfers leadership and updates request status atomically.

        Args:
            request_id: Request to accept
            accepting_user: User accepting the request

        Returns:
            ReassignmentResponse with updated request details

        Raises:
            NotFoundError: Request not found
            ForbiddenError: User is not the target of the request
            ValidationError: Request is not pending
        """
        request = self._validate_accept_request(request_id, accepting_user)
        run = self._get_run(request.run_id)
        store_name = self._get_store_name(run.store_id)

        # Wrap leadership transfer and status update in transaction
        if self.db:
            with transaction(self.db, "accept leader reassignment"):
                self._transfer_leadership(request.run_id, request.from_user_id, request.to_user_id)
                self.repo.update_reassignment_status(request_id, 'accepted')
        else:
            # Fallback for when db session not available (shouldn't happen in production)
            self._transfer_leadership(request.run_id, request.from_user_id, request.to_user_id)
            self.repo.update_reassignment_status(request_id, 'accepted')

        # Notify after successful transaction
        await self._notify_acceptance(request, accepting_user, store_name, request_id)

        logger.info(
            'Leader reassignment accepted',
            extra={
                'run_id': str(request.run_id),
                'old_leader_id': str(request.from_user_id),
                'new_leader_id': str(accepting_user.id),
                'request_id': str(request_id),
            },
        )

        return ReassignmentResponse(
            id=str(request.id),
            run_id=str(request.run_id),
            from_user_id=str(request.from_user_id),
            to_user_id=str(request.to_user_id),
            status='accepted',
            created_at=request.created_at.isoformat(),
            resolved_at=request.resolved_at.isoformat() if request.resolved_at else None,
        )

    def _validate_accept_request(
        self, request_id: UUID, accepting_user: User
    ) -> LeaderReassignmentRequest:
        """Validate accept request."""
        request = self.repo.get_reassignment_request_by_id(request_id)
        if not request:
            raise NotFoundError('Reassignment request', request_id)

        if request.to_user_id != accepting_user.id:
            raise ForbiddenError('Only the target user can accept this request')

        if request.status != 'pending':
            raise ValidationError(f'Request is {request.status}, cannot accept')

        return request

    def _get_run(self, run_id: UUID) -> Run:
        """Get run or raise error."""
        run = self.repo.get_run_by_id(run_id)
        if not run:
            raise NotFoundError('Run', run_id)
        return run

    def _transfer_leadership(self, run_id: UUID, from_user_id: UUID, to_user_id: UUID) -> None:
        """Transfer leadership from one user to another."""
        old_leader_participation = self.repo.get_participation(from_user_id, run_id)
        new_leader_participation = self.repo.get_participation(to_user_id, run_id)

        if not old_leader_participation or not new_leader_participation:
            raise ValidationError('Invalid participation status')

        old_leader_participation.is_leader = False
        new_leader_participation.is_leader = True

    async def _notify_acceptance(
        self,
        request: LeaderReassignmentRequest,
        accepting_user: User,
        store_name: str,
        request_id: UUID,
    ) -> None:
        """Create notification and broadcast acceptance."""
        notification_data = {
            'run_id': str(request.run_id),
            'new_leader_id': str(accepting_user.id),
            'new_leader_name': accepting_user.name,
            'store_name': store_name,
        }

        notification = self.repo.create_notification(
            request.from_user_id, 'leader_reassignment_accepted', notification_data
        )

        # Broadcast to old leader
        try:
            await ws_manager.broadcast(
                f'user:{request.from_user_id}',
                {
                    'type': 'new_notification',
                    'data': {
                        'id': str(notification.id),
                        'type': 'leader_reassignment_accepted',
                        'data': notification_data,
                        'read': False,
                        'created_at': notification.created_at.isoformat() + 'Z'
                        if notification.created_at
                        else None,
                    },
                },
            )
        except Exception as e:
            logger.warning(
                'Failed to broadcast notification to user',
                extra={
                    'error': str(e),
                    'user_id': str(request.from_user_id),
                    'run_id': str(request.run_id),
                },
            )

        # Broadcast to run participants
        try:
            await ws_manager.broadcast(
                f'run:{request.run_id}',
                {
                    'type': 'reassignment_accepted',
                    'data': {
                        'run_id': str(request.run_id),
                        'old_leader_id': str(request.from_user_id),
                        'new_leader_id': str(accepting_user.id),
                        'request_id': str(request_id),
                    },
                },
            )
        except Exception as e:
            logger.warning(
                'Failed to broadcast reassignment acceptance',
                extra={
                    'error': str(e),
                    'run_id': str(request.run_id),
                    'request_id': str(request_id),
                },
            )

    async def decline_reassignment(self, request_id: UUID, declining_user: User) -> ReassignmentResponse:
        """Decline a leader reassignment request.

        Args:
            request_id: Request to decline
            declining_user: User declining the request

        Returns:
            ReassignmentResponse with updated request details

        Raises:
            NotFoundError: Request not found
            ForbiddenError: User is not the target of the request
            ValidationError: Request is not pending
        """
        request = self._validate_decline_request(request_id, declining_user)
        run = self._get_run(request.run_id)
        store_name = self._get_store_name(run.store_id)

        # Wrap status update and notification in transaction
        if self.db:
            with transaction(self.db, "decline reassignment request"):
                self.repo.update_reassignment_status(request_id, 'declined')
                await self._notify_decline(request, declining_user, store_name, request_id)
        else:
            self.repo.update_reassignment_status(request_id, 'declined')
            await self._notify_decline(request, declining_user, store_name, request_id)

        logger.info(
            'Leader reassignment declined',
            extra={
                'run_id': str(request.run_id),
                'from_user_id': str(request.from_user_id),
                'declined_by_id': str(declining_user.id),
                'request_id': str(request_id),
            },
        )

        return ReassignmentResponse(
            id=str(request.id),
            run_id=str(request.run_id),
            from_user_id=str(request.from_user_id),
            to_user_id=str(request.to_user_id),
            status='declined',
            created_at=request.created_at.isoformat(),
            resolved_at=request.resolved_at.isoformat() if request.resolved_at else None,
        )

    def _validate_decline_request(
        self, request_id: UUID, declining_user: User
    ) -> LeaderReassignmentRequest:
        """Validate decline request."""
        request = self.repo.get_reassignment_request_by_id(request_id)
        if not request:
            raise NotFoundError('Reassignment request', request_id)

        if request.to_user_id != declining_user.id:
            raise ForbiddenError('Only the target user can decline this request')

        if request.status != 'pending':
            raise ValidationError(f'Request is {request.status}, cannot decline')

        return request

    async def _notify_decline(
        self,
        request: LeaderReassignmentRequest,
        declining_user: User,
        store_name: str,
        request_id: UUID,
    ) -> None:
        """Create notification and broadcast decline."""
        notification_data = {
            'run_id': str(request.run_id),
            'declined_by_id': str(declining_user.id),
            'declined_by_name': declining_user.name,
            'store_name': store_name,
        }

        notification = self.repo.create_notification(
            request.from_user_id, 'leader_reassignment_declined', notification_data
        )

        # Broadcast to original leader
        try:
            await ws_manager.broadcast(
                f'user:{request.from_user_id}',
                {
                    'type': 'new_notification',
                    'data': {
                        'id': str(notification.id),
                        'type': 'leader_reassignment_declined',
                        'data': notification_data,
                        'read': False,
                        'created_at': notification.created_at.isoformat() + 'Z'
                        if notification.created_at
                        else None,
                    },
                },
            )
        except Exception as e:
            logger.warning(
                'Failed to broadcast notification to user',
                extra={
                    'error': str(e),
                    'user_id': str(request.from_user_id),
                    'run_id': str(request.run_id),
                },
            )

        # Broadcast to run participants
        try:
            await ws_manager.broadcast(
                f'run:{request.run_id}',
                {
                    'type': 'reassignment_declined',
                    'data': {
                        'run_id': str(request.run_id),
                        'from_user_id': str(request.from_user_id),
                        'declined_by_id': str(declining_user.id),
                        'request_id': str(request_id),
                    },
                },
            )
        except Exception as e:
            logger.warning(
                'Failed to broadcast reassignment decline',
                extra={
                    'error': str(e),
                    'run_id': str(request.run_id),
                    'request_id': str(request_id),
                },
            )

    def cancel_reassignment(self, request_id: UUID, cancelling_user: User) -> ReassignmentResponse:
        """Cancel a pending reassignment request.

        Args:
            request_id: Request to cancel
            cancelling_user: User cancelling the request

        Returns:
            ReassignmentResponse with updated request details

        Raises:
            NotFoundError: Request not found
            ForbiddenError: User is not the requester
            ValidationError: Request is not pending
        """
        # Get request
        request = self.repo.get_reassignment_request_by_id(request_id)
        if not request:
            raise NotFoundError('Reassignment request', request_id)

        # Check if user is the requester
        if request.from_user_id != cancelling_user.id:
            raise ForbiddenError('Only the requesting user can cancel this request')

        # Check if request is still pending
        if request.status != 'pending':
            raise ValidationError(f'Request is {request.status}, cannot cancel')

        # Update request status
        self.repo.update_reassignment_status(request_id, 'cancelled')

        logger.info(
            'Leader reassignment cancelled',
            extra={
                'run_id': str(request.run_id),
                'from_user_id': str(cancelling_user.id),
                'request_id': str(request_id),
            },
        )

        return ReassignmentResponse(
            id=str(request.id),
            run_id=str(request.run_id),
            from_user_id=str(request.from_user_id),
            to_user_id=str(request.to_user_id),
            status='cancelled',
            created_at=request.created_at.isoformat(),
            resolved_at=request.resolved_at.isoformat() if request.resolved_at else None,
        )

    def get_pending_requests_for_user(self, user_id: UUID) -> MyRequestsResponse:
        """Get all pending reassignment requests involving a user.

        Args:
            user_id: User to check

        Returns:
            MyRequestsResponse with 'sent' and 'received' lists of requests
        """
        sent_requests = self.repo.get_pending_reassignments_from_user(user_id)
        received_requests = self.repo.get_pending_reassignments_to_user(user_id)

        return MyRequestsResponse(
            sent=[self._format_request(r) for r in sent_requests],
            received=[self._format_request(r) for r in received_requests],
        )

    def get_pending_request_for_run(self, run_id: UUID) -> ReassignmentDetailResponse | None:
        """Get pending reassignment request for a run (if any).

        Args:
            run_id: Run to check

        Returns:
            ReassignmentDetailResponse or None
        """
        request = self.repo.get_pending_reassignment_for_run(run_id)
        return self._format_request(request) if request else None

    def _format_request(self, request: LeaderReassignmentRequest) -> ReassignmentDetailResponse:
        """Format a reassignment request for API response."""
        # Get user names
        from_user = self.repo.get_user_by_id(request.from_user_id)
        to_user = self.repo.get_user_by_id(request.to_user_id)

        # Get run details
        run = self.repo.get_run_by_id(request.run_id)

        # Get store name
        store_name = 'Unknown Store'
        if run:
            store = self.repo.get_store_by_id(run.store_id)
            store_name = store.name if store else 'Unknown Store'

        return ReassignmentDetailResponse(
            id=str(request.id),
            run_id=str(request.run_id),
            from_user_id=str(request.from_user_id),
            from_user_name=from_user.name if from_user else 'Unknown',
            to_user_id=str(request.to_user_id),
            to_user_name=to_user.name if to_user else 'Unknown',
            store_name=store_name,
            status=request.status,
            created_at=request.created_at.isoformat(),
        )
