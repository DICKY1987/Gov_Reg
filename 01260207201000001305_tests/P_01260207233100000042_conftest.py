"""
Shared pytest fixtures for registry transition tests.

Provides:
- repo_root: Path to repository root
- registry_path: Path to test registry file
- write_policy_path: Path to write policy file
- contract_path: Path to transition contract file
- tmp_registry: Temporary registry for tests
- sample_planned_record: Sample planned record fixture
- sample_scan_data: Sample scan data fixture
"""
import sys
from pathlib import Path
import pytest
import json
import tempfile
import shutil

@pytest.fixture
def repo_root():
    """Repository root directory."""
    return Path(__file__).parent.parent

@pytest.fixture
def registry_path(repo_root):
    """Path to governance registry."""
    return repo_root / "REGISTRY" / "governance_registry.json"

@pytest.fixture
def write_policy_path(repo_root):
    """Path to write policy."""
    return repo_root / "REGISTRY" / "UNIFIED_SSOT_REGISTRY_WRITE_POLICY.yaml"

@pytest.fixture
def contract_path(repo_root):
    """Path to transition contract."""
    return repo_root / "transition_contract.bundle.yaml"

@pytest.fixture
def tmp_registry(tmp_path):
    """Temporary registry with minimal valid data."""
    registry_data = {
        "version": "2.0",
        "records": [
            {
                "record_id": "REC-001",
                "file_id": "01999000042260124001",
                "canonical_path": "src/test.py",
                "lifecycle_state": "PLANNED",
                "path_history": [],
                "path_aliases": []
            }
        ]
    }
    
    registry_file = tmp_path / "test_registry.json"
    with open(registry_file, 'w', encoding='utf-8') as f:
        json.dump(registry_data, f, indent=2)
    
    return registry_file

@pytest.fixture
def sample_planned_record():
    """Sample planned record."""
    return {
        "record_id": "REC-TEST-001",
        "file_id": "01999000042260124999",
        "canonical_path": "src/example.py",
        "lifecycle_state": "PLANNED",
        "path_history": ["old/path.py"],
        "path_aliases": ["alias.py"],
        "created_utc": "2026-01-30T00:00:00Z"
    }

@pytest.fixture
def sample_scan_data():
    """Sample scan data."""
    return {
        "path": "src/example.py",
        "size_bytes": 1024,
        "sha256": "abc123",
        "mtime_utc": "2026-01-30T06:00:00Z",
        "last_seen_utc": "2026-01-30T06:11:00Z",
        "artifact_kind": "source",
        "layer": "core"
    }
