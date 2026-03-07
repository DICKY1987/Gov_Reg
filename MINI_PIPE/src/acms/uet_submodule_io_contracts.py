"""
UET Submodule IO Contracts V1

Standardized data contracts for cross-module communication.
All module boundaries MUST use these typed structures.
Reference: UET_SUBMODULE_IO_CONTRACTS.md
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


# ============================================================================
# EXECUTION CONTRACTS
# ============================================================================


@dataclass
class ExecutionRequestV1:
    """
    Request for executing a pattern/task.
    Used at orchestrator -> executor boundary.
    """

    request_id: str
    operation_kind: str  # e.g., "EXEC-AIDER-EDIT", "EXEC-PYTEST", "EXEC-CREATE"
    pattern_id: str  # Reference to PATTERN_INDEX.yaml
    workspace: "GitWorkspaceRefV1"
    file_scope: List[str] = field(default_factory=list)  # Files to operate on
    context: Dict[str, Any] = field(
        default_factory=dict
    )  # run_id, ws_id, phase_id, etc.
    inputs: Dict[str, Any] = field(default_factory=dict)  # Pattern-specific parameters
    timeout_seconds: int = 1800
    created_at: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat() + "Z"


@dataclass
class ExecutionResultV1:
    """
    Result from pattern/task execution.
    Returned from executor -> orchestrator.
    """

    request_id: str
    success: bool
    exit_code: int
    outputs: Dict[str, Any] = field(default_factory=dict)  # Pattern-specific outputs
    errors: List["ErrorEventV1"] = field(default_factory=list)
    patches: List["PatchRecordV1"] = field(default_factory=list)
    logs: List["LogEventV1"] = field(default_factory=list)
    run_record: Optional["RunRecordV1"] = None
    duration_seconds: float = 0.0
    completed_at: Optional[str] = None

    def __post_init__(self):
        if self.completed_at is None:
            self.completed_at = (
                datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            )


# ============================================================================
# TOOL EXECUTION CONTRACTS
# ============================================================================


@dataclass
class ToolRunRequestV1:
    """
    Request for running an external tool.
    Used at pattern engine -> tool adapter boundary.
    """

    tool_id: str  # e.g., "aider", "pytest", "pyrefact"
    cmd: List[str]  # Full command with arguments
    cwd: str  # Working directory (absolute path)
    env: Dict[str, str] = field(default_factory=dict)  # Environment variables
    timeout_seconds: int = 1800
    stdin_data: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)  # For logging/tracing


@dataclass
class ToolRunResultV1:
    """
    Result from external tool execution.
    NEVER raises exceptions - all failures encoded in exit_code/stderr.
    """

    tool_id: str
    exit_code: int  # 0=success, >0=tool error, -1=timeout, -2=not found, -3=exec error
    stdout: str
    stderr: str
    duration_seconds: float
    timed_out: bool = False
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    def __post_init__(self):
        if self.started_at is None:
            self.started_at = (
                datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            )
        if self.completed_at is None:
            self.completed_at = (
                datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            )

    @property
    def success(self) -> bool:
        """Tool succeeded if exit_code is 0."""
        return self.exit_code == 0


# ============================================================================
# GIT WORKSPACE CONTRACTS
# ============================================================================


@dataclass
class GitWorkspaceRefV1:
    """
    Reference to a Git workspace/worktree.
    Immutable identifier for a workspace.
    """

    ws_id: str  # Unique workspace ID
    root_path: str  # Absolute path to workspace root
    branch_name: str  # Git branch name
    commit_sha: Optional[str] = None  # HEAD commit at creation time
    created_at: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = (
                datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            )


@dataclass
class GitStatusV1:
    """
    Status of a Git workspace.
    Snapshot of current Git state.
    """

    workspace_ref: GitWorkspaceRefV1
    is_clean: bool
    modified_files: List[str] = field(default_factory=list)
    untracked_files: List[str] = field(default_factory=list)
    staged_files: List[str] = field(default_factory=list)
    current_commit: Optional[str] = None
    checked_at: Optional[str] = None

    def __post_init__(self):
        if self.checked_at is None:
            self.checked_at = (
                datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            )


# ============================================================================
# PATCH & CHANGE TRACKING CONTRACTS
# ============================================================================


@dataclass
class PatchRecordV1:
    """
    Record of a code patch/change.
    Immutable record for audit trail.
    """

    patch_id: str
    file_path: str
    operation: str  # "create", "edit", "delete"
    diff: Optional[str] = None  # Unified diff format
    tool_id: Optional[str] = None  # Tool that created the patch
    request_id: Optional[str] = None  # Associated ExecutionRequest
    created_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat() + "Z"


# ============================================================================
# ERROR & LOGGING CONTRACTS
# ============================================================================


class ErrorSeverity(Enum):
    """Error severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ErrorEventV1:
    """
    Structured error event.
    Never raise exceptions across module boundaries - return these instead.
    """

    error_id: str
    severity: ErrorSeverity
    message: str
    error_code: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    stacktrace: Optional[str] = None
    timestamp: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = (
                datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            )


@dataclass
class LogEventV1:
    """
    Structured log event.
    For observability and debugging.
    """

    level: str  # "DEBUG", "INFO", "WARNING", "ERROR"
    message: str
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = (
                datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            )


@dataclass
class RunRecordV1:
    """
    Complete record of a pattern/task execution.
    Combines request, result, and all events.
    """

    record_id: str
    request: ExecutionRequestV1
    result: ExecutionResultV1
    tool_runs: List[ToolRunResultV1] = field(default_factory=list)
    events: List[LogEventV1] = field(default_factory=list)
    created_at: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = (
                datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            )


# ============================================================================
# WORKSTREAM CONTRACTS
# ============================================================================


@dataclass
class WorkstreamTaskV1:
    """
    A single task within a workstream.
    Maps to ExecutionRequestV1 during execution.
    """

    task_id: str
    pattern_id: str
    operation_kind: str
    file_scope: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)  # Other task_ids
    inputs: Dict[str, Any] = field(default_factory=dict)
    timeout_seconds: int = 1800
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkstreamV1:
    """
    UET-compatible workstream definition.
    Reference: UET_WORKSTREAM_SPEC.md
    """

    ws_id: str
    name: str
    description: str
    tasks: List[WorkstreamTaskV1] = field(default_factory=list)
    parallelism: int = 1  # Max parallel tasks
    workspace_ref: Optional[GitWorkspaceRefV1] = None
    gap_ids: List[str] = field(default_factory=list)  # Source gaps
    priority_score: float = 0.0
    dependencies: List[str] = field(default_factory=list)  # Other ws_ids
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = (
                datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "ws_id": self.ws_id,
            "name": self.name,
            "description": self.description,
            "tasks": [
                {
                    "task_id": t.task_id,
                    "pattern_id": t.pattern_id,
                    "operation_kind": t.operation_kind,
                    "file_scope": t.file_scope,
                    "dependencies": t.dependencies,
                    "inputs": t.inputs,
                    "timeout_seconds": t.timeout_seconds,
                    "metadata": t.metadata,
                }
                for t in self.tasks
            ],
            "parallelism": self.parallelism,
            "workspace_ref": {
                "ws_id": self.workspace_ref.ws_id,
                "root_path": self.workspace_ref.root_path,
                "branch_name": self.workspace_ref.branch_name,
                "commit_sha": self.workspace_ref.commit_sha,
                "created_at": self.workspace_ref.created_at,
            }
            if self.workspace_ref
            else None,
            "gap_ids": self.gap_ids,
            "priority_score": self.priority_score,
            "dependencies": self.dependencies,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }
