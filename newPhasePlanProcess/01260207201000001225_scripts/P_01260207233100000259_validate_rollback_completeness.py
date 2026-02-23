#!/usr/bin/env python3
"""
GATE-015: Rollback Completeness Validation

Validates that every step with state changes has complete, testable rollback:
- Rollback strategy is valid enum (undo, restore_backup, compensate, manual)
- Rollback commands are specified and executable
- Rollback verification criteria are complete
- Warn on strategy='manual' (requires human intervention)
- Check that rollback reverses all outputs

Replaces FM-09 (recovery policy gaps)
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple
from datetime import datetime


def validate_rollback_completeness(
    plan: Dict[str, Any]
) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Validate rollback completeness across all steps.

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
                "why_it_matters": "Cannot validate rollback without phases",
            }
        )
        return False, defects

    # Statistics
    total_steps = 0
    steps_with_outputs = 0
    steps_with_manual_rollback = 0
    steps_with_no_rollback_verification = 0

    # Validate each step's rollback
    for phase_idx, phase in enumerate(phases):
        phase_id = phase.get("phase_id", f"P{phase_idx:02d}")
        steps = phase.get("steps", [])

        for step_idx, step in enumerate(steps):
            total_steps += 1
            step_id = step.get("step_id", f"S{step_idx:03d}")
            location = f"/plan/phases/{phase_idx}/steps/{step_idx}"

            # Check if step has outputs (produces artifacts = state change)
            outputs = step.get("outputs", [])
            has_outputs = len(outputs) > 0
            if has_outputs:
                steps_with_outputs += 1

            rollback = step.get("rollback", {})

            # Validate rollback structure (already done by GATE-003, but check completeness)
            strategy = rollback.get("strategy")
            commands = rollback.get("commands", [])
            verification = rollback.get("verification", [])

            # Check if step produces outputs but has empty rollback commands
            if has_outputs and not commands:
                defects.append(
                    {
                        "severity": "high",
                        "category": "rollback_gap",
                        "location": f"{location}/rollback/commands",
                        "problem": f"Step {step_id} produces {len(outputs)} artifacts but has no rollback commands",
                        "why_it_matters": "Steps with state changes must have rollback to enable safe recovery",
                    }
                )

            # Check for manual rollback strategy
            if strategy == "manual":
                steps_with_manual_rollback += 1
                defects.append(
                    {
                        "severity": "medium",
                        "category": "rollback_gap",
                        "location": f"{location}/rollback/strategy",
                        "problem": f"Step {step_id} uses manual rollback strategy",
                        "why_it_matters": "Manual rollback requires human intervention and cannot be automated",
                    }
                )

            # Check that rollback has verification criteria
            if has_outputs and not verification:
                steps_with_no_rollback_verification += 1
                defects.append(
                    {
                        "severity": "high",
                        "category": "verification_gap",
                        "location": f"{location}/rollback/verification",
                        "problem": f"Step {step_id} has no rollback verification criteria",
                        "why_it_matters": "Cannot confirm rollback succeeded without verification",
                    }
                )

            # Check that rollback verification is meaningful
            if verification:
                rollback_defects = validate_rollback_verification(
                    verification, step_id, outputs, location
                )
                defects.extend(rollback_defects)

            # Validate rollback commands are executable (have required fields)
            for cmd_idx, command in enumerate(commands):
                cmd_defects = validate_rollback_command(
                    command, step_id, f"{location}/rollback/commands/{cmd_idx}"
                )
                defects.extend(cmd_defects)

    # Add summary
    defects.insert(
        0,
        {
            "severity": "info",
            "category": "other",
            "location": "/plan/phases",
            "problem": f"Rollback summary: {total_steps} total steps, {steps_with_outputs} with outputs, {steps_with_manual_rollback} manual rollback, {steps_with_no_rollback_verification} missing verification",
            "why_it_matters": "Summary statistics for rollback completeness analysis",
        },
    )

    # Pass if no critical/high severity defects
    critical_defects = [d for d in defects if d["severity"] in ["critical", "high"]]
    passed = len(critical_defects) == 0

    return passed, defects


def validate_rollback_verification(
    verification: List[Dict[str, Any]],
    step_id: str,
    outputs: List[Dict[str, Any]],
    location: str,
) -> List[Dict[str, Any]]:
    """Validate rollback verification criteria."""
    defects = []

    # Check that verification covers removal/restoration of outputs
    output_artifact_ids = {
        out.get("artifact_id") for out in outputs if out.get("artifact_id")
    }

    # Count verification criteria that check for artifact removal
    removal_checks = 0
    for criteria in verification:
        criteria_type = criteria.get("type")
        if criteria_type in ["not_exists", "diff_empty"]:
            removal_checks += 1

    # Warn if step produces artifacts but rollback verification doesn't check removal
    if output_artifact_ids and removal_checks == 0:
        defects.append(
            {
                "severity": "medium",
                "category": "verification_gap",
                "location": f"{location}/rollback/verification",
                "problem": f"Step {step_id} produces artifacts but rollback verification doesn't check removal (no 'not_exists' or 'diff_empty' criteria)",
                "why_it_matters": "Rollback should verify that produced artifacts are removed/restored",
            }
        )

    return defects


def validate_rollback_command(
    command: Dict[str, Any], step_id: str, location: str
) -> List[Dict[str, Any]]:
    """Validate a single rollback command."""
    defects = []

    # Check that command has required fields (already validated by GATE-003)
    # Here we add semantic checks

    cmd = command.get("cmd", "")

    # Warn if rollback command looks like forward command (common mistake)
    dangerous_patterns = ["create", "add", "install", "deploy", "apply"]
    safe_patterns = [
        "rm",
        "remove",
        "delete",
        "uninstall",
        "undo",
        "restore",
        "revert",
        "checkout",
    ]

    cmd_lower = cmd.lower()
    has_dangerous = any(pattern in cmd_lower for pattern in dangerous_patterns)
    has_safe = any(pattern in cmd_lower for pattern in safe_patterns)

    if has_dangerous and not has_safe:
        defects.append(
            {
                "severity": "medium",
                "category": "rollback_gap",
                "location": location,
                "problem": f"Rollback command looks like forward operation: '{cmd}'",
                "why_it_matters": "Rollback commands should undo/remove, not create/add",
            }
        )

    # Check timeout is reasonable for rollback (should be quick)
    timeout_s = command.get("timeout_s", 0)
    if timeout_s > 600:  # 10 minutes
        defects.append(
            {
                "severity": "low",
                "category": "rollback_gap",
                "location": location,
                "problem": f"Rollback timeout is very long ({timeout_s}s = {timeout_s//60}min)",
                "why_it_matters": "Rollback should be fast; long timeouts may indicate complex operation",
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
        "gate_id": "GATE-015",
        "gate_name": "Rollback Completeness Validation",
        "passed": passed,
        "defect_count": len(defects),
        "defects": defects,
    }

    summary_path = evidence_dir / "rollback_completeness_validation.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"Evidence written to: {summary_path}")


def main():
    parser = argparse.ArgumentParser(
        description="GATE-015: Validate rollback completeness in v3.0.0 plan"
    )
    parser.add_argument("--plan-file", required=True, help="Path to plan JSON file")
    parser.add_argument(
        "--evidence-dir",
        default=".state/evidence/GATE-015",
        help="Directory for evidence output (default: .state/evidence/GATE-015)",
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
    passed, defects = validate_rollback_completeness(plan)

    # Write evidence
    evidence_dir = Path(args.evidence_dir)
    write_evidence(evidence_dir, passed, defects)

    # Print results
    summary_defects = [d for d in defects if d["severity"] == "info"]
    other_defects = [d for d in defects if d["severity"] != "info"]

    if summary_defects:
        print(summary_defects[0]["problem"])

    if passed:
        print("✓ GATE-015 PASSED: Rollback completeness is valid")
        if other_defects:
            print(f"  ({len(other_defects)} warnings - see evidence file)")
        sys.exit(0)
    else:
        print(f"✗ GATE-015 FAILED: {len(other_defects)} defects found")
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
