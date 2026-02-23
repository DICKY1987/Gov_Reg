#!/usr/bin/env python3
"""FM-04: Dead Artifacts Detection"""
import argparse, json, sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan-file', required=True, help='Path to plan JSON file')
    args = parser.parse_args()

    with open(args.plan_file) as f:
        data = json.load(f)

    artifacts = data.get('plan', {}).get('artifacts', {})
    dead = []

    for aid, adata in artifacts.items():
        if not adata.get('producer_phase') and adata.get('consumer_phases'):
            dead.append(aid)

    print(f"{'✅ PASSED' if not dead else '❌ DEAD'}: {len(dead)} dead artifacts")
    sys.exit(0 if not dead else 1)

if __name__ == '__main__':
    main()
