# DOC_LINK: DOC-CORE-CORE-STATE-CLIENT-124
"""State client for accessing pipeline state.

Provides a clean API for panels to read pipeline state without
directly coupling to the underlying storage mechanism.
"""

# DOC_ID: DOC-CORE-CORE-STATE-CLIENT-124

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class PipelineSummary:
    """Summary of current pipeline state."""

    total_tasks: int
    running_tasks: int
    completed_tasks: int
    failed_tasks: int
    active_workers: int
    last_update: datetime
    status: str  # 'idle', 'running', 'paused', 'error'


@dataclass
class TaskInfo:
    """Information about a pipeline task."""

    task_id: str
    name: str
    status: str
    worker_id: Optional[str]
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    error_message: Optional[str] = None


@dataclass
class ExecutionInfo:
    """Information about a pipeline execution."""

    execution_id: str
    phase_name: Optional[str]
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    metadata: Dict[str, Any]


@dataclass
class PatchLedgerEntry:
    """Patch ledger record for tracking file changes."""

    patch_id: str
    execution_id: Optional[str]
    created_at: Optional[datetime]
    state: str
    patch_content: str
    metadata: Dict[str, Any]
    files: List[str]


class StateBackend(ABC):
    """Abstract backend for state storage."""

    @abstractmethod
    def get_pipeline_summary(self) -> PipelineSummary:
        """Get current pipeline summary."""
        pass

    @abstractmethod
    def get_tasks(self, limit: int = 100) -> List[TaskInfo]:
        """Get recent tasks."""
        pass

    @abstractmethod
    def get_task(self, task_id: str) -> Optional[TaskInfo]:
        """Get specific task by ID."""
        pass

    @abstractmethod
    def get_executions(self, limit: int = 50) -> List[ExecutionInfo]:
        """Get recent executions."""
        pass

    @abstractmethod
    def get_patch_ledger(self, limit: int = 50) -> List[PatchLedgerEntry]:
        """Get recent patch ledger entries."""
        pass


class InMemoryStateBackend(StateBackend):
    """In-memory state backend for testing and development."""

    def __init__(self):
        self._summary = PipelineSummary(
            total_tasks=12,
            running_tasks=3,
            completed_tasks=7,
            failed_tasks=2,
            active_workers=2,
            last_update=datetime.now(),
            status="running",
        )

        self._tasks = [
            TaskInfo(
                task_id="task-001",
                name="Validate Workstreams",
                status="completed",
                worker_id="worker-1",
                start_time=datetime.now(),
                end_time=datetime.now(),
            ),
            TaskInfo(
                task_id="task-002",
                name="Run Error Detection",
                status="running",
                worker_id="worker-1",
                start_time=datetime.now(),
                end_time=None,
            ),
            TaskInfo(
                task_id="task-003",
                name="Generate Patches",
                status="failed",
                worker_id="worker-2",
                start_time=datetime.now(),
                end_time=datetime.now(),
                error_message="Ruff plugin timeout",
            ),
        ]

        now = datetime.now()
        self._executions = [
            ExecutionInfo(
                execution_id="exec-001",
                phase_name="PHASE_1",
                status="completed",
                started_at=now,
                completed_at=now,
                metadata={"owner": "pipeline"},
            ),
            ExecutionInfo(
                execution_id="exec-002",
                phase_name="PHASE_2",
                status="running",
                started_at=now,
                completed_at=None,
                metadata={"owner": "pipeline"},
            ),
        ]

        self._patches = [
            PatchLedgerEntry(
                patch_id="patch-001",
                execution_id="exec-002",
                created_at=now,
                state="validated",
                patch_content="diff --git a/example.py b/example.py\n+print('hello')",
                metadata={"files": ["example.py"], "tool": "uet"},
                files=["example.py"],
            ),
            PatchLedgerEntry(
                patch_id="patch-002",
                execution_id="exec-002",
                created_at=now,
                state="pending",
                patch_content="# Patch placeholder",
                metadata={"files": ["placeholder.py"]},
                files=["placeholder.py"],
            ),
        ]

    def get_pipeline_summary(self) -> PipelineSummary:
        return self._summary

    def get_tasks(self, limit: int = 100) -> List[TaskInfo]:
        return self._tasks[:limit]

    def get_task(self, task_id: str) -> Optional[TaskInfo]:
        for task in self._tasks:
            if task.task_id == task_id:
                return task
        return None

    def get_executions(self, limit: int = 50) -> List[ExecutionInfo]:
        return self._executions[:limit]

    def get_patch_ledger(self, limit: int = 50) -> List[PatchLedgerEntry]:
        return self._patches[:limit]


class StateClient:
    """Client for accessing pipeline state from panels."""

    def __init__(self, backend: StateBackend):
        self._backend = backend

    def get_pipeline_summary(self) -> PipelineSummary:
        """Get current pipeline summary.

        Returns:
            PipelineSummary with current pipeline state
        """
        return self._backend.get_pipeline_summary()

    def get_tasks(self, limit: int = 100) -> List[TaskInfo]:
        """Get recent tasks.

        Args:
            limit: Maximum number of tasks to return

        Returns:
            List of TaskInfo objects
        """
        return self._backend.get_tasks(limit)

    def get_task(self, task_id: str) -> Optional[TaskInfo]:
        """Get specific task by ID.

        Args:
            task_id: Task identifier

        Returns:
            TaskInfo if found, None otherwise
        """
        return self._backend.get_task(task_id)

    def get_executions(self, limit: int = 50) -> List[ExecutionInfo]:
        """Get recent executions.

        Args:
            limit: Maximum number of executions to return

        Returns:
            List of ExecutionInfo objects
        """
        return self._backend.get_executions(limit)

    def get_patch_ledger(self, limit: int = 50) -> List[PatchLedgerEntry]:
        """Get recent patch ledger entries.

        Args:
            limit: Maximum number of patch records

        Returns:
            List of PatchLedgerEntry objects
        """
        return self._backend.get_patch_ledger(limit)
