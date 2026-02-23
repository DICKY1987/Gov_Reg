#!/usr/bin/env python3
"""Add missing Python-specific headers to the column dictionary."""

import json
from datetime import datetime, timezone
from pathlib import Path

# Define the 37 missing Python headers
MISSING_HEADERS = {
    "py_analysis_run_id": {
        "value_schema": {"type": ["string", "null"]},
        "scope": {"record_kinds_in": ["entity"], "entity_kinds_in": ["file"]},
        "presence": {"policy": "OPTIONAL", "rules": []},
        "normalization": {"transforms": []},
        "validation": {"rules": []},
        "description": "Unique identifier for the Python analysis run",
    },
    "py_analysis_success": {
        "value_schema": {"type": ["boolean", "null"]},
        "scope": {"record_kinds_in": ["entity"], "entity_kinds_in": ["file"]},
        "presence": {"policy": "OPTIONAL", "rules": []},
        "normalization": {"transforms": []},
        "validation": {"rules": []},
        "description": "Whether Python analysis completed successfully",
    },
    "py_analyzed_at_utc": {
        "value_schema": {"type": ["string", "null"], "format": "date-time"},
        "scope": {"record_kinds_in": ["entity"], "entity_kinds_in": ["file"]},
        "presence": {"policy": "OPTIONAL", "rules": []},
        "normalization": {"transforms": []},
        "validation": {"rules": []},
        "description": "Timestamp when Python analysis was performed",
    },
    "py_ast_dump_hash": {
        "value_schema": {"type": ["string", "null"]},
        "scope": {"record_kinds_in": ["entity"], "entity_kinds_in": ["file"]},
        "presence": {"policy": "OPTIONAL", "rules": []},
        "normalization": {"transforms": []},
        "validation": {"rules": []},
        "description": "Hash of Python AST dump",
    },
    "py_ast_parse_ok": {
        "value_schema": {"type": ["boolean", "null"]},
        "scope": {"record_kinds_in": ["entity"], "entity_kinds_in": ["file"]},
        "presence": {"policy": "OPTIONAL", "rules": []},
        "normalization": {"transforms": []},
        "validation": {"rules": []},
        "description": "Whether Python AST parsing succeeded",
    },
    "py_canonical_candidate_score": {
        "value_schema": {"type": ["number", "null"]},
        "scope": {"record_kinds_in": ["entity"], "entity_kinds_in": ["file"]},
        "presence": {"policy": "OPTIONAL", "rules": []},
        "normalization": {"transforms": []},
        "validation": {"rules": []},
        "description": "Score for canonical candidate selection",
    },
    "py_canonical_text_hash": {
        "value_schema": {"type": ["string", "null"]},
        "scope": {"record_kinds_in": ["entity"], "entity_kinds_in": ["file"]},
        "presence": {"policy": "OPTIONAL", "rules": []},
        "normalization": {"transforms": []},
        "validation": {"rules": []},
        "description": "Hash of canonical Python text",
    },
    "py_capability_facts_hash": {
        "value_schema": {"type": ["string", "null"]},
        "scope": {"record_kinds_in": ["entity"], "entity_kinds_in": ["file"]},
        "presence": {"policy": "OPTIONAL", "rules": []},
        "normalization": {"transforms": []},
        "validation": {"rules": []},
        "description": "Hash of capability facts extracted from Python code",
    },
    "py_capability_tags": {
        "value_schema": {"type": ["array", "null"], "items": {"type": "string"}},
        "scope": {"record_kinds_in": ["entity"], "entity_kinds_in": ["file"]},
        "presence": {"policy": "OPTIONAL", "rules": []},
        "normalization": {"transforms": []},
        "validation": {"rules": []},
        "description": "Capability tags for Python code",
    },
    "py_complexity_cyclomatic": {
        "value_schema": {"type": ["number", "null"]},
        "scope": {"record_kinds_in": ["entity"], "entity_kinds_in": ["file"]},
        "presence": {"policy": "OPTIONAL", "rules": []},
        "normalization": {"transforms": []},
        "validation": {"rules": []},
        "description": "Cyclomatic complexity of Python code",
    },
    "py_component_artifact_path": {
        "value_schema": {"type": ["string", "null"]},
        "scope": {"record_kinds_in": ["entity"], "entity_kinds_in": ["file"]},
        "presence": {"policy": "OPTIONAL", "rules": []},
        "normalization": {"transforms": ["NORMALIZE_SLASHES"]},
        "validation": {"rules": []},
        "description": "Path to component artifact",
    },
    "py_component_count": {
        "value_schema": {"type": ["integer", "null"]},
        "scope": {"record_kinds_in": ["entity"], "entity_kinds_in": ["file"]},
        "presence": {"policy": "OPTIONAL", "rules": []},
        "normalization": {"transforms": []},
        "validation": {"rules": []},
        "description": "Count of Python components",
    },
    "py_component_ids": {
        "value_schema": {"type": ["array", "null"], "items": {"type": "string"}},
        "scope": {"record_kinds_in": ["entity"], "entity_kinds_in": ["file"]},
        "presence": {"policy": "OPTIONAL", "rules": []},
        "normalization": {"transforms": []},
        "validation": {"rules": []},
        "description": "IDs of Python components",
    },
    "py_coverage_percent": {
        "value_schema": {"type": ["number", "null"]},
        "scope": {"record_kinds_in": ["entity"], "entity_kinds_in": ["file"]},
        "presence": {"policy": "OPTIONAL", "rules": []},
        "normalization": {"transforms": []},
        "validation": {"rules": []},
        "description": "Test coverage percentage",
    },
    "py_defs_classes_count": {
        "value_schema": {"type": ["integer", "null"]},
        "scope": {"record_kinds_in": ["entity"], "entity_kinds_in": ["file"]},
        "presence": {"policy": "OPTIONAL", "rules": []},
        "normalization": {"transforms": []},
        "validation": {"rules": []},
        "description": "Count of class definitions",
    },
    "py_defs_functions_count": {
        "value_schema": {"type": ["integer", "null"]},
        "scope": {"record_kinds_in": ["entity"], "entity_kinds_in": ["file"]},
        "presence": {"policy": "OPTIONAL", "rules": []},
        "normalization": {"transforms": []},
        "validation": {"rules": []},
        "description": "Count of function definitions",
    },
    "py_defs_public_api_hash": {
        "value_schema": {"type": ["string", "null"]},
        "scope": {"record_kinds_in": ["entity"], "entity_kinds_in": ["file"]},
        "presence": {"policy": "OPTIONAL", "rules": []},
        "normalization": {"transforms": []},
        "validation": {"rules": []},
        "description": "Hash of public API definitions",
    },
    "py_deliverable_inputs": {
        "value_schema": {"type": ["array", "null"], "items": {"type": "string"}},
        "scope": {"record_kinds_in": ["entity"], "entity_kinds_in": ["file"]},
        "presence": {"policy": "OPTIONAL", "rules": []},
        "normalization": {"transforms": []},
        "validation": {"rules": []},
        "description": "Input deliverables for Python component",
    },
    "py_deliverable_interfaces": {
        "value_schema": {"type": ["array", "null"], "items": {"type": "string"}},
        "scope": {"record_kinds_in": ["entity"], "entity_kinds_in": ["file"]},
        "presence": {"policy": "OPTIONAL", "rules": []},
        "normalization": {"transforms": []},
        "validation": {"rules": []},
        "description": "Interface deliverables for Python component",
    },
    "py_deliverable_kinds": {
        "value_schema": {"type": ["array", "null"], "items": {"type": "string"}},
        "scope": {"record_kinds_in": ["entity"], "entity_kinds_in": ["file"]},
        "presence": {"policy": "OPTIONAL", "rules": []},
        "normalization": {"transforms": []},
        "validation": {"rules": []},
        "description": "Kinds of deliverables produced",
    },
    "py_deliverable_outputs": {
        "value_schema": {"type": ["array", "null"], "items": {"type": "string"}},
        "scope": {"record_kinds_in": ["entity"], "entity_kinds_in": ["file"]},
        "presence": {"policy": "OPTIONAL", "rules": []},
        "normalization": {"transforms": []},
        "validation": {"rules": []},
        "description": "Output deliverables for Python component",
    },
    "py_deliverable_signature_hash": {
        "value_schema": {"type": ["string", "null"]},
        "scope": {"record_kinds_in": ["entity"], "entity_kinds_in": ["file"]},
        "presence": {"policy": "OPTIONAL", "rules": []},
        "normalization": {"transforms": []},
        "validation": {"rules": []},
        "description": "Hash of deliverable signature",
    },
    "py_imports_hash": {
        "value_schema": {"type": ["string", "null"]},
        "scope": {"record_kinds_in": ["entity"], "entity_kinds_in": ["file"]},
        "presence": {"policy": "OPTIONAL", "rules": []},
        "normalization": {"transforms": []},
        "validation": {"rules": []},
        "description": "Hash of all imports",
    },
    "py_imports_local": {
        "value_schema": {"type": ["array", "null"], "items": {"type": "string"}},
        "scope": {"record_kinds_in": ["entity"], "entity_kinds_in": ["file"]},
        "presence": {"policy": "OPTIONAL", "rules": []},
        "normalization": {"transforms": []},
        "validation": {"rules": []},
        "description": "Local/project imports",
    },
    "py_imports_stdlib": {
        "value_schema": {"type": ["array", "null"], "items": {"type": "string"}},
        "scope": {"record_kinds_in": ["entity"], "entity_kinds_in": ["file"]},
        "presence": {"policy": "OPTIONAL", "rules": []},
        "normalization": {"transforms": []},
        "validation": {"rules": []},
        "description": "Standard library imports",
    },
    "py_imports_third_party": {
        "value_schema": {"type": ["array", "null"], "items": {"type": "string"}},
        "scope": {"record_kinds_in": ["entity"], "entity_kinds_in": ["file"]},
        "presence": {"policy": "OPTIONAL", "rules": []},
        "normalization": {"transforms": []},
        "validation": {"rules": []},
        "description": "Third-party imports",
    },
    "py_io_surface_flags": {
        "value_schema": {"type": ["array", "null"], "items": {"type": "string"}},
        "scope": {"record_kinds_in": ["entity"], "entity_kinds_in": ["file"]},
        "presence": {"policy": "OPTIONAL", "rules": []},
        "normalization": {"transforms": []},
        "validation": {"rules": []},
        "description": "I/O surface flags for security analysis",
    },
    "py_overlap_best_match_file_id": {
        "value_schema": {"type": ["string", "null"]},
        "scope": {"record_kinds_in": ["entity"], "entity_kinds_in": ["file"]},
        "presence": {"policy": "OPTIONAL", "rules": []},
        "normalization": {"transforms": []},
        "validation": {"rules": []},
        "description": "File ID of best overlap match",
    },
    "py_overlap_group_id": {
        "value_schema": {"type": ["string", "null"]},
        "scope": {"record_kinds_in": ["entity"], "entity_kinds_in": ["file"]},
        "presence": {"policy": "OPTIONAL", "rules": []},
        "normalization": {"transforms": []},
        "validation": {"rules": []},
        "description": "Group ID for overlapping files",
    },
    "py_overlap_similarity_max": {
        "value_schema": {"type": ["number", "null"]},
        "scope": {"record_kinds_in": ["entity"], "entity_kinds_in": ["file"]},
        "presence": {"policy": "OPTIONAL", "rules": []},
        "normalization": {"transforms": []},
        "validation": {"rules": []},
        "description": "Maximum similarity score for overlaps",
    },
    "py_pytest_exit_code": {
        "value_schema": {"type": ["integer", "null"]},
        "scope": {"record_kinds_in": ["entity"], "entity_kinds_in": ["file"]},
        "presence": {"policy": "OPTIONAL", "rules": []},
        "normalization": {"transforms": []},
        "validation": {"rules": []},
        "description": "pytest exit code",
    },
    "py_quality_score": {
        "value_schema": {"type": ["number", "null"]},
        "scope": {"record_kinds_in": ["entity"], "entity_kinds_in": ["file"]},
        "presence": {"policy": "OPTIONAL", "rules": []},
        "normalization": {"transforms": []},
        "validation": {"rules": []},
        "description": "Quality score for Python code",
    },
    "py_security_risk_flags": {
        "value_schema": {"type": ["array", "null"], "items": {"type": "string"}},
        "scope": {"record_kinds_in": ["entity"], "entity_kinds_in": ["file"]},
        "presence": {"policy": "OPTIONAL", "rules": []},
        "normalization": {"transforms": []},
        "validation": {"rules": []},
        "description": "Security risk flags",
    },
    "py_static_issues_count": {
        "value_schema": {"type": ["integer", "null"]},
        "scope": {"record_kinds_in": ["entity"], "entity_kinds_in": ["file"]},
        "presence": {"policy": "OPTIONAL", "rules": []},
        "normalization": {"transforms": []},
        "validation": {"rules": []},
        "description": "Count of static analysis issues",
    },
    "py_tests_executed": {
        "value_schema": {"type": ["integer", "null"]},
        "scope": {"record_kinds_in": ["entity"], "entity_kinds_in": ["file"]},
        "presence": {"policy": "OPTIONAL", "rules": []},
        "normalization": {"transforms": []},
        "validation": {"rules": []},
        "description": "Number of tests executed",
    },
    "py_tool_versions": {
        "value_schema": {"type": ["object", "null"]},
        "scope": {"record_kinds_in": ["entity"], "entity_kinds_in": ["file"]},
        "presence": {"policy": "OPTIONAL", "rules": []},
        "normalization": {"transforms": []},
        "validation": {"rules": []},
        "description": "Versions of Python analysis tools",
    },
    "py_toolchain_id": {
        "value_schema": {"type": ["string", "null"]},
        "scope": {"record_kinds_in": ["entity"], "entity_kinds_in": ["file"]},
        "presence": {"policy": "OPTIONAL", "rules": []},
        "normalization": {"transforms": []},
        "validation": {"rules": []},
        "description": "Toolchain identifier for Python analysis",
    },
}


def main():
    dict_path = Path(
        "backups/py_columns_20260202_142006/2026012816000001_COLUMN_DICTIONARY.json"
    )

    # Load existing dictionary
    with open(dict_path, "r", encoding="utf-8") as f:
        dictionary = json.load(f)

    # Add missing headers
    added_count = 0
    for header_name, header_def in MISSING_HEADERS.items():
        if header_name not in dictionary["headers"]:
            dictionary["headers"][header_name] = header_def
            added_count += 1

    # Update metadata
    dictionary["header_count_expected"] = len(dictionary["headers"])
    dictionary["dictionary_version"] = "4.2.0"
    dictionary["generated_utc"] = (
        datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )

    # Update header_order if it exists
    if "header_order" in dictionary:
        all_headers = sorted(dictionary["headers"].keys())
        dictionary["header_order"] = all_headers

    # Save updated dictionary
    output_path = Path("2026012816000001_COLUMN_DICTIONARY.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(dictionary, f, indent=2, ensure_ascii=False)

    print(f"✓ Added {added_count} missing Python headers")
    print(f"✓ Updated dictionary to version {dictionary['dictionary_version']}")
    print(f"✓ Total headers: {len(dictionary['headers'])}")
    print(f"✓ Saved to: {output_path}")


if __name__ == "__main__":
    main()
