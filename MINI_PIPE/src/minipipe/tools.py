"""
Tool Adapter Layer for AI Development Pipeline.

Provides config-driven external tool execution with subprocess handling,
timeouts, error capture, and result tracking. Supports template-based
command rendering and standardized result reporting.
"""

# DOC_ID: DOC-CORE-ENGINE-TOOLS-161

import subprocess
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ToolResult:
    """
    Standardized result from tool execution.

    Attributes:
        tool_id: Identifier of the tool that was run
        command_line: Full command that was executed
        exit_code: Process exit code (0 for success, -1 for timeout)
        stdout: Standard output from the process
        stderr: Standard error from the process
        timed_out: Whether the process exceeded timeout limit
        started_at: ISO 8601 UTC timestamp when execution started
        completed_at: ISO 8601 UTC timestamp when execution completed
        duration_sec: Execution duration in seconds
        success: Whether execution was successful (based on exit codes)
    """

    tool_id: str
    command_line: str
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool
    started_at: str
    completed_at: str
    duration_sec: float
    success: bool

    def to_dict(self) -> Dict[str, Any]:
        """Convert ToolResult to dictionary."""
        return asdict(self)


# Global cache for tool profiles
_tool_profiles_cache: Optional[Dict[str, Any]] = None


def load_tool_profiles(profile_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load tool profiles from Invoke config hierarchy.

    Args:
        profile_path: DEPRECATED - Use invoke.yaml instead. If provided, shows warning.

    Returns:
        Dictionary of tool profiles keyed by tool_id

    Raises:
        FileNotFoundError: If invoke.yaml doesn't exist
    """
    global _tool_profiles_cache

    # Show deprecation warning if old path is used
    if profile_path:
        import warnings

        warnings.warn(
            f"Loading from {profile_path} is deprecated. "
            "Tool profiles are now loaded from invoke.yaml. "
            "This parameter will be removed in Phase G+1.",
            DeprecationWarning,
            stacklevel=2,
        )

    # Load from invoke.yaml via config_loader
    from core.config_loader import load_project_config

    cfg = load_project_config()
    tools_config = cfg.get("tools", {})

    if not tools_config:
        raise FileNotFoundError(
            "No tools configuration found in invoke.yaml. "
            "Run 'invoke bootstrap' to initialize configuration."
        )

    _tool_profiles_cache = tools_config
    return tools_config


def get_tool_profile(
    tool_id: str, profiles: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Retrieve a specific tool profile by ID.

    Args:
        tool_id: Identifier of the tool
        profiles: Optional pre-loaded profiles dict. If None, loads from default path.

    Returns:
        Tool profile configuration dictionary

    Raises:
        KeyError: If tool_id not found in profiles
        FileNotFoundError: If profile file doesn't exist (when loading)
    """
    if profiles is None:
        # Use cache if available, otherwise load
        if _tool_profiles_cache is None:
            profiles = load_tool_profiles()
        else:
            profiles = _tool_profiles_cache

    if tool_id not in profiles:
        raise KeyError(f"Tool profile '{tool_id}' not found in configuration")

    return profiles[tool_id]


def render_command(
    tool_id: str, context: Dict[str, Any], profile: Optional[Dict[str, Any]] = None
) -> List[str]:
    """
    Render command from tool profile with template substitution.

    Supports template variables:
        {cwd} - Current working directory
        {repo_root} - Repository root directory
        {message} - Custom message (from context)
        {file} - File path (from context)
        ... any key in context dict

    Args:
        tool_id: Identifier of the tool
        context: Dictionary of template variables for substitution
        profile: Optional pre-loaded tool profile. If None, loads from config.

    Returns:
        List of command arguments with templates substituted

    Raises:
        KeyError: If required template variable missing from context
    """
    if profile is None:
        profile = get_tool_profile(tool_id)

    # Build template context with defaults
    template_context = {
        "cwd": str(Path.cwd()),
        "repo_root": str(_get_repo_root()),
    }
    template_context.update(context)

    # Render command
    command = [profile["command"]]

    # Render args with template substitution
    for arg in profile.get("args", []):
        rendered_arg = arg
        # Simple template substitution
        for key, value in template_context.items():
            rendered_arg = rendered_arg.replace(f"{{{key}}}", str(value))
        command.append(rendered_arg)

    return command


def run_tool(
    tool_id: str,
    context: Dict[str, Any],
    *,
    run_id: Optional[str] = None,
    ws_id: Optional[str] = None,
) -> ToolResult:
    """
    Execute a tool with the given context.

    Main entry point for tool execution. Loads profile, renders command,
    executes subprocess with timeout, captures output, and returns
    standardized result.

    Args:
        tool_id: Identifier of the tool to run
        context: Template variables and configuration for this execution
        run_id: Optional run identifier (for DB integration in ws-ph03-db-integration)
        ws_id: Optional workstream identifier (for DB integration)

    Returns:
        ToolResult with execution details and output

    Raises:
        KeyError: If tool_id not found or required context variable missing
        FileNotFoundError: If tool binary not found
    """
    # Load profile
    profile = get_tool_profile(tool_id)

    # Render command
    command = render_command(tool_id, context, profile)
    command_line = " ".join(command)

    # Prepare execution environment
    env = None
    if profile.get("env"):
        import os

        env = os.environ.copy()
        env.update(profile["env"])

    # Determine working directory
    working_dir = profile.get("working_dir")
    if working_dir:
        # Render working_dir template
        working_dir_context = {
            "cwd": str(Path.cwd()),
            "repo_root": str(_get_repo_root()),
        }
        working_dir_context.update(context)

        for key, value in working_dir_context.items():
            working_dir = working_dir.replace(f"{{{key}}}", str(value))

    # Get timeout
    timeout_sec = profile.get("timeout_sec", 60)

    # Execute
    started_at = datetime.now(UTC).isoformat() + "Z"
    start_time = time.time()

    timed_out = False
    exit_code = 0
    stdout = ""
    stderr = ""

    try:
        result = subprocess.run(
            command,
            capture_output=profile.get("capture_output", True),
            timeout=timeout_sec,
            env=env,
            cwd=working_dir,
            text=True,
        )
        exit_code = result.returncode
        stdout = result.stdout or ""
        stderr = result.stderr or ""

    except subprocess.TimeoutExpired as e:
        timed_out = True
        exit_code = -1
        stdout = e.stdout.decode("utf-8") if e.stdout else ""
        stderr = e.stderr.decode("utf-8") if e.stderr else ""

    except FileNotFoundError as e:
        # Tool binary not found
        exit_code = -2
        stderr = f"Tool binary not found: {e}"

    except Exception as e:
        # Other execution errors
        exit_code = -3
        stderr = f"Execution error: {e}"

    # Calculate duration
    end_time = time.time()
    duration_sec = end_time - start_time
    completed_at = datetime.now(UTC).isoformat() + "Z"

    # Determine success
    success_exit_codes = profile.get("success_exit_codes", [0])
    success = exit_code in success_exit_codes and not timed_out

    return ToolResult(
        tool_id=tool_id,
        command_line=command_line,
        exit_code=exit_code,
        stdout=stdout,
        stderr=stderr,
        timed_out=timed_out,
        started_at=started_at,
        completed_at=completed_at,
        duration_sec=duration_sec,
        success=success,
    )


def _get_repo_root() -> Path:
    """
    Get the repository root directory.

    Searches upward from current directory for .git directory.

    Returns:
        Path to repository root

    Raises:
        RuntimeError: If .git directory not found
    """
    current = Path.cwd().resolve()

    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent

    raise RuntimeError("Could not find repository root (.git directory not found)")
