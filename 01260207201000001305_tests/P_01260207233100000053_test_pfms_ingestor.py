"""
Tests for pfms_ingestor - PFMS Ingestion Pipeline
"""

import pytest
import tempfile
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from govreg_core.pfms_ingestor import PFMSIngestor
from govreg_core.registry_writer import RegistryWriter
from govreg_core.pfms_generator import PFMSGenerator
from govreg_core.feature_flags import FeatureFlags, MigrationPhase


@pytest.fixture
def temp_registry(tmp_path):
    """Create temporary registry."""
    registry_path = tmp_path / "registry.json"

    initial_data = {
        "files": [],
        "schema_version": "v3"
    }

    with open(registry_path, 'w') as f:
        json.dump(initial_data, f)

    return RegistryWriter(str(registry_path))


@pytest.fixture
def enable_phase3(tmp_path):
    """Enable Phase 3 for testing."""
    flags_path = tmp_path / "feature_flags.json"
    flags = FeatureFlags(str(flags_path))
    flags.set_phase(MigrationPhase.PHASE_3_REGISTRY)
    return flags


def test_ingest_created_file(temp_registry, enable_phase3, tmp_path):
    """Test: Ingest created file into registry."""
    # Create test file
    test_file = tmp_path / "src" / "test.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("print('hello')")

    # Create PFMS
    generator = PFMSGenerator()
    mutations = {
        "created_files": [{
            "relative_path": str(test_file),
            "artifact_kind": "PYTHON_MODULE",
            "layer": "CORE",
            "file_id": "01999000042260124001"
        }]
    }
    pfms = generator.create_mutation_set(mutations, "PLAN-001")

    # Ingest
    ingestor = PFMSIngestor(temp_registry)
    ingestor.flags = enable_phase3
    report = ingestor.ingest_pfms(pfms)

    # Check report
    assert len(report['ingested_files']) == 1
    assert len(report['failed_files']) == 0

    # Check registry entry created
    entry = temp_registry.read_registry_entry("01999000042260124001")
    assert entry is not None
    assert entry['relative_path'] == str(test_file)
    assert entry['content_hash'] is not None  # File exists, hash computed
    assert entry['source_plan_id'] == 'PLAN-001'


def test_ingest_modified_file(temp_registry, enable_phase3, tmp_path):
    """Test: Ingest modified file into registry."""
    # Create initial entry
    test_file = tmp_path / "src" / "test.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("print('old')")

    initial_entry = {
        'file_id': '01999000042260124001',
        'relative_path': str(test_file),
        'artifact_kind': 'PYTHON_MODULE',
        'layer': 'CORE',
        'content_hash': 'old_hash'
    }
    temp_registry.create_registry_entry(initial_entry)

    # Modify file
    test_file.write_text("print('new')")

    # Create PFMS for modification
    generator = PFMSGenerator()
    mutations = {
        "modified_files": [{
            "relative_path": str(test_file)
        }]
    }
    pfms = generator.create_mutation_set(mutations, "PLAN-002")

    # Ingest
    ingestor = PFMSIngestor(temp_registry)
    ingestor.flags = enable_phase3
    report = ingestor.ingest_pfms(pfms)

    # Check report
    assert len(report['ingested_files']) == 1

    # Check entry updated
    entry = temp_registry.read_registry_entry("01999000042260124001")
    assert entry['content_hash'] != 'old_hash'  # New hash
    assert entry['previous_content_hash'] == 'old_hash'  # History preserved
    assert entry['source_plan_id'] == 'PLAN-002'
    assert len(entry['modification_history']) == 1


def test_phase3_not_active_raises_error(temp_registry, tmp_path):
    """Test: Ingestion fails if Phase 3 not active."""
    flags_path = tmp_path / "feature_flags.json"
    flags = FeatureFlags(str(flags_path))
    flags.set_phase(MigrationPhase.PHASE_1_FOUNDATION)  # Not Phase 3

    generator = PFMSGenerator()
    mutations = {"created_files": []}
    pfms = generator.create_mutation_set(mutations, "PLAN-001")

    ingestor = PFMSIngestor(temp_registry)
    ingestor.flags = flags

    with pytest.raises(RuntimeError, match="Phase 3 not active"):
        ingestor.ingest_pfms(pfms)


def test_ingest_moved_file(temp_registry, enable_phase3, tmp_path):
    """Test: Ingest moved file into registry."""
    # Create initial entry
    old_path = tmp_path / "src" / "old.py"
    old_path.parent.mkdir(parents=True)
    old_path.write_text("print('test')")

    initial_entry = {
        'file_id': '01999000042260124001',
        'relative_path': str(old_path),
        'artifact_kind': 'PYTHON_MODULE',
        'layer': 'CORE'
    }
    temp_registry.create_registry_entry(initial_entry)

    # Create PFMS for move
    new_path = tmp_path / "src" / "new.py"
    generator = PFMSGenerator()
    mutations = {
        "moved_files": [{
            "old_path": str(old_path),
            "new_path": str(new_path)
        }]
    }
    pfms = generator.create_mutation_set(mutations, "PLAN-003")

    # Ingest
    ingestor = PFMSIngestor(temp_registry)
    ingestor.flags = enable_phase3
    report = ingestor.ingest_pfms(pfms)

    # Check report
    assert len(report['ingested_files']) == 1

    # Check entry updated
    entry = temp_registry.read_registry_entry("01999000042260124001")
    assert entry['relative_path'] == str(new_path)
    assert entry['source_plan_id'] == 'PLAN-003'


def test_ingest_deleted_file(temp_registry, enable_phase3, tmp_path):
    """Test: Ingest deleted file (marks as deleted, doesn't remove)."""
    # Create initial entry
    test_file = tmp_path / "src" / "test.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("print('test')")

    initial_entry = {
        'file_id': '01999000042260124001',
        'relative_path': str(test_file),
        'artifact_kind': 'PYTHON_MODULE',
        'layer': 'CORE'
    }
    temp_registry.create_registry_entry(initial_entry)

    # Create PFMS for deletion
    generator = PFMSGenerator()
    mutations = {
        "deleted_files": [{
            "relative_path": str(test_file)
        }]
    }
    pfms = generator.create_mutation_set(mutations, "PLAN-004")

    # Ingest
    ingestor = PFMSIngestor(temp_registry)
    ingestor.flags = enable_phase3
    report = ingestor.ingest_pfms(pfms)

    # Check report
    assert len(report['ingested_files']) == 1

    # Check entry still exists but marked as deleted
    entry = temp_registry.read_registry_entry("01999000042260124001")
    assert entry is not None  # Still exists
    assert 'deleted_at' in entry  # Marked as deleted
    assert entry['deleted_by_plan_id'] == 'PLAN-004'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
