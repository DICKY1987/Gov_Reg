"""
Tests for field_precedence.py - Per-column transition rules

4 tests covering:
- Immutable field conflict detection
- Authoritative fields overwrite planned
- Inferred fields preserved with warning
- Authoritative vs inferred classification
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import pytest
from registry_transition import FieldPrecedence, ImmutableConflict
from registry_transition.field_precedence import classify_scan_output

def test_immutable_conflict():
    """Test ImmutableConflict raised for immutable field changes."""
    fp = FieldPrecedence()
    
    planned = {
        'record_id': 'test-001',
        'file_id': '01999000042260124001',
        'lifecycle_state': 'PLANNED'
    }
    
    scan = {
        'file_id': '01999000042260124999'  # Different!
    }
    
    with pytest.raises(ImmutableConflict) as exc_info:
        fp.apply(planned, scan, 'PLANNED_to_PRESENT')
    
    assert exc_info.value.field == 'file_id'
    assert exc_info.value.planned_value == '01999000042260124001'
    assert exc_info.value.scan_value == '01999000042260124999'

def test_authoritative_overwrites():
    """Test authoritative fields (size_bytes, sha256) overwrite planned."""
    fp = FieldPrecedence()
    
    planned = {
        'record_id': 'test-002',
        'file_id': '01999000042260124002',
        'size_bytes': None,
        'sha256': None
    }
    
    scan = {
        'size_bytes': 2048,
        'sha256': 'abc123def456',
        'mtime_utc': '2026-01-30T06:00:00Z'
    }
    
    result = fp.apply(planned, scan, 'PLANNED_to_PRESENT')
    
    assert result['size_bytes'] == 2048
    assert result['sha256'] == 'abc123def456'
    assert result['mtime_utc'] == '2026-01-30T06:00:00Z'

def test_inferred_preserved_with_warning():
    """Test inferred fields (artifact_kind) preserved, warning emitted."""
    fp = FieldPrecedence()
    
    planned = {
        'record_id': 'test-003',
        'file_id': '01999000042260124003',
        'artifact_kind': 'source_code'
    }
    
    scan = {
        'artifact_kind': 'test_code'  # Different inference
    }
    
    result = fp.apply(planned, scan, 'PLANNED_to_PRESENT')
    
    # Planned value should be preserved
    assert result['artifact_kind'] == 'source_code'
    
    # Warning should be emitted (check file exists)
    warnings_file = Path('.state/evidence/warnings.jsonl')
    assert warnings_file.exists()

def test_split_authoritative_vs_inferred():
    """Test classify_scan_output splits fields correctly."""
    scan_data = {
        'size_bytes': 1024,
        'sha256': 'xyz789',
        'mtime_utc': '2026-01-30T06:00:00Z',
        'last_seen_utc': '2026-01-30T06:11:00Z',
        'artifact_kind': 'test',
        'layer': 'infra',
        'language': 'python',
        'framework': 'pytest'
    }
    
    authoritative, inferred = classify_scan_output(scan_data)
    
    # Authoritative should be measurable facts
    assert 'size_bytes' in authoritative
    assert 'sha256' in authoritative
    assert 'mtime_utc' in authoritative
    assert 'last_seen_utc' in authoritative
    
    # Inferred should be interpretations
    assert 'artifact_kind' in inferred
    assert 'layer' in inferred
    assert 'language' in inferred
    assert 'framework' in inferred
