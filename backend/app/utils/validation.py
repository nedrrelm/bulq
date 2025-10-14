"""Validation helper functions for common validation patterns.

This module provides validation helpers that delegate to the state machine
for consistent state validation across the application.
"""

from uuid import UUID

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
        raise BadRequestError(f'Invalid {resource_name} ID format') from e


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
        error_msg = state_machine.get_action_error_message(
            action_name, RunState(run.state), allowed_states
        )
        raise BadRequestError(error_msg)


def validate_state_transition(
    current_state: RunState,
    target_state: RunState,
    allowed_transitions: dict[RunState, list[RunState]] | None = None,
) -> None:
    """Validate that a state transition is allowed.

    NOTE: This function is kept for backward compatibility but delegates to
    the state machine. New code should use state_machine.validate_transition()
    directly.

    Args:
        current_state: Current state
        target_state: Desired target state
        allowed_transitions: Optional dict of allowed transitions.
                           If None, uses state machine rules (ignored if provided).

    Raises:
        BadRequestError: If the transition is not allowed
    """
    # If custom transitions provided, validate manually (legacy behavior)
    if allowed_transitions is not None:
        allowed = allowed_transitions.get(current_state, [])
        if target_state not in allowed:
            allowed_str = ', '.join([s.value for s in allowed]) if allowed else 'none'
            raise BadRequestError(
                f"Cannot transition from '{current_state}' to '{target_state}'. "
                f'Allowed transitions: {allowed_str}'
            )
        return

    # Delegate to state machine for standard validation
    try:
        state_machine.validate_transition(current_state, target_state)
    except ValueError as e:
        # Convert ValueError to BadRequestError for API consistency
        raise BadRequestError(str(e)) from e
