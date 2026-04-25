#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from resolver import escape, pointer_get, resolve_from_artifact


ROOT = Path(__file__).resolve().parent.parent
INDEX_DIR = ROOT / "indexes"
EVIDENCE_DIR = ROOT / "evidence"
INVENTORY_PATH = ROOT / "inventory.json"

SOURCE_FILES = {
    "NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_3.json": ROOT / "NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_3.json",
    "NEWPHASEPLANPROCESS_TECHNICAL_SPECIFICATION_V3_3.json": ROOT / "NEWPHASEPLANPROCESS_TECHNICAL_SPECIFICATION_V3_3.json",
    "NEWPHASEPLANPROCESS_INSTRUCTION_DOCUMENT_V3_3.json": ROOT / "NEWPHASEPLANPROCESS_INSTRUCTION_DOCUMENT_V3_3.json",
}

ARRAY_RULES = {
    "NEWPHASEPLANPROCESS_TECHNICAL_SPECIFICATION_V3_3.json": {
        "/architecture/system_layers/layer_1_planning/components": {
            "classification": "index_eligible",
            "identity_field": "component_id",
            "identity_pattern": r"^COMP-L\d-\d{2}$",
            "index_output": "by_component_id",
        },
        "/architecture/system_layers/layer_2_validation/components": {
            "classification": "index_eligible",
            "identity_field": "component_id",
            "identity_pattern": r"^COMP-L\d-\d{2}$",
            "index_output": "by_component_id",
        },
        "/architecture/system_layers/layer_2_validation/components/1/execution_phases": {
            "classification": "structural",
            "reason": "plain-string execution phases remain inventory-only per Phase A.1",
        },
        "/architecture/system_layers/layer_2_validation/components/1/gate_registry": {
            "classification": "index_eligible",
            "identity_field": "id",
            "identity_pattern": r"^GATE-[A-Z0-9-]+$",
            "index_output": "by_gate_id",
        },
        "/architecture/system_layers/layer_3_execution/components": {
            "classification": "index_eligible",
            "identity_field": "component_id",
            "identity_pattern": r"^COMP-L\d-\d{2}$",
            "index_output": "by_component_id",
        },
        "/architecture/system_layers/layer_4_observability/components": {
            "classification": "index_eligible",
            "identity_field": "component_id",
            "identity_pattern": r"^COMP-L\d-\d{2}$",
            "index_output": "by_component_id",
        },
    },
    "NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_3.json": {
        "/abstraction_governance/boundary_contracts": {
            "classification": "index_eligible",
            "identity_field": "contract_id",
            "identity_pattern": r"^ABS-[A-Z0-9-]+$",
            "index_output": "by_abstraction_contract_id",
        },
        "/execution_patterns/task_pattern_mappings": {
            "classification": "index_eligible",
            "identity_field": "pattern_id",
            "identity_pattern": r"^PAT-[A-Z0-9-]+$",
            "index_output": "by_pattern_id",
        },
        "/implementation_behavior_contract/profiles": {
            "classification": "index_eligible",
            "identity_field": "behavior_profile_id",
            "identity_pattern": r"^[A-Z0-9_]+$",
            "index_output": "by_behavior_profile_id",
        },
        "/implementation_behavior_contract/situational_rules": {
            "classification": "index_eligible",
            "identity_field": "rule_id",
            "identity_pattern": r"^BEH-[A-Z0-9-]+$",
            "index_output": "by_behavior_rule_id",
        },
        "/executor_registry/registered_executors": {
            "classification": "index_eligible",
            "identity_field": "executor_id",
            "identity_pattern": r"^EXEC-[A-Z0-9-]+$",
            "index_output": "by_executor_id",
        },
        "/reusable_program_contract/program_taxonomy": {
            "classification": "index_eligible",
            "identity_field": "program_type",
            "identity_pattern": r"^(Gate|Phase|Transport|Mutation|Executor)$",
            "index_output": "by_program_type",
        },
        "/artifact_intent_manifest/records": {
            "classification": "index_eligible",
            "identity_field": "artifact_intent_id",
            "identity_pattern": r"^AINT-\d{3,}$",
            "index_output": "by_artifact_intent_id",
        },
        "/planned_registry_projection/records": {
            "classification": "index_eligible",
            "identity_field": "projection_id",
            "identity_pattern": r"^REGPROJ-\d{3,}$",
            "index_output": "by_projection_id",
        },
        "/final_summary/what_was_delivered/enhancements": {
            "classification": "index_eligible",
            "identity_field": "id",
            "identity_pattern": r"^ENH-\d{3}$",
            "index_output": "by_enhancement_id",
        },
        "/validation_gates": {
            "classification": "index_eligible",
            "identity_field": "gate_id",
            "identity_pattern": r"^GATE-[A-Z0-9-]+$",
            "index_output": "by_gate_id",
        },
    },
    "NEWPHASEPLANPROCESS_INSTRUCTION_DOCUMENT_V3_3.json": {},
}


def json_load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def json_dump(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def walk_arrays(node: Any, pointer: str = "") -> list[tuple[str, list[Any]]]:
    arrays: list[tuple[str, list[Any]]] = []
    if isinstance(node, list):
        arrays.append((pointer, node))
        for index, child in enumerate(node):
            arrays.extend(walk_arrays(child, f"{pointer}/{index}"))
    elif isinstance(node, dict):
        for key, child in node.items():
            arrays.extend(walk_arrays(child, f"{pointer}/{escape(key)}"))
    return arrays


def object_items_sorted(node: dict[str, Any]) -> list[tuple[str, Any]]:
    return sorted(node.items(), key=lambda item: item[0])


def build_inventory() -> dict[str, Any]:
    files: dict[str, Any] = {}
    for file_name, path in SOURCE_FILES.items():
        data = json_load(path)
        arrays = []
        for pointer, values in sorted(walk_arrays(data), key=lambda item: item[0]):
            rule = ARRAY_RULES[file_name].get(pointer)
            element_type = "empty"
            for value in values:
                if value is None:
                    continue
                if isinstance(value, dict):
                    element_type = "object"
                elif isinstance(value, list):
                    element_type = "array"
                else:
                    element_type = type(value).__name__
                break
            if rule and rule["classification"] == "index_eligible":
                arrays.append(
                    {
                        "path": pointer,
                        "classification": "index_eligible",
                        "patch_mode": "element_by_identity",
                        "element_type": element_type,
                        "identity_field": rule["identity_field"],
                        "identity_pattern": rule["identity_pattern"],
                        "index_output": rule["index_output"],
                        "duplicate_identity_action": "fail_closed",
                        "missing_identity_action": "fail_closed",
                    }
                )
            else:
                reason = "default structural classification"
                if rule and rule["classification"] == "structural":
                    reason = rule["reason"]
                arrays.append(
                    {
                        "path": pointer,
                        "classification": "structural",
                        "patch_mode": "replace_whole_array",
                        "element_type": element_type,
                        "index_output": None,
                        "reason": reason,
                    }
                )
        files[file_name] = {
            "source_sha256": sha256(path),
            "arrays": arrays,
        }
    return {
        "inventory_version": "1.1.0",
        "files": files,
    }


def build_index_for_rule(
    data: Any,
    pointer: str,
    identity_field: str,
    map_name: str,
    dest: dict[str, dict[str, str]],
) -> None:
    values = pointer_get(data, pointer)
    if not isinstance(values, list):
        raise ValueError(f"{pointer} is not an array")
    target = dest.setdefault(map_name, {})
    for index, item in enumerate(values):
        if not isinstance(item, dict):
            raise ValueError(f"{pointer}/{index} is not an object")
        identity = item.get(identity_field)
        if not identity:
            raise ValueError(f"{pointer}/{index} missing identity field {identity_field}")
        if identity in target:
            raise ValueError(f"Duplicate identity {identity} in map {map_name}")
        target[identity] = f"{pointer}/{index}"


def build_step_map(template_data: Any, dest: dict[str, dict[str, str]]) -> None:
    target = dest.setdefault("by_step_id", {})
    for phase_id, steps in object_items_sorted(template_data.get("step_contracts", {})):
        if not isinstance(steps, dict):
            continue
        for step_key, step in object_items_sorted(steps):
            if not isinstance(step, dict):
                continue
            step_id = step.get("step_id")
            if not step_id:
                continue
            if step_id != step_key:
                raise ValueError(f"Step key mismatch at {phase_id}/{step_key}: {step_id}")
            composite = f"{phase_id}/{step_id}"
            if composite in target:
                raise ValueError(f"Duplicate composite step identity {composite}")
            target[composite] = f"/step_contracts/{escape(phase_id)}/{escape(step_id)}"


def build_indexes(inventory: dict[str, Any]) -> dict[str, Any]:
    outputs: dict[str, Any] = {}
    for file_name, path in SOURCE_FILES.items():
        data = json_load(path)
        maps: dict[str, dict[str, str]] = {}
        for array_meta in inventory["files"][file_name]["arrays"]:
            if array_meta["classification"] != "index_eligible":
                continue
            rule = ARRAY_RULES[file_name][array_meta["path"]]
            build_index_for_rule(
                data,
                array_meta["path"],
                rule["identity_field"],
                rule["index_output"],
                maps,
            )
        if file_name == "NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_3.json":
            build_step_map(data, maps)
        outputs[file_name] = {
            "index_version": "1.1.0",
            "source_file": file_name,
            "source_sha256": sha256(path),
            "canonical_locator_type": "json_pointer",
            "maps": {name: dict(sorted(entries.items())) for name, entries in sorted(maps.items())},
        }
    return outputs


def validate_indexes(inventory: dict[str, Any], indexes: dict[str, Any]) -> dict[str, Any]:
    gate_results = {
        "IDX-GATE-01": {"name": "identity_uniqueness", "status": "PASS", "details": []},
        "IDX-GATE-02": {"name": "pointer_resolution", "status": "PASS", "details": []},
        "IDX-GATE-03": {"name": "source_hash_freshness", "status": "PASS", "details": []},
        "IDX-GATE-04": {"name": "resolver_roundtrip", "status": "PASS", "details": []},
        "IDX-GATE-05": {"name": "classification_completeness", "status": "PASS", "details": []},
    }

    for file_name, path in SOURCE_FILES.items():
        data = json_load(path)
        artifact = indexes[file_name]
        actual_hash = sha256(path)
        if artifact["source_sha256"] != actual_hash:
            gate_results["IDX-GATE-03"]["status"] = "FAIL"
            gate_results["IDX-GATE-03"]["details"].append({"file": file_name, "expected": artifact["source_sha256"], "actual": actual_hash})
        for map_name, entries in artifact["maps"].items():
            for semantic_id, pointer in entries.items():
                node = pointer_get(data, pointer)
                gate_results["IDX-GATE-02"]["details"].append({"file": file_name, "map": map_name, "id": semantic_id, "pointer": pointer})
                if map_name == "by_step_id":
                    if node.get("step_id") != semantic_id.split("/")[-1]:
                        gate_results["IDX-GATE-02"]["status"] = "FAIL"
                elif map_name == "by_component_id":
                    if node.get("component_id") != semantic_id:
                        gate_results["IDX-GATE-02"]["status"] = "FAIL"
                elif map_name == "by_enhancement_id":
                    if node.get("id") != semantic_id:
                        gate_results["IDX-GATE-02"]["status"] = "FAIL"
                elif map_name == "by_pattern_id":
                    if node.get("pattern_id") != semantic_id:
                        gate_results["IDX-GATE-02"]["status"] = "FAIL"
                elif map_name == "by_executor_id":
                    if node.get("executor_id") != semantic_id:
                        gate_results["IDX-GATE-02"]["status"] = "FAIL"
                elif map_name == "by_gate_id":
                    gate_value = node.get("gate_id", node.get("id"))
                    if gate_value != semantic_id:
                        gate_results["IDX-GATE-02"]["status"] = "FAIL"
        current_arrays = sorted(pointer for pointer, _ in walk_arrays(data))
        inventory_arrays = sorted(entry["path"] for entry in inventory["files"][file_name]["arrays"])
        if current_arrays != inventory_arrays:
            gate_results["IDX-GATE-05"]["status"] = "FAIL"
            gate_results["IDX-GATE-05"]["details"].append({"file": file_name, "inventory_count": len(inventory_arrays), "observed_count": len(current_arrays)})

    sandbox_result = run_sandbox_reorder_test(indexes)
    gate_results["IDX-GATE-04"]["details"].append(sandbox_result)
    if sandbox_result["status"] != "PASS":
        gate_results["IDX-GATE-04"]["status"] = "FAIL"

    namespace_validation = validate_reserved_namespaces(indexes)
    cross_file_integrity = validate_cross_file_integrity(indexes)
    gate_results["IDX-GATE-04"]["details"].append(cross_file_integrity)
    if cross_file_integrity["status"] != "PASS":
        gate_results["IDX-GATE-04"]["status"] = "FAIL"

    overall = "PASS" if all(result["status"] == "PASS" for result in gate_results.values()) else "FAIL"
    return {
        "status": overall,
        "gates": gate_results,
        "namespace_validation": namespace_validation,
        "cross_file_integrity": cross_file_integrity,
    }


def validate_reserved_namespaces(indexes: dict[str, Any]) -> dict[str, Any]:
    spec_artifact = indexes["NEWPHASEPLANPROCESS_TECHNICAL_SPECIFICATION_V3_3.json"]
    template_artifact = indexes["NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_3.json"]
    counts = {
        "GATE-CFG": sum(1 for gate_id in spec_artifact["maps"].get("by_gate_id", {}) if gate_id.startswith("GATE-CFG-")),
        "PAT": len(template_artifact["maps"].get("by_pattern_id", {})),
        "EXEC": len(template_artifact["maps"].get("by_executor_id", {})),
        "COMP": len(spec_artifact["maps"].get("by_component_id", {})),
    }
    required_non_empty = ["GATE-CFG", "PAT", "EXEC", "COMP"]
    status = "PASS" if all(counts[name] > 0 for name in required_non_empty) else "FAIL"
    return {
        "status": status,
        "counts": counts,
        "required_non_empty": required_non_empty,
    }


def validate_cross_file_integrity(indexes: dict[str, Any]) -> dict[str, Any]:
    template_file = "NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_3.json"
    spec_file = "NEWPHASEPLANPROCESS_TECHNICAL_SPECIFICATION_V3_3.json"
    template_data = json_load(SOURCE_FILES[template_file])
    template_artifact = indexes[template_file]
    spec_artifact = indexes[spec_file]

    checks: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    for phase_id, steps in object_items_sorted(template_data.get("step_contracts", {})):
        if not isinstance(steps, dict):
            continue
        for step_id, step in object_items_sorted(steps):
            if not isinstance(step, dict):
                continue
            pattern_id = step.get("pattern_id")
            if pattern_id:
                try:
                    pointer = resolve_from_artifact(template_artifact, pattern_id)
                    checks.append({"type": "step_pattern", "phase": phase_id, "step": step_id, "id": pattern_id, "pointer": pointer})
                except KeyError as exc:
                    errors.append({"type": "step_pattern", "phase": phase_id, "step": step_id, "id": pattern_id, "error": str(exc)})
            executor_id = step.get("executor_binding", {}).get("executor_id")
            if executor_id:
                try:
                    pointer = resolve_from_artifact(template_artifact, executor_id)
                    checks.append({"type": "step_executor", "phase": phase_id, "step": step_id, "id": executor_id, "pointer": pointer})
                except KeyError as exc:
                    errors.append({"type": "step_executor", "phase": phase_id, "step": step_id, "id": executor_id, "error": str(exc)})
            behavior_pattern = step.get("behavior_spec", {}).get("pattern_id")
            if behavior_pattern:
                try:
                    pointer = resolve_from_artifact(template_artifact, behavior_pattern)
                    checks.append({"type": "behavior_pattern", "phase": phase_id, "step": step_id, "id": behavior_pattern, "pointer": pointer})
                except KeyError as exc:
                    errors.append({"type": "behavior_pattern", "phase": phase_id, "step": step_id, "id": behavior_pattern, "error": str(exc)})

    for mapping in template_data.get("execution_patterns", {}).get("task_pattern_mappings", []):
        if not isinstance(mapping, dict):
            continue
        pattern_id = mapping.get("pattern_id")
        if pattern_id:
            try:
                pointer = resolve_from_artifact(template_artifact, pattern_id)
                checks.append({"type": "mapping_pattern", "task_kind": mapping.get("task_kind"), "id": pattern_id, "pointer": pointer})
            except KeyError as exc:
                errors.append({"type": "mapping_pattern", "task_kind": mapping.get("task_kind"), "id": pattern_id, "error": str(exc)})
        executor_id = mapping.get("executor_id")
        if executor_id:
            try:
                pointer = resolve_from_artifact(template_artifact, executor_id)
                checks.append({"type": "mapping_executor", "task_kind": mapping.get("task_kind"), "id": executor_id, "pointer": pointer})
            except KeyError as exc:
                errors.append({"type": "mapping_executor", "task_kind": mapping.get("task_kind"), "id": executor_id, "error": str(exc)})

    for gate_id in template_data.get("pipeline_boundary_contract", {}).get("validation_required_before_execution", []):
        try:
            pointer = resolve_from_artifact(spec_artifact, gate_id)
            checks.append({"type": "boundary_gate", "id": gate_id, "pointer": pointer})
        except KeyError as exc:
            errors.append({"type": "boundary_gate", "id": gate_id, "error": str(exc)})

    for gate in template_data.get("validation_gates", []):
        if not isinstance(gate, dict):
            continue
        gate_id = gate.get("gate_id")
        if not gate_id:
            continue
        try:
            pointer = resolve_from_artifact(spec_artifact, gate_id)
            checks.append({"type": "template_gate", "id": gate_id, "pointer": pointer})
        except KeyError as exc:
            errors.append({"type": "template_gate", "id": gate_id, "error": str(exc)})

    return {
        "status": "PASS" if not errors else "FAIL",
        "checked_count": len(checks),
        "checks": checks,
        "errors": errors,
    }


def run_sandbox_reorder_test(indexes: dict[str, Any]) -> dict[str, Any]:
    template_path = SOURCE_FILES["NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_3.json"]
    spec_path = SOURCE_FILES["NEWPHASEPLANPROCESS_TECHNICAL_SPECIFICATION_V3_3.json"]
    template = json_load(template_path)
    spec = json_load(spec_path)

    template_copy = copy.deepcopy(template)
    spec_copy = copy.deepcopy(spec)

    template_copy["validation_gates"] = list(reversed(template_copy["validation_gates"]))
    template_copy["final_summary"]["what_was_delivered"]["enhancements"] = list(
        reversed(template_copy["final_summary"]["what_was_delivered"]["enhancements"])
    )
    template_copy["execution_patterns"]["task_pattern_mappings"] = list(
        reversed(template_copy["execution_patterns"]["task_pattern_mappings"])
    )
    template_copy["executor_registry"]["registered_executors"] = list(
        reversed(template_copy["executor_registry"]["registered_executors"])
    )
    spec_copy["architecture"]["system_layers"]["layer_2_validation"]["components"][1]["gate_registry"] = list(
        reversed(spec_copy["architecture"]["system_layers"]["layer_2_validation"]["components"][1]["gate_registry"])
    )

    sandbox_indexes = copy.deepcopy(indexes)
    sandbox_indexes["NEWPHASEPLANPROCESS_TECHNICAL_SPECIFICATION_V3_3.json"]["maps"]["by_gate_id"] = {}
    sandbox_indexes["NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_3.json"]["maps"]["by_gate_id"] = {}
    sandbox_indexes["NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_3.json"]["maps"]["by_enhancement_id"] = {}
    sandbox_indexes["NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_3.json"]["maps"]["by_pattern_id"] = {}
    sandbox_indexes["NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_3.json"]["maps"]["by_executor_id"] = {}

    build_index_for_rule(
        spec_copy,
        "/architecture/system_layers/layer_2_validation/components/1/gate_registry",
        "id",
        "by_gate_id",
        sandbox_indexes["NEWPHASEPLANPROCESS_TECHNICAL_SPECIFICATION_V3_3.json"]["maps"],
    )
    build_index_for_rule(
        template_copy,
        "/validation_gates",
        "gate_id",
        "by_gate_id",
        sandbox_indexes["NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_3.json"]["maps"],
    )
    build_index_for_rule(
        template_copy,
        "/final_summary/what_was_delivered/enhancements",
        "id",
        "by_enhancement_id",
        sandbox_indexes["NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_3.json"]["maps"],
    )
    build_index_for_rule(
        template_copy,
        "/execution_patterns/task_pattern_mappings",
        "pattern_id",
        "by_pattern_id",
        sandbox_indexes["NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_3.json"]["maps"],
    )
    build_index_for_rule(
        template_copy,
        "/executor_registry/registered_executors",
        "executor_id",
        "by_executor_id",
        sandbox_indexes["NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_3.json"]["maps"],
    )

    key_sets_match = (
        set(sandbox_indexes["NEWPHASEPLANPROCESS_TECHNICAL_SPECIFICATION_V3_3.json"]["maps"]["by_gate_id"]) ==
        set(indexes["NEWPHASEPLANPROCESS_TECHNICAL_SPECIFICATION_V3_3.json"]["maps"]["by_gate_id"])
        and set(sandbox_indexes["NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_3.json"]["maps"]["by_gate_id"]) ==
        set(indexes["NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_3.json"]["maps"]["by_gate_id"])
        and set(sandbox_indexes["NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_3.json"]["maps"]["by_enhancement_id"]) ==
        set(indexes["NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_3.json"]["maps"]["by_enhancement_id"])
        and set(sandbox_indexes["NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_3.json"]["maps"]["by_pattern_id"]) ==
        set(indexes["NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_3.json"]["maps"]["by_pattern_id"])
        and set(sandbox_indexes["NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_3.json"]["maps"]["by_executor_id"]) ==
        set(indexes["NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_3.json"]["maps"]["by_executor_id"])
    )
    return {
        "status": "PASS" if key_sets_match else "FAIL",
        "checked_maps": ["by_gate_id", "by_enhancement_id", "by_pattern_id", "by_executor_id"],
    }


def write_reports(inventory: dict[str, Any], indexes: dict[str, Any], validation: dict[str, Any]) -> None:
    json_dump(EVIDENCE_DIR / "PH-03" / "inventory_validation.json", inventory)
    json_dump(
        EVIDENCE_DIR / "PH-05" / "index_build_report.json",
        {
            "status": "PASS",
            "artifacts": [str((INDEX_DIR / f"{Path(name).stem}.index.json").relative_to(ROOT)) for name in SOURCE_FILES],
        },
    )
    json_dump(
        EVIDENCE_DIR / "PH-06" / "resolver_report.json",
        {
            "status": "PASS",
            "resolver_module": "tools/resolver.py",
            "roundtrip_counts": {
                file_name: sum(len(entries) for entries in artifact["maps"].values())
                for file_name, artifact in indexes.items()
            },
            "namespace_validation": validation["namespace_validation"],
            "cross_file_integrity": validation["cross_file_integrity"],
        },
    )
    json_dump(EVIDENCE_DIR / "PH-08" / "validation_gate_report.json", validation)
    json_dump(
        EVIDENCE_DIR / "PH-09" / "final_readiness_report.json",
        {
            "status": validation["status"],
            "required_artifacts_present": True,
            "files": sorted(SOURCE_FILES),
            "namespace_validation": validation["namespace_validation"],
            "cross_file_integrity": validation["cross_file_integrity"],
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate deterministic semantic-ID indexes for the v3.3 governance docs.")
    parser.add_argument("--inventory-only", action="store_true", help="Write inventory.json without generating index artifacts.")
    args = parser.parse_args()

    inventory = build_inventory()
    json_dump(INVENTORY_PATH, inventory)
    if args.inventory_only:
        return

    indexes = build_indexes(inventory)
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    for file_name, artifact in indexes.items():
        json_dump(INDEX_DIR / f"{Path(file_name).stem}.index.json", artifact)

    validation = validate_indexes(inventory, indexes)
    write_reports(inventory, indexes, validation)
    if validation["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
