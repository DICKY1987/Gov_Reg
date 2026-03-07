# coding: utf-8
"""Pipeline Status Widget - Shows overall pipeline status."""
# DOC_ID: DOC-GUI-APP-V2-PIPELINE-STATUS-010

from gui_app_v2.widgets.base_panel import BasePanelWidget


class PipelineStatusWidget(BasePanelWidget):
    """Panel showing pipeline status."""

    def __init__(self, state_client=None, parent=None):
        self.state_client = state_client
        super().__init__("🚀 Pipeline", refresh_interval=2000, parent=parent)

    def refresh_data(self):
        """Refresh pipeline status from state."""
        if not self.state_client:
            self.set_value("--", "#808080")
            self.set_subtitle("No data source")
            return

        try:
            summary = self.state_client.get_pipeline_summary()
            status = summary.status.upper()

            # Color code by status
            color_map = {
                "RUNNING": "#4ec9b0",
                "IDLE": "#dcdcaa",
                "ERROR": "#f48771",
                "PAUSED": "#569cd6",
            }
            color = color_map.get(status, "#d4d4d4")

            self.set_value(status, color)
            self.set_subtitle(f"{summary.completed_tasks} completed")
        except Exception:
            self.set_value("ERR", "#f48771")
            self.set_subtitle("Error loading")
