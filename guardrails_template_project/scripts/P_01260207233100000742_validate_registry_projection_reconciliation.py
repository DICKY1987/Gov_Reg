#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any

from validator_common import base_evidence, default_main, fail, observe, planned_registry_records


FIELD_MAP = {
    "planned_relative_path": ("relative_path", "path", "planned_relative_path"),
    "planned_artifact_kind": ("artifact_kind", "planned_artifact_kind"),
    "planned_mutation_type": ("mutation_type", "planned_mutation_type"),
    "planned_module_id": ("module_id", "planned_module_id"),
    "planned_component_id": ("component_id", "planned_component_id"),
    "planned_phase_id": ("phase_id", "planned_phase_id"),
    "planned_step_id": ("step_id", "planned_step_id"),
    "planned_registry_inclusion": ("registry_inclusion", "planned_registry_inclusion"),
}
EXPLANATION_FIELDS = ("deviation_explanation", "reconciliation_explanation", "mismatch_explanation")


def has_explanation(record: dict[str, Any]) -> bool:
    return any(isinstance(record.get(field), str) and record[field].strip() for field in EXPLANATION_FIELDS)


def observed_value(record: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in record:
            return record[key]
    return None


def validate(plan_path: Path, plan: dict[str, Any]) -> dict[str, Any]:
    evidence = base_evidence("GATE-RECON-002", plan_path)
    observed_registry = plan.get("observed_registry_writes")
    projections = planned_registry_records(plan)
    if observed_registry is None:
        observe(evidence, "No observed_registry_writes section present; planning-only registry reconciliation completed", planned_projection_count=len(projections))
        return evidence
    if not isinstance(observed_registry, list):
        fail(evidence, "observed_registry_writes must be an array when present")
        return evidence

    observed_by_path = {
        str(item.get("relative_path") or item.get("path")): item
        for item in observed_registry
        if isinstance(item, dict) and (item.get("relative_path") or item.get("path"))
    }
    for projection in projections:
        path_value = projection.get("planned_relative_path")
        if not path_value:
            fail(evidence, "Projected registry record is missing planned_relative_path", projection_id=projection.get("projection_id"))
            continue
        observed = observed_by_path.get(str(path_value))
        if observed is None:
            fail(evidence, "Projected registry record was not observed", path=path_value)
            continue
        for planned_field, observed_fields in FIELD_MAP.items():
            if planned_field not in projection:
                continue
            expected = projection.get(planned_field)
            actual = observed_value(observed, observed_fields)
            if actual is not None and actual != expected and not has_explanation(observed):
                fail(
                    evidence,
                    "Observed registry value differs from planned projection without explanation",
                    path=path_value,
                    field=planned_field,
                    expected=expected,
                    observed=actual,
                )

    projected_paths = {str(record.get("planned_relative_path")) for record in projections if record.get("planned_relative_path")}
    for path_value, observed in sorted(observed_by_path.items()):
        if path_value not in projected_paths and not has_explanation(observed):
            fail(evidence, "Observed registry write has no planned projection or explanation", path=path_value)
    observe(evidence, "Compared planned registry projection to observed writes", observed_count=len(observed_by_path), planned_projection_count=len(projections))
    return evidence


if __name__ == "__main__":
    default_main("registry_projection_reconciliation", validate)
