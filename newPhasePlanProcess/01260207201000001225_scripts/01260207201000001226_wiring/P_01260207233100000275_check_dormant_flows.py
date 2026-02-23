#!/usr/bin/env python3
"""FM-07: Dormant Flows Check"""
import argparse, json, sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan-file', required=True, help='Path to plan JSON file')
    args = parser.parse_args()

    with open(args.plan_file) as f:
        data = json.load(f)

    phases = data.get('plan', {}).get('phases_by_id', {})
    dormant = [pid for pid, pdata in phases.items() if not pdata.get('validation_gates')]

    print(f"{'✅ PASSED' if not dormant else '⚠️  DORMANT'}: {len(dormant)} dormant phases")
    sys.exit(0)

if __name__ == '__main__':
    main()
