# DOC_LINK: DOC-CORE-UI-CORE-FILE-STATE-BACKEND-781
"""File-based state backend for reading PHASE_5_EXECUTION JSON state files.

Replaces SQLiteStateBackend for production use.
Reads JSON state files instead of a SQL database.
"""

# DOC_ID: DOC-CORE-UI-CORE-FILE-STATE-BACKEND-781

import logging
import os
from pathlib import Path
from typing import List, Optional

from ui_core.file_state_mapper import FileStateMapper
from ui_core.state_client import (
    ExecutionInfo,
    PatchLedgerEntry,
    PipelineSummary,
    StateBackend,
    TaskInfo,
)

logger = logging.getLogger(__name__)


class FileStateBackend(StateBackend):
    """File-based state backend using JSON state files from PHASE_5_EXECUTION.

    Reads state from .state/*.json files instead of a SQL database.
    Provides the same StateBackend interface as SQLiteStateBackend.

    Configuration:
        - STATE_DIR environment variable or constructor arg
        - Defaults to ".state" directory
    """

    def __init__(self, state_dir: Optional[str | Path] = None):
        """Initialize file state backend.

        Args:
            state_dir: Directory containing state JSON files.
                      If None, uses STATE_DIR env var or ".state" default.
        """
        # Resolve state directory
        if state_dir is None:
            state_dir = os.getenv("STATE_DIR", ".state")

        self.state_dir = Path(state_dir)
        self.mapper = FileStateMapper(self.state_dir)

        # Log initialization
        if self.state_dir.exists():
            logger.info(f"FileStateBackend initialized with state_dir: {self.state_dir}")
        else:
            logger.warning(
                f"State directory not found: {self.state_dir} (will use empty data)"
            )

    def get_pipeline_summary(self) -> PipelineSummary:
        """Get current pipeline summary.

        Returns:
            PipelineSummary with aggregated task counts from execution_results.json
        """
        return self.mapper.get_pipeline_summary()

    def get_tasks(
        self,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[TaskInfo]:
        """Get task list.

        Args:
            status: Optional filter by task status
            limit: Maximum number of tasks to return

        Returns:
            List of TaskInfo objects from execution_results.json
        """
        return self.mapper.get_tasks(status=status, limit=limit)

    def get_task(self, task_id: str) -> Optional[TaskInfo]:
        """Get single task by ID.

        Args:
            task_id: Task identifier

        Returns:
            TaskInfo if found, None otherwise
        """
        return self.mapper.get_task(task_id)

    def get_executions(self, limit: int = 10) -> List[ExecutionInfo]:
        """Get execution list.

        Args:
            limit: Maximum number of executions to return

        Returns:
            List of ExecutionInfo objects (derived from run_id)
        """
        return self.mapper.get_executions(limit=limit)

    def get_patch_ledger(self, limit: int = 100) -> List[PatchLedgerEntry]:
        """Get patch ledger entries.

        Args:
            limit: Maximum number of patches to return

        Returns:
            List of PatchLedgerEntry objects (empty for now)
        """
        return self.mapper.get_patch_ledger(limit=limit)

    def get_run_id(self) -> Optional[str]:
        """Get current run ID.

        Returns:
            Run ID from execution_results.json, or None
        """
        return self.mapper.get_run_id()

    def get_tool_metrics(self) -> dict:
        """Get tool performance metrics.

        Returns:
            Dict mapping tool_id to metrics from router_state.json
        """
        return self.mapper.get_tool_metrics()
