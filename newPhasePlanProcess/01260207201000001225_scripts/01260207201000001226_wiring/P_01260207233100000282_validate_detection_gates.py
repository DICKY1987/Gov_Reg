#!/usr/bin/env python3
"""FM-11: Detection Gate Gaps Validation"""
import argparse, json, sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan-file', required=True, help='Path to plan JSON file')
    args = parser.parse_args()

    with open(args.plan_file) as f:
        data = json.load(f)

    phases = data.get('plan', {}).get('phases_by_id', {})
    gates = data.get('plan', {}).get('gates_by_id', {})

    gaps = [pid for pid, pdata in phases.items() if not pdata.get('validation_gates')]

    print(f"{'✅ PASSED' if not gaps else '⚠️  GAPS'}: {len(gaps)} detection gate gaps")
    sys.exit(0)

if __name__ == '__main__':
    main()
