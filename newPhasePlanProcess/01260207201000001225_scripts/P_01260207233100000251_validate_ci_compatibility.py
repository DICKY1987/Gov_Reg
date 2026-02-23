#!/usr/bin/env python3
"""CI Compatibility Validator - Validates CI/CD pipeline compatibility"""
import argparse, json, sys
from pathlib import Path

class CICompatibilityValidator:
    def __init__(self, plan_path):
        self.plan_path = Path(plan_path)
        self.warnings = []

    def validate(self):
        with open(self.plan_path) as f:
            data = json.load(f)

        commands = data.get('plan', {}).get('commands', {})

        # Check for CI-unfriendly commands
        for cmd_id, cmd_data in commands.items():
            cmd = cmd_data.get('command', '')
            if 'sudo' in cmd:
                self.warnings.append(f"Command {cmd_id} uses sudo (may fail in CI)")
            if 'interactive' in cmd or '-i' in cmd:
                self.warnings.append(f"Command {cmd_id} may be interactive")

        return len(self.warnings) == 0, {
            'compatible': len(self.warnings) == 0,
            'warnings': self.warnings
        }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan-file', required=True, help='Path to plan JSON file')
    parser.add_argument('--evidence-dir', help='Evidence output directory (optional)')
    parser.add_argument('--output', default='ci_compatibility.json')
    args = parser.parse_args()

    validator = CICompatibilityValidator(args.plan_file)
    is_valid, result = validator.validate()

    with open(args.output, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"{'✅ PASSED' if is_valid else '⚠️  WARNINGS'}: CI Compatibility")
    sys.exit(0 if is_valid else 1)

if __name__ == '__main__':
    main()
