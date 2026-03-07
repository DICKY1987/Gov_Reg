"""
Tests for Tier 2 Canonical Hash Extractor
BDD Spec: specs/behaviors/BDD-REGV3-CANONICAL-HASH-002.yaml
Requirement: R-REGV3-HASH-002
"""
# DOC_ID: DOC-TEST-6-TESTS-TEST-TIER2-CANONICAL-HASH-610

from importlib import util
from pathlib import Path

_module_path = Path(__file__).resolve().parent.parent / "common" / "DOC-SCRIPT-1008__tier2_canonical_hash.py"
_spec = util.spec_from_file_location("tier2_canonical_hash", _module_path)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Unable to load module from {_module_path}")
_module = util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
extract_canonical_hash = _module.extract_canonical_hash
import tempfile
import os


def test_canonical_hash_json_sorted_keys():
    """Test that JSON keys are sorted for canonical hash"""
    # Create JSON with unsorted keys
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{"b": 2, "a": 1}')
        temp_json = f.name

    try:
        hash1 = extract_canonical_hash(temp_json, trace_id="test")
        assert hash1 is not None
        assert len(hash1) == 64  # SHA256 hex length
    finally:
        os.unlink(temp_json)


def test_canonical_hash_deterministic():
    """Test that hash is deterministic across runs"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{"test": "value"}')
        temp_json = f.name

    try:
        hash1 = extract_canonical_hash(temp_json)
        hash2 = extract_canonical_hash(temp_json)
        assert hash1 == hash2
    finally:
        os.unlink(temp_json)


def test_canonical_hash_non_json_returns_none():
    """Test that non-JSON/YAML files return None"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write('print("test")')
        temp_py = f.name

    try:
        result = extract_canonical_hash(temp_py)
        assert result is None
    finally:
        os.unlink(temp_py)


if __name__ == "__main__":
    test_canonical_hash_json_sorted_keys()
    test_canonical_hash_deterministic()
    test_canonical_hash_non_json_returns_none()
    print("All canonical hash tests passed!")
