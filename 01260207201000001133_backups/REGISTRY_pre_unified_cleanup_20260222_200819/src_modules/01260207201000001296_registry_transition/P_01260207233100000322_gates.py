"""
Gates - Completeness and Validity Checks

Separate gates with distinct exit codes:
- CompletenessGate: Check all required records are PRESENT
- ValidityGate: Check schema, write policy, referential integrity
"""
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

class CompletenessGate:
    """
    Gate A: Completeness verification.
    
    Rule: Every record with planned_by_phase_id == X and required == true
    must be PRESENT or (DEPRECATED + in waiver list).
    
    Exit code: 0 (pass), 10 (fail)
    """
    
    def __init__(self, registry_path: Path):
        """Initialize with registry path."""
        self.registry_path = Path(registry_path)
    
    def check(
        self,
        phase_id: str,
        waivers: Optional[Dict[str, str]] = None
    ) -> Dict:
        """
        Check completeness for given phase.
        
        Args:
            phase_id: Phase identifier to check
            waivers: Dict of {record_id: waiver_reason}
        
        Returns:
            Report dict with pass/fail status
        """
        waivers = waivers or {}
        
        try:
            with open(self.registry_path, encoding='utf-8') as f:
                registry = json.load(f)
        except Exception as e:
            return {
                'pass': False,
                'error': f"Failed to load registry: {e}",
                'exit_code': 10
            }
        
        incomplete_records = []
        waived_records = []
        complete_records = []
        
        for record in registry:
            # Check if record is for this phase
            if record.get('planned_by_phase_id') != phase_id:
                continue
            
            # Skip non-required records
            if not record.get('required', True):
                continue
            
            record_id = record.get('record_id')
            state = record.get('lifecycle_state')
            
            # Check state
            if state == 'PRESENT':
                complete_records.append(record_id)
            elif state == 'DEPRECATED' and record_id in waivers:
                waived_records.append({
                    'record_id': record_id,
                    'waiver_reason': waivers[record_id],
                    'waived_by': record.get('waived_by', 'unknown')
                })
            else:
                incomplete_records.append({
                    'record_id': record_id,
                    'current_state': state,
                    'canonical_path': record.get('canonical_path', 'unknown')
                })
        
        passed = len(incomplete_records) == 0
        
        report = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'phase_id': phase_id,
            'pass': passed,
            'exit_code': 0 if passed else 10,
            'summary': {
                'complete': len(complete_records),
                'waived': len(waived_records),
                'incomplete': len(incomplete_records)
            },
            'incomplete_records': incomplete_records,
            'waived_records': waived_records
        }
        
        # Write evidence
        self._emit_evidence(report, 'completeness_report.json')
        
        return report
    
    def _emit_evidence(self, report: Dict, filename: str):
        """Write report to evidence directory."""
        evidence_dir = Path('.state/evidence/gates')
        evidence_dir.mkdir(parents=True, exist_ok=True)
        
        with open(evidence_dir / filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)

class ValidityGate:
    """
    Gate B: Validity verification.
    
    Rules:
    1. JSON Schema valid
    2. Write policy satisfied (no immutable violations, no nulls where forbidden)
    3. Derivation consistency (recompute_on_scan columns not stale)
    4. Referential integrity (depends_on_file_ids valid)
    
    Exit code: 0 (pass), 11 (fail)
    """
    
    def __init__(
        self,
        registry_path: Path,
        schema_path: Optional[Path] = None,
        write_policy_path: Optional[Path] = None
    ):
        """Initialize with registry and schema paths."""
        self.registry_path = Path(registry_path)
        self.schema_path = Path(schema_path) if schema_path else None
        self.write_policy_path = Path(write_policy_path) if write_policy_path else None
    
    def check(self) -> Dict:
        """
        Run all validity checks.
        
        Returns:
            Report dict with pass/fail status
        """
        try:
            with open(self.registry_path, encoding='utf-8') as f:
                registry = json.load(f)
        except Exception as e:
            return {
                'pass': False,
                'error': f"Failed to load registry: {e}",
                'exit_code': 11
            }
        
        violations = []
        
        # Rule 1: Schema validation (if schema provided)
        if self.schema_path and self.schema_path.exists():
            schema_violations = self._check_schema(registry)
            violations.extend(schema_violations)
        
        # Rule 2: Write policy checks
        policy_violations = self._check_write_policy(registry)
        violations.extend(policy_violations)
        
        # Rule 3: Derivation consistency (basic check)
        # TODO: Implement full derivation consistency check
        
        # Rule 4: Referential integrity
        ref_violations = self._check_referential_integrity(registry)
        violations.extend(ref_violations)
        
        passed = len(violations) == 0
        
        report = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'pass': passed,
            'exit_code': 0 if passed else 11,
            'violations': violations,
            'summary': {
                'total_violations': len(violations),
                'by_type': self._count_by_type(violations)
            }
        }
        
        # Write evidence
        self._emit_evidence(report, 'validity_report.json')
        
        return report
    
    def _check_schema(self, registry: List[Dict]) -> List[Dict]:
        """Validate against JSON schema."""
        violations = []
        # TODO: Implement actual JSON schema validation
        return violations
    
    def _check_write_policy(self, registry: List[Dict]) -> List[Dict]:
        """Check write policy compliance."""
        violations = []
        
        for record in registry:
            record_id = record.get('record_id', 'unknown')
            
            # Check immutable fields are present
            for field in ['file_id', 'record_id', 'created_utc']:
                if field not in record or record[field] is None:
                    violations.append({
                        'type': 'missing_immutable',
                        'record_id': record_id,
                        'field': field
                    })
            
            # Check forbid_null fields
            # TODO: Load actual write policy and check forbid_null fields
        
        return violations
    
    def _check_referential_integrity(self, registry: List[Dict]) -> List[Dict]:
        """Check referential integrity."""
        violations = []
        
        # Build set of valid file_ids
        valid_file_ids = {
            r.get('file_id')
            for r in registry
            if r.get('file_id')
        }
        
        # Check depends_on_file_ids
        for record in registry:
            record_id = record.get('record_id', 'unknown')
            depends_on = record.get('depends_on_file_ids', [])
            
            for dep_id in depends_on:
                if dep_id not in valid_file_ids:
                    violations.append({
                        'type': 'broken_reference',
                        'record_id': record_id,
                        'field': 'depends_on_file_ids',
                        'invalid_reference': dep_id
                    })
        
        return violations
    
    def _count_by_type(self, violations: List[Dict]) -> Dict[str, int]:
        """Count violations by type."""
        counts = {}
        for v in violations:
            vtype = v.get('type', 'unknown')
            counts[vtype] = counts.get(vtype, 0) + 1
        return counts
    
    def _emit_evidence(self, report: Dict, filename: str):
        """Write report to evidence directory."""
        evidence_dir = Path('.state/evidence/gates')
        evidence_dir.mkdir(parents=True, exist_ok=True)
        
        with open(evidence_dir / filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
