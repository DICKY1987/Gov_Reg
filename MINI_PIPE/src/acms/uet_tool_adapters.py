"""
UET Contract-Compliant Tool Adapters

Provides contract-based tool execution following UET_SUBMODULE_IO_CONTRACTS.
All tool invocations MUST go through these adapters.

Reference: DOC_AIDER_CONTRACT.md, UET_ABSTRACTION_GUIDELINES.md
"""

import json
import os
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.acms.uet_submodule_io_contracts import (
    ErrorEventV1,
    ErrorSeverity,
    LogEventV1,
    ToolRunRequestV1,
    ToolRunResultV1,
)


# ============================================================================
# CORE TOOL EXECUTION
# ============================================================================


def run_tool(request: ToolRunRequestV1) -> ToolRunResultV1:
    """
    Execute an external tool according to UET contracts.

    NEVER raises exceptions - all failures encoded in ToolRunResultV1.

    Args:
        request: Tool execution request

    Returns:
        ToolRunResultV1 with exit_code, stdout, stderr, duration
    """
    started_at = time.time()
    start_timestamp = _utc_timestamp()

    # Initialize result variables
    exit_code = 0
    stdout = ""
    stderr = ""
    timed_out = False

    # Validate request
    if not request.cmd:
        return ToolRunResultV1(
            tool_id=request.tool_id,
            exit_code=-3,
            stdout="",
            stderr="Empty command list",
            duration_seconds=0.0,
            timed_out=False,
            started_at=start_timestamp,
            completed_at=_utc_timestamp(),
        )

    # Check working directory exists
    if not Path(request.cwd).exists():
        return ToolRunResultV1(
            tool_id=request.tool_id,
            exit_code=-3,
            stdout="",
            stderr=f"Working directory does not exist: {request.cwd}",
            duration_seconds=0.0,
            timed_out=False,
            started_at=start_timestamp,
            completed_at=_utc_timestamp(),
        )

    # Prepare environment
    env = os.environ.copy()
    env.update(request.env)

    # Execute subprocess
    try:
        result = subprocess.run(
            request.cmd,
            cwd=request.cwd,
            env=env,
            capture_output=True,
            text=True,
            timeout=request.timeout_seconds,
            stdin=subprocess.PIPE if request.stdin_data else None,
            input=request.stdin_data,
        )
        exit_code = result.returncode
        stdout = result.stdout or ""
        stderr = result.stderr or ""

    except subprocess.TimeoutExpired as e:
        timed_out = True
        exit_code = -1
        stdout = e.stdout.decode("utf-8") if e.stdout else ""
        stderr = f"Process timed out after {request.timeout_seconds} seconds"
        if e.stderr:
            stderr += f"\n{e.stderr.decode('utf-8')}"

    except FileNotFoundError as e:
        exit_code = -2
        stderr = f"Binary not found: {request.cmd[0]}\n{e}"

    except Exception as e:
        exit_code = -3
        stderr = f"Execution error: {type(e).__name__}: {e}"

    # Calculate duration
    duration = time.time() - started_at
    completed_timestamp = _utc_timestamp()

    return ToolRunResultV1(
        tool_id=request.tool_id,
        exit_code=exit_code,
        stdout=stdout,
        stderr=stderr,
        duration_seconds=duration,
        timed_out=timed_out,
        started_at=start_timestamp,
        completed_at=completed_timestamp,
    )


# ============================================================================
# AIDER ADAPTER (DOC_AIDER_CONTRACT)
# ============================================================================


def build_aider_tool_request(
    model_name: str,
    prompt_file: str,
    file_scope: List[str],
    workspace_root: str,
    context: Optional[Dict[str, Any]] = None,
    timeout_seconds: int = 1800,
) -> ToolRunRequestV1:
    """
    Build ToolRunRequestV1 for Aider according to DOC_AIDER_CONTRACT.

    Args:
        model_name: LLM model to use (e.g., "gpt-4")
        prompt_file: Path to file containing instructions
        file_scope: List of files to edit
        workspace_root: Absolute path to worktree root
        context: Optional context for logging (run_id, ws_id, etc.)
        timeout_seconds: Execution timeout

    Returns:
        ToolRunRequestV1 configured for Aider
    """
    # Build command
    cmd = [
        "aider",
        "--no-auto-commits",
        "--yes",
        "--model",
        model_name,
        "--message-file",
        prompt_file,
    ]

    # Add files to edit
    cmd.extend(file_scope)

    # Prepare environment
    env = {
        "AIDER_NO_AUTO_COMMITS": "1",
    }
    if model_name:
        env["AIDER_MODEL"] = model_name

    return ToolRunRequestV1(
        tool_id="aider",
        cmd=cmd,
        cwd=workspace_root,
        env=env,
        timeout_seconds=timeout_seconds,
        context=context or {},
    )


def run_aider(
    request: ToolRunRequestV1, context: Optional[Dict[str, Any]] = None
) -> ToolRunResultV1:
    """
    Execute Aider according to DOC_AIDER_CONTRACT.

    NEVER raises exceptions - all failures encoded in ToolRunResultV1.

    Args:
        request: Tool execution request (should have tool_id="aider")
        context: Execution context (for logging/events)

    Returns:
        ToolRunResultV1 with exit_code, stdout, stderr, duration
    """
    # Validate tool_id
    if request.tool_id != "aider":
        return ToolRunResultV1(
            tool_id=request.tool_id,
            exit_code=-3,
            stdout="",
            stderr=f"Expected tool_id='aider', got '{request.tool_id}'",
            duration_seconds=0.0,
            timed_out=False,
            started_at=_utc_timestamp(),
            completed_at=_utc_timestamp(),
        )

    # Log tool invocation
    log_event = LogEventV1(
        level="INFO",
        message=f"Running aider: {' '.join(request.cmd)}",
        context={
            "tool_id": "aider",
            "cwd": request.cwd,
            **(context or {}),
        },
    )
    _log_event(log_event)

    # Execute via generic run_tool
    result = run_tool(request)

    # Log result
    result_log = LogEventV1(
        level="INFO" if result.success else "ERROR",
        message=f"Aider completed: exit_code={result.exit_code}, duration={result.duration_seconds:.2f}s",
        context={
            "tool_id": "aider",
            "exit_code": result.exit_code,
            "duration_seconds": result.duration_seconds,
            "timed_out": result.timed_out,
            **(context or {}),
        },
    )
    _log_event(result_log)

    return result


# ============================================================================
# OTHER TOOL ADAPTERS
# ============================================================================


def run_pytest(
    test_paths: List[str],
    workspace_root: str,
    context: Optional[Dict[str, Any]] = None,
    timeout_seconds: int = 600,
) -> ToolRunResultV1:
    """
    Execute pytest with contract compliance.

    Args:
        test_paths: List of test files/directories
        workspace_root: Absolute path to worktree root
        context: Optional context for logging
        timeout_seconds: Execution timeout

    Returns:
        ToolRunResultV1
    """
    cmd = ["pytest", "-v", "--tb=short"]
    cmd.extend(test_paths)

    request = ToolRunRequestV1(
        tool_id="pytest",
        cmd=cmd,
        cwd=workspace_root,
        env={},
        timeout_seconds=timeout_seconds,
        context=context or {},
    )

    return run_tool(request)


def run_pyrefact(
    file_paths: List[str],
    workspace_root: str,
    context: Optional[Dict[str, Any]] = None,
    timeout_seconds: int = 300,
) -> ToolRunResultV1:
    """
    Execute pyrefact with contract compliance.

    Args:
        file_paths: List of files to refactor
        workspace_root: Absolute path to worktree root
        context: Optional context for logging
        timeout_seconds: Execution timeout

    Returns:
        ToolRunResultV1
    """
    cmd = ["pyrefact"]
    cmd.extend(file_paths)

    request = ToolRunRequestV1(
        tool_id="pyrefact",
        cmd=cmd,
        cwd=workspace_root,
        env={},
        timeout_seconds=timeout_seconds,
        context=context or {},
    )

    return run_tool(request)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _utc_timestamp() -> str:
    """Generate ISO 8601 UTC timestamp."""
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _log_event(event: LogEventV1):
    """
    Log an event.

    In production, this would write to a structured event log.
    For now, just print to stderr.
    """
    import sys
    import json

    # Simple JSON logging
    log_data = {
        "timestamp": event.timestamp,
        "level": event.level,
        "message": event.message,
        "context": event.context,
    }

    # Write to stderr (won't interfere with stdout captures)
    print(json.dumps(log_data), file=sys.stderr)


def build_error_event(
    message: str,
    severity: ErrorSeverity = ErrorSeverity.ERROR,
    error_code: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    stacktrace: Optional[str] = None,
) -> ErrorEventV1:
    """
    Build a structured error event.

    Args:
        message: Error message
        severity: Error severity level
        error_code: Optional error code
        context: Optional context dict
        stacktrace: Optional stack trace

    Returns:
        ErrorEventV1
    """
    return ErrorEventV1(
        error_id=f"err-{uuid.uuid4().hex[:8]}",
        severity=severity,
        message=message,
        error_code=error_code,
        context=context or {},
        stacktrace=stacktrace,
    )


def load_tool_profiles(
    profile_path: str = "config/tool_profiles.json",
) -> Dict[str, Any]:
    """
    Load tool profiles from configuration.

    Args:
        profile_path: Path to tool_profiles.json

    Returns:
        Dictionary of tool profiles

    Raises:
        FileNotFoundError: If profile file doesn't exist
    """
    path = Path(profile_path)
    if not path.exists():
        raise FileNotFoundError(f"Tool profiles not found: {profile_path}")

    with open(path, "r", encoding="utf-8") as f:
        config = json.load(f)

    return config.get("profiles", {})


def get_tool_profile(
    tool_id: str, profiles: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Get a specific tool profile.

    Args:
        tool_id: Tool identifier
        profiles: Optional pre-loaded profiles dict

    Returns:
        Tool profile dictionary

    Raises:
        KeyError: If tool_id not found
    """
    if profiles is None:
        profiles = load_tool_profiles()

    if tool_id not in profiles:
        raise KeyError(f"Tool profile not found: {tool_id}")

    return profiles[tool_id]
