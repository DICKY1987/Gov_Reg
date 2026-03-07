# DOC_LINK: DOC-PAT-PANELS-FILE-LIFECYCLE-PANEL-465
"""File lifecycle panel for tracking file changes through the pipeline."""

from datetime import datetime
from typing import Iterable

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import DataTable, Static
from tui_app.core.panel_plugin import PanelContext
from tui_app.core.panel_registry import register_panel


class FileLifecycleWidget(Vertical):
    """Displays patch ledger entries with auto-refresh."""

    # DOC_ID: DOC-PAT-PANELS-FILE-LIFECYCLE-PANEL-465

    def __init__(self, context: PanelContext):
        super().__init__(id="file-lifecycle-root")
        self.context = context
        panel_cfg = getattr(context.config, "panels", None)
        self.refresh_interval = panel_cfg.file_lifecycle if panel_cfg else 3.0
        self.summary = Static("", classes="card", id="file-lifecycle-summary")
        self.table = DataTable(id="file-lifecycle-table", zebra_stripes=True)

    def compose(self) -> ComposeResult:
        yield self.summary
        yield self.table

    def on_mount(self) -> None:
        """Initialize table and kick off refresh."""
        self.table.cursor_type = "row"
        self.table.add_columns("Patch", "Execution", "State", "Created", "Files")
        self._refresh()
        self.set_interval(self.refresh_interval, self._refresh)

    def _refresh(self) -> None:
        """Refresh patch ledger view."""
        client = self.context.state_client
        self.table.clear()

        if not client:
            self.summary.update("[red]No state client configured[/]")
            self.table.add_row("n/a", "n/a", "n/a", "-", "-")
            return

        patches = client.get_patch_ledger(limit=25)
        executions = client.get_executions(limit=10)

        if not patches:
            self.summary.update("[yellow]No patches recorded yet[/]")
            self.table.add_row("No patches", "-", "-", "-", "-")
            return

        validated = sum(1 for p in patches if (p.state or "").lower() == "validated")
        pending = sum(1 for p in patches if (p.state or "").lower() == "pending")
        failed = sum(1 for p in patches if (p.state or "").lower() == "failed")
        running_execs = sum(
            1 for e in executions if (e.status or "").lower() == "running"
        )

        summary_lines = [
            f"[bold cyan]Patches:[/] {len(patches)}  "
            f"[green]Validated[/]: {validated}  "
            f"[yellow]Pending[/]: {pending}  "
            f"[red]Failed[/]: {failed}",
            f"[dim]Executions[/]: {len(executions)} (running: {running_execs})",
        ]
        self.summary.update("\n".join(summary_lines))

        for patch in patches:
            state_lower = (patch.state or "").lower()
            state_style = {
                "validated": "green",
                "pending": "yellow",
                "failed": "red",
            }.get(state_lower, "cyan")
            state_cell = Text(
                patch.state.title() if patch.state else "unknown", style=state_style
            )

            created = self._format_datetime(patch.created_at)
            files = self._format_files(patch.files)

            self.table.add_row(
                patch.patch_id,
                patch.execution_id or "-",
                state_cell,
                created,
                files,
            )

    @staticmethod
    def _format_datetime(value: datetime | None) -> str:
        return value.strftime("%Y-%m-%d %H:%M:%S") if value else "-"

    @staticmethod
    def _format_files(files: Iterable[str]) -> str:
        file_list = list(files or [])
        if not file_list:
            return "(unknown)"
        if len(file_list) > 3:
            return ", ".join(file_list[:3]) + " ..."
        return ", ".join(file_list)


@register_panel("file_lifecycle")
class FileLifecyclePanel:
    """Panel showing file lifecycle and patch ledger."""

    @property
    def panel_id(self) -> str:
        return "file_lifecycle"

    @property
    def title(self) -> str:
        return "File Lifecycle"

    def create_widget(self, context: PanelContext) -> FileLifecycleWidget:
        """Create file lifecycle widget."""
        return FileLifecycleWidget(context)

    def on_mount(self, context: PanelContext) -> None:
        """Called when panel is mounted."""
        pass

    def on_unmount(self, context: PanelContext) -> None:
        """Called when panel is unmounted."""
        pass
