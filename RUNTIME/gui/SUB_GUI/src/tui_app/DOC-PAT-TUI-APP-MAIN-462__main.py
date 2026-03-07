# DOC_LINK: DOC-PAT-TUI-APP-MAIN-462
"""TUI Application Main Entry Point.

Textual-based terminal UI for AI Development Pipeline monitoring and control.
"""

# DOC_ID: DOC-PAT-TUI-APP-MAIN-462

import argparse
import sys
from typing import Optional

# Import panels to trigger registration
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Footer, Header
from tui_app.config.layout_config import TUIConfig, load_tui_config
from tui_app.core.layout_manager import BasicLayoutManager
from tui_app.core.panel_plugin import PanelContext
from tui_app.core.panel_registry import get_registry
from tui_app.core.pattern_client import (
    InMemoryPatternStateStore,
    PatternClient,
    SQLitePatternStateStore,
)
from tui_app.core.sqlite_state_backend import SQLiteStateBackend
from tui_app.core.state_client import InMemoryStateBackend, StateClient


class PipelineTUI(App):
    """Main TUI application for pipeline monitoring."""

    CSS = ""

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
        ("d", "switch_dashboard", "Dashboard"),
        ("f", "switch_file_lifecycle", "Files"),
        ("t", "switch_tool_health", "Tools"),
        ("l", "switch_log_stream", "Logs"),
        ("p", "switch_pattern_activity", "Patterns"),
    ]

    def __init__(
        self,
        panel_id: str = "dashboard",
        smoke_test: bool = False,
        use_mock_data: bool = False,
        config: Optional[TUIConfig] = None,
        layout: str = "single",
        secondary_panel: Optional[str] = None,
    ):
        super().__init__()
        self.panel_id = panel_id
        self.smoke_test = smoke_test
        self.tui_config: TUIConfig = config or load_tui_config()
        self._css = self._build_css()
        self.layout_mode = layout
        self.secondary_panel = secondary_panel if layout == "dual" else None

        # Initialize clients (use SQLite by default, InMemory for testing)
        if use_mock_data:
            self.state_client = StateClient(InMemoryStateBackend())
            self.pattern_client = PatternClient(InMemoryPatternStateStore())
        else:
            state_backend = SQLiteStateBackend()
            self.state_client = StateClient(state_backend)
            self.pattern_client = PatternClient(
                SQLitePatternStateStore(db_path=state_backend.db_path)
            )

        # Initialize layout manager
        self.layout_manager = BasicLayoutManager()

        # Get panel registry
        self.registry = get_registry()

    def compose(self) -> ComposeResult:
        """Compose the UI layout."""
        yield Header(show_clock=True)
        yield Container(id="panel-container")
        yield Footer()

    def _build_css(self) -> str:
        """Generate CSS based on the current theme configuration."""
        palette = self.tui_config.theme
        # Note: Textual CSS doesn't support CSS variables (:root, var())
        # We substitute the palette values directly into the CSS
        return f"""
        Screen {{
            background: {palette.surface};
            color: {palette.text};
        }}

        #panel-container {{
            height: 100%;
            border: solid {palette.primary};
            padding: 1;
        }}

        Header, Footer {{
            background: {palette.primary};
            color: {palette.text};
        }}

        .card {{
            background: {palette.surface};
            border: solid {palette.muted};
            padding: 1;
        }}

        .accent {{
            color: {palette.accent};
        }}

        .warning {{
            color: {palette.warning};
        }}

        .danger {{
            color: {palette.danger};
        }}

        #dual-container {{
            height: 100%;
        }}

        #dual-container > * {{
            width: 1fr;
            height: 100%;
            border: solid {palette.muted};
            padding: 1;
        }}
        """

    def on_mount(self) -> None:
        """Called when app is mounted."""
        if self._css:
            self.stylesheet.add_source(self._css)
        self.title = "AI Pipeline TUI"
        self.sub_title = "Monitoring & Control"

        # Mount initial panel
        self._mount_panel(self.panel_id)

        # If smoke test, exit immediately
        if self.smoke_test:
            self.exit(0)

    def _mount_panel(self, panel_id: str) -> None:
        """Mount a panel by ID."""
        self.panel_id = panel_id
        panel = self.registry.create_panel(panel_id)
        if not panel:
            # Fallback to dashboard
            panel = self.registry.create_panel("dashboard")
            if not panel:
                self.exit(1, f"Failed to create panel: {panel_id}")
                return

        # Create context
        context = PanelContext(
            panel_id=panel_id,
            state_client=self.state_client,
            pattern_client=self.pattern_client,
            config=self.tui_config,
        )

        # Mount panel
        widget = self.layout_manager.mount_panel(panel, context)

        content = widget
        if self.secondary_panel:
            secondary = self.registry.create_panel(self.secondary_panel)
            if secondary:
                secondary_context = PanelContext(
                    panel_id=self.secondary_panel,
                    state_client=self.state_client,
                    pattern_client=self.pattern_client,
                    config=self.tui_config,
                )
                secondary_widget = BasicLayoutManager().mount_panel(
                    secondary, secondary_context
                )
                content = Horizontal(widget, secondary_widget, id="dual-container")

        # Update container
        container = self.query_one("#panel-container", Container)
        container.remove_children()
        container.mount(content)

        # Update subtitle
        self.sub_title = panel.title

    def action_switch_dashboard(self) -> None:
        """Switch to dashboard panel."""
        self._mount_panel("dashboard")

    def action_switch_file_lifecycle(self) -> None:
        """Switch to file lifecycle panel."""
        self._mount_panel("file_lifecycle")

    def action_switch_tool_health(self) -> None:
        """Switch to tool health panel."""
        self._mount_panel("tool_health")

    def action_switch_log_stream(self) -> None:
        """Switch to log stream panel."""
        self._mount_panel("log_stream")

    def action_switch_pattern_activity(self) -> None:
        """Switch to pattern activity panel."""
        self._mount_panel("pattern_activity")

    def action_refresh(self) -> None:
        """Force immediate refresh of current panel."""
        # Remount the current panel to trigger refresh
        self._mount_panel(self.panel_id)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="AI Pipeline TUI")
    parser.add_argument(
        "--panel",
        default="dashboard",
        choices=[
            "dashboard",
            "file_lifecycle",
            "tool_health",
            "log_stream",
            "pattern_activity",
        ],
        help="Initial panel to display",
    )
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Run smoke test (launch and exit immediately)",
    )
    parser.add_argument(
        "--use-mock-data",
        action="store_true",
        help="Use mock in-memory data instead of SQLite database",
    )
    parser.add_argument(
        "--layout",
        choices=["single", "dual"],
        default="single",
        help="Layout mode (single panel or dual split view)",
    )
    parser.add_argument(
        "--secondary-panel",
        choices=[
            "dashboard",
            "file_lifecycle",
            "tool_health",
            "log_stream",
            "pattern_activity",
        ],
        default=None,
        help="Secondary panel to show in dual layout",
    )

    args = parser.parse_args()

    app = PipelineTUI(
        panel_id=args.panel,
        smoke_test=args.smoke_test,
        use_mock_data=args.use_mock_data,
        layout=args.layout,
        secondary_panel=args.secondary_panel,
    )

    try:
        app.run()
    except Exception as e:
        print(f"Error running TUI: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
