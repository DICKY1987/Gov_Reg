"""
TASK-015: End-to-End Integration Tests
"""

import pytest
import json
import sys
from pathlib import Path
from typing import Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.registry_writer.normalizer import Normalizer
from src.registry_writer.write_policy_validator import WritePolicyValidator
from src.registry_writer.backup_manager import BackupManager
from govreg_core.P_01999000042260125006_id_allocator_facade import IDAllocator


@pytest.fixture
def sample_record():
    return {
        "file_id": "01999000042260124999",
        "relative_path": "test\\file.py",
        "record_kind": "ENTITY",
        "entity_kind": "FILE",
        "extension": ".py"
    }


def test_normalizer_pipeline(sample_record):
    """Test normalizer applies transforms correctly."""
    normalizer = Normalizer()
    normalized = normalizer.normalize_record(sample_record)

    assert normalized["record_kind"] == "entity"  # LOWERCASE
    assert normalized["entity_kind"] == "file"  # LOWERCASE
    assert normalized["extension"] == "py"  # no dot, lowercase
    assert "/" in normalized["relative_path"]  # forward slashes


def test_write_policy_validator_immutable():
    """Test write policy validator enforces immutable fields."""
    validator = WritePolicyValidator()

    patch = {"record_kind": "edge"}
    old_record = {"record_kind": "entity"}

    is_valid, violations = validator.validate_patch(patch, old_record, actor="manual")

    assert not is_valid
    assert len(violations) > 0
    assert violations[0]["rule"] == "immutable"


def test_backup_manager_creates_backup(tmp_path):
    """Test backup manager creates valid backups."""
    registry_file = tmp_path / "registry.json"
    backup_dir = tmp_path / "backups"

    registry_file.write_text(json.dumps({"test": "data"}))

    mgr = BackupManager(registry_file, backup_dir)
    backup_path = mgr.create_backup()

    assert backup_path.exists()
    assert mgr.verify_backup(backup_path)


def test_id_allocator_generates_unique_ids(tmp_path):
    """Test ID allocator generates unique 20-digit IDs."""
    registry_file = tmp_path / "registry.json"
    registry_file.write_text(json.dumps({"files": []}))

    allocator = IDAllocator(registry_file)
    allocator.load_registry()

    id1 = allocator.allocate_id()
    id2 = allocator.allocate_id()

    assert len(id1) == 20
    assert len(id2) == 20
    assert id1 != id2
    assert id1.startswith("01999")


def test_e2e_add_new_file_record(tmp_path):
    """E2E: Add new file record with full pipeline."""
    registry_file = tmp_path / "registry.json"
    registry_file.write_text(json.dumps({
        "files": [],
        "column_headers": {}
    }))

    normalizer = Normalizer()
    validator = WritePolicyValidator()
    allocator = IDAllocator(registry_file)

    # New record
    new_record = {
        "record_kind": "ENTITY",
        "entity_kind": "FILE",
        "relative_path": "src\\test.py",
        "extension": ".py"
    }

    # Normalize
    normalized = normalizer.normalize_record(new_record)

    # Validate (no old record = new)
    is_valid, violations = validator.validate_patch(normalized, None, actor="tool")
    assert is_valid, f"Validation failed: {violations}"

    # Allocate ID
    allocator.load_registry()
    file_id = allocator.allocate_id()
    normalized["file_id"] = file_id

    # Verify
    assert normalized["record_kind"] == "entity"
    assert normalized["extension"] == "py"
    assert len(file_id) == 20


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
