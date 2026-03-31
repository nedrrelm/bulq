"""Unit tests for RunState enum and RunStateMachine class.

Tests cover:
- RunState enum values and string representation
- State transition validation (valid and invalid transitions)
- Action permission methods for all run operations
- Helper methods for state information and error messages
"""

import pytest

from app.core import error_codes
from app.core.exceptions import BadRequestError
from app.core.run_state import RunState, RunStateMachine


class TestRunStateEnum:
    """Test the RunState enum."""

    def test_enum_values_are_correct_strings(self):
        """Test that enum values match expected string values."""
        assert RunState.PLANNING == 'planning'
        assert RunState.ACTIVE == 'active'
        assert RunState.CONFIRMED == 'confirmed'
        assert RunState.SHOPPING == 'shopping'
        assert RunState.ADJUSTING == 'adjusting'
        assert RunState.DISTRIBUTING == 'distributing'
        assert RunState.COMPLETED == 'completed'
        assert RunState.CANCELLED == 'cancelled'

    def test_enum_str_method_returns_value(self):
        """Test that __str__ method returns the enum value."""
        assert str(RunState.PLANNING) == 'planning'
        assert str(RunState.ACTIVE) == 'active'
        assert str(RunState.CONFIRMED) == 'confirmed'
        assert str(RunState.SHOPPING) == 'shopping'
        assert str(RunState.ADJUSTING) == 'adjusting'
        assert str(RunState.DISTRIBUTING) == 'distributing'
        assert str(RunState.COMPLETED) == 'completed'
        assert str(RunState.CANCELLED) == 'cancelled'

    def test_all_states_exist(self):
        """Test that all 8 expected states are defined."""
        expected_states = {
            'planning',
            'active',
            'confirmed',
            'shopping',
            'adjusting',
            'distributing',
            'completed',
            'cancelled',
        }
        actual_states = {state.value for state in RunState}
        assert actual_states == expected_states


class TestStateTransitions:
    """Test state transition validation."""

    @pytest.fixture
    def state_machine(self):
        """Create a RunStateMachine instance for testing."""
        return RunStateMachine()

    @pytest.mark.parametrize(
        'from_state,to_state',
        [
            # From PLANNING
            (RunState.PLANNING, RunState.ACTIVE),
            (RunState.PLANNING, RunState.CONFIRMED),
            (RunState.PLANNING, RunState.CANCELLED),
            # From ACTIVE
            (RunState.ACTIVE, RunState.CONFIRMED),
            (RunState.ACTIVE, RunState.PLANNING),
            (RunState.ACTIVE, RunState.CANCELLED),
            # From CONFIRMED
            (RunState.CONFIRMED, RunState.SHOPPING),
            (RunState.CONFIRMED, RunState.ACTIVE),
            (RunState.CONFIRMED, RunState.CANCELLED),
            # From SHOPPING
            (RunState.SHOPPING, RunState.ADJUSTING),
            (RunState.SHOPPING, RunState.DISTRIBUTING),
            (RunState.SHOPPING, RunState.CANCELLED),
            # From ADJUSTING
            (RunState.ADJUSTING, RunState.DISTRIBUTING),
            (RunState.ADJUSTING, RunState.CANCELLED),
            # From DISTRIBUTING
            (RunState.DISTRIBUTING, RunState.COMPLETED),
        ],
    )
    def test_valid_transitions(self, state_machine, from_state, to_state):
        """Test that all valid transitions return True."""
        assert state_machine.can_transition(from_state, to_state) is True

    @pytest.mark.parametrize(
        'from_state,to_state',
        [
            # Invalid from PLANNING
            (RunState.PLANNING, RunState.SHOPPING),
            (RunState.PLANNING, RunState.ADJUSTING),
            (RunState.PLANNING, RunState.DISTRIBUTING),
            (RunState.PLANNING, RunState.COMPLETED),
            (RunState.PLANNING, RunState.PLANNING),
            # Invalid from ACTIVE
            (RunState.ACTIVE, RunState.SHOPPING),
            (RunState.ACTIVE, RunState.ADJUSTING),
            (RunState.ACTIVE, RunState.DISTRIBUTING),
            (RunState.ACTIVE, RunState.COMPLETED),
            (RunState.ACTIVE, RunState.ACTIVE),
            # Invalid from CONFIRMED
            (RunState.CONFIRMED, RunState.PLANNING),
            (RunState.CONFIRMED, RunState.ADJUSTING),
            (RunState.CONFIRMED, RunState.DISTRIBUTING),
            (RunState.CONFIRMED, RunState.COMPLETED),
            (RunState.CONFIRMED, RunState.CONFIRMED),
            # Invalid from SHOPPING
            (RunState.SHOPPING, RunState.PLANNING),
            (RunState.SHOPPING, RunState.ACTIVE),
            (RunState.SHOPPING, RunState.CONFIRMED),
            (RunState.SHOPPING, RunState.COMPLETED),
            (RunState.SHOPPING, RunState.SHOPPING),
            # Invalid from ADJUSTING
            (RunState.ADJUSTING, RunState.PLANNING),
            (RunState.ADJUSTING, RunState.ACTIVE),
            (RunState.ADJUSTING, RunState.CONFIRMED),
            (RunState.ADJUSTING, RunState.SHOPPING),
            (RunState.ADJUSTING, RunState.COMPLETED),
            (RunState.ADJUSTING, RunState.ADJUSTING),
            # Invalid from DISTRIBUTING
            (RunState.DISTRIBUTING, RunState.PLANNING),
            (RunState.DISTRIBUTING, RunState.ACTIVE),
            (RunState.DISTRIBUTING, RunState.CONFIRMED),
            (RunState.DISTRIBUTING, RunState.SHOPPING),
            (RunState.DISTRIBUTING, RunState.ADJUSTING),
            (RunState.DISTRIBUTING, RunState.CANCELLED),
            (RunState.DISTRIBUTING, RunState.DISTRIBUTING),
            # From COMPLETED (terminal state)
            (RunState.COMPLETED, RunState.PLANNING),
            (RunState.COMPLETED, RunState.ACTIVE),
            (RunState.COMPLETED, RunState.CONFIRMED),
            (RunState.COMPLETED, RunState.SHOPPING),
            (RunState.COMPLETED, RunState.ADJUSTING),
            (RunState.COMPLETED, RunState.DISTRIBUTING),
            (RunState.COMPLETED, RunState.CANCELLED),
            (RunState.COMPLETED, RunState.COMPLETED),
            # From CANCELLED (terminal state)
            (RunState.CANCELLED, RunState.PLANNING),
            (RunState.CANCELLED, RunState.ACTIVE),
            (RunState.CANCELLED, RunState.CONFIRMED),
            (RunState.CANCELLED, RunState.SHOPPING),
            (RunState.CANCELLED, RunState.ADJUSTING),
            (RunState.CANCELLED, RunState.DISTRIBUTING),
            (RunState.CANCELLED, RunState.COMPLETED),
            (RunState.CANCELLED, RunState.CANCELLED),
        ],
    )
    def test_invalid_transitions(self, state_machine, from_state, to_state):
        """Test that all invalid transitions return False."""
        assert state_machine.can_transition(from_state, to_state) is False

    def test_validate_transition_raises_on_invalid_transition(self, state_machine):
        """Test that validate_transition raises BadRequestError on invalid transitions."""
        with pytest.raises(BadRequestError) as exc_info:
            state_machine.validate_transition(RunState.PLANNING, RunState.SHOPPING)

        assert exc_info.value.code == error_codes.INVALID_RUN_STATE_TRANSITION
        assert 'planning' in exc_info.value.message
        assert 'shopping' in exc_info.value.message
        assert exc_info.value.details['current_state'] == 'planning'
        assert exc_info.value.details['target_state'] == 'shopping'

    def test_validate_transition_with_run_id(self, state_machine):
        """Test that validate_transition includes run_id in error context."""
        run_id = 'test-run-123'
        with pytest.raises(BadRequestError) as exc_info:
            state_machine.validate_transition(RunState.COMPLETED, RunState.ACTIVE, run_id=run_id)

        assert exc_info.value.code == error_codes.INVALID_RUN_STATE_TRANSITION

    def test_validate_transition_passes_for_valid_transition(self, state_machine):
        """Test that validate_transition does not raise for valid transitions."""
        # Should not raise any exception
        state_machine.validate_transition(RunState.PLANNING, RunState.ACTIVE)
        state_machine.validate_transition(RunState.ACTIVE, RunState.CONFIRMED)
        state_machine.validate_transition(RunState.SHOPPING, RunState.DISTRIBUTING)

    def test_terminal_states_have_no_valid_transitions(self, state_machine):
        """Test that COMPLETED and CANCELLED are terminal states."""
        assert state_machine.get_valid_transitions(RunState.COMPLETED) == []
        assert state_machine.get_valid_transitions(RunState.CANCELLED) == []

    def test_terminal_state_error_message_shows_none(self, state_machine):
        """Test that error message for terminal states shows 'none' as valid transitions."""
        with pytest.raises(BadRequestError) as exc_info:
            state_machine.validate_transition(RunState.COMPLETED, RunState.ACTIVE)

        assert 'none' in exc_info.value.message.lower()


class TestActionPermissions:
    """Test action permission validation methods."""

    @pytest.fixture
    def state_machine(self):
        """Create a RunStateMachine instance for testing."""
        return RunStateMachine()

    @pytest.mark.parametrize(
        'state,expected',
        [
            (RunState.PLANNING, True),
            (RunState.ACTIVE, True),
            (RunState.CONFIRMED, False),
            (RunState.SHOPPING, False),
            (RunState.ADJUSTING, True),
            (RunState.DISTRIBUTING, False),
            (RunState.COMPLETED, False),
            (RunState.CANCELLED, False),
        ],
    )
    def test_can_place_bid(self, state_machine, state, expected):
        """Test can_place_bid for all states."""
        assert state_machine.can_place_bid(state) == expected

    @pytest.mark.parametrize(
        'state,expected',
        [
            (RunState.PLANNING, True),
            (RunState.ACTIVE, True),
            (RunState.CONFIRMED, False),
            (RunState.SHOPPING, False),
            (RunState.ADJUSTING, True),
            (RunState.DISTRIBUTING, False),
            (RunState.COMPLETED, False),
            (RunState.CANCELLED, False),
        ],
    )
    def test_can_retract_bid(self, state_machine, state, expected):
        """Test can_retract_bid for all states."""
        assert state_machine.can_retract_bid(state) == expected

    @pytest.mark.parametrize(
        'state,expected',
        [
            (RunState.PLANNING, False),
            (RunState.ACTIVE, True),
            (RunState.CONFIRMED, False),
            (RunState.SHOPPING, False),
            (RunState.ADJUSTING, False),
            (RunState.DISTRIBUTING, False),
            (RunState.COMPLETED, False),
            (RunState.CANCELLED, False),
        ],
    )
    def test_can_toggle_ready(self, state_machine, state, expected):
        """Test can_toggle_ready for all states."""
        assert state_machine.can_toggle_ready(state) == expected

    @pytest.mark.parametrize(
        'state,expected',
        [
            (RunState.PLANNING, False),
            (RunState.ACTIVE, False),
            (RunState.CONFIRMED, True),
            (RunState.SHOPPING, False),
            (RunState.ADJUSTING, False),
            (RunState.DISTRIBUTING, False),
            (RunState.COMPLETED, False),
            (RunState.CANCELLED, False),
        ],
    )
    def test_can_start_shopping(self, state_machine, state, expected):
        """Test can_start_shopping for all states."""
        assert state_machine.can_start_shopping(state) == expected

    @pytest.mark.parametrize(
        'state,expected',
        [
            (RunState.PLANNING, True),
            (RunState.ACTIVE, True),
            (RunState.CONFIRMED, True),
            (RunState.SHOPPING, True),
            (RunState.ADJUSTING, True),
            (RunState.DISTRIBUTING, False),
            (RunState.COMPLETED, False),
            (RunState.CANCELLED, False),
        ],
    )
    def test_can_cancel(self, state_machine, state, expected):
        """Test can_cancel for all states."""
        assert state_machine.can_cancel(state) == expected

    @pytest.mark.parametrize(
        'state,expected',
        [
            (RunState.PLANNING, True),
            (RunState.ACTIVE, True),
            (RunState.CONFIRMED, False),
            (RunState.SHOPPING, False),
            (RunState.ADJUSTING, False),
            (RunState.DISTRIBUTING, False),
            (RunState.COMPLETED, False),
            (RunState.CANCELLED, False),
        ],
    )
    def test_can_join_run(self, state_machine, state, expected):
        """Test can_join_run for all states."""
        assert state_machine.can_join_run(state) == expected

    @pytest.mark.parametrize(
        'state,expected',
        [
            (RunState.PLANNING, False),
            (RunState.ACTIVE, False),
            (RunState.CONFIRMED, False),
            (RunState.SHOPPING, True),
            (RunState.ADJUSTING, True),
            (RunState.DISTRIBUTING, True),
            (RunState.COMPLETED, True),
            (RunState.CANCELLED, False),
        ],
    )
    def test_can_view_shopping_list(self, state_machine, state, expected):
        """Test can_view_shopping_list for all states."""
        assert state_machine.can_view_shopping_list(state) == expected

    @pytest.mark.parametrize(
        'state,expected',
        [
            (RunState.PLANNING, False),
            (RunState.ACTIVE, False),
            (RunState.CONFIRMED, False),
            (RunState.SHOPPING, True),
            (RunState.ADJUSTING, False),
            (RunState.DISTRIBUTING, False),
            (RunState.COMPLETED, False),
            (RunState.CANCELLED, False),
        ],
    )
    def test_can_complete_shopping(self, state_machine, state, expected):
        """Test can_complete_shopping for all states."""
        assert state_machine.can_complete_shopping(state) == expected

    @pytest.mark.parametrize(
        'state,expected',
        [
            (RunState.PLANNING, False),
            (RunState.ACTIVE, False),
            (RunState.CONFIRMED, False),
            (RunState.SHOPPING, False),
            (RunState.ADJUSTING, False),
            (RunState.DISTRIBUTING, True),
            (RunState.COMPLETED, True),
            (RunState.CANCELLED, False),
        ],
    )
    def test_can_view_distribution(self, state_machine, state, expected):
        """Test can_view_distribution for all states."""
        assert state_machine.can_view_distribution(state) == expected

    @pytest.mark.parametrize(
        'state,expected',
        [
            (RunState.PLANNING, False),
            (RunState.ACTIVE, False),
            (RunState.CONFIRMED, False),
            (RunState.SHOPPING, False),
            (RunState.ADJUSTING, False),
            (RunState.DISTRIBUTING, True),
            (RunState.COMPLETED, False),
            (RunState.CANCELLED, False),
        ],
    )
    def test_can_complete_distribution(self, state_machine, state, expected):
        """Test can_complete_distribution for all states."""
        assert state_machine.can_complete_distribution(state) == expected

    @pytest.mark.parametrize(
        'state,expected',
        [
            (RunState.PLANNING, True),
            (RunState.ACTIVE, True),
            (RunState.CONFIRMED, True),
            (RunState.SHOPPING, True),
            (RunState.ADJUSTING, True),
            (RunState.DISTRIBUTING, True),
            (RunState.COMPLETED, False),
            (RunState.CANCELLED, False),
        ],
    )
    def test_is_active_run(self, state_machine, state, expected):
        """Test is_active_run for all states."""
        assert state_machine.is_active_run(state) == expected

    @pytest.mark.parametrize(
        'state,expected',
        [
            (RunState.PLANNING, False),
            (RunState.ACTIVE, False),
            (RunState.CONFIRMED, False),
            (RunState.SHOPPING, False),
            (RunState.ADJUSTING, False),
            (RunState.DISTRIBUTING, False),
            (RunState.COMPLETED, True),
            (RunState.CANCELLED, True),
        ],
    )
    def test_is_terminal_state(self, state_machine, state, expected):
        """Test is_terminal_state for all states."""
        assert state_machine.is_terminal_state(state) == expected


class TestHelperMethods:
    """Test helper methods for state information."""

    @pytest.fixture
    def state_machine(self):
        """Create a RunStateMachine instance for testing."""
        return RunStateMachine()

    def test_get_valid_transitions_planning(self, state_machine):
        """Test get_valid_transitions returns correct list for PLANNING state."""
        transitions = state_machine.get_valid_transitions(RunState.PLANNING)
        assert set(transitions) == {
            RunState.ACTIVE,
            RunState.CONFIRMED,
            RunState.CANCELLED,
        }

    def test_get_valid_transitions_active(self, state_machine):
        """Test get_valid_transitions returns correct list for ACTIVE state."""
        transitions = state_machine.get_valid_transitions(RunState.ACTIVE)
        assert set(transitions) == {
            RunState.CONFIRMED,
            RunState.PLANNING,
            RunState.CANCELLED,
        }

    def test_get_valid_transitions_confirmed(self, state_machine):
        """Test get_valid_transitions returns correct list for CONFIRMED state."""
        transitions = state_machine.get_valid_transitions(RunState.CONFIRMED)
        assert set(transitions) == {
            RunState.SHOPPING,
            RunState.ACTIVE,
            RunState.CANCELLED,
        }

    def test_get_valid_transitions_shopping(self, state_machine):
        """Test get_valid_transitions returns correct list for SHOPPING state."""
        transitions = state_machine.get_valid_transitions(RunState.SHOPPING)
        assert set(transitions) == {
            RunState.ADJUSTING,
            RunState.DISTRIBUTING,
            RunState.CANCELLED,
        }

    def test_get_valid_transitions_adjusting(self, state_machine):
        """Test get_valid_transitions returns correct list for ADJUSTING state."""
        transitions = state_machine.get_valid_transitions(RunState.ADJUSTING)
        assert set(transitions) == {RunState.DISTRIBUTING, RunState.CANCELLED}

    def test_get_valid_transitions_distributing(self, state_machine):
        """Test get_valid_transitions returns correct list for DISTRIBUTING state."""
        transitions = state_machine.get_valid_transitions(RunState.DISTRIBUTING)
        assert transitions == [RunState.COMPLETED]

    def test_get_valid_transitions_completed(self, state_machine):
        """Test get_valid_transitions returns empty list for COMPLETED state."""
        transitions = state_machine.get_valid_transitions(RunState.COMPLETED)
        assert transitions == []

    def test_get_valid_transitions_cancelled(self, state_machine):
        """Test get_valid_transitions returns empty list for CANCELLED state."""
        transitions = state_machine.get_valid_transitions(RunState.CANCELLED)
        assert transitions == []

    @pytest.mark.parametrize(
        'state,expected_description',
        [
            (RunState.PLANNING, 'Leader is planning the run'),
            (RunState.ACTIVE, 'Users are actively placing bids'),
            (RunState.CONFIRMED, 'All users ready, awaiting shopping trip'),
            (RunState.SHOPPING, 'Shopping trip in progress'),
            (RunState.ADJUSTING, 'Adjusting bids due to insufficient quantities'),
            (RunState.DISTRIBUTING, 'Items being distributed to members'),
            (RunState.COMPLETED, 'Run completed successfully'),
            (RunState.CANCELLED, 'Run was cancelled'),
        ],
    )
    def test_get_state_description(self, state_machine, state, expected_description):
        """Test get_state_description returns human-readable descriptions."""
        assert state_machine.get_state_description(state) == expected_description

    def test_get_action_error_message_formats_correctly(self, state_machine):
        """Test get_action_error_message formats error message correctly."""
        action = 'place bid'
        current_state = RunState.CONFIRMED
        allowed_states = [RunState.PLANNING, RunState.ACTIVE, RunState.ADJUSTING]

        error_msg = state_machine.get_action_error_message(action, current_state, allowed_states)

        assert 'Place bid' in error_msg
        assert 'confirmed' in error_msg
        assert 'planning' in error_msg
        assert 'active' in error_msg
        assert 'adjusting' in error_msg

    def test_get_action_error_message_capitalizes_action(self, state_machine):
        """Test get_action_error_message capitalizes the action name."""
        error_msg = state_machine.get_action_error_message(
            'view shopping list', RunState.PLANNING, [RunState.SHOPPING]
        )

        assert error_msg.startswith('View shopping list')

    def test_get_action_error_message_includes_current_state(self, state_machine):
        """Test get_action_error_message includes current state in message."""
        error_msg = state_machine.get_action_error_message(
            'complete distribution', RunState.SHOPPING, [RunState.DISTRIBUTING]
        )

        assert "'shopping'" in error_msg

    def test_get_action_error_message_lists_all_allowed_states(self, state_machine):
        """Test get_action_error_message lists all allowed states."""
        allowed_states = [RunState.PLANNING, RunState.ACTIVE, RunState.ADJUSTING]
        error_msg = state_machine.get_action_error_message(
            'place bid', RunState.CONFIRMED, allowed_states
        )

        for state in allowed_states:
            assert state.value in error_msg


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.fixture
    def state_machine(self):
        """Create a RunStateMachine instance for testing."""
        return RunStateMachine()

    def test_can_transition_with_same_state(self, state_machine):
        """Test that transitions to the same state are invalid."""
        for state in RunState:
            assert state_machine.can_transition(state, state) is False

    def test_validate_transition_without_run_id(self, state_machine):
        """Test validate_transition works without run_id parameter."""
        with pytest.raises(BadRequestError):
            state_machine.validate_transition(RunState.COMPLETED, RunState.PLANNING)

    def test_multiple_state_machines_are_independent(self):
        """Test that multiple RunStateMachine instances work independently."""
        sm1 = RunStateMachine()
        sm2 = RunStateMachine()

        # Both should have the same behavior
        assert sm1.can_transition(RunState.PLANNING, RunState.ACTIVE) == sm2.can_transition(
            RunState.PLANNING, RunState.ACTIVE
        )
        assert sm1.get_state_description(RunState.PLANNING) == sm2.get_state_description(
            RunState.PLANNING
        )

    def test_singleton_state_machine_exists(self):
        """Test that the singleton state_machine instance exists and works."""
        from app.core.run_state import state_machine

        assert isinstance(state_machine, RunStateMachine)
        assert state_machine.can_transition(RunState.PLANNING, RunState.ACTIVE) is True

    def test_can_finish_adjusting_method(self, state_machine):
        """Test can_finish_adjusting method for all states."""
        # Only ADJUSTING state should return True
        assert state_machine.can_finish_adjusting(RunState.ADJUSTING) is True

        # All other states should return False
        for state in RunState:
            if state != RunState.ADJUSTING:
                assert state_machine.can_finish_adjusting(state) is False
