#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any

from validator_common import (
    MUTATION_TYPES,
    artifact_record_id,
    artifact_record_path,
    artifact_records,
    base_evidence,
    default_main,
    fail,
    observe,
    required_step_output_paths,
)


TRACEABILITY_KEYS = (
    "traceability_refs",
    "linked_requirement_ids",
    "linked_module_ids",
    "linked_component_ids",
    "linked_step_ids",
)


def non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def non_empty_list(value: Any) -> bool:
    return isinstance(value, list) and any(item not in (None, "") for item in value)


def has_traceability(record: dict[str, Any]) -> bool:
    if record.get("phase_id") and record.get("step_id"):
        return True
    return any(non_empty_list(record.get(key)) for key in TRACEABILITY_KEYS)


def validate(plan_path: Path, plan: dict[str, Any]) -> dict[str, Any]:
    evidence = base_evidence("GATE-ARTIFACT-001", plan_path)
    section = plan.get("artifact_intent_manifest")
    if not isinstance(section, dict):
        fail(evidence, "Missing artifact_intent_manifest section")
        return evidence

    if not isinstance(section.get("checks"), dict):
        fail(evidence, "artifact_intent_manifest.checks must be an object")

    records = artifact_records(plan)
    if not isinstance(section.get("records"), list):
        fail(evidence, "artifact_intent_manifest.records must be an array")

    by_path = {artifact_record_path(record): record for record in records if artifact_record_path(record)}
    for phase_id, step_id, output_path in sorted(required_step_output_paths(plan)):
        if output_path not in by_path:
            fail(evidence, "Required step output is missing from artifact_intent_manifest", phase_id=phase_id, step_id=step_id, path=output_path)

    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    context_artifact_ids = {
        str(item.get("context_artifact_id") or item.get("artifact_id") or item.get("id"))
        for item in plan.get("referenced_context_artifacts", {}).get("artifacts", [])
        if isinstance(item, dict) and (item.get("context_artifact_id") or item.get("artifact_id") or item.get("id"))
    }
    for record in records:
        record_id = artifact_record_id(record)
        if not record_id:
            fail(evidence, "Artifact intent record missing identifier", record=record)
        elif record_id in seen_ids:
            fail(evidence, "Duplicate artifact intent identifier", artifact_id=record_id)
        else:
            seen_ids.add(record_id)
        mutation_type = record.get("mutation_type") or record.get("planned_mutation_type")
        if mutation_type not in MUTATION_TYPES:
            fail(evidence, "Invalid artifact intent mutation type", artifact_id=record_id, mutation_type=mutation_type)
        path_value = artifact_record_path(record)
        if not path_value:
            fail(evidence, "Artifact intent record missing planned path", artifact_id=record_id)
        elif path_value in seen_paths:
            fail(evidence, "Duplicate artifact intent path", artifact_id=record_id, path=path_value)
        else:
            seen_paths.add(path_value)
        if not non_empty_string(record.get("purpose")):
            fail(evidence, "Artifact intent record missing purpose", artifact_id=record_id)
        if not isinstance(record.get("required_for_definition_of_done"), bool):
            fail(evidence, "Artifact intent required_for_definition_of_done must be boolean", artifact_id=record_id)
        if not non_empty_list(record.get("validation_sources")):
            fail(evidence, "Artifact intent record missing validation_sources", artifact_id=record_id)
        if not has_traceability(record):
            fail(evidence, "Artifact intent record is not traceable to a step or traceability refs", artifact_id=record_id)
        dependencies = record.get("context_artifact_dependencies", [])
        if not isinstance(dependencies, list):
            fail(evidence, "Artifact intent context_artifact_dependencies must be an array", artifact_id=record_id)
        else:
            for dependency in dependencies:
                if str(dependency) not in context_artifact_ids:
                    fail(evidence, "Artifact intent references undeclared context artifact", artifact_id=record_id, context_artifact_id=dependency)
    observe(evidence, "Validated artifact intent manifest", record_count=len(records))
    return evidence


if __name__ == "__main__":
    default_main("artifact_intent_manifest", validate)
