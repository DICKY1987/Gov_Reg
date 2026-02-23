#!/usr/bin/env python3
"""
GATE-009: Spine Coverage Validation

Validates phase spine coverage mapping to ensure all phases have validation coverage.

Exit Codes:
    0: Valid coverage
    1: Coverage gaps found
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SpineCoverageValidator:
    """Validates spine coverage mapping"""

    def __init__(self, plan_path: str):
        self.plan_path = Path(plan_path)
        self.plan_data: Dict[str, Any] = {}
        self.errors: List[Dict[str, str]] = []
        self.warnings: List[Dict[str, str]] = []
        self.coverage_gaps: List[str] = []

    def validate(self) -> Tuple[bool, Dict[str, Any]]:
        logger.info(f"Validating spine coverage: {self.plan_path}")

        if not self._load_plan():
            return False, self._generate_evidence()

        self._build_spine_map()
        self._validate_phase_coverage()
        self._detect_coverage_gaps()
        self._calculate_coverage_score()

        is_valid = len(self.errors) == 0 and len(self.coverage_gaps) == 0
        logger.info(f"{'✅ PASSED' if is_valid else '❌ FAILED'}: {len(self.coverage_gaps)} gaps")
        return is_valid, self._generate_evidence()

    def _load_plan(self) -> bool:
        if not self.plan_path.exists():
            self.errors.append({'error_code': 'FILE_NOT_FOUND', 'error_message': str(self.plan_path), 'severity': 'critical'})
            return False
        try:
            with open(self.plan_path, 'r', encoding='utf-8') as f:
                self.plan_data = json.load(f)
            return True
        except json.JSONDecodeError as e:
            self.errors.append({'error_code': 'INVALID_JSON', 'error_message': str(e), 'severity': 'critical'})
            return False

    def _build_spine_map(self):
        """Build spine coverage map"""
        self.spine_map = {}
        phases = self.plan_data.get('plan', {}).get('phases_by_id', {})

        for phase_id, phase_data in phases.items():
            if isinstance(phase_data, dict):
                gates = phase_data.get('validation_gates', [])
                self.spine_map[phase_id] = {
                    'gates': gates,
                    'has_coverage': len(gates) > 0
                }

    def _validate_phase_coverage(self):
        """Validate each phase has validation coverage"""
        for phase_id, coverage in self.spine_map.items():
            if not coverage['has_coverage']:
                self.coverage_gaps.append(phase_id)
                self.warnings.append({
                    'warning_code': 'NO_COVERAGE',
                    'warning_message': f'Phase {phase_id} has no validation gates',
                    'location': f'plan.phases_by_id.{phase_id}'
                })

    def _detect_coverage_gaps(self):
        """Detect coverage gaps"""
        if self.coverage_gaps:
            logger.warning(f"Found {len(self.coverage_gaps)} phases without coverage")

    def _calculate_coverage_score(self):
        """Calculate coverage score percentage"""
        total_phases = len(self.spine_map)
        covered_phases = sum(1 for c in self.spine_map.values() if c['has_coverage'])
        self.coverage_score = (covered_phases / total_phases * 100) if total_phases > 0 else 0

    def _generate_evidence(self) -> Dict[str, Any]:
        return {
            'gate_id': 'GATE-009',
            'gate_name': 'Spine coverage validation',
            'validated_at': datetime.utcnow().isoformat() + 'Z',
            'validator_version': '1.0.0',
            'plan_file': str(self.plan_path),
            'validation_result': {
                'status': 'valid' if len(self.errors) == 0 and len(self.coverage_gaps) == 0 else 'invalid',
                'errors_count': len(self.errors),
                'warnings_count': len(self.warnings),
                'errors': self.errors,
                'warnings': self.warnings
            },
            'coverage_analysis': {
                'total_phases': len(self.spine_map),
                'covered_phases': sum(1 for c in self.spine_map.values() if c['has_coverage']),
                'coverage_score': getattr(self, 'coverage_score', 0),
                'coverage_gaps': self.coverage_gaps
            }
        }


def main():
    parser = argparse.ArgumentParser(description='GATE-009: Validate spine coverage')
    parser.add_argument('--plan-file', required=True, help='Path to plan JSON file')
    parser.add_argument('--evidence-dir', default='.state/evidence/GATE-009')
    args = parser.parse_args()

    validator = SpineCoverageValidator(args.plan_file)
    is_valid, evidence = validator.validate()

    evidence_dir = Path(args.evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    with open(evidence_dir / 'spine_coverage_validation.json', 'w') as f:
        json.dump(evidence, f, indent=2)

    print(f"\n{'✅ PASSED' if is_valid else '❌ FAILED'}: Spine Coverage ({evidence['coverage_analysis']['coverage_score']:.1f}%)\n")
    sys.exit(0 if is_valid else 1)


if __name__ == '__main__':
    main()
