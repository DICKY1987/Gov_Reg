# DOC_LINK: DOC-GUI-VALIDATION-600
"""Validation script for GUI architecture.

Verifies that all components are correctly installed and configured.
"""

# DOC_ID: DOC-GUI-VALIDATION-600

import sys
from pathlib import Path


def check_file_exists(path: Path, description: str) -> bool:
    """Check if a file exists and report."""
    exists = path.exists()
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {path}")
    return exists


def check_imports() -> bool:
    """Check that critical imports work."""
    print("\n🔍 Checking Python imports...")

    checks = []

    # Check PySide6
    try:
        import PySide6

        print("✅ PySide6 installed")
        checks.append(True)
    except ImportError:
        print("❌ PySide6 NOT installed (run: pip install -r requirements-gui.txt)")
        checks.append(False)

    # Check YAML
    try:
        import yaml

        print("✅ PyYAML installed")
        checks.append(True)
    except ImportError:
        print("❌ PyYAML NOT installed")
        checks.append(False)

    # Check ui_core imports
    try:
        from ui_core.panel_context import PanelContext
        from ui_core.pattern_client import PatternClient
        from ui_core.state_client import StateClient

        print("✅ ui_core imports working")
        checks.append(True)
    except ImportError as e:
        print(f"❌ ui_core imports FAILED: {e}")
        checks.append(False)

    # Check gui_app imports
    try:
        from gui_app.core.gui_app import GuiApp
        from gui_app.core.gui_panel_registry import get_registry

        print("✅ gui_app imports working")
        checks.append(True)
    except ImportError as e:
        print(f"❌ gui_app imports FAILED: {e}")
        checks.append(False)

    return all(checks)


def check_panels() -> bool:
    """Check that all panels are registered."""
    print("\n🔍 Checking panel registration...")

    try:
        from gui_app.core.gui_panel_registry import get_registry

        registry = get_registry()
        panels = registry.list_panels()

        expected = [
            "dashboard",
            "file_lifecycle",
            "tool_health",
            "log_stream",
            "pattern_activity",
        ]

        all_registered = True
        for panel_id in expected:
            if panel_id in panels:
                print(f"✅ Panel '{panel_id}' registered")
            else:
                print(f"❌ Panel '{panel_id}' NOT registered")
                all_registered = False

        return all_registered
    except Exception as e:
        print(f"❌ Panel check FAILED: {e}")
        return False


def main():
    """Run all validation checks."""
    print("=" * 60)
    print("GUI Architecture Validation")
    print("=" * 60)

    # Change to src directory
    src_dir = Path(__file__).parent / "src"
    if src_dir.exists():
        import os

        os.chdir(src_dir)
        print(f"📁 Working directory: {src_dir}\n")

    checks = []

    # File structure checks
    print("🔍 Checking file structure...\n")

    files_to_check = [
        (Path("ui_core/__init__.py"), "ui_core package"),
        (Path("ui_core/panel_context.py"), "PanelContext"),
        (Path("ui_core/state_client.py"), "StateClient"),
        (Path("ui_core/pattern_client.py"), "PatternClient"),
        (Path("ui_core/layout_config.py"), "UIConfig"),
        (Path("gui_app/__init__.py"), "gui_app package"),
        (Path("gui_app/main.py"), "GUI entry point"),
        (Path("gui_app/core/gui_app.py"), "GuiApp main window"),
        (Path("gui_app/panels/dashboard_panel.py"), "Dashboard panel"),
        (Path("config/ui_config.yaml"), "Unified config"),
        (Path("../requirements-gui.txt"), "GUI requirements"),
    ]

    for path, desc in files_to_check:
        checks.append(check_file_exists(path, desc))

    # Import checks
    checks.append(check_imports())

    # Panel registration checks
    checks.append(check_panels())

    # Summary
    print("\n" + "=" * 60)
    if all(checks):
        print("✅ ALL CHECKS PASSED - GUI architecture is ready!")
        print("\nNext steps:")
        print("  1. Run: python -m gui_app.main --use-mock-data")
        print("  2. See: ../docs/GUI_QUICK_START.md")
        return 0
    else:
        print("❌ SOME CHECKS FAILED - See errors above")
        print("\nTroubleshooting:")
        print("  1. Install dependencies: pip install -r ../requirements-gui.txt")
        print("  2. Check you're in gui/src/ directory")
        print("  3. See: ../docs/GUI_QUICK_START.md")
        return 1


if __name__ == "__main__":
    sys.exit(main())
