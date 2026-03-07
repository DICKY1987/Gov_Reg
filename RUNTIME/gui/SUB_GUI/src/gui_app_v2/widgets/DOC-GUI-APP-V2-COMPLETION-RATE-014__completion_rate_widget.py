# coding: utf-8
"""Completion Rate Widget - Shows task completion percentage."""
# DOC_ID: DOC-GUI-APP-V2-COMPLETION-RATE-014

from gui_app_v2.widgets.base_panel import BasePanelWidget


class CompletionRateWidget(BasePanelWidget):
    """Panel showing completion rate."""

    def __init__(self, state_client=None, parent=None):
        self.state_client = state_client
        super().__init__("📊 Completion", refresh_interval=3000, parent=parent)

    def refresh_data(self):
        """Refresh completion rate from state."""
        if not self.state_client:
            self.set_value("--", "#808080")
            self.set_subtitle("No data source")
            return

        try:
            summary = self.state_client.get_pipeline_summary()
            if summary.total_tasks > 0:
                rate = int((summary.completed_tasks / summary.total_tasks) * 100)
                self.set_value(f"{rate}%", "#4ec9b0")
                self.set_subtitle(f"{summary.completed_tasks}/{summary.total_tasks}")
            else:
                self.set_value("0%", "#808080")
                self.set_subtitle("no tasks")
        except Exception:
            self.set_value("ERR", "#f48771")
            self.set_subtitle("Error loading")
