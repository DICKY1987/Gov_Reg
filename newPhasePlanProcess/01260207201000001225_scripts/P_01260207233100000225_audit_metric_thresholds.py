#!/usr/bin/env python3
"""Metric Threshold Auditor - Audits metrics against defined thresholds"""
import argparse, json, sys
from pathlib import Path

class MetricThresholdAuditor:
    def __init__(self, plan_path):
        self.plan_path = Path(plan_path)
        self.violations = []
        self.thresholds = {
            'determinism_score': 0.95,
            'gate_coverage_percent': 100,
            'automation_ratio_percent': 80
        }

    def audit(self):
        with open(self.plan_path) as f:
            data = json.load(f)

        metrics = data.get('plan', {}).get('metrics', {})

        for metric_name, threshold in self.thresholds.items():
            actual = metrics.get(metric_name, 0)
            if actual < threshold:
                self.violations.append({
                    'metric': metric_name,
                    'threshold': threshold,
                    'actual': actual,
                    'deficit': threshold - actual
                })

        return len(self.violations) == 0, {
            'compliant': len(self.violations) == 0,
            'violations': self.violations
        }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan-file', dest='plan_file', required=False)
    parser.add_argument('plan_file_positional', nargs='?')  # Accept positional too
    parser.add_argument('--output', default='threshold_audit.json')
    parser.add_argument('--evidence-dir', help='Evidence output directory (optional)', default='.state/evidence')

    args = parser.parse_args()



    # Use flag if provided, otherwise positional

    plan_file = args.plan_file or args.plan_file_positional

    if not plan_file:

        parser.error("plan_file is required (as --plan-file or positional argument)")

    args.plan_file = plan_file

    auditor = MetricThresholdAuditor(args.plan_file)
    is_compliant, result = auditor.audit()

    with open(args.output, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"{'✅ COMPLIANT' if is_compliant else '❌ VIOLATIONS'}: {len(result['violations'])} threshold violations")
    sys.exit(0 if is_compliant else 1)

if __name__ == '__main__':
    main()
