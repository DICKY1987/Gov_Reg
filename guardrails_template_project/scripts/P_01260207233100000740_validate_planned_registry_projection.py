#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any

from validator_common import (
    artifact_record_id,
    artifact_record_path,
    artifact_records,
    base_evidence,
    default_main,
    fail,
    observe,
    planned_registry_records,
)


META_FIELDS = {"projection_id", "artifact_intent_ref", "notes"}
RUNTIME_PREFIXES = ("observed_", "actual_", "derived_", "computed_", "runtime_")
TEMPORAL_WORDS = ("date", "time", "timestamp", "created", "modified")
REQUIRED_RECORD_FIELDS = {
    "projection_id",
    "artifact_intent_ref",
    "planned_relative_path",
    "planned_artifact_kind",
    "planned_mutation_type",
    "planned_lifecycle_state",
    "planned_phase_id",
    "planned_step_id",
    "planned_validation_sources",
    "planned_registry_inclusion",
}
MUTATION_TO_LIFECYCLE = {
    "create_new": "PLANNED_CREATE",
    "edit_existing": "PLANNED_EDIT",
    "remove_existing": "PLANNED_DELETE",
}


def validate(plan_path: Path, plan: dict[str, Any]) -> dict[str, Any]:
    evidence = base_evidence("GATE-REGISTRY-001", plan_path)
    section = plan.get("planned_registry_projection")
    if not isinstance(section, dict):
        fail(evidence, "Missing planned_registry_projection section")
        return evidence

    if section.get("enabled") is not True:
        fail(evidence, "planned_registry_projection.enabled must be true")

    policy = section.get("projection_policy")
    if not isinstance(policy, dict):
        fail(evidence, "planned_registry_projection.projection_policy must be an object")
        policy = {}
    for field in (
        "allow_only_pre_execution_known_fields",
        "forbid_runtime_observed_fields",
        "forbid_derived_fields",
        "forbid_content_hash_claims_before_execution",
        "intent_prefix_required_for_temporal_fields",
    ):
        if policy.get(field) is not True:
            fail(evidence, "Projection policy flag must be true", field=field, observed=policy.get(field))

    allowed = set(section.get("allowed_projected_fields", [])) | META_FIELDS
    forbidden = set(section.get("forbidden_projected_fields", []))
    artifact_by_id = {artifact_record_id(record): record for record in artifact_records(plan) if artifact_record_id(record)}
    projected_artifact_refs: set[str] = set()
    seen_projection_ids: set[str] = set()

    for record in planned_registry_records(plan):
        projection_id = record.get("projection_id") or record.get("id")
        if not projection_id:
            fail(evidence, "Projected registry record missing projection_id")
        elif str(projection_id) in seen_projection_ids:
            fail(evidence, "Duplicate projected registry projection_id", projection_id=projection_id)
        else:
            seen_projection_ids.add(str(projection_id))
        missing_fields = sorted(field for field in REQUIRED_RECORD_FIELDS if field not in record)
        if missing_fields:
            fail(evidence, "Projected registry record missing required fields", projection_id=projection_id, missing_fields=missing_fields)

        for key in record:
            if key in forbidden or key.startswith(RUNTIME_PREFIXES):
                fail(evidence, "Projected record contains runtime or derived field", projection_id=projection_id, field=key)
            if key not in allowed:
                fail(evidence, "Projected record contains a field outside allowed projection fields", projection_id=projection_id, field=key)
            if any(word in key for word in TEMPORAL_WORDS) and not key.startswith("planned_") and key not in META_FIELDS:
                fail(evidence, "Temporal projection field is not planned_-prefixed", projection_id=projection_id, field=key)

        artifact_ref = record.get("artifact_intent_ref")
        if not artifact_ref:
            fail(evidence, "Projected registry record missing artifact_intent_ref", projection_id=projection_id)
            continue
        artifact_ref = str(artifact_ref)
        projected_artifact_refs.add(artifact_ref)
        artifact = artifact_by_id.get(artifact_ref)
        if artifact is None:
            fail(evidence, "Projected registry record references unknown artifact intent", projection_id=projection_id, artifact_intent_ref=artifact_ref)
            continue

        expected_path = artifact_record_path(artifact)
        if expected_path and record.get("planned_relative_path") != expected_path:
            fail(evidence, "Projected registry path does not match artifact intent path", projection_id=projection_id, artifact_intent_ref=artifact_ref, expected=expected_path, observed=record.get("planned_relative_path"))
        expected_mutation = artifact.get("mutation_type") or artifact.get("planned_mutation_type")
        if expected_mutation and record.get("planned_mutation_type") != expected_mutation:
            fail(evidence, "Projected registry mutation does not match artifact intent mutation", projection_id=projection_id, artifact_intent_ref=artifact_ref, expected=expected_mutation, observed=record.get("planned_mutation_type"))
        expected_lifecycle = MUTATION_TO_LIFECYCLE.get(str(expected_mutation))
        if expected_lifecycle and record.get("planned_lifecycle_state") != expected_lifecycle:
            fail(evidence, "Projected registry lifecycle does not match mutation type", projection_id=projection_id, artifact_intent_ref=artifact_ref, expected=expected_lifecycle, observed=record.get("planned_lifecycle_state"))
        if artifact.get("phase_id") and record.get("planned_phase_id") != artifact.get("phase_id"):
            fail(evidence, "Projected registry phase does not match artifact intent phase", projection_id=projection_id, artifact_intent_ref=artifact_ref)
        if artifact.get("step_id") and record.get("planned_step_id") != artifact.get("step_id"):
            fail(evidence, "Projected registry step does not match artifact intent step", projection_id=projection_id, artifact_intent_ref=artifact_ref)
        validation_sources = record.get("planned_validation_sources")
        if not isinstance(validation_sources, list) or not validation_sources:
            fail(evidence, "Projected registry record missing planned_validation_sources", projection_id=projection_id, artifact_intent_ref=artifact_ref)

    missing_projections = sorted(set(artifact_by_id) - projected_artifact_refs)
    for artifact_id in missing_projections:
        fail(evidence, "Artifact intent has no planned registry projection", artifact_intent_ref=artifact_id)

    observe(evidence, "Validated planned registry projection", record_count=len(planned_registry_records(plan)))
    return evidence


if __name__ == "__main__":
    default_main("planned_registry_projection", validate)
