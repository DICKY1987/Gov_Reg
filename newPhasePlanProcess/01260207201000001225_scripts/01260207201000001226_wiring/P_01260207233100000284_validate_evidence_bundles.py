#!/usr/bin/env python3
"""FM-08: Evidence Bundle Gaps Validation"""
import argparse, json, sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan-file', required=True, help='Path to plan JSON file')
    args = parser.parse_args()

    with open(args.plan_file) as f:
        data = json.load(f)

    gates = data.get('plan', {}).get('gates_by_id', {})
    gaps = [gid for gid, gdata in gates.items() if not gdata.get('evidence_output')]

    print(f"{'✅ PASSED' if not gaps else '❌ GAPS'}: {len(gaps)} evidence gaps")
    sys.exit(0 if not gaps else 1)

if __name__ == '__main__':
    main()
