# DOC_LINK: DOC-TEST-MASTER-SUITE-001
# DOC_ID: DOC-TEST-MASTER-SUITE-001
"""
Master Test Suite for Stable ID System
doc_id: DOC-TEST-MASTER-SUITE-001
Executes all tests across all ID types and layers
"""

import sys
import pytest
from pathlib import Path

# Add common modules to path
sys.path.insert(0, str(Path(__file__).parent.parent / "common"))

def run_all_tests():
    """Run complete test suite with detailed reporting"""

    test_dirs = [
        Path(__file__).parent,  # doc_id tests
        Path(__file__).parent.parent / "trigger_id" / "6_TESTS",
        Path(__file__).parent.parent / "pattern_id" / "6_TESTS",
    ]

    # Test discovery and execution
    args = [
        "-v",  # Verbose
        "--tb=short",  # Short traceback
        "--strict-markers",  # Strict marker checking
        "-ra",  # Show all test summary
        "--cov=.",  # Coverage for all modules
        "--cov-report=html",  # HTML coverage report
        "--cov-report=term-missing",  # Terminal report with missing lines
    ]

    # Add all test directories
    for test_dir in test_dirs:
        if test_dir.exists():
            args.append(str(test_dir))

    return pytest.main(args)

if __name__ == "__main__":
    sys.exit(run_all_tests())
