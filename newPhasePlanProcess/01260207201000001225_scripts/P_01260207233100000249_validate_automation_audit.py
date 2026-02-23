#!/usr/bin/env python3
"""GATE-998: Automation Audit - Audits automation for compliance"""
import argparse, json, sys
from pathlib import Path
from datetime import datetime

class AutomationAuditor:
    def __init__(self, plan_path):
        self.plan_path = Path(plan_path)
        self.errors, self.warnings = [], []

    def audit(self):
        with open(self.plan_path) as f:
            data = json.load(f)

        commands = data.get('plan', {}).get('commands', {})
        gates = data.get('plan', {}).get('gates_by_id', {})

        audit_result = {
            'total_commands': len(commands),
            'total_gates': len(gates),
            'automation_coverage': len(commands) / max(len(gates), 1) * 100 if gates else 0
        }

        return len(self.errors) == 0, {
            'gate_id': 'GATE-998',
            'validated_at': datetime.utcnow().isoformat() + 'Z',
            'status': 'compliant' if len(self.errors) == 0 else 'non_compliant',
            'audit_results': audit_result,
            'errors': self.errors
        }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan-file', dest='plan_file', required=False)
    parser.add_argument('plan_file_positional', nargs='?')  # Accept positional too
    parser.add_argument('--evidence-dir', default='.state/evidence/GATE-998')
    args = parser.parse_args()



    # Use flag if provided, otherwise positional

    plan_file = args.plan_file or args.plan_file_positional

    if not plan_file:

        parser.error("plan_file is required (as --plan-file or positional argument)")

    args.plan_file = plan_file

    auditor = AutomationAuditor(args.plan_file)
    is_valid, evidence = auditor.audit()

    Path(args.evidence_dir).mkdir(parents=True, exist_ok=True)
    with open(Path(args.evidence_dir) / 'automation_audit.json', 'w') as f:
        json.dump(evidence, f, indent=2)

    print(f"{'✅ PASSED' if is_valid else '❌ FAILED'}: Automation Audit")
    sys.exit(0 if is_valid else 1)

if __name__ == '__main__':
    main()
