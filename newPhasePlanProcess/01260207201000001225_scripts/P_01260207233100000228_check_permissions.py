#!/usr/bin/env python3
"""Permission Checker - Checks file and execution permissions"""
import argparse, json, sys, os
from pathlib import Path

class PermissionChecker:
    def __init__(self, plan_path):
        self.plan_path = Path(plan_path)
        self.errors = []

    def check(self):
        with open(self.plan_path) as f:
            data = json.load(f)

        manifest = data.get('plan', {}).get('file_manifest', {})

        for file_path, file_data in manifest.items():
            path = Path(file_path)
            if path.exists():
                # Check if we have required permissions
                perms = file_data.get('permissions', [])
                if 'write' in perms and not os.access(path, os.W_OK):
                    self.errors.append(f"No write permission: {file_path}")
                if 'read' in perms and not os.access(path, os.R_OK):
                    self.errors.append(f"No read permission: {file_path}")

        return len(self.errors) == 0, {
            'valid': len(self.errors) == 0,
            'errors': self.errors
        }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan-file', dest='plan_file', required=False)
    parser.add_argument('plan_file_positional', nargs='?')  # Accept positional too
    parser.add_argument('--output', default='permissions_check.json')
    parser.add_argument('--evidence-dir', default='.state/evidence/VAL-PERMISSIONS')
    args = parser.parse_args()

    # Use flag if provided, otherwise positional
    plan_file = args.plan_file or args.plan_file_positional
    if not plan_file:
        parser.error("plan_file is required (as --plan-file or positional argument)")

    checker = PermissionChecker(plan_file)
    is_valid, result = checker.check()

    # Write to evidence dir
    evidence_dir = Path(args.evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    output_path = evidence_dir / 'permissions_check.json' if args.output == 'permissions_check.json' else Path(args.output)

    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"{'✅ PASSED' if is_valid else '❌ FAILED'}: Permission Check")
    sys.exit(0 if is_valid else 1)

if __name__ == '__main__':
    main()
