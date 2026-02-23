"""
Tests for transition_integration - End-to-end integration tests

3 tests covering:
- Full batch flow (identity → transition → write)
- Conflict resolution flow
- Waiver mechanism
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import pytest
import json
from registry_transition import (
    IdentityResolver, StateMachine, FieldPrecedence,
    RegistryWriter, CompletenessGate
)

def test_full_batch_flow(tmp_path, contract_path):
    """Test complete flow: identity resolution → transition → write."""
    # Setup registry
    registry_path = tmp_path / "registry.json"
    planned_records = [
        {
            'record_id': 'rec-001',
            'file_id': '01999000042260124001',
            'canonical_path': 'src/module.py',
            'lifecycle_state': 'PLANNED',
            'path_history': [],
            'path_aliases': [],
            'created_utc': '2026-01-30T00:00:00Z',
            'identity_resolved': True,
            'no_conflicts': True
        }
    ]
    
    with open(registry_path, 'w', encoding='utf-8') as f:
        json.dump(planned_records, f)
    
    # Step 1: Identity resolution
    resolver = IdentityResolver(planned_records)
    observed = [{'observed_path': 'src/module.py'}]
    match_results = resolver.resolve_batch(observed)
    
    assert len(match_results) == 1
    assert match_results[0].match_kind == 'exact_path'
    
    # Step 2: State transition
    sm = StateMachine(contract_path)
    record = planned_records[0]
    transition_result = sm.transition(record, 'PRESENT', 'PLANNED_to_PRESENT')
    
    assert transition_result.success is True
    
    # Step 3: Write to registry
    writer = RegistryWriter(registry_path)
    write_result = writer.apply_transition_batch([transition_result])
    
    assert write_result.success is True
    assert write_result.git_sync_required is True

def test_conflict_resolution_flow(tmp_path, contract_path):
    """Test conflict detection and resolution."""
    # Setup with conflicting records
    planned_records = [
        {
            'record_id': 'rec-001',
            'file_id': '01999000042260124001',
            'canonical_path': 'src/conflict.py',
            'lifecycle_state': 'PLANNED',
            'path_history': [],
            'path_aliases': [],
            'created_utc': '2026-01-30T00:00:00Z'
        },
        {
            'record_id': 'rec-002',
            'file_id': '01999000042260124002',
            'canonical_path': 'src/conflict.py',  # Duplicate!
            'lifecycle_state': 'PLANNED',
            'path_history': [],
            'path_aliases': [],
            'created_utc': '2026-01-30T00:00:00Z'
        }
    ]
    
    # Detect conflict
    resolver = IdentityResolver(planned_records)
    observed = [{'observed_path': 'src/conflict.py'}]
    results = resolver.resolve_batch(observed)
    
    assert len(results) == 1
    assert results[0].match_kind == 'conflict'
    assert len(results[0].candidates) == 2
    
    # Transition to CONFLICT state
    sm = StateMachine(contract_path)
    record = planned_records[0]
    record['conflict_detected'] = True
    record['conflict_kind'] = 'MULTI_MATCH'
    
    conflict_transition = sm.transition(record, 'CONFLICT', 'any_to_CONFLICT')
    assert conflict_transition.success is True
    
    # After adjudication, transition to PRESENT
    record['lifecycle_state'] = 'CONFLICT'
    record['adjudication_complete'] = True
    
    resolve_transition = sm.transition(record, 'PRESENT', 'CONFLICT_to_PRESENT')
    assert resolve_transition.success is True

def test_waiver_mechanism(tmp_path):
    """Test completeness gate with waiver approval."""
    registry_path = tmp_path / "registry.json"
    registry_data = [
        {
            'record_id': 'rec-001',
            'lifecycle_state': 'PRESENT',
            'planned_by_phase_id': 'PH-TEST',
            'required': True,
            'canonical_path': 'src/required.py'
        },
        {
            'record_id': 'rec-002',
            'lifecycle_state': 'DEPRECATED',
            'planned_by_phase_id': 'PH-TEST',
            'required': True,
            'canonical_path': 'src/deprecated.py',
            'waived_by': 'architect'
        }
    ]
    
    with open(registry_path, 'w', encoding='utf-8') as f:
        json.dump(registry_data, f)
    
    # Without waiver - should fail
    gate = CompletenessGate(registry_path)
    report_no_waiver = gate.check('PH-TEST')
    
    assert report_no_waiver['pass'] is False
    
    # With waiver - should pass
    waivers = {
        'rec-002': 'Feature descoped per ADR-042'
    }
    report_with_waiver = gate.check('PH-TEST', waivers)
    
    assert report_with_waiver['pass'] is True
    assert report_with_waiver['summary']['waived'] == 1
    assert report_with_waiver['summary']['incomplete'] == 0
