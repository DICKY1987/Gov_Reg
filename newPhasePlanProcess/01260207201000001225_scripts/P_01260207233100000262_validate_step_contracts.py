#!/usr/bin/env python3
"""
GATE-003: Step Contracts Validation

Validates that every step has complete contracts:
- step_id uniqueness
- Required fields present: inputs, outputs, preconditions, commands, postconditions, rollback, evidence, idempotency
- Commands have required fields: cwd, timeout_s, expect_exit_codes
- Preconditions/postconditions have evidence_path (optional but recommended)
- artifact_ref IDs follow valid pattern
- Rollback strategy is valid enum value
- Idempotency configuration is complete
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple
from datetime import datetime
import re


def validate_step_contracts(plan: Dict[str, Any]) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Validate all step contracts in the plan.

    Returns:
        Tuple of (passed: bool, defects: list)
    """
    defects = []

    # Extract phases
    phases = plan.get("plan", {}).get("phases", [])
    if not phases:
        defects.append(
            {
                "severity": "critical",
                "category": "missing_field",
                "location": "/plan/phases",
                "problem": "No phases defined in plan",
                "why_it_matters": "Plan must have at least one phase with steps",
            }
        )
        return False, defects

    # Collect all step IDs to check uniqueness
    step_ids = []

    # Validate each phase's steps
    for phase_idx, phase in enumerate(phases):
        phase_id = phase.get("phase_id", f"P{phase_idx:02d}")
        steps = phase.get("steps", [])

        if not steps:
            defects.append(
                {
                    "severity": "high",
                    "category": "missing_field",
                    "location": f"/plan/phases/{phase_idx}/steps",
                    "problem": f"Phase {phase_id} has no steps",
                    "why_it_matters": "Each phase must have at least one step",
                }
            )
            continue

        for step_idx, step in enumerate(steps):
            step_defects = validate_step(step, phase_id, phase_idx, step_idx)
            defects.extend(step_defects)

            # Track step_id for uniqueness check
            step_id = step.get("step_id")
            if step_id:
                step_ids.append(step_id)

    # Check step_id uniqueness
    step_id_counts = {}
    for step_id in step_ids:
        step_id_counts[step_id] = step_id_counts.get(step_id, 0) + 1

    for step_id, count in step_id_counts.items():
        if count > 1:
            defects.append(
                {
                    "severity": "critical",
                    "category": "contradiction",
                    "location": "/plan/phases",
                    "problem": f"step_id '{step_id}' appears {count} times (must be unique)",
                    "why_it_matters": "Step IDs must be unique across all phases for dependency tracking",
                }
            )

    passed = len(defects) == 0
    return passed, defects


def validate_step(
    step: Dict[str, Any], phase_id: str, phase_idx: int, step_idx: int
) -> List[Dict[str, Any]]:
    """Validate a single step's contract."""
    defects = []
    location_prefix = f"/plan/phases/{phase_idx}/steps/{step_idx}"

    # Required fields
    required_fields = [
        "step_id",
        "title",
        "intent",
        "inputs",
        "outputs",
        "preconditions",
        "commands",
        "postconditions",
        "rollback",
        "evidence",
        "idempotency",
    ]

    for field in required_fields:
        if field not in step:
            defects.append(
                {
                    "severity": "critical",
                    "category": "missing_field",
                    "location": f"{location_prefix}/{field}",
                    "problem": f"Step missing required field: {field}",
                    "why_it_matters": f"Step contracts require {field} for mechanical execution",
                }
            )

    # Validate step_id pattern
    step_id = step.get("step_id", "")
    if step_id and not re.match(r"^S\d{3}$", step_id):
        defects.append(
            {
                "severity": "high",
                "category": "schema",
                "location": f"{location_prefix}/step_id",
                "problem": f"step_id '{step_id}' does not match pattern ^S\\d{{3}}$",
                "why_it_matters": "step_id must follow S001-S999 pattern for ordering",
            }
        )

    # Validate inputs (array of artifact_ref)
    inputs = step.get("inputs", [])
    if not isinstance(inputs, list):
        defects.append(
            {
                "severity": "high",
                "category": "schema",
                "location": f"{location_prefix}/inputs",
                "problem": "inputs must be an array",
                "why_it_matters": "Step inputs define artifact dependencies",
            }
        )
    else:
        for idx, artifact_ref in enumerate(inputs):
            artifact_defects = validate_artifact_ref(
                artifact_ref, f"{location_prefix}/inputs/{idx}"
            )
            defects.extend(artifact_defects)

    # Validate outputs (array of artifact_ref)
    outputs = step.get("outputs", [])
    if not isinstance(outputs, list):
        defects.append(
            {
                "severity": "high",
                "category": "schema",
                "location": f"{location_prefix}/outputs",
                "problem": "outputs must be an array",
                "why_it_matters": "Step outputs define produced artifacts",
            }
        )
    else:
        for idx, artifact_ref in enumerate(outputs):
            artifact_defects = validate_artifact_ref(
                artifact_ref, f"{location_prefix}/outputs/{idx}"
            )
            defects.extend(artifact_defects)

    # Validate preconditions (array with at least one)
    preconditions = step.get("preconditions", [])
    if not isinstance(preconditions, list):
        defects.append(
            {
                "severity": "high",
                "category": "schema",
                "location": f"{location_prefix}/preconditions",
                "problem": "preconditions must be an array",
                "why_it_matters": "Preconditions validate step can execute safely",
            }
        )
    elif len(preconditions) == 0:
        defects.append(
            {
                "severity": "high",
                "category": "verification_gap",
                "location": f"{location_prefix}/preconditions",
                "problem": "Step has no preconditions",
                "why_it_matters": "Every step must validate preconditions before execution",
            }
        )
    else:
        for idx, criteria in enumerate(preconditions):
            criteria_defects = validate_criteria(
                criteria, f"{location_prefix}/preconditions/{idx}"
            )
            defects.extend(criteria_defects)

    # Validate commands (array with at least one)
    commands = step.get("commands", [])
    if not isinstance(commands, list):
        defects.append(
            {
                "severity": "critical",
                "category": "schema",
                "location": f"{location_prefix}/commands",
                "problem": "commands must be an array",
                "why_it_matters": "Commands define what the step executes",
            }
        )
    elif len(commands) == 0:
        defects.append(
            {
                "severity": "critical",
                "category": "missing_field",
                "location": f"{location_prefix}/commands",
                "problem": "Step has no commands",
                "why_it_matters": "Every step must have at least one command to execute",
            }
        )
    else:
        for idx, command in enumerate(commands):
            command_defects = validate_command(
                command, f"{location_prefix}/commands/{idx}"
            )
            defects.extend(command_defects)

    # Validate postconditions (array with at least one)
    postconditions = step.get("postconditions", [])
    if not isinstance(postconditions, list):
        defects.append(
            {
                "severity": "high",
                "category": "schema",
                "location": f"{location_prefix}/postconditions",
                "problem": "postconditions must be an array",
                "why_it_matters": "Postconditions validate step executed correctly",
            }
        )
    elif len(postconditions) == 0:
        defects.append(
            {
                "severity": "high",
                "category": "verification_gap",
                "location": f"{location_prefix}/postconditions",
                "problem": "Step has no postconditions",
                "why_it_matters": "Every step must validate outputs and detect unintended changes",
            }
        )
    else:
        for idx, criteria in enumerate(postconditions):
            criteria_defects = validate_criteria(
                criteria, f"{location_prefix}/postconditions/{idx}"
            )
            defects.extend(criteria_defects)

    # Validate rollback
    rollback = step.get("rollback", {})
    rollback_defects = validate_rollback(rollback, f"{location_prefix}/rollback")
    defects.extend(rollback_defects)

    # Validate evidence
    evidence = step.get("evidence", {})
    evidence_defects = validate_evidence(evidence, f"{location_prefix}/evidence")
    defects.extend(evidence_defects)

    # Validate idempotency
    idempotency = step.get("idempotency", {})
    idempotency_defects = validate_idempotency(
        idempotency, f"{location_prefix}/idempotency"
    )
    defects.extend(idempotency_defects)

    return defects


def validate_artifact_ref(
    artifact_ref: Dict[str, Any], location: str
) -> List[Dict[str, Any]]:
    """Validate artifact_ref structure."""
    defects = []

    required_fields = ["artifact_id", "path", "kind"]
    for field in required_fields:
        if field not in artifact_ref:
            defects.append(
                {
                    "severity": "high",
                    "category": "missing_field",
                    "location": f"{location}/{field}",
                    "problem": f"artifact_ref missing required field: {field}",
                    "why_it_matters": "Artifact references need complete identification",
                }
            )

    # Validate artifact_id pattern
    artifact_id = artifact_ref.get("artifact_id", "")
    if artifact_id and not re.match(r"^[A-Z0-9_\-\.]{6,80}$", artifact_id):
        defects.append(
            {
                "severity": "medium",
                "category": "schema",
                "location": f"{location}/artifact_id",
                "problem": f"artifact_id '{artifact_id}' does not match pattern",
                "why_it_matters": "artifact_id must be 6-80 uppercase alphanumeric with _-.",
            }
        )

    # Validate kind enum
    kind = artifact_ref.get("kind")
    valid_kinds = ["file", "directory", "report", "registry_entry", "backup"]
    if kind and kind not in valid_kinds:
        defects.append(
            {
                "severity": "high",
                "category": "schema",
                "location": f"{location}/kind",
                "problem": f"kind '{kind}' not in valid values: {valid_kinds}",
                "why_it_matters": "Artifact kind must be one of the defined types",
            }
        )

    return defects


def validate_criteria(criteria: Dict[str, Any], location: str) -> List[Dict[str, Any]]:
    """Validate criteria structure."""
    defects = []

    required_fields = ["type", "statement"]
    for field in required_fields:
        if field not in criteria:
            defects.append(
                {
                    "severity": "high",
                    "category": "missing_field",
                    "location": f"{location}/{field}",
                    "problem": f"criteria missing required field: {field}",
                    "why_it_matters": "Criteria need type and statement for evaluation",
                }
            )

    # Validate type enum
    criteria_type = criteria.get("type")
    valid_types = [
        "exists",
        "not_exists",
        "json_valid",
        "schema_valid",
        "hash_equals",
        "diff_empty",
        "contains",
        "custom",
    ]
    if criteria_type and criteria_type not in valid_types:
        defects.append(
            {
                "severity": "high",
                "category": "schema",
                "location": f"{location}/type",
                "problem": f"criteria type '{criteria_type}' not in valid values: {valid_types}",
                "why_it_matters": "Criteria type must be one of the implemented types",
            }
        )

    # Warn if evidence_path missing (optional but recommended)
    if "evidence_path" not in criteria:
        defects.append(
            {
                "severity": "low",
                "category": "verification_gap",
                "location": f"{location}/evidence_path",
                "problem": "criteria missing optional evidence_path",
                "why_it_matters": "Evidence paths enable audit trail for criteria evaluation",
            }
        )

    return defects


def validate_command(command: Dict[str, Any], location: str) -> List[Dict[str, Any]]:
    """Validate command structure."""
    defects = []

    required_fields = ["cmd", "cwd", "timeout_s", "expect_exit_codes"]
    for field in required_fields:
        if field not in command:
            defects.append(
                {
                    "severity": "critical",
                    "category": "missing_field",
                    "location": f"{location}/{field}",
                    "problem": f"command missing required field: {field}",
                    "why_it_matters": f"Commands require {field} for deterministic execution",
                }
            )

    # Validate timeout_s range
    timeout_s = command.get("timeout_s")
    if timeout_s is not None:
        if not isinstance(timeout_s, int) or timeout_s < 1 or timeout_s > 86400:
            defects.append(
                {
                    "severity": "high",
                    "category": "schema",
                    "location": f"{location}/timeout_s",
                    "problem": f"timeout_s must be integer between 1 and 86400, got: {timeout_s}",
                    "why_it_matters": "Timeout prevents hung commands (max 24 hours)",
                }
            )

    # Validate expect_exit_codes is non-empty array
    exit_codes = command.get("expect_exit_codes", [])
    if not isinstance(exit_codes, list):
        defects.append(
            {
                "severity": "critical",
                "category": "schema",
                "location": f"{location}/expect_exit_codes",
                "problem": "expect_exit_codes must be an array",
                "why_it_matters": "Exit codes define command success criteria",
            }
        )
    elif len(exit_codes) == 0:
        defects.append(
            {
                "severity": "critical",
                "category": "missing_field",
                "location": f"{location}/expect_exit_codes",
                "problem": "expect_exit_codes is empty",
                "why_it_matters": "At least one expected exit code must be specified",
            }
        )

    return defects


def validate_rollback(rollback: Dict[str, Any], location: str) -> List[Dict[str, Any]]:
    """Validate rollback structure."""
    defects = []

    required_fields = ["strategy", "commands", "verification"]
    for field in required_fields:
        if field not in rollback:
            defects.append(
                {
                    "severity": "high",
                    "category": "rollback_gap",
                    "location": f"{location}/{field}",
                    "problem": f"rollback missing required field: {field}",
                    "why_it_matters": "Rollback needs strategy, commands, and verification",
                }
            )

    # Validate strategy enum
    strategy = rollback.get("strategy")
    valid_strategies = ["undo", "restore_backup", "compensate", "manual"]
    if strategy and strategy not in valid_strategies:
        defects.append(
            {
                "severity": "high",
                "category": "schema",
                "location": f"{location}/strategy",
                "problem": f"rollback strategy '{strategy}' not in valid values: {valid_strategies}",
                "why_it_matters": "Rollback strategy must be one of the defined types",
            }
        )

    # Warn if strategy is manual
    if strategy == "manual":
        defects.append(
            {
                "severity": "low",
                "category": "rollback_gap",
                "location": f"{location}/strategy",
                "problem": "rollback strategy is 'manual' (requires human intervention)",
                "why_it_matters": "Manual rollback cannot be automated; consider automated alternatives",
            }
        )

    return defects


def validate_evidence(evidence: Dict[str, Any], location: str) -> List[Dict[str, Any]]:
    """Validate evidence structure."""
    defects = []

    required_fields = ["paths", "summary_path"]
    for field in required_fields:
        if field not in evidence:
            defects.append(
                {
                    "severity": "high",
                    "category": "verification_gap",
                    "location": f"{location}/{field}",
                    "problem": f"evidence missing required field: {field}",
                    "why_it_matters": "Evidence needs paths and summary for audit trail",
                }
            )

    # Validate paths is non-empty array
    paths = evidence.get("paths", [])
    if not isinstance(paths, list):
        defects.append(
            {
                "severity": "high",
                "category": "schema",
                "location": f"{location}/paths",
                "problem": "evidence paths must be an array",
                "why_it_matters": "Evidence paths list all artifacts produced by step",
            }
        )
    elif len(paths) == 0:
        defects.append(
            {
                "severity": "medium",
                "category": "verification_gap",
                "location": f"{location}/paths",
                "problem": "evidence paths is empty",
                "why_it_matters": "At least one evidence path should be specified",
            }
        )

    return defects


def validate_idempotency(
    idempotency: Dict[str, Any], location: str
) -> List[Dict[str, Any]]:
    """Validate idempotency structure."""
    defects = []

    required_fields = ["rerun_safe", "locking"]
    for field in required_fields:
        if field not in idempotency:
            defects.append(
                {
                    "severity": "high",
                    "category": "non_determinism",
                    "location": f"{location}/{field}",
                    "problem": f"idempotency missing required field: {field}",
                    "why_it_matters": "Idempotency contract must declare rerun safety and locking",
                }
            )

    # Validate locking structure
    locking = idempotency.get("locking", {})
    if not isinstance(locking, dict):
        defects.append(
            {
                "severity": "high",
                "category": "schema",
                "location": f"{location}/locking",
                "problem": "locking must be an object",
                "why_it_matters": "Locking configuration defines concurrency safety",
            }
        )
    else:
        locking_required_fields = ["required", "mechanism", "scope"]
        for field in locking_required_fields:
            if field not in locking:
                defects.append(
                    {
                        "severity": "high",
                        "category": "missing_field",
                        "location": f"{location}/locking/{field}",
                        "problem": f"locking missing required field: {field}",
                        "why_it_matters": "Locking configuration must be complete",
                    }
                )

        # Validate mechanism enum
        mechanism = locking.get("mechanism")
        valid_mechanisms = ["lockfile", "sqlite_txn", "os_mutex", "none"]
        if mechanism and mechanism not in valid_mechanisms:
            defects.append(
                {
                    "severity": "high",
                    "category": "schema",
                    "location": f"{location}/locking/mechanism",
                    "problem": f"locking mechanism '{mechanism}' not in valid values: {valid_mechanisms}",
                    "why_it_matters": "Locking mechanism must be one of the implemented types",
                }
            )

        # Validate scope enum
        scope = locking.get("scope")
        valid_scopes = ["global", "phase", "step", "resource"]
        if scope and scope not in valid_scopes:
            defects.append(
                {
                    "severity": "high",
                    "category": "schema",
                    "location": f"{location}/locking/scope",
                    "problem": f"locking scope '{scope}' not in valid values: {valid_scopes}",
                    "why_it_matters": "Locking scope must be one of the defined levels",
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
        "gate_id": "GATE-003",
        "gate_name": "Step Contracts Validation",
        "passed": passed,
        "defect_count": len(defects),
        "defects": defects,
    }

    summary_path = evidence_dir / "step_contracts_validation.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"Evidence written to: {summary_path}")


def main():
    parser = argparse.ArgumentParser(
        description="GATE-003: Validate step contracts in v3.0.0 plan"
    )
    parser.add_argument("--plan-file", required=True, help="Path to plan JSON file")
    parser.add_argument(
        "--evidence-dir",
        default=".state/evidence/GATE-003",
        help="Directory for evidence output (default: .state/evidence/GATE-003)",
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
    passed, defects = validate_step_contracts(plan)

    # Write evidence
    evidence_dir = Path(args.evidence_dir)
    write_evidence(evidence_dir, passed, defects)

    # Print results
    if passed:
        print("✓ GATE-003 PASSED: All step contracts are valid")
        sys.exit(0)
    else:
        print(f"✗ GATE-003 FAILED: {len(defects)} defects found")
        for defect in defects[:5]:  # Show first 5
            print(f"  [{defect['severity']}] {defect['location']}: {defect['problem']}")
        if len(defects) > 5:
            print(f"  ... and {len(defects) - 5} more defects (see evidence file)")
        sys.exit(1)


if __name__ == "__main__":
    main()
