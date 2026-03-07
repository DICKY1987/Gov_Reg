# DOC_LINK: DOC-CORE-ENGINE-STATE-MACHINE-159
"""Run State Machine - WS-03-01A

Implements the state machine for run lifecycle following COOPERATION_SPEC.
Defines valid state transitions and transition logic.
"""

# DOC_ID: DOC-CORE-ENGINE-STATE-MACHINE-159

import sys
from enum import Enum
from pathlib import Path
from typing import Dict, Optional, Set

# Event emission (Phase 3: Observability)
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
try:
    )
    from event_emitter import get_event_emitter
    EVENT_SYSTEM_AVAILABLE = True
except ImportError:
    EVENT_SYSTEM_AVAILABLE = False
    def get_event_emitter():
        return None

def _emit_event(subsystem: str, step_id: str, subject: str, summary: str,
                severity: str = "INFO", details: dict = None):
    """Helper to emit events with graceful degradation if event system unavailable."""
    if EVENT_SYSTEM_AVAILABLE:
        try:
            emitter = get_event_emitter()
            if emitter:
                emitter.emit(
                    subsystem=subsystem,
                    step_id=step_id,
                    subject=subject,
                    summary=summary,
                    severity=severity,
                    details=details or {}
                )
        except Exception:
            pass  # Gracefully degrade if event system fails


class RunState(Enum):
    """Valid states for a run"""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    QUARANTINED = "quarantined"
    CANCELED = "canceled"


class StepState(Enum):
    """Valid states for a step attempt"""

    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"


class RunStateMachine:
    """State machine for run lifecycle"""

    # Define valid state transitions
    TRANSITIONS: Dict[RunState, Set[RunState]] = {
        RunState.PENDING: {RunState.RUNNING, RunState.CANCELED},
        RunState.RUNNING: {
            RunState.SUCCEEDED,
            RunState.FAILED,
            RunState.QUARANTINED,
            RunState.CANCELED,
        },
        RunState.SUCCEEDED: set(),  # Terminal state
        RunState.FAILED: {
            RunState.QUARANTINED,  # Can quarantine a failed run
        },
        RunState.QUARANTINED: set(),  # Terminal state
        RunState.CANCELED: set(),  # Terminal state
    }

    # Terminal states (cannot transition out)
    TERMINAL_STATES = {RunState.SUCCEEDED, RunState.QUARANTINED, RunState.CANCELED}

    @classmethod
    def can_transition(cls, from_state: str, to_state: str) -> bool:
        """Check if a state transition is valid"""
        try:
            from_enum = RunState(from_state)
            to_enum = RunState(to_state)
        except ValueError:
            return False

        can_transition_result = to_enum in cls.TRANSITIONS.get(from_enum, set())

        # Emit state transition event
        if can_transition_result:
            _emit_event(
                subsystem="PHASE_5_EXECUTION",
                step_id="STATE_TRANSITION",
                subject="run_state_machine",
                summary=f"Run state transition: {from_state} -> {to_state}",
                severity="INFO",
                details={"from_state": from_state, "to_state": to_state, "valid": True}
            )

        return can_transition_result

    @classmethod
    def is_terminal(cls, state: str) -> bool:
        """Check if a state is terminal"""
        try:
            state_enum = RunState(state)
            return state_enum in cls.TERMINAL_STATES
        except ValueError:
            return False

    @classmethod
    def validate_transition(cls, from_state: str, to_state: str) -> Optional[str]:
        """
        Validate a transition and return error message if invalid.

        Returns:
            None if valid, error message string if invalid
        """
        # Check if states are valid
        try:
            from_enum = RunState(from_state)
            to_enum = RunState(to_state)
        except ValueError as e:
            error_msg = f"Invalid state: {e}"
            _emit_event(
                subsystem="PHASE_5_EXECUTION",
                step_id="STATE_TRANSITION_INVALID",
                subject="run_state_machine",
                summary=f"Invalid state transition attempted: {from_state} -> {to_state}",
                severity="ERROR",
                details={"from_state": from_state, "to_state": to_state, "error": error_msg}
            )
            return error_msg

        # Check if already in terminal state
        if cls.is_terminal(from_state):
            error_msg = f"Cannot transition from terminal state '{from_state}'"
            _emit_event(
                subsystem="PHASE_5_EXECUTION",
                step_id="STATE_TRANSITION_INVALID",
                subject="run_state_machine",
                summary=f"Cannot transition from terminal state: {from_state}",
                severity="ERROR",
                details={"from_state": from_state, "to_state": to_state, "error": error_msg}
            )
            return error_msg

        # Check if transition is allowed
        if not cls.can_transition(from_state, to_state):
            error_msg = f"Invalid transition: '{from_state}' -> '{to_state}'"
            _emit_event(
                subsystem="PHASE_5_EXECUTION",
                step_id="STATE_TRANSITION_INVALID",
                subject="run_state_machine",
                summary=f"Invalid state transition: {from_state} -> {to_state}",
                severity="ERROR",
                details={"from_state": from_state, "to_state": to_state, "error": error_msg}
            )
            return error_msg

        return None


class StepStateMachine:
    """State machine for step attempt lifecycle"""

    TRANSITIONS: Dict[StepState, Set[StepState]] = {
        StepState.RUNNING: {StepState.SUCCEEDED, StepState.FAILED, StepState.CANCELED},
        StepState.SUCCEEDED: set(),  # Terminal
        StepState.FAILED: set(),  # Terminal
        StepState.CANCELED: set(),  # Terminal
    }

    TERMINAL_STATES = {StepState.SUCCEEDED, StepState.FAILED, StepState.CANCELED}

    @classmethod
    def can_transition(cls, from_state: str, to_state: str) -> bool:
        """Check if a state transition is valid"""
        try:
            from_enum = StepState(from_state)
            to_enum = StepState(to_state)
        except ValueError:
            return False

        return to_enum in cls.TRANSITIONS.get(from_enum, set())

    @classmethod
    def is_terminal(cls, state: str) -> bool:
        """Check if a state is terminal"""
        try:
            state_enum = StepState(state)
            return state_enum in cls.TERMINAL_STATES
        except ValueError:
            return False

    @classmethod
    def validate_transition(cls, from_state: str, to_state: str) -> Optional[str]:
        """Validate a transition and return error message if invalid"""
        try:
            from_enum = StepState(from_state)
            to_enum = StepState(to_state)
        except ValueError as e:
            return f"Invalid state: {e}"

        if cls.is_terminal(from_state):
            return f"Cannot transition from terminal state '{from_state}'"

        if not cls.can_transition(from_state, to_state):
            return f"Invalid transition: '{from_state}' -> '{to_state}'"

        return None


def generate_state_diagram():
    """Generate ASCII state diagram for documentation"""
    print("Run State Machine:")
    print("==================")
    print()
    print("  [pending]")
    print("      |")
    print("      v")
    print("  [running] -----> [succeeded]")
    print("      |")
    print("      +---------> [failed] -----> [quarantined]")
    print("      |")
    print("      +---------> [canceled]")
    print()
    print("Terminal states: succeeded, quarantined, canceled")
    print()
    print()
    print("Step State Machine:")
    print("===================")
    print()
    print("  [running] -----> [succeeded]")
    print("      |")
    print("      +---------> [failed]")
    print("      |")
    print("      +---------> [canceled]")
    print()
    print("Terminal states: succeeded, failed, canceled")


if __name__ == "__main__":
    # Generate diagrams for documentation
    generate_state_diagram()

    # Test some transitions
    print("\n\nTransition Tests:")
    print("=================")

    tests = [
        ("pending", "running", True),
        ("running", "succeeded", True),
        ("running", "failed", True),
        ("succeeded", "failed", False),
        ("pending", "succeeded", False),
        ("failed", "quarantined", True),
    ]

    for from_state, to_state, expected in tests:
        result = RunStateMachine.can_transition(from_state, to_state)
        status = "✓" if result == expected else "✗"
        print(f"{status} {from_state:12} -> {to_state:12} : {result}")
