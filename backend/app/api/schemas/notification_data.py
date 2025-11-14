"""Pydantic models for notification data payloads.

This module defines typed schemas for each notification type's data structure.
These models ensure type safety and consistent structure for notification data
sent to the frontend for localization.

All notification data should contain only raw data (IDs, names, values, states)
without any pre-formatted messages.
"""

from pydantic import BaseModel, Field


class RunStateChangedData(BaseModel):
    """Data for run_state_changed notification type.

    Sent when a run transitions to a new state.
    """

    run_id: str = Field(..., description='ID of the run that changed state')
    store_name: str = Field(..., description='Name of the store for this run')
    old_state: str = Field(..., description='Previous state of the run')
    new_state: str = Field(..., description='New state of the run')
    group_id: str = Field(..., description='ID of the group this run belongs to')

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            'example': {
                'run_id': '123e4567-e89b-12d3-a456-426614174000',
                'store_name': 'Costco Downtown',
                'old_state': 'active',
                'new_state': 'confirmed',
                'group_id': '123e4567-e89b-12d3-a456-426614174001',
            }
        }


class LeaderReassignmentRequestData(BaseModel):
    """Data for leader_reassignment_request notification type.

    Sent when a run leader requests to transfer leadership to another user.
    """

    run_id: str = Field(..., description='ID of the run')
    from_user_id: str = Field(..., description='ID of the user requesting transfer')
    from_user_name: str = Field(..., description='Name of the user requesting transfer')
    request_id: str = Field(..., description='ID of the reassignment request')
    store_name: str = Field(..., description='Name of the store for this run')

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            'example': {
                'run_id': '123e4567-e89b-12d3-a456-426614174000',
                'from_user_id': '123e4567-e89b-12d3-a456-426614174002',
                'from_user_name': 'John Doe',
                'request_id': '123e4567-e89b-12d3-a456-426614174003',
                'store_name': 'Costco Downtown',
            }
        }


class LeaderReassignmentAcceptedData(BaseModel):
    """Data for leader_reassignment_accepted notification type.

    Sent to the original leader when their transfer request is accepted.
    """

    run_id: str = Field(..., description='ID of the run')
    new_leader_id: str = Field(..., description='ID of the new leader')
    new_leader_name: str = Field(..., description='Name of the new leader')
    store_name: str = Field(..., description='Name of the store for this run')

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            'example': {
                'run_id': '123e4567-e89b-12d3-a456-426614174000',
                'new_leader_id': '123e4567-e89b-12d3-a456-426614174004',
                'new_leader_name': 'Jane Smith',
                'store_name': 'Costco Downtown',
            }
        }


class LeaderReassignmentDeclinedData(BaseModel):
    """Data for leader_reassignment_declined notification type.

    Sent to the original leader when their transfer request is declined.
    """

    run_id: str = Field(..., description='ID of the run')
    declined_by_id: str = Field(..., description='ID of the user who declined')
    declined_by_name: str = Field(..., description='Name of the user who declined')
    store_name: str = Field(..., description='Name of the store for this run')

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            'example': {
                'run_id': '123e4567-e89b-12d3-a456-426614174000',
                'declined_by_id': '123e4567-e89b-12d3-a456-426614174004',
                'declined_by_name': 'Jane Smith',
                'store_name': 'Costco Downtown',
            }
        }


# WebSocket message data models


class BidUpdatedData(BaseModel):
    """Data for bid_updated WebSocket message type.

    Sent when a user places or updates a bid.
    """

    product_id: str = Field(..., description='ID of the product bid on')
    user_id: str = Field(..., description='ID of the user who placed the bid')
    user_name: str = Field(..., description='Name of the user who placed the bid')
    quantity: float = Field(..., description='Bid quantity')
    interested_only: bool = Field(..., description='Whether bid is interest-only')
    new_total: float = Field(..., description='New total quantity for product')

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            'example': {
                'product_id': '123e4567-e89b-12d3-a456-426614174000',
                'user_id': '123e4567-e89b-12d3-a456-426614174001',
                'user_name': 'John Doe',
                'quantity': 5.0,
                'interested_only': False,
                'new_total': 15.0,
            }
        }


class BidRetractedData(BaseModel):
    """Data for bid_retracted WebSocket message type.

    Sent when a user retracts their bid.
    """

    product_id: str = Field(..., description='ID of the product')
    user_id: str = Field(..., description='ID of the user who retracted the bid')
    new_total: float = Field(..., description='New total quantity for product')

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            'example': {
                'product_id': '123e4567-e89b-12d3-a456-426614174000',
                'user_id': '123e4567-e89b-12d3-a456-426614174001',
                'new_total': 10.0,
            }
        }


class ReadyToggledData(BaseModel):
    """Data for ready_toggled WebSocket message type.

    Sent when a user toggles their ready status.
    """

    user_id: str = Field(..., description='ID of the user who toggled ready')
    is_ready: bool = Field(..., description='New ready status')

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            'example': {
                'user_id': '123e4567-e89b-12d3-a456-426614174001',
                'is_ready': True,
            }
        }


class StateChangedData(BaseModel):
    """Data for state_changed WebSocket message type.

    Sent when a run state changes (broadcast to run room).
    """

    run_id: str = Field(..., description='ID of the run')
    new_state: str = Field(..., description='New state of the run')

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            'example': {
                'run_id': '123e4567-e89b-12d3-a456-426614174000',
                'new_state': 'confirmed',
            }
        }


class RunCreatedData(BaseModel):
    """Data for run_created WebSocket message type.

    Sent when a new run is created (broadcast to group room).
    """

    run_id: str = Field(..., description='ID of the new run')
    store_id: str = Field(..., description='ID of the store')
    store_name: str = Field(..., description='Name of the store')
    state: str = Field(..., description='Initial state of the run')
    leader_name: str = Field(..., description='Name of the run leader')

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            'example': {
                'run_id': '123e4567-e89b-12d3-a456-426614174000',
                'store_id': '123e4567-e89b-12d3-a456-426614174005',
                'store_name': 'Costco Downtown',
                'state': 'planning',
                'leader_name': 'John Doe',
            }
        }
