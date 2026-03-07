# coding: utf-8
"""GUI Application v2 Main Entry Point.

User vision implementation: Split terminal + modular panel grid.
"""
# DOC_ID: DOC-GUI-APP-V2-MAIN-016

import argparse
import sys

from gui_app_v2.core.main_window_v2 import MainWindowV2
from PySide6.QtWidgets import QApplication
from ui_core.pattern_client import InMemoryPatternStateStore, PatternClient
from ui_core.sqlite_state_backend import SQLiteStateBackend
from ui_core.state_client import InMemoryStateBackend, StateClient


def main():
    """Main entry point for GUI v2."""
    parser = argparse.ArgumentParser(description="AI Pipeline GUI v2")
    parser.add_argument(
        "--use-mock-data",
        action="store_true",
        help="Use mock in-memory data instead of SQLite database",
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default=None,
        help="Path to SQLite database (if not using mock data)",
    )

    args = parser.parse_args()

    # Initialize Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("AI Pipeline Monitor v2")
    app.setOrganizationName("AI Pipeline")

    # Initialize clients
    if args.use_mock_data:
        state_client = StateClient(InMemoryStateBackend())
        pattern_client = PatternClient(InMemoryPatternStateStore())
    else:
        state_backend = SQLiteStateBackend(db_path=args.db_path)
        state_client = StateClient(state_backend)
        pattern_client = PatternClient(
            InMemoryPatternStateStore()  # TODO: Add SQLite pattern store
        )

    # Create and show main window
    window = MainWindowV2(
        state_client=state_client,
        pattern_client=pattern_client,
    )
    window.show()

    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
