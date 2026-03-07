# DOC_LINK: DOC-CORE-UI-CORE-FILE-STATE-MAPPER-780
"""File state mapper for PHASE_5_EXECUTION JSON state files.

Maps JSON state files (.state/*.json) to UI data models.
Handles missing files and fields gracefully with sensible defaults.
"""

# DOC_ID: DOC-CORE-UI-CORE-FILE-STATE-MAPPER-780

import json
import logging
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ui_core.pattern_client import PatternRun, PatternStatus
from ui_core.state_client import ExecutionInfo, PatchLedgerEntry, PipelineSummary, TaskInfo

logger = logging.getLogger(__name__)


class FileStateMapper:
    """Maps PHASE_5 JSON state files to UI data models.

    State Files:
        - routing_decisions.json: Task routing decisions
        - adapter_assignments.json: Tool-to-task assignments
        - execution_results.json: Task execution outcomes
        - router_state.json: Tool metrics and performance

    Graceful Degradation:
        - Missing files → empty data
        - Missing fields → sensible defaults
        - Malformed JSON → logged error, empty data
    """

    def __init__(self, state_dir: Path | str = ".state"):
        """Initialize mapper with state directory path.

        Args:
            state_dir: Directory containing state JSON files
        """
        self.state_dir = Path(state_dir)

    def _read_json_file(self, filename: str) -> Dict[str, Any]:
        """Read and parse JSON file with error handling.

        Args:
            filename: Name of JSON file to read

        Returns:
            Parsed JSON data, or empty dict on error
        """
        file_path = self.state_dir / filename

        if not file_path.exists():
            logger.debug(f"State file not found: {file_path}")
            return {}

        try:
            with file_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Malformed JSON in {file_path}: {e}")
            return {}
        except IOError as e:
            logger.error(f"Failed to read {file_path}: {e}")
            return {}

    def get_pipeline_summary(self, run_id: Optional[str] = None) -> PipelineSummary:
        """Generate pipeline summary from execution results.

        Args:
            run_id: Optional run ID filter (unused, for compatibility)

        Returns:
            PipelineSummary with aggregated task counts
        """
        results_data = self._read_json_file("execution_results.json")
        router_data = self._read_json_file("router_state.json")

        results = results_data.get("results", [])

        # Count tasks by status
        status_counts = Counter(r.get("status", "unknown") for r in results)

        total_tasks = len(results)
        running_tasks = status_counts.get("in_progress", 0)
        completed_tasks = status_counts.get("completed", 0)
        failed_tasks = status_counts.get("failed", 0)

        # Count active workers (tools with non-zero call count)
        metrics = router_data.get("metrics", {})
        active_workers = sum(
            1 for tool_metrics in metrics.values()
            if tool_metrics.get("call_count", 0) > 0
        )

        # Determine overall status
        if failed_tasks > 0:
            status = "error"
        elif running_tasks > 0:
            status = "running"
        elif total_tasks > 0 and completed_tasks == total_tasks:
            status = "idle"
        else:
            status = "idle"

        # Get last update time from file modification time
        results_file = self.state_dir / "execution_results.json"
        if results_file.exists():
            mtime = results_file.stat().st_mtime
            last_update = datetime.fromtimestamp(mtime)
        else:
            last_update = datetime.now()

        return PipelineSummary(
            total_tasks=total_tasks,
            running_tasks=running_tasks,
            completed_tasks=completed_tasks,
            failed_tasks=failed_tasks,
            active_workers=active_workers,
            last_update=last_update,
            status=status,
        )

    def get_tasks(
        self,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[TaskInfo]:
        """Get task list from execution results.

        Args:
            status: Optional status filter
            limit: Maximum tasks to return

        Returns:
            List of TaskInfo objects
        """
        results_data = self._read_json_file("execution_results.json")
        results = results_data.get("results", [])

        # Filter by status if specified
        if status:
            results = [r for r in results if r.get("status") == status]

        # Convert to TaskInfo objects
        tasks = []
        for result in results[:limit]:
            tasks.append(self._map_result_to_task_info(result))

        return tasks

    def get_task(self, task_id: str) -> Optional[TaskInfo]:
        """Get single task by ID.

        Args:
            task_id: Task identifier

        Returns:
            TaskInfo if found, None otherwise
        """
        results_data = self._read_json_file("execution_results.json")
        results = results_data.get("results", [])

        for result in results:
            if result.get("task_id") == task_id:
                return self._map_result_to_task_info(result)

        return None

    def _map_result_to_task_info(self, result: Dict[str, Any]) -> TaskInfo:
        """Map execution result to TaskInfo.

        Args:
            result: Raw execution result dict

        Returns:
            TaskInfo object
        """
        # Use task_kind as name (no human-readable name available)
        name = result.get("task_kind", "Unknown Task")

        # Map tool_id to worker_id
        worker_id = result.get("tool_id")

        # Error message from error field
        error_message = result.get("error")

        return TaskInfo(
            task_id=result.get("task_id", ""),
            name=name,
            status=result.get("status", "unknown"),
            worker_id=worker_id,
            start_time=None,  # Not available in state files
            end_time=None,    # Not available in state files
            error_message=error_message,
        )

    def get_executions(self, limit: int = 10) -> List[ExecutionInfo]:
        """Get execution list (derived from run_id).

        Args:
            limit: Maximum executions to return

        Returns:
            List of ExecutionInfo objects
        """
        results_data = self._read_json_file("execution_results.json")
        run_id = results_data.get("run_id")

        if not run_id:
            return []

        # Create single execution from run_id
        # (No phase tracking available in state files)
        return [
            ExecutionInfo(
                execution_id=run_id,
                phase_name=None,
                status="running",  # Inferred
                started_at=None,
                completed_at=None,
                metadata={},
            )
        ]

    def get_patch_ledger(self, limit: int = 100) -> List[PatchLedgerEntry]:
        """Get patch ledger entries.

        Args:
            limit: Maximum patches to return

        Returns:
            List of PatchLedgerEntry objects (empty for now - patch ledger format TBD)
        """
        # TODO: Implement when patch ledger file format is determined
        logger.debug("Patch ledger not yet implemented")
        return []

    def get_tool_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get tool performance metrics from router state.

        Returns:
            Dict mapping tool_id to metrics
        """
        router_data = self._read_json_file("router_state.json")
        return router_data.get("metrics", {})

    def get_routing_decisions(self) -> List[Dict[str, Any]]:
        """Get routing decisions.

        Returns:
            List of routing decision records
        """
        decisions_data = self._read_json_file("routing_decisions.json")
        return decisions_data.get("decisions", [])

    def get_adapter_assignments(self) -> List[Dict[str, Any]]:
        """Get tool-to-task adapter assignments.

        Returns:
            List of assignment records
        """
        assignments_data = self._read_json_file("adapter_assignments.json")
        return assignments_data.get("assignments", [])

    def get_pattern_runs(self, limit: int = 10) -> List[PatternRun]:
        """Get pattern execution runs (derived from execution results).

        Args:
            limit: Maximum runs to return

        Returns:
            List of PatternRun objects
        """
        results_data = self._read_json_file("execution_results.json")
        run_id = results_data.get("run_id")
        results = results_data.get("results", [])

        if not run_id or not results:
            return []

        # Aggregate results into a single pattern run
        total_steps = len(results)
        completed_steps = sum(
            1 for r in results
            if r.get("status") == "completed"
        )

        # Determine status
        if any(r.get("status") == "failed" for r in results):
            status = PatternStatus.FAILED
        elif any(r.get("status") == "in_progress" for r in results):
            status = PatternStatus.RUNNING
        elif completed_steps == total_steps:
            status = PatternStatus.COMPLETED
        else:
            status = PatternStatus.PENDING

        # Calculate progress
        progress = completed_steps / total_steps if total_steps > 0 else 0.0

        # Get timestamps from file
        results_file = self.state_dir / "execution_results.json"
        if results_file.exists():
            mtime = results_file.stat().st_mtime
            start_time = datetime.fromtimestamp(mtime)
        else:
            start_time = datetime.now()

        end_time = None
        if status in (PatternStatus.COMPLETED, PatternStatus.FAILED):
            end_time = start_time  # Approximate

        # Determine current phase from task kinds
        current_phase = None
        if results:
            # Use the most recent task kind as current phase
            in_progress = [r for r in results if r.get("status") == "in_progress"]
            if in_progress:
                current_phase = in_progress[0].get("task_kind", "unknown")

        return [
            PatternRun(
                run_id=run_id,
                pattern_id="phase5_execution",
                pattern_name="Phase 5 Execution",
                status=status,
                start_time=start_time,
                end_time=end_time,
                progress=progress,
                current_phase=current_phase,
                error_message=None,
            )
        ]

    def get_run_id(self) -> Optional[str]:
        """Get current run ID from state files.

        Returns:
            Run ID if available, None otherwise
        """
        results_data = self._read_json_file("execution_results.json")
        return results_data.get("run_id")
