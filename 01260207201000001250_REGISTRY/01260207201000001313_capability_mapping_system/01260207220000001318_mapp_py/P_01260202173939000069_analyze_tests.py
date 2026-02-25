#!/usr/bin/env python3
"""
Test Runner - Phase C Script (Optional)
Produces: py_test_pass_count, py_test_fail_count, py_test_coverage_pct

Runs pytest on test files and collects metrics.
"""
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import re


def run_pytest(file_path: Path, project_root: Path) -> Dict[str, Any]:
    """
    Run pytest on a test file.

    Returns:
    - stdout: str
    - stderr: str
    - returncode: int
    - duration: float (seconds)
    """
    try:
        result = subprocess.run(
            ["pytest", str(file_path), "-v", "--tb=short"],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(project_root),
        )

        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }

    except subprocess.TimeoutExpired:
        return {
            "stdout": "",
            "stderr": "Test execution timed out (60s)",
            "returncode": -1,
        }

    except FileNotFoundError:
        return {
            "stdout": "",
            "stderr": "pytest not found - please install: pip install pytest",
            "returncode": -2,
        }

    except Exception as e:
        return {"stdout": "", "stderr": f"Test execution failed: {e}", "returncode": -3}


def parse_pytest_output(output: str) -> Dict[str, int]:
    """
    Parse pytest output to extract test counts.

    Looks for patterns like:
    - "5 passed"
    - "2 failed"
    - "1 error"
    """
    passed = 0
    failed = 0
    errors = 0

    # Match patterns like "5 passed", "2 failed", "1 error"
    passed_match = re.search(r"(\d+)\s+passed", output)
    if passed_match:
        passed = int(passed_match.group(1))

    failed_match = re.search(r"(\d+)\s+failed", output)
    if failed_match:
        failed = int(failed_match.group(1))

    error_match = re.search(r"(\d+)\s+error", output)
    if error_match:
        errors = int(error_match.group(1))

    return {
        "passed": passed,
        "failed": failed + errors,  # Combine failures and errors
        "total": passed + failed + errors,
    }


def run_coverage(file_path: Path, project_root: Path) -> Optional[float]:
    """
    Run pytest with coverage to get coverage percentage.

    Returns coverage percentage or None if coverage not available.
    """
    try:
        result = subprocess.run(
            ["pytest", str(file_path), "--cov", "--cov-report=term"],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(project_root),
        )

        # Parse coverage from output
        # Looks for: "TOTAL    123    45    63%"
        coverage_match = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", result.stdout)
        if coverage_match:
            return float(coverage_match.group(1))

        return None

    except Exception:
        return None


def analyze_tests(file_path: Path, project_root: Optional[Path] = None) -> dict:
    """
    Run tests and collect metrics.

    Returns dict with:
    - py_test_pass_count: int
    - py_test_fail_count: int
    - py_test_coverage_pct: Optional[float]
    - success: bool
    - error: Optional[str]
    """
    if project_root is None:
        project_root = file_path.parent

    try:
        # Run pytest
        result = run_pytest(file_path, project_root)

        if result["returncode"] < 0:
            # Execution error
            raise Exception(result["stderr"])

        # Parse test counts
        counts = parse_pytest_output(result["stdout"])

        # Try to get coverage
        coverage = run_coverage(file_path, project_root)

        return {
            "py_test_pass_count": counts["passed"],
            "py_test_fail_count": counts["failed"],
            "py_test_total_count": counts["total"],
            "py_test_coverage_pct": coverage,
            "test_output": result["stdout"],
            "success": True,
            "error": None,
        }

    except Exception as e:
        return {
            "py_test_pass_count": 0,
            "py_test_fail_count": 0,
            "py_test_total_count": 0,
            "py_test_coverage_pct": None,
            "test_output": "",
            "success": False,
            "error": f"Test analysis failed: {e}",
        }


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: test_runner.py <test_file> [project_root]", file=sys.stderr)
        sys.exit(1)

    file_path = Path(sys.argv[1])
    project_root = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    if not file_path.exists():
        print(f"Error: Test file not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    result = analyze_tests(file_path, project_root)

    if result["success"]:
        print(f"Passed: {result['py_test_pass_count']}")
        print(f"Failed: {result['py_test_fail_count']}")
        print(f"Total: {result['py_test_total_count']}")
        if result["py_test_coverage_pct"] is not None:
            print(f"Coverage: {result['py_test_coverage_pct']}%")
    else:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
