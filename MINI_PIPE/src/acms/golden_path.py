"""
ACMS Golden Path Documentation

This module defines the single recommended execution path for the ACMS system.
All other orchestration flows are optional extensions.

GOLDEN PATH: repo_root → gaps → plan → MINI_PIPE execution → summary

Required Components (Core Path):
  1. acms_controller.py - Main orchestrator
  2. gap_registry.py - Gap storage and queries
  3. execution_planner.py - Workstream clustering
  4. phase_plan_compiler.py - Plan generation
  5. acms_minipipe_adapter.py - MINI_PIPE interface
  6. MINI_PIPE_orchestrator.py - Execution engine
  7. MINI_PIPE_scheduler.py - Task scheduling
  8. MINI_PIPE_router.py - Task routing
  9. MINI_PIPE_executor.py - Task execution
  10. MINI_PIPE_tools.py - Tool adapters

Optional Components (Advanced Features):
  - MINI_PIPE_process_spawner.py - Long-lived worker processes
  - MINI_PIPE_circuit_breaker*.py - Circuit breaker patterns
  - MINI_PIPE_retry.py - Retry strategies
  - MINI_PIPE_resilient_executor.py - Enhanced executor
  - MINI_PIPE_recovery.py - Recovery logic
  - MINI_PIPE_patch_converter.py - Patch normalization
  - MINI_PIPE_patch_ledger.py - Patch state tracking
  - MINI_PIPE_*_trigger.py - File system triggers

Usage (Recommended):
    from acms_controller import ACMSController
    
    # Single golden path entrypoint
    controller = ACMSController(repo_root=Path("/path/to/repo"))
    result = controller.run_full_cycle(mode="full")

CLI Usage:
    # Golden path execution
    python acms_controller.py /path/to/repo --mode full
    
    # Or use the demo
    python demo_acms_pipeline.py

Configuration:
    All optional features are disabled by default.
    Enable advanced features via configuration flags:
    
    - triggers_enabled: bool = False
    - enable_resilience: bool = False
    - enable_patch_ledger: bool = False

State Management:
    Each run is immutable with explicit state transitions:
    INIT → GAP_ANALYSIS → PLANNING → EXECUTION → SUMMARY → DONE
    
    Run artifacts stored in: .acms_runs/{run_id}/
    - acms_state.json - Run state and metadata
    - gap_analysis_report.json - Raw gap analysis
    - gap_registry.json - Normalized gaps
    - workstreams.json - Clustered workstreams
    - mini_pipe_execution_plan.json - Execution plan
    - run_status.json - Unified status view
    - run.ledger.jsonl - State transition log
"""

from enum import Enum
from typing import Final


class RunState(Enum):
    """ACMS run state machine"""

    INIT = "init"
    GAP_ANALYSIS = "gap_analysis"
    PLANNING = "planning"
    EXECUTION = "execution"
    SUMMARY = "summary"
    DONE = "done"
    FAILED = "failed"


# Golden path components (required)
CORE_COMPONENTS: Final = [
    "acms_controller.py",
    "gap_registry.py",
    "execution_planner.py",
    "phase_plan_compiler.py",
    "acms_minipipe_adapter.py",
    "MINI_PIPE_orchestrator.py",
    "MINI_PIPE_scheduler.py",
    "MINI_PIPE_router.py",
    "MINI_PIPE_executor.py",
    "MINI_PIPE_tools.py",
]

# Optional components (advanced features)
OPTIONAL_COMPONENTS: Final = [
    "MINI_PIPE_process_spawner.py",
    "MINI_PIPE_circuit_breaker.py",
    "MINI_PIPE_circuit_breakers.py",
    "MINI_PIPE_retry.py",
    "MINI_PIPE_resilient_executor.py",
    "MINI_PIPE_recovery.py",
    "MINI_PIPE_patch_converter.py",
    "MINI_PIPE_patch_ledger.py",
    "MINI_PIPE_request_builder_trigger.py",
    "MINI_PIPE_router_trigger.py",
    "MINI_PIPE_monitoring_trigger.py",
]

# Default configuration (minimal golden path)
DEFAULT_CONFIG: Final = {
    "triggers_enabled": False,
    "enable_resilience": False,
    "enable_patch_ledger": False,
    "max_concurrent_tasks": 4,
    "timeout_seconds": 3600,
}
