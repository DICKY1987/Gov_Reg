#!/usr/bin/env python3
"""
GATE-000: Structural consistency pre-check.

Validates plan JSON structure before any phase executes.
Checks:
  1. Plan JSON is parseable
  2. Required top-level keys present
  3. All IDs unique (gate_ids, phase_ids)
  4. Cross-references resolve (gates reference valid phases)
  5. No forbidden obfuscation patterns (TMP-07)
  6. No dual definitions (TMP-01)

Usage:
  python P_01260207233100000258_validate_plan_structure.py <plan_path>

Evidence output:
  .state/evidence/PRE/structure_validation.json
"""

import json
import re
import sys
import argparse
from pathlib import Path


OBFUSCATION_PATTERNS = [
    re.compile(r"\bchr\s*\("),
    re.compile(r"\beval\s*\("),
    re.compile(r"\bexec\s*\("),
    re.compile(r"\bbase64\b"),
]

REQUIRED_TOP_LEVEL_KEYS = [
    "template_metadata",
    "critical_constraint",
    "validation_gates",
    "phase_contracts",
    "metrics",
    "infrastructure",
]


def validate_structure(plan_path: Path) -> dict:
    results = {
        "plan_path": str(plan_path),
        "structure_ok": True,
        "cross_refs_ok": True,
        "ids_unique": True,
        "no_obfuscation": True,
        "no_dual_definitions": True,
        "errors": [],
    }

    # 1. Parse JSON
    try:
        with open(plan_path, "r", encoding="utf-8") as f:
            plan = json.load(f)
    except json.JSONDecodeError as e:
        results["structure_ok"] = False
        results["errors"].append(f"JSON parse error: {e}")
        return results
    except FileNotFoundError:
        results["structure_ok"] = False
        results["errors"].append(f"File not found: {plan_path}")
        return results

    # 2. Required top-level keys
    missing = [k for k in REQUIRED_TOP_LEVEL_KEYS if k not in plan]
    if missing:
        results["structure_ok"] = False
        results["errors"].append(f"Missing top-level keys: {missing}")

    # 3. Unique IDs
    # Gate IDs
    gates = plan.get("validation_gates", [])
    if isinstance(gates, list):
        gate_ids = [g.get("gate_id") for g in gates if isinstance(g, dict)]
        if len(gate_ids) != len(set(gate_ids)):
            results["ids_unique"] = False
            dupes = [gid for gid in gate_ids if gate_ids.count(gid) > 1]
            results["errors"].append(f"Duplicate gate_ids: {set(dupes)}")

    # Phase contract IDs
    contracts = plan.get("phase_contracts", {})
    if isinstance(contracts, dict):
        phase_ids = [k for k in contracts.keys() if k.startswith("PH-")]
        if len(phase_ids) != len(set(phase_ids)):
            results["ids_unique"] = False
            results["errors"].append("Duplicate phase contract IDs found")

    # 4. Cross-references: gates reference valid phases
    if isinstance(gates, list) and isinstance(contracts, dict):
        valid_phases = set(contracts.keys())
        # Also allow "PRE" as a special phase for GATE-000
        valid_phases.add("PRE")
        for gate in gates:
            if not isinstance(gate, dict):
                continue
            gate_phase = gate.get("phase")
            gate_id = gate.get("gate_id", "?")
            if gate_phase and gate_phase not in valid_phases:
                results["cross_refs_ok"] = False
                results["errors"].append(
                    f"Gate {gate_id} references phase '{gate_phase}' not in phase_contracts"
                )

    # 5. Obfuscation check (TMP-07) -- scan only command strings, not rule descriptions
    def extract_command_strings(obj):
        """Extract all command/command string values from gates and validation sections."""
        commands = []
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == "command" and isinstance(v, str):
                    commands.append(v)
                elif k == "command" and isinstance(v, dict):
                    # Structured command: join command_ref + args
                    parts = [v.get("command_ref", "")] + v.get("args", [])
                    commands.append(" ".join(parts))
                else:
                    commands.extend(extract_command_strings(v))
        elif isinstance(obj, list):
            for item in obj:
                commands.extend(extract_command_strings(item))
        return commands

    command_strings = extract_command_strings(plan.get("validation_gates", []))
    command_strings.extend(extract_command_strings(plan.get("self_healing", {})))
    all_commands_text = " ".join(command_strings)
    for pattern in OBFUSCATION_PATTERNS:
        matches = pattern.findall(all_commands_text)
        if matches:
            results["no_obfuscation"] = False
            results["errors"].append(
                f"Obfuscation pattern '{pattern.pattern}' found in commands ({len(matches)} occurrences)"
            )

    # 6. Dual definition check (TMP-01)
    # Look for fields that have both "original" and "corrected" variants
    def check_dual_defs(obj, path=""):
        if isinstance(obj, dict):
            keys = list(obj.keys())
            for k in keys:
                if k.startswith("original_") or k.endswith("_original"):
                    corrected_key = k.replace("original", "corrected")
                    if corrected_key in keys:
                        results["no_dual_definitions"] = False
                        results["errors"].append(
                            f"Dual definition at {path}: '{k}' and '{corrected_key}'"
                        )
                check_dual_defs(obj[k], f"{path}/{k}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                check_dual_defs(item, f"{path}/{i}")

    check_dual_defs(plan)

    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-file", required=True, help="Path to plan JSON file")
    parser.add_argument(
        "--evidence-dir", required=True, help="Evidence output directory"
    )
    args = parser.parse_args()
    if False:  # Argparse handles required args
        print(__doc__)
        sys.exit(1)

    plan_path = Path(args.plan_file)
    results = validate_structure(plan_path)

    # Write evidence
    evidence_dir = Path(args.evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    evidence_path = evidence_dir / "structure_validation.json"
    with open(evidence_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        f.write("\n")

    # Print summary
    print(f"structure_ok: {str(results['structure_ok']).lower()}")
    print(f"cross_refs_ok: {str(results['cross_refs_ok']).lower()}")
    print(f"ids_unique: {str(results['ids_unique']).lower()}")
    print(f"no_obfuscation: {str(results['no_obfuscation']).lower()}")
    print(f"no_dual_definitions: {str(results['no_dual_definitions']).lower()}")

    if results["errors"]:
        print(f"\nErrors ({len(results['errors'])}):")
        for err in results["errors"]:
            print(f"  - {err}")
        sys.exit(1)

    print(f"\nEvidence written to: {evidence_path}")
    sys.exit(0)


if __name__ == "__main__":
    main()
