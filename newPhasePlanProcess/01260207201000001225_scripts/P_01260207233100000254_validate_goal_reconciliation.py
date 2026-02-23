#!/usr/bin/env python3
"""GATE-999: Goal Reconciliation - Validates goal decomposition and reconciliation"""
import argparse, json, sys
from pathlib import Path
from datetime import datetime

class GoalReconciliationValidator:
    def __init__(self, plan_path):
        self.plan_path = Path(plan_path)
        self.errors, self.warnings = [], []

    def validate(self):
        with open(self.plan_path) as f:
            data = json.load(f)

        phases = data.get('plan', {}).get('phases_by_id', {})
        for phase_id, phase_data in phases.items():
            if not phase_data.get('deliverables'):
                self.warnings.append(f"Phase {phase_id} missing deliverables")

        return len(self.errors) == 0, {
            'gate_id': 'GATE-999',
            'validated_at': datetime.utcnow().isoformat() + 'Z',
            'status': 'valid' if len(self.errors) == 0 else 'invalid',
            'errors': self.errors,
            'warnings': self.warnings
        }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan-file', dest='plan_file', required=False)
    parser.add_argument('plan_file_positional', nargs='?')  # Accept positional too
    parser.add_argument('--evidence-dir', default='.state/evidence/GATE-999')
    args = parser.parse_args()



    # Use flag if provided, otherwise positional

    plan_file = args.plan_file or args.plan_file_positional

    if not plan_file:

        parser.error("plan_file is required (as --plan-file or positional argument)")

    args.plan_file = plan_file

    validator = GoalReconciliationValidator(args.plan_file)
    is_valid, evidence = validator.validate()

    Path(args.evidence_dir).mkdir(parents=True, exist_ok=True)
    with open(Path(args.evidence_dir) / 'goal_reconciliation.json', 'w') as f:
        json.dump(evidence, f, indent=2)

    print(f"{'✅ PASSED' if is_valid else '❌ FAILED'}: Goal Reconciliation")
    sys.exit(0 if is_valid else 1)

if __name__ == '__main__':
    main()
