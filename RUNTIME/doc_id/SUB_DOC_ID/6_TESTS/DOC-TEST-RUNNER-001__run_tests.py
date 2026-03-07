# DOC_LINK: DOC-TEST-RUNNER-001
# DOC_ID: DOC-TEST-RUNNER-001
"""
Test Runner Script
doc_id: DOC-TEST-RUNNER-001
Convenient wrapper for running test suites
"""

import sys
import subprocess
from pathlib import Path
import argparse

def run_tests(args):
    """Run pytest with specified arguments"""

    test_path = Path(__file__).parent

    # Build pytest command
    cmd = [sys.executable, "-m", "pytest"]

    # Add test directory
    cmd.append(str(test_path))

    # Add verbosity
    if args.verbose:
        cmd.append("-vv")
    else:
        cmd.append("-v")

    # Add coverage if requested
    if args.coverage:
        cmd.extend([
            "--cov=.",
            "--cov-report=html",
            "--cov-report=term-missing"
        ])

    # Add specific test markers
    if args.marker:
        cmd.extend(["-m", args.marker])

    # Add specific test file
    if args.test_file:
        cmd.append(args.test_file)

    # Add parallel execution if requested
    if args.parallel:
        cmd.extend(["-n", "auto"])

    # Add other pytest args
    if args.pytest_args:
        cmd.extend(args.pytest_args)

    print(f"Running: {' '.join(cmd)}")
    print("-" * 80)

    # Execute
    result = subprocess.run(cmd, cwd=test_path.parent)
    return result.returncode

def main():
    parser = argparse.ArgumentParser(description="Run Stable ID System Tests")

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )

    parser.add_argument(
        "-c", "--coverage",
        action="store_true",
        help="Run with coverage report"
    )

    parser.add_argument(
        "-m", "--marker",
        help="Run tests with specific marker (syntax, registry, integration, etc.)"
    )

    parser.add_argument(
        "-f", "--test-file",
        help="Run specific test file"
    )

    parser.add_argument(
        "-p", "--parallel",
        action="store_true",
        help="Run tests in parallel (requires pytest-xdist)"
    )

    parser.add_argument(
        "pytest_args",
        nargs="*",
        help="Additional arguments to pass to pytest"
    )

    args = parser.parse_args()

    sys.exit(run_tests(args))

if __name__ == "__main__":
    main()
