# DOC_LINK: DOC-CORE-STATE-MACHINE-003
"""State Machine for ID System Orchestrator

Implements the 11-state machine defined in DOC-GUIDE-PROCESS-FLOW-AND-AUTOMATION-LOGIC-638.

States:
- INITIAL: Starting state
- DETECTING: Detecting changes from git/filesystem
- CLASSIFYING: Classifying changes into entities
- RESOLVING: Resolving entity identities
- REMEDIATING: Applying remediations
- VALIDATING: Running validators
- AGGREGATING: Aggregating validation results
- GATE_DECISION: Making pass/fail decision
- COMMIT: Committing changes
- BLOCK: Blocking commit
- MANUAL_REQUIRED: Manual intervention required
- ROLLBACK: Rolling back changes
- SUCCESS: Completed successfully
- FAILED: Failed

DOC_ID: DOC-CORE-STATE-MACHINE-003
"""

import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional


class State(Enum):
    """Orchestrator states"""
    INITIAL = "INITIAL"
    DETECTING = "DETECTING"
    CLASSIFYING = "CLASSIFYING"
    RESOLVING = "RESOLVING"
    REMEDIATING = "REMEDIATING"
    VALIDATING = "VALIDATING"
    AGGREGATING = "AGGREGATING"
    GATE_DECISION = "GATE_DECISION"
    COMMIT = "COMMIT"
    BLOCK = "BLOCK"
    MANUAL_REQUIRED = "MANUAL_REQUIRED"
    ROLLBACK = "ROLLBACK"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


@dataclass
class StateTransition:
    """Records a state transition"""
    from_state: State
    to_state: State
    timestamp: str
    reason: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            'from': self.from_state.value,
            'to': self.to_state.value,
            'at': self.timestamp,
            'reason': self.reason
        }


@dataclass
class StateMachine:
    """State machine for orchestrator execution

    Manages state transitions and persistence.
    Enforces valid transition rules per design document Section 5.2.
    """

    current_state: State = State.INITIAL
    context: str = "unknown"
    started_at: Optional[str] = None
    transitions: List[StateTransition] = field(default_factory=list)
    evidence_files: List[str] = field(default_factory=list)

    # Transition rules: current_state -> allowed_next_states
    _transition_rules: Dict[State, List[State]] = field(default_factory=lambda: {
        State.INITIAL: [State.DETECTING],
        State.DETECTING: [State.CLASSIFYING, State.SUCCESS],  # SUCCESS if no changes
        State.CLASSIFYING: [State.RESOLVING],
        State.RESOLVING: [State.REMEDIATING, State.MANUAL_REQUIRED],
        State.REMEDIATING: [State.VALIDATING, State.ROLLBACK],
        State.VALIDATING: [State.AGGREGATING, State.ROLLBACK],
        State.AGGREGATING: [State.GATE_DECISION],
        State.GATE_DECISION: [State.COMMIT, State.BLOCK],
        State.COMMIT: [State.SUCCESS],
        State.BLOCK: [State.FAILED],
        State.ROLLBACK: [State.FAILED],
        State.MANUAL_REQUIRED: [State.RESOLVING, State.FAILED],  # Retry after override
        State.SUCCESS: [],  # Terminal
        State.FAILED: [],   # Terminal
    })

    def __post_init__(self):
        """Initialize started_at if not provided"""
        if self.started_at is None:
            self.started_at = self._now_iso()

    def _now_iso(self) -> str:
        """Get current timestamp in ISO format"""
        return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

    def transition(self, to_state: State, reason: Optional[str] = None) -> bool:
        """Transition to a new state

        Args:
            to_state: Target state
            reason: Optional reason for transition

        Returns:
            True if transition succeeded, False if invalid

        Raises:
            ValueError: If transition is not allowed
        """
        # Check if transition is allowed
        allowed_states = self._transition_rules.get(self.current_state, [])

        if to_state not in allowed_states:
            raise ValueError(
                f"Invalid transition: {self.current_state.value} -> {to_state.value}. "
                f"Allowed transitions: {[s.value for s in allowed_states]}"
            )

        # Record transition
        transition = StateTransition(
            from_state=self.current_state,
            to_state=to_state,
            timestamp=self._now_iso(),
            reason=reason
        )

        self.transitions.append(transition)
        self.current_state = to_state

        return True

    def is_terminal(self) -> bool:
        """Check if current state is terminal"""
        return self.current_state in [State.SUCCESS, State.FAILED]

    def add_evidence(self, filepath: str):
        """Record an evidence file"""
        if filepath not in self.evidence_files:
            self.evidence_files.append(filepath)

    def to_dict(self) -> Dict:
        """Convert to dictionary for persistence"""
        return {
            'current_state': self.current_state.value,
            'context': self.context,
            'started_at': self.started_at,
            'transitions': [t.to_dict() for t in self.transitions],
            'evidence_files': self.evidence_files
        }

    def save(self, output_dir: Path):
        """Save state to run directory

        Args:
            output_dir: Directory to save state.json
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        state_file = output_dir / 'state.json'

        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, state_file: Path) -> 'StateMachine':
        """Load state from file

        Args:
            state_file: Path to state.json

        Returns:
            StateMachine instance
        """
        with open(state_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Reconstruct transitions
        transitions = [
            StateTransition(
                from_state=State(t['from']),
                to_state=State(t['to']),
                timestamp=t['at'],
                reason=t.get('reason')
            )
            for t in data['transitions']
        ]

        return cls(
            current_state=State(data['current_state']),
            context=data['context'],
            started_at=data['started_at'],
            transitions=transitions,
            evidence_files=data['evidence_files']
        )


__doc_id__ = 'DOC-CORE-STATE-MACHINE-003'
