#!/usr/bin/env python3
"""
GATE-004: Assumptions Validation

Validates that assumptions are explicit, testable, and risk-assessed:
- assumption_id uniqueness across plan
- assumption_id matches pattern ^A\d{3}$
- statement is non-empty
- risk_if_false is non-empty and describes actual risk
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple
from datetime import datetime
import re


def validate_assumptions(plan: Dict[str, Any]) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Validate all assumptions in the plan.

    Returns:
        Tuple of (passed: bool, defects: list)
    """
    defects = []

    # Extract assumptions
    assumptions = plan.get("plan", {}).get("assumptions", [])

    # Check if assumptions exist (optional but recommended)
    if not assumptions:
        defects.append(
            {
                "severity": "low",
                "category": "missing_field",
                "location": "/plan/assumptions",
                "problem": "Plan has no assumptions",
                "why_it_matters": "Assumptions make implicit dependencies explicit; consider if plan truly has zero assumptions",
            }
        )
        # Not a failure - assumptions are optional
        return True, defects

    if not isinstance(assumptions, list):
        defects.append(
            {
                "severity": "critical",
                "category": "schema",
                "location": "/plan/assumptions",
                "problem": "assumptions must be an array",
                "why_it_matters": "Schema requires assumptions to be a list",
            }
        )
        return False, defects

    # Collect assumption IDs for uniqueness check
    assumption_ids = []

    # Validate each assumption
    for idx, assumption in enumerate(assumptions):
        assumption_defects = validate_assumption(assumption, idx)
        defects.extend(assumption_defects)

        # Track assumption_id for uniqueness
        assumption_id = assumption.get("assumption_id")
        if assumption_id:
            assumption_ids.append(assumption_id)

    # Check assumption_id uniqueness
    assumption_id_counts = {}
    for assumption_id in assumption_ids:
        assumption_id_counts[assumption_id] = (
            assumption_id_counts.get(assumption_id, 0) + 1
        )

    for assumption_id, count in assumption_id_counts.items():
        if count > 1:
            defects.append(
                {
                    "severity": "critical",
                    "category": "contradiction",
                    "location": "/plan/assumptions",
                    "problem": f"assumption_id '{assumption_id}' appears {count} times (must be unique)",
                    "why_it_matters": "Assumption IDs must be unique for traceability",
                }
            )

    passed = all(d["severity"] != "critical" for d in defects)
    return passed, defects


def validate_assumption(assumption: Dict[str, Any], idx: int) -> List[Dict[str, Any]]:
    """Validate a single assumption."""
    defects = []
    location = f"/plan/assumptions/{idx}"

    # Required fields
    required_fields = ["assumption_id", "statement", "risk_if_false"]
    for field in required_fields:
        if field not in assumption:
            defects.append(
                {
                    "severity": "critical",
                    "category": "missing_field",
                    "location": f"{location}/{field}",
                    "problem": f"Assumption missing required field: {field}",
                    "why_it_matters": "Assumptions must be identifiable, stated, and risk-assessed",
                }
            )

    # Validate assumption_id pattern
    assumption_id = assumption.get("assumption_id", "")
    if assumption_id:
        if not re.match(r"^A\d{3}$", assumption_id):
            defects.append(
                {
                    "severity": "high",
                    "category": "schema",
                    "location": f"{location}/assumption_id",
                    "problem": f"assumption_id '{assumption_id}' does not match pattern ^A\\d{{3}}$",
                    "why_it_matters": "assumption_id must follow A001-A999 pattern",
                }
            )

    # Validate statement is non-empty and meaningful
    statement = assumption.get("statement", "")
    if not statement or not statement.strip():
        defects.append(
            {
                "severity": "critical",
                "category": "missing_field",
                "location": f"{location}/statement",
                "problem": "Assumption statement is empty",
                "why_it_matters": "Assumption must have a clear statement",
            }
        )
    elif len(statement.strip()) < 10:
        defects.append(
            {
                "severity": "medium",
                "category": "verification_gap",
                "location": f"{location}/statement",
                "problem": f"Assumption statement is too short ({len(statement.strip())} chars)",
                "why_it_matters": "Assumption statement should be descriptive (at least 10 characters)",
            }
        )

    # Validate risk_if_false is non-empty and describes risk
    risk_if_false = assumption.get("risk_if_false", "")
    if not risk_if_false or not risk_if_false.strip():
        defects.append(
            {
                "severity": "critical",
                "category": "missing_field",
                "location": f"{location}/risk_if_false",
                "problem": "risk_if_false is empty",
                "why_it_matters": "Must describe what happens if assumption is false",
            }
        )
    elif len(risk_if_false.strip()) < 10:
        defects.append(
            {
                "severity": "medium",
                "category": "verification_gap",
                "location": f"{location}/risk_if_false",
                "problem": f"risk_if_false is too short ({len(risk_if_false.strip())} chars)",
                "why_it_matters": "Risk description should be descriptive (at least 10 characters)",
            }
        )

    # Check for vague risk descriptions
    vague_phrases = [
        "might fail",
        "could break",
        "may not work",
        "probably won't",
        "issues",
    ]
    risk_lower = risk_if_false.lower()
    if any(phrase in risk_lower for phrase in vague_phrases):
        defects.append(
            {
                "severity": "low",
                "category": "verification_gap",
                "location": f"{location}/risk_if_false",
                "problem": f"risk_if_false contains vague language: {risk_if_false}",
                "why_it_matters": "Risk should be specific (e.g., 'X will fail' not 'X might fail')",
            }
        )

    # Check that statement doesn't contain guessing language
    guessing_phrases = [
        "assume",
        "probably",
        "likely",
        "should",
        "might",
        "TBD",
        "TODO",
    ]
    statement_lower = statement.lower()
    for phrase in guessing_phrases:
        if phrase in statement_lower:
            defects.append(
                {
                    "severity": "high",
                    "category": "verification_gap",
                    "location": f"{location}/statement",
                    "problem": f"Assumption statement contains guessing language: '{phrase}'",
                    "why_it_matters": "Assumptions should be stated as facts, not guesses (e.g., 'X is available' not 'X should be available')",
                }
            )

    return defects


def write_evidence(
    evidence_dir: Path,
    passed: bool,
    defects: List[Dict[str, Any]],
    assumptions_count: int,
) -> None:
    """Write evidence artifacts."""
    evidence_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().isoformat() + "Z"

    summary = {
        "timestamp": timestamp,
        "gate_id": "GATE-004",
        "gate_name": "Assumptions Validation",
        "passed": passed,
        "assumptions_count": assumptions_count,
        "defect_count": len(defects),
        "defects": defects,
    }

    summary_path = evidence_dir / "assumptions_validation.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"Evidence written to: {summary_path}")


def main():
    parser = argparse.ArgumentParser(
        description="GATE-004: Validate assumptions in v3.0.0 plan"
    )
    parser.add_argument("--plan-file", required=True, help="Path to plan JSON file")
    parser.add_argument(
        "--evidence-dir",
        default=".state/evidence/GATE-004",
        help="Directory for evidence output (default: .state/evidence/GATE-004)",
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
    passed, defects = validate_assumptions(plan)

    assumptions_count = len(plan.get("plan", {}).get("assumptions", []))

    # Write evidence
    evidence_dir = Path(args.evidence_dir)
    write_evidence(evidence_dir, passed, defects, assumptions_count)

    # Print results
    if passed:
        print(f"✓ GATE-004 PASSED: All {assumptions_count} assumptions are valid")
        sys.exit(0)
    else:
        print(
            f"✗ GATE-004 FAILED: {len(defects)} defects found in {assumptions_count} assumptions"
        )
        for defect in defects[:5]:  # Show first 5
            print(f"  [{defect['severity']}] {defect['location']}: {defect['problem']}")
        if len(defects) > 5:
            print(f"  ... and {len(defects) - 5} more defects (see evidence file)")
        sys.exit(1)


if __name__ == "__main__":
    main()
