#!/usr/bin/env python3
"""Secret Checker - Scans for exposed secrets and credentials"""
import argparse, json, sys, re
from pathlib import Path

class SecretChecker:
    def __init__(self, plan_path):
        self.plan_path = Path(plan_path)
        self.secrets_found = []

        # Common secret patterns
        self.patterns = [
            (r'(?i)(api[_-]?key|apikey)\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{20,})', 'API Key'),
            (r'(?i)(password|passwd|pwd)\s*[:=]\s*["\']?([^\s"\']{8,})', 'Password'),
            (r'(?i)(secret[_-]?key)\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{20,})', 'Secret Key'),
            (r'(?i)(aws[_-]?access[_-]?key[_-]?id)\s*[:=]\s*["\']?([A-Z0-9]{20})', 'AWS Access Key'),
        ]

    def scan(self):
        with open(self.plan_path) as f:
            content = f.read()

        for pattern, secret_type in self.patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                self.secrets_found.append({
                    'type': secret_type,
                    'location': f'Line {content[:match.start()].count(chr(10)) + 1}',
                    'matched': match.group(1)
                })

        return len(self.secrets_found) == 0, {
            'clean': len(self.secrets_found) == 0,
            'secrets_found': len(self.secrets_found),
            'details': self.secrets_found
        }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan-file', dest='plan_file', required=False)
    parser.add_argument('plan_file_positional', nargs='?')  # Accept positional too
    parser.add_argument('--output', default='secrets_scan.json')
    parser.add_argument('--evidence-dir', help='Evidence output directory (optional)', default='.state/evidence')

    args = parser.parse_args()



    # Use flag if provided, otherwise positional

    plan_file = args.plan_file or args.plan_file_positional

    if not plan_file:

        parser.error("plan_file is required (as --plan-file or positional argument)")

    args.plan_file = plan_file

    checker = SecretChecker(args.plan_file)
    is_clean, result = checker.scan()

    with open(args.output, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"{'✅ CLEAN' if is_clean else '❌ SECRETS FOUND'}: {result['secrets_found']} secrets detected")
    sys.exit(0 if is_clean else 1)

if __name__ == '__main__':
    main()
