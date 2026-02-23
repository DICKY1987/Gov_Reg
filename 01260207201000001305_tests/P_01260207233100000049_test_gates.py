"""
Tests for gates.py - Completeness and Validity checks

4 tests covering:
- Completeness gate pass
- Completeness gate fail
- Validity gate pass
- Validity gate fail
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import pytest
import json
from registry_transition import CompletenessGate, ValidityGate

def test_completeness_pass(tmp_path):
    """Test completeness gate passes with all records PRESENT."""
    registry_path = tmp_path / "registry.json"
    registry_data = [
        {
            'record_id': 'rec-001',
            'lifecycle_state': 'PRESENT',
            'planned_by_phase_id': 'PH-TEST',
            'required': True,
            'canonical_path': 'src/test1.py'
        },
        {
            'record_id': 'rec-002',
            'lifecycle_state': 'PRESENT',
            'planned_by_phase_id': 'PH-TEST',
            'required': True,
            'canonical_path': 'src/test2.py'
        }
    ]
    
    with open(registry_path, 'w', encoding='utf-8') as f:
        json.dump(registry_data, f)
    
    gate = CompletenessGate(registry_path)
    report = gate.check('PH-TEST')
    
    assert report['pass'] is True
    assert report['exit_code'] == 0
    assert report['summary']['complete'] == 2
    assert report['summary']['incomplete'] == 0

def test_completeness_fail(tmp_path):
    """Test completeness gate fails with incomplete records."""
    registry_path = tmp_path / "registry.json"
    registry_data = [
        {
            'record_id': 'rec-001',
            'lifecycle_state': 'PRESENT',
            'planned_by_phase_id': 'PH-TEST',
            'required': True,
            'canonical_path': 'src/test1.py'
        },
        {
            'record_id': 'rec-002',
            'lifecycle_state': 'PLANNED',  # Still planned!
            'planned_by_phase_id': 'PH-TEST',
            'required': True,
            'canonical_path': 'src/test2.py'
        }
    ]
    
    with open(registry_path, 'w', encoding='utf-8') as f:
        json.dump(registry_data, f)
    
    gate = CompletenessGate(registry_path)
    report = gate.check('PH-TEST')
    
    assert report['pass'] is False
    assert report['exit_code'] == 10
    assert report['summary']['complete'] == 1
    assert report['summary']['incomplete'] == 1
    assert len(report['incomplete_records']) == 1

def test_validity_pass(tmp_path):
    """Test validity gate passes with valid registry."""
    registry_path = tmp_path / "registry.json"
    registry_data = [
        {
            'record_id': 'rec-001',
            'file_id': '01999000042260124001',
            'created_utc': '2026-01-30T00:00:00Z',
            'canonical_path': 'src/test.py',
            'lifecycle_state': 'PRESENT',
            'depends_on_file_ids': []
        }
    ]
    
    with open(registry_path, 'w', encoding='utf-8') as f:
        json.dump(registry_data, f)
    
    gate = ValidityGate(registry_path)
    report = gate.check()
    
    assert report['pass'] is True
    assert report['exit_code'] == 0
    assert len(report['violations']) == 0

def test_validity_fail(tmp_path):
    """Test validity gate fails with missing immutable fields."""
    registry_path = tmp_path / "registry.json"
    registry_data = [
        {
            'record_id': 'rec-001',
            'file_id': None,  # Missing immutable field!
            'created_utc': None,  # Missing immutable field!
            'canonical_path': 'src/test.py',
            'lifecycle_state': 'PRESENT'
        }
    ]
    
    with open(registry_path, 'w', encoding='utf-8') as f:
        json.dump(registry_data, f)
    
    gate = ValidityGate(registry_path)
    report = gate.check()
    
    assert report['pass'] is False
    assert report['exit_code'] == 11
    assert len(report['violations']) >= 2  # file_id and created_utc
    
    # Check violation types
    violation_types = [v['type'] for v in report['violations']]
    assert 'missing_immutable' in violation_types
