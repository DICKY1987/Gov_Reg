#!/usr/bin/env python3
"""FM-12: E2E Proof Linkage Gaps Validation"""
import argparse, json, sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan-file', required=True, help='Path to plan JSON file')
    args = parser.parse_args()
    
    with open(args.plan_file) as f:
        data = json.load(f)
    
    gates = data.get('plan', {}).get('gates_by_id', {})
    gaps = []
    
    for gid, gdata in gates.items():
        if not gdata.get('validation_command') or not gdata.get('success_pattern'):
            gaps.append(gid)
    
    print(f"{'✅ PASSED' if not gaps else '❌ GAPS'}: {len(gaps)} E2E linkage gaps")
    sys.exit(0 if not gaps else 1)

if __name__ == '__main__':
    main()
