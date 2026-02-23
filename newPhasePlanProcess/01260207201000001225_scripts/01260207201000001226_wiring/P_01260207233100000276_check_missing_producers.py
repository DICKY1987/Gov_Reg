#!/usr/bin/env python3
"""FM-05: Missing Producers Check"""
import argparse, json, sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan-file', required=True, help='Path to plan JSON file')
    args = parser.parse_args()

    with open(args.plan_file) as f:
        data = json.load(f)

    artifacts = data.get('plan', {}).get('artifacts', {})
    missing = []

    for aid, adata in artifacts.items():
        if not adata.get('producer_phase'):
            missing.append(aid)

    print(f"{'✅ PASSED' if not missing else '❌ MISSING'}: {len(missing)} missing producers")
    sys.exit(0 if not missing else 1)

if __name__ == '__main__':
    main()
