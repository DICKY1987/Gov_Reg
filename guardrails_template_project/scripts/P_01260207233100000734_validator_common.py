#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ALLOWED_AUTHORITY_LEVELS = {"AUTHORITATIVE", "CONSTRAINING", "INFORMATIONAL"}
MUTATION_TYPES = {"create_new", "edit_existing", "remove_existing"}
NEW_GATE_EVIDENCE = {
    "referenced_context_artifacts": ".state/evidence/GATE-CONTEXT-001/validation.json",
    "context_authority_resolution": ".state/evidence/GATE-CONTEXT-002/validation.json",
    "artifact_intent_manifest": ".state/evidence/GATE-ARTIFACT-001/validation.json",
    "artifact_intent_vs_steps": ".state/evidence/GATE-ARTIFACT-002/validation.json",
    "planned_registry_projection": ".state/evidence/GATE-REGISTRY-001/validation.json",
    "artifact_reconciliation": ".state/evidence/GATE-RECON-001/validation.json",
    "registry_projection_reconciliation": ".state/evidence/GATE-RECON-002/validation.json",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_path(path_value: str | Path) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return ROOT / path


def load_plan(path_arg: str) -> tuple[Path, dict[str, Any]]:
    path = repo_path(path_arg)
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("Plan document must be a JSON object")
    return path, payload


def json_dump(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def emit_and_exit(payload: dict[str, Any], evidence_rel: str) -> None:
    json_dump(repo_path(evidence_rel), payload)
    print(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True))
    raise SystemExit(0 if payload.get("status") == "PASS" else 1)


def base_evidence(check_id: str, plan_path: Path) -> dict[str, Any]:
    return {
        "check_id": check_id,
        "plan_path": str(plan_path.relative_to(ROOT) if plan_path.is_relative_to(ROOT) else plan_path),
        "generated_at": utc_now(),
        "status": "PASS",
        "errors": [],
        "warnings": [],
        "observations": [],
    }


def fail(payload: dict[str, Any], message: str, **details: Any) -> None:
    payload["status"] = "FAIL"
    entry = {"message": message}
    entry.update(details)
    payload.setdefault("errors", []).append(entry)


def warn(payload: dict[str, Any], message: str, **details: Any) -> None:
    entry = {"message": message}
    entry.update(details)
    payload.setdefault("warnings", []).append(entry)


def observe(payload: dict[str, Any], message: str, **details: Any) -> None:
    entry = {"message": message}
    entry.update(details)
    payload.setdefault("observations", []).append(entry)


def iter_steps(plan: dict[str, Any]) -> list[tuple[str, str, dict[str, Any]]]:
    steps: list[tuple[str, str, dict[str, Any]]] = []
    contracts = plan.get("step_contracts", {})
    if not isinstance(contracts, dict):
        return steps
    for phase_id, phase_steps in contracts.items():
        if not isinstance(phase_steps, dict):
            continue
        for step_key, step in phase_steps.items():
            if isinstance(step, dict):
                steps.append((str(phase_id), str(step.get("step_id") or step_key), step))
    return steps


def required_step_output_paths(plan: dict[str, Any]) -> set[tuple[str, str, str]]:
    paths: set[tuple[str, str, str]] = set()
    for phase_id, step_id, step in iter_steps(plan):
        outputs = step.get("outputs", [])
        if not isinstance(outputs, list):
            continue
        for output in outputs:
            if not isinstance(output, dict):
                continue
            if output.get("required") is False:
                continue
            path_value = output.get("path")
            if path_value:
                paths.add((phase_id, step_id, str(path_value)))
    return paths


def artifact_records(plan: dict[str, Any]) -> list[dict[str, Any]]:
    manifest = plan.get("artifact_intent_manifest", {})
    records = manifest.get("records", []) if isinstance(manifest, dict) else []
    return [record for record in records if isinstance(record, dict)]


def artifact_record_path(record: dict[str, Any]) -> str | None:
    for key in ("planned_relative_path", "relative_path", "path"):
        value = record.get(key)
        if value:
            return str(value)
    return None


def artifact_record_id(record: dict[str, Any]) -> str | None:
    for key in ("artifact_intent_id", "artifact_id", "id"):
        value = record.get(key)
        if value:
            return str(value)
    return None


def planned_registry_records(plan: dict[str, Any]) -> list[dict[str, Any]]:
    projection = plan.get("planned_registry_projection", {})
    records = projection.get("records", []) if isinstance(projection, dict) else []
    return [record for record in records if isinstance(record, dict)]


def default_main(evidence_key: str, validator) -> None:
    plan_arg = sys.argv[1] if len(sys.argv) > 1 else "NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_2.json"
    plan_path, plan = load_plan(plan_arg)
    payload = validator(plan_path, plan)
    emit_and_exit(payload, NEW_GATE_EVIDENCE[evidence_key])
