#!/usr/bin/env python3
"""
GATE-002: Validation Gate Completeness Check

Ensures all validation gates are properly defined with executable commands,
regex patterns, and evidence specifications.

Exit Codes:
    0: All gates valid
    1: Gate definition errors
    2: File not found
    3: Invalid JSON

Evidence Output:
    .state/evidence/GATE-002/gates_validation.json
"""

import argparse
import json
import logging
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class GateValidator:
    """Validates gate definitions for completeness and executability"""

    REQUIRED_GATE_FIELDS = ['gate_name', 'validation_command']
    OPTIONAL_GATE_FIELDS = ['success_pattern', 'evidence_output', 'depends_on']

    def __init__(self, plan_path: str):
        self.plan_path = Path(plan_path)
        self.plan_data: Dict[str, Any] = {}
        self.errors: List[Dict[str, str]] = []
        self.warnings: List[Dict[str, str]] = []

    def validate(self) -> Tuple[bool, Dict[str, Any]]:
        """Run all gate validation checks"""
        logger.info(f"Validating gates: {self.plan_path}")

        if not self._load_plan():
            return False, self._generate_evidence()

        self._validate_gates_structure()
        self._validate_gate_completeness()
        self._validate_command_executability()
        self._validate_regex_patterns()
        self._validate_evidence_paths()
        self._validate_gate_dependencies()
        self._check_phase_gate_coverage()

        is_valid = len(self.errors) == 0
        logger.info(f"{'✅ PASSED' if is_valid else '❌ FAILED'}: {len(self.errors)} errors")
        return is_valid, self._generate_evidence()

    def _load_plan(self) -> bool:
        """Load plan JSON file"""
        if not self.plan_path.exists():
            self.errors.append({
                'error_code': 'FILE_NOT_FOUND',
                'error_message': f'Plan file not found: {self.plan_path}',
                'severity': 'critical'
            })
            return False

        try:
            with open(self.plan_path, 'r', encoding='utf-8') as f:
                self.plan_data = json.load(f)
            return True
        except json.JSONDecodeError as e:
            self.errors.append({
                'error_code': 'INVALID_JSON',
                'error_message': f'Invalid JSON: {str(e)}',
                'severity': 'critical'
            })
            return False

    def _validate_gates_structure(self):
        """Validate gates_by_id structure exists"""
        if 'plan' not in self.plan_data:
            self.errors.append({
                'error_code': 'MISSING_PLAN_SECTION',
                'error_message': 'plan section missing',
                'location': 'root',
                'severity': 'critical'
            })
            return

        if 'gates_by_id' not in self.plan_data['plan']:
            self.errors.append({
                'error_code': 'MISSING_GATES',
                'error_message': 'gates_by_id missing from plan',
                'location': 'plan',
                'severity': 'critical'
            })
            return

        gates = self.plan_data['plan']['gates_by_id']
        if not isinstance(gates, dict):
            self.errors.append({
                'error_code': 'INVALID_TYPE',
                'error_message': 'gates_by_id must be object',
                'location': 'plan.gates_by_id',
                'severity': 'critical'
            })

    def _validate_gate_completeness(self):
        """Validate each gate has required fields"""
        gates = self.plan_data.get('plan', {}).get('gates_by_id', {})

        for gate_id, gate_data in gates.items():
            if not isinstance(gate_data, dict):
                self.errors.append({
                    'error_code': 'INVALID_GATE_TYPE',
                    'error_message': f'Gate {gate_id} must be object',
                    'location': f'plan.gates_by_id.{gate_id}',
                    'severity': 'error'
                })
                continue

            for field in self.REQUIRED_GATE_FIELDS:
                if field not in gate_data:
                    self.errors.append({
                        'error_code': 'MISSING_REQUIRED_FIELD',
                        'error_message': f'Gate {gate_id} missing: {field}',
                        'location': f'plan.gates_by_id.{gate_id}',
                        'severity': 'error'
                    })

    def _validate_command_executability(self):
        """Check if validation commands reference executable programs"""
        gates = self.plan_data.get('plan', {}).get('gates_by_id', {})

        for gate_id, gate_data in gates.items():
            if not isinstance(gate_data, dict):
                continue

            cmd = gate_data.get('validation_command', '')
            if not cmd:
                continue

            # Extract command name (first token)
            cmd_parts = cmd.split()
            if not cmd_parts:
                self.errors.append({
                    'error_code': 'EMPTY_COMMAND',
                    'error_message': f'Gate {gate_id} has empty command',
                    'location': f'plan.gates_by_id.{gate_id}.validation_command',
                    'severity': 'error'
                })
                continue

            cmd_name = cmd_parts[0]

            # Check if command exists in PATH
            if not shutil.which(cmd_name):
                self.warnings.append({
                    'warning_code': 'COMMAND_NOT_FOUND',
                    'warning_message': f'Gate {gate_id} command not found in PATH: {cmd_name}',
                    'location': f'plan.gates_by_id.{gate_id}.validation_command'
                })

    def _validate_regex_patterns(self):
        """Validate success_pattern regex syntax"""
        gates = self.plan_data.get('plan', {}).get('gates_by_id', {})

        for gate_id, gate_data in gates.items():
            if not isinstance(gate_data, dict):
                continue

            pattern = gate_data.get('success_pattern')
            if not pattern:
                self.warnings.append({
                    'warning_code': 'MISSING_SUCCESS_PATTERN',
                    'warning_message': f'Gate {gate_id} has no success_pattern',
                    'location': f'plan.gates_by_id.{gate_id}'
                })
                continue

            try:
                re.compile(pattern)
            except re.error as e:
                self.errors.append({
                    'error_code': 'INVALID_REGEX',
                    'error_message': f'Gate {gate_id} invalid regex: {str(e)}',
                    'location': f'plan.gates_by_id.{gate_id}.success_pattern',
                    'severity': 'error'
                })

    def _validate_evidence_paths(self):
        """Check evidence output paths are specified"""
        gates = self.plan_data.get('plan', {}).get('gates_by_id', {})

        for gate_id, gate_data in gates.items():
            if not isinstance(gate_data, dict):
                continue

            evidence_path = gate_data.get('evidence_output')
            if not evidence_path:
                self.warnings.append({
                    'warning_code': 'MISSING_EVIDENCE_PATH',
                    'warning_message': f'Gate {gate_id} has no evidence_output',
                    'location': f'plan.gates_by_id.{gate_id}'
                })

    def _validate_gate_dependencies(self):
        """Validate gate dependencies are resolvable"""
        gates = self.plan_data.get('plan', {}).get('gates_by_id', {})
        gate_ids = set(gates.keys())

        for gate_id, gate_data in gates.items():
            if not isinstance(gate_data, dict):
                continue

            depends_on = gate_data.get('depends_on', [])
            if not isinstance(depends_on, list):
                self.errors.append({
                    'error_code': 'INVALID_DEPENDS_ON_TYPE',
                    'error_message': f'Gate {gate_id} depends_on must be array',
                    'location': f'plan.gates_by_id.{gate_id}.depends_on',
                    'severity': 'error'
                })
                continue

            for dep_id in depends_on:
                if dep_id not in gate_ids:
                    self.errors.append({
                        'error_code': 'MISSING_GATE_DEPENDENCY',
                        'error_message': f'Gate {gate_id} depends on non-existent gate: {dep_id}',
                        'location': f'plan.gates_by_id.{gate_id}.depends_on',
                        'severity': 'error'
                    })

    def _check_phase_gate_coverage(self):
        """Check that all phases have associated gates"""
        phases = self.plan_data.get('plan', {}).get('phases_by_id', {})
        gates = self.plan_data.get('plan', {}).get('gates_by_id', {})

        phases_without_gates = []
        for phase_id, phase_data in phases.items():
            if not isinstance(phase_data, dict):
                continue

            phase_gates = phase_data.get('validation_gates', [])
            if not phase_gates:
                phases_without_gates.append(phase_id)

        if phases_without_gates:
            self.warnings.append({
                'warning_code': 'PHASES_WITHOUT_GATES',
                'warning_message': f'{len(phases_without_gates)} phases without gates: {", ".join(phases_without_gates[:5])}',
                'location': 'plan.phases_by_id'
            })

    def _generate_evidence(self) -> Dict[str, Any]:
        """Generate evidence artifact"""
        gates = self.plan_data.get('plan', {}).get('gates_by_id', {})

        return {
            'gate_id': 'GATE-002',
            'gate_name': 'Validation gate completeness check',
            'validated_at': datetime.utcnow().isoformat() + 'Z',
            'validator_version': '1.0.0',
            'plan_file': str(self.plan_path),
            'validation_result': {
                'status': 'valid' if len(self.errors) == 0 else 'invalid',
                'errors_count': len(self.errors),
                'warnings_count': len(self.warnings),
                'errors': self.errors,
                'warnings': self.warnings
            },
            'statistics': {
                'total_gates': len(gates),
                'gates_with_commands': sum(1 for g in gates.values() if isinstance(g, dict) and 'validation_command' in g),
                'gates_with_patterns': sum(1 for g in gates.values() if isinstance(g, dict) and 'success_pattern' in g),
                'gates_with_evidence': sum(1 for g in gates.values() if isinstance(g, dict) and 'evidence_output' in g)
            }
        }


def save_evidence(evidence: Dict[str, Any], output_dir: Path):
    """Save evidence artifact"""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / 'gates_validation.json'

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(evidence, f, indent=2)

    logger.info(f"Evidence saved: {output_file}")


def main():
    parser = argparse.ArgumentParser(description='GATE-002: Validate gate definitions')
    parser.add_argument('--plan-file', required=True, help='Path to plan JSON file')
    parser.add_argument('--evidence-dir', default='.state/evidence/GATE-002')
    parser.add_argument('--verbose', action='store_true')

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    validator = GateValidator(args.plan_file)
    is_valid, evidence = validator.validate()

    evidence_dir = Path(args.evidence_dir)
    save_evidence(evidence, evidence_dir)

    print("\n" + "="*70)
    print("GATE-002: Validation Gate Completeness Check")
    print("="*70)
    print(f"Status: {'✅ PASSED' if is_valid else '❌ FAILED'}")
    print(f"Errors: {len(validator.errors)}")
    print(f"Warnings: {len(validator.warnings)}")
    print(f"Evidence: {evidence_dir / 'gates_validation.json'}")
    print("="*70 + "\n")

    sys.exit(0 if is_valid else 1)


if __name__ == '__main__':
    main()
