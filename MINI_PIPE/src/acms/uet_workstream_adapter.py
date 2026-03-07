"""
UET Workstream Adapter for MINI_PIPE

Loads UET workstream JSON files and converts them to ExecutionRequestV1 for execution.
Integrates ACMS workstreams with MINI_PIPE orchestrator.

Reference: Track 2.3 - UET_ALIGNMENT_IMPLEMENTATION_GUIDE.md
"""

import json
import logging
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.acms.path_registry import resolve_path
from src.acms.uet_submodule_io_contracts import (
    ExecutionRequestV1,
    ExecutionResultV1,
    GitWorkspaceRefV1,
    WorkstreamV1,
    WorkstreamTaskV1,
)

logger = logging.getLogger(__name__)


class UETWorkstreamAdapter:
    """
    Adapter for loading and executing UET workstreams via MINI_PIPE.

    Responsibilities:
    - Load workstream JSON files
    - Validate against UET schema
    - Convert WorkstreamV1 → List[ExecutionRequestV1]
    - Handle workspace references
    - Track execution state
    """

    def __init__(self, workspace_ref: Optional[GitWorkspaceRefV1] = None):
        """
        Initialize adapter.

        Args:
            workspace_ref: Optional default workspace reference for all workstreams
        """
        self.workspace_ref = workspace_ref
        self.loaded_workstreams: Dict[str, WorkstreamV1] = {}

    def load_workstream(self, workstream_path: Path) -> WorkstreamV1:
        """
        Load a workstream from JSON file.

        Args:
            workstream_path: Path to workstream JSON file

        Returns:
            WorkstreamV1 object

        Raises:
            FileNotFoundError: If workstream file doesn't exist
            ValueError: If workstream JSON is invalid
        """
        if not workstream_path.exists():
            raise FileNotFoundError(f"Workstream not found: {workstream_path}")

        try:
            with open(workstream_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in workstream file: {e}")

        # Convert to WorkstreamV1
        workstream = self._dict_to_workstream(data)

        # Cache it
        self.loaded_workstreams[workstream.ws_id] = workstream

        logger.info(
            f"Loaded workstream {workstream.ws_id} with {len(workstream.tasks)} tasks"
        )
        return workstream

    def load_workstreams_from_directory(self, directory: Path) -> List[WorkstreamV1]:
        """
        Load all workstream JSON files from a directory.

        Args:
            directory: Directory containing workstream JSON files

        Returns:
            List of WorkstreamV1 objects
        """
        if not directory.exists():
            logger.warning(f"Workstream directory does not exist: {directory}")
            return []

        workstreams = []
        for json_file in directory.glob("ws-*.json"):
            try:
                ws = self.load_workstream(json_file)
                workstreams.append(ws)
            except Exception as e:
                logger.error(f"Failed to load workstream from {json_file}: {e}")

        logger.info(f"Loaded {len(workstreams)} workstreams from {directory}")
        return workstreams

    def workstream_to_execution_requests(
        self,
        workstream: WorkstreamV1,
        workspace_override: Optional[GitWorkspaceRefV1] = None,
    ) -> List[ExecutionRequestV1]:
        """
        Convert a WorkstreamV1 to a list of ExecutionRequestV1 objects.

        Args:
            workstream: Workstream to convert
            workspace_override: Optional workspace to override workstream's workspace_ref

        Returns:
            List of execution requests (one per task)
        """
        requests = []

        # Determine workspace
        workspace = workspace_override or workstream.workspace_ref or self.workspace_ref
        if not workspace:
            raise ValueError(
                f"No workspace reference available for workstream {workstream.ws_id}. "
                "Provide workspace_ref in workstream, as override, or in adapter init."
            )

        # Convert each task
        for task in workstream.tasks:
            request = ExecutionRequestV1(
                request_id=f"{workstream.ws_id}-{task.task_id}-{uuid.uuid4().hex[:8]}",
                operation_kind=task.operation_kind,
                pattern_id=task.pattern_id,
                workspace=workspace,
                file_scope=task.file_scope,
                context={
                    "ws_id": workstream.ws_id,
                    "task_id": task.task_id,
                    "run_id": workstream.metadata.get("run_id"),
                    "gap_ids": workstream.gap_ids,
                    **task.metadata,
                },
                inputs=task.inputs,
                timeout_seconds=task.timeout_seconds,
            )
            requests.append(request)

        logger.info(
            f"Converted workstream {workstream.ws_id} to {len(requests)} execution requests"
        )
        return requests

    def _dict_to_workstream(self, data: Dict[str, Any]) -> WorkstreamV1:
        """Convert dictionary to WorkstreamV1."""
        # Parse workspace_ref if present
        workspace_ref = None
        if data.get("workspace_ref"):
            ws_ref_data = data["workspace_ref"]
            workspace_ref = GitWorkspaceRefV1(
                ws_id=ws_ref_data["ws_id"],
                root_path=ws_ref_data["root_path"],
                branch_name=ws_ref_data["branch_name"],
                commit_sha=ws_ref_data.get("commit_sha"),
                created_at=ws_ref_data.get("created_at"),
            )

        # Parse tasks
        tasks = []
        for task_data in data.get("tasks", []):
            task = WorkstreamTaskV1(
                task_id=task_data["task_id"],
                pattern_id=task_data["pattern_id"],
                operation_kind=task_data["operation_kind"],
                file_scope=task_data.get("file_scope", []),
                dependencies=task_data.get("dependencies", []),
                inputs=task_data.get("inputs", {}),
                timeout_seconds=task_data.get("timeout_seconds", 1800),
                metadata=task_data.get("metadata", {}),
            )
            tasks.append(task)

        # Build workstream
        return WorkstreamV1(
            ws_id=data["ws_id"],
            name=data["name"],
            description=data["description"],
            tasks=tasks,
            parallelism=data.get("parallelism", 1),
            workspace_ref=workspace_ref,
            gap_ids=data.get("gap_ids", []),
            priority_score=data.get("priority_score", 0.0),
            dependencies=data.get("dependencies", []),
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at"),
        )

    def get_workstream_by_id(self, ws_id: str) -> Optional[WorkstreamV1]:
        """Get a loaded workstream by ID."""
        return self.loaded_workstreams.get(ws_id)

    def list_loaded_workstreams(self) -> List[str]:
        """List all loaded workstream IDs."""
        return list(self.loaded_workstreams.keys())


def load_workstream_for_run(run_id: str) -> List[WorkstreamV1]:
    """
    Convenience function to load all workstreams for a specific run.

    Args:
        run_id: Run identifier

    Returns:
        List of workstreams for this run

    Example:
        >>> workstreams = load_workstream_for_run("run-001")
        >>> print(f"Loaded {len(workstreams)} workstreams")
    """
    try:
        # Use path registry to get workstream directory
        ws_dir = resolve_path("workstreams.runtime.plans_dir", run_id=run_id)

        adapter = UETWorkstreamAdapter()
        workstreams = adapter.load_workstreams_from_directory(ws_dir)

        return workstreams
    except Exception as e:
        logger.error(f"Failed to load workstreams for run {run_id}: {e}")
        return []


def workstream_file_to_execution_requests(
    workstream_file: Path,
    workspace: GitWorkspaceRefV1,
) -> List[ExecutionRequestV1]:
    """
    Convenience function to convert a workstream file directly to execution requests.

    Args:
        workstream_file: Path to workstream JSON
        workspace: Git workspace reference

    Returns:
        List of execution requests

    Example:
        >>> workspace = GitWorkspaceRefV1(
        ...     ws_id="workspace-main",
        ...     root_path="/path/to/repo",
        ...     branch_name="main",
        ... )
        >>> requests = workstream_file_to_execution_requests(
        ...     Path(".acms_runs/run-001/workstreams/ws-acms-001.json"),
        ...     workspace,
        ... )
    """
    adapter = UETWorkstreamAdapter(workspace_ref=workspace)
    workstream = adapter.load_workstream(workstream_file)
    requests = adapter.workstream_to_execution_requests(workstream)
    return requests
