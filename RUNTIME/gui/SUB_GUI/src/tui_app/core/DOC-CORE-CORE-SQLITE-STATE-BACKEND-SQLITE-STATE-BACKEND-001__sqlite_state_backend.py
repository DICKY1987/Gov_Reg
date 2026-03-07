# DOC_LINK: DOC-CORE-CORE-SQLITE-STATE-BACKEND-SQLITE-STATE-BACKEND-001
"""SQLite backend for accessing real pipeline state.

Connects to .worktrees/pipeline_state.db and provides StateBackend implementation.
"""

# DOC_ID: DOC-CORE-CORE-SQLITE-STATE-BACKEND-SQLITE-STATE-BACKEND-001

import ast
import json
import sqlite3
import DOC-ERROR-UTILS-TIME-145__time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from tui_app.core.state_client import (
    ExecutionInfo,
    PatchLedgerEntry,
    PipelineSummary,
    StateBackend,
    TaskInfo,
)


class SQLiteStateBackend(StateBackend):
    """SQLite-backed state storage for TUI panels."""

    def __init__(
        self, db_path: str = ".worktrees/pipeline_state.db", max_retries: int = 3
    ):
        """Initialize SQLite backend.

        Args:
            db_path: Path to SQLite database file
            max_retries: Maximum connection retry attempts
        """
        self.db_path = db_path
        self.max_retries = max_retries
        self._conn = self._connect_with_retry()

    @staticmethod
    def _parse_timestamp(value: Optional[str]) -> Optional[datetime]:
        """Parse timestamp string to datetime."""
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            try:
                return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            except Exception:
                return None

    @staticmethod
    def _parse_metadata(metadata_raw: Optional[str]) -> dict:
        """Parse metadata JSON or Python dict string safely."""
        if not metadata_raw:
            return {}
        if isinstance(metadata_raw, dict):
            return metadata_raw
        try:
            return json.loads(metadata_raw)
        except Exception:
            try:
                return ast.literal_eval(metadata_raw)
            except Exception:
                return {"raw": metadata_raw}

    @staticmethod
    def _extract_files_from_patch(
        patch_content: Optional[str], metadata: dict
    ) -> List[str]:
        """Extract file paths from patch content or metadata."""
        files: list[str] = []
        if metadata:
            meta_files = metadata.get("files")
            if isinstance(meta_files, list):
                files.extend(str(f) for f in meta_files)

        if patch_content:
            for line in patch_content.splitlines():
                if line.startswith("diff --git"):
                    parts = line.split()
                    if len(parts) >= 3:
                        candidate = parts[2]
                        files.append(candidate.replace("a/", "", 1))
                elif line.startswith("--- ") or line.startswith("+++ "):
                    path = line[4:]
                    files.append(path.replace("a/", "", 1).replace("b/", "", 1))

        # Preserve order while deduplicating
        seen = set()
        unique_files = []
        for f in files:
            if f not in seen:
                unique_files.append(f)
                seen.add(f)
        return unique_files

    def _connect_with_retry(self) -> sqlite3.Connection:
        """Connect to database with retry logic.

        Returns:
            SQLite connection

        Raises:
            sqlite3.Error: If all retry attempts fail
        """
        for attempt in range(self.max_retries):
            try:
                # Create database if it doesn't exist
                db_file = Path(self.db_path)
                if not db_file.exists():
                    db_file.parent.mkdir(parents=True, exist_ok=True)
                    conn = sqlite3.connect(self.db_path, check_same_thread=False)
                    self._initialize_schema(conn)
                    return conn

                conn = sqlite3.connect(self.db_path, check_same_thread=False)
                conn.row_factory = sqlite3.Row  # Enable column access by name
                return conn
            except sqlite3.Error as e:
                if attempt == self.max_retries - 1:
                    raise RuntimeError(
                        f"Failed to connect to database after {self.max_retries} attempts: {e}"
                    )
                time.sleep(1)

        raise RuntimeError("Unexpected error in database connection retry logic")

    def _initialize_schema(self, conn: sqlite3.Connection) -> None:
        """Initialize database schema if tables don't exist.

        Args:
            conn: SQLite connection
        """
        cursor = conn.cursor()

        # Create uet_executions table
        cursor.execute(
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

        # Create uet_tasks table
        cursor.execute(
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

        # Create patch_ledger table
        cursor.execute(
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

        conn.commit()

    def get_pipeline_summary(self) -> PipelineSummary:
        """Get current pipeline summary.

        Returns:
            PipelineSummary with current state
        """
        cursor = self._conn.cursor()

        # Count tasks by status
        cursor.execute("SELECT COUNT(*) FROM uet_tasks")
        total_tasks = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM uet_tasks WHERE status = 'running'")
        running_tasks = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM uet_tasks WHERE status = 'completed'")
        completed_tasks = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM uet_tasks WHERE status = 'failed'")
        failed_tasks = cursor.fetchone()[0]

        # Count active executions
        cursor.execute("SELECT COUNT(*) FROM uet_executions WHERE status = 'running'")
        active_workers = cursor.fetchone()[0]

        # Get last update time
        cursor.execute("SELECT MAX(started_at) FROM uet_executions")
        last_update_str = cursor.fetchone()[0]
        last_update = self._parse_timestamp(last_update_str) or datetime.now()

        # Determine overall status
        if running_tasks > 0 or active_workers > 0:
            status = "running"
        elif failed_tasks > 0:
            status = "error"
        elif total_tasks > 0:
            status = "idle"
        else:
            status = "idle"

        return PipelineSummary(
            total_tasks=total_tasks,
            running_tasks=running_tasks,
            completed_tasks=completed_tasks,
            failed_tasks=failed_tasks,
            active_workers=active_workers,
            last_update=last_update,
            status=status,
        )

    def get_tasks(self, limit: int = 100) -> List[TaskInfo]:
        """Get recent tasks.

        Args:
            limit: Maximum number of tasks to return

        Returns:
            List of TaskInfo objects
        """
        cursor = self._conn.cursor()

        cursor.execute(
            """
            SELECT
                task_id,
                task_type,
                status,
                execution_id,
                started_at,
                completed_at
            FROM uet_tasks
            ORDER BY
                CASE
                    WHEN started_at IS NULL THEN created_at
                    ELSE started_at
                END DESC
            LIMIT ?
        """,
            (limit,),
        )

        tasks = []
        for row in cursor.fetchall():
            task = TaskInfo(
                task_id=row[0],
                name=row[1] or f"Task {row[0][:8]}",  # Use task_type as name
                status=row[2] or "unknown",
                worker_id=row[3],  # execution_id as worker_id
                start_time=self._parse_timestamp(row[4]),
                end_time=self._parse_timestamp(row[5]),
                error_message=None,  # Not stored in current schema
            )
            tasks.append(task)

        return tasks

    def get_task(self, task_id: str) -> Optional[TaskInfo]:
        """Get specific task by ID.

        Args:
            task_id: Task identifier

        Returns:
            TaskInfo if found, None otherwise
        """
        cursor = self._conn.cursor()

        cursor.execute(
            """
            SELECT
                task_id,
                task_type,
                status,
                execution_id,
                started_at,
                completed_at
            FROM uet_tasks
            WHERE task_id = ?
        """,
            (task_id,),
        )

        row = cursor.fetchone()
        if not row:
            return None

        return TaskInfo(
            task_id=row[0],
            name=row[1] or f"Task {row[0][:8]}",
            status=row[2] or "unknown",
            worker_id=row[3],
            start_time=self._parse_timestamp(row[4]),
            end_time=self._parse_timestamp(row[5]),
            error_message=None,
        )

    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()

    def __del__(self):
        """Cleanup on destruction."""
        self.close()

    def get_executions(self, limit: int = 50) -> List[ExecutionInfo]:
        """Get recent executions ordered by start time descending."""
        cursor = self._conn.cursor()
        cursor.execute(
            """
            SELECT
                execution_id,
                phase_name,
                status,
                started_at,
                completed_at,
                metadata
            FROM uet_executions
            ORDER BY started_at DESC
            LIMIT ?
            """,
            (limit,),
        )

        executions: list[ExecutionInfo] = []
        for row in cursor.fetchall():
            metadata = self._parse_metadata(row[5])
            executions.append(
                ExecutionInfo(
                    execution_id=row[0],
                    phase_name=row[1],
                    status=row[2] or "unknown",
                    started_at=self._parse_timestamp(row[3]),
                    completed_at=self._parse_timestamp(row[4]),
                    metadata=metadata,
                )
            )
        return executions

    def get_patch_ledger(self, limit: int = 50) -> List[PatchLedgerEntry]:
        """Get recent patch ledger entries ordered by creation time."""
        cursor = self._conn.cursor()
        cursor.execute(
            """
            SELECT
                patch_id,
                execution_id,
                created_at,
                state,
                patch_content,
                metadata
            FROM patch_ledger
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        )

        patches: list[PatchLedgerEntry] = []
        for row in cursor.fetchall():
            metadata = self._parse_metadata(row[5])
            files = self._extract_files_from_patch(row[4], metadata)
            patches.append(
                PatchLedgerEntry(
                    patch_id=row[0],
                    execution_id=row[1],
                    created_at=self._parse_timestamp(row[2]),
                    state=row[3] or "unknown",
                    patch_content=row[4] or "",
                    metadata=metadata,
                    files=files,
                )
            )
        return patches
