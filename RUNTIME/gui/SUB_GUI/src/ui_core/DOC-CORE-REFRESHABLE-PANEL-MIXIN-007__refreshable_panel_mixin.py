# DOC_LINK: DOC-CORE-REFRESHABLE-PANEL-MIXIN-007
"""Refreshable Panel Mixin - Provides manual refresh controls for GUI panels.

Adds standardized refresh button, pause/resume toggle, and last updated timestamp
to panels that inherit this mixin.
"""

# DOC_ID: DOC-CORE-REFRESHABLE-PANEL-MIXIN-007

from datetime import datetime
from typing import Optional, Callable

from PySide6.QtWidgets import QHBoxLayout, QPushButton, QLabel, QWidget, QCheckBox
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QAction, QKeySequence


class RefreshablePanelMixin:
    """Mixin to add manual refresh controls to GUI panels.

    Provides:
    - Refresh button
    - Pause/Resume toggle
    - Last updated timestamp
    - Keyboard shortcuts (F5, Ctrl+R)
    """

    # Signal for refresh requested (if panel uses Qt signals)
    refresh_requested = Signal()

    def setup_refresh_controls(
        self,
        parent_widget: QWidget,
        on_refresh: Callable[[], None],
        auto_refresh_timer: Optional[QTimer] = None,
        show_pause_toggle: bool = True
    ) -> QWidget:
        """Setup refresh controls and return widget to add to layout.

        Args:
            parent_widget: Parent widget for controls
            on_refresh: Callback function when refresh is triggered
            auto_refresh_timer: Optional QTimer for auto-refresh (to pause/resume)
            show_pause_toggle: Whether to show pause/resume toggle

        Returns:
            QWidget containing refresh controls
        """
        self._on_refresh_callback = on_refresh
        self._auto_refresh_timer = auto_refresh_timer
        self._last_refresh_time = None

        # Create controls container
        controls_widget = QWidget(parent_widget)
        controls_layout = QHBoxLayout(controls_widget)
        controls_layout.setContentsMargins(5, 5, 5, 5)

        # Refresh button
        self._refresh_button = QPushButton("🔄 Refresh")
        self._refresh_button.setToolTip("Refresh data (F5 or Ctrl+R)")
        self._refresh_button.clicked.connect(self._on_manual_refresh)
        controls_layout.addWidget(self._refresh_button)

        # Pause/Resume toggle
        if show_pause_toggle and auto_refresh_timer:
            self._pause_checkbox = QCheckBox("Pause Auto-Refresh")
            self._pause_checkbox.setToolTip("Pause automatic updates")
            self._pause_checkbox.stateChanged.connect(self._on_pause_toggled)
            controls_layout.addWidget(self._pause_checkbox)
        else:
            self._pause_checkbox = None

        # Last updated label
        self._last_updated_label = QLabel("Last updated: Never")
        self._last_updated_label.setStyleSheet("color: gray; font-size: 10px;")
        controls_layout.addWidget(self._last_updated_label)

        # Stretch to push controls to the left
        controls_layout.addStretch()

        # Setup keyboard shortcuts (if parent supports actions)
        if hasattr(parent_widget, 'addAction'):
            # F5 shortcut
            refresh_action_f5 = QAction("Refresh", parent_widget)
            refresh_action_f5.setShortcut(QKeySequence("F5"))
            refresh_action_f5.triggered.connect(self._on_manual_refresh)
            parent_widget.addAction(refresh_action_f5)

            # Ctrl+R shortcut
            refresh_action_ctrlr = QAction("Refresh", parent_widget)
            refresh_action_ctrlr.setShortcut(QKeySequence("Ctrl+R"))
            refresh_action_ctrlr.triggered.connect(self._on_manual_refresh)
            parent_widget.addAction(refresh_action_ctrlr)

        return controls_widget

    def _on_manual_refresh(self):
        """Handle manual refresh button click."""
        # Update timestamp
        self._last_refresh_time = datetime.now()
        self._update_timestamp_label()

        # Call refresh callback
        if self._on_refresh_callback:
            self._on_refresh_callback()

        # Emit signal (if supported)
        if hasattr(self, 'refresh_requested'):
            try:
                self.refresh_requested.emit()
            except:
                pass  # Signal not connected, ignore

    def _on_pause_toggled(self, state):
        """Handle pause checkbox toggle."""
        if not self._auto_refresh_timer:
            return

        is_paused = (state == Qt.CheckState.Checked.value)

        if is_paused:
            # Pause timer
            self._auto_refresh_timer.stop()
            if self._pause_checkbox:
                self._pause_checkbox.setText("▶️ Resume Auto-Refresh")
        else:
            # Resume timer
            self._auto_refresh_timer.start()
            if self._pause_checkbox:
                self._pause_checkbox.setText("⏸️ Pause Auto-Refresh")

    def _update_timestamp_label(self):
        """Update the last updated timestamp label."""
        if not self._last_refresh_time:
            return

        # Format timestamp
        time_str = self._last_refresh_time.strftime("%H:%M:%S")

        # Calculate seconds ago
        seconds_ago = (datetime.now() - self._last_refresh_time).total_seconds()

        if seconds_ago < 60:
            time_ago = f"{int(seconds_ago)}s ago"
        elif seconds_ago < 3600:
            time_ago = f"{int(seconds_ago / 60)}m ago"
        else:
            time_ago = f"{int(seconds_ago / 3600)}h ago"

        self._last_updated_label.setText(f"Last updated: {time_str} ({time_ago})")

    def mark_refreshed(self):
        """Mark panel as refreshed (call this from auto-refresh logic)."""
        self._last_refresh_time = datetime.now()
        self._update_timestamp_label()

    def is_auto_refresh_paused(self) -> bool:
        """Check if auto-refresh is currently paused."""
        if not self._pause_checkbox:
            return False
        return self._pause_checkbox.isChecked()


# Example usage in a panel:
"""
class MyPanel(QWidget, RefreshablePanelMixin):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        # Add refresh controls at the top
        refresh_controls = self.setup_refresh_controls(
            parent_widget=self,
            on_refresh=self._refresh_data,
            auto_refresh_timer=self.refresh_timer,
            show_pause_toggle=True
        )
        layout.addWidget(refresh_controls)

        # ... rest of panel layout ...

    def _refresh_data(self):
        '''Called when refresh button clicked or F5 pressed'''
        # Reload data
        self.data = load_new_data()
        # Update display
        self.update_display()
        # Mark as refreshed (updates timestamp)
        self.mark_refreshed()
"""
