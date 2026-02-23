#!/usr/bin/env python3
"""
GATE-016: Verification Completeness Validation

Validates that every step has postconditions covering:
- Output validation (all outputs have corresponding postconditions)
- Change detection (unintended side effects are checked)
- Evidence paths are specified for audit trail

Replaces FM-08 (evidence bundle gaps)
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple, Set
from datetime import datetime


def validate_verification_completeness(
    plan: Dict[str, Any]
) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Validate verification completeness across all steps.

    Returns:
        Tuple of (passed: bool, defects: list)
    """
    defects = []

    phases = plan.get("plan", {}).get("phases", [])

    if not phases:
        defects.append(
            {
                "severity": "critical",
                "category": "missing_field",
                "location": "/plan/phases",
                "problem": "No phases defined in plan",
                "why_it_matters": "Cannot validate verification without phases",
            }
        )
        return False, defects

    # Statistics
    total_steps = 0
    steps_with_outputs = 0
    steps_with_insufficient_verification = 0
    steps_missing_evidence_paths = 0

    # Validate each step's verification
    for phase_idx, phase in enumerate(phases):
        phase_id = phase.get("phase_id", f"P{phase_idx:02d}")
        steps = phase.get("steps", [])

        for step_idx, step in enumerate(steps):
            total_steps += 1
            step_id = step.get("step_id", f"S{step_idx:03d}")
            location = f"/plan/phases/{phase_idx}/steps/{step_idx}"

            outputs = step.get("outputs", [])
            postconditions = step.get("postconditions", [])

            has_outputs = len(outputs) > 0
            if has_outputs:
                steps_with_outputs += 1

            # Check 1: Every step with outputs must validate those outputs
            if has_outputs:
                coverage_defects = check_output_coverage(
                    outputs, postconditions, step_id, location
                )
                defects.extend(coverage_defects)

                if coverage_defects:
                    steps_with_insufficient_verification += 1

            # Check 2: Postconditions should check for unintended side effects
            side_effect_defects = check_side_effect_detection(
                postconditions, step_id, location
            )
            defects.extend(side_effect_defects)

            # Check 3: Evidence paths should be present
            evidence_path_defects = check_evidence_paths(
                postconditions, step_id, location
            )
            defects.extend(evidence_path_defects)

            if evidence_path_defects:
                steps_missing_evidence_paths += 1

            # Check 4: Postcondition types should be appropriate
            type_defects = check_postcondition_types(
                postconditions, outputs, step_id, location
            )
            defects.extend(type_defects)

    # Add summary
    defects.insert(
        0,
        {
            "severity": "info",
            "category": "other",
            "location": "/plan/phases",
            "problem": f"Verification summary: {total_steps} total steps, {steps_with_outputs} with outputs, {steps_with_insufficient_verification} insufficient verification, {steps_missing_evidence_paths} missing evidence paths",
            "why_it_matters": "Summary statistics for verification completeness analysis",
        },
    )

    # Pass if no critical/high severity defects
    critical_defects = [d for d in defects if d["severity"] in ["critical", "high"]]
    passed = len(critical_defects) == 0

    return passed, defects


def check_output_coverage(
    outputs: List[Dict[str, Any]],
    postconditions: List[Dict[str, Any]],
    step_id: str,
    location: str,
) -> List[Dict[str, Any]]:
    """Check that all outputs have corresponding verification."""
    defects = []

    if not outputs:
        return defects

    output_artifact_ids = {
        out.get("artifact_id") for out in outputs if out.get("artifact_id")
    }

    # Count postconditions that validate existence/content of outputs
    validation_criteria = 0
    for criteria in postconditions:
        criteria_type = criteria.get("type")
        # These criteria types validate outputs
        if criteria_type in [
            "exists",
            "json_valid",
            "schema_valid",
            "hash_equals",
            "contains",
        ]:
            validation_criteria += 1

    # Heuristic: should have at least one validation per output
    expected_min_criteria = len(output_artifact_ids)

    if validation_criteria < expected_min_criteria:
        defects.append(
            {
                "severity": "high",
                "category": "verification_gap",
                "location": f"{location}/postconditions",
                "problem": f"Step {step_id} produces {len(output_artifact_ids)} artifacts but has only {validation_criteria} validation criteria (expected at least {expected_min_criteria})",
                "why_it_matters": "Each output should be validated (exists, valid format, correct content)",
            }
        )

    # Check for 'exists' criteria (basic check)
    exists_count = sum(1 for c in postconditions if c.get("type") == "exists")
    if exists_count == 0 and len(output_artifact_ids) > 0:
        defects.append(
            {
                "severity": "medium",
                "category": "verification_gap",
                "location": f"{location}/postconditions",
                "problem": f"Step {step_id} produces artifacts but has no 'exists' postcondition",
                "why_it_matters": "Should verify output files were actually created",
            }
        )

    return defects


def check_side_effect_detection(
    postconditions: List[Dict[str, Any]], step_id: str, location: str
) -> List[Dict[str, Any]]:
    """Check that postconditions detect unintended side effects."""
    defects = []

    # Look for change detection criteria
    change_detection_types = ["diff_empty", "hash_equals", "not_exists"]
    has_change_detection = any(
        c.get("type") in change_detection_types for c in postconditions
    )

    if not has_change_detection:
        defects.append(
            {
                "severity": "low",
                "category": "verification_gap",
                "location": f"{location}/postconditions",
                "problem": f"Step {step_id} has no change detection postconditions (diff_empty, hash_equals, or not_exists)",
                "why_it_matters": "Change detection helps catch unintended side effects",
            }
        )

    return defects


def check_evidence_paths(
    postconditions: List[Dict[str, Any]], step_id: str, location: str
) -> List[Dict[str, Any]]:
    """Check that postconditions specify evidence paths."""
    defects = []

    missing_evidence_count = 0
    for idx, criteria in enumerate(postconditions):
        if "evidence_path" not in criteria:
            missing_evidence_count += 1

    if missing_evidence_count > 0:
        defects.append(
            {
                "severity": "low",
                "category": "verification_gap",
                "location": f"{location}/postconditions",
                "problem": f"Step {step_id} has {missing_evidence_count} postconditions without evidence_path",
                "why_it_matters": "Evidence paths enable audit trail for verification",
            }
        )

    return defects


def check_postcondition_types(
    postconditions: List[Dict[str, Any]],
    outputs: List[Dict[str, Any]],
    step_id: str,
    location: str,
) -> List[Dict[str, Any]]:
    """Check that postcondition types are appropriate for outputs."""
    defects = []

    # If outputs include .json files, should have json_valid or schema_valid
    json_outputs = [out for out in outputs if out.get("path", "").endswith(".json")]

    if json_outputs:
        has_json_validation = any(
            c.get("type") in ["json_valid", "schema_valid"] for c in postconditions
        )

        if not has_json_validation:
            defects.append(
                {
                    "severity": "medium",
                    "category": "verification_gap",
                    "location": f"{location}/postconditions",
                    "problem": f"Step {step_id} produces JSON files but has no json_valid or schema_valid postcondition",
                    "why_it_matters": "JSON outputs should be validated for correctness",
                }
            )

    # If outputs include schema files, should have schema_valid
    schema_outputs = [out for out in outputs if "schema" in out.get("path", "").lower()]

    if schema_outputs:
        has_schema_validation = any(
            c.get("type") == "schema_valid" for c in postconditions
        )

        if not has_schema_validation:
            defects.append(
                {
                    "severity": "medium",
                    "category": "verification_gap",
                    "location": f"{location}/postconditions",
                    "problem": f"Step {step_id} produces schema files but has no schema_valid postcondition",
                    "why_it_matters": "Schema files should be validated against JSON Schema metaschema",
                }
            )

    return defects


def write_evidence(
    evidence_dir: Path, passed: bool, defects: List[Dict[str, Any]]
) -> None:
    """Write evidence artifacts."""
    evidence_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().isoformat() + "Z"

    summary = {
        "timestamp": timestamp,
        "gate_id": "GATE-016",
        "gate_name": "Verification Completeness Validation",
        "passed": passed,
        "defect_count": len(defects),
        "defects": defects,
    }

    summary_path = evidence_dir / "verification_completeness_validation.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"Evidence written to: {summary_path}")


def main():
    parser = argparse.ArgumentParser(
        description="GATE-016: Validate verification completeness in v3.0.0 plan"
    )
    parser.add_argument("--plan-file", required=True, help="Path to plan JSON file")
    parser.add_argument(
        "--evidence-dir",
        default=".state/evidence/GATE-016",
        help="Directory for evidence output (default: .state/evidence/GATE-016)",
    )

    args = parser.parse_args()

    # Load plan
    try:
        with open(args.plan_file, "r", encoding="utf-8") as f:
            plan = json.load(f)
    except FileNotFoundError:
        print(f"Error: Plan file not found: {args.plan_file}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in plan file: {e}", file=sys.stderr)
        sys.exit(1)

    # Validate
    passed, defects = validate_verification_completeness(plan)

    # Write evidence
    evidence_dir = Path(args.evidence_dir)
    write_evidence(evidence_dir, passed, defects)

    # Print results
    summary_defects = [d for d in defects if d["severity"] == "info"]
    other_defects = [d for d in defects if d["severity"] != "info"]

    if summary_defects:
        print(summary_defects[0]["problem"])

    if passed:
        print("✓ GATE-016 PASSED: Verification completeness is valid")
        if other_defects:
            print(f"  ({len(other_defects)} warnings - see evidence file)")
        sys.exit(0)
    else:
        print(f"✗ GATE-016 FAILED: {len(other_defects)} defects found")
        for defect in other_defects[:5]:
            if defect["severity"] in ["critical", "high"]:
                print(f"  [{defect['severity']}] {defect['problem']}")
        if len(other_defects) > 5:
            print(
                f"  ... and {len(other_defects) - 5} more defects (see evidence file)"
            )
        sys.exit(1)


if __name__ == "__main__":
    main()
