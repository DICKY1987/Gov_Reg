# coding: utf-8
"""Task Counter Widget - Shows total task count."""
# DOC_ID: DOC-GUI-APP-V2-TASK-COUNTER-008

from gui_app_v2.widgets.base_panel import BasePanelWidget


class TaskCounterWidget(BasePanelWidget):
    """Panel showing total task count."""

    def __init__(self, state_client=None, parent=None):
        self.state_client = state_client
        super().__init__("📋 Tasks", refresh_interval=2000, parent=parent)

    def refresh_data(self):
        """Refresh task count from state."""
        if not self.state_client:
            self.set_value("--", "#808080")
            self.set_subtitle("No data source")
            return

        try:
            summary = self.state_client.get_pipeline_summary()
            self.set_value(str(summary.total_tasks), "#4ec9b0")
            self.set_subtitle(f"{summary.running_tasks} running")
        except Exception:
            self.set_value("ERR", "#f48771")
            self.set_subtitle("Error loading")
