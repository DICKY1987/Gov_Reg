# DOC_LINK: DOC-GUI-TESTS-SMOKE-500
"""Smoke tests for GUI application.

Verifies that GUI can be instantiated without crashing.
"""

# DOC_ID: DOC-GUI-TESTS-SMOKE-500

import sys

import pytest
from gui_app.core.gui_app import GuiApp
from ui_core.pattern_client import InMemoryPatternStateStore, PatternClient
from ui_core.state_client import InMemoryStateBackend, StateClient


@pytest.fixture(scope="session")
def qt_app():
    """Create Qt application instance for tests."""
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


def test_gui_app_instantiates(qt_app):
    """GUI app can be created without crashing."""
    state = StateClient(InMemoryStateBackend())
    window = GuiApp(state_client=state)

    assert window.windowTitle() == "AI Pipeline Monitor"
    assert window.tab_widget.count() == 5  # 5 panels


def test_gui_app_with_all_clients(qt_app):
    """GUI app works with both state and pattern clients."""
    state = StateClient(InMemoryStateBackend())
    pattern = PatternClient(InMemoryPatternStateStore())

    window = GuiApp(
        state_client=state,
        pattern_client=pattern,
    )

    assert window.state_client is not None
    assert window.pattern_client is not None


def test_gui_panel_switching(qt_app):
    """GUI can switch between panels."""
    state = StateClient(InMemoryStateBackend())
    window = GuiApp(state_client=state, initial_panel="dashboard")

    # Should start on dashboard (index 0)
    assert window.tab_widget.currentIndex() == 0

    # Switch to pattern activity (index 4)
    window._switch_to_panel("pattern_activity")
    assert window.tab_widget.currentIndex() == 4


def test_gui_panels_registered(qt_app):
    """All 5 panels are registered."""
    from gui_app.core.gui_panel_registry import get_registry

    registry = get_registry()
    panels = registry.list_panels()

    expected = [
        "dashboard",
        "file_lifecycle",
        "tool_health",
        "log_stream",
        "pattern_activity",
    ]

    for panel_id in expected:
        assert panel_id in panels, f"Panel {panel_id} not registered"
