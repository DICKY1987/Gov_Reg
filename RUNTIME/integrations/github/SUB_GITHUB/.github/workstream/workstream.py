"""
Workstream State Machine implementation.

Implements the Workstream state machine per SSOT §1.3.
Workstreams group related tasks and track collective progress.

States: PENDING, READY, RUNNING, PAUSED, BLOCKED, VALIDATING, COMPLETED, FAILED, CANCELLED
Reference: DOC-SSOT-STATE-MACHINES-001 §1.3
"""

from typing import Dict, Set, Optional
from datetime import datetime, timezone

from .base import BaseState, BaseStateMachine


class WorkstreamState(BaseState):
    """
    Workstream lifecycle states per SSOT §1.3.1.
    """

    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    BLOCKED = "blocked"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

    @classmethod
    def get_terminal_states(cls) -> Set["WorkstreamState"]:
        """Terminal states: COMPLETED, FAILED, CANCELLED."""
        return {cls.COMPLETED, cls.FAILED, cls.CANCELLED}

    @classmethod
    def get_valid_transitions(cls) -> Dict["WorkstreamState", Set["WorkstreamState"]]:
        """
        Valid transitions per SSOT §1.3.4.
        """
        return {
            cls.PENDING: {cls.READY, cls.BLOCKED},
            cls.READY: {cls.RUNNING, cls.CANCELLED},
            cls.RUNNING: {
                cls.PAUSED,
                cls.BLOCKED,
                cls.VALIDATING,
                cls.FAILED,
                cls.CANCELLED,
            },
            cls.PAUSED: {cls.RUNNING, cls.CANCELLED},
            cls.BLOCKED: {cls.PENDING, cls.CANCELLED},
            cls.VALIDATING: {cls.COMPLETED, cls.FAILED},
            cls.COMPLETED: set(),
            cls.FAILED: set(),
            cls.CANCELLED: set(),
        }


class WorkstreamStateMachine(BaseStateMachine):
    """
    Workstream state machine for task group tracking.

    Manages workstream lifecycle per SSOT §1.3.
    """

    def __init__(
        self, workstream_id: str, run_id: str, metadata: Optional[Dict] = None
    ):
        super().__init__(
            entity_id=workstream_id,
            entity_type="workstream",
            initial_state=WorkstreamState.PENDING,
            metadata=metadata or {},
        )

        self.workstream_id = workstream_id
        self.run_id = run_id

        # Task tracking
        self.total_tasks = 0
        self.completed_tasks = 0
        self.failed_tasks = 0
        self.critical_failed = False

        # Timestamps
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None

    def mark_ready(self):
        """Mark workstream as ready to start."""
        self.transition(
            WorkstreamState.READY, reason="Dependencies satisfied", trigger="ready"
        )

    def start(self):
        """Start workstream execution."""
        self.transition(
            WorkstreamState.RUNNING, reason="Workstream started", trigger="started"
        )
        self.started_at = datetime.now(timezone.utc)

    def pause(self, operator: str = None):
        """Pause workstream."""
        self.transition(
            WorkstreamState.PAUSED, reason="Paused", trigger="paused", operator=operator
        )

    def resume(self, operator: str = None):
        """Resume workstream."""
        self.transition(
            WorkstreamState.RUNNING,
            reason="Resumed",
            trigger="resumed",
            operator=operator,
        )

    def block(self, reason: str):
        """Block workstream."""
        self.transition(WorkstreamState.BLOCKED, reason=reason, trigger="blocked")

    def unblock(self):
        """Unblock workstream."""
        self.transition(
            WorkstreamState.PENDING, reason="Unblocked", trigger="unblocked"
        )

    def begin_validation(self):
        """Begin validation."""
        self.transition(
            WorkstreamState.VALIDATING,
            reason="All tasks complete",
            trigger="validating",
        )

    def complete(self):
        """Mark as completed."""
        self.transition(
            WorkstreamState.COMPLETED, reason="Validation passed", trigger="completed"
        )
        self.completed_at = datetime.now(timezone.utc)

    def fail(self, reason: str):
        """Mark as failed."""
        self.transition(WorkstreamState.FAILED, reason=reason, trigger="failed")
        self.completed_at = datetime.now(timezone.utc)

    def cancel(self, operator: str = None):
        """Cancel workstream."""
        self.transition(
            WorkstreamState.CANCELLED,
            reason="Cancelled",
            trigger="cancelled",
            operator=operator,
        )
        self.completed_at = datetime.now(timezone.utc)

    def update_task_counts(
        self, total: int = None, completed: int = None, failed: int = None
    ):
        """Update task counts."""
        if total is not None:
            self.total_tasks = total
        if completed is not None:
            self.completed_tasks = completed
        if failed is not None:
            self.failed_tasks = failed

    def get_progress(self) -> Dict:
        """Get workstream progress."""
        progress = {
            "workstream_id": self.workstream_id,
            "run_id": self.run_id,
            "state": self.current_state.value,
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "is_terminal": self.is_terminal(),
        }

        if self.total_tasks > 0:
            progress["completion_percentage"] = (
                self.completed_tasks / self.total_tasks
            ) * 100

        return progress
