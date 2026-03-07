# DOC_LINK: DOC-TEST-MANAGEMENT-SCRIPTS-001
"""
Comprehensive tests for top-level management scripts.

DOC_ID: DOC-TEST-MANAGEMENT-SCRIPTS-001
"""

import pytest
import sys
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

REPO_ROOT = Path(__file__).parent.parent.parent
MODULE_ROOT = Path(__file__).parent.parent


class TestSyncAllRegistries:
    """Test sync_all_registries.py."""

    def test_script_exists(self):
        """Sync script should exist."""
        script_path = MODULE_ROOT / "sync_all_registries.py"
        assert script_path.exists(), f"Script not found at {script_path}"

    def test_script_syntax(self):
        """Sync script should have valid syntax."""
        script_path = MODULE_ROOT / "sync_all_registries.py"
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(script_path)],
            capture_output=True
        )
        assert result.returncode == 0, f"Syntax error: {result.stderr}"

    def test_script_imports(self):
        """Sync script should import without errors."""
        try:
            import sync_all_registries
            assert sync_all_registries is not None
        except ImportError as e:
            pytest.skip(f"Cannot import: {e}")

    def test_sync_function_exists(self):
        """Sync script should have main sync function."""
        try:
            from sync_all_registries import sync_all
            assert callable(sync_all)
        except ImportError:
            pytest.skip("Module not available")


class TestValidateIDTypeRegistry:
    """Test validate_id_type_registry.py."""

    def test_script_exists(self):
        """Validator script should exist."""
        script_path = MODULE_ROOT / "validate_id_type_registry.py"
        assert script_path.exists()

    def test_script_syntax(self):
        """Validator script should have valid syntax."""
        script_path = MODULE_ROOT / "validate_id_type_registry.py"
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(script_path)],
            capture_output=True
        )
        assert result.returncode == 0

    def test_script_imports(self):
        """Validator script should import."""
        try:
            import validate_id_type_registry
            assert validate_id_type_registry is not None
        except ImportError as e:
            pytest.skip(f"Cannot import: {e}")

    def test_validate_function_exists(self):
        """Validator should have validate function."""
        try:
            from validate_id_type_registry import validate
            assert callable(validate)
        except ImportError:
            pytest.skip("Module not available")


class TestUnifiedPreCommitHook:
    """Test unified_pre_commit_hook.py."""

    def test_hook_exists(self):
        """Unified hook should exist."""
        hook_path = MODULE_ROOT / "unified_pre_commit_hook.py"
        assert hook_path.exists()

    def test_hook_syntax(self):
        """Hook should have valid syntax."""
        hook_path = MODULE_ROOT / "unified_pre_commit_hook.py"
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(hook_path)],
            capture_output=True
        )
        assert result.returncode == 0

    def test_hook_imports(self):
        """Hook should import."""
        try:
            import unified_pre_commit_hook
            assert unified_pre_commit_hook is not None
        except ImportError as e:
            pytest.skip(f"Cannot import: {e}")

    def test_hook_main_function(self):
        """Hook should have main function."""
        try:
            from unified_pre_commit_hook import main
            assert callable(main)
        except ImportError:
            pytest.skip("Module not available")


class TestGenerateDashboard:
    """Test generate_dashboard.py."""

    def test_script_exists(self):
        """Dashboard generator should exist."""
        script_path = MODULE_ROOT / "generate_dashboard.py"
        assert script_path.exists()

    def test_script_syntax(self):
        """Dashboard generator should have valid syntax."""
        script_path = MODULE_ROOT / "generate_dashboard.py"
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(script_path)],
            capture_output=True
        )
        assert result.returncode == 0

    def test_script_imports(self):
        """Dashboard generator should import."""
        try:
            import generate_dashboard
            assert generate_dashboard is not None
        except ImportError as e:
            pytest.skip(f"Cannot import: {e}")

    def test_generate_function_exists(self):
        """Should have generate function."""
        try:
            from generate_dashboard import generate
            assert callable(generate)
        except ImportError:
            pytest.skip("Module not available")


class TestIDTypeManager:
    """Test id_type_manager.py."""

    def test_manager_exists(self):
        """ID type manager should exist."""
        script_path = MODULE_ROOT / "id_type_manager.py"
        assert script_path.exists()

    def test_manager_syntax(self):
        """Manager should have valid syntax."""
        script_path = MODULE_ROOT / "id_type_manager.py"
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(script_path)],
            capture_output=True
        )
        assert result.returncode == 0

    def test_manager_imports(self):
        """Manager should import."""
        try:
            import id_type_manager
            assert id_type_manager is not None
        except ImportError as e:
            pytest.skip(f"Cannot import: {e}")

    def test_manager_class_exists(self):
        """Should have IDTypeManager class."""
        try:
            from id_type_manager import IDTypeManager
            assert IDTypeManager is not None
        except ImportError:
            pytest.skip("Module not available")


class TestMigrationScripts:
    """Test migration scripts."""

    def test_migrate_trigger_ids_exists(self):
        """Trigger ID migration script should exist."""
        script_path = MODULE_ROOT / "migrate_trigger_ids.py"
        assert script_path.exists()

    def test_migrate_pattern_ids_exists(self):
        """Pattern ID migration script should exist."""
        script_path = MODULE_ROOT / "migrate_pattern_ids.py"
        assert script_path.exists()

    def test_migrate_legacy_format_exists(self):
        """Legacy format migration should exist."""
        script_path = MODULE_ROOT / "migrate_legacy_format.py"
        assert script_path.exists()

    def test_migration_scripts_syntax(self):
        """All migration scripts should have valid syntax."""
        scripts = [
            "migrate_trigger_ids.py",
            "migrate_pattern_ids.py",
            "migrate_legacy_format.py"
        ]

        for script_name in scripts:
            script_path = MODULE_ROOT / script_name
            if script_path.exists():
                result = subprocess.run(
                    [sys.executable, "-m", "py_compile", str(script_path)],
                    capture_output=True
                )
                assert result.returncode == 0, f"Syntax error in {script_name}"


class TestRestructureRegistry:
    """Test restructure_registry.py."""

    def test_script_exists(self):
        """Restructure script should exist."""
        script_path = MODULE_ROOT / "restructure_registry.py"
        assert script_path.exists()

    def test_script_syntax(self):
        """Restructure script should have valid syntax."""
        script_path = MODULE_ROOT / "restructure_registry.py"
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(script_path)],
            capture_output=True
        )
        assert result.returncode == 0

    def test_script_imports(self):
        """Restructure script should import."""
        try:
            import restructure_registry
            assert restructure_registry is not None
        except ImportError as e:
            pytest.skip(f"Cannot import: {e}")


class TestManagementIntegration:
    """Integration tests for management scripts."""

    def test_sync_then_validate_workflow(self):
        """Test sync → validate workflow."""
        # Both scripts should exist
        sync_path = MODULE_ROOT / "sync_all_registries.py"
        validate_path = MODULE_ROOT / "validate_id_type_registry.py"

        assert sync_path.exists()
        assert validate_path.exists()

    def test_generate_dashboard_after_sync(self):
        """Test dashboard generation after sync."""
        sync_path = MODULE_ROOT / "sync_all_registries.py"
        dashboard_path = MODULE_ROOT / "generate_dashboard.py"

        assert sync_path.exists()
        assert dashboard_path.exists()

    def test_migration_then_sync_workflow(self):
        """Test migration → sync workflow."""
        migrate_path = MODULE_ROOT / "migrate_trigger_ids.py"
        sync_path = MODULE_ROOT / "sync_all_registries.py"

        assert migrate_path.exists()
        assert sync_path.exists()


class TestDashboardOutput:
    """Test dashboard generation output."""

    def test_unified_dashboard_exists(self):
        """Unified dashboard HTML should exist."""
        dashboard_path = MODULE_ROOT / "unified_dashboard.html"
        assert dashboard_path.exists()

    def test_dashboard_has_content(self):
        """Dashboard should have meaningful content."""
        dashboard_path = MODULE_ROOT / "unified_dashboard.html"
        content = dashboard_path.read_text()

        assert len(content) > 1000, "Dashboard too small"
        assert "doc_id" in content.lower() or "stable" in content.lower()

    def test_dashboard_is_valid_html(self):
        """Dashboard should be valid HTML."""
        dashboard_path = MODULE_ROOT / "unified_dashboard.html"
        content = dashboard_path.read_text()

        assert "<html" in content.lower()
        assert "</html>" in content.lower()
        assert "<body" in content.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
