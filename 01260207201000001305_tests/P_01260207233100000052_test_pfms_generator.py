"""
Tests for PFMS Generator - Mutation Set Creation
"""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from govreg_core.pfms_generator import PFMSGenerator


def test_mutation_set_dual_identity():
    """Test from spec Section 0.2: Dual identity (ID + content_hash)."""
    generator = PFMSGenerator()

    mutations = {
        "created_files": [{"relative_path": "src/a.py", "content": "..."}]
    }

    # Create twice (different runs)
    pfms1 = generator.create_mutation_set(mutations, "PLAN-001")
    pfms2 = generator.create_mutation_set(mutations, "PLAN-001")

    # Different IDs (instance identity)
    assert pfms1['mutation_set_id'] != pfms2['mutation_set_id']

    # Same content hash (semantic identity)
    assert pfms1['content_hash'] == pfms2['content_hash']

    # Comparison uses content_hash
    assert generator.are_mutation_sets_identical(pfms1, pfms2) is True


def test_different_mutations_different_hash():
    """Test: Different mutations produce different content_hash."""
    generator = PFMSGenerator()

    mutations1 = {
        "created_files": [{"relative_path": "src/a.py"}]
    }

    mutations2 = {
        "created_files": [{"relative_path": "src/b.py"}]
    }

    pfms1 = generator.create_mutation_set(mutations1, "PLAN-001")
    pfms2 = generator.create_mutation_set(mutations2, "PLAN-002")

    assert pfms1['content_hash'] != pfms2['content_hash']
    assert generator.are_mutation_sets_identical(pfms1, pfms2) is False


def test_canonicalization_order_independence():
    """Test: File order doesn't affect content_hash."""
    generator = PFMSGenerator()

    mutations1 = {
        "created_files": [
            {"relative_path": "src/a.py"},
            {"relative_path": "src/b.py"}
        ]
    }

    mutations2 = {
        "created_files": [
            {"relative_path": "src/b.py"},
            {"relative_path": "src/a.py"}
        ]
    }

    pfms1 = generator.create_mutation_set(mutations1, "PLAN-001")
    pfms2 = generator.create_mutation_set(mutations2, "PLAN-001")

    # Content hash should match (canonicalized)
    assert pfms1['content_hash'] == pfms2['content_hash']


def test_mutation_set_structure():
    """Test: PFMS has required fields."""
    generator = PFMSGenerator()

    mutations = {
        "created_files": [{"relative_path": "src/a.py"}],
        "modified_files": [],
        "deleted_files": []
    }

    pfms = generator.create_mutation_set(mutations, "PLAN-001")

    # Required fields
    assert 'mutation_set_id' in pfms
    assert 'content_hash' in pfms
    assert 'plan_id' in pfms
    assert 'mutations' in pfms
    assert 'created_at' in pfms
    assert 'schema_version' in pfms

    # Field types
    assert len(pfms['mutation_set_id']) == 20, "20-digit ID"
    assert len(pfms['content_hash']) == 64, "SHA256 hex (64 chars)"
    assert pfms['schema_version'] == '1.2.0'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
