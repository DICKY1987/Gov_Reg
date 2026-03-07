# DOC_LINK: DOC-TEST-STATE-MACHINE-006
"""Unit tests for StateMachine

Tests state transitions, validation, and persistence.

DOC_ID: DOC-TEST-STATE-MACHINE-006
"""

import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from RUNTIME.doc_id.SUB_DOC_ID.orchestrator.state.state_machine import (
    State,
    StateTransition,
    StateMachine
)


class TestState:
    """Test State enum"""

    def test_state_values(self):
        """Test state enum values"""
        assert State.INITIAL.value == "INITIAL"
        assert State.DETECTING.value == "DETECTING"
        assert State.SUCCESS.value == "SUCCESS"
        assert State.FAILED.value == "FAILED"


class TestStateTransition:
    """Test StateTransition dataclass"""

    def test_state_transition_creation(self):
        """Test creating a state transition"""
        transition = StateTransition(
            from_state=State.INITIAL,
            to_state=State.DETECTING,
            timestamp="2026-01-10T00:00:00Z",
            reason="Test transition"
        )

        assert transition.from_state == State.INITIAL
        assert transition.to_state == State.DETECTING
        assert transition.reason == "Test transition"

    def test_state_transition_to_dict(self):
        """Test converting transition to dict"""
        transition = StateTransition(
            from_state=State.INITIAL,
            to_state=State.DETECTING,
            timestamp="2026-01-10T00:00:00Z"
        )

        result = transition.to_dict()

        assert result['from'] == "INITIAL"
        assert result['to'] == "DETECTING"
        assert result['at'] == "2026-01-10T00:00:00Z"


class TestStateMachine:
    """Test StateMachine"""

    def test_state_machine_initialization(self):
        """Test state machine starts in INITIAL state"""
        sm = StateMachine(context="test")

        assert sm.current_state == State.INITIAL
        assert sm.context == "test"
        assert sm.started_at is not None
        assert len(sm.transitions) == 0

    def test_valid_transition(self):
        """Test valid state transition"""
        sm = StateMachine(context="test")

        # INITIAL -> DETECTING is valid
        result = sm.transition(State.DETECTING)

        assert result is True
        assert sm.current_state == State.DETECTING
        assert len(sm.transitions) == 1
        assert sm.transitions[0].from_state == State.INITIAL
        assert sm.transitions[0].to_state == State.DETECTING

    def test_invalid_transition(self):
        """Test invalid state transition raises ValueError"""
        sm = StateMachine(context="test")

        # INITIAL -> SUCCESS is invalid (must go through workflow)
        with pytest.raises(ValueError) as exc_info:
            sm.transition(State.SUCCESS)

        assert "Invalid transition" in str(exc_info.value)
        assert sm.current_state == State.INITIAL  # State unchanged

    def test_transition_with_reason(self):
        """Test transition with reason"""
        sm = StateMachine(context="test")

        sm.transition(State.DETECTING, reason="Starting detection")

        assert sm.transitions[0].reason == "Starting detection"

    def test_complete_workflow_success_path(self):
        """Test complete successful workflow"""
        sm = StateMachine(context="test")

        # Success path: INITIAL -> DETECTING -> CLASSIFYING -> RESOLVING
        # -> REMEDIATING -> VALIDATING -> AGGREGATING -> GATE_DECISION
        # -> COMMIT -> SUCCESS

        sm.transition(State.DETECTING)
        sm.transition(State.CLASSIFYING)
        sm.transition(State.RESOLVING)
        sm.transition(State.REMEDIATING)
        sm.transition(State.VALIDATING)
        sm.transition(State.AGGREGATING)
        sm.transition(State.GATE_DECISION)
        sm.transition(State.COMMIT)
        sm.transition(State.SUCCESS)

        assert sm.current_state == State.SUCCESS
        assert len(sm.transitions) == 9
        assert sm.is_terminal()

    def test_complete_workflow_failure_path(self):
        """Test workflow with failure and rollback"""
        sm = StateMachine(context="test")

        # Failure path: INITIAL -> DETECTING -> CLASSIFYING -> RESOLVING
        # -> REMEDIATING -> ROLLBACK -> FAILED

        sm.transition(State.DETECTING)
        sm.transition(State.CLASSIFYING)
        sm.transition(State.RESOLVING)
        sm.transition(State.REMEDIATING)
        sm.transition(State.ROLLBACK)
        sm.transition(State.FAILED)

        assert sm.current_state == State.FAILED
        assert sm.is_terminal()

    def test_manual_intervention_path(self):
        """Test manual intervention required path"""
        sm = StateMachine(context="test")

        # INITIAL -> DETECTING -> CLASSIFYING -> RESOLVING -> MANUAL_REQUIRED
        sm.transition(State.DETECTING)
        sm.transition(State.CLASSIFYING)
        sm.transition(State.RESOLVING)
        sm.transition(State.MANUAL_REQUIRED, reason="Ambiguous identity")

        assert sm.current_state == State.MANUAL_REQUIRED

        # After user provides override, retry: MANUAL_REQUIRED -> RESOLVING
        sm.transition(State.RESOLVING)
        assert sm.current_state == State.RESOLVING

    def test_is_terminal(self):
        """Test terminal state detection"""
        sm = StateMachine(context="test")

        assert not sm.is_terminal()  # INITIAL is not terminal

        sm.transition(State.DETECTING)
        assert not sm.is_terminal()  # DETECTING is not terminal

        # Navigate to SUCCESS
        sm.transition(State.CLASSIFYING)
        sm.transition(State.RESOLVING)
        sm.transition(State.REMEDIATING)
        sm.transition(State.VALIDATING)
        sm.transition(State.AGGREGATING)
        sm.transition(State.GATE_DECISION)
        sm.transition(State.COMMIT)
        sm.transition(State.SUCCESS)

        assert sm.is_terminal()  # SUCCESS is terminal

    def test_add_evidence(self):
        """Test adding evidence files"""
        sm = StateMachine(context="test")

        sm.add_evidence("changes.json")
        sm.add_evidence("entities.json")
        sm.add_evidence("changes.json")  # Duplicate

        assert len(sm.evidence_files) == 2  # No duplicates
        assert "changes.json" in sm.evidence_files
        assert "entities.json" in sm.evidence_files

    def test_to_dict(self):
        """Test converting state machine to dict"""
        sm = StateMachine(context="test")
        sm.transition(State.DETECTING)
        sm.add_evidence("changes.json")

        result = sm.to_dict()

        assert result['current_state'] == "DETECTING"
        assert result['context'] == "test"
        assert result['started_at'] is not None
        assert len(result['transitions']) == 1
        assert result['evidence_files'] == ["changes.json"]

    def test_save_and_load(self):
        """Test saving and loading state machine"""
        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            # Create and save state machine
            sm = StateMachine(context="test")
            sm.transition(State.DETECTING, reason="Test")
            sm.add_evidence("changes.json")
            sm.save(output_dir)

            # Verify file created
            state_file = output_dir / 'state.json'
            assert state_file.exists()

            # Load state machine
            sm_loaded = StateMachine.load(state_file)

            assert sm_loaded.current_state == State.DETECTING
            assert sm_loaded.context == "test"
            assert len(sm_loaded.transitions) == 1
            assert sm_loaded.transitions[0].reason == "Test"
            assert sm_loaded.evidence_files == ["changes.json"]

    def test_no_changes_shortcut(self):
        """Test shortcut path when no changes detected"""
        sm = StateMachine(context="test")

        # DETECTING -> SUCCESS (shortcut when no changes)
        sm.transition(State.DETECTING)
        sm.transition(State.SUCCESS, reason="No changes")

        assert sm.current_state == State.SUCCESS
        assert len(sm.transitions) == 2


__doc_id__ = 'DOC-TEST-STATE-MACHINE-006'
