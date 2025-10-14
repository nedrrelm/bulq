"""
Tests for run state machine logic and business rules.
"""
import pytest
from app.core.run_state import RunState, RunStateMachine, state_machine


class TestRunStateMachine:
    """Tests for RunStateMachine"""

    def test_valid_transition_planning_to_active(self):
        """Test valid transition from planning to active"""
        sm = RunStateMachine()
        assert sm.can_transition(RunState.PLANNING, RunState.ACTIVE) is True

    def test_valid_transition_active_to_confirmed(self):
        """Test valid transition from active to confirmed"""
        sm = RunStateMachine()
        assert sm.can_transition(RunState.ACTIVE, RunState.CONFIRMED) is True

    def test_valid_transition_confirmed_to_shopping(self):
        """Test valid transition from confirmed to shopping"""
        sm = RunStateMachine()
        assert sm.can_transition(RunState.CONFIRMED, RunState.SHOPPING) is True

    def test_valid_transition_shopping_to_distributing(self):
        """Test valid transition from shopping to distributing"""
        sm = RunStateMachine()
        assert sm.can_transition(RunState.SHOPPING, RunState.DISTRIBUTING) is True

    def test_valid_transition_shopping_to_adjusting(self):
        """Test valid transition from shopping to adjusting"""
        sm = RunStateMachine()
        assert sm.can_transition(RunState.SHOPPING, RunState.ADJUSTING) is True

    def test_valid_transition_adjusting_to_distributing(self):
        """Test valid transition from adjusting to distributing"""
        sm = RunStateMachine()
        assert sm.can_transition(RunState.ADJUSTING, RunState.DISTRIBUTING) is True

    def test_valid_transition_distributing_to_completed(self):
        """Test valid transition from distributing to completed"""
        sm = RunStateMachine()
        assert sm.can_transition(RunState.DISTRIBUTING, RunState.COMPLETED) is True

    def test_invalid_transition_planning_to_shopping(self):
        """Test invalid transition from planning directly to shopping"""
        sm = RunStateMachine()
        assert sm.can_transition(RunState.PLANNING, RunState.SHOPPING) is False

    def test_invalid_transition_planning_to_completed(self):
        """Test invalid transition from planning directly to completed"""
        sm = RunStateMachine()
        assert sm.can_transition(RunState.PLANNING, RunState.COMPLETED) is False

    def test_invalid_transition_completed_to_any(self):
        """Test that completed state cannot transition to any state"""
        sm = RunStateMachine()
        assert sm.can_transition(RunState.COMPLETED, RunState.PLANNING) is False
        assert sm.can_transition(RunState.COMPLETED, RunState.ACTIVE) is False
        assert sm.can_transition(RunState.COMPLETED, RunState.CANCELLED) is False

    def test_invalid_transition_cancelled_to_any(self):
        """Test that cancelled state cannot transition to any state"""
        sm = RunStateMachine()
        assert sm.can_transition(RunState.CANCELLED, RunState.PLANNING) is False
        assert sm.can_transition(RunState.CANCELLED, RunState.ACTIVE) is False
        assert sm.can_transition(RunState.CANCELLED, RunState.COMPLETED) is False

    def test_can_cancel_from_planning(self):
        """Test that runs can be cancelled from planning state"""
        sm = RunStateMachine()
        assert sm.can_cancel(RunState.PLANNING) is True

    def test_can_cancel_from_active(self):
        """Test that runs can be cancelled from active state"""
        sm = RunStateMachine()
        assert sm.can_cancel(RunState.ACTIVE) is True

    def test_can_cancel_from_confirmed(self):
        """Test that runs can be cancelled from confirmed state"""
        sm = RunStateMachine()
        assert sm.can_cancel(RunState.CONFIRMED) is True

    def test_can_cancel_from_shopping(self):
        """Test that runs can be cancelled from shopping state"""
        sm = RunStateMachine()
        assert sm.can_cancel(RunState.SHOPPING) is True

    def test_can_cancel_from_adjusting(self):
        """Test that runs can be cancelled from adjusting state"""
        sm = RunStateMachine()
        assert sm.can_cancel(RunState.ADJUSTING) is True

    def test_cannot_cancel_from_distributing(self):
        """Test that runs cannot be cancelled from distributing state"""
        sm = RunStateMachine()
        assert sm.can_cancel(RunState.DISTRIBUTING) is False

    def test_cannot_cancel_from_completed(self):
        """Test that runs cannot be cancelled from completed state"""
        sm = RunStateMachine()
        assert sm.can_cancel(RunState.COMPLETED) is False

    def test_get_valid_transitions_planning(self):
        """Test getting valid transitions from planning state"""
        sm = RunStateMachine()
        transitions = sm.get_valid_transitions(RunState.PLANNING)
        assert RunState.ACTIVE in transitions
        assert RunState.CANCELLED in transitions
        assert len(transitions) == 2

    def test_get_valid_transitions_active(self):
        """Test getting valid transitions from active state"""
        sm = RunStateMachine()
        transitions = sm.get_valid_transitions(RunState.ACTIVE)
        assert RunState.CONFIRMED in transitions
        assert RunState.PLANNING in transitions
        assert RunState.CANCELLED in transitions
        assert len(transitions) == 3

    def test_get_valid_transitions_shopping(self):
        """Test getting valid transitions from shopping state"""
        sm = RunStateMachine()
        transitions = sm.get_valid_transitions(RunState.SHOPPING)
        assert RunState.ADJUSTING in transitions
        assert RunState.DISTRIBUTING in transitions
        assert RunState.CANCELLED in transitions
        assert len(transitions) == 3

    def test_get_valid_transitions_completed(self):
        """Test that completed state has no valid transitions"""
        sm = RunStateMachine()
        transitions = sm.get_valid_transitions(RunState.COMPLETED)
        assert len(transitions) == 0

    def test_is_terminal_state_completed(self):
        """Test that completed is a terminal state"""
        sm = RunStateMachine()
        assert sm.is_terminal_state(RunState.COMPLETED) is True

    def test_is_terminal_state_cancelled(self):
        """Test that cancelled is a terminal state"""
        sm = RunStateMachine()
        assert sm.is_terminal_state(RunState.CANCELLED) is True

    def test_is_not_terminal_state_planning(self):
        """Test that planning is not a terminal state"""
        sm = RunStateMachine()
        assert sm.is_terminal_state(RunState.PLANNING) is False

    def test_is_not_terminal_state_active(self):
        """Test that active is not a terminal state"""
        sm = RunStateMachine()
        assert sm.is_terminal_state(RunState.ACTIVE) is False

    def test_validate_transition_success(self):
        """Test validate_transition with valid transition"""
        sm = RunStateMachine()
        # Should not raise
        sm.validate_transition(RunState.PLANNING, RunState.ACTIVE)

    def test_validate_transition_failure(self):
        """Test validate_transition with invalid transition"""
        sm = RunStateMachine()
        with pytest.raises(ValueError) as exc:
            sm.validate_transition(RunState.PLANNING, RunState.SHOPPING)
        assert "Invalid state transition" in str(exc.value)

    def test_validate_transition_with_run_id(self):
        """Test validate_transition includes run_id in error"""
        sm = RunStateMachine()
        with pytest.raises(ValueError) as exc:
            sm.validate_transition(
                RunState.PLANNING,
                RunState.COMPLETED,
                run_id="test-run-123"
            )
        assert "Invalid state transition" in str(exc.value)

    def test_get_state_description(self):
        """Test getting state descriptions"""
        sm = RunStateMachine()
        assert len(sm.get_state_description(RunState.PLANNING)) > 0
        assert len(sm.get_state_description(RunState.ACTIVE)) > 0
        assert len(sm.get_state_description(RunState.COMPLETED)) > 0

    def test_state_enum_string_conversion(self):
        """Test that RunState enum can be used as string"""
        assert str(RunState.PLANNING) == "planning"
        assert str(RunState.ACTIVE) == "active"
        assert str(RunState.COMPLETED) == "completed"

    def test_singleton_state_machine(self):
        """Test that singleton state_machine is available"""
        assert state_machine is not None
        assert isinstance(state_machine, RunStateMachine)

    def test_backward_transition_active_to_planning(self):
        """Test backward transition from active to planning is allowed"""
        sm = RunStateMachine()
        assert sm.can_transition(RunState.ACTIVE, RunState.PLANNING) is True

    def test_backward_transition_confirmed_to_active(self):
        """Test backward transition from confirmed to active is allowed"""
        sm = RunStateMachine()
        assert sm.can_transition(RunState.CONFIRMED, RunState.ACTIVE) is True

    def test_complete_happy_path_flow(self):
        """Test complete flow through all states (happy path)"""
        sm = RunStateMachine()

        # planning -> active
        assert sm.can_transition(RunState.PLANNING, RunState.ACTIVE) is True

        # active -> confirmed
        assert sm.can_transition(RunState.ACTIVE, RunState.CONFIRMED) is True

        # confirmed -> shopping
        assert sm.can_transition(RunState.CONFIRMED, RunState.SHOPPING) is True

        # shopping -> distributing (no adjustment needed)
        assert sm.can_transition(RunState.SHOPPING, RunState.DISTRIBUTING) is True

        # distributing -> completed
        assert sm.can_transition(RunState.DISTRIBUTING, RunState.COMPLETED) is True

    def test_complete_adjusting_flow(self):
        """Test complete flow with adjusting state"""
        sm = RunStateMachine()

        # planning -> active
        assert sm.can_transition(RunState.PLANNING, RunState.ACTIVE) is True

        # active -> confirmed
        assert sm.can_transition(RunState.ACTIVE, RunState.CONFIRMED) is True

        # confirmed -> shopping
        assert sm.can_transition(RunState.CONFIRMED, RunState.SHOPPING) is True

        # shopping -> adjusting (insufficient quantities)
        assert sm.can_transition(RunState.SHOPPING, RunState.ADJUSTING) is True

        # adjusting -> distributing
        assert sm.can_transition(RunState.ADJUSTING, RunState.DISTRIBUTING) is True

        # distributing -> completed
        assert sm.can_transition(RunState.DISTRIBUTING, RunState.COMPLETED) is True

    def test_cancellation_flow(self):
        """Test that runs can be cancelled from early states"""
        sm = RunStateMachine()

        # Can cancel from planning
        assert sm.can_transition(RunState.PLANNING, RunState.CANCELLED) is True

        # Can cancel from active
        assert sm.can_transition(RunState.ACTIVE, RunState.CANCELLED) is True

        # Can cancel from confirmed
        assert sm.can_transition(RunState.CONFIRMED, RunState.CANCELLED) is True

        # Can cancel from shopping
        assert sm.can_transition(RunState.SHOPPING, RunState.CANCELLED) is True

        # Cannot cancel from distributing
        assert sm.can_transition(RunState.DISTRIBUTING, RunState.CANCELLED) is False


class TestRunStateBusinessLogic:
    """Tests for business logic related to run states"""

    def test_all_states_have_descriptions(self):
        """Test that all states have descriptions"""
        sm = RunStateMachine()
        for state in RunState:
            description = sm.get_state_description(state)
            assert description is not None
            assert len(description) > 0
            assert description != "Unknown state"

    def test_all_states_have_transition_rules(self):
        """Test that all states have defined transition rules"""
        sm = RunStateMachine()
        for state in RunState:
            transitions = sm.get_valid_transitions(state)
            assert transitions is not None  # Even empty list is valid

    def test_no_self_transitions(self):
        """Test that states cannot transition to themselves"""
        sm = RunStateMachine()
        for state in RunState:
            assert sm.can_transition(state, state) is False

    def test_terminal_states_have_no_transitions(self):
        """Test that terminal states have no valid transitions"""
        sm = RunStateMachine()
        terminal_states = [RunState.COMPLETED, RunState.CANCELLED]
        for state in terminal_states:
            transitions = sm.get_valid_transitions(state)
            assert len(transitions) == 0
            assert sm.is_terminal_state(state) is True

    def test_non_terminal_states_have_transitions(self):
        """Test that non-terminal states have at least one valid transition"""
        sm = RunStateMachine()
        non_terminal_states = [
            RunState.PLANNING,
            RunState.ACTIVE,
            RunState.CONFIRMED,
            RunState.SHOPPING,
            RunState.ADJUSTING,
            RunState.DISTRIBUTING,
        ]
        for state in non_terminal_states:
            transitions = sm.get_valid_transitions(state)
            assert len(transitions) > 0
            assert sm.is_terminal_state(state) is False
