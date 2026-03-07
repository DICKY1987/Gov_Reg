# DOC_LINK: DOC-CORE-MONITORING-PROGRESS-TRACKER-178
"""Progress Tracker - WS-03-03B

Tracks execution progress and calculates completion percentages.
"""

# DOC_ID: DOC-CORE-MONITORING-PROGRESS-TRACKER-178

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Dict, List, Optional


@dataclass
class ProgressSnapshot:
    """Snapshot of execution progress at a point in time"""

    run_id: str
    timestamp: str

    # Overall progress
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    pending_tasks: int

    # Completion percentage (0-100)
    completion_percent: float

    # Timing
    started_at: Optional[str] = None
    estimated_completion: Optional[str] = None
    elapsed_seconds: Optional[float] = None
    estimated_remaining_seconds: Optional[float] = None

    # Current state
    current_task: Optional[str] = None
    current_task_progress: Optional[float] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "pending_tasks": self.pending_tasks,
            "completion_percent": self.completion_percent,
            "started_at": self.started_at,
            "estimated_completion": self.estimated_completion,
            "elapsed_seconds": self.elapsed_seconds,
            "estimated_remaining_seconds": self.estimated_remaining_seconds,
            "current_task": self.current_task,
            "current_task_progress": self.current_task_progress,
        }


class ProgressTracker:
    """Tracks execution progress for a run

    Calculates completion percentages, time estimates, and
    provides real-time progress snapshots.
    """

    def __init__(self, run_id: str, total_tasks: int):
        """
        Args:
            run_id: Run identifier
            total_tasks: Total number of tasks to complete
        """
        self.run_id = run_id
        self.total_tasks = total_tasks
        self.completed_tasks = 0
        self.failed_tasks = 0
        self.started_at: Optional[datetime] = None
        self.current_task: Optional[str] = None
        self.current_task_progress: Optional[float] = None

        # Task timing for estimates
        self.task_durations: List[float] = []

    def start(self):
        """Mark run as started"""
        self.started_at = datetime.now(UTC)

    def start_task(self, task_id: str):
        """Mark a task as started

        Args:
            task_id: Task identifier
        """
        self.current_task = task_id
        self.current_task_progress = 0.0

    def update_task_progress(self, progress: float):
        """Update current task progress

        Args:
            progress: Progress percentage (0-100)
        """
        self.current_task_progress = min(100.0, max(0.0, progress))

    def complete_task(self, task_id: str, duration: Optional[float] = None):
        """Mark a task as completed

        Args:
            task_id: Task identifier
            duration: Optional task duration in seconds
        """
        self.completed_tasks += 1
        self.current_task = None
        self.current_task_progress = None

        if duration is not None:
            self.task_durations.append(duration)

    def fail_task(self, task_id: str):
        """Mark a task as failed

        Args:
            task_id: Task identifier
        """
        self.failed_tasks += 1
        self.current_task = None
        self.current_task_progress = None

    def get_completion_percent(self) -> float:
        """Calculate completion percentage

        Returns:
            Percentage complete (0-100)
        """
        if self.total_tasks == 0:
            return 100.0

        base_percent = (self.completed_tasks / self.total_tasks) * 100

        # Add partial credit for current task
        if self.current_task_progress is not None:
            task_weight = 100.0 / self.total_tasks
            partial_credit = (self.current_task_progress / 100.0) * task_weight
            return min(100.0, base_percent + partial_credit)

        return base_percent

    def get_elapsed_time(self) -> Optional[float]:
        """Get elapsed time in seconds

        Returns:
            Seconds elapsed since start, or None if not started
        """
        if self.started_at is None:
            return None

        return (datetime.now(UTC) - self.started_at).total_seconds()

    def get_estimated_remaining_time(self) -> Optional[float]:
        """Estimate remaining time based on task durations

        Returns:
            Estimated seconds remaining, or None if not enough data
        """
        if not self.task_durations:
            return None

        # Calculate average task duration
        avg_duration = sum(self.task_durations) / len(self.task_durations)

        # Estimate remaining tasks
        remaining_tasks = self.total_tasks - self.completed_tasks

        # Account for current task progress
        if self.current_task_progress is not None:
            remaining_in_current = (100 - self.current_task_progress) / 100.0
            remaining_tasks = remaining_tasks - 1 + remaining_in_current

        return avg_duration * remaining_tasks

    def get_estimated_completion_time(self) -> Optional[datetime]:
        """Estimate completion time

        Returns:
            Estimated completion datetime, or None if not enough data
        """
        remaining = self.get_estimated_remaining_time()
        if remaining is None:
            return None

        return datetime.now(UTC) + timedelta(seconds=remaining)

    def get_snapshot(self) -> ProgressSnapshot:
        """Get current progress snapshot

        Returns:
            ProgressSnapshot with current state
        """
        pending = self.total_tasks - self.completed_tasks - self.failed_tasks

        est_completion = self.get_estimated_completion_time()

        return ProgressSnapshot(
            run_id=self.run_id,
            timestamp=datetime.now(UTC).isoformat() + "Z",
            total_tasks=self.total_tasks,
            completed_tasks=self.completed_tasks,
            failed_tasks=self.failed_tasks,
            pending_tasks=pending,
            completion_percent=self.get_completion_percent(),
            started_at=self.started_at.isoformat() + "Z" if self.started_at else None,
            estimated_completion=(
                est_completion.isoformat() + "Z" if est_completion else None
            ),
            elapsed_seconds=self.get_elapsed_time(),
            estimated_remaining_seconds=self.get_estimated_remaining_time(),
            current_task=self.current_task,
            current_task_progress=self.current_task_progress,
        )
