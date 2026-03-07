# DOC_LINK: DOC-ERROR-UTILS-TYPES-146
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, TypedDict


@dataclass
class PluginIssue:
    tool: str
    path: str
    line: Optional[int] = None
    column: Optional[int] = None
    code: Optional[str] = None
    category: Optional[str] = (
        None  # e.g., "syntax", "type", "style", "formatting", "security", "test_failure"
    )
    severity: Optional[str] = None  # e.g., "error", "warning", "info"
    message: Optional[str] = None
    layer: Optional[str] = (
        None  # e.g., "Layer 1 - Infrastructure", "Layer 5 - Business Logic"
    )


@dataclass
class PluginResult:
    plugin_id: str
    success: bool
    issues: List[PluginIssue] = field(default_factory=list)
    stdout: str = ""
    stderr: str = ""
    returncode: int = 0
    duration_ms: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class PluginManifest(TypedDict, total=False):
    plugin_id: str
    name: str
    file_extensions: List[str]
    requires: List[str]
    tool: Dict[str, Any]


@dataclass
class PipelineSummary:
    plugins_run: int
    total_errors: int
    total_warnings: int
    auto_fixed: int = 0
    issues_by_tool: Dict[str, int] = field(default_factory=dict)
    issues_by_category: Dict[str, int] = field(default_factory=dict)
    has_hard_fail: Optional[bool] = None
    style_only: Optional[bool] = None
    auto_repairable: int = 0  # Errors with available auto-fix
    requires_human: int = 0  # Errors needing manual intervention


@dataclass
class PipelineReport:
    run_id: str
    file_in: str
    file_out: Optional[str]
    timestamp_utc: str
    toolchain: Dict[str, str] = field(default_factory=dict)
    summary: PipelineSummary = field(default=None)  # type: ignore[assignment]
    issues: List[PluginIssue] = field(default_factory=list)
    status: str = "completed"  # or "skipped" / "failed"
