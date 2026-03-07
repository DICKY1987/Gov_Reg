# coding: utf-8
"""Worker Status Widget - Shows active worker count."""
# DOC_ID: DOC-GUI-APP-V2-WORKER-STATUS-009

from gui_app_v2.widgets.base_panel import BasePanelWidget


class WorkerStatusWidget(BasePanelWidget):
    """Panel showing active worker count."""

    def __init__(self, state_client=None, parent=None):
        self.state_client = state_client
        super().__init__("⚙️ Workers", refresh_interval=2000, parent=parent)

    def refresh_data(self):
        """Refresh worker count from state."""
        if not self.state_client:
            self.set_value("--", "#808080")
            self.set_subtitle("No data source")
            return

        try:
            summary = self.state_client.get_pipeline_summary()
            self.set_value(str(summary.active_workers), "#569cd6")
            self.set_subtitle("active")
        except Exception:
            self.set_value("ERR", "#f48771")
            self.set_subtitle("Error loading")
