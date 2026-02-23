"""
Tests for state_machine.py - Contract loader and transition enforcer

6 tests covering:
- Contract YAML loading
- Happy path transitions
- Blocked transitions (missing conditions)
- Invalid skip transitions
- Quarantine escapes
- Available transitions lookup
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import pytest
from registry_transition import StateMachine, TransitionResult

def test_load_contract_yaml(contract_path):
    """Test loading transition contract from YAML."""
    sm = StateMachine(contract_path)
    
    assert sm.contract is not None
    assert len(sm.transitions) == 8
    assert 'PLANNED_to_PRESENT' in sm.transitions
    assert 'any_to_CONFLICT' in sm.transitions

def test_planned_to_present_happy(contract_path):
    """Test successful PLANNED → PRESENT transition."""
    sm = StateMachine(contract_path)
    
    record = {
        'record_id': 'test-001',
        'lifecycle_state': 'PLANNED',
        'identity_resolved': True,
        'no_conflicts': True
    }
    
    result = sm.transition(record, 'PRESENT', 'PLANNED_to_PRESENT')
    
    assert result.success is True
    assert result.from_state == 'PLANNED'
    assert result.to_state == 'PRESENT'
    assert result.transition_name == 'PLANNED_to_PRESENT'
    assert len(result.errors) == 0

def test_blocked_missing_condition(contract_path):
    """Test transition blocked by missing condition."""
    sm = StateMachine(contract_path)
    
    record = {
        'record_id': 'test-002',
        'lifecycle_state': 'PLANNED',
        'identity_resolved': False,  # Missing!
        'no_conflicts': True
    }
    
    result = sm.transition(record, 'PRESENT', 'PLANNED_to_PRESENT')
    
    assert result.success is False
    assert len(result.errors) > 0
    assert 'identity_resolved' in result.errors[0]

def test_skip_rejected(contract_path):
    """Test invalid state skip is rejected."""
    sm = StateMachine(contract_path)
    
    record = {
        'record_id': 'test-003',
        'lifecycle_state': 'PLANNED'
    }
    
    # Try to skip PRESENT and go directly to DELETED
    result = sm.transition(record, 'DELETED')
    
    assert result.success is False
    assert 'No valid transition' in result.errors[0]

def test_quarantine_escape(contract_path):
    """Test escape from quarantine state."""
    sm = StateMachine(contract_path)
    
    # ORPHANED → PLANNED
    record = {
        'record_id': 'test-004',
        'lifecycle_state': 'ORPHANED',
        'manual_reclassification': True
    }
    
    result = sm.transition(record, 'PLANNED', 'ORPHANED_to_PLANNED')
    
    assert result.success is True
    assert result.to_state == 'PLANNED'

def test_available_transitions(contract_path):
    """Test available transitions lookup."""
    sm = StateMachine(contract_path)
    
    record = {
        'record_id': 'test-005',
        'lifecycle_state': 'PLANNED'
    }
    
    available = sm.available_transitions(record)
    
    assert 'PLANNED_to_PRESENT' in available
    assert 'PLANNED_to_DEPRECATED' in available
    assert 'any_to_ORPHANED' in available
    assert 'any_to_CONFLICT' in available
    
    # Should not include transitions from other states
    assert 'PRESENT_to_DEPRECATED' not in available
