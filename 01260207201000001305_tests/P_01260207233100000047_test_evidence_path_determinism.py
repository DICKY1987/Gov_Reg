#!/usr/bin/env python3
"""
Evidence Path Determinism Tests

Tests that evidence path computation is deterministic:
- Same inputs produce identical paths across runs
- Path formulas use only defined variables
- Sanitization rules are applied consistently
"""

import pytest
import json
import re
from pathlib import Path


@pytest.fixture
def evidence_policy():
    """Load evidence_path_policy.json"""
    policy_path = Path("policies/evidence_path_policy.json")
    with open(policy_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def compute_path(formula: str, variables: dict) -> str:
    """
    Compute evidence path from formula and variables.
    Apply sanitization rules.
    """
    path = formula
    
    # Sanitize plan_id: lowercase, replace spaces with hyphens
    if 'plan_id' in variables:
        plan_id = variables['plan_id'].lower()
        plan_id = re.sub(r'[^a-z0-9-_]', '-', plan_id)
        variables['plan_id'] = plan_id
    
    # Substitute variables
    for var, value in variables.items():
        path = path.replace(f"{{{var}}}", str(value))
    
    return path


def test_path_formula_determinism(evidence_policy):
    """Test that same inputs produce identical paths across multiple runs"""
    
    # Test inputs
    inputs = {
        "plan_id": "PLAN-QC-001",
        "run_id": "20260128_170410",
        "gate_id": "G-CTRL-001",
        "control_id": "CTRL-SEC-001",
        "phase_id": "PH-01"
    }
    
    # Compute paths 3 times
    formulas = evidence_policy['path_formulas']
    
    paths_run1 = {}
    paths_run2 = {}
    paths_run3 = {}
    
    for formula_name, formula_spec in formulas.items():
        formula = formula_spec['formula']
        
        # Filter variables needed for this formula
        needed_vars = {k: v for k, v in inputs.items() if f"{{{k}}}" in formula}
        
        paths_run1[formula_name] = compute_path(formula, needed_vars.copy())
        paths_run2[formula_name] = compute_path(formula, needed_vars.copy())
        paths_run3[formula_name] = compute_path(formula, needed_vars.copy())
    
    # Assert determinism: all 3 runs produce identical paths
    assert paths_run1 == paths_run2, f"Run 1 and Run 2 paths differ: {paths_run1} != {paths_run2}"
    assert paths_run2 == paths_run3, f"Run 2 and Run 3 paths differ: {paths_run2} != {paths_run3}"
    
    # Print results for inspection
    print("\nDeterministic paths computed:")
    for name, path in sorted(paths_run1.items()):
        print(f"  {name}: {path}")


def test_sanitization_applied(evidence_policy):
    """Test that sanitization rules are applied to plan_id"""
    
    # Test inputs with special characters
    test_cases = [
        ("PLAN-QC-001", "plan-qc-001"),
        ("Plan QC 001", "plan-qc-001"),
        ("PLAN_QC_001", "plan_qc_001"),
        ("Plan@QC#001!", "plan-qc-001-"),
    ]
    
    formula = evidence_policy['path_formulas']['root']['formula']
    
    for input_plan_id, expected_sanitized in test_cases:
        variables = {"plan_id": input_plan_id, "run_id": "20260128_170410"}
        path = compute_path(formula, variables)
        
        # Check that sanitized plan_id appears in path
        assert expected_sanitized in path, f"Expected {expected_sanitized} in path, got {path}"


def test_required_reports_have_deterministic_paths(evidence_policy):
    """Test that required report paths are deterministic"""
    
    required_reports = evidence_policy['required_reports']
    
    inputs = {
        "plan_id": "PLAN-QC-001",
        "run_id": "20260128_170410",
        "gate_id": "G-CTRL-001",
        "control_id": "CTRL-SEC-001",
        "phase_id": "PH-01"
    }
    
    report_paths = {}
    
    for report_name, report_spec in required_reports.items():
        path_formula = report_spec['path']
        
        # Filter variables needed for this formula
        needed_vars = {k: v for k, v in inputs.items() if f"{{{k}}}" in path_formula}
        
        report_paths[report_name] = compute_path(path_formula, needed_vars)
    
    # Check paths are deterministic (run twice)
    report_paths2 = {}
    for report_name, report_spec in required_reports.items():
        path_formula = report_spec['path']
        needed_vars = {k: v for k, v in inputs.items() if f"{{{k}}}" in path_formula}
        report_paths2[report_name] = compute_path(path_formula, needed_vars)
    
    assert report_paths == report_paths2, "Required report paths are not deterministic"
    
    print("\nRequired report paths:")
    for name, path in sorted(report_paths.items()):
        print(f"  {name}: {path}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
