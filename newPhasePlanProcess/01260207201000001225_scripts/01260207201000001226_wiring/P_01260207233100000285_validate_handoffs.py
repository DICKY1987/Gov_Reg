#!/usr/bin/env python3
"""FM-03: Incomplete Handoffs Validation"""
import argparse, json, sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan-file', required=True, help='Path to plan JSON file')
    args = parser.parse_args()

    with open(args.plan_file) as f:
        data = json.load(f)

    artifacts = data.get('plan', {}).get('artifacts', {})
    incomplete = []

    for aid, adata in artifacts.items():
        if not adata.get('schema_ref') or not adata.get('location'):
            incomplete.append(aid)

    print(f"{'✅ PASSED' if not incomplete else '❌ INCOMPLETE'}: {len(incomplete)} incomplete handoffs")
    sys.exit(0 if not incomplete else 1)

if __name__ == '__main__':
    main()
