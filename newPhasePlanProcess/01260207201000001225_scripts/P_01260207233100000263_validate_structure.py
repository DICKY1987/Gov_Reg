#!/usr/bin/env python3
"""
GATE-001: Plan Structure Validation Script

Validates overall plan structure including all required sections, proper nesting,
and structural integrity beyond basic JSON parsing.

Exit Codes:
    0: Structure valid
    1: Structure errors found
    2: File not found or cannot be read
    3: Invalid JSON syntax

Evidence Output:
    .state/evidence/GATE-001/structure_validation.json
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StructureValidationError(Exception):
    """Custom exception for structure validation errors"""
    pass


class PlanStructureValidator:
    """Validates plan JSON structure against requirements"""

    # Required top-level sections
    REQUIRED_SECTIONS = [
        'meta',
        'plan'
    ]

    # Required meta fields
    REQUIRED_META_FIELDS = [
        'plan_id',
        'template_version',
        'created_at',
        'system_version'
    ]

    # Required plan fields
    REQUIRED_PLAN_FIELDS = [
        'classification',
        'phases_by_id',
        'gates_by_id',
        'metrics'
    ]

    # ID format patterns
    ID_PATTERNS = {
        'plan_id': r'^PLAN-[A-Z0-9]{8,16}$',
        'phase_id': r'^PH-\d{2,4}$',
        'gate_id': r'^GATE-\d{3}$',
        'command_id': r'^CMD-\d{3,6}$'
    }

    def __init__(self, plan_path: str):
        """
        Initialize validator with plan file path

        Args:
            plan_path: Path to plan JSON file
        """
        self.plan_path = Path(plan_path)
        self.plan_data: Dict[str, Any] = {}
        self.errors: List[Dict[str, str]] = []
        self.warnings: List[Dict[str, str]] = []

    def validate(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Run all validation checks

        Returns:
            Tuple of (is_valid, evidence_dict)
        """
        logger.info(f"Validating plan structure: {self.plan_path}")

        # Load plan file
        if not self._load_plan():
            return False, self._generate_evidence()

        # Run validation checks
        self._validate_required_sections()
        self._validate_meta_section()
        self._validate_plan_section()
        self._validate_phases()
        self._validate_gates()
        self._validate_id_formats()
        self._validate_nesting()

        is_valid = len(self.errors) == 0

        if is_valid:
            logger.info("✅ Plan structure validation PASSED")
        else:
            logger.error(f"❌ Plan structure validation FAILED with {len(self.errors)} errors")

        return is_valid, self._generate_evidence()

    def _load_plan(self) -> bool:
        """Load and parse plan JSON file"""
        if not self.plan_path.exists():
            error = {
                'error_code': 'FILE_NOT_FOUND',
                'error_message': f'Plan file not found: {self.plan_path}',
                'severity': 'critical'
            }
            self.errors.append(error)
            logger.error(error['error_message'])
            return False

        try:
            with open(self.plan_path, 'r', encoding='utf-8') as f:
                self.plan_data = json.load(f)
            logger.info(f"✅ Loaded plan file: {self.plan_path.name}")
            return True
        except json.JSONDecodeError as e:
            error = {
                'error_code': 'INVALID_JSON',
                'error_message': f'Invalid JSON syntax: {str(e)}',
                'location': f'Line {e.lineno}, Column {e.colno}',
                'severity': 'critical'
            }
            self.errors.append(error)
            logger.error(error['error_message'])
            return False
        except Exception as e:
            error = {
                'error_code': 'LOAD_ERROR',
                'error_message': f'Error loading plan file: {str(e)}',
                'severity': 'critical'
            }
            self.errors.append(error)
            logger.error(error['error_message'])
            return False

    def _validate_required_sections(self):
        """Validate all required top-level sections are present"""
        for section in self.REQUIRED_SECTIONS:
            if section not in self.plan_data:
                self.errors.append({
                    'error_code': 'MISSING_SECTION',
                    'error_message': f'Required section missing: {section}',
                    'location': 'root',
                    'severity': 'critical'
                })
                logger.error(f"❌ Missing required section: {section}")
            else:
                logger.debug(f"✅ Found section: {section}")

    def _validate_meta_section(self):
        """Validate meta section structure and required fields"""
        if 'meta' not in self.plan_data:
            return

        meta = self.plan_data['meta']

        if not isinstance(meta, dict):
            self.errors.append({
                'error_code': 'INVALID_TYPE',
                'error_message': 'meta section must be an object',
                'location': 'meta',
                'severity': 'critical'
            })
            return

        # Check required meta fields
        for field in self.REQUIRED_META_FIELDS:
            if field not in meta:
                self.errors.append({
                    'error_code': 'MISSING_FIELD',
                    'error_message': f'Required meta field missing: {field}',
                    'location': 'meta',
                    'severity': 'critical'
                })
            else:
                logger.debug(f"✅ Found meta field: {field}")

        # Validate timestamps
        if 'created_at' in meta:
            if not self._is_valid_iso8601(meta['created_at']):
                self.errors.append({
                    'error_code': 'INVALID_TIMESTAMP',
                    'error_message': 'created_at must be ISO 8601 format',
                    'location': 'meta.created_at',
                    'severity': 'error'
                })

    def _validate_plan_section(self):
        """Validate plan section structure and required fields"""
        if 'plan' not in self.plan_data:
            return

        plan = self.plan_data['plan']

        if not isinstance(plan, dict):
            self.errors.append({
                'error_code': 'INVALID_TYPE',
                'error_message': 'plan section must be an object',
                'location': 'plan',
                'severity': 'critical'
            })
            return

        # Check required plan fields
        for field in self.REQUIRED_PLAN_FIELDS:
            if field not in plan:
                self.errors.append({
                    'error_code': 'MISSING_FIELD',
                    'error_message': f'Required plan field missing: {field}',
                    'location': 'plan',
                    'severity': 'critical'
                })
            else:
                logger.debug(f"✅ Found plan field: {field}")

    def _validate_phases(self):
        """Validate phases_by_id structure"""
        if 'plan' not in self.plan_data or 'phases_by_id' not in self.plan_data['plan']:
            return

        phases = self.plan_data['plan']['phases_by_id']

        if not isinstance(phases, dict):
            self.errors.append({
                'error_code': 'INVALID_TYPE',
                'error_message': 'phases_by_id must be an object',
                'location': 'plan.phases_by_id',
                'severity': 'critical'
            })
            return

        if len(phases) == 0:
            self.warnings.append({
                'warning_code': 'EMPTY_PHASES',
                'warning_message': 'No phases defined',
                'location': 'plan.phases_by_id'
            })

        logger.info(f"✅ Found {len(phases)} phases")

        # Validate each phase
        for phase_id, phase_data in phases.items():
            self._validate_phase(phase_id, phase_data)

    def _validate_phase(self, phase_id: str, phase_data: Any):
        """Validate individual phase structure"""
        if not isinstance(phase_data, dict):
            self.errors.append({
                'error_code': 'INVALID_TYPE',
                'error_message': f'Phase {phase_id} must be an object',
                'location': f'plan.phases_by_id.{phase_id}',
                'severity': 'error'
            })
            return

        # Required phase fields
        required_fields = ['phase_name', 'deliverables']
        for field in required_fields:
            if field not in phase_data:
                self.errors.append({
                    'error_code': 'MISSING_FIELD',
                    'error_message': f'Phase {phase_id} missing required field: {field}',
                    'location': f'plan.phases_by_id.{phase_id}',
                    'severity': 'error'
                })

    def _validate_gates(self):
        """Validate gates_by_id structure"""
        if 'plan' not in self.plan_data or 'gates_by_id' not in self.plan_data['plan']:
            return

        gates = self.plan_data['plan']['gates_by_id']

        if not isinstance(gates, dict):
            self.errors.append({
                'error_code': 'INVALID_TYPE',
                'error_message': 'gates_by_id must be an object',
                'location': 'plan.gates_by_id',
                'severity': 'critical'
            })
            return

        if len(gates) == 0:
            self.warnings.append({
                'warning_code': 'EMPTY_GATES',
                'warning_message': 'No gates defined',
                'location': 'plan.gates_by_id'
            })

        logger.info(f"✅ Found {len(gates)} gates")

        # Validate each gate
        for gate_id, gate_data in gates.items():
            self._validate_gate(gate_id, gate_data)

    def _validate_gate(self, gate_id: str, gate_data: Any):
        """Validate individual gate structure"""
        if not isinstance(gate_data, dict):
            self.errors.append({
                'error_code': 'INVALID_TYPE',
                'error_message': f'Gate {gate_id} must be an object',
                'location': f'plan.gates_by_id.{gate_id}',
                'severity': 'error'
            })
            return

        # Required gate fields
        required_fields = ['gate_name', 'validation_command']
        for field in required_fields:
            if field not in gate_data:
                self.errors.append({
                    'error_code': 'MISSING_FIELD',
                    'error_message': f'Gate {gate_id} missing required field: {field}',
                    'location': f'plan.gates_by_id.{gate_id}',
                    'severity': 'error'
                })

    def _validate_id_formats(self):
        """Validate ID format patterns"""
        import re

        # Validate plan_id
        if 'meta' in self.plan_data and 'plan_id' in self.plan_data['meta']:
            plan_id = self.plan_data['meta']['plan_id']
            if not re.match(self.ID_PATTERNS['plan_id'], plan_id):
                self.errors.append({
                    'error_code': 'INVALID_ID_FORMAT',
                    'error_message': f'Invalid plan_id format: {plan_id}',
                    'location': 'meta.plan_id',
                    'severity': 'error',
                    'expected_pattern': self.ID_PATTERNS['plan_id']
                })

        # Validate phase IDs
        if 'plan' in self.plan_data and 'phases_by_id' in self.plan_data['plan']:
            for phase_id in self.plan_data['plan']['phases_by_id'].keys():
                if not re.match(self.ID_PATTERNS['phase_id'], phase_id):
                    self.errors.append({
                        'error_code': 'INVALID_ID_FORMAT',
                        'error_message': f'Invalid phase_id format: {phase_id}',
                        'location': f'plan.phases_by_id.{phase_id}',
                        'severity': 'error',
                        'expected_pattern': self.ID_PATTERNS['phase_id']
                    })

        # Validate gate IDs
        if 'plan' in self.plan_data and 'gates_by_id' in self.plan_data['plan']:
            for gate_id in self.plan_data['plan']['gates_by_id'].keys():
                if not re.match(self.ID_PATTERNS['gate_id'], gate_id):
                    self.errors.append({
                        'error_code': 'INVALID_ID_FORMAT',
                        'error_message': f'Invalid gate_id format: {gate_id}',
                        'location': f'plan.gates_by_id.{gate_id}',
                        'severity': 'error',
                        'expected_pattern': self.ID_PATTERNS['gate_id']
                    })

    def _validate_nesting(self):
        """Validate proper nesting and hierarchy"""
        # Check for circular dependencies in phases
        if 'plan' in self.plan_data and 'phases_by_id' in self.plan_data['plan']:
            phases = self.plan_data['plan']['phases_by_id']
            for phase_id, phase_data in phases.items():
                if isinstance(phase_data, dict) and 'depends_on' in phase_data:
                    depends_on = phase_data['depends_on']
                    if isinstance(depends_on, list):
                        # Check dependencies exist
                        for dep_id in depends_on:
                            if dep_id not in phases:
                                self.errors.append({
                                    'error_code': 'MISSING_DEPENDENCY',
                                    'error_message': f'Phase {phase_id} depends on non-existent phase: {dep_id}',
                                    'location': f'plan.phases_by_id.{phase_id}.depends_on',
                                    'severity': 'error'
                                })

    def _is_valid_iso8601(self, timestamp: str) -> bool:
        """Check if string is valid ISO 8601 timestamp"""
        try:
            datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return True
        except (ValueError, AttributeError):
            return False

    def _generate_evidence(self) -> Dict[str, Any]:
        """Generate evidence artifact"""
        return {
            'gate_id': 'GATE-001',
            'gate_name': 'Plan structure validation',
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
                'phases_count': len(self.plan_data.get('plan', {}).get('phases_by_id', {})),
                'gates_count': len(self.plan_data.get('plan', {}).get('gates_by_id', {}))
            }
        }


def save_evidence(evidence: Dict[str, Any], output_dir: Path):
    """Save evidence artifact to file"""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / 'structure_validation.json'

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(evidence, f, indent=2)

    logger.info(f"✅ Evidence saved: {output_file}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='GATE-001: Validate plan structure'
    )
    parser.add_argument(
        '--plan-file',
        dest='plan_file',
        required=False,
        help='Path to plan JSON file'
    )
    parser.add_argument(
        'plan_file_positional',
        nargs='?',
        help='Path to plan JSON file (positional)'
    )
    parser.add_argument(
        '--evidence-dir',
        default='.state/evidence/GATE-001',
        help='Directory for evidence output (default: .state/evidence/GATE-001)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Use flag if provided, otherwise positional
    plan_file = args.plan_file or args.plan_file_positional
    if not plan_file:
        parser.error("plan_file is required (as --plan-file or positional argument)")
    args.plan_file = plan_file

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Validate structure
    validator = PlanStructureValidator(args.plan_file)
    is_valid, evidence = validator.validate()

    # Save evidence
    evidence_dir = Path(args.evidence_dir)
    save_evidence(evidence, evidence_dir)

    # Print summary
    print("\n" + "="*70)
    print("GATE-001: Plan Structure Validation")
    print("="*70)
    print(f"Status: {'✅ PASSED' if is_valid else '❌ FAILED'}")
    print(f"Errors: {len(validator.errors)}")
    print(f"Warnings: {len(validator.warnings)}")
    print(f"Evidence: {evidence_dir / 'structure_validation.json'}")
    print("="*70 + "\n")

    # Exit with appropriate code
    if not validator.plan_path.exists():
        sys.exit(2)
    elif not validator.plan_data:
        sys.exit(3)
    elif not is_valid:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
