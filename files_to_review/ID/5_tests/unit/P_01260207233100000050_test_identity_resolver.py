"""
Tests for identity_resolver.py - 4-step matching algorithm

6 tests covering:
- Exact path matching
- Rename-intent matching
- Strong identity (file_id extraction)
- No match → orphaned
- Multi-match → conflict
- Batch resolution
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import pytest
from registry_transition import IdentityResolver, ConflictKind

@pytest.fixture
def planned_records():
    """Sample planned records for testing."""
    return [
        {
            'record_id': 'rec-001',
            'file_id': '01999000042260124001',
            'canonical_path': 'src/exact.py',
            'path_history': [],
            'path_aliases': []
        },
        {
            'record_id': 'rec-002',
            'file_id': '01999000042260124002',
            'canonical_path': 'src/renamed.py',
            'path_history': ['src/old_name.py'],
            'path_aliases': []
        },
        {
            'record_id': 'rec-003',
            'file_id': '01999000042260124003',
            'canonical_path': 'src/module.py',
            'path_history': [],
            'path_aliases': []
        }
    ]

def test_exact_path(planned_records):
    """Test Step 1: Exact path matching."""
    resolver = IdentityResolver(planned_records)
    
    observed = [{'observed_path': 'src/exact.py'}]
    results = resolver.resolve_batch(observed)
    
    assert len(results) == 1
    assert results[0].match_kind == 'exact_path'
    assert results[0].matched_record_id == 'rec-001'

def test_rename_intent(planned_records):
    """Test Step 2: Rename-intent via path_history."""
    resolver = IdentityResolver(planned_records)
    
    observed = [{'observed_path': 'src/old_name.py'}]
    results = resolver.resolve_batch(observed)
    
    assert len(results) == 1
    assert results[0].match_kind == 'rename_intent'
    assert results[0].matched_record_id == 'rec-002'

def test_strong_identity(planned_records):
    """Test Step 3: Strong identity via file_id extraction."""
    resolver = IdentityResolver(planned_records)
    
    observed = [{'observed_path': 'src/P_01999000042260124003_module.py'}]
    results = resolver.resolve_batch(observed)
    
    assert len(results) == 1
    assert results[0].match_kind == 'strong_identity'
    assert results[0].matched_record_id == 'rec-003'

def test_no_match_orphaned(planned_records):
    """Test Step 4: No match → orphaned."""
    resolver = IdentityResolver(planned_records)
    
    observed = [{'observed_path': 'unknown/orphan.py'}]
    results = resolver.resolve_batch(observed)
    
    assert len(results) == 1
    assert results[0].match_kind == 'orphaned'
    assert results[0].matched_record_id is None

def test_multi_match_conflict(planned_records):
    """Test conflict detection for multiple matches."""
    # Add duplicate canonical path
    planned_records.append({
        'record_id': 'rec-004',
        'file_id': '01999000042260124004',
        'canonical_path': 'src/exact.py',  # Duplicate!
        'path_history': [],
        'path_aliases': []
    })
    
    resolver = IdentityResolver(planned_records)
    
    observed = [{'observed_path': 'src/exact.py'}]
    results = resolver.resolve_batch(observed)
    
    assert len(results) == 1
    assert results[0].match_kind == 'conflict'
    assert results[0].conflict_kind == ConflictKind.MULTI_MATCH
    assert len(results[0].candidates) == 2

def test_batch_resolution(planned_records):
    """Test batch resolution with mixed outcomes."""
    resolver = IdentityResolver(planned_records)
    
    observed = [
        {'observed_path': 'src/exact.py'},       # Match
        {'observed_path': 'src/old_name.py'},    # Rename
        {'observed_path': 'unknown/file.py'},    # Orphan
    ]
    
    results = resolver.resolve_batch(observed)
    
    assert len(results) == 3
    assert results[0].match_kind == 'exact_path'
    assert results[1].match_kind == 'rename_intent'
    assert results[2].match_kind == 'orphaned'
