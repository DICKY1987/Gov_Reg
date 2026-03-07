# DOC_LINK: DOC-PAT-PANELS-TOOL-HEALTH-PANEL-468
"""Tool health panel for monitoring error detection tool status."""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import DataTable, Static
from tui_app.core.panel_plugin import PanelContext
from tui_app.core.panel_registry import register_panel


@dataclass
class ToolStatus:
    """Represents the health of a tool observed in logs."""

    # DOC_ID: DOC-PAT-PANELS-TOOL-HEALTH-PANEL-468
    name: str
    status: str
    last_seen: Optional[datetime]
    message: str


class ToolHealthWidget(Vertical):
    """Displays tool status derived from recent log lines."""

    def __init__(self, context: PanelContext):
        super().__init__(id="tool-health-root")
        self.context = context
        panel_cfg = getattr(context.config, "panels", None)
        self.refresh_interval = panel_cfg.tool_health if panel_cfg else 4.0
        self.summary = Static("", classes="card", id="tool-health-summary")
        self.table = DataTable(id="tool-health-table", zebra_stripes=True)

    def compose(self) -> ComposeResult:
        yield self.summary
        yield self.table

    def on_mount(self) -> None:
        """Initialize table and schedule refresh."""
        self.table.cursor_type = "row"
        self.table.add_columns("Tool", "Status", "Last Seen", "Message")
        self._refresh()
        self.set_interval(self.refresh_interval, self._refresh)

    def _refresh(self) -> None:
        log_path = Path(
            getattr(
                getattr(self.context.config, "logs", {}), "path", "logs/combined.log"
            )
        )
        statuses = self._load_statuses(log_path)

        self.table.clear()
        if not statuses:
            self.summary.update("[yellow]No tool activity found in logs[/]")
            self.table.add_row("n/a", "n/a", "-", "No tool data available")
            return

        healthy = sum(1 for s in statuses if s.status == "ok")
        warn = sum(1 for s in statuses if s.status == "warn")
        error = sum(1 for s in statuses if s.status == "error")

        self.summary.update(
            f"[bold cyan]Tools:[/] {len(statuses)}  "
            f"[green]OK[/]: {healthy}  "
            f"[yellow]Warn[/]: {warn}  "
            f"[red]Error[/]: {error}\n"
            f"[dim]Log:[/] {log_path}"
        )

        for status in statuses:
            style = {"ok": "green", "warn": "yellow", "error": "red"}.get(
                status.status, "cyan"
            )
            status_cell = Text(status.status.upper(), style=style)
            seen = (
                status.last_seen.strftime("%Y-%m-%d %H:%M:%S")
                if status.last_seen
                else "-"
            )
            self.table.add_row(status.name, status_cell, seen, status.message[:60])

    def _load_statuses(self, log_path: Path) -> List[ToolStatus]:
        """Parse the log file and derive tool health."""
        if not log_path.exists():
            return self._fallback_statuses()

        statuses: Dict[str, ToolStatus] = {}
        try:
            with log_path.open("r", encoding="utf-8", errors="ignore") as handle:
                lines = handle.readlines()[-400:]
        except Exception:
            return self._fallback_statuses()

        for line in lines:
            try:
                data = json.loads(line)
            except Exception:
                continue

            tool_name = data.get("toolName")
            if not tool_name:
                continue

            message = data.get("msg", "")
            status = self._derive_status(message)
            timestamp = self._parse_timestamp(data.get("timestamp") or data.get("time"))

            statuses[tool_name] = ToolStatus(
                name=tool_name,
                status=status,
                last_seen=timestamp,
                message=message or "No message",
            )

        if not statuses:
            return self._fallback_statuses()

        return list(statuses.values())

    @staticmethod
    def _derive_status(message: str) -> str:
        lower_msg = (message or "").lower()
        if "error" in lower_msg or "failed" in lower_msg:
            return "error"
        if "registered successfully" in lower_msg or "ready" in lower_msg:
            return "ok"
        return "warn" if "registering" in lower_msg else "info"

    @staticmethod
    def _parse_timestamp(value) -> Optional[datetime]:
        if not value:
            return None
        if isinstance(value, (int, float)):
            try:
                return datetime.fromtimestamp(value / 1000 if value > 1e12 else value)
            except Exception:
                return None
        try:
            # Handle ISO timestamps with trailing Z
            value_str = str(value).replace("Z", "")
            return datetime.fromisoformat(value_str)
        except Exception:
            return None

    @staticmethod
    def _fallback_statuses() -> List[ToolStatus]:
        """Return placeholder statuses when no log data is available."""
        return [
            ToolStatus("ruff", "info", None, "Awaiting tool heartbeat"),
            ToolStatus("mypy", "info", None, "Awaiting tool heartbeat"),
            ToolStatus("pytest", "info", None, "Awaiting tool heartbeat"),
        ]


@register_panel("tool_health")
class ToolHealthPanel:
    """Panel showing health and status of error detection tools."""

    @property
    def panel_id(self) -> str:
        return "tool_health"

    @property
    def title(self) -> str:
        return "Tool Health"

    def create_widget(self, context: PanelContext) -> ToolHealthWidget:
        """Create tool health widget."""
        return ToolHealthWidget(context)

    def on_mount(self, context: PanelContext) -> None:
        """Called when panel is mounted."""
        pass

    def on_unmount(self, context: PanelContext) -> None:
        """Called when panel is unmounted."""
        pass
