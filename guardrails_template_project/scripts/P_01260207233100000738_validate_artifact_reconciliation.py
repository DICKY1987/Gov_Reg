#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any

from validator_common import artifact_record_path, artifact_records, base_evidence, default_main, fail, observe, repo_path


EXPLANATION_FIELDS = ("deviation_explanation", "reconciliation_explanation", "mismatch_explanation")


def has_explanation(record: dict[str, Any]) -> bool:
    return any(isinstance(record.get(field), str) and record[field].strip() for field in EXPLANATION_FIELDS)


def validate(plan_path: Path, plan: dict[str, Any]) -> dict[str, Any]:
    evidence = base_evidence("GATE-RECON-001", plan_path)
    observations = plan.get("observed_artifacts")
    records = artifact_records(plan)
    if observations is None:
        observe(evidence, "No observed_artifacts section present; planning-only artifact reconciliation completed", planned_record_count=len(records))
        return evidence
    if not isinstance(observations, list):
        fail(evidence, "observed_artifacts must be an array when present")
        return evidence

    observed_by_path = {
        str(item.get("path") or item.get("relative_path")): item
        for item in observations
        if isinstance(item, dict) and (item.get("path") or item.get("relative_path"))
    }
    observed_paths = set(observed_by_path)
    planned_paths = {artifact_record_path(record) for record in records if artifact_record_path(record)}

    for record in records:
        path_value = artifact_record_path(record)
        mutation_type = record.get("mutation_type") or record.get("planned_mutation_type")
        if not path_value:
            continue
        if mutation_type == "remove_existing":
            if repo_path(path_value).exists() or path_value in observed_paths:
                fail(evidence, "Removed artifact still appears present", path=path_value)
        elif path_value not in observed_paths and not repo_path(path_value).exists():
            fail(evidence, "Planned artifact was not observed after execution", path=path_value)

    for path_value, observation in sorted(observed_by_path.items()):
        if path_value not in planned_paths and not has_explanation(observation):
            fail(evidence, "Observed artifact has no artifact intent record or explanation", path=path_value)
    observe(evidence, "Compared planned artifact intent to observed artifacts", observed_count=len(observed_paths), planned_record_count=len(records))
    return evidence


if __name__ == "__main__":
    default_main("artifact_reconciliation", validate)
