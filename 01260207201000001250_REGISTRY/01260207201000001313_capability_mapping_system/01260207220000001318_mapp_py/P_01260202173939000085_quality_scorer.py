#!/usr/bin/env python3
"""
Quality Scorer - Composite Quality Metrics
DOC-SCRIPT-XXXX-QUALITY

Produces: py_quality_score (0-100)

Combines test coverage, lint results, complexity, and documentation
into a single quality score using weighted composite calculation.
"""
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Scoring weights (sum to 100)
WEIGHTS = {
    'tests': 30,        # Test existence and pass rate
    'coverage': 20,     # Code coverage percentage
    'docstrings': 20,   # Documentation completeness
    'lint': 15,         # Static analysis issues (inverted)
    'complexity': 15,   # Cyclomatic complexity (inverted)
}


def calculate_score(metrics: dict) -> int:
    """
    Calculate composite quality score.
    
    Args:
        metrics: Dict with py_* column values
        
    Returns:
        Score 0-100 (integer)
    """
    score = 0.0
    breakdown = {}
    
    # Tests component (0-30 points)
    tests_executed = metrics.get('py_tests_executed', False)
    pytest_exit_code = metrics.get('py_pytest_exit_code')
    
    if tests_executed:
        if pytest_exit_code == 0:
            tests_score = WEIGHTS['tests']
        elif pytest_exit_code is not None:
            tests_score = WEIGHTS['tests'] * 0.5  # Partial credit
        else:
            tests_score = WEIGHTS['tests'] * 0.3
    else:
        tests_score = 0
    
    score += tests_score
    breakdown['tests'] = {'weight': WEIGHTS['tests'], 'earned': tests_score}
    
    # Coverage component (0-20 points)
    coverage = metrics.get('py_coverage_percent')
    if coverage is not None and coverage > 0:
        coverage_score = WEIGHTS['coverage'] * (coverage / 100.0)
    else:
        coverage_score = 0
    
    score += coverage_score
    breakdown['coverage'] = {'weight': WEIGHTS['coverage'], 'earned': coverage_score}
    
    # Docstrings component (0-20 points)
    # Proxy: check if public API is documented
    has_public_api = metrics.get('py_defs_public_api_hash') is not None
    func_count = metrics.get('py_defs_functions_count', 0) or 0
    class_count = metrics.get('py_defs_classes_count', 0) or 0
    
    if has_public_api and (func_count + class_count) > 0:
        docstrings_score = WEIGHTS['docstrings']
    elif func_count + class_count == 0:
        docstrings_score = WEIGHTS['docstrings']  # No code = no doc requirement
    else:
        docstrings_score = WEIGHTS['docstrings'] * 0.3  # Partial credit
    
    score += docstrings_score
    breakdown['docstrings'] = {'weight': WEIGHTS['docstrings'], 'earned': docstrings_score}
    
    # Lint component (0-15 points) - fewer issues = higher score
    issues = metrics.get('py_static_issues_count')
    if issues is not None:
        if issues == 0:
            lint_score = WEIGHTS['lint']
        elif issues <= 5:
            lint_score = WEIGHTS['lint'] * 0.8
        elif issues <= 10:
            lint_score = WEIGHTS['lint'] * 0.5
        elif issues <= 20:
            lint_score = WEIGHTS['lint'] * 0.3
        else:
            lint_score = WEIGHTS['lint'] * 0.1
    else:
        lint_score = WEIGHTS['lint'] * 0.5  # Unknown = neutral
    
    score += lint_score
    breakdown['lint'] = {'weight': WEIGHTS['lint'], 'earned': lint_score}
    
    # Complexity component (0-15 points) - lower complexity = higher score
    complexity = metrics.get('py_complexity_cyclomatic')
    if complexity is not None:
        if complexity <= 5:
            complexity_score = WEIGHTS['complexity']
        elif complexity <= 10:
            complexity_score = WEIGHTS['complexity'] * 0.8
        elif complexity <= 20:
            complexity_score = WEIGHTS['complexity'] * 0.5
        elif complexity <= 30:
            complexity_score = WEIGHTS['complexity'] * 0.3
        else:
            complexity_score = WEIGHTS['complexity'] * 0.1
    else:
        complexity_score = WEIGHTS['complexity'] * 0.5  # Unknown = neutral
    
    score += complexity_score
    breakdown['complexity'] = {'weight': WEIGHTS['complexity'], 'earned': complexity_score}
    
    # Clamp to [0, 100]
    final_score = int(round(max(0, min(100, score))))
    
    return final_score


def generate_breakdown(metrics: dict, score: int) -> dict:
    """Generate detailed scoring breakdown for transparency."""
    
    # Recalculate for breakdown
    breakdown = {}
    
    # Recalculate each component (duplicate logic for clarity)
    tests_executed = metrics.get('py_tests_executed', False)
    pytest_exit_code = metrics.get('py_pytest_exit_code')
    
    if tests_executed and pytest_exit_code == 0:
        breakdown['tests'] = {'weight': WEIGHTS['tests'], 'earned': WEIGHTS['tests'], 'notes': 'Tests pass'}
    elif tests_executed:
        breakdown['tests'] = {'weight': WEIGHTS['tests'], 'earned': WEIGHTS['tests'] * 0.5, 'notes': 'Tests fail'}
    else:
        breakdown['tests'] = {'weight': WEIGHTS['tests'], 'earned': 0, 'notes': 'No tests'}
    
    coverage = metrics.get('py_coverage_percent', 0)
    breakdown['coverage'] = {
        'weight': WEIGHTS['coverage'],
        'earned': WEIGHTS['coverage'] * (coverage / 100.0) if coverage else 0,
        'notes': f'{coverage}% coverage' if coverage else 'No coverage'
    }
    
    # Docstrings component
    docstring_coverage = metrics.get('docstring_coverage', 0)
    breakdown['docstrings'] = {
        'weight': WEIGHTS.get('docstrings', 0.15),
        'earned': WEIGHTS.get('docstrings', 0.15) * (docstring_coverage / 100.0),
        'notes': f'{docstring_coverage}% docstring coverage'
    }
    
    # Lint component
    lint_issues = metrics.get('py_static_issues_count', 0)
    # Score decreases with more issues: 100 issues = 0 score, 0 issues = full score
    lint_earned = max(0, WEIGHTS.get('lint', 0.25) * (1 - lint_issues / 100.0))
    breakdown['lint'] = {
        'weight': WEIGHTS.get('lint', 0.25),
        'earned': lint_earned,
        'notes': f'{lint_issues} static issues'
    }
    
    # Complexity component
    complexity_avg = metrics.get('py_complexity_cyclomatic', 0)
    # Score decreases with higher complexity: 10+ = 0, <2 = full score
    complexity_factor = max(0, min(1, (10 - complexity_avg) / 8))
    breakdown['complexity'] = {
        'weight': WEIGHTS.get('complexity', 0.15),
        'earned': WEIGHTS.get('complexity', 0.15) * complexity_factor,
        'notes': f'Avg cyclomatic complexity: {complexity_avg:.1f}'
    }
    
    return {
        'total_score': score,
        'max_score': 100,
        'components': breakdown,
        'methodology': 'Weighted composite with deterministic calculation',
        'weights': WEIGHTS
    }


if __name__ == '__main__':
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description='Calculate quality score')
    parser.add_argument('--metrics-json', required=True, help='JSON file with py_* metrics')
    parser.add_argument('--output', help='Output JSON file')
    parser.add_argument('--verbose', action='store_true', help='Show breakdown')
    
    args = parser.parse_args()
    
    # Load metrics
    with open(args.metrics_json, 'r', encoding='utf-8') as f:
        metrics = json.load(f)
    
    # Calculate score
    score = calculate_score(metrics)
    breakdown = generate_breakdown(metrics, score) if args.verbose else None
    
    # Prepare output
    output = {
        'py_quality_score': score
    }
    if breakdown:
        output['breakdown'] = breakdown
    
    # Write or print
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, sort_keys=True)
        print(f"Quality score: {score}/100 → {args.output}", file=sys.stderr)
    else:
        print(json.dumps(output, indent=2, sort_keys=True))
    
    sys.exit(0)
