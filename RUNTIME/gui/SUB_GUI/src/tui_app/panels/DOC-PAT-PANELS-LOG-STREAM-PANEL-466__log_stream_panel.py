# DOC_LINK: DOC-PAT-PANELS-LOG-STREAM-PANEL-466
"""Log stream panel for viewing pipeline logs in real-time."""

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static
from tui_app.core.panel_plugin import PanelContext
from tui_app.core.panel_registry import register_panel


class LogStreamWidget(Vertical):
    """Displays a live tail of the pipeline log file."""

    # DOC_ID: DOC-PAT-PANELS-LOG-STREAM-PANEL-466

    def __init__(self, context: PanelContext):
        super().__init__(id="log-stream-root")
        self.context = context
        panel_cfg = getattr(context.config, "panels", None)
        logs_cfg = getattr(context.config, "logs", None)
        self.refresh_interval = panel_cfg.log_stream if panel_cfg else 3.0
        self.log_path = Path(getattr(logs_cfg, "path", "logs/combined.log"))
        self.max_lines = getattr(logs_cfg, "max_lines", 60)
        self.summary = Static("", classes="card", id="log-stream-summary")
        self.log_view = Static("", id="log-stream-body")

    def compose(self) -> ComposeResult:
        yield self.summary
        yield self.log_view

    def on_mount(self) -> None:
        """Initial render and schedule refresh."""
        self._refresh()
        self.set_interval(self.refresh_interval, self._refresh)

    def _refresh(self) -> None:
        if not self.log_path.exists():
            self.summary.update(f"[yellow]Log file not found[/] ({self.log_path})")
            self.log_view.update("No log file available.")
            return

        try:
            content = self.log_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as exc:
            self.summary.update(f"[red]Unable to read log:[/] {exc}")
            self.log_view.update("Unable to read log file.")
            return

        lines = content.splitlines()
        tail = lines[-self.max_lines :]
        self.summary.update(
            f"[bold cyan]Live log tail[/] - showing last {len(tail)} lines from {self.log_path}"
        )
        self.log_view.update("\n".join(tail))


@register_panel("log_stream")
class LogStreamPanel:
    """Panel showing real-time log stream from pipeline."""

    @property
    def panel_id(self) -> str:
        return "log_stream"

    @property
    def title(self) -> str:
        return "Log Stream"

    def create_widget(self, context: PanelContext) -> LogStreamWidget:
        """Create log stream widget."""
        return LogStreamWidget(context)

    def on_mount(self, context: PanelContext) -> None:
        """Called when panel is mounted."""
        pass

    def on_unmount(self, context: PanelContext) -> None:
        """Called when panel is unmounted."""
        pass
