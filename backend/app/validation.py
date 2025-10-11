"""Validation helper functions for common validation patterns."""

from uuid import UUID
from typing import Optional
from .exceptions import BadRequestError
from .models import Run
from .run_state import RunState


def validate_uuid(id_str: str, resource_name: str = "ID") -> UUID:
    """
    Validate and convert a string to UUID.

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
    except ValueError:
        raise BadRequestError(f"Invalid {resource_name} ID format")


def validate_run_state_for_action(
    run: Run,
    allowed_states: list[RunState],
    action_name: str
) -> None:
    """
    Validate that a run is in one of the allowed states for a specific action.

    Args:
        run: The run object to validate
        allowed_states: List of states that are allowed for this action
        action_name: Name of the action for error message (e.g., "bidding", "shopping")

    Raises:
        BadRequestError: If the run is not in an allowed state
    """
    if run.state not in allowed_states:
        allowed_states_str = ", ".join([s.value for s in allowed_states])
        raise BadRequestError(
            f"{action_name.capitalize()} not allowed in current run state. "
            f"Run is in '{run.state}' state, but must be in one of: {allowed_states_str}"
        )


def validate_state_transition(
    current_state: RunState,
    target_state: RunState,
    allowed_transitions: Optional[dict[RunState, list[RunState]]] = None
) -> None:
    """
    Validate that a state transition is allowed.

    Args:
        current_state: Current state
        target_state: Desired target state
        allowed_transitions: Optional dict of allowed transitions.
                           If None, uses default state machine rules.

    Raises:
        BadRequestError: If the transition is not allowed
    """
    if allowed_transitions is None:
        # Default allowed transitions
        allowed_transitions = {
            RunState.PLANNING: [RunState.ACTIVE, RunState.CANCELLED],
            RunState.ACTIVE: [RunState.CONFIRMED, RunState.CANCELLED],
            RunState.CONFIRMED: [RunState.SHOPPING, RunState.CANCELLED],
            RunState.SHOPPING: [RunState.ADJUSTING, RunState.CANCELLED],
            RunState.ADJUSTING: [RunState.DISTRIBUTING, RunState.CANCELLED],
            RunState.DISTRIBUTING: [RunState.COMPLETED],
            RunState.COMPLETED: [],
            RunState.CANCELLED: []
        }

    allowed = allowed_transitions.get(current_state, [])
    if target_state not in allowed:
        allowed_str = ", ".join([s.value for s in allowed]) if allowed else "none"
        raise BadRequestError(
            f"Cannot transition from '{current_state}' to '{target_state}'. "
            f"Allowed transitions: {allowed_str}"
        )
