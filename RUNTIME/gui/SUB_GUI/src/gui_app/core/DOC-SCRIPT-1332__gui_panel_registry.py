# DOC_LINK: DOC-SCRIPT-1332
"""Panel registry for GUI app."""

from __future__ import annotations


class GuiPanelRegistry:
    """Registry for GUI panels."""

    def __init__(self):
        self._panels: dict[str, str] = {}

    def register(self, panel_id: str, title: str) -> None:
        self._panels[panel_id] = title

    def list_panels(self) -> list[str]:
        return list(self._panels.keys())

    def get_title(self, panel_id: str) -> str | None:
        return self._panels.get(panel_id)


_registry = GuiPanelRegistry()

_registry.register("dashboard", "Dashboard")
_registry.register("file_lifecycle", "File Lifecycle")
_registry.register("tool_health", "Tool Health")
_registry.register("log_stream", "Log Stream")
_registry.register("pattern_activity", "Pattern Activity")


def get_registry() -> GuiPanelRegistry:
    return _registry
