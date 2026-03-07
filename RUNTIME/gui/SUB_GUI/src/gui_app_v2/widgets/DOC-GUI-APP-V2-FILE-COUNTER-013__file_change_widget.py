# coding: utf-8
"""File Change Counter Widget - Shows recent file changes."""
# DOC_ID: DOC-GUI-APP-V2-FILE-COUNTER-013

from gui_app_v2.widgets.base_panel import BasePanelWidget


class FileChangeWidget(BasePanelWidget):
    """Panel showing file change count."""

    def __init__(self, state_client=None, parent=None):
        self.state_client = state_client
        super().__init__("📝 Files", refresh_interval=3000, parent=parent)

    def refresh_data(self):
        """Refresh file change count from state."""
        if not self.state_client:
            self.set_value("--", "#808080")
            self.set_subtitle("No data source")
            return

        try:
            patches = self.state_client.get_patch_ledger(limit=100)
            count = len(patches)
            self.set_value(str(count), "#4ec9b0")
            self.set_subtitle("recent changes")
        except Exception:
            self.set_value("ERR", "#f48771")
            self.set_subtitle("Error loading")
