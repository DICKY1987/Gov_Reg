#!/usr/bin/env python3
"""
GATE-006: Automation Specification Validation

Validates automation specifications including commands, retry policies,
and self-healing configurations.

Exit Codes:
    0: Valid
    1: Validation errors
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


class AutomationSpecValidator:
    """Validates automation specifications"""

    def __init__(self, plan_path: str):
        self.plan_path = Path(plan_path)
        self.plan_data: Dict[str, Any] = {}
        self.errors: List[Dict[str, str]] = []
        self.warnings: List[Dict[str, str]] = []

    def validate(self) -> Tuple[bool, Dict[str, Any]]:
        logger.info(f"Validating automation spec: {self.plan_path}")

        if not self._load_plan():
            return False, self._generate_evidence()

        self._validate_automation_ratio()
        self._validate_commands()
        self._validate_retry_policies()
        self._validate_self_healing()

        is_valid = len(self.errors) == 0
        logger.info(f"{'✅ PASSED' if is_valid else '❌ FAILED'}: {len(self.errors)} errors")
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

    def _validate_automation_ratio(self):
        """Validate automation_ratio_percent"""
        metrics = self.plan_data.get('plan', {}).get('metrics', {})

        if 'automation_ratio_percent' in metrics:
            ratio = metrics['automation_ratio_percent']
            if not isinstance(ratio, (int, float)) or not (0 <= ratio <= 100):
                self.errors.append({'error_code': 'INVALID_AUTOMATION_RATIO', 'error_message': f'Invalid ratio: {ratio}', 'severity': 'error'})
        else:
            self.warnings.append({'warning_code': 'MISSING_AUTOMATION_RATIO', 'warning_message': 'automation_ratio_percent not defined'})

    def _validate_commands(self):
        """Validate command definitions"""
        commands = self.plan_data.get('plan', {}).get('commands', {})

        for cmd_id, cmd_data in commands.items():
            if not isinstance(cmd_data, dict):
                self.errors.append({'error_code': 'INVALID_COMMAND', 'error_message': f'Command {cmd_id} must be object', 'severity': 'error'})
                continue

            if 'command' not in cmd_data:
                self.errors.append({'error_code': 'MISSING_COMMAND', 'error_message': f'Command {cmd_id} missing command field', 'severity': 'error'})

    def _validate_retry_policies(self):
        """Validate retry policy configurations"""
        self_healing = self.plan_data.get('plan', {}).get('self_healing', {})

        if 'retry_policies' in self_healing:
            policies = self_healing['retry_policies']
            if not isinstance(policies, dict):
                self.errors.append({'error_code': 'INVALID_RETRY_POLICIES', 'error_message': 'retry_policies must be object', 'severity': 'error'})

    def _validate_self_healing(self):
        """Validate self-healing configuration"""
        self_healing = self.plan_data.get('plan', {}).get('self_healing', {})

        if not self_healing:
            self.warnings.append({'warning_code': 'NO_SELF_HEALING', 'warning_message': 'No self-healing configuration'})

    def _generate_evidence(self) -> Dict[str, Any]:
        commands = self.plan_data.get('plan', {}).get('commands', {})

        return {
            'gate_id': 'GATE-006',
            'gate_name': 'Automation specification validation',
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
                'total_commands': len(commands)
            }
        }


def main():
    parser = argparse.ArgumentParser(description='GATE-006: Validate automation spec')
    parser.add_argument('--plan-file', required=True, help='Path to plan JSON file')
    parser.add_argument('--evidence-dir', default='.state/evidence/GATE-006')
    args = parser.parse_args()

    validator = AutomationSpecValidator(args.plan_file)
    is_valid, evidence = validator.validate()

    evidence_dir = Path(args.evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    with open(evidence_dir / 'automation_spec_validation.json', 'w') as f:
        json.dump(evidence, f, indent=2)

    print(f"\n{'✅ PASSED' if is_valid else '❌ FAILED'}: Automation Spec Validation\n")
    sys.exit(0 if is_valid else 1)


if __name__ == '__main__':
    main()
