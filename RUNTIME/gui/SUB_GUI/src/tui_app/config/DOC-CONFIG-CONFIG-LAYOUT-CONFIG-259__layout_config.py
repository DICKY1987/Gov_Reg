# DOC_LINK: DOC-CONFIG-CONFIG-LAYOUT-CONFIG-259
"""Layout and theme configuration for the TUI app."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class LayoutConfig:
    """Configuration for TUI layout."""

    # DOC_ID: DOC-CONFIG-CONFIG-LAYOUT-CONFIG-259
    default_panel: str = "dashboard"
    theme: str = "dark"
    refresh_interval: int = 1000  # milliseconds


@dataclass
class PanelConfig:
    """Configuration for individual panels."""

    panel_id: str
    enabled: bool = True
    auto_refresh: bool = True
    refresh_interval: Optional[int] = None  # Override global refresh


@dataclass
class ThemeConfig:
    """Color palette for the TUI."""

    surface: str = "#0b1221"
    primary: str = "#1f6feb"
    accent: str = "#2bc48a"
    warning: str = "#f5a524"
    danger: str = "#ff6b6b"
    muted: str = "#94a3b8"
    text: str = "#dfe7f5"


@dataclass
class PanelRefreshConfig:
    """Per-panel refresh intervals in seconds."""

    dashboard: float = 2.0
    pattern_activity: float = 5.0
    file_lifecycle: float = 3.0
    tool_health: float = 4.0
    log_stream: float = 3.0

    def interval_for(self, panel_id: str, default: float) -> float:
        """Return interval for a panel with a fallback."""
        return getattr(self, panel_id, default)


@dataclass
class LogConfig:
    """Log configuration for the log stream panel."""

    path: Path = Path("logs/combined.log")
    max_lines: int = 60


@dataclass
class TUIConfig:
    """Top-level TUI configuration loaded from YAML."""

    theme: ThemeConfig
    panels: PanelRefreshConfig
    logs: LogConfig


DEFAULT_CONFIG_PATH = Path("tui_app/config/tui_config.yaml")


def load_tui_config(path: Path = DEFAULT_CONFIG_PATH) -> TUIConfig:
    """Load TUI configuration from YAML with safe defaults."""
    config_data: dict = {}
    if path.exists():
        with path.open("r", encoding="utf-8") as handle:
            config_data = yaml.safe_load(handle) or {}

    theme_data = config_data.get("theme", {}) or {}
    panel_data = config_data.get("panels", {}) or {}
    log_data = config_data.get("logs", {}) or {}

    theme = ThemeConfig(
        surface=theme_data.get("surface", ThemeConfig.surface),
        primary=theme_data.get("primary", ThemeConfig.primary),
        accent=theme_data.get("accent", ThemeConfig.accent),
        warning=theme_data.get("warning", ThemeConfig.warning),
        danger=theme_data.get("danger", ThemeConfig.danger),
        muted=theme_data.get("muted", ThemeConfig.muted),
        text=theme_data.get("text", ThemeConfig.text),
    )

    panels = PanelRefreshConfig(
        dashboard=float(
            panel_data.get("dashboard_refresh_seconds", PanelRefreshConfig.dashboard)
        ),
        pattern_activity=float(
            panel_data.get(
                "pattern_refresh_seconds", PanelRefreshConfig.pattern_activity
            )
        ),
        file_lifecycle=float(
            panel_data.get("file_refresh_seconds", PanelRefreshConfig.file_lifecycle)
        ),
        tool_health=float(
            panel_data.get("tool_refresh_seconds", PanelRefreshConfig.tool_health)
        ),
        log_stream=float(
            panel_data.get("log_refresh_seconds", PanelRefreshConfig.log_stream)
        ),
    )

    logs = LogConfig(
        path=Path(log_data.get("path", LogConfig.path)),
        max_lines=int(log_data.get("max_lines", LogConfig.max_lines)),
    )

    return TUIConfig(theme=theme, panels=panels, logs=logs)
