# DOC_LINK: DOC-TEST-TUI-PANEL-FRAMEWORK-TEST-PANELS-SMOKE-156
"""Smoke tests for panel creation."""

import pytest

# Import panels to trigger registration
from tui_app.core.panel_plugin import PanelContext
from tui_app.core.panel_registry import get_registry
from tui_app.core.pattern_client import InMemoryPatternStateStore, PatternClient
from tui_app.core.state_client import InMemoryStateBackend, StateClient


@pytest.fixture
def panel_context():
    """Create a panel context for testing."""
    # DOC_ID: DOC-TEST-TUI-PANEL-FRAMEWORK-TEST-PANELS-SMOKE-156
    state_client = StateClient(InMemoryStateBackend())
    pattern_client = PatternClient(InMemoryPatternStateStore())

    return PanelContext(
        panel_id="test", state_client=state_client, pattern_client=pattern_client
    )


def test_dashboard_panel_creation(panel_context):
    """Test creating dashboard panel."""
    registry = get_registry()
    panel = registry.create_panel("dashboard")

    assert panel is not None
    assert panel.panel_id == "dashboard"

    widget = panel.create_widget(panel_context)
    assert widget is not None


def test_file_lifecycle_panel_creation(panel_context):
    """Test creating file lifecycle panel."""
    registry = get_registry()
    panel = registry.create_panel("file_lifecycle")

    assert panel is not None
    assert panel.panel_id == "file_lifecycle"

    widget = panel.create_widget(panel_context)
    assert widget is not None


def test_tool_health_panel_creation(panel_context):
    """Test creating tool health panel."""
    registry = get_registry()
    panel = registry.create_panel("tool_health")

    assert panel is not None
    assert panel.panel_id == "tool_health"

    widget = panel.create_widget(panel_context)
    assert widget is not None


def test_log_stream_panel_creation(panel_context):
    """Test creating log stream panel."""
    registry = get_registry()
    panel = registry.create_panel("log_stream")

    assert panel is not None
    assert panel.panel_id == "log_stream"

    widget = panel.create_widget(panel_context)
    assert widget is not None


def test_pattern_activity_panel_creation(panel_context):
    """Test creating pattern activity panel."""
    registry = get_registry()
    panel = registry.create_panel("pattern_activity")

    assert panel is not None
    assert panel.panel_id == "pattern_activity"

    widget = panel.create_widget(panel_context)
    assert widget is not None


def test_all_panels_registered():
    """Test that all expected panels are registered."""
    registry = get_registry()
    panel_ids = registry.list_panels()

    expected_panels = [
        "dashboard",
        "file_lifecycle",
        "tool_health",
        "log_stream",
        "pattern_activity",
    ]

    for panel_id in expected_panels:
        assert panel_id in panel_ids, f"Panel {panel_id} not registered"
