#!/usr/bin/env python3
# DOC_LINK: DOC-TEST-TESTS-RUN-ALL-TESTS-628
"""
Test Runner - Run all test suites

Discovers and runs all tests in the tests/ directory.

Usage:
    python run_all_tests.py              # Run all tests
    python run_all_tests.py -v           # Verbose output
    python run_all_tests.py --fast       # Skip slow integration tests
    python run_all_tests.py --coverage   # Run with coverage report
"""
DOC_ID: DOC-TEST-TESTS-RUN-ALL-TESTS-628

import sys
import unittest
from pathlib import Path
import DOC-ERROR-UTILS-TIME-145__time

# Add parent to path
.parent.parent))


def run_all_tests(verbosity=2, fast_mode=False):
    """
    Discover and run all tests

    Args:
        verbosity: Test output verbosity (0-2)
        fast_mode: Skip slow integration tests

    Returns:
        bool: True if all tests passed
    """
    start_time = time.time()

    print("=" * 70)
    print("PROCESS_STEP_LIB TEST SUITE")
    print("=" * 70)
    print()

    # Discover tests
    loader = unittest.TestLoader()
    start_dir = Path(__file__).parent
    suite = loader.discover(str(start_dir), pattern='test_*.py')

    # Count tests
    test_count = suite.countTestCases()
    print(f"Discovered {test_count} tests\n")

    if fast_mode:
        print("⚡ Fast mode: Skipping integration tests\n")
        # TODO: Implement filtering for fast mode

    # Run tests
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)

    # Print summary
    elapsed = time.time() - start_time

    print()
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failed: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    print(f"Time: {elapsed:.2f}s")
    print("=" * 70)

    if result.wasSuccessful():
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")

    return result.wasSuccessful()


def run_with_coverage():
    """Run tests with coverage report"""
    try:
        import coverage
    except ImportError:
        print("❌ coverage not installed")
        print("Install with: pip install coverage")
        return False

    print("Running tests with coverage...")
    print()

    # Start coverage
    cov = coverage.Coverage()
    cov.start()

    # Run tests
    success = run_all_tests(verbosity=2)

    # Stop coverage
    cov.stop()
    cov.save()

    # Generate report
    print()
    print("=" * 70)
    print("COVERAGE REPORT")
    print("=" * 70)
    print()

    cov.report()

    # Generate HTML report
    html_dir = Path(__file__).parent / 'htmlcov'
    cov.html_report(directory=str(html_dir))
    print(f"\nHTML report: {html_dir}/index.html")

    return success


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Run PROCESS_STEP_LIB test suite',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_all_tests.py              # Run all tests
  python run_all_tests.py -v           # Verbose output
  python run_all_tests.py --fast       # Skip slow tests
  python run_all_tests.py --coverage   # With coverage report
  python run_all_tests.py -q           # Quiet output
        """
    )

    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Verbose test output')
    parser.add_argument('-q', '--quiet', action='store_true',
                        help='Minimal test output')
    parser.add_argument('--fast', action='store_true',
                        help='Skip slow integration tests')
    parser.add_argument('--coverage', action='store_true',
                        help='Run with coverage report')

    args = parser.parse_args()

    # Determine verbosity
    if args.quiet:
        verbosity = 0
    elif args.verbose:
        verbosity = 2
    else:
        verbosity = 1

    # Run tests
    if args.coverage:
        success = run_with_coverage()
    else:
        success = run_all_tests(verbosity=verbosity, fast_mode=args.fast)

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
