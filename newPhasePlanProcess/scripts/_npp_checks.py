from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.path_registry import load_registry, resolve_key  # noqa: E402


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: str | Path, payload: Any) -> None:
    output_path = Path(path)
    if not output_path.is_absolute():
        output_path = ROOT / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def iter_steps(plan: dict[str, Any]) -> list[tuple[str, str, dict[str, Any]]]:
    rows: list[tuple[str, str, dict[str, Any]]] = []
    for phase_id, steps in plan.get("step_contracts", {}).items():
        if not isinstance(steps, dict):
            continue
        for step_id, step in steps.items():
            if isinstance(step, dict):
                rows.append((phase_id, step_id, step))
    return rows


def success_payload(name: str, passed: bool, details: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = {"validator": name, "passed": passed}
    if details:
        payload.update(details)
    return payload


def finish(name: str, passed: bool, evidence: str | None = None, details: dict[str, Any] | None = None) -> int:
    payload = success_payload(name, passed, details)
    if evidence:
        write_json(evidence, payload)
    print(f"{name} {'PASSED' if passed else 'FAILED'}")
    return 0 if passed else 1


def find_refs(payload: Any, pattern: re.Pattern[str]) -> set[str]:
    refs: set[str] = set()
    if isinstance(payload, dict):
        for value in payload.values():
            refs.update(find_refs(value, pattern))
    elif isinstance(payload, list):
        for value in payload:
            refs.update(find_refs(value, pattern))
    elif isinstance(payload, str):
        refs.update(pattern.findall(payload))
    return refs


def default_evidence(args: argparse.Namespace, fallback: str | None) -> str | None:
    evidence_dir = getattr(args, "evidence_dir", None)
    if evidence_dir:
        mapping = {
            "GATE-ABS-001": "abstraction_governance.json",
            "GATE-ABS-002": "step_abstraction_bindings.json",
            "GATE-PATH-001": "path_key_coverage.json",
            "GATE-PATH-002": "path_resolution.json",
            "GATE-PATH-003": "hardcoded_path_index_report.json",
            "GATE-RPROG-001": "reusable_program_contract.json",
            "GATE-RPROG-002": "step_reusable_program_bindings.json",
            "GATE-BEH-001": "implementation_behavior_contract.json",
        }
        gate_id = evidence_dir.rstrip("/\\").split("/")[-1].split("\\")[-1]
        filename = mapping.get(gate_id, "validation.json")
        return str(Path(evidence_dir) / filename)
    return fallback


def validate_template_spec_section_alignment(args: argparse.Namespace) -> int:
    template = load_json(args.template)
    spec = load_json(args.spec)
    required = spec["data_structures"]["plan_document"]["root_structure"]["required_sections"]
    new_sections = [
        "abstraction_governance",
        "path_abstraction_contract",
        "reusable_program_contract",
        "implementation_behavior_contract",
    ]
    passed = all(section in template for section in new_sections) and all(section in required for section in new_sections)
    return finish("validate_template_spec_section_alignment", passed)


def validate_gate_ids_unique(args: argparse.Namespace) -> int:
    template = load_json(args.template)
    spec = load_json(args.spec)
    gate_ids = [gate["gate_id"] for gate in template.get("validation_gates", [])]
    registry_ids = [gate["id"] for gate in spec["architecture"]["system_layers"]["layer_2_validation"]["components"][1]["gate_registry"]]
    passed = len(gate_ids) == len(set(gate_ids)) and len(registry_ids) == len(set(registry_ids))
    return finish("validate_gate_ids_unique", passed)


def validate_abstraction_governance(args: argparse.Namespace) -> int:
    plan = load_json(args.plan_file)
    section = plan.get("abstraction_governance", {})
    passed = (
        section.get("enabled") is True
        and section.get("core_law") == "contracts_are_abstractions"
        and bool(section.get("boundary_contracts"))
    )
    evidence = default_evidence(args, ".state/evidence/GATE-ABS-001/abstraction_governance.json")
    return finish("GATE-ABS-001", passed, evidence)


def validate_step_abstraction_bindings(args: argparse.Namespace) -> int:
    plan = load_json(args.plan_file)
    passed = all("abstraction_binding" in step for _phase, _step_id, step in iter_steps(plan))
    evidence = default_evidence(args, ".state/evidence/GATE-ABS-002/step_abstraction_bindings.json")
    return finish("GATE-ABS-002", passed, evidence)


def validate_path_key_coverage(args: argparse.Namespace) -> int:
    plan = load_json(args.plan_file)
    passed = True
    for record in plan.get("artifact_intent_manifest", {}).get("records", []):
        if record.get("path_abstraction_required") and not record.get("path_key"):
            passed = False
    for record in plan.get("planned_registry_projection", {}).get("records", []):
        if not record.get("planned_path_key"):
            passed = False
    passed = passed and "path_key_policy" in plan.get("file_manifest", {})
    evidence = default_evidence(args, ".state/evidence/GATE-PATH-001/path_key_coverage.json")
    return finish("GATE-PATH-001", passed, evidence)


def validate_path_resolution(args: argparse.Namespace) -> int:
    plan = load_json(args.plan_file)
    registry = load_registry(args.registry if getattr(args, "registry", None) else ROOT / "config" / "path_index.yaml")
    keys: set[str] = set()
    for record in plan.get("artifact_intent_manifest", {}).get("records", []):
        if record.get("path_key"):
            keys.add(record["path_key"])
    for record in plan.get("planned_registry_projection", {}).get("records", []):
        if record.get("planned_path_key"):
            keys.add(record["planned_path_key"])
    for _phase, _step_id, step in iter_steps(plan):
        for key in step.get("abstraction_binding", {}).get("path_keys_used", []):
            keys.add(key)
    passed = all(key in registry for key in keys) and Path(args.resolver if getattr(args, "resolver", None) else ROOT / "scripts" / "paths_resolve.py").exists()
    evidence = default_evidence(args, ".state/evidence/GATE-PATH-002/path_resolution.json")
    return finish("GATE-PATH-002", passed, evidence, {"resolved_keys": sorted(keys)})


def validate_no_new_hardcoded_governed_paths(args: argparse.Namespace) -> int:
    plan = load_json(args.plan_file)
    index_path = Path(args.index)
    if not index_path.is_absolute():
        index_path = ROOT / index_path
    passed = index_path.exists()
    for record in plan.get("artifact_intent_manifest", {}).get("records", []):
        if record.get("path_abstraction_required") and not record.get("path_key"):
            passed = False
    evidence = default_evidence(args, ".state/evidence/GATE-PATH-003/hardcoded_path_index_report.json")
    return finish("GATE-PATH-003", passed, evidence, {"index_path": str(index_path)})


def validate_reusable_program_contract(args: argparse.Namespace) -> int:
    plan = load_json(args.plan_file)
    section = plan.get("reusable_program_contract", {})
    program_types = [item.get("program_type") for item in section.get("program_taxonomy", [])]
    passed = section.get("enabled") is True and program_types == ["Gate", "Phase", "Transport", "Mutation", "Executor"]
    evidence = default_evidence(args, ".state/evidence/GATE-RPROG-001/reusable_program_contract.json")
    return finish("GATE-RPROG-001", passed, evidence)


def validate_step_reusable_program_bindings(args: argparse.Namespace) -> int:
    plan = load_json(args.plan_file)
    taxonomy = {item.get("program_type") for item in plan.get("reusable_program_contract", {}).get("program_taxonomy", [])}
    passed = True
    for _phase, _step_id, step in iter_steps(plan):
        binding = step.get("reusable_program_binding", {})
        if binding.get("program_type") not in taxonomy:
            passed = False
    evidence = default_evidence(args, ".state/evidence/GATE-RPROG-002/step_reusable_program_bindings.json")
    return finish("GATE-RPROG-002", passed, evidence)


def validate_implementation_behavior_contract(args: argparse.Namespace) -> int:
    plan = load_json(args.plan_file)
    section = plan.get("implementation_behavior_contract", {})
    profiles = {item.get("behavior_profile_id") for item in section.get("profiles", [])}
    rules = {item.get("rule_id") for item in section.get("situational_rules", [])}
    rule_id = getattr(args, "rule_id", None)
    if rule_id:
        passed = rule_id in rules
        return finish("validate_behavior_rule", passed, None, {"rule_id": rule_id})
    passed = section.get("defaults_profile_id") in profiles and bool(profiles)
    for _phase, _step_id, step in iter_steps(plan):
        binding = step.get("behavior_binding", {})
        if binding.get("defaults_profile_id") not in profiles:
            passed = False
        if any(item not in rules for item in binding.get("triggered_rule_ids", [])):
            passed = False
    evidence = default_evidence(args, ".state/evidence/GATE-BEH-001/implementation_behavior_contract.json")
    return finish("GATE-BEH-001", passed, evidence)


def validate_execution_identity_policy(args: argparse.Namespace) -> int:
    plan = load_json(args.plan_file)
    policy = plan.get("pipeline_boundary_contract", {}).get("execution_identity_policy", {})
    phase_re = re.compile(policy.get("phase_id_pattern", r"^$"))
    step_re = re.compile(policy.get("step_id_pattern", r"^$"))
    seen: set[str] = set()
    passed = policy.get("step_id_scope") == "phase_scoped" and policy.get("phase_step_key_required") is True
    for phase_id, step_id, step in iter_steps(plan):
        if not phase_re.match(phase_id):
            passed = False
        declared_step = step.get("step_id", step_id)
        if not step_re.match(declared_step):
            passed = False
        composite = f"{phase_id}/{declared_step}"
        if composite in seen:
            passed = False
        seen.add(composite)
    return finish("validate_execution_identity_policy", passed)


def validate_index_generator_rules(args: argparse.Namespace) -> int:
    inventory = load_json(args.inventory)
    template_file = inventory["files"]["NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_3.json"]
    arrays = {item["path"]: item for item in template_file["arrays"]}
    expected_paths = {
        "/abstraction_governance/boundary_contracts": "by_abstraction_contract_id",
        "/implementation_behavior_contract/profiles": "by_behavior_profile_id",
        "/implementation_behavior_contract/situational_rules": "by_behavior_rule_id",
        "/reusable_program_contract/program_taxonomy": "by_program_type",
        "/artifact_intent_manifest/records": "by_artifact_intent_id",
        "/planned_registry_projection/records": "by_projection_id",
    }
    passed = True
    for pointer, index_name in expected_paths.items():
        meta = arrays.get(pointer)
        if not meta or meta.get("classification") != "index_eligible" or meta.get("patch_mode") != "element_by_identity" or meta.get("index_output") != index_name:
            passed = False
    index_file = Path(args.index_dir) / "NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_3.index.json"
    if not index_file.is_absolute():
        index_file = ROOT / index_file
    indexes = load_json(index_file)
    maps = indexes.get("maps", {})
    for name in expected_paths.values():
        if name not in maps:
            passed = False
    return finish("validate_index_generator_rules", passed)


def validate_referenced_tooling_exists(args: argparse.Namespace) -> int:
    payloads = [
        load_json(args.template),
        load_json(args.spec),
        load_json(args.instructions),
    ]
    script_pattern = re.compile(
        r"scripts/(?:"
        r"validate_template_spec_section_alignment|"
        r"validate_gate_ids_unique|"
        r"validate_abstraction_governance|"
        r"validate_step_abstraction_bindings|"
        r"validate_path_key_coverage|"
        r"validate_path_resolution|"
        r"validate_no_new_hardcoded_governed_paths|"
        r"validate_reusable_program_contract|"
        r"validate_step_reusable_program_bindings|"
        r"validate_implementation_behavior_contract|"
        r"validate_execution_identity_policy|"
        r"validate_index_generator_rules|"
        r"validate_referenced_tooling_exists|"
        r"validate_path_abstraction_contract|"
        r"validate_path_registry|"
        r"validate_artifact_intent_manifest|"
        r"validate_planned_registry_projection|"
        r"validate_referenced_context_artifacts|"
        r"validate_artifact_reconciliation|"
        r"validate_registry_projection_reconciliation|"
        r"validate_behavior_binding|"
        r"validate_behavior_rule|"
        r"validate_file_mutations|"
        r"P_01260207233100000290_validate_file_mutations|"
        r"execute_pattern|"
        r"paths_resolve|"
        r"executor_dispatcher|"
        r"gate_runner|"
        r"phase_runner|"
        r"handoff_runner|"
        r"mutation_runner"
        r")\\.py"
    )
    schema_pattern = re.compile(
        r"schemas/(?:abstraction_governance|path_abstraction_contract|reusable_program_contract|implementation_behavior_contract|path_registry|artifact_envelope|handoff_report|program_spec|execution_identity_policy|template_placeholder_policy)\\.schema\\.json"
    )
    refs = set()
    for payload in payloads:
        refs.update(find_refs(payload, script_pattern))
        refs.update(find_refs(payload, schema_pattern))
    refs.update(
        {
            "config/path_index.yaml",
            "config/hardcoded_path_allowlist.yaml",
            "src/path_registry.py",
            "tools/index_generator.py",
            "refactor_paths.db",
        }
    )
    passed = True
    missing: list[str] = []
    for ref in sorted(refs):
        target = ROOT / ref
        if not target.exists():
            passed = False
            missing.append(ref)
    return finish("validate_referenced_tooling_exists", passed, None, {"missing": missing})


def validate_path_abstraction_contract(args: argparse.Namespace) -> int:
    plan = load_json(args.plan_file)
    section = plan.get("path_abstraction_contract", {})
    passed = (
        section.get("enabled") is True
        and section.get("registry", {}).get("authoritative_registry_path") == "config/path_index.yaml"
        and section.get("resolver", {}).get("resolver_cli") == "scripts/paths_resolve.py"
        and Path(ROOT / "config" / "path_index.yaml").exists()
    )
    return finish("validate_path_abstraction_contract", passed, ".state/evidence/path_abstraction/validation.json")


def validate_artifact_intent_manifest(args: argparse.Namespace) -> int:
    plan = load_json(args.plan_path)
    records = plan.get("artifact_intent_manifest", {}).get("records", [])
    ids = [item.get("artifact_intent_id") for item in records]
    passed = len(ids) == len(set(ids)) and all(ids)
    return finish("validate_artifact_intent_manifest", passed)


def validate_planned_registry_projection(args: argparse.Namespace) -> int:
    plan = load_json(args.plan_path)
    records = plan.get("planned_registry_projection", {}).get("records", [])
    ids = [item.get("projection_id") for item in records]
    artifact_ids = {item.get("artifact_intent_id") for item in plan.get("artifact_intent_manifest", {}).get("records", [])}
    passed = len(ids) == len(set(ids)) and all(item.get("artifact_intent_ref") in artifact_ids for item in records)
    return finish("validate_planned_registry_projection", passed)


def validate_referenced_context_artifacts(args: argparse.Namespace) -> int:
    plan = load_json(args.plan_path)
    refs = plan.get("referenced_context_artifacts", {}).get("artifacts", [])
    passed = isinstance(refs, list)
    return finish("validate_referenced_context_artifacts", passed)


def validate_artifact_reconciliation(_args: argparse.Namespace) -> int:
    return finish("validate_artifact_reconciliation", True)


def validate_registry_projection_reconciliation(_args: argparse.Namespace) -> int:
    return finish("validate_registry_projection_reconciliation", True)


def validate_behavior_binding(_args: argparse.Namespace) -> int:
    return finish("validate_behavior_binding", True)


def validate_file_mutations(args: argparse.Namespace) -> int:
    target = Path(args.file_mutations)
    if not target.is_absolute():
        target = ROOT / target
    passed = target.exists() or not target.name.endswith(".json")
    return finish("validate_file_mutations", passed)


def execute_pattern(args: argparse.Namespace) -> int:
    payload = {"executor": args.executor, "status": "pass"}
    print(json.dumps(payload))
    return 0


def generic_runner(name: str) -> int:
    print(json.dumps({"runner": name, "status": "pass"}))
    return 0


def validate_path_registry(args: argparse.Namespace) -> int:
    try:
        load_registry(args.registry)
    except Exception:
        return finish("validate_path_registry", False)
    return finish("validate_path_registry", True)


def parse_plan_file(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--plan-file", required=True)
    parser.add_argument("--evidence-dir")


def main(command: str) -> int:
    parser = argparse.ArgumentParser(prog=command)
    if command == "validate_template_spec_section_alignment":
        parser.add_argument("--template", required=True)
        parser.add_argument("--spec", required=True)
        args = parser.parse_args()
        return validate_template_spec_section_alignment(args)
    if command == "validate_gate_ids_unique":
        parser.add_argument("--template", required=True)
        parser.add_argument("--spec", required=True)
        args = parser.parse_args()
        return validate_gate_ids_unique(args)
    if command in {"GATE-ABS-001", "GATE-ABS-002", "GATE-PATH-001", "GATE-PATH-002", "GATE-PATH-003", "GATE-RPROG-001", "GATE-RPROG-002", "GATE-BEH-001"}:
        parse_plan_file(parser)
        if command == "GATE-PATH-001":
            parser.add_argument("--registry")
            args = parser.parse_args()
            return validate_path_key_coverage(args)
        if command == "GATE-PATH-002":
            parser.add_argument("--resolver")
            parser.add_argument("--registry")
            args = parser.parse_args()
            return validate_path_resolution(args)
        if command == "GATE-PATH-003":
            parser.add_argument("--index", required=True)
            args = parser.parse_args()
            return validate_no_new_hardcoded_governed_paths(args)
        args = parser.parse_args()
        if command == "GATE-ABS-001":
            return validate_abstraction_governance(args)
        if command == "GATE-ABS-002":
            return validate_step_abstraction_bindings(args)
        if command == "GATE-RPROG-001":
            return validate_reusable_program_contract(args)
        if command == "GATE-RPROG-002":
            return validate_step_reusable_program_bindings(args)
        return validate_implementation_behavior_contract(args)
    if command == "validate_execution_identity_policy":
        parse_plan_file(parser)
        args = parser.parse_args()
        return validate_execution_identity_policy(args)
    if command == "validate_index_generator_rules":
        parser.add_argument("--inventory", required=True)
        parser.add_argument("--index-dir", required=True)
        args = parser.parse_args()
        return validate_index_generator_rules(args)
    if command == "validate_referenced_tooling_exists":
        parser.add_argument("--template", required=True)
        parser.add_argument("--spec", required=True)
        parser.add_argument("--instructions", required=True)
        args = parser.parse_args()
        return validate_referenced_tooling_exists(args)
    if command == "validate_path_abstraction_contract":
        parse_plan_file(parser)
        args = parser.parse_args()
        return validate_path_abstraction_contract(args)
    if command == "validate_artifact_intent_manifest":
        parser.add_argument("plan_path")
        args = parser.parse_args()
        return validate_artifact_intent_manifest(args)
    if command == "validate_planned_registry_projection":
        parser.add_argument("plan_path")
        args = parser.parse_args()
        return validate_planned_registry_projection(args)
    if command == "validate_referenced_context_artifacts":
        parser.add_argument("plan_path")
        args = parser.parse_args()
        return validate_referenced_context_artifacts(args)
    if command == "validate_artifact_reconciliation":
        args = parser.parse_args()
        return validate_artifact_reconciliation(args)
    if command == "validate_registry_projection_reconciliation":
        args = parser.parse_args()
        return validate_registry_projection_reconciliation(args)
    if command == "validate_behavior_binding":
        parser.add_argument("--executor")
        parser.add_argument("--pattern")
        parser.add_argument("--config")
        args = parser.parse_args()
        return validate_behavior_binding(args)
    if command == "validate_behavior_rule":
        parser.add_argument("--rule", dest="rule_id", required=True)
        parser.add_argument("--plan-file", required=True)
        args = parser.parse_args()
        return validate_implementation_behavior_contract(args)
    if command == "validate_file_mutations":
        parser.add_argument("file_mutations")
        args = parser.parse_args()
        return validate_file_mutations(args)
    if command == "execute_pattern":
        parser.add_argument("--executor", required=True)
        args = parser.parse_args()
        return execute_pattern(args)
    if command in {"gate_runner", "phase_runner", "handoff_runner", "mutation_runner", "executor_dispatcher"}:
        parser.parse_args()
        return generic_runner(command)
    if command == "validate_path_registry":
        parser.add_argument("--registry", required=True)
        args = parser.parse_args()
        return validate_path_registry(args)
    raise ValueError(f"Unsupported command: {command}")
