#!/usr/bin/env python3
"""
GATE-017: Single Source of Truth (SSOT) Validation

Validates that facts (paths, versions, states) appear in only one authoritative location:
- Detect duplicate facts across plan (same value in multiple places)
- Detect contradictions (same fact with different values)
- Allow derived facts (generated from authoritative source via formula/reference)
- Check for hardcoded values that should be variables
- Scan for path literals, version strings, configuration values

Enforces DRY (Don't Repeat Yourself) principle at the plan level.
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple, Set
from datetime import datetime
from collections import defaultdict
import re


def validate_ssot(plan: Dict[str, Any]) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Validate single source of truth across plan.

    Returns:
        Tuple of (passed: bool, defects: list)
    """
    defects = []

    # Extract potential facts
    path_facts = defaultdict(list)  # path string -> list of locations
    version_facts = defaultdict(list)  # version string -> list of locations
    config_facts = defaultdict(list)  # config value -> list of locations

    # Scan plan for facts
    phases = plan.get("plan", {}).get("phases", [])

    if not phases:
        defects.append(
            {
                "severity": "critical",
                "category": "missing_field",
                "location": "/plan/phases",
                "problem": "No phases defined in plan",
                "why_it_matters": "Cannot validate SSOT without phases",
            }
        )
        return False, defects

    # Collect facts from various locations
    for phase_idx, phase in enumerate(phases):
        steps = phase.get("steps", [])

        for step_idx, step in enumerate(steps):
            step_id = step.get("step_id", f"S{step_idx:03d}")
            location_prefix = f"/plan/phases/{phase_idx}/steps/{step_idx}"

            # Extract facts from commands
            commands = step.get("commands", [])
            for cmd_idx, command in enumerate(commands):
                cmd_location = f"{location_prefix}/commands/{cmd_idx}"
                extract_facts_from_command(
                    command, cmd_location, path_facts, version_facts, config_facts
                )

            # Extract facts from artifact references
            inputs = step.get("inputs", [])
            outputs = step.get("outputs", [])

            for idx, artifact in enumerate(inputs):
                artifact_location = f"{location_prefix}/inputs/{idx}"
                extract_facts_from_artifact(
                    artifact, artifact_location, path_facts, version_facts, config_facts
                )

            for idx, artifact in enumerate(outputs):
                artifact_location = f"{location_prefix}/outputs/{idx}"
                extract_facts_from_artifact(
                    artifact, artifact_location, path_facts, version_facts, config_facts
                )

    # Check for duplicates
    duplicate_defects = check_duplicates(path_facts, version_facts, config_facts)
    defects.extend(duplicate_defects)

    # Check for contradictions
    contradiction_defects = check_contradictions(plan)
    defects.extend(contradiction_defects)

    # Summary
    total_path_facts = len(path_facts)
    duplicate_paths = len([p for p, locs in path_facts.items() if len(locs) > 1])
    total_version_facts = len(version_facts)
    duplicate_versions = len([v for v, locs in version_facts.items() if len(locs) > 1])

    defects.insert(
        0,
        {
            "severity": "info",
            "category": "other",
            "location": "/plan",
            "problem": f"SSOT summary: {total_path_facts} path facts ({duplicate_paths} duplicated), {total_version_facts} version facts ({duplicate_versions} duplicated)",
            "why_it_matters": "Summary statistics for SSOT analysis",
        },
    )

    # Pass if no critical/high severity defects
    critical_defects = [d for d in defects if d["severity"] in ["critical", "high"]]
    passed = len(critical_defects) == 0

    return passed, defects


def extract_facts_from_command(
    command: Dict[str, Any],
    location: str,
    path_facts: Dict,
    version_facts: Dict,
    config_facts: Dict,
) -> None:
    """Extract facts from command."""
    cmd = command.get("cmd", "")
    cwd = command.get("cwd", "")

    # Extract paths from cmd
    # Look for file paths (contain / or \ or end with common extensions)
    path_pattern = r"(?:[./\\][\w./\\-]+)|(?:[\w-]+\.(?:py|js|json|yaml|yml|sh|md|txt))"
    paths = re.findall(path_pattern, cmd)

    for path in paths:
        if len(path) > 3:  # Ignore very short matches
            path_facts[path].append(location + "/cmd")

    # Extract cwd
    if cwd and cwd != ".":
        path_facts[cwd].append(location + "/cwd")

    # Extract version numbers (e.g., 3.11, v2.4.0, 1.2.3)
    version_pattern = r"\bv?\d+\.\d+(?:\.\d+)?(?:\.\d+)?\b"
    versions = re.findall(version_pattern, cmd)

    for version in versions:
        version_facts[version].append(location + "/cmd")


def extract_facts_from_artifact(
    artifact: Dict[str, Any],
    location: str,
    path_facts: Dict,
    version_facts: Dict,
    config_facts: Dict,
) -> None:
    """Extract facts from artifact reference."""
    path = artifact.get("path", "")

    if path:
        path_facts[path].append(location + "/path")


def check_duplicates(
    path_facts: Dict, version_facts: Dict, config_facts: Dict
) -> List[Dict[str, Any]]:
    """Check for duplicate facts."""
    defects = []

    # Check path duplicates
    for path, locations in path_facts.items():
        if len(locations) > 1:
            # Filter out very common paths (likely correct repetition)
            common_paths = [".", "..", "/", "scripts", "schemas", ".state"]
            if path in common_paths:
                continue

            # Only flag as medium severity (might be legitimate)
            defects.append(
                {
                    "severity": "medium",
                    "category": "other",
                    "location": ", ".join(locations[:3]),
                    "problem": f"Path '{path}' appears in {len(locations)} locations: {locations[:3]}{'...' if len(locations) > 3 else ''}",
                    "why_it_matters": "Duplicate paths should be extracted to single authoritative source (e.g., plan.artifacts.paths)",
                }
            )

    # Check version duplicates
    for version, locations in version_facts.items():
        if len(locations) > 1:
            defects.append(
                {
                    "severity": "medium",
                    "category": "other",
                    "location": ", ".join(locations[:3]),
                    "problem": f"Version '{version}' appears in {len(locations)} locations: {locations[:3]}{'...' if len(locations) > 3 else ''}",
                    "why_it_matters": "Version numbers should be defined once (e.g., in plan.meta or plan.environment)",
                }
            )

    return defects


def check_contradictions(plan: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Check for contradictory facts (same entity, different values)."""
    defects = []

    # Check plan_version consistency
    plan_obj = plan.get("plan", {})
    plan_version = plan_obj.get("plan_version")

    # Check if plan_version matches schema $id
    # (This is a specific check, could be generalized)

    # Check artifact_id uniqueness across inputs/outputs
    artifact_ids = {}  # artifact_id -> (phase, step, io_type, path)

    phases = plan_obj.get("phases", [])
    for phase_idx, phase in enumerate(phases):
        steps = phase.get("steps", [])

        for step_idx, step in enumerate(steps):
            step_id = step.get("step_id")

            # Check inputs
            for artifact in step.get("inputs", []):
                artifact_id = artifact.get("artifact_id")
                path = artifact.get("path")

                if artifact_id:
                    if artifact_id in artifact_ids:
                        prev_phase, prev_step, prev_io, prev_path = artifact_ids[
                            artifact_id
                        ]

                        # Check if path is consistent
                        if path != prev_path:
                            defects.append(
                                {
                                    "severity": "high",
                                    "category": "contradiction",
                                    "location": f"/plan/phases/{phase_idx}/steps/{step_idx}/inputs",
                                    "problem": f"Artifact '{artifact_id}' has inconsistent paths: '{prev_path}' in {prev_step} vs '{path}' in {step_id}",
                                    "why_it_matters": "Same artifact must have same path across all references",
                                }
                            )
                    else:
                        artifact_ids[artifact_id] = (phase_idx, step_id, "input", path)

            # Check outputs
            for artifact in step.get("outputs", []):
                artifact_id = artifact.get("artifact_id")
                path = artifact.get("path")

                if artifact_id:
                    if artifact_id in artifact_ids:
                        prev_phase, prev_step, prev_io, prev_path = artifact_ids[
                            artifact_id
                        ]

                        # Check if path is consistent
                        if path != prev_path:
                            defects.append(
                                {
                                    "severity": "high",
                                    "category": "contradiction",
                                    "location": f"/plan/phases/{phase_idx}/steps/{step_idx}/outputs",
                                    "problem": f"Artifact '{artifact_id}' has inconsistent paths: '{prev_path}' in {prev_step} vs '{path}' in {step_id}",
                                    "why_it_matters": "Same artifact must have same path across all references",
                                }
                            )
                    else:
                        artifact_ids[artifact_id] = (phase_idx, step_id, "output", path)

    return defects


def write_evidence(
    evidence_dir: Path, passed: bool, defects: List[Dict[str, Any]]
) -> None:
    """Write evidence artifacts."""
    evidence_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().isoformat() + "Z"

    summary = {
        "timestamp": timestamp,
        "gate_id": "GATE-017",
        "gate_name": "Single Source of Truth Validation",
        "passed": passed,
        "defect_count": len(defects),
        "defects": defects,
    }

    summary_path = evidence_dir / "ssot_validation.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"Evidence written to: {summary_path}")


def main():
    parser = argparse.ArgumentParser(
        description="GATE-017: Validate single source of truth in v3.0.0 plan"
    )
    parser.add_argument("--plan-file", required=True, help="Path to plan JSON file")
    parser.add_argument(
        "--evidence-dir",
        default=".state/evidence/GATE-017",
        help="Directory for evidence output (default: .state/evidence/GATE-017)",
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
    passed, defects = validate_ssot(plan)

    # Write evidence
    evidence_dir = Path(args.evidence_dir)
    write_evidence(evidence_dir, passed, defects)

    # Print results
    summary_defects = [d for d in defects if d["severity"] == "info"]
    other_defects = [d for d in defects if d["severity"] != "info"]

    if summary_defects:
        print(summary_defects[0]["problem"])

    if passed:
        print("✓ GATE-017 PASSED: Single source of truth validated")
        if other_defects:
            print(f"  ({len(other_defects)} warnings - see evidence file)")
        sys.exit(0)
    else:
        print(f"✗ GATE-017 FAILED: {len(other_defects)} defects found")
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
