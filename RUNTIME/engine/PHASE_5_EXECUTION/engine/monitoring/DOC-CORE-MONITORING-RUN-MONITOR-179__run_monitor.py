# DOC_LINK: DOC-CORE-MONITORING-RUN-MONITOR-179
"""Run Monitor - WS-03-03B

Monitors run execution and aggregates metrics.
"""

# DOC_ID: DOC-CORE-MONITORING-RUN-MONITOR-179

import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

# Add framework root to path for imports
.parent.parent.parent.parent))

from core.state.db import Database


class RunStatus(Enum):
    """Run status for monitoring"""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    QUARANTINED = "quarantined"
    CANCELED = "canceled"


@dataclass
class RunMetrics:
    """Aggregated metrics for a run"""

    run_id: str
    status: str

    # Step counts
    total_steps: int
    completed_steps: int
    failed_steps: int

    # Events
    total_events: int
    error_events: int

    # Timing
    created_at: str
    started_at: Optional[str]
    ended_at: Optional[str]
    duration_seconds: Optional[float]

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "run_id": self.run_id,
            "status": self.status,
            "total_steps": self.total_steps,
            "completed_steps": self.completed_steps,
            "failed_steps": self.failed_steps,
            "total_events": self.total_events,
            "error_events": self.error_events,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "duration_seconds": self.duration_seconds,
        }


class RunMonitor:
    """Monitors run execution and provides metrics

    Aggregates data from database to provide real-time
    monitoring and dashboard-ready metrics.
    """

    def __init__(self, db_path: str = ":memory:"):
        """
        Args:
            db_path: Path to SQLite database
        """
        self.db = Database(db_path)
        self.db.connect()  # Initialize connection

    def get_run_metrics(self, run_id: str) -> Optional[RunMetrics]:
        """Get metrics for a specific run

        Args:
            run_id: Run identifier

        Returns:
            RunMetrics or None if run not found
        """
        # Get run record
        run = self.db.get_run(run_id)
        if not run:
            return None

        # Count step attempts
        cursor = self.db.conn.cursor()
        cursor.execute(
            """
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN state = 'succeeded' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN state = 'failed' THEN 1 ELSE 0 END) as failed
            FROM step_attempts
            WHERE run_id = ?
        """,
            (run_id,),
        )

        steps = cursor.fetchone()
        total_steps = steps[0] if steps else 0
        completed_steps = steps[1] if steps else 0
        failed_steps = steps[2] if steps else 0

        # Count events
        cursor.execute(
            """
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN event_type LIKE '%error%' OR event_type LIKE '%failed%' THEN 1 ELSE 0 END) as errors
            FROM run_events
            WHERE run_id = ?
        """,
            (run_id,),
        )

        events = cursor.fetchone()
        total_events = events[0] if events and events[0] else 0
        error_events = events[1] if events and events[1] else 0

        # Calculate duration
        duration = None
        if run.get("started_at") and run.get("ended_at"):
            from datetime import datetime

            started = datetime.fromisoformat(run["started_at"].replace("Z", "+00:00"))
            ended = datetime.fromisoformat(run["ended_at"].replace("Z", "+00:00"))
            duration = (ended - started).total_seconds()

        return RunMetrics(
            run_id=run_id,
            status=run["state"],
            total_steps=total_steps,
            completed_steps=completed_steps,
            failed_steps=failed_steps,
            total_events=total_events,
            error_events=error_events,
            created_at=run["created_at"],
            started_at=run.get("started_at"),
            ended_at=run.get("ended_at"),
            duration_seconds=duration,
        )

    def list_active_runs(self) -> List[str]:
        """List all active (non-terminal) runs

        Returns:
            List of run IDs
        """
        cursor = self.db.conn.cursor()
        cursor.execute(
            """
            SELECT run_id
            FROM runs
            WHERE state IN ('pending', 'running')
            ORDER BY created_at DESC
        """
        )

        return [row[0] for row in cursor.fetchall()]

    def get_summary(self) -> Dict:
        """Get summary of all runs

        Returns:
            Dictionary with aggregated metrics
        """
        cursor = self.db.conn.cursor()

        # Count runs by state
        cursor.execute(
            """
            SELECT state, COUNT(*) as count
            FROM runs
            GROUP BY state
        """
        )

        state_counts = {row[0]: row[1] for row in cursor.fetchall()}

        # Count total steps
        cursor.execute(
            """
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN state = 'succeeded' THEN 1 ELSE 0 END) as succeeded,
                SUM(CASE WHEN state = 'failed' THEN 1 ELSE 0 END) as failed
            FROM step_attempts
        """
        )

        steps = cursor.fetchone()

        return {
            "total_runs": sum(state_counts.values()),
            "runs_by_state": state_counts,
            "active_runs": state_counts.get("running", 0)
            + state_counts.get("pending", 0),
            "total_steps": steps[0] if steps else 0,
            "succeeded_steps": steps[1] if steps else 0,
            "failed_steps": steps[2] if steps else 0,
        }
