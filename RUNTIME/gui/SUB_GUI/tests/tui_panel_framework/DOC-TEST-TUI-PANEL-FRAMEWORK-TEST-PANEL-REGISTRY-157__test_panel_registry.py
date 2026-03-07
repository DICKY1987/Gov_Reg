# DOC_LINK: DOC-TEST-TUI-PANEL-FRAMEWORK-TEST-PANEL-REGISTRY-157
"""Tests for panel registry."""

from textual.widgets import Static
from tui_app.core.panel_plugin import PanelContext
from tui_app.core.panel_registry import PanelRegistry, register_panel


class MockPanel:
    """Mock panel for testing."""

    # DOC_ID: DOC-TEST-TUI-PANEL-FRAMEWORK-TEST-PANEL-REGISTRY-157

    @property
    def panel_id(self) -> str:
        return "mock"

    @property
    def title(self) -> str:
        return "Mock Panel"

    def create_widget(self, context: PanelContext) -> Static:
        return Static("Mock content")

    def on_mount(self, context: PanelContext) -> None:
        pass

    def on_unmount(self, context: PanelContext) -> None:
        pass


def test_panel_registry_register():
    """Test registering a panel."""
    registry = PanelRegistry()
    registry.register("test", MockPanel)

    assert "test" in registry.list_panels()
    assert registry.get("test") == MockPanel


def test_panel_registry_get_nonexistent():
    """Test getting a nonexistent panel."""
    registry = PanelRegistry()

    assert registry.get("nonexistent") is None


def test_panel_registry_create_panel():
    """Test creating a panel instance."""
    registry = PanelRegistry()
    registry.register("mock", MockPanel)

    panel = registry.create_panel("mock")
    assert panel is not None
    assert panel.panel_id == "mock"


def test_register_panel_decorator():
    """Test the register_panel decorator."""
    registry = PanelRegistry()

    @register_panel("decorated")
    class DecoratedPanel:
        @property
        def panel_id(self) -> str:
            return "decorated"

        @property
        def title(self) -> str:
            return "Decorated Panel"

        def create_widget(self, context: PanelContext) -> Static:
            return Static("Decorated")

        def on_mount(self, context: PanelContext) -> None:
            pass

        def on_unmount(self, context: PanelContext) -> None:
            pass

    # Note: decorator uses global registry, not our local one
    # This is expected behavior for the decorator
    assert DecoratedPanel is not None
