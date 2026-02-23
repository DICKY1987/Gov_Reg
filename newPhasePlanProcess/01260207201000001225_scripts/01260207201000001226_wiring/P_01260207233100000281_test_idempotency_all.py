#!/usr/bin/env python3
"""FM-10: Idempotency Violations Test"""
import argparse, json, sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan-file', required=True, help='Path to plan JSON file')
    args = parser.parse_args()

    with open(args.plan_file) as f:
        data = json.load(f)

    commands = data.get('plan', {}).get('commands', {})
    violations = [cid for cid, cdata in commands.items() if cdata.get('idempotent') and 'rm -rf' in cdata.get('command', '')]

    print(f"{'✅ PASSED' if not violations else '❌ VIOLATIONS'}: {len(violations)} idempotency violations")
    sys.exit(0 if not violations else 1)

if __name__ == '__main__':
    main()
