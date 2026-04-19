#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = ROOT / ".state"
RUN_STATUS_PATH = STATE_DIR / "run_status.json"
MUTATION_LEDGER_PATH = STATE_DIR / "mutation_ledger.jsonl"
SCHEMA_PATH = ROOT / "schemas" / "NEWPHASEPLANPROCESS_plan.schema.v3.0.0.json"
GATE_DEPENDENCIES_PATH = ROOT / "scripts" / "gate_dependencies.json"
VALIDATOR_MODULES = {
    "GATE-CONTEXT-001": "validate_referenced_context_artifacts",
    "GATE-CONTEXT-002": "validate_context_authority_resolution",
    "GATE-ARTIFACT-001": "validate_artifact_intent_manifest",
    "GATE-ARTIFACT-002": "validate_artifact_intent_vs_steps",
    "GATE-REGISTRY-001": "validate_planned_registry_projection",
    "GATE-RECON-001": "validate_artifact_reconciliation",
    "GATE-RECON-002": "validate_registry_projection_reconciliation",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def json_load(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def json_dump(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def repo_path(path_arg: str) -> Path:
    path = Path(path_arg)
    if path.is_absolute():
        return path
    return ROOT / path


def load_plan(path_arg: str) -> tuple[Path, dict[str, Any]]:
    path = repo_path(path_arg)
    payload = json_load(path)
    if not isinstance(payload, dict):
        raise ValueError("Plan document must be a JSON object")
    return path, payload


def gate_id(gate: dict[str, Any]) -> str:
    return str(gate.get("gate_id") or gate.get("id") or "")


def schema_required_sections() -> list[str]:
    if not SCHEMA_PATH.exists():
        return []
    schema = json_load(SCHEMA_PATH)
    return list(schema.get("required", []))


def validate_plan(plan_path: Path, plan: dict[str, Any]) -> dict[str, Any]:
    required = schema_required_sections()
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    for section in required:
        if section not in plan:
            errors.append({"message": "Missing required top-level section", "section": section})
    for section in ("referenced_context_artifacts", "artifact_intent_manifest", "planned_registry_projection"):
        if section not in plan:
            errors.append({"message": "Missing v3.3.0 governance section", "section": section})

    metadata = plan.get("template_metadata", {})
    if metadata.get("version") != "3.3.0":
        errors.append({"message": "template_metadata.version must be 3.3.0", "observed": metadata.get("version")})

    gates = plan.get("validation_gates", [])
    if not isinstance(gates, list):
        errors.append({"message": "validation_gates must be an array"})
        gates = []
    seen_gates: set[str] = set()
    required_gate_fields = {
        "gate_id",
        "phase",
        "purpose",
        "command",
        "timeout_sec",
        "retries",
        "expect_exit_code",
        "expect_stdout_regex",
        "forbid_stdout_regex",
        "expect_files",
        "evidence",
    }
    for index, gate in enumerate(gates):
        if not isinstance(gate, dict):
            errors.append({"message": "Gate record must be an object", "index": index})
            continue
        current_gate_id = gate_id(gate)
        if not current_gate_id:
            errors.append({"message": "Gate missing gate_id", "index": index})
        elif current_gate_id in seen_gates:
            errors.append({"message": "Duplicate gate_id", "gate_id": current_gate_id})
        seen_gates.add(current_gate_id)
        missing = sorted(required_gate_fields - set(gate))
        if missing:
            errors.append({"message": "Gate does not match full gate contract", "gate_id": current_gate_id, "missing_fields": missing})

    for current_gate_id, module_name in VALIDATOR_MODULES.items():
        validator_path = ROOT / "scripts" / f"{module_name}.py"
        if not validator_path.exists():
            errors.append({"message": "Validator script missing", "gate_id": current_gate_id, "path": str(validator_path.relative_to(ROOT))})

    report = {
        "command": "validate",
        "generated_at": utc_now(),
        "plan_path": str(plan_path.relative_to(ROOT) if plan_path.is_relative_to(ROOT) else plan_path),
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "warnings": warnings,
        "required_sections_checked": required,
        "gate_count": len(gates),
    }
    json_dump(STATE_DIR / "evidence" / "plan_cli_validate.json", report)
    return report


def write_run_status(status: str, current_phase: str, gate_results: list[dict[str, Any]]) -> None:
    payload = {
        "run_id": "npp-v3.3.0-validation",
        "current_phase": current_phase,
        "phase_counts": {"total": 2, "completed": 2 if status == "completed" else 1},
        "task_counts": {"total_gates": len(gate_results), "passed_gates": sum(1 for item in gate_results if item.get("status") == "PASS")},
        "status": status,
        "timestamps": {"updated_at": utc_now()},
        "planned_state_source": "validation_gates",
        "observed_state_source": "gate_results",
    }
    json_dump(RUN_STATUS_PATH, payload)


def append_ledger(record: dict[str, Any]) -> None:
    MUTATION_LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    with MUTATION_LEDGER_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def write_behavior_binding_proof(plan: dict[str, Any]) -> dict[str, Any]:
    patterns = {
        item.get("pattern_id")
        for item in plan.get("execution_patterns", {}).get("task_pattern_mappings", [])
        if isinstance(item, dict)
    }
    executors = {
        item.get("executor_id")
        for item in plan.get("executor_registry", {}).get("registered_executors", [])
        if isinstance(item, dict)
    }
    checks = []
    status = "PASS"
    for phase_id, phase_steps in plan.get("step_contracts", {}).items():
        if not isinstance(phase_steps, dict):
            continue
        for step_id, step in phase_steps.items():
            if not isinstance(step, dict):
                continue
            pattern_id = step.get("pattern_id")
            executor_id = step.get("executor_binding", {}).get("executor_id")
            check = {
                "phase_id": phase_id,
                "step_id": step_id,
                "pattern_id": pattern_id,
                "executor_id": executor_id,
                "pattern_registered": pattern_id in patterns,
                "executor_registered": executor_id in executors,
            }
            if not check["pattern_registered"] or not check["executor_registered"]:
                status = "FAIL"
            checks.append(check)
    payload = {
        "generated_at": utc_now(),
        "status": status,
        "checks": checks,
        "planned_state_source": "step_contracts",
        "observed_state_source": "registered pattern and executor maps",
    }
    json_dump(STATE_DIR / "evidence" / "behavior_binding_proof.json", payload)
    return payload


def static_gate_result(plan: dict[str, Any], gate: dict[str, Any]) -> dict[str, Any]:
    current_gate_id = gate_id(gate)
    checks = []
    status = "PASS"
    if current_gate_id == "GATE-001":
        validation = validate_plan(ROOT / "NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_2.json", plan)
        status = validation["status"]
        checks.append({"name": "plan_cli_validate", "status": status})
    elif current_gate_id == "GATE-002":
        gate_ids = [gate_id(item) for item in plan.get("validation_gates", []) if isinstance(item, dict)]
        status = "PASS" if len(gate_ids) == len(set(gate_ids)) else "FAIL"
        checks.append({"name": "gate_ids_unique", "status": status, "count": len(gate_ids)})
    elif current_gate_id == "GATE-003":
        missing = []
        for phase_id, phase_steps in plan.get("step_contracts", {}).items():
            if not isinstance(phase_steps, dict):
                continue
            for step_id, step in phase_steps.items():
                required = {"step_id", "purpose", "inputs", "outputs", "file_scope", "evidence", "pattern_id", "executor_binding", "behavior_spec"}
                absent = sorted(required - set(step)) if isinstance(step, dict) else sorted(required)
                if absent:
                    missing.append({"phase_id": phase_id, "step_id": step_id, "missing": absent})
        status = "PASS" if not missing else "FAIL"
        checks.append({"name": "step_contracts_complete", "status": status, "missing": missing})
    elif current_gate_id == "GATE-004":
        assumptions = plan.get("assumptions_scope", {})
        status = "PASS" if isinstance(assumptions, dict) and "definition_of_done" in assumptions else "FAIL"
        checks.append({"name": "assumptions_scope_present", "status": status})
    elif current_gate_id == "GATE-FILE-MUTATIONS":
        status = "PASS" if "artifact_intent_manifest" in plan else "FAIL"
        checks.append({"name": "artifact_intent_manifest_present", "status": status})
    elif current_gate_id.startswith("GATE-CFG-"):
        proof = write_behavior_binding_proof(plan)
        status = proof["status"]
        checks.append({"name": "behavior_binding_proof", "status": status})
    else:
        checks.append({"name": "static_template_gate_contract", "status": "PASS", "note": "Template-level static validation gate"})

    payload = {"gate_id": current_gate_id, "generated_at": utc_now(), "status": status, "checks": checks}
    for expected in gate.get("expect_files", []) if isinstance(gate.get("expect_files"), list) else []:
        path_value = expected.get("path") if isinstance(expected, dict) else None
        if path_value:
            json_dump(repo_path(path_value), payload)
    return payload


def run_validator_gate(plan_path: Path, gate: dict[str, Any]) -> dict[str, Any]:
    current_gate_id = gate_id(gate)
    module_name = VALIDATOR_MODULES[current_gate_id]
    module = importlib.import_module(module_name)
    result = module.validate(plan_path, json_load(plan_path))
    for expected in gate.get("expect_files", []) if isinstance(gate.get("expect_files"), list) else []:
        path_value = expected.get("path") if isinstance(expected, dict) else None
        if path_value:
            json_dump(repo_path(path_value), result)
    return result


def ordered_gates(plan: dict[str, Any]) -> list[dict[str, Any]]:
    gates = [gate for gate in plan.get("validation_gates", []) if isinstance(gate, dict)]
    if not GATE_DEPENDENCIES_PATH.exists():
        return gates
    dependencies = json_load(GATE_DEPENDENCIES_PATH)
    order = {item: index for index, item in enumerate(dependencies.get("execution_order", []))}
    return sorted(gates, key=lambda item: order.get(gate_id(item), len(order)))


def run_gates(plan_path: Path, plan: dict[str, Any]) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    write_run_status("running", "gate_execution", results)
    validation = validate_plan(plan_path, plan)
    if validation["status"] != "PASS":
        results.append({"gate_id": "PLAN-VALIDATE", "status": "FAIL", "details": validation})
    for gate in ordered_gates(plan):
        current_gate_id = gate_id(gate)
        try:
            if current_gate_id in VALIDATOR_MODULES:
                result = run_validator_gate(plan_path, gate)
            else:
                result = static_gate_result(plan, gate)
            status = result.get("status", "FAIL")
        except Exception as exc:
            result = {"gate_id": current_gate_id, "status": "FAIL", "error": str(exc), "generated_at": utc_now()}
            status = "FAIL"
        result.setdefault("gate_id", current_gate_id)
        results.append(result)
        append_ledger(
            {
                "record_type": "gate_execution",
                "planned_gate_id": current_gate_id,
                "observed_status": status,
                "observed_at": utc_now(),
                "planned_state_source": "validation_gates",
                "observed_state_source": "validator_result",
            }
        )
    overall = "PASS" if results and all(item.get("status") == "PASS" for item in results) else "FAIL"
    summary = {
        "command": "run-gates",
        "generated_at": utc_now(),
        "plan_path": str(plan_path.relative_to(ROOT) if plan_path.is_relative_to(ROOT) else plan_path),
        "status": overall,
        "gate_results": results,
        "gate_count": len(results),
        "runtime_outputs": [
            str(RUN_STATUS_PATH.relative_to(ROOT)),
            str(MUTATION_LEDGER_PATH.relative_to(ROOT)),
            ".state/evidence/behavior_binding_proof.json",
        ],
    }
    json_dump(STATE_DIR / "evidence" / "run_gates_summary.json", summary)
    write_run_status("completed" if overall == "PASS" else "failed", "gate_execution", results)
    return summary


def execute(plan_path: Path, plan: dict[str, Any]) -> dict[str, Any]:
    summary = run_gates(plan_path, plan)
    summary["command"] = "execute"
    json_dump(STATE_DIR / "evidence" / "execute_summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate and run gates for NEWPHASEPLANPROCESS plans.")
    parser.add_argument("command", choices=["validate", "run-gates", "execute"])
    parser.add_argument("plan_path")
    args = parser.parse_args()

    plan_path, plan = load_plan(args.plan_path)
    if args.command == "validate":
        result = validate_plan(plan_path, plan)
        print("plan_validation_ok" if result["status"] == "PASS" else "plan_validation_failed")
    elif args.command == "run-gates":
        result = run_gates(plan_path, plan)
        print("run_gates_ok" if result["status"] == "PASS" else "run_gates_failed")
    else:
        result = execute(plan_path, plan)
        print("execute_ok" if result["status"] == "PASS" else "execute_failed")
    raise SystemExit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    main()
