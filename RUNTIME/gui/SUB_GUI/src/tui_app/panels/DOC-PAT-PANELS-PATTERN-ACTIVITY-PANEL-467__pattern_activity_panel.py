# DOC_LINK: DOC-PAT-PANELS-PATTERN-ACTIVITY-PANEL-467
"""Pattern activity panel for visualizing pattern execution."""

from datetime import datetime

from textual.widgets import Static
from tui_app.core.panel_plugin import PanelContext
from tui_app.core.panel_registry import register_panel


class PatternActivityWidget(Static):
    """Pattern activity widget with auto-refresh capability."""

    # DOC_ID: DOC-PAT-PANELS-PATTERN-ACTIVITY-PANEL-467

    def __init__(self, context: PanelContext):
        super().__init__("", id="pattern-activity-content")
        self.context = context
        panel_cfg = getattr(context.config, "panels", None)
        self.refresh_interval = (
            panel_cfg.pattern_activity if panel_cfg else 5.0
        )  # seconds

    def on_mount(self) -> None:
        """Called when widget is mounted - start auto-refresh."""
        self._refresh_data()
        self.set_interval(self.refresh_interval, self._refresh_data)

    def _refresh_data(self) -> None:
        """Fetch and display updated pattern activity data."""
        if not self.context.pattern_client:
            self.update("[bold red]No pattern client configured[/]")
            return

        # Get current time for "last updated" indicator
        last_updated = datetime.now().strftime("%H:%M:%S")

        runs = self.context.pattern_client.get_recent_runs(limit=10)

        # Build timeline view
        timeline_lines = [
            "[bold cyan]Pattern Runs:[/]",
            f"[dim]Last updated: {last_updated}[/]",
            "",
        ]
        for run in runs:
            status_symbol = {
                "completed": "[green]✓[/]",
                "running": "[yellow]⟳[/]",
                "failed": "[red]✗[/]",
                "pending": "[dim]○[/]",
                "cancelled": "[dim]✗[/]",
            }.get(run.status.value, "○")

            timeline_lines.append(f"{status_symbol} {run.pattern_name}")
            timeline_lines.append(
                f"   [dim]{run.run_id}[/] - Progress: {int(run.progress * 100)}%"
            )
            if run.current_phase:
                timeline_lines.append(f"   [dim cyan]Phase: {run.current_phase}[/]")
            if run.error_message:
                timeline_lines.append(f"   [dim red]Error: {run.error_message}[/]")
            timeline_lines.append("")

        # Build detail view for first run
        detail_lines = ["[bold cyan]Event Details:[/]", ""]
        if runs:
            first_run = runs[0]
            events = self.context.pattern_client.get_run_events(first_run.run_id)

            detail_lines.append(f"[bold]{first_run.pattern_name}[/]")
            detail_lines.append(f"Run ID: {first_run.run_id}")
            detail_lines.append("")
            detail_lines.append("[bold cyan]Events:[/]")
            detail_lines.append("")

            for event in events:
                event_symbol = {
                    "started": "▶",
                    "phase_started": "▷",
                    "phase_completed": "✓",
                    "validation_passed": "✓",
                    "validation_failed": "✗",
                    "executed": "●",
                    "completed": "✓",
                    "failed": "✗",
                }.get(event.event_type.value, "●")

                detail_lines.append(f"{event_symbol} {event.message}")
                if event.phase:
                    detail_lines.append(f"  [dim]Phase: {event.phase}[/]")

        # Combine views side-by-side (simplified text layout)
        content = "\n".join(timeline_lines)
        content += "\n\n" + "─" * 60 + "\n\n"
        content += "\n".join(detail_lines)

        self.update(content)


@register_panel("pattern_activity")
class PatternActivityPanel:
    """Panel showing pattern execution timeline and event details.

    Displays:
    - Timeline view (left): List of pattern runs
    - Detail view (right): Events for selected run
    """

    @property
    def panel_id(self) -> str:
        return "pattern_activity"

    @property
    def title(self) -> str:
        return "Pattern Activity"

    def create_widget(self, context: PanelContext) -> PatternActivityWidget:
        """Create pattern activity widget with auto-refresh."""
        return PatternActivityWidget(context)

    def on_mount(self, context: PanelContext) -> None:
        """Called when panel is mounted."""
        pass

    def on_unmount(self, context: PanelContext) -> None:
        """Called when panel is unmounted."""
        pass
