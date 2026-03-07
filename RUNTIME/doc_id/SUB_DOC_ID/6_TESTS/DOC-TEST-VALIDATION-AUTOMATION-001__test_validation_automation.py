# DOC_LINK: DOC-TEST-VALIDATION-AUTOMATION-001
"""
Comprehensive tests for validation and automation modules.

DOC_ID: DOC-TEST-VALIDATION-AUTOMATION-001
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

PARENT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PARENT_DIR))


class TestValidationModules:
    """Test all validation modules in 2_VALIDATION_FIXING."""

    def test_validation_directory_exists(self):
        """Validation directory should exist."""
        validation_dir = PARENT_DIR / "2_VALIDATION_FIXING"
        assert validation_dir.exists()

    def test_validate_doc_id_coverage_exists(self):
        """Coverage validator file should exist."""
        validator_path = PARENT_DIR / "2_VALIDATION_FIXING" / "validate_doc_id_coverage.py"
        assert validator_path.exists()

    def test_validate_doc_id_sync_exists(self):
        """Sync validator file should exist."""
        validator_path = PARENT_DIR / "2_VALIDATION_FIXING" / "validate_doc_id_sync.py"
        assert validator_path.exists()

    def test_validate_doc_id_uniqueness_exists(self):
        """Uniqueness validator file should exist."""
        validator_path = PARENT_DIR / "2_VALIDATION_FIXING" / "validate_doc_id_uniqueness.py"
        assert validator_path.exists()


class TestAutomationModules:
    """Test all automation modules in 3_AUTOMATION_HOOKS."""

    def test_automation_directory_exists(self):
        """Automation directory should exist."""
        automation_dir = PARENT_DIR / "3_AUTOMATION_HOOKS"
        assert automation_dir.exists()

    def test_pre_commit_hook_exists(self):
        """Pre-commit hook file should exist."""
        hook_path = PARENT_DIR / "3_AUTOMATION_HOOKS" / "pre_commit_hook.py"
        assert hook_path.exists()

    def test_file_watcher_exists(self):
        """File watcher file should exist."""
        watcher_path = PARENT_DIR / "3_AUTOMATION_HOOKS" / "file_watcher.py"
        assert watcher_path.exists()


class TestReportingModules:
    """Test all reporting modules in 4_REPORTING_MONITORING."""

    def test_reporting_directory_exists(self):
        """Reporting directory should exist."""
        reporting_dir = PARENT_DIR / "4_REPORTING_MONITORING"
        assert reporting_dir.exists()


class TestRegistryModules:
    """Test all registry modules in 5_REGISTRY_DATA."""

    def test_registry_directory_exists(self):
        """Registry directory should exist."""
        registry_dir = PARENT_DIR / "5_REGISTRY_DATA"
        assert registry_dir.exists()

    def test_doc_id_registry_exists(self):
        """DOC_ID registry should exist."""
        registry_path = PARENT_DIR / "5_REGISTRY_DATA" / "DOC_ID_REGISTRY.yaml"
        assert registry_path.exists()

    def test_doc_id_inventory_exists(self):
        """DOC_ID inventory should exist."""
        inventory_path = PARENT_DIR / "5_REGISTRY_DATA" / "DOC_ID_INVENTORY.jsonl"
        assert inventory_path.exists()


class TestCLIModules:
    """Test CLI modules in 7_CLI_INTERFACE."""

    def test_cli_directory_exists(self):
        """CLI directory should exist."""
        cli_dir = PARENT_DIR / "7_CLI_INTERFACE"
        assert cli_dir.exists()

    def test_doc_id_cli_exists(self):
        """CLI module file should exist."""
        cli_path = PARENT_DIR / "7_CLI_INTERFACE" / "doc_id_cli.py"
        assert cli_path.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
