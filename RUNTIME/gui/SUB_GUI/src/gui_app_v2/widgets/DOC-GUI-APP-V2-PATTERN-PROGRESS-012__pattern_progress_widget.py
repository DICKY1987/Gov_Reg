# coding: utf-8
"""Pattern Progress Widget - Shows pattern execution progress."""
# DOC_ID: DOC-GUI-APP-V2-PATTERN-PROGRESS-012

from gui_app_v2.widgets.base_panel import BasePanelWidget


class PatternProgressWidget(BasePanelWidget):
    """Panel showing pattern execution progress."""

    def __init__(self, pattern_client=None, parent=None):
        self.pattern_client = pattern_client
        super().__init__("⚡ Patterns", refresh_interval=3000, parent=parent)

    def refresh_data(self):
        """Refresh pattern progress from client."""
        if not self.pattern_client:
            self.set_value("--", "#808080")
            self.set_subtitle("No data source")
            return

        try:
            runs = self.pattern_client.get_recent_runs(limit=1)
            if runs:
                run = runs[0]
                progress = int(run.progress * 100)
                self.set_value(f"{progress}%", "#dcdcaa")
                self.set_subtitle(run.status.value)
            else:
                self.set_value("0%", "#808080")
                self.set_subtitle("no active runs")
        except Exception:
            self.set_value("ERR", "#f48771")
            self.set_subtitle("Error loading")
