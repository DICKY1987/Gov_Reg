#!/usr/bin/env python3
"""
SEC-021 Quality Controls Catalog Validator

Validates SEC-021 JSON file against schema and checks semantic constraints:
- control_id uniqueness
- all required fields present
- evidence paths use deterministic formulas
- control_mappings reference valid control_ids

Usage:
    python validators/validate_sec_021.py sections/sec_021_quality_controls_catalog.json
    python validators/validate_sec_021.py sections/sec_021_quality_controls_catalog.json --schema schemas/sec_021_quality_controls_catalog.schema.json
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

try:
    import jsonschema
    from jsonschema import Draft7Validator, ValidationError
except ImportError:
    jsonschema = None
    Draft7Validator = None
    ValidationError = None


def load_json(path: Path) -> dict[str, Any]:
    """Load and parse a JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_control_id_uniqueness(data: dict[str, Any]) -> tuple[bool, list[str]]:
    """Check that all control_id values are unique."""
    controls = data.get("quality_controls_catalog", {}).get("controls", [])
    control_ids = [c.get("control_id") for c in controls]

    seen = set()
    duplicates = []
    for cid in control_ids:
        if cid in seen:
            duplicates.append(cid)
        seen.add(cid)

    return len(duplicates) == 0, duplicates


def validate_required_fields(data: dict[str, Any]) -> tuple[bool, list[str]]:
    """Check that all required top-level and control fields are present."""
    missing = []

    # Top-level required fields
    required_top = ["section_id", "title", "required", "instructions_file", "quality_controls_catalog"]
    for field in required_top:
        if field not in data:
            missing.append(f"top-level.{field}")

    # Quality controls catalog required fields
    catalog = data.get("quality_controls_catalog", {})
    required_catalog = ["version", "description", "control_classes", "controls", "control_mappings", "enforcement_policy"]
    for field in required_catalog:
        if field not in catalog:
            missing.append(f"quality_controls_catalog.{field}")

    # Per-control required fields
    for i, control in enumerate(catalog.get("controls", [])):
        required_control = ["control_id", "class", "name", "description", "enforcement", "evidence_requirements", "severity"]
        for field in required_control:
            if field not in control:
                missing.append(f"controls[{i}].{field}")

    return len(missing) == 0, missing


def validate_evidence_paths_deterministic(data: dict[str, Any]) -> tuple[bool, list[str]]:
    """Check that evidence paths use deterministic template variables."""
    valid_vars = {"{{PHASE}}", "{{CONTROL_ID}}", "{{ARTIFACT_NAME}}", "{{RUN_ID}}", "{{GATE_ID}}", "{{PLAN_ID}}"}
    issues = []

    controls = data.get("quality_controls_catalog", {}).get("controls", [])
    for control in controls:
        evidence = control.get("evidence_requirements", {})
        path_formula = evidence.get("path_formula", "")

        # Extract template variables from path_formula
        import re
        found_vars = set(re.findall(r"\{\{[A-Z_]+\}\}", path_formula))

        # Check for unknown variables
        unknown = found_vars - valid_vars
        if unknown:
            issues.append(f"{control.get('control_id')}: unknown variables {unknown}")

    return len(issues) == 0, issues


def validate_control_mappings(data: dict[str, Any]) -> tuple[bool, list[str]]:
    """Check that control_mappings reference valid control_ids."""
    catalog = data.get("quality_controls_catalog", {})
    controls = catalog.get("controls", [])
    valid_ids = {c.get("control_id") for c in controls}

    issues = []
    mappings = catalog.get("control_mappings", {})

    # Check by_phase mappings
    for phase, ctrl_ids in mappings.get("by_phase", {}).items():
        for cid in ctrl_ids:
            if cid not in valid_ids:
                issues.append(f"by_phase.{phase}: invalid control_id '{cid}'")

    # Check by_gate mappings
    for gate, ctrl_ids in mappings.get("by_gate", {}).items():
        for cid in ctrl_ids:
            if cid not in valid_ids:
                issues.append(f"by_gate.{gate}: invalid control_id '{cid}'")

    return len(issues) == 0, issues


def validate_schema(data: dict[str, Any], schema_path: Path) -> tuple[bool, list[str]]:
    """Validate data against JSON Schema."""
    schema = load_json(schema_path)
    validator = Draft7Validator(schema)

    errors = []
    for error in validator.iter_errors(data):
        path = ".".join(str(p) for p in error.absolute_path) or "root"
        errors.append(f"{path}: {error.message}")

    return len(errors) == 0, errors


def validate_sec_021_file(sec_021_path: Path) -> Dict:
    """
    Validate SEC-021 file.
    Returns dict with validation results.
    """
    try:
        with open(sec_021_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return {
            "status": "error",
            "error": f"JSON parse error: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
    
    # Extract controls
    controls = data.get('quality_controls_catalog', {}).get('controls', [])
    
    # Check control_id uniqueness
    control_ids = []
    for control in controls:
        cid = control.get('control_id', '')
        control_ids.append(cid)
    
    unique_ids = set(control_ids)
    duplicates = [cid for cid in unique_ids if control_ids.count(cid) > 1]
    
    # Check required fields
    required_fields = ['control_id', 'title', 'control_class', 'required', 'intent']
    missing_fields = []
    
    for control in controls:
        for field in required_fields:
            if field not in control:
                missing_fields.append(f"{control.get('control_id', 'UNKNOWN')}.{field}")
    
    # Determine status
    control_id_uniqueness = len(duplicates) == 0
    all_required_fields_present = len(missing_fields) == 0
    
    result = {
        "control_id_uniqueness": control_id_uniqueness,
        "all_required_fields_present": all_required_fields_present,
        "control_count": len(controls),
        "status": "pass" if (control_id_uniqueness and all_required_fields_present) else "fail"
    }
    
    if duplicates:
        result["duplicate_control_ids"] = duplicates
    
    if missing_fields:
        result["missing_fields"] = missing_fields
    
    return result


def main():
    parser = argparse.ArgumentParser(description="Validate SEC-021 Quality Controls Catalog")
    parser.add_argument("input_file", type=Path, help="Path to SEC-021 JSON file")
    parser.add_argument("--schema", type=Path, default=None, help="Path to JSON Schema (optional)")
    parser.add_argument("--output", type=Path, default=None, help="Path to write validation report JSON")
    args = parser.parse_args()

    # Load input file
    try:
        data = load_json(args.input_file)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {args.input_file}: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: File not found: {args.input_file}")
        sys.exit(1)

    # Run validations
    results = {
        "input_file": str(args.input_file),
        "schema_file": str(args.schema) if args.schema else None,
        "validations": {}
    }

    all_passed = True

    # Schema validation (if schema provided)
    if args.schema:
        schema_valid, schema_errors = validate_schema(data, args.schema)
        results["validations"]["schema"] = {
            "passed": schema_valid,
            "errors": schema_errors
        }
        if not schema_valid:
            all_passed = False

    # Control ID uniqueness
    unique, duplicates = validate_control_id_uniqueness(data)
    results["validations"]["control_id_uniqueness"] = {
        "passed": unique,
        "duplicates": duplicates
    }
    print(f"control_id_uniqueness: {str(unique).lower()}")
    if not unique:
        all_passed = False

    # Required fields
    fields_ok, missing = validate_required_fields(data)
    results["validations"]["required_fields"] = {
        "passed": fields_ok,
        "missing": missing
    }
    print(f"all_required_fields_present: {str(fields_ok).lower()}")
    if not fields_ok:
        all_passed = False

    # Evidence path determinism
    paths_ok, path_issues = validate_evidence_paths_deterministic(data)
    results["validations"]["evidence_paths"] = {
        "passed": paths_ok,
        "issues": path_issues
    }
    print(f"evidence_paths_deterministic: {str(paths_ok).lower()}")
    if not paths_ok:
        all_passed = False

    # Control mappings
    mappings_ok, mapping_issues = validate_control_mappings(data)
    results["validations"]["control_mappings"] = {
        "passed": mappings_ok,
        "issues": mapping_issues
    }
    print(f"control_mappings_valid: {str(mappings_ok).lower()}")
    if not mappings_ok:
        all_passed = False

    # Overall status
    results["status"] = "pass" if all_passed else "fail"
    print(f"status: {results['status']}")

    # Write output file if specified
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"Report written to: {args.output}")

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
