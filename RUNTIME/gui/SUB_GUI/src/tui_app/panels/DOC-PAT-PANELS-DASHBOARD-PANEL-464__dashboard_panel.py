# DOC_LINK: DOC-PAT-PANELS-DASHBOARD-PANEL-464
"""Dashboard panel for pipeline summary visualization."""

from datetime import datetime

from textual.widgets import Static
from tui_app.core.panel_plugin import PanelContext
from tui_app.core.panel_registry import register_panel


class DashboardWidget(Static):
    """Dashboard widget with auto-refresh capability."""

    # DOC_ID: DOC-PAT-PANELS-DASHBOARD-PANEL-464

    def __init__(self, context: PanelContext):
        super().__init__("", id="dashboard-content")
        self.context = context
        panel_cfg = getattr(context.config, "panels", None)
        self.refresh_interval = panel_cfg.dashboard if panel_cfg else 2.0  # seconds

    def on_mount(self) -> None:
        """Called when widget is mounted - start auto-refresh."""
        self._refresh_data()
        self.set_interval(self.refresh_interval, self._refresh_data)

    def _refresh_data(self) -> None:
        """Fetch and display updated dashboard data."""
        if not self.context.state_client:
            self.update("[bold red]No state client configured[/]")
            return

        # Get current time for "last updated" indicator
        last_updated = datetime.now().strftime("%H:%M:%S")

        # Get pipeline summary from state client
        summary = self.context.state_client.get_pipeline_summary()
        tasks = self.context.state_client.get_tasks(limit=5)

        # Build display text
        lines = [
            f"[bold cyan]Pipeline Status:[/] {summary.status.upper()}",
            f"[dim]Last updated: {last_updated}[/]",
            "",
            f"Total Tasks:     {summary.total_tasks}",
            f"Running:         {summary.running_tasks}",
            f"Completed:       {summary.completed_tasks}",
            f"Failed:          {summary.failed_tasks}",
            f"Active Workers:  {summary.active_workers}",
            "",
            "[bold cyan]Recent Tasks:[/]",
            "",
        ]

        for task in tasks:
            status_color = {
                "completed": "green",
                "running": "yellow",
                "failed": "red",
            }.get(task.status, "white")

            lines.append(f"[{status_color}]●[/] {task.name} ({task.status})")
            if task.error_message:
                lines.append(f"  [dim red]Error: {task.error_message}[/]")

        content = "\n".join(lines)
        self.update(content)


@register_panel("dashboard")
class DashboardPanel:
    """Main dashboard panel showing pipeline summary."""

    @property
    def panel_id(self) -> str:
        return "dashboard"

    @property
    def title(self) -> str:
        return "Pipeline Dashboard"

    def create_widget(self, context: PanelContext) -> DashboardWidget:
        """Create dashboard widget with auto-refresh."""
        return DashboardWidget(context)

    def on_mount(self, context: PanelContext) -> None:
        """Called when panel is mounted."""
        pass

    def on_unmount(self, context: PanelContext) -> None:
        """Called when panel is unmounted."""
        pass
