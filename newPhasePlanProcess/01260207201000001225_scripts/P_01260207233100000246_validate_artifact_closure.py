#!/usr/bin/env python3
"""
GATE-014: Artifact Closure Validation

Validates that all artifact references form a closed graph:
- Build producer/consumer graph from step inputs/outputs
- Detect orphaned artifacts (produced but never consumed)
- Detect dead artifacts (consumed but never produced - missing producers)
- Detect write conflicts (multiple producers for same artifact_id)
- Detect external dependencies (consumed from external sources)

Replaces plan-level FM checks: FM-01 (orphans), FM-02 (write conflicts),
FM-04 (dead artifacts), FM-05 (missing producers)
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List, Set, Tuple
from datetime import datetime
from collections import defaultdict


def validate_artifact_closure(
    plan: Dict[str, Any]
) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Validate artifact closure across all steps.

    Returns:
        Tuple of (passed: bool, defects: list)
    """
    defects = []

    # Build artifact graph
    producers = defaultdict(
        list
    )  # artifact_id -> list of (phase_idx, step_idx, step_id)
    consumers = defaultdict(
        list
    )  # artifact_id -> list of (phase_idx, step_idx, step_id)
    all_artifact_ids = set()

    phases = plan.get("plan", {}).get("phases", [])

    if not phases:
        defects.append(
            {
                "severity": "critical",
                "category": "missing_field",
                "location": "/plan/phases",
                "problem": "No phases defined in plan",
                "why_it_matters": "Cannot validate artifact closure without phases",
            }
        )
        return False, defects

    # First pass: collect all producers and consumers
    for phase_idx, phase in enumerate(phases):
        phase_id = phase.get("phase_id", f"P{phase_idx:02d}")
        steps = phase.get("steps", [])

        for step_idx, step in enumerate(steps):
            step_id = step.get("step_id", f"S{step_idx:03d}")

            # Collect inputs (consumers)
            inputs = step.get("inputs", [])
            for input_ref in inputs:
                artifact_id = input_ref.get("artifact_id")
                if artifact_id:
                    consumers[artifact_id].append((phase_idx, step_idx, step_id))
                    all_artifact_ids.add(artifact_id)

            # Collect outputs (producers)
            outputs = step.get("outputs", [])
            for output_ref in outputs:
                artifact_id = output_ref.get("artifact_id")
                if artifact_id:
                    producers[artifact_id].append((phase_idx, step_idx, step_id))
                    all_artifact_ids.add(artifact_id)

    # Check for write conflicts (multiple producers)
    for artifact_id in all_artifact_ids:
        producer_list = producers[artifact_id]
        if len(producer_list) > 1:
            producer_steps = [step_id for _, _, step_id in producer_list]
            defects.append(
                {
                    "severity": "critical",
                    "category": "contradiction",
                    "location": f"/plan/phases",
                    "problem": f"Artifact '{artifact_id}' has multiple producers: {producer_steps}",
                    "why_it_matters": "Multiple steps producing same artifact causes race conditions and non-determinism",
                }
            )

    # Check for orphaned artifacts (produced but never consumed)
    for artifact_id in all_artifact_ids:
        if producers[artifact_id] and not consumers[artifact_id]:
            producer_steps = [step_id for _, _, step_id in producers[artifact_id]]
            defects.append(
                {
                    "severity": "medium",
                    "category": "verification_gap",
                    "location": f"/plan/phases",
                    "problem": f"Artifact '{artifact_id}' is produced by {producer_steps} but never consumed",
                    "why_it_matters": "Orphaned artifacts may indicate incomplete plan or unnecessary work",
                }
            )

    # Check for dead artifacts (consumed but never produced)
    # These might be external dependencies (acceptable) or missing producers (error)
    external_artifacts = set()
    for artifact_id in all_artifact_ids:
        if consumers[artifact_id] and not producers[artifact_id]:
            consumer_steps = [step_id for _, _, step_id in consumers[artifact_id]]

            # Check if this might be an external dependency (pre-existing file)
            # Heuristic: if artifact_id contains known external patterns
            external_patterns = ["SCHEMA", "CONFIG", "EXISTING", "INPUT", "SOURCE"]
            is_likely_external = any(
                pattern in artifact_id for pattern in external_patterns
            )

            if is_likely_external:
                external_artifacts.add(artifact_id)
                defects.append(
                    {
                        "severity": "low",
                        "category": "verification_gap",
                        "location": f"/plan/phases",
                        "problem": f"Artifact '{artifact_id}' consumed by {consumer_steps} but not produced (likely external dependency)",
                        "why_it_matters": "External dependencies should be documented in plan.assumptions",
                    }
                )
            else:
                defects.append(
                    {
                        "severity": "high",
                        "category": "missing_field",
                        "location": f"/plan/phases",
                        "problem": f"Artifact '{artifact_id}' consumed by {consumer_steps} but no producer step exists",
                        "why_it_matters": "Missing producer means step will fail when it tries to consume this artifact",
                    }
                )

    # Check for dependency ordering violations
    # A step consuming an artifact must come after the step producing it
    for artifact_id in all_artifact_ids:
        if not producers[artifact_id] or not consumers[artifact_id]:
            continue

        # Get producer location
        prod_phase_idx, prod_step_idx, prod_step_id = producers[artifact_id][0]

        # Check all consumers
        for cons_phase_idx, cons_step_idx, cons_step_id in consumers[artifact_id]:
            # Violation if consumer is before producer
            if cons_phase_idx < prod_phase_idx:
                defects.append(
                    {
                        "severity": "critical",
                        "category": "ordering",
                        "location": f"/plan/phases",
                        "problem": f"Step {cons_step_id} (phase {cons_phase_idx}) consumes '{artifact_id}' before {prod_step_id} (phase {prod_phase_idx}) produces it",
                        "why_it_matters": "Dependency ordering violation will cause execution failure",
                    }
                )
            elif cons_phase_idx == prod_phase_idx and cons_step_idx <= prod_step_idx:
                defects.append(
                    {
                        "severity": "critical",
                        "category": "ordering",
                        "location": f"/plan/phases/{cons_phase_idx}",
                        "problem": f"Step {cons_step_id} (index {cons_step_idx}) consumes '{artifact_id}' before/same as {prod_step_id} (index {prod_step_idx}) produces it",
                        "why_it_matters": "Steps must execute in order: producer before consumer",
                    }
                )

    # Summary statistics
    total_artifacts = len(all_artifact_ids)
    produced_count = len([aid for aid in all_artifact_ids if producers[aid]])
    consumed_count = len([aid for aid in all_artifact_ids if consumers[aid]])
    orphaned_count = len(
        [aid for aid in all_artifact_ids if producers[aid] and not consumers[aid]]
    )
    external_count = len(external_artifacts)
    write_conflicts = len([aid for aid in all_artifact_ids if len(producers[aid]) > 1])

    # Add summary to defects as informational
    defects.insert(
        0,
        {
            "severity": "info",
            "category": "other",
            "location": "/plan/phases",
            "problem": f"Artifact graph summary: {total_artifacts} total, {produced_count} produced, {consumed_count} consumed, {orphaned_count} orphaned, {external_count} external, {write_conflicts} conflicts",
            "why_it_matters": "Summary statistics for artifact closure analysis",
        },
    )

    # Pass if no critical/high severity defects
    critical_defects = [d for d in defects if d["severity"] in ["critical", "high"]]
    passed = len(critical_defects) == 0

    return passed, defects


def write_evidence(
    evidence_dir: Path, passed: bool, defects: List[Dict[str, Any]]
) -> None:
    """Write evidence artifacts."""
    evidence_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().isoformat() + "Z"

    summary = {
        "timestamp": timestamp,
        "gate_id": "GATE-014",
        "gate_name": "Artifact Closure Validation",
        "passed": passed,
        "defect_count": len(defects),
        "defects": defects,
    }

    summary_path = evidence_dir / "artifact_closure_validation.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"Evidence written to: {summary_path}")


def main():
    parser = argparse.ArgumentParser(
        description="GATE-014: Validate artifact closure in v3.0.0 plan"
    )
    parser.add_argument("--plan-file", required=True, help="Path to plan JSON file")
    parser.add_argument(
        "--evidence-dir",
        default=".state/evidence/GATE-014",
        help="Directory for evidence output (default: .state/evidence/GATE-014)",
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
    passed, defects = validate_artifact_closure(plan)

    # Write evidence
    evidence_dir = Path(args.evidence_dir)
    write_evidence(evidence_dir, passed, defects)

    # Print results
    # Extract summary (first defect if present)
    summary_defects = [d for d in defects if d["severity"] == "info"]
    other_defects = [d for d in defects if d["severity"] != "info"]

    if summary_defects:
        print(summary_defects[0]["problem"])

    if passed:
        print("✓ GATE-014 PASSED: Artifact closure is valid")
        if other_defects:
            print(f"  ({len(other_defects)} warnings - see evidence file)")
        sys.exit(0)
    else:
        print(f"✗ GATE-014 FAILED: {len(other_defects)} defects found")
        for defect in other_defects[:5]:  # Show first 5
            if defect["severity"] in ["critical", "high"]:
                print(f"  [{defect['severity']}] {defect['problem']}")
        if len(other_defects) > 5:
            print(
                f"  ... and {len(other_defects) - 5} more defects (see evidence file)"
            )
        sys.exit(1)


if __name__ == "__main__":
    main()
