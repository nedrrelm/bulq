"""Run state machine for managing run state transitions."""

from enum import Enum

from app.infrastructure.request_context import get_logger

logger = get_logger(__name__)


class RunState(str, Enum):
    """Run state enum that can be used as both string and enum."""

    PLANNING = 'planning'
    ACTIVE = 'active'
    CONFIRMED = 'confirmed'
    SHOPPING = 'shopping'
    ADJUSTING = 'adjusting'
    DISTRIBUTING = 'distributing'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'

    def __str__(self) -> str:
        """Return the string value."""
        return self.value


class RunStateMachine:
    """State machine for managing run state transitions with validation."""

    # Define valid state transitions
    VALID_TRANSITIONS = {
        RunState.PLANNING: [RunState.ACTIVE, RunState.CANCELLED],
        RunState.ACTIVE: [RunState.CONFIRMED, RunState.PLANNING, RunState.CANCELLED],
        RunState.CONFIRMED: [RunState.SHOPPING, RunState.ACTIVE, RunState.CANCELLED],
        RunState.SHOPPING: [RunState.ADJUSTING, RunState.DISTRIBUTING, RunState.CANCELLED],
        RunState.ADJUSTING: [RunState.DISTRIBUTING, RunState.CANCELLED],
        RunState.DISTRIBUTING: [RunState.COMPLETED, RunState.CANCELLED],
        RunState.COMPLETED: [],  # Terminal state
        RunState.CANCELLED: [],  # Terminal state
    }

    # Human-readable state descriptions
    STATE_DESCRIPTIONS = {
        RunState.PLANNING: 'Leader is planning the run',
        RunState.ACTIVE: 'Users are actively placing bids',
        RunState.CONFIRMED: 'All users ready, awaiting shopping trip',
        RunState.SHOPPING: 'Shopping trip in progress',
        RunState.ADJUSTING: 'Adjusting bids due to insufficient quantities',
        RunState.DISTRIBUTING: 'Items being distributed to members',
        RunState.COMPLETED: 'Run completed successfully',
        RunState.CANCELLED: 'Run was cancelled',
    }

    def can_transition(self, from_state: RunState, to_state: RunState) -> bool:
        """Check if a state transition is valid.

        Args:
            from_state: Current state
            to_state: Desired state

        Returns:
            True if transition is valid, False otherwise
        """
        valid_next_states = self.VALID_TRANSITIONS.get(from_state, [])
        return to_state in valid_next_states

    def get_valid_transitions(self, from_state: RunState) -> list[RunState]:
        """Get all valid transitions from a given state.

        Args:
            from_state: Current state

        Returns:
            List of valid next states
        """
        return self.VALID_TRANSITIONS.get(from_state, [])

    def get_state_description(self, state: RunState) -> str:
        """Get human-readable description of a state.

        Args:
            state: The state to describe

        Returns:
            Description string
        """
        return self.STATE_DESCRIPTIONS.get(state, 'Unknown state')

    def validate_transition(
        self, from_state: RunState, to_state: RunState, run_id: str | None = None
    ) -> None:
        """Validate a state transition and raise exception if invalid.

        Args:
            from_state: Current state
            to_state: Desired state
            run_id: Optional run ID for logging context

        Raises:
            ValueError: If transition is not valid
        """
        if not self.can_transition(from_state, to_state):
            valid_states = self.get_valid_transitions(from_state)
            valid_states_str = (
                ', '.join([s.value for s in valid_states]) if valid_states else 'none'
            )

            error_msg = (
                f'Invalid state transition from {from_state.value} to {to_state.value}. '
                f'Valid transitions: {valid_states_str}'
            )

            logger.warning(
                'Invalid state transition attempted',
                extra={
                    'run_id': run_id,
                    'from_state': from_state.value,
                    'to_state': to_state.value,
                    'valid_transitions': valid_states_str,
                },
            )

            raise ValueError(error_msg)

    def is_terminal_state(self, state: RunState) -> bool:
        """Check if a state is terminal (no further transitions possible).

        Args:
            state: State to check

        Returns:
            True if terminal state, False otherwise
        """
        return len(self.VALID_TRANSITIONS.get(state, [])) == 0

    def can_cancel(self, state: RunState) -> bool:
        """Check if a run can be cancelled from the given state.

        Args:
            state: Current state

        Returns:
            True if cancellation is allowed, False otherwise
        """
        return RunState.CANCELLED in self.VALID_TRANSITIONS.get(state, [])

    # Action-based validation methods

    def can_place_bid(self, state: RunState) -> bool:
        """Check if bidding is allowed in the given state.

        Args:
            state: Current run state

        Returns:
            True if bidding is allowed, False otherwise
        """
        return state in [RunState.PLANNING, RunState.ACTIVE, RunState.ADJUSTING]

    def can_retract_bid(self, state: RunState) -> bool:
        """Check if bid retraction is allowed in the given state.

        Args:
            state: Current run state

        Returns:
            True if bid retraction is allowed, False otherwise
        """
        return state in [RunState.PLANNING, RunState.ACTIVE, RunState.ADJUSTING]

    def can_toggle_ready(self, state: RunState) -> bool:
        """Check if toggling ready status is allowed in the given state.

        Args:
            state: Current run state

        Returns:
            True if toggling ready is allowed, False otherwise
        """
        return state == RunState.ACTIVE

    def can_start_shopping(self, state: RunState) -> bool:
        """Check if starting shopping is allowed in the given state.

        Args:
            state: Current run state

        Returns:
            True if starting shopping is allowed, False otherwise
        """
        return state == RunState.CONFIRMED

    def can_finish_adjusting(self, state: RunState) -> bool:
        """Check if finishing adjusting is allowed in the given state.

        Args:
            state: Current run state

        Returns:
            True if finishing adjusting is allowed, False otherwise
        """
        return state == RunState.ADJUSTING

    def can_view_shopping_list(self, state: RunState) -> bool:
        """Check if viewing shopping list is allowed in the given state.

        Args:
            state: Current run state

        Returns:
            True if viewing shopping list is allowed, False otherwise
        """
        return state in [RunState.SHOPPING, RunState.ADJUSTING, RunState.DISTRIBUTING, RunState.COMPLETED]

    def can_complete_shopping(self, state: RunState) -> bool:
        """Check if completing shopping is allowed in the given state.

        Args:
            state: Current run state

        Returns:
            True if completing shopping is allowed, False otherwise
        """
        return state == RunState.SHOPPING

    def can_view_distribution(self, state: RunState) -> bool:
        """Check if viewing distribution is allowed in the given state.

        Args:
            state: Current run state

        Returns:
            True if viewing distribution is allowed, False otherwise
        """
        return state in [RunState.DISTRIBUTING, RunState.COMPLETED]

    def can_complete_distribution(self, state: RunState) -> bool:
        """Check if completing distribution is allowed in the given state.

        Args:
            state: Current run state

        Returns:
            True if completing distribution is allowed, False otherwise
        """
        return state == RunState.DISTRIBUTING

    def is_active_run(self, state: RunState) -> bool:
        """Check if a run is in an active (non-terminal) state.

        Args:
            state: Current run state

        Returns:
            True if run is active, False if completed or cancelled
        """
        return state not in [RunState.COMPLETED, RunState.CANCELLED]

    def can_join_run(self, state: RunState) -> bool:
        """Check if new participants can join in the given state.

        Args:
            state: Current run state

        Returns:
            True if joining is allowed, False otherwise
        """
        return state in [RunState.PLANNING, RunState.ACTIVE]

    def get_action_error_message(self, action: str, current_state: RunState, allowed_states: list[RunState]) -> str:
        """Generate a consistent error message for invalid actions.

        Args:
            action: Name of the action being attempted
            current_state: Current run state
            allowed_states: List of states where the action is allowed

        Returns:
            Formatted error message
        """
        allowed_states_str = ', '.join([s.value for s in allowed_states])
        return (
            f'{action.capitalize()} not allowed in current run state. '
            f"Run is in '{current_state.value}' state, but must be in one of: {allowed_states_str}"
        )


# Create a singleton instance for convenience
state_machine = RunStateMachine()
