# coding: utf-8
"""Panel Grid Widget - Modular grid layout for small information panels."""
# DOC_ID: DOC-GUI-APP-V2-PANEL-GRID-005

from PySide6.QtWidgets import QGridLayout, QWidget


class PanelGridWidget(QWidget):
    """Grid layout for modular panel widgets."""

    def __init__(self, rows=4, cols=3, parent=None):
        super().__init__(parent)
        self.rows = rows
        self.cols = cols
        self.panels = {}
        self.setup_ui()

    def setup_ui(self):
        """Setup grid layout."""
        self.layout = QGridLayout(self)
        self.layout.setSpacing(8)
        self.layout.setContentsMargins(4, 4, 4, 4)

        # Initialize empty grid
        for row in range(self.rows):
            for col in range(self.cols):
                # Placeholder panels will be added here
                pass

    def add_panel(
        self,
        panel_widget: QWidget,
        row: int,
        col: int,
        rowspan: int = 1,
        colspan: int = 1,
    ):
        """Add a panel widget to the grid.

        Args:
            panel_widget: The widget to add
            row: Grid row position (0-based)
            col: Grid column position (0-based)
            rowspan: Number of rows to span
            colspan: Number of columns to span
        """
        key = (row, col)

        # Remove existing panel if present
        if key in self.panels:
            old_widget = self.panels[key]
            self.layout.removeWidget(old_widget)
            old_widget.deleteLater()

        # Add new panel
        self.layout.addWidget(panel_widget, row, col, rowspan, colspan)
        self.panels[key] = panel_widget

    def remove_panel(self, row: int, col: int):
        """Remove a panel from the grid."""
        key = (row, col)
        if key in self.panels:
            widget = self.panels[key]
            self.layout.removeWidget(widget)
            widget.deleteLater()
            del self.panels[key]

    def clear_grid(self):
        """Remove all panels from grid."""
        for key in list(self.panels.keys()):
            self.remove_panel(*key)

    def get_panel(self, row: int, col: int) -> QWidget:
        """Get panel widget at position."""
        return self.panels.get((row, col))
