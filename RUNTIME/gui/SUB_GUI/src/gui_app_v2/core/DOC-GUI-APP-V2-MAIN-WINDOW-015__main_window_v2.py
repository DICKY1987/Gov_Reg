# coding: utf-8
"""Main Window v2 - Split Terminal + Panel Grid Layout."""
# DOC_ID: DOC-GUI-APP-V2-MAIN-WINDOW-015

from gui_app_v2.core.file_lifecycle_bar import FileLifecycleBar
from gui_app_v2.core.panel_grid_widget import PanelGridWidget
from gui_app_v2.core.terminal_widget import TerminalWidget
from gui_app_v2.widgets.completion_rate_widget import CompletionRateWidget
from gui_app_v2.widgets.error_counter_widget import ErrorCounterWidget
from gui_app_v2.widgets.file_change_widget import FileChangeWidget
from gui_app_v2.widgets.pattern_progress_widget import PatternProgressWidget
from gui_app_v2.widgets.pipeline_status_widget import PipelineStatusWidget
from gui_app_v2.widgets.task_counter_widget import TaskCounterWidget
from gui_app_v2.widgets.worker_status_widget import WorkerStatusWidget
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)


class MainWindowV2(QMainWindow):
    """Main window with split terminal and panel grid layout."""

    def __init__(self, state_client=None, pattern_client=None):
        super().__init__()
        self.state_client = state_client
        self.pattern_client = pattern_client
        self.setup_ui()

    def setup_ui(self):
        """Setup the main window UI."""
        self.setWindowTitle("AI Pipeline Monitor v2.0")
        self.setGeometry(100, 100, 1400, 800)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top section: Terminal + Panel Grid (using splitter)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Terminal
        self.terminal = TerminalWidget()
        splitter.addWidget(self.terminal)

        # Right: Panel Grid
        self.panel_grid = PanelGridWidget(rows=4, cols=3)
        splitter.addWidget(self.panel_grid)

        # Set initial splitter sizes (40% terminal, 60% panels)
        splitter.setSizes([560, 840])
        main_layout.addWidget(splitter, 1)  # Stretch factor 1

        # Bottom: File Lifecycle Bar
        self.lifecycle_bar = FileLifecycleBar(self.state_client)
        self.lifecycle_bar.setMaximumHeight(80)  # Fixed height
        main_layout.addWidget(self.lifecycle_bar, 0)  # No stretch

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        # Populate panel grid
        self.populate_panels()

        # Apply dark theme
        self.apply_theme()

        # Demo: Add some test commands to terminal
        self.add_demo_content()

    def populate_panels(self):
        """Populate the panel grid with widgets."""
        # Row 0 (larger panels)
        self.panel_grid.add_panel(
            PipelineStatusWidget(self.state_client), 0, 0, rowspan=1, colspan=1
        )
        self.panel_grid.add_panel(
            TaskCounterWidget(self.state_client), 0, 1, rowspan=1, colspan=1
        )
        self.panel_grid.add_panel(
            WorkerStatusWidget(self.state_client), 0, 2, rowspan=1, colspan=1
        )

        # Row 1 (larger panels)
        self.panel_grid.add_panel(
            ErrorCounterWidget(self.state_client), 1, 0, rowspan=1, colspan=1
        )
        self.panel_grid.add_panel(
            CompletionRateWidget(self.state_client), 1, 1, rowspan=1, colspan=1
        )
        self.panel_grid.add_panel(
            FileChangeWidget(self.state_client), 1, 2, rowspan=1, colspan=1
        )

        # Row 2 (smaller panels)
        self.panel_grid.add_panel(
            PatternProgressWidget(self.pattern_client), 2, 0, rowspan=1, colspan=1
        )
        self.panel_grid.add_panel(
            self.create_placeholder("🔧 Tool Health"), 2, 1, rowspan=1, colspan=1
        )
        self.panel_grid.add_panel(
            self.create_placeholder("📈 CPU Usage"), 2, 2, rowspan=1, colspan=1
        )

        # Row 3 (smaller panels)
        self.panel_grid.add_panel(
            self.create_placeholder("💾 Memory"), 3, 0, rowspan=1, colspan=1
        )
        self.panel_grid.add_panel(
            self.create_placeholder("⏱️ Uptime"), 3, 1, rowspan=1, colspan=1
        )
        self.panel_grid.add_panel(
            self.create_placeholder("🌐 Network"), 3, 2, rowspan=1, colspan=1
        )

    def create_placeholder(self, text: str) -> QWidget:
        """Create a placeholder panel widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        label = QLabel(text)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(
            """
            QLabel {
                color: #808080;
                font-size: 12px;
            }
        """
        )
        layout.addWidget(label)
        widget.setStyleSheet(
            """
            QWidget {
                background-color: #252526;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
            }
        """
        )
        return widget

    def apply_theme(self):
        """Apply dark theme to window."""
        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #1e1e1e;
            }
            QStatusBar {
                background-color: #007acc;
                color: #ffffff;
                font-size: 10px;
                padding: 4px;
            }
        """
        )

    def add_demo_content(self):
        """Add demo content to terminal and lifecycle bar."""
        # Terminal demo
        self.terminal.append_text("Welcome to AI Pipeline v2.0!\n")
        self.terminal.append_text("System initialized successfully.\n\n")

        # File lifecycle demo (if using mock data)
        if self.state_client:
            self.lifecycle_bar.add_file_event("config.yaml", "modify")
            self.lifecycle_bar.add_file_event("task_executor.py", "modify")
            self.lifecycle_bar.add_file_event("new_feature.py", "add")
