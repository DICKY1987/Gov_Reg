# DOC_LINK: DOC-CORE-CORE-UI-MODELS-128
"""Data models for user-facing interface components.

This module defines the data structures used by TUI/GUI panels to display
pipeline state, health, and observability data.
"""

# DOC_ID: DOC-CORE-CORE-UI-MODELS-128

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple

# ============================================================================
# File Lifecycle Models
# ============================================================================


class FileState(Enum):
    """File lifecycle states."""

    DISCOVERED = "discovered"
    CLASSIFIED = "classified"
    INTAKE = "intake"
    ROUTED = "routed"
    PROCESSING = "processing"
    IN_FLIGHT = "in_flight"
    AWAITING_REVIEW = "awaiting_review"
    AWAITING_COMMIT = "awaiting_commit"
    COMMITTED = "committed"
    QUARANTINED = "quarantined"


class FileRole(Enum):
    """File type/role classification."""

    CODE = "code"
    SPEC = "spec"
    PLAN = "plan"
    TEST = "test"
    CONFIG = "config"
    DOCS = "docs"
    ASSET = "asset"
    OTHER = "other"


@dataclass
class FileToolTouch:
    """Record of a tool touching a file."""

    timestamp: datetime
    tool_id: str
    tool_name: str
    action: str
    status: str
    error_message: Optional[str] = None


@dataclass
class FileLifecycleRecord:
    """Complete file lifecycle tracking record."""

    file_id: str
    current_path: str
    origin_path: Optional[str] = None

    # Classification
    file_role: FileRole = FileRole.OTHER

    # State tracking
    current_state: FileState = FileState.DISCOVERED
    state_timestamps: Dict[str, datetime] = field(default_factory=dict)

    # Correlation
    workstream_id: Optional[str] = None
    job_id: Optional[str] = None
    run_id: Optional[str] = None

    # History
    tools_touched: List[FileToolTouch] = field(default_factory=list)

    # Error tracking
    last_error_code: Optional[str] = None
    last_error_message: Optional[str] = None
    last_error_plugin: Optional[str] = None

    # Final disposition
    committed_sha: Optional[str] = None
    committed_repo_path: Optional[str] = None
    quarantine_reason: Optional[str] = None
    quarantine_folder: Optional[str] = None

    # Timestamps
    first_seen: Optional[datetime] = None
    last_processed: Optional[datetime] = None
    time_in_current_state: Optional[float] = None


# ============================================================================
# Tool Health Models
# ============================================================================


class ToolStatus(Enum):
    """Tool health status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNREACHABLE = "unreachable"
    CIRCUIT_OPEN = "circuit_open"
    UNKNOWN = "unknown"


class ToolCategory(Enum):
    """Tool categories."""

    AI_EDITOR = "ai_editor"
    TEST_RUNNER = "test_runner"
    SCM = "scm"
    LINTER = "linter"
    ERROR_ENGINE = "error_engine"
    BUILD_TOOL = "build_tool"
    OTHER = "other"


@dataclass
class ToolHealthMetrics:
    """Performance and reliability metrics for a tool."""

    # Request counts
    requests_5min: int = 0
    requests_15min: int = 0
    requests_60min: int = 0

    # Success/failure
    success_count: int = 0
    failure_count: int = 0
    success_rate: float = 0.0

    # Latency (seconds)
    mean_latency: float = 0.0
    p95_latency: float = 0.0
    p99_latency: float = 0.0

    # Capacity
    max_concurrency: int = 1
    current_in_flight: int = 0
    queue_length: int = 0

    # Reliability
    retry_count: int = 0
    time_since_last_failure: Optional[float] = None

    # Output metrics
    avg_output_size_bytes: Optional[float] = None


@dataclass
class ToolHealthStatus:
    """Complete health status for a tool/adapter."""

    tool_id: str
    display_name: str
    category: ToolCategory
    version: Optional[str] = None

    # Status
    status: ToolStatus = ToolStatus.UNKNOWN
    status_reason: Optional[str] = None
    last_successful_invocation: Optional[datetime] = None

    # Metrics
    metrics: ToolHealthMetrics = field(default_factory=ToolHealthMetrics)


# ============================================================================
# Workstream Status Models
# ============================================================================


class WorkstreamStatus(Enum):
    """Workstream execution status."""

    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WorkstreamProgress:
    """Progress tracking for a workstream."""

    current_phase: Optional[str] = None
    total_phases: int = 0
    completed_phases: int = 0

    current_step: Optional[str] = None
    total_steps: int = 0
    completed_steps: int = 0

    progress_percentage: float = 0.0


@dataclass
class WorkstreamRecord:
    """Complete workstream tracking record."""

    ws_id: str
    run_id: str

    # Identification
    label: Optional[str] = None
    description: Optional[str] = None

    # Status
    status: WorkstreamStatus = WorkstreamStatus.PENDING
    progress: WorkstreamProgress = field(default_factory=WorkstreamProgress)

    # Timing
    start_time: Optional[datetime] = None
    last_update: Optional[datetime] = None
    total_duration_sec: Optional[float] = None

    # Counters
    files_processed: int = 0
    files_succeeded: int = 0
    files_quarantined: int = 0
    total_tool_invocations: int = 0

    # Artifacts
    worktree_path: Optional[str] = None
    spec_path: Optional[str] = None
    workstream_json_path: Optional[str] = None


# ============================================================================
# Error Record Models
# ============================================================================


class ErrorSeverity(Enum):
    """Error severity levels."""

    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error classification categories."""

    SYNTAX = "syntax"
    CONFIG = "config"
    NETWORK = "network"
    TOOL_TIMEOUT = "tool_timeout"
    AI_REFUSAL = "ai_refusal"
    VALIDATION_FAILED = "validation_failed"
    BUILD_FAILED = "build_failed"
    TEST_FAILED = "test_failed"
    MERGE_CONFLICT = "merge_conflict"
    PERMISSION_DENIED = "permission_denied"
    UNKNOWN = "unknown"


@dataclass
class ErrorRecord:
    """Structured error record for quarantine center."""

    error_id: str

    # Entity tracking
    entity_type: str  # "file", "job", "tool_instance", "workstream"
    file_id: Optional[str] = None
    job_id: Optional[str] = None
    ws_id: Optional[str] = None
    tool_id: Optional[str] = None
    run_id: Optional[str] = None

    # Classification
    plugin: Optional[str] = None
    severity: ErrorSeverity = ErrorSeverity.ERROR
    category: ErrorCategory = ErrorCategory.UNKNOWN

    # Messages
    human_message: str = ""
    technical_details: str = ""
    recommendation: Optional[str] = None

    # Timing
    first_seen: datetime = field(default_factory=lambda: datetime.now())
    last_seen: datetime = field(default_factory=lambda: datetime.now())
    occurrence_count: int = 1

    # Quarantine
    quarantine_path: Optional[str] = None
    can_retry: bool = True
    auto_fix_available: bool = False


# ============================================================================
# Dashboard Summary Models
# ============================================================================


@dataclass
class PipelineSummary:
    """High-level pipeline health summary for dashboard."""

    # Workstream/job counts
    workstreams_running: int = 0
    workstreams_queued: int = 0
    workstreams_completed: int = 0
    workstreams_failed: int = 0

    # File counts by state
    files_intake: int = 0
    files_classified: int = 0
    files_in_flight: int = 0
    files_awaiting_review: int = 0
    files_committed: int = 0
    files_quarantined: int = 0

    # Throughput
    files_per_hour: float = 0.0
    jobs_per_hour: float = 0.0
    avg_file_latency_sec: float = 0.0

    # Error surface
    errors_per_hour: float = 0.0
    top_error_types: List[Tuple[str, int]] = field(default_factory=list)

    # Tool health
    tools_healthy: int = 0
    tools_degraded: int = 0
    tools_down: int = 0


@dataclass
class ToolSummary:
    """One-line tool summary for dashboard."""

    tool_id: str
    tool_name: str
    status: ToolStatus
    success_rate: float
    p95_latency: float


# ============================================================================
# Run/Job Models
# ============================================================================


@dataclass
class JobRecord:
    """Job execution record."""

    job_id: str
    parent_ws_id: Optional[str] = None
    run_id: Optional[str] = None

    # Tool invocations
    tools_invoked: List[str] = field(default_factory=list)

    # Status
    latest_step_status: Optional[str] = None
    latest_step_description: Optional[str] = None
    exit_code: Optional[int] = None
    completed: bool = False

    # Timing
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


# ============================================================================
# Control Panel Models
# ============================================================================


class RunMode(Enum):
    """Pipeline run mode."""

    RUNNING = "running"
    DRAINING = "draining"
    PAUSED = "paused"


class HeadlessPolicy(Enum):
    """Headless execution policy."""

    ALLOW_ALL = "allow_all"
    REQUIRE_REVIEW_IF_RISKY = "require_review_if_risky"
    DRY_RUN_ONLY = "dry_run_only"


@dataclass
class PipelineControlState:
    """Current pipeline control settings."""

    run_mode: RunMode = RunMode.RUNNING

    # Concurrency
    global_max_workers: int = 4
    per_tool_concurrency: Dict[str, int] = field(default_factory=dict)

    # Headless policy
    headless_policy: HeadlessPolicy = HeadlessPolicy.REQUIRE_REVIEW_IF_RISKY

    # Sandbox
    active_worktree: Optional[str] = None
    worktree_to_branch_mapping: Dict[str, str] = field(default_factory=dict)

    # Logging
    log_level: str = "info"
