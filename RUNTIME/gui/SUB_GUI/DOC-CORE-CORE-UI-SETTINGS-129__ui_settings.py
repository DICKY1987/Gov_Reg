# DOC_LINK: DOC-CORE-CORE-UI-SETTINGS-129
"""UI Settings Manager

Manages UI startup settings, including which tools run in interactive vs headless mode.
Allows changing the interactive tool selection at runtime.

Usage:
    from core.ui_settings import UISettingsManager

    settings = UISettingsManager()

    # Get the current interactive tool
    interactive_tool = settings.get_interactive_tool()

    # Change the interactive tool
    settings.set_interactive_tool("aider")

    # Check if a tool should run in headless mode
    is_headless = settings.is_headless("codex")
"""

# DOC_ID: DOC-CORE-CORE-UI-SETTINGS-129

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


class UISettingsManager:
    """Manages UI settings and tool execution modes."""

    DEFAULT_CONFIG_PATH = "config/ui_settings.yaml"

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize settings manager.

        Args:
            config_path: Optional path to config file. If not provided,
                        uses DEFAULT_CONFIG_PATH relative to repo root.
        """
        self.config_path = config_path or self._get_default_config_path()
        self._settings: Dict[str, Any] = {}
        self._load_settings()

    def _get_default_config_path(self) -> Path:
        """Get the default config path relative to repo root."""
        # Try to find repo root
        current = Path(__file__).resolve()
        while current != current.parent:
            if (current / ".git").exists() or (current / "config").exists():
                return current / self.DEFAULT_CONFIG_PATH
            current = current.parent

        # Fallback to relative path from this file
        return Path(__file__).parent.parent / self.DEFAULT_CONFIG_PATH

    def _load_settings(self) -> None:
        """Load settings from YAML file."""
        if not Path(self.config_path).exists():
            # Use default settings if file doesn't exist
            self._settings = self._get_default_settings()
            return

        with open(self.config_path, "r", encoding="utf-8") as f:
            self._settings = yaml.safe_load(f)

    def _get_default_settings(self) -> Dict[str, Any]:
        """Get default settings if config file doesn't exist."""
        return {
            "default_interactive_tool": "aim",
            "available_interactive_tools": ["aim", "aider", "codex", "core.ui_cli"],
            "tool_modes": {
                "aim": {
                    "default_mode": "interactive",
                    "supports_headless": True,
                    "description": "AIM+ Unified CLI",
                }
            },
            "startup": {
                "auto_launch_interactive": True,
                "auto_launch_headless": [],
                "interactive_tool_layout": "main_terminal",
            },
        }

    def save_settings(self) -> None:
        """Save current settings to YAML file."""
        config_dir = Path(self.config_path).parent
        config_dir.mkdir(parents=True, exist_ok=True)

        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.dump(self._settings, f, default_flow_style=False, sort_keys=False)

    def get_interactive_tool(self) -> str:
        """
        Get the currently configured interactive tool.

        Returns:
            Name of the interactive tool (e.g., 'aim', 'aider')
        """
        return self._settings.get("default_interactive_tool", "aim")

    def set_interactive_tool(self, tool_name: str) -> bool:
        """
        Set the interactive tool and update configuration.

        Args:
            tool_name: Name of the tool to make interactive

        Returns:
            True if successful, False if tool is not available
        """
        available = self.get_available_interactive_tools()
        if tool_name not in available:
            return False

        self._settings["default_interactive_tool"] = tool_name
        self.save_settings()
        return True

    def get_available_interactive_tools(self) -> List[str]:
        """
        Get list of tools that can run in interactive mode.

        Returns:
            List of tool names
        """
        return self._settings.get("available_interactive_tools", ["aim"])

    def is_headless(self, tool_name: str) -> bool:
        """
        Check if a tool should run in headless mode.

        A tool runs headless if:
        - It's not the current interactive tool, AND
        - It supports headless mode

        Args:
            tool_name: Name of the tool to check

        Returns:
            True if tool should run headless, False if interactive
        """
        interactive_tool = self.get_interactive_tool()

        # If this is the interactive tool, it's not headless
        if tool_name == interactive_tool:
            return False

        # Check if tool supports headless mode
        tool_modes = self._settings.get("tool_modes", {})
        tool_config = tool_modes.get(tool_name, {})

        # Default to headless if not specified
        return tool_config.get("supports_headless", True)

    def get_tool_mode(self, tool_name: str) -> str:
        """
        Get the execution mode for a tool.

        Args:
            tool_name: Name of the tool

        Returns:
            'interactive' or 'headless'
        """
        return "interactive" if not self.is_headless(tool_name) else "headless"

    def get_tool_config(self, tool_name: str) -> Dict[str, Any]:
        """
        Get full configuration for a tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Dictionary with tool configuration
        """
        tool_modes = self._settings.get("tool_modes", {})
        return tool_modes.get(tool_name, {})

    def get_startup_config(self) -> Dict[str, Any]:
        """
        Get UI startup configuration.

        Returns:
            Dictionary with startup settings
        """
        return self._settings.get(
            "startup",
            {
                "auto_launch_interactive": True,
                "auto_launch_headless": [],
                "interactive_tool_layout": "main_terminal",
            },
        )

    def should_auto_launch_interactive(self) -> bool:
        """
        Check if interactive tool should auto-launch at startup.

        Returns:
            True if should auto-launch
        """
        startup = self.get_startup_config()
        return startup.get("auto_launch_interactive", True)

    def get_auto_launch_headless_tools(self) -> List[str]:
        """
        Get list of tools to auto-launch in headless mode.

        Returns:
            List of tool names
        """
        startup = self.get_startup_config()
        return startup.get("auto_launch_headless", [])

    def get_interactive_layout(self) -> str:
        """
        Get the preferred layout for the interactive tool.

        Returns:
            Layout name (e.g., 'main_terminal', 'side_panel', 'popup')
        """
        startup = self.get_startup_config()
        return startup.get("interactive_tool_layout", "main_terminal")

    def list_all_tools(self) -> Dict[str, Dict[str, Any]]:
        """
        Get configuration for all tools.

        Returns:
            Dictionary mapping tool names to their configurations
        """
        return self._settings.get("tool_modes", {})

    def get_settings_summary(self) -> Dict[str, Any]:
        """
        Get a summary of current settings for display.

        Returns:
            Dictionary with key settings
        """
        return {
            "interactive_tool": self.get_interactive_tool(),
            "interactive_mode": self.get_tool_mode(self.get_interactive_tool()),
            "available_interactive_tools": self.get_available_interactive_tools(),
            "auto_launch_interactive": self.should_auto_launch_interactive(),
            "auto_launch_headless": self.get_auto_launch_headless_tools(),
            "interactive_layout": self.get_interactive_layout(),
        }


# Singleton instance for convenience
_settings_instance: Optional[UISettingsManager] = None


def get_settings_manager() -> UISettingsManager:
    """
    Get singleton instance of UISettingsManager.

    Returns:
        UISettingsManager instance
    """
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = UISettingsManager()
    return _settings_instance
