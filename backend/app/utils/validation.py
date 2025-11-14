"""Validation helper functions for common validation patterns.

This module provides validation helpers that delegate to the state machine
for consistent state validation across the application.
"""

from uuid import UUID

from app.core import error_codes
from app.core.exceptions import BadRequestError
from app.core.models import Run
from app.core.run_state import RunState, state_machine


def validate_uuid(id_str: str, resource_name: str = 'ID') -> UUID:
    """Validate and convert a string to UUID.

    Args:
        id_str: The string to convert to UUID
        resource_name: Name of the resource for error message (e.g., "Group", "Run", "User")

    Returns:
        UUID object

    Raises:
        BadRequestError: If the string is not a valid UUID format
    """
    try:
        return UUID(id_str)
    except ValueError as e:
        raise BadRequestError(
            code=error_codes.INVALID_UUID_FORMAT,
            message=f'Invalid {resource_name} ID format',
            field=resource_name.lower(),
            value=id_str,
        ) from e


def validate_run_state_for_action(
    run: Run, allowed_states: list[RunState], action_name: str
) -> None:
    """Validate that a run is in one of the allowed states for a specific action.

    NOTE: This function is kept for backward compatibility but delegates to
    the state machine for consistent validation. New code should use the
    state machine's can_* methods directly.

    Args:
        run: The run object to validate
        allowed_states: List of states that are allowed for this action
        action_name: Name of the action for error message (e.g., "bidding", "shopping")

    Raises:
        BadRequestError: If the run is not in an allowed state
    """
    if run.state not in allowed_states:
        # Determine the appropriate error code based on the allowed states
        error_code = _get_state_error_code(RunState(run.state), allowed_states)
        error_msg = state_machine.get_action_error_message(
            action_name, RunState(run.state), allowed_states
        )
        raise BadRequestError(
            code=error_code,
            message=error_msg,
            current_state=run.state,
            allowed_states=[s.value for s in allowed_states],
            action=action_name,
        )


def _get_state_error_code(current_state: RunState, allowed_states: list[RunState]) -> str:
    """Determine the appropriate error code based on the current state.

    Helper function to map specific run states to their corresponding error codes.

    Args:
        current_state: The current run state
        allowed_states: List of allowed states for the action

    Returns:
        Error code string from error_codes module
    """
    # If only one allowed state, return a specific error for that state
    if len(allowed_states) == 1:
        allowed = allowed_states[0]
        state_to_code = {
            RunState.PLANNING: error_codes.RUN_NOT_IN_PLANNING_STATE,
            RunState.ACTIVE: error_codes.RUN_NOT_IN_ACTIVE_STATE,
            RunState.CONFIRMED: error_codes.RUN_NOT_IN_CONFIRMED_STATE,
            RunState.SHOPPING: error_codes.RUN_NOT_IN_SHOPPING_STATE,
            RunState.ADJUSTING: error_codes.RUN_NOT_IN_ADJUSTING_STATE,
            RunState.DISTRIBUTING: error_codes.RUN_NOT_IN_DISTRIBUTING_STATE,
        }
        return state_to_code.get(allowed, error_codes.INVALID_RUN_STATE_TRANSITION)

    # Check for terminal states
    if current_state == RunState.CANCELLED:
        return error_codes.RUN_ALREADY_CANCELLED
    if current_state == RunState.COMPLETED:
        return error_codes.RUN_ALREADY_COMPLETED

    # Default to generic state transition error
    return error_codes.INVALID_RUN_STATE_TRANSITION
