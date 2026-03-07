# DOC_LINK: DOC-SCRIPT-1331
"""Minimal GUI app implementation for tests."""

from __future__ import annotations

from .gui_panel_registry import get_registry


class GuiApp:
    """GUI application shell for pipeline monitoring."""

    def __init__(
        self,
        state_client,
        pattern_client=None,
        initial_panel: str = "dashboard",
    ):
        from PySide6.QtWidgets import QMainWindow, QTabWidget, QWidget

        self._window = QMainWindow()
        self._window.setWindowTitle("AI Pipeline Monitor")

        self.state_client = state_client
        self.pattern_client = pattern_client

        self.tab_widget = QTabWidget()
        self._panel_order: list[str] = []

        registry = get_registry()
        for panel_id in registry.list_panels():
            title = registry.get_title(panel_id) or panel_id
            self.tab_widget.addTab(QWidget(), title)
            self._panel_order.append(panel_id)

        self._window.setCentralWidget(self.tab_widget)
        self._switch_to_panel(initial_panel)

    def __getattr__(self, name: str):
        return getattr(self._window, name)

    def _switch_to_panel(self, panel_id: str) -> None:
        """Switch active tab to the panel with the given ID."""
        if panel_id not in self._panel_order:
            return
        index = self._panel_order.index(panel_id)
        self.tab_widget.setCurrentIndex(index)
