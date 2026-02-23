"""
Tests for migration_guard - Point of No Return
"""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from govreg_core.migration_guard import MigrationGuard, check_reversibility
from govreg_core.feature_flags import FeatureFlags, MigrationPhase


def test_phase_0_2_reversible(tmp_path):
    """Test: Phase 0-2 fully reversible."""
    flags_path = tmp_path / "flags.json"
    flags = FeatureFlags(str(flags_path))
    flags.set_phase(MigrationPhase.PHASE_1_FOUNDATION)
    
    guard = MigrationGuard()
    guard.flags = flags
    
    status = guard.check_migration_reversibility({})
    
    assert status.reversible is True
    assert "No schema changes" in status.reason
    assert status.data_loss_risk is False


def test_phase_3_no_data_reversible(tmp_path):
    """Test: Phase 3 with no v3 data - reversible."""
    flags_path = tmp_path / "flags.json"
    flags = FeatureFlags(str(flags_path))
    flags.set_phase(MigrationPhase.PHASE_3_REGISTRY)
    
    guard = MigrationGuard()
    guard.flags = flags
    
    registry_state = {
        'files': [
            {'file_id': '01999000042260124001', 'relative_path': 'src/a.py'}
        ]
    }
    
    status = guard.check_migration_reversibility(registry_state)
    
    assert status.reversible is True
    assert "no data written" in status.reason
    assert status.data_loss_risk is False


def test_phase_3_with_data_reversible_with_loss(tmp_path):
    """Test: Phase 3 with v3 data - reversible with data loss."""
    flags_path = tmp_path / "flags.json"
    flags = FeatureFlags(str(flags_path))
    flags.set_phase(MigrationPhase.PHASE_3_REGISTRY)
    
    guard = MigrationGuard()
    guard.flags = flags
    
    registry_state = {
        'files': [
            {
                'file_id': '01999000042260124001',
                'relative_path': 'src/a.py',
                'content_hash': 'abc123',  # v3 field populated
                'observed_at': '2026-02-03T00:00:00Z'
            }
        ]
    }
    
    status = guard.check_migration_reversibility(registry_state)
    
    assert status.reversible is True
    assert status.data_loss_risk is True
    assert "entries use new fields" in status.reason


def test_phase_4_irreversible(tmp_path):
    """Test: Phase 4 - IRREVERSIBLE."""
    flags_path = tmp_path / "flags.json"
    flags = FeatureFlags(str(flags_path))
    flags.set_phase(MigrationPhase.PHASE_4_DEPRECATION)
    
    guard = MigrationGuard()
    guard.flags = flags
    
    status = guard.check_migration_reversibility({})
    
    assert status.reversible is False
    assert "POINT OF NO RETURN CROSSED" in status.reason
    assert status.irreversible_since == "phase_4_legacy_deprecation"


def test_pre_migration_checklist_phase_4(tmp_path):
    """Test: Pre-migration checklist required for Phase 4."""
    flags_path = tmp_path / "flags.json"
    flags = FeatureFlags(str(flags_path))
    
    guard = MigrationGuard()
    guard.flags = flags
    
    checklist = guard.enforce_pre_migration_checklist(MigrationPhase.PHASE_4_DEPRECATION)
    
    assert checklist['required'] is True
    assert len(checklist['items']) >= 10
    assert any('backup' in item['item'].lower() for item in checklist['items'])
    assert any('approval' in item['item'].lower() for item in checklist['items'])


def test_pre_migration_checklist_not_required_phase_2(tmp_path):
    """Test: Pre-migration checklist NOT required for Phase 2."""
    guard = MigrationGuard()
    
    checklist = guard.enforce_pre_migration_checklist(MigrationPhase.PHASE_2_CORE)
    
    assert checklist['required'] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
