"""
Tests for reconciliation - PFMS vs Reality
"""

import pytest
import tempfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from govreg_core.reconciliation import Reconciliation, reconcile_pfms
from govreg_core.pfms_generator import PFMSGenerator
from govreg_core.registry_schema_v3 import ReconciliationState


def test_exact_match(tmp_path):
    """Test: All files match - EXACT_MATCH."""
    reconciler = Reconciliation()
    
    # Create test files
    test_file = tmp_path / "src" / "test.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("print('hello')")
    
    # Create PFMS (without expected_content_hash for now)
    generator = PFMSGenerator()
    mutations = {
        "created_files": [{
            "relative_path": str(test_file)
        }]
    }
    pfms = generator.create_mutation_set(mutations, "PLAN-001")
    
    # Reconcile
    report = reconciler.reconcile_pfms_with_reality(pfms)
    
    # Should be EXACT_MATCH or SUBSET_MATCH (no expected hash provided)
    assert report['reconciliation_state'] in ['EXACT_MATCH', 'SUBSET_MATCH']
    assert report['missing_files'] == 0


def test_missing_file_no_overlap(tmp_path):
    """Test: All files missing - NO_OVERLAP (critical)."""
    reconciler = Reconciliation()
    
    # Create PFMS for non-existent file
    generator = PFMSGenerator()
    mutations = {
        "created_files": [{
            "relative_path": str(tmp_path / "nonexistent.py")
        }]
    }
    pfms = generator.create_mutation_set(mutations, "PLAN-001")
    
    # Reconcile
    report = reconciler.reconcile_pfms_with_reality(pfms)
    
    # Should be NO_OVERLAP
    assert report['reconciliation_state'] == ReconciliationState.NO_OVERLAP.value
    assert report['missing_files'] == 1
    assert report['exact_matches'] == 0


def test_partial_overlap(tmp_path):
    """Test: Some files match, some missing - PARTIAL_OVERLAP."""
    reconciler = Reconciliation()
    
    # Create one file
    test_file1 = tmp_path / "src" / "a.py"
    test_file1.parent.mkdir(parents=True)
    test_file1.write_text("print('a')")
    
    # Don't create second file
    test_file2 = tmp_path / "src" / "b.py"
    
    # Create PFMS
    generator = PFMSGenerator()
    mutations = {
        "created_files": [
            {"relative_path": str(test_file1)},
            {"relative_path": str(test_file2)}
        ]
    }
    pfms = generator.create_mutation_set(mutations, "PLAN-001")
    
    # Reconcile
    report = reconciler.reconcile_pfms_with_reality(pfms)
    
    # Should be PARTIAL_OVERLAP or SUBSET_MATCH
    assert report['reconciliation_state'] in ['PARTIAL_OVERLAP', 'SUBSET_MATCH']
    assert report['missing_files'] == 1
    assert report['exact_matches'] >= 0


def test_empty_mutations():
    """Test: Empty mutations - EXACT_MATCH."""
    reconciler = Reconciliation()
    
    generator = PFMSGenerator()
    mutations = {"created_files": [], "modified_files": []}
    pfms = generator.create_mutation_set(mutations, "PLAN-001")
    
    report = reconciler.reconcile_pfms_with_reality(pfms)
    
    assert report['reconciliation_state'] == ReconciliationState.EXACT_MATCH.value
    assert report['total_planned'] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
