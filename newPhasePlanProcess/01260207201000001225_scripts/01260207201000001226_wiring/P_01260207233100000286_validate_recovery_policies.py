#!/usr/bin/env python3
"""FM-09: Recovery Policy Gaps Validation"""
import argparse, json, sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan-file', required=True, help='Path to plan JSON file')
    args = parser.parse_args()
    
    with open(args.plan_file) as f:
        data = json.load(f)
    
    commands = data.get('plan', {}).get('commands', {})
    gaps = [cid for cid, cdata in commands.items() if not cdata.get('retry_policy')]
    
    has_gaps = len(gaps) > 0
    print(f"{'✅ PASSED' if not has_gaps else '⚠️  GAPS'}: {len(gaps)} recovery policy gaps")
    sys.exit(1 if has_gaps else 0)

if __name__ == '__main__':
    main()
