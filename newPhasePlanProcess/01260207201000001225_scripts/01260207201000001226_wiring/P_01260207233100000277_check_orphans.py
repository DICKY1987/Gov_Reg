#!/usr/bin/env python3
"""FM-01: Orphaned Artifacts Detection"""
import argparse, json, sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan-file', required=True, help='Path to plan JSON file')
    args = parser.parse_args()

    with open(args.plan_file) as f:
        data = json.load(f)

    artifacts = data.get('plan', {}).get('artifacts', {})
    orphans = []

    for aid, adata in artifacts.items():
        if not adata.get('consumer_phases'):
            orphans.append(aid)

    print(f"{'✅ PASSED' if not orphans else '❌ ORPHANS'}: {len(orphans)} orphaned artifacts")
    sys.exit(0 if not orphans else 1)

if __name__ == '__main__':
    main()
