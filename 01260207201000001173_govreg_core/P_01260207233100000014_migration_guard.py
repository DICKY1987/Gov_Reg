"""
Migration Guard - Point of No Return Detection

Implements reversibility checks per spec Section 4.3.

Phase boundaries:
- Phase 0-2: Fully reversible
- Phase 3: Reversible with data loss
- Phase 4+: IRREVERSIBLE (content_hash becomes required)
"""

from enum import Enum
from typing import Dict, List, Optional
import logging

from .feature_flags import get_feature_flags, MigrationPhase

logger = logging.getLogger(__name__)


class ReversibilityStatus:
    """Migration reversibility status."""
    
    def __init__(
        self,
        reversible: bool,
        reason: str,
        rollback_steps: List[str],
        data_loss_risk: bool = False,
        irreversible_since: Optional[str] = None
    ):
        self.reversible = reversible
        self.reason = reason
        self.rollback_steps = rollback_steps
        self.data_loss_risk = data_loss_risk
        self.irreversible_since = irreversible_since


class MigrationGuard:
    """Check migration reversibility and enforce boundaries."""
    
    def __init__(self):
        self.flags = get_feature_flags()
    
    def check_migration_reversibility(self, registry_state: Dict) -> ReversibilityStatus:
        """
        Determine if migration can be rolled back.
        
        Args:
            registry_state: Current registry state
        
        Returns:
            ReversibilityStatus with actionable information
        """
        current_phase = self.flags.flags.get("migration_phase")
        
        # Phase 0-2: Fully reversible
        if current_phase in ["phase_0_preparation", "phase_1_foundation", "phase_2_core_components"]:
            return ReversibilityStatus(
                reversible=True,
                reason="No schema changes yet",
                rollback_steps=["Disable feature flags", "Revert code"]
            )
        
        # Phase 3: Conditional reversibility
        if current_phase == "phase_3_registry_extension":
            # Check if new fields have been written
            new_field_usage = self._count_registry_entries_with_fields(
                registry_state,
                fields=['content_hash', 'observed_at', 'source_plan_id']
            )
            
            if new_field_usage == 0:
                return ReversibilityStatus(
                    reversible=True,
                    reason="Schema extended but no data written with new fields",
                    rollback_steps=["Revert schema", "Disable v3 writer"]
                )
            else:
                return ReversibilityStatus(
                    reversible=True,  # Still reversible with data loss
                    reason=f"{new_field_usage} entries use new fields",
                    rollback_steps=[
                        "⚠️ WARNING: Rollback will lose new field data",
                        "Backup registry before rollback",
                        "Revert schema (new fields become nullable again)",
                        "Legacy writer will ignore new fields"
                    ],
                    data_loss_risk=True
                )
        
        # Phase 4-5: IRREVERSIBLE
        if current_phase in ["phase_4_legacy_deprecation", "phase_5_production_cutover"]:
            return ReversibilityStatus(
                reversible=False,
                reason="POINT OF NO RETURN CROSSED: content_hash is now required",
                rollback_steps=["NOT POSSIBLE"],
                irreversible_since="phase_4_legacy_deprecation"
            )
        
        # Unknown phase
        return ReversibilityStatus(
            reversible=False,
            reason=f"Unknown phase: {current_phase}",
            rollback_steps=["Manual intervention required"]
        )
    
    def _count_registry_entries_with_fields(
        self,
        registry_state: Dict,
        fields: List[str]
    ) -> int:
        """
        Count registry entries using specified fields.
        
        Args:
            registry_state: Registry state dict
            fields: List of field names to check
        
        Returns:
            Count of entries with any of the fields populated
        """
        count = 0
        entries = registry_state.get('files', [])
        
        for entry in entries:
            for field in fields:
                if entry.get(field) is not None:
                    count += 1
                    break  # Count each entry only once
        
        return count
    
    def enforce_pre_migration_checklist(self, phase: MigrationPhase) -> Dict:
        """
        Enforce pre-migration checklist before crossing point of no return.
        
        Args:
            phase: Phase to check requirements for
        
        Returns:
            Checklist status dict
        """
        if phase != MigrationPhase.PHASE_4_DEPRECATION:
            return {
                'required': False,
                'reason': f'{phase.value} does not require pre-migration checklist'
            }
        
        checklist = {
            'required': True,
            'phase': 'phase_4_legacy_deprecation',
            'items': [
                {'item': 'Full registry backup created and verified', 'status': 'PENDING'},
                {'item': 'Backup restoration tested successfully', 'status': 'PENDING'},
                {'item': 'All teams notified of irreversible boundary', 'status': 'PENDING'},
                {'item': 'Emergency rollback procedure documented', 'status': 'PENDING'},
                {'item': 'Monitoring and alerting configured', 'status': 'PENDING'},
                {'item': 'At least 2 weeks of stable operation in phase_3', 'status': 'PENDING'},
                {'item': 'No critical defects in v3 writer', 'status': 'PENDING'},
                {'item': 'Performance validated (no degradation)', 'status': 'PENDING'},
                {'item': 'Approval from technical leads obtained', 'status': 'PENDING'},
                {'item': 'Sign-off from governance team obtained', 'status': 'PENDING'}
            ]
        }
        
        logger.warning("Pre-migration checklist required before Phase 4")
        
        return checklist


def check_reversibility(registry_state: Dict) -> ReversibilityStatus:
    """Check migration reversibility (convenience wrapper)."""
    guard = MigrationGuard()
    return guard.check_migration_reversibility(registry_state)
