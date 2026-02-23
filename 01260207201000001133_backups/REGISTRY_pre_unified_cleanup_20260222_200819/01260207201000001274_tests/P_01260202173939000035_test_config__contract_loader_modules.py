"""
Tests for TASK-001: config/ contract loader modules
"""

import pytest
import sys
from pathlib import Path

# Add parent dirs to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import column_dictionary_loader, write_policy_loader, derivations_loader
from config.registry_paths import (
    REGISTRY_PATH, BACKUP_DIR, SCHEMA_PATH, WRITE_POLICY_PATH,
    DERIVATIONS_PATH, COLUMN_DICTIONARY_PATH, EVIDENCE_DIR
)


def test_column_dictionary_loader_returns_147_headers():
    """column_dictionary_loader.load() returns dict with 147 headers"""
    column_dict = column_dictionary_loader.load()
    assert "headers" in column_dict
    assert len(column_dict["headers"]) == 147
    assert column_dict.get("header_count_expected") == 147


def test_column_dictionary_get_header_definition():
    """Can retrieve specific header definitions"""
    header_def = column_dictionary_loader.get_header_definition("record_kind")
    assert header_def is not None
    assert "value_schema" in header_def
    assert "normalization" in header_def


def test_write_policy_loader_returns_columns():
    """write_policy_loader.load() returns dict with all column policies"""
    write_policy = write_policy_loader.load()
    assert "columns" in write_policy
    assert len(write_policy["columns"]) > 0


def test_write_policy_get_column_policy():
    """Can retrieve specific column policies"""
    policy = write_policy_loader.get_column_policy("record_kind")
    assert policy is not None
    assert "update_policy" in policy or "null_policy" in policy


def test_derivations_loader_returns_formulas():
    """derivations_loader.load() returns dict with all formulas"""
    derivations = derivations_loader.load()
    assert "derived_columns" in derivations


def test_registry_paths_exports_required_paths():
    """registry_paths.py exports all required paths"""
    assert REGISTRY_PATH.exists()
    assert COLUMN_DICTIONARY_PATH.exists()
    assert WRITE_POLICY_PATH.exists()
    assert DERIVATIONS_PATH.exists()
    assert BACKUP_DIR.exists()
    assert EVIDENCE_DIR.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
