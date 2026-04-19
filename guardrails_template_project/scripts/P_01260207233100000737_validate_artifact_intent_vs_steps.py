#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any

from validator_common import (
    artifact_record_path,
    artifact_records,
    base_evidence,
    default_main,
    fail,
    observe,
    required_step_output_paths,
)


def validate(plan_path: Path, plan: dict[str, Any]) -> dict[str, Any]:
    evidence = base_evidence("GATE-ARTIFACT-002", plan_path)
    declared = {artifact_record_path(record) for record in artifact_records(plan) if artifact_record_path(record)}
    required_outputs = required_step_output_paths(plan)
    outputs_by_step: dict[tuple[str, str], set[str]] = {}
    for phase_id, step_id, output_path in required_outputs:
        outputs_by_step.setdefault((phase_id, step_id), set()).add(output_path)

    for phase_id, step_id, output_path in sorted(required_outputs):
        if output_path not in declared:
            fail(evidence, "Step output has no declared artifact intent", phase_id=phase_id, step_id=step_id, path=output_path)

    for record in artifact_records(plan):
        phase_id = record.get("phase_id") or record.get("planned_phase_id")
        step_id = record.get("step_id") or record.get("planned_step_id")
        path_value = artifact_record_path(record)
        if phase_id and step_id:
            step_key = (str(phase_id), str(step_id))
            if step_key not in outputs_by_step:
                fail(evidence, "Artifact intent record references a step with no required output", phase_id=phase_id, step_id=step_id)
            elif path_value and path_value not in outputs_by_step[step_key]:
                fail(evidence, "Artifact intent path is not produced by the referenced step", phase_id=phase_id, step_id=step_id, path=path_value)
    observe(evidence, "Compared artifact intent records to step outputs", declared_count=len(declared), required_output_count=len(required_outputs))
    return evidence


if __name__ == "__main__":
    default_main("artifact_intent_vs_steps", validate)
