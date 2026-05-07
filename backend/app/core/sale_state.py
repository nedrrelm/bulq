"""Sale state machine for managing sale state transitions."""

from enum import StrEnum

from app.core import error_codes
from app.core.exceptions import BadRequestError
from app.infrastructure.request_context import get_logger

logger = get_logger(__name__)


class SaleState(StrEnum):
    """Sale state enum."""

    PLANNING = 'planning'
    ACTIVE = 'active'
    CONFIRMED = 'confirmed'
    SHOPPING = 'shopping'
    DISTRIBUTING = 'distributing'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'

    def __str__(self) -> str:
        return self.value


class SaleStateMachine:
    """State machine for managing sale state transitions."""

    VALID_TRANSITIONS = {
        SaleState.PLANNING: [SaleState.ACTIVE, SaleState.CANCELLED],
        SaleState.ACTIVE: [SaleState.CONFIRMED, SaleState.PLANNING, SaleState.CANCELLED],
        SaleState.CONFIRMED: [SaleState.DISTRIBUTING, SaleState.ACTIVE, SaleState.CANCELLED],
        SaleState.DISTRIBUTING: [SaleState.COMPLETED],
        SaleState.COMPLETED: [],
        SaleState.CANCELLED: [],
    }

    def can_transition(self, from_state: SaleState, to_state: SaleState) -> bool:
        valid_next_states = self.VALID_TRANSITIONS.get(from_state, [])
        return to_state in valid_next_states

    def validate_transition(
        self, from_state: SaleState, to_state: SaleState, sale_id: str | None = None
    ) -> None:
        if not self.can_transition(from_state, to_state):
            valid_states = self.VALID_TRANSITIONS.get(from_state, [])
            valid_states_str = (
                ', '.join([s.value for s in valid_states]) if valid_states else 'none'
            )

            logger.warning(
                'Invalid sale state transition attempted',
                extra={
                    'sale_id': sale_id,
                    'from_state': from_state.value,
                    'to_state': to_state.value,
                },
            )

            raise BadRequestError(
                code=error_codes.SALE_INVALID_STATE,
                message=(
                    f'Invalid state transition from {from_state.value} to {to_state.value}. '
                    f'Valid transitions: {valid_states_str}'
                ),
                current_state=from_state.value,
                target_state=to_state.value,
            )

    def is_terminal_state(self, state: SaleState) -> bool:
        return len(self.VALID_TRANSITIONS.get(state, [])) == 0

    def can_cancel(self, state: SaleState) -> bool:
        return SaleState.CANCELLED in self.VALID_TRANSITIONS.get(state, [])

    def can_edit_products(self, state: SaleState) -> bool:
        return state == SaleState.PLANNING


sale_state_machine = SaleStateMachine()
