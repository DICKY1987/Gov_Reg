#!/usr/bin/env python3
"""GATE-010: Wiring Proof Validation - Master end-to-end wiring validation"""
import argparse, json, sys
from pathlib import Path
from datetime import datetime

class WiringProofValidator:
    def __init__(self, plan_path):
        self.plan_path = Path(plan_path)
        self.errors = []

    def validate(self):
        with open(self.plan_path) as f:
            data = json.load(f)

        artifacts = data.get('plan', {}).get('artifacts', {})
        phases = data.get('plan', {}).get('phases_by_id', {})

        # Check artifact flow integrity
        for artifact_id, artifact_data in artifacts.items():
            producer = artifact_data.get('producer_phase')
            consumers = artifact_data.get('consumer_phases', [])

            if producer and producer not in phases:
                self.errors.append(f"Artifact {artifact_id}: producer {producer} not found")

            for consumer in consumers:
                if consumer not in phases:
                    self.errors.append(f"Artifact {artifact_id}: consumer {consumer} not found")

        return len(self.errors) == 0, {
            'gate_id': 'GATE-010',
            'validated_at': datetime.utcnow().isoformat() + 'Z',
            'status': 'valid' if len(self.errors) == 0 else 'invalid',
            'errors': self.errors
        }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan-file', dest='plan_file', required=False)
    parser.add_argument('plan_file_positional', nargs='?')  # Accept positional too
    parser.add_argument('--evidence-dir', default='.state/evidence/GATE-010')
    args = parser.parse_args()



    # Use flag if provided, otherwise positional

    plan_file = args.plan_file or args.plan_file_positional

    if not plan_file:

        parser.error("plan_file is required (as --plan-file or positional argument)")

    args.plan_file = plan_file

    validator = WiringProofValidator(args.plan_file)
    is_valid, evidence = validator.validate()

    Path(args.evidence_dir).mkdir(parents=True, exist_ok=True)
    with open(Path(args.evidence_dir) / 'wiring_proof.json', 'w') as f:
        json.dump(evidence, f, indent=2)

    print(f"{'✅ PASSED' if is_valid else '❌ FAILED'}: Wiring Proof")
    sys.exit(0 if is_valid else 1)

if __name__ == '__main__':
    main()
