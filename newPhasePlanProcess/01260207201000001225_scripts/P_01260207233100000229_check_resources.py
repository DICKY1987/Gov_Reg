#!/usr/bin/env python3
"""Resource Checker - Checks resource availability and requirements"""
import argparse, json, sys, shutil
from pathlib import Path
import platform

class ResourceChecker:
    def __init__(self, plan_path):
        self.plan_path = Path(plan_path)
        self.warnings = []

    def check(self):
        # Check disk space
        stat = shutil.disk_usage(Path.cwd())
        free_gb = stat.free / (1024**3)
        if free_gb < 1:
            self.warnings.append(f"Low disk space: {free_gb:.2f}GB free")

        # Check Python version
        py_version = platform.python_version()
        if not py_version.startswith('3.'):
            self.warnings.append(f"Python version {py_version} (recommend 3.10+)")

        # Check common tools
        tools = ['git', 'python', 'pip']
        for tool in tools:
            if not shutil.which(tool):
                self.warnings.append(f"Tool not found: {tool}")

        return len(self.warnings) == 0, {
            'disk_free_gb': free_gb,
            'python_version': py_version,
            'platform': platform.system(),
            'warnings': self.warnings
        }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan-file', dest='plan_file', required=False)
    parser.add_argument('plan_file_positional', nargs='?')  # Accept positional too
    parser.add_argument('--output', default='resource_check.json')
    parser.add_argument('--evidence-dir', help='Evidence output directory (optional)', default='.state/evidence')

    args = parser.parse_args()



    # Use flag if provided, otherwise positional

    plan_file = args.plan_file or args.plan_file_positional

    if not plan_file:

        parser.error("plan_file is required (as --plan-file or positional argument)")

    args.plan_file = plan_file

    checker = ResourceChecker(args.plan_file)
    is_ok, result = checker.check()

    with open(args.output, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"{'✅ PASSED' if is_ok else '⚠️  WARNINGS'}: Resource Check")
    sys.exit(0)

if __name__ == '__main__':
    main()
