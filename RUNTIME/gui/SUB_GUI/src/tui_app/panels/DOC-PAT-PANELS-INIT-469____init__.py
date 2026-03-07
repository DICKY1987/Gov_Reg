"""Panel implementations for TUI app."""

# Import all panels to trigger registration
from .dashboard_panel import DashboardPanel
from .file_lifecycle_panel import FileLifecyclePanel
from .log_stream_panel import LogStreamPanel
from .pattern_activity_panel import PatternActivityPanel
from .tool_health_panel import ToolHealthPanel

__all__ = [
    "DashboardPanel",
    "FileLifecyclePanel",
    "ToolHealthPanel",
    "LogStreamPanel",
    "PatternActivityPanel",
]
# DOC_LINK: DOC-PAT-PANELS-INIT-469
