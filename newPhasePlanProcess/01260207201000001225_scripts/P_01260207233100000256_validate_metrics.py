#!/usr/bin/env python3
"""Metrics Validator - Validates all plan metrics calculations"""
import argparse, json, sys
from pathlib import Path

class MetricsValidator:
    def __init__(self, plan_path):
        self.plan_path = Path(plan_path)
        self.errors = []

    def validate(self):
        with open(self.plan_path) as f:
            data = json.load(f)

        metrics = data.get('plan', {}).get('metrics', {})

        # Validate determinism_score
        det_score = metrics.get('determinism_score')
        if det_score is not None:
            if not isinstance(det_score, (int, float)) or not (0 <= det_score <= 1):
                self.errors.append('Invalid determinism_score (must be 0-1)')

        # Validate gate_coverage
        gate_cov = metrics.get('gate_coverage_percent')
        if gate_cov is not None:
            if not isinstance(gate_cov, (int, float)) or not (0 <= gate_cov <= 100):
                self.errors.append('Invalid gate_coverage_percent (must be 0-100)')

        # Validate automation_ratio
        auto_ratio = metrics.get('automation_ratio_percent')
        if auto_ratio is not None:
            if not isinstance(auto_ratio, (int, float)) or not (0 <= auto_ratio <= 100):
                self.errors.append('Invalid automation_ratio_percent (must be 0-100)')

        return len(self.errors) == 0, {
            'valid': len(self.errors) == 0,
            'errors': self.errors,
            'metrics_found': list(metrics.keys())
        }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan-file', required=True, help='Path to plan JSON file')
    parser.add_argument('--evidence-dir', help='Evidence output directory (optional)')
    parser.add_argument('--output', default='metrics_validation.json')
    args = parser.parse_args()

    validator = MetricsValidator(args.plan_file)
    is_valid, result = validator.validate()

    with open(args.output, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"{'✅ PASSED' if is_valid else '❌ FAILED'}: Metrics Validation")
    sys.exit(0 if is_valid else 1)

if __name__ == '__main__':
    main()
