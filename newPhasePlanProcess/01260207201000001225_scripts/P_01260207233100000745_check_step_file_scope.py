#!/usr/bin/env python3
"""
Step File Scope Validator

Validates that a step's file mutations are within its declared file_scope.

Exit codes:
  0 = All mutations within scope
  1 = Scope violation detected
  2 = Plan structure error
"""

import json
import argparse
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from fnmatch import fnmatch
from datetime import datetime


def matches_any_pattern(path: str, patterns: List[str]) -> bool:
    """Check if path matches any glob pattern in list."""
    return any(fnmatch(path, pattern) for pattern in patterns)


def find_phase(plan: Dict[str, Any], phase_id: str) -> Optional[Dict[str, Any]]:
    """Find phase by ID."""
    phases = plan.get("plan", {}).get("phases", [])
    for phase in phases:
        if phase.get("phase_id") == phase_id:
            return phase
    return None


def find_step(phase: Dict[str, Any], step_id: str) -> Optional[Dict[str, Any]]:
    """Find step by ID within phase."""
    steps = phase.get("steps", [])
    for step in steps:
        if step.get("step_id") == step_id:
            return step
    return None


def validate_step_file_scope(
    plan: Dict[str, Any], phase_id: str, step_id: str
) -> Tuple[bool, List[str]]:
    """Validate step file scope against mutations."""
    defects = []

    # Extract phase and step
    phase = find_phase(plan, phase_id)
    if not phase:
        defects.append(f"Phase {phase_id} not found in plan")
        return False, defects

    step = find_step(phase, step_id)
    if not step:
        defects.append(f"Step {step_id} not found in phase {phase_id}")
        return False, defects

    # Get file scope
    file_scope = step.get("file_scope", {})
    allowed = file_scope.get("allowed_paths", [])
    forbidden = file_scope.get("forbidden_paths", [])
    read_only = file_scope.get("read_only_paths", [])

    # If no file scope defined, warn but don't fail
    if not file_scope:
        defects.append(
            f"WARNING: Step {step_id} has no file_scope defined (recommended)"
        )
        # Don't return False - missing scope is a warning, not a failure
        return True, defects

    # Get step outputs (files this step creates/modifies)
    outputs = step.get("outputs", [])

    # Validate each output against scope
    for idx, output in enumerate(outputs):
        path = output.get("path", "")
        output_type = output.get("type", "")

        if output_type in ["file", "dir"]:
            # Check allowed
            if allowed and not matches_any_pattern(path, allowed):
                defects.append(
                    f"Output {path} not in allowed_paths (output index {idx})"
                )

            # Check forbidden
            if forbidden and matches_any_pattern(path, forbidden):
                defects.append(
                    f"Output {path} matches forbidden_paths (output index {idx})"
                )

            # Check read-only (for modifications)
            is_modify = (
                output.get("mutation_type") == "modify"
                or output.get("action") == "modify"
            )
            if is_modify and read_only and matches_any_pattern(path, read_only):
                defects.append(
                    f"Cannot modify read-only path {path} (output index {idx})"
                )

    # Also check inputs that are read-only violations
    inputs = step.get("inputs", [])
    for idx, inp in enumerate(inputs):
        path = inp.get("path", "")
        input_type = inp.get("type", "")

        if input_type in ["file", "dir"]:
            # Inputs shouldn't be in forbidden paths
            if forbidden and matches_any_pattern(path, forbidden):
                defects.append(
                    f"Input {path} matches forbidden_paths (input index {idx})"
                )

    return len(defects) == 0, defects


def write_evidence(
    evidence_dir: Path, phase_id: str, step_id: str, passed: bool, defects: List[str]
) -> None:
    """Write evidence artifacts."""
    evidence_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().isoformat() + "Z"

    evidence = {
        "timestamp": timestamp,
        "validator": "check_step_file_scope.py",
        "phase_id": phase_id,
        "step_id": step_id,
        "passed": passed,
        "defect_count": len(defects),
        "defects": defects,
    }

    evidence_file = evidence_dir / f"{phase_id}_{step_id}_file_scope.json"
    with open(evidence_file, "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2)

    print(f"Evidence written to: {evidence_file}")


def main():
    parser = argparse.ArgumentParser(description="Validate step file scope")
    parser.add_argument("--plan-file", required=True, help="Path to plan JSON")
    parser.add_argument(
        "--phase-id", required=True, help="Phase ID (e.g., PH-03A)"
    )
    parser.add_argument(
        "--step-id", required=True, help="Step ID (e.g., STEP-001)"
    )
    parser.add_argument(
        "--evidence-dir",
        default=".state/evidence/file_scope",
        help="Evidence directory",
    )

    args = parser.parse_args()

    # Load plan
    try:
        with open(args.plan_file, "r", encoding="utf-8") as f:
            plan = json.load(f)
    except FileNotFoundError:
        print(f"Error: Plan file not found: {args.plan_file}", file=sys.stderr)
        sys.exit(2)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in plan file: {e}", file=sys.stderr)
        sys.exit(2)

    # Validate
    passed, defects = validate_step_file_scope(plan, args.phase_id, args.step_id)

    # Write evidence
    evidence_dir = Path(args.evidence_dir)
    write_evidence(evidence_dir, args.phase_id, args.step_id, passed, defects)

    # Exit
    if passed:
        print(f"✓ File scope validation PASSED for {args.step_id}")
        if defects:
            print("  Warnings:")
            for defect in defects:
                print(f"    - {defect}")
        sys.exit(0)
    else:
        print(f"✗ File scope validation FAILED for {args.step_id}:")
        for defect in defects:
            print(f"  - {defect}")
        sys.exit(1)


if __name__ == "__main__":
    main()
