# coding: utf-8
"""Terminal Widget - Embedded terminal display for command output."""
# DOC_ID: DOC-GUI-APP-V2-TERMINAL-WIDGET-004

from PySide6.QtCore import QProcess, QTimer, Signal
from PySide6.QtGui import QFont, QTextCursor
from PySide6.QtWidgets import QTextEdit, QVBoxLayout, QWidget


class TerminalWidget(QWidget):
    """Terminal widget with command execution capability."""

    command_executed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.process = None
        self.setup_ui()

    def setup_ui(self):
        """Setup terminal UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Terminal display
        self.terminal = QTextEdit()
        self.terminal.setReadOnly(True)
        self.terminal.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)

        # Monospace font
        font = QFont("Consolas", 9)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.terminal.setFont(font)

        # Dark terminal theme
        self.terminal.setStyleSheet(
            """
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
            }
        """
        )

        layout.addWidget(self.terminal)

        # Auto-scroll timer
        self.scroll_timer = QTimer()
        self.scroll_timer.timeout.connect(self.auto_scroll)
        self.scroll_timer.start(100)

        # Initial message
        self.append_text("AI Pipeline Terminal v2.0\n")
        self.append_text("=" * 50 + "\n")
        self.append_text("Ready for commands...\n\n")

    def append_text(self, text: str):
        """Append text to terminal."""
        self.terminal.moveCursor(QTextCursor.MoveOperation.End)
        self.terminal.insertPlainText(text)

    def auto_scroll(self):
        """Auto-scroll to bottom."""
        scrollbar = self.terminal.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def execute_command(self, command: str):
        """Execute a shell command and display output."""
        self.append_text(f"$ {command}\n")

        if self.process and self.process.state() == QProcess.ProcessState.Running:
            self.append_text("[ERROR] Process already running\n\n")
            return

        self.process = QProcess()
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)

        self.process.readyReadStandardOutput.connect(self.handle_output)
        self.process.finished.connect(self.handle_finished)

        # Start process (Windows PowerShell)
        self.process.start("powershell.exe", ["-Command", command])

    def handle_output(self):
        """Handle process output."""
        if self.process:
            output = self.process.readAllStandardOutput().data().decode("utf-8")
            self.append_text(output)

    def handle_finished(self, exit_code, exit_status):
        """Handle process completion."""
        self.append_text(f"\n[Process exited with code {exit_code}]\n\n")
        self.command_executed.emit(f"Exit code: {exit_code}")

    def clear(self):
        """Clear terminal."""
        self.terminal.clear()
        self.append_text("AI Pipeline Terminal v2.0\n")
        self.append_text("=" * 50 + "\n\n")
