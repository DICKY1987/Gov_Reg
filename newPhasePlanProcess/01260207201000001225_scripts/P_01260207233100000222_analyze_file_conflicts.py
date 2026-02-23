#!/usr/bin/env python3
"""File Conflict Analyzer - Detects write conflicts and race conditions"""
import argparse, json, sys
from pathlib import Path
from collections import defaultdict

class FileConflictAnalyzer:
    def __init__(self, plan_path):
        self.plan_path = Path(plan_path)
        self.conflicts = []

    def analyze(self):
        with open(self.plan_path) as f:
            data = json.load(f)

        manifest = data.get('plan', {}).get('file_manifest', {})
        writers = defaultdict(list)

        for file_path, file_data in manifest.items():
            perms = file_data.get('permissions', [])
            phase = file_data.get('phase_id', 'unknown')
            if 'write' in perms or 'create' in perms:
                writers[file_path].append(phase)

        for file_path, phases in writers.items():
            if len(phases) > 1:
                self.conflicts.append({
                    'file': file_path,
                    'writers': phases,
                    'risk': 'high' if len(phases) > 2 else 'medium'
                })

        return len(self.conflicts) == 0, {
            'total_conflicts': len(self.conflicts),
            'conflicts': self.conflicts
        }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan-file', dest='plan_file', required=False)
    parser.add_argument('plan_file_positional', nargs='?')  # Accept positional too
    parser.add_argument('--output', default='file_conflicts.json')
    parser.add_argument('--evidence-dir', help='Evidence output directory (optional)', default='.state/evidence')

    args = parser.parse_args()



    # Use flag if provided, otherwise positional

    plan_file = args.plan_file or args.plan_file_positional

    if not plan_file:

        parser.error("plan_file is required (as --plan-file or positional argument)")

    args.plan_file = plan_file

    analyzer = FileConflictAnalyzer(args.plan_file)
    is_valid, result = analyzer.analyze()

    with open(args.output, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"{'✅ PASSED' if is_valid else '❌ FAILED'}: {result['total_conflicts']} conflicts found")
    sys.exit(0 if is_valid else 1)

if __name__ == '__main__':
    main()
