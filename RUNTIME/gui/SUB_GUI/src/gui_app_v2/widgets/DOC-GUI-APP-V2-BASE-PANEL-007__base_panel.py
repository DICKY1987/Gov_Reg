# coding: utf-8
"""Base Panel Widget - Template for small modular panels."""
# DOC_ID: DOC-GUI-APP-V2-BASE-PANEL-007

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class BasePanelWidget(QWidget):
    """Base class for small panel widgets."""

    def __init__(self, title: str, refresh_interval: int = 2000, parent=None):
        super().__init__(parent)
        self.title = title
        self.refresh_interval = refresh_interval
        self.setup_ui()
        self.start_refresh()

    def setup_ui(self):
        """Setup panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # Title
        self.title_label = QLabel(self.title)
        self.title_label.setStyleSheet(
            """
            QLabel {
                font-weight: bold;
                font-size: 10px;
                color: #569cd6;
            }
        """
        )
        layout.addWidget(self.title_label)

        # Value display
        self.value_label = QLabel("--")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_label.setStyleSheet(
            """
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #d4d4d4;
            }
        """
        )
        layout.addWidget(self.value_label)

        # Subtitle/description
        self.subtitle_label = QLabel("")
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle_label.setStyleSheet(
            """
            QLabel {
                font-size: 9px;
                color: #808080;
            }
        """
        )
        layout.addWidget(self.subtitle_label)

        # Panel style
        self.setStyleSheet(
            """
            BasePanelWidget {
                background-color: #252526;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
            }
        """
        )

    def set_value(self, value: str, color: str = "#d4d4d4"):
        """Set the main value display."""
        self.value_label.setText(str(value))
        self.value_label.setStyleSheet(
            f"""
            QLabel {{
                font-size: 24px;
                font-weight: bold;
                color: {color};
            }}
        """
        )

    def set_subtitle(self, text: str):
        """Set the subtitle text."""
        self.subtitle_label.setText(text)

    def refresh_data(self):
        """Override this method to implement data refresh logic."""
        pass

    def start_refresh(self):
        """Start auto-refresh timer."""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(self.refresh_interval)
        self.refresh_data()  # Initial refresh
