"""
Unit tests for canonical_hash module.

Tests:
- Determinism (same input → same hash)
- Key order independence
- Content changes detection
- File hashing
"""

import pytest
import tempfile
from pathlib import Path
import sys
import os

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from govreg_core.canonical_hash import (
    hash_canonical_data,
    hash_file_content,
    verify_determinism
)


def test_hash_determinism():
    """Test: Same input produces same hash."""
    data = {"key": "value", "list": [1, 2, 3]}

    hash1 = hash_canonical_data(data)
    hash2 = hash_canonical_data(data)

    assert hash1 == hash2, "Hash must be deterministic"
    assert len(hash1) == 64, "SHA256 hash must be 64 hex chars"


def test_key_order_independence():
    """Test: Dict key order doesn't affect hash."""
    data1 = {"key": "value", "list": [1, 2, 3]}
    data2 = {"list": [1, 2, 3], "key": "value"}

    hash1 = hash_canonical_data(data1)
    hash2 = hash_canonical_data(data2)

    assert hash1 == hash2, "Hash must be key-order independent"


def test_content_sensitivity():
    """Test: Different content produces different hash."""
    data1 = {"key": "value1"}
    data2 = {"key": "value2"}

    hash1 = hash_canonical_data(data1)
    hash2 = hash_canonical_data(data2)

    assert hash1 != hash2, "Different content must produce different hash"


def test_nested_structures():
    """Test: Nested dicts and lists hash correctly."""
    data = {
        "nested": {
            "deep": {
                "value": 123
            }
        },
        "list": [{"a": 1}, {"b": 2}]
    }

    hash1 = hash_canonical_data(data)
    hash2 = hash_canonical_data(data)

    assert hash1 == hash2, "Nested structures must hash deterministically"


def test_file_content_hashing():
    """Test: File content hashing works."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("test content\n")
        temp_path = f.name

    try:
        path = Path(temp_path)
        hash1 = hash_file_content(path)
        hash2 = hash_file_content(path)

        assert hash1 == hash2, "File hash must be deterministic"
        assert len(hash1) == 64, "SHA256 hash must be 64 hex chars"
    finally:
        os.unlink(temp_path)


def test_file_not_found():
    """Test: Non-existent file raises FileNotFoundError."""
    path = Path("nonexistent_file_12345.txt")

    with pytest.raises(FileNotFoundError):
        hash_file_content(path)


def test_verify_determinism():
    """Test: Determinism verification works."""
    data = {"test": "data"}
    expected_hash = hash_canonical_data(data)

    assert verify_determinism(data, expected_hash) is True
    assert verify_determinism(data, "wrong_hash") is False


def test_mutation_set_comparison_example():
    """Test: Example from spec - mutation set comparison."""
    mutations = {
        "created_files": [
            {"relative_path": "src/a.py", "content": "print('hello')"}
        ],
        "modified_files": [],
        "deleted_files": []
    }

    # Same mutations, different runs
    content_hash_1 = hash_canonical_data(mutations)
    content_hash_2 = hash_canonical_data(mutations)

    # Content hash must match (for reproducibility)
    assert content_hash_1 == content_hash_2

    # Different mutations
    mutations_different = {
        "created_files": [
            {"relative_path": "src/b.py", "content": "print('world')"}
        ],
        "modified_files": [],
        "deleted_files": []
    }

    content_hash_3 = hash_canonical_data(mutations_different)
    assert content_hash_1 != content_hash_3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
