# coding: utf-8
"""Error Counter Widget - Shows failed task count."""
# DOC_ID: DOC-GUI-APP-V2-ERROR-COUNTER-011

from gui_app_v2.widgets.base_panel import BasePanelWidget


class ErrorCounterWidget(BasePanelWidget):
    """Panel showing error count."""

    def __init__(self, state_client=None, parent=None):
        self.state_client = state_client
        super().__init__("❌ Errors", refresh_interval=3000, parent=parent)

    def refresh_data(self):
        """Refresh error count from state."""
        if not self.state_client:
            self.set_value("--", "#808080")
            self.set_subtitle("No data source")
            return

        try:
            summary = self.state_client.get_pipeline_summary()
            failed = summary.failed_tasks

            # Red if failures, green if none
            color = "#f48771" if failed > 0 else "#4ec9b0"

            self.set_value(str(failed), color)
            self.set_subtitle("failed tasks")
        except Exception:
            self.set_value("ERR", "#f48771")
            self.set_subtitle("Error loading")
