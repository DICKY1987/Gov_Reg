#!/usr/bin/env python3
"""
Quality Scorer - Phase C Script
Produces: py_quality_score

Computes overall quality score from multiple metrics.
"""
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional


def compute_quality_score(metrics: Dict[str, Any]) -> float:
    """
    Compute quality score (0-100) from various metrics.

    Scoring breakdown:
    - Test coverage (25%): normalized to 0-1
    - Static issues (25%): inverse normalized (fewer = better)
    - Complexity (20%): inverse normalized (lower = better)
    - Has tests (10%): boolean
    - Has docstrings (10%): boolean
    - Security surface (10%): inverse (fewer operations = better)

    Returns score 0-100.
    """
    score = 0.0

    # 1. Test coverage (25 points)
    coverage = metrics.get("py_test_coverage_pct")
    if coverage is not None:
        score += (coverage / 100.0) * 25.0

    # 2. Static issues (25 points) - fewer is better
    static_issues = metrics.get("py_static_issues_count", 0)
    if static_issues == 0:
        score += 25.0
    elif static_issues < 10:
        score += (1.0 - (static_issues / 10.0)) * 25.0
    # else: 0 points

    # 3. Complexity (20 points) - lower is better
    complexity = metrics.get("py_cyclomatic_complexity", 0)
    if complexity == 0:
        score += 20.0
    elif complexity < 10:
        score += (1.0 - (complexity / 10.0)) * 20.0
    elif complexity < 20:
        score += (1.0 - ((complexity - 10) / 20.0)) * 10.0
    # else: 0 points

    # 4. Has tests (10 points)
    test_count = metrics.get("py_test_pass_count", 0) + metrics.get(
        "py_test_fail_count", 0
    )
    if test_count > 0:
        score += 10.0

    # 5. Has documentation (10 points)
    # Check if functions/classes have docstrings
    components = metrics.get("py_components_list", [])
    if components:
        with_docstrings = sum(1 for c in components if c.get("docstring"))
        doc_ratio = with_docstrings / len(components)
        score += doc_ratio * 10.0

    # 6. Security surface (10 points) - fewer risky operations = better
    security_ops = (
        metrics.get("py_file_operations_count", 0)
        + metrics.get("py_network_calls_count", 0)
        + metrics.get("py_security_calls_count", 0)
    )
    if security_ops == 0:
        score += 10.0
    elif security_ops < 5:
        score += (1.0 - (security_ops / 5.0)) * 10.0
    elif security_ops < 10:
        score += (1.0 - ((security_ops - 5) / 10.0)) * 5.0
    # else: 0 points

    return round(score, 2)


def calculate_quality_score(metrics_file: Path) -> dict:
    """
    Calculate quality score from metrics JSON.

    Returns dict with:
    - py_quality_score: float (0-100)
    - score_breakdown: Dict (per-category scores)
    - success: bool
    - error: Optional[str]
    """
    try:
        metrics = json.loads(metrics_file.read_text())

        score = compute_quality_score(metrics)

        # Compute breakdown for transparency
        breakdown = {
            "coverage_contribution": min(
                25, (metrics.get("py_test_coverage_pct", 0) / 100.0) * 25
            ),
            "static_issues_contribution": "calculated",
            "complexity_contribution": "calculated",
            "has_tests": (
                metrics.get("py_test_pass_count", 0)
                + metrics.get("py_test_fail_count", 0)
            )
            > 0,
            "documentation_ratio": "calculated",
            "security_score": "calculated",
        }

        return {
            "py_quality_score": score,
            "score_breakdown": breakdown,
            "success": True,
            "error": None,
        }

    except Exception as e:
        return {
            "py_quality_score": 0.0,
            "score_breakdown": {},
            "success": False,
            "error": f"Quality score calculation failed: {e}",
        }


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: quality_scorer.py <metrics.json>", file=sys.stderr)
        sys.exit(1)

    metrics_file = Path(sys.argv[1])

    if not metrics_file.exists():
        print(f"Error: Metrics file not found: {metrics_file}", file=sys.stderr)
        sys.exit(1)

    result = calculate_quality_score(metrics_file)

    if result["success"]:
        print(f"Quality score: {result['py_quality_score']}/100")
        print(f"\nBreakdown: {json.dumps(result['score_breakdown'], indent=2)}")
    else:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
