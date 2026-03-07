# coding: utf-8
"""File Lifecycle Bar - Persistent bottom bar showing file changes."""
# DOC_ID: DOC-GUI-APP-V2-FILE-LIFECYCLE-BAR-006

from datetime import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget


class FileLifecycleBar(QWidget):
    """Bottom bar showing file lifecycle events."""

    def __init__(self, state_client=None, parent=None):
        super().__init__(parent)
        self.state_client = state_client
        self.file_items = []
        self.setup_ui()
        self.start_refresh()

    def setup_ui(self):
        """Setup lifecycle bar UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # Title bar
        title_label = QLabel("📁 File Lifecycle")
        title_label.setStyleSheet(
            """
            QLabel {
                background-color: #2d2d30;
                color: #ffffff;
                padding: 4px 8px;
                font-weight: bold;
                font-size: 11px;
            }
        """
        )
        layout.addWidget(title_label)

        # Scrollable file list
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setFixedHeight(50)  # Fixed height for file items

        # Container for file items
        self.file_container = QWidget()
        self.file_layout = QHBoxLayout(self.file_container)
        self.file_layout.setContentsMargins(4, 4, 4, 4)
        self.file_layout.setSpacing(8)
        self.file_layout.addStretch()

        scroll_area.setWidget(self.file_container)
        layout.addWidget(scroll_area)

        # Style
        self.setStyleSheet(
            """
            FileLifecycleBar {
                background-color: #1e1e1e;
                border-top: 2px solid #3c3c3c;
            }
        """
        )

    def add_file_event(self, filename: str, operation: str, timestamp: str = None):
        """Add a file event to the bar.

        Args:
            filename: Name of the file
            operation: Operation type (add, modify, delete)
            timestamp: Event timestamp (defaults to now)
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%H:%M:%S")

        # Color code by operation
        color_map = {
            "add": "#4ec9b0",
            "modify": "#dcdcaa",
            "delete": "#f48771",
            "pending": "#569cd6",
            "applied": "#4ec9b0",
        }
        color = color_map.get(operation.lower(), "#d4d4d4")

        # Create file item widget
        item = QLabel(f"⚡ {filename}")
        item.setToolTip(f"{operation.upper()} at {timestamp}")
        item.setStyleSheet(
            f"""
            QLabel {{
                background-color: #2d2d30;
                color: {color};
                padding: 4px 8px;
                border-radius: 3px;
                font-size: 10px;
                font-family: Consolas;
            }}
        """
        )

        # Insert before stretch
        self.file_layout.insertWidget(self.file_layout.count() - 1, item)
        self.file_items.append(item)

        # Limit to 20 items
        if len(self.file_items) > 20:
            old_item = self.file_items.pop(0)
            self.file_layout.removeWidget(old_item)
            old_item.deleteLater()

    def refresh_from_state(self):
        """Refresh file events from state client."""
        if not self.state_client:
            return

        try:
            patches = self.state_client.get_patch_ledger(limit=10)
            for patch in patches:
                for file in patch.files[:3]:  # Show first 3 files
                    self.add_file_event(file, patch.state)
        except Exception:
            pass  # Silently fail if no data

    def start_refresh(self):
        """Start auto-refresh timer."""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_from_state)
        self.refresh_timer.start(5000)  # 5 second refresh

    def clear(self):
        """Clear all file items."""
        for item in self.file_items:
            self.file_layout.removeWidget(item)
            item.deleteLater()
        self.file_items.clear()
