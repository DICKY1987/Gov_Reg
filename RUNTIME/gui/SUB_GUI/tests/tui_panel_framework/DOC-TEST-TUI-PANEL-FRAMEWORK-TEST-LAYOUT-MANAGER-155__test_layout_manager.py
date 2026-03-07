# DOC_LINK: DOC-TEST-TUI-PANEL-FRAMEWORK-TEST-LAYOUT-MANAGER-155
"""Tests for layout manager."""

from textual.widgets import Static
from tui_app.core.layout_manager import BasicLayoutManager
from tui_app.core.panel_plugin import PanelContext


class MockPanel:
    """Mock panel for testing."""

    # DOC_ID: DOC-TEST-TUI-PANEL-FRAMEWORK-TEST-LAYOUT-MANAGER-155

    def __init__(self):
        self.mounted = False
        self.unmounted = False

    @property
    def panel_id(self) -> str:
        return "mock"

    @property
    def title(self) -> str:
        return "Mock Panel"

    def create_widget(self, context: PanelContext) -> Static:
        return Static("Mock content")

    def on_mount(self, context: PanelContext) -> None:
        self.mounted = True

    def on_unmount(self, context: PanelContext) -> None:
        self.unmounted = True


def test_basic_layout_manager_mount_panel():
    """Test mounting a panel."""
    manager = BasicLayoutManager()
    panel = MockPanel()
    context = PanelContext(panel_id="mock")

    widget = manager.mount_panel(panel, context)

    assert widget is not None
    assert panel.mounted is True
    assert manager.get_current_panel() == panel


def test_basic_layout_manager_unmount_current():
    """Test unmounting current panel."""
    manager = BasicLayoutManager()
    panel = MockPanel()
    context = PanelContext(panel_id="mock")

    manager.mount_panel(panel, context)
    manager.unmount_current()

    assert panel.unmounted is True
    assert manager.get_current_panel() is None


def test_basic_layout_manager_remount():
    """Test remounting a new panel (should unmount previous)."""
    manager = BasicLayoutManager()

    panel1 = MockPanel()
    context1 = PanelContext(panel_id="mock1")
    manager.mount_panel(panel1, context1)

    panel2 = MockPanel()
    context2 = PanelContext(panel_id="mock2")
    manager.mount_panel(panel2, context2)

    assert panel1.unmounted is True
    assert panel2.mounted is True
    assert manager.get_current_panel() == panel2
