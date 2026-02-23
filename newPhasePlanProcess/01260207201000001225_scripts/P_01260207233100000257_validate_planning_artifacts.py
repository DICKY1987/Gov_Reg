#!/usr/bin/env python3
"""
GATE-005: Planning Artifacts Validation

Validates planning_artifacts/ directory structure and metadata.

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


class PlanningArtifactsValidator:
    """Validates planning artifacts structure"""

    def __init__(self, plan_path: str):
        self.plan_path = Path(plan_path)
        self.plan_data: Dict[str, Any] = {}
        self.errors: List[Dict[str, str]] = []
        self.warnings: List[Dict[str, str]] = []

    def validate(self) -> Tuple[bool, Dict[str, Any]]:
        """Run validation checks"""
        logger.info(f"Validating planning artifacts: {self.plan_path}")

        if not self._load_plan():
            return False, self._generate_evidence()

        self._validate_artifacts_section()
        self._validate_artifact_metadata()
        self._validate_producers_consumers()

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

    def _validate_artifacts_section(self):
        """Check artifacts section exists"""
        if 'plan' not in self.plan_data:
            return

        if 'artifacts' not in self.plan_data['plan']:
            self.warnings.append({'warning_code': 'NO_ARTIFACTS', 'warning_message': 'No artifacts section defined'})

    def _validate_artifact_metadata(self):
        """Validate artifact metadata"""
        artifacts = self.plan_data.get('plan', {}).get('artifacts', {})

        for artifact_id, artifact_data in artifacts.items():
            if not isinstance(artifact_data, dict):
                self.errors.append({'error_code': 'INVALID_ARTIFACT', 'error_message': f'Artifact {artifact_id} must be object', 'severity': 'error'})
                continue

            # Check required fields
            if 'artifact_type' not in artifact_data:
                self.errors.append({'error_code': 'MISSING_TYPE', 'error_message': f'Artifact {artifact_id} missing type', 'severity': 'error'})

    def _validate_producers_consumers(self):
        """Validate producer/consumer relationships"""
        artifacts = self.plan_data.get('plan', {}).get('artifacts', {})
        phases = set(self.plan_data.get('plan', {}).get('phases_by_id', {}).keys())

        for artifact_id, artifact_data in artifacts.items():
            if not isinstance(artifact_data, dict):
                continue

            producer = artifact_data.get('producer_phase')
            if producer and producer not in phases:
                self.errors.append({'error_code': 'INVALID_PRODUCER', 'error_message': f'Artifact {artifact_id} producer not found: {producer}', 'severity': 'error'})

            consumers = artifact_data.get('consumer_phases', [])
            for consumer in consumers:
                if consumer not in phases:
                    self.errors.append({'error_code': 'INVALID_CONSUMER', 'error_message': f'Artifact {artifact_id} consumer not found: {consumer}', 'severity': 'error'})

    def _generate_evidence(self) -> Dict[str, Any]:
        return {
            'gate_id': 'GATE-005',
            'gate_name': 'Planning artifacts validation',
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
                'total_artifacts': len(self.plan_data.get('plan', {}).get('artifacts', {}))
            }
        }


def main():
    parser = argparse.ArgumentParser(description='GATE-005: Validate planning artifacts')
    parser.add_argument('--plan-file', required=True, help='Path to plan JSON file')
    parser.add_argument('--evidence-dir', default='.state/evidence/GATE-005')
    args = parser.parse_args()

    validator = PlanningArtifactsValidator(args.plan_file)
    is_valid, evidence = validator.validate()

    evidence_dir = Path(args.evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    with open(evidence_dir / 'planning_artifacts_validation.json', 'w') as f:
        json.dump(evidence, f, indent=2)

    print(f"\n{'✅ PASSED' if is_valid else '❌ FAILED'}: Planning Artifacts Validation\n")
    sys.exit(0 if is_valid else 1)


if __name__ == '__main__':
    main()
