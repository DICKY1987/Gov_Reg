#!/usr/bin/env python3
"""FM-02: Write Conflicts Detection"""
import argparse, json, sys
from pathlib import Path
from collections import defaultdict

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan-file', required=True, help='Path to plan JSON file')
    args = parser.parse_args()

    with open(args.plan_file) as f:
        data = json.load(f)

    artifacts = data.get('plan', {}).get('artifacts', {})
    conflicts = []

    writers = defaultdict(list)
    for aid, adata in artifacts.items():
        producer = adata.get('producer_phase')
        if producer:
            writers[aid].append(producer)

    for aid, producers in writers.items():
        if len(producers) > 1:
            conflicts.append({'artifact': aid, 'writers': producers})

    print(f"{'✅ PASSED' if not conflicts else '❌ CONFLICTS'}: {len(conflicts)} write conflicts")
    sys.exit(0 if not conflicts else 1)

if __name__ == '__main__':
    main()
