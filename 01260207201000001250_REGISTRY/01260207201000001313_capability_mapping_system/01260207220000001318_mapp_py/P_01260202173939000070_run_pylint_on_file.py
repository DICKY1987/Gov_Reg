#!/usr/bin/env python3
"""
Linter Runner - Phase C Script (Optional)
Produces: py_static_issues_count

Runs static analysis tools (pylint/flake8/mypy) and counts issues.
"""
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List
import re


def run_pylint(file_path: Path) -> Dict[str, Any]:
    """Run pylint on file."""
    try:
        result = subprocess.run(
            ["pylint", str(file_path), "--output-format=json"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.stdout:
            issues = json.loads(result.stdout)
            return {"tool": "pylint", "issues": issues, "count": len(issues)}

        return {"tool": "pylint", "issues": [], "count": 0}

    except FileNotFoundError:
        return {"tool": "pylint", "error": "not installed", "count": 0}
    except Exception as e:
        return {"tool": "pylint", "error": str(e), "count": 0}


def run_flake8(file_path: Path) -> Dict[str, Any]:
    """Run flake8 on file."""
    try:
        result = subprocess.run(
            ["flake8", str(file_path)], capture_output=True, text=True, timeout=30
        )

        # Count lines in output (each line is one issue)
        issues = [line for line in result.stdout.strip().split("\n") if line]

        return {"tool": "flake8", "issues": issues, "count": len(issues)}

    except FileNotFoundError:
        return {"tool": "flake8", "error": "not installed", "count": 0}
    except Exception as e:
        return {"tool": "flake8", "error": str(e), "count": 0}


def run_mypy(file_path: Path) -> Dict[str, Any]:
    """Run mypy on file."""
    try:
        result = subprocess.run(
            ["mypy", str(file_path), "--no-error-summary"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Count lines with errors
        issues = [
            line for line in result.stdout.strip().split("\n") if ": error:" in line
        ]

        return {"tool": "mypy", "issues": issues, "count": len(issues)}

    except FileNotFoundError:
        return {"tool": "mypy", "error": "not installed", "count": 0}
    except Exception as e:
        return {"tool": "mypy", "error": str(e), "count": 0}


def analyze_static_issues(file_path: Path) -> dict:
    """
    Run static analysis tools and aggregate results.

    Returns dict with:
    - py_static_issues_count: int (total issues across all tools)
    - tool_results: List[Dict] (per-tool breakdown)
    - success: bool
    - error: Optional[str]
    """
    try:
        results = []
        total_issues = 0

        # Run all available tools
        pylint_result = run_pylint(file_path)
        results.append(pylint_result)
        if "error" not in pylint_result:
            total_issues += pylint_result["count"]

        flake8_result = run_flake8(file_path)
        results.append(flake8_result)
        if "error" not in flake8_result:
            total_issues += flake8_result["count"]

        mypy_result = run_mypy(file_path)
        results.append(mypy_result)
        if "error" not in mypy_result:
            total_issues += mypy_result["count"]

        return {
            "py_static_issues_count": total_issues,
            "tool_results": results,
            "success": True,
            "error": None,
        }

    except Exception as e:
        return {
            "py_static_issues_count": 0,
            "tool_results": [],
            "success": False,
            "error": f"Static analysis failed: {e}",
        }


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: linter_runner.py <file_path>", file=sys.stderr)
        sys.exit(1)

    file_path = Path(sys.argv[1])

    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    result = analyze_static_issues(file_path)

    if result["success"]:
        print(f"Total static issues: {result['py_static_issues_count']}")
        print("\nPer-tool breakdown:")
        for tool_result in result["tool_results"]:
            tool = tool_result["tool"]
            if "error" in tool_result:
                print(f"  {tool}: {tool_result['error']}")
            else:
                print(f"  {tool}: {tool_result['count']} issues")
    else:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
