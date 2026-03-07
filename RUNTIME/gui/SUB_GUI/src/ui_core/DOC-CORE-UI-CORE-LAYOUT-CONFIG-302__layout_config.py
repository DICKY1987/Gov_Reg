# DOC_LINK: DOC-CORE-UI-CORE-LAYOUT-CONFIG-302
"""Configuration loader for UI applications (TUI and GUI).

Loads ui_config.yaml which contains shared settings for both shells.
"""

# DOC_ID: DOC-CORE-UI-CORE-LAYOUT-CONFIG-302

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class ThemePalette:
    """Color palette for UI theming."""

    surface: str
    primary: str
    accent: str
    warning: str
    danger: str
    muted: str
    text: str


@dataclass
class PanelRefreshConfig:
    """Refresh intervals for panels (in seconds)."""

    dashboard: float = 2.0
    pattern: float = 5.0
    file: float = 3.0
    tool: float = 4.0
    log: float = 3.0


@dataclass
class LogConfig:
    """Log file configuration."""

    path: str = "logs/combined.log"
    max_lines: int = 60


@dataclass
class TUISpecificConfig:
    """TUI-specific configuration."""

    theme: ThemePalette


@dataclass
class GUISpecificConfig:
    """GUI-specific configuration."""

    width: int = 1280
    height: int = 800
    remember_position: bool = True
    theme: str = "Fusion"  # Qt theme name


@dataclass
class UIConfig:
    """Unified configuration for TUI and GUI."""

    panels: PanelRefreshConfig
    logs: LogConfig
    tui: Optional[TUISpecificConfig] = None
    gui: Optional[GUISpecificConfig] = None


def load_ui_config(config_path: Optional[Path] = None) -> UIConfig:
    """Load UI configuration from YAML file.

    Args:
        config_path: Path to config file. If None, searches for:
                     - gui/src/config/ui_config.yaml (new unified config)
                     - gui/src/tui_app/config/tui_config.yaml (fallback)

    Returns:
        UIConfig instance
    """
    if config_path is None:
        # Try new unified config first
        unified_path = Path("gui/src/config/ui_config.yaml")
        if unified_path.exists():
            config_path = unified_path
        else:
            # Fallback to TUI config
            config_path = Path("gui/src/tui_app/config/tui_config.yaml")

    if not config_path.exists():
        # Return defaults
        return UIConfig(
            panels=PanelRefreshConfig(),
            logs=LogConfig(),
            tui=TUISpecificConfig(
                theme=ThemePalette(
                    surface="#0b1221",
                    primary="#1f6feb",
                    accent="#2bc48a",
                    warning="#f5a524",
                    danger="#ff6b6b",
                    muted="#94a3b8",
                    text="#dfe7f5",
                )
            ),
            gui=GUISpecificConfig(),
        )

    with open(config_path, "r") as f:
        data = yaml.safe_load(f)

    # Parse panel refresh config
    panel_data = data.get("panels", {})
    panels = PanelRefreshConfig(
        dashboard=panel_data.get("dashboard_refresh_seconds", 2.0),
        pattern=panel_data.get("pattern_refresh_seconds", 5.0),
        file=panel_data.get("file_refresh_seconds", 3.0),
        tool=panel_data.get("tool_refresh_seconds", 4.0),
        log=panel_data.get("log_refresh_seconds", 3.0),
    )

    # Parse log config
    log_data = data.get("logs", {})
    logs = LogConfig(
        path=log_data.get("path", "logs/combined.log"),
        max_lines=log_data.get("max_lines", 60),
    )

    # Parse TUI-specific config (if present)
    tui = None
    if "tui" in data:
        tui_data = data["tui"]
        theme_data = tui_data.get("theme", {})
        tui = TUISpecificConfig(
            theme=(
                ThemePalette(**theme_data)
                if theme_data
                else ThemePalette(
                    surface="#0b1221",
                    primary="#1f6feb",
                    accent="#2bc48a",
                    warning="#f5a524",
                    danger="#ff6b6b",
                    muted="#94a3b8",
                    text="#dfe7f5",
                )
            )
        )
    elif "theme" in data:
        # Old TUI config format (backward compatibility)
        theme_data = data.get("theme", {})
        tui = TUISpecificConfig(theme=ThemePalette(**theme_data))

    # Parse GUI-specific config (if present)
    gui = None
    if "gui" in data:
        gui_data = data["gui"]
        window_data = gui_data.get("window", {})
        gui = GUISpecificConfig(
            width=window_data.get("width", 1280),
            height=window_data.get("height", 800),
            remember_position=window_data.get("remember_position", True),
            theme=gui_data.get("theme", "Fusion"),
        )

    return UIConfig(panels=panels, logs=logs, tui=tui, gui=gui)


# Backward compatibility alias
TUIConfig = UIConfig
load_tui_config = load_ui_config
