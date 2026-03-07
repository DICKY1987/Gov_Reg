# DOC_LINK: DOC-CORE-CORE-PATTERN-CLIENT-PATTERN-CLIENT-001
"""Pattern state client for accessing pattern execution data.

Provides interfaces for panels to access pattern execution state
and events for visualization.
"""

# DOC_ID: DOC-CORE-CORE-PATTERN-CLIENT-PATTERN-CLIENT-001

import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional


class PatternStatus(Enum):
    """Status of a pattern execution run."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PatternEventType(Enum):
    """Types of pattern execution events."""

    STARTED = "started"
    PHASE_STARTED = "phase_started"
    PHASE_COMPLETED = "phase_completed"
    VALIDATION_PASSED = "validation_passed"
    VALIDATION_FAILED = "validation_failed"
    EXECUTED = "executed"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class PatternRun:
    """Information about a pattern execution run."""

    run_id: str
    pattern_id: str
    pattern_name: str
    status: PatternStatus
    start_time: datetime
    end_time: Optional[datetime]
    progress: float  # 0.0 to 1.0
    current_phase: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class PatternEvent:
    """Event in a pattern execution run."""

    event_id: str
    run_id: str
    event_type: PatternEventType
    timestamp: datetime
    phase: Optional[str]
    message: str
    details: Optional[dict] = None


class PatternStateStore(ABC):
    """Abstract interface for pattern state storage."""

    @abstractmethod
    def get_recent_runs(self, limit: int = 50) -> List[PatternRun]:
        """Get recent pattern runs."""
        pass

    @abstractmethod
    def get_run_events(self, run_id: str) -> List[PatternEvent]:
        """Get all events for a specific run."""
        pass

    @abstractmethod
    def get_active_patterns(self) -> List[PatternRun]:
        """Get currently active pattern runs."""
        pass


class InMemoryPatternStateStore(PatternStateStore):
    """In-memory pattern state store with seeded test data."""

    def __init__(self):
        now = datetime.now()

        # Seed some pattern runs
        self._runs = [
            PatternRun(
                run_id="run-001",
                pattern_id="PAT-GUI-PANEL-001",
                pattern_name="Panel Framework Implementation",
                status=PatternStatus.COMPLETED,
                start_time=now,
                end_time=now,
                progress=1.0,
                current_phase="Testing",
            ),
            PatternRun(
                run_id="run-002",
                pattern_id="PAT-ATOMIC-CREATE-001",
                pattern_name="Atomic File Creation",
                status=PatternStatus.RUNNING,
                start_time=now,
                end_time=None,
                progress=0.6,
                current_phase="Phase B: Creating Files",
            ),
            PatternRun(
                run_id="run-003",
                pattern_id="PAT-ATOMIC-REFINE-001",
                pattern_name="Code Refinement",
                status=PatternStatus.FAILED,
                start_time=now,
                end_time=now,
                progress=0.4,
                current_phase="Validation",
                error_message="Test suite failed: 2 tests",
            ),
        ]

        # Seed events for runs
        self._events = {
            "run-001": [
                PatternEvent(
                    "evt-001",
                    "run-001",
                    PatternEventType.STARTED,
                    now,
                    None,
                    "Pattern execution started",
                ),
                PatternEvent(
                    "evt-002",
                    "run-001",
                    PatternEventType.PHASE_STARTED,
                    now,
                    "Phase A",
                    "Starting Phase A: Setup",
                ),
                PatternEvent(
                    "evt-003",
                    "run-001",
                    PatternEventType.PHASE_COMPLETED,
                    now,
                    "Phase A",
                    "Phase A completed successfully",
                ),
                PatternEvent(
                    "evt-004",
                    "run-001",
                    PatternEventType.PHASE_STARTED,
                    now,
                    "Phase B",
                    "Starting Phase B: Implementation",
                ),
                PatternEvent(
                    "evt-005",
                    "run-001",
                    PatternEventType.PHASE_COMPLETED,
                    now,
                    "Phase B",
                    "Phase B completed successfully",
                ),
                PatternEvent(
                    "evt-006",
                    "run-001",
                    PatternEventType.VALIDATION_PASSED,
                    now,
                    "Testing",
                    "All tests passed",
                ),
                PatternEvent(
                    "evt-007",
                    "run-001",
                    PatternEventType.COMPLETED,
                    now,
                    None,
                    "Pattern execution completed",
                ),
            ],
            "run-002": [
                PatternEvent(
                    "evt-101",
                    "run-002",
                    PatternEventType.STARTED,
                    now,
                    None,
                    "Pattern execution started",
                ),
                PatternEvent(
                    "evt-102",
                    "run-002",
                    PatternEventType.PHASE_STARTED,
                    now,
                    "Phase A",
                    "Starting Phase A: Analysis",
                ),
                PatternEvent(
                    "evt-103",
                    "run-002",
                    PatternEventType.PHASE_COMPLETED,
                    now,
                    "Phase A",
                    "Phase A completed successfully",
                ),
                PatternEvent(
                    "evt-104",
                    "run-002",
                    PatternEventType.PHASE_STARTED,
                    now,
                    "Phase B",
                    "Starting Phase B: Creating Files",
                ),
            ],
            "run-003": [
                PatternEvent(
                    "evt-201",
                    "run-003",
                    PatternEventType.STARTED,
                    now,
                    None,
                    "Pattern execution started",
                ),
                PatternEvent(
                    "evt-202",
                    "run-003",
                    PatternEventType.PHASE_STARTED,
                    now,
                    "Validation",
                    "Running test suite",
                ),
                PatternEvent(
                    "evt-203",
                    "run-003",
                    PatternEventType.VALIDATION_FAILED,
                    now,
                    "Validation",
                    "Test suite failed: 2 tests",
                ),
                PatternEvent(
                    "evt-204",
                    "run-003",
                    PatternEventType.FAILED,
                    now,
                    None,
                    "Pattern execution failed",
                ),
            ],
        }

    def get_recent_runs(self, limit: int = 50) -> List[PatternRun]:
        return self._runs[:limit]

    def get_run_events(self, run_id: str) -> List[PatternEvent]:
        return self._events.get(run_id, [])

    def get_active_patterns(self) -> List[PatternRun]:
        return [run for run in self._runs if run.status == PatternStatus.RUNNING]


class PatternClient:
    """Client for accessing pattern execution state from panels."""

    def __init__(self, store: PatternStateStore):
        self._store = store

    def get_recent_runs(self, limit: int = 50) -> List[PatternRun]:
        """Get recent pattern runs.

        Args:
            limit: Maximum number of runs to return

        Returns:
            List of PatternRun objects
        """
        return self._store.get_recent_runs(limit)

    def get_run_events(self, run_id: str) -> List[PatternEvent]:
        """Get all events for a specific run.

        Args:
            run_id: Pattern run identifier

        Returns:
            List of PatternEvent objects
        """
        return self._store.get_run_events(run_id)

    def get_active_patterns(self) -> List[PatternRun]:
        """Get currently active pattern runs.

        Returns:
            List of active PatternRun objects
        """
        return self._store.get_active_patterns()


class SQLitePatternStateStore(PatternStateStore):
    """SQLite-backed pattern state derived from pipeline tables.

    Uses `uet_executions` as pattern runs and `patch_ledger` entries as events.
    """

    def __init__(self, db_path: str = ".worktrees/pipeline_state.db"):
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        """Create required tables if they do not exist (mirrors SQLiteStateBackend)."""
        cur = self._conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS uet_executions (
                execution_id TEXT PRIMARY KEY,
                phase_name TEXT,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                status TEXT,
                metadata JSON
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS uet_tasks (
                task_id TEXT PRIMARY KEY,
                execution_id TEXT,
                task_type TEXT,
                dependencies JSON,
                status TEXT,
                created_at TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                result JSON,
                FOREIGN KEY (execution_id) REFERENCES uet_executions(execution_id)
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS patch_ledger (
                patch_id TEXT PRIMARY KEY,
                execution_id TEXT,
                created_at TIMESTAMP,
                state TEXT,
                patch_content TEXT,
                validation_result JSON,
                metadata JSON,
                FOREIGN KEY (execution_id) REFERENCES uet_executions(execution_id)
            )
            """
        )
        self._conn.commit()

    def _parse_timestamp(self, value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except Exception:
            try:
                return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            except Exception:
                return None

    def get_recent_runs(self, limit: int = 50) -> List[PatternRun]:
        cur = self._conn.cursor()
        cur.execute(
            """
            SELECT execution_id, phase_name, status, started_at, completed_at
            FROM uet_executions
            ORDER BY COALESCE(started_at, completed_at) DESC
            LIMIT ?
            """,
            (limit,),
        )

        runs: list[PatternRun] = []
        for row in cur.fetchall():
            status = (row["status"] or "pending").lower()
            status_enum = {
                "running": PatternStatus.RUNNING,
                "completed": PatternStatus.COMPLETED,
                "failed": PatternStatus.FAILED,
                "cancelled": PatternStatus.CANCELLED,
                "pending": PatternStatus.PENDING,
            }.get(status, PatternStatus.PENDING)

            progress = (
                1.0
                if status_enum
                in (
                    PatternStatus.COMPLETED,
                    PatternStatus.FAILED,
                    PatternStatus.CANCELLED,
                )
                else 0.6
            )
            runs.append(
                PatternRun(
                    run_id=row["execution_id"],
                    pattern_id=row["execution_id"],
                    pattern_name=row["phase_name"] or "Execution",
                    status=status_enum,
                    start_time=self._parse_timestamp(row["started_at"]),
                    end_time=self._parse_timestamp(row["completed_at"]),
                    progress=progress,
                    current_phase=row["phase_name"],
                    error_message=(
                        None
                        if status_enum != PatternStatus.FAILED
                        else "Execution reported failure"
                    ),
                )
            )
        return runs

    def get_run_events(self, run_id: str) -> List[PatternEvent]:
        cur = self._conn.cursor()
        events: list[PatternEvent] = []

        # Execution lifecycle
        cur.execute(
            """
            SELECT started_at, completed_at, status
            FROM uet_executions
            WHERE execution_id = ?
            """,
            (run_id,),
        )
        row = cur.fetchone()
        if row:
            started_at = self._parse_timestamp(row["started_at"]) or datetime.now()
            status = (row["status"] or "pending").lower()
            events.append(
                PatternEvent(
                    event_id=f"{run_id}-start",
                    run_id=run_id,
                    event_type=PatternEventType.STARTED,
                    timestamp=started_at,
                    phase=status,
                    message="Execution started",
                )
            )
            if row["completed_at"]:
                events.append(
                    PatternEvent(
                        event_id=f"{run_id}-complete",
                        run_id=run_id,
                        event_type=(
                            PatternEventType.COMPLETED
                            if status != "failed"
                            else PatternEventType.FAILED
                        ),
                        timestamp=self._parse_timestamp(row["completed_at"])
                        or started_at,
                        phase=status,
                        message="Execution completed",
                    )
                )

        # Task milestones
        cur.execute(
            """
            SELECT task_id, task_type, status, started_at, completed_at
            FROM uet_tasks
            WHERE execution_id = ?
            ORDER BY COALESCE(started_at, completed_at) ASC
            """,
            (run_id,),
        )
        for idx, row in enumerate(cur.fetchall(), start=1):
            status = (row["status"] or "pending").lower()
            evt_type = (
                PatternEventType.PHASE_STARTED
                if status in ("pending", "running")
                else PatternEventType.PHASE_COMPLETED
            )
            events.append(
                PatternEvent(
                    event_id=f"{run_id}-task-{idx}",
                    run_id=run_id,
                    event_type=evt_type,
                    timestamp=self._parse_timestamp(row["started_at"])
                    or datetime.now(),
                    phase=row["task_type"],
                    message=f"Task {row['task_id']} ({row['task_type']}) {status}",
                )
            )

        # Patch ledger entries
        cur.execute(
            """
            SELECT created_at, state, patch_id, patch_content
            FROM patch_ledger
            WHERE execution_id = ?
            ORDER BY created_at ASC
            """,
            (run_id,),
        )
        for idx, row in enumerate(cur.fetchall(), start=1):
            state = (row["state"] or "").lower()
            event_type = {
                "validated": PatternEventType.VALIDATION_PASSED,
                "failed": PatternEventType.VALIDATION_FAILED,
                "applied": PatternEventType.COMPLETED,
            }.get(state, PatternEventType.EXECUTED)

            events.append(
                PatternEvent(
                    event_id=f"{run_id}-patch-{idx}",
                    run_id=run_id,
                    event_type=event_type,
                    timestamp=self._parse_timestamp(row["created_at"])
                    or datetime.now(),
                    phase=row["state"],
                    message=f"Patch {row['patch_id']} ({state or 'executed'})",
                    details={"patch_excerpt": (row["patch_content"] or "")[:80]},
                )
            )

        if not events:
            events.append(
                PatternEvent(
                    event_id=f"evt-{run_id}-placeholder",
                    run_id=run_id,
                    event_type=PatternEventType.STARTED,
                    timestamp=datetime.now(),
                    phase=None,
                    message="No events recorded for this execution.",
                    details=None,
                )
            )
        return events

    def get_active_patterns(self) -> List[PatternRun]:
        return [
            run for run in self.get_recent_runs() if run.status == PatternStatus.RUNNING
        ]
