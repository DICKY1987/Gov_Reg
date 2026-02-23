#!/usr/bin/env python3
"""File Scope Checker - Analyzes file dependencies and scope boundaries"""
import argparse, json, sys
from pathlib import Path

class FileScopeChecker:
    def __init__(self, plan_path):
        self.plan_path = Path(plan_path)
        self.violations = []

    def check(self):
        with open(self.plan_path) as f:
            data = json.load(f)

        manifest = data.get('plan', {}).get('file_manifest', {})
        phases = set(data.get('plan', {}).get('phases_by_id', {}).keys())

        for file_path, file_data in manifest.items():
            phase_id = file_data.get('phase_id')
            if phase_id and phase_id not in phases:
                self.violations.append(f"File {file_path} references unknown phase {phase_id}")

        return len(self.violations) == 0, {'violations': self.violations}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan-file', required=True, help='Path to plan JSON file')
    parser.add_argument('--evidence-dir', help='Evidence output directory (optional)')
    parser.add_argument('--output', default='file_scope_analysis.json')
    args = parser.parse_args()

    checker = FileScopeChecker(args.plan_file)
    is_valid, result = checker.check()

    with open(args.output, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"{'✅ PASSED' if is_valid else '❌ FAILED'}: File Scope Check")
    sys.exit(0 if is_valid else 1)

if __name__ == '__main__':
    main()
