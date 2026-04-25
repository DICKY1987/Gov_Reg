#!/usr/bin/env python3
"""Generate RFC-6902 patch files for the 19 NPP v3.3 governance mechanisms.

Run from repo root:  python tools/build_patches.py
Outputs to:          patches/TEMPLATE_V3_3.patch.json
                     patches/SPEC_V3_3.patch.json
                     patches/INSTRUCTION_V3_3.patch.json

Re-running after patches have already been applied will raise RuntimeError
(idempotency guard) — this is intentional.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from resolver import pointer_get  # noqa: E402
from src.path_registry import load_registry  # noqa: E402

REGISTRY = load_registry(ROOT / "config" / "path_index.yaml")
PATCH_DIR = ROOT / "patches"
PATCH_DIR.mkdir(exist_ok=True)

TEMPLATE_FILE = ROOT / REGISTRY["docs.template"]
SPEC_FILE = ROOT / REGISTRY["docs.spec"]
INSTR_FILE = ROOT / REGISTRY["docs.instructions"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_doc(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except UnicodeDecodeError as exc:
        raise SystemExit(
            f"ERROR: {path.name} cannot be decoded as UTF-8.\n"
            "Re-save it as UTF-8 (without BOM) before running this script.\n"
            f"Detail: {exc}"
        ) from exc


def save_patch(name: str, ops: list) -> None:
    out = PATCH_DIR / name
    out.write_text(json.dumps(ops, indent=2) + "\n", encoding="utf-8")
    print(f"  wrote {out.relative_to(ROOT)}")


def assert_absent(doc: dict, key: str, doc_label: str) -> None:
    if key in doc:
        raise RuntimeError(
            f"Already patched: '{key}' exists in {doc_label}. "
            "Apply patches only once; restore from git if you need to re-run."
        )


# ---------------------------------------------------------------------------
# Mechanism definitions
# ---------------------------------------------------------------------------

# Primary document for each mechanism: "template" or "spec"
MECHANISMS: list[dict] = [
    {
        "key": "situational_determinism_contract",
        "gate_id": "GATE-DET-001",
        "primary": "template",
        "required_field": "resolution_order",
        "required_value": ["invariants", "phase_contracts", "step_contracts", "runtime_defaults"],
        "gate_name": "Situational Determinism Contract Valid",
        "gate_purpose": "situational_determinism_contract is present with fail-closed resolution_order.",
        "critical_rule": "Execution branching must follow a declared deterministic resolution order.",
        "failure_impact": "Ambiguous situational resolution produces non-reproducible execution.",
    },
    {
        "key": "governance_precedence",
        "gate_id": "GATE-GOV-001",
        "primary": "template",
        "required_field": "precedence_levels",
        "required_value": ["invariants", "step_contracts", "pattern_defaults", "template_defaults"],
        "gate_name": "Governance Precedence Valid",
        "gate_purpose": "governance_precedence declares a non-empty precedence_levels list.",
        "critical_rule": "Rule conflicts must be resolved by declared precedence, not implicit ordering.",
        "failure_impact": "Conflicting rules produce non-deterministic governance outcomes.",
    },
    {
        "key": "executor_routing_policy",
        "gate_id": "GATE-ROUT-001",
        "primary": "template",
        "required_field": "routing_rules",
        "required_value": [{"condition": "default", "executor": "EXEC-PYTHON-CLI-V1"}],
        "gate_name": "Executor Routing Policy Valid",
        "gate_purpose": "executor_routing_policy provides a non-empty routing_rules list.",
        "critical_rule": "Executor selection must follow a declared, auditable routing contract.",
        "failure_impact": "Arbitrary executor selection breaks traceability and reproducibility.",
    },
    {
        "key": "hermetic_step_contract",
        "gate_id": "GATE-HERM-001",
        "primary": "template",
        "required_field": "isolation_requirements",
        "required_value": ["declare_inputs", "declare_outputs", "pin_env_hash"],
        "gate_name": "Hermetic Step Contract Valid",
        "gate_purpose": "hermetic_step_contract declares isolation_requirements for reproducible execution.",
        "critical_rule": "Steps must declare all inputs, outputs, and environment pins.",
        "failure_impact": "Undeclared dependencies cause irreproducible step outputs.",
    },
    {
        "key": "decision_logging_policy",
        "gate_id": "GATE-LOG-001",
        "primary": "template",
        "required_field": "log_targets",
        "required_value": [".state/evidence/decisions/decision_log.jsonl"],
        "gate_name": "Decision Logging Policy Valid",
        "gate_purpose": "decision_logging_policy specifies at least one log_targets path.",
        "critical_rule": "Every consequential decision must be logged for audit and replay.",
        "failure_impact": "Missing decision logs prevent post-hoc audit and debugging.",
    },
    {
        "key": "durable_execution_contract",
        "gate_id": "GATE-DUR-001",
        "primary": "template",
        "required_field": "checkpoint_policy",
        "required_value": {"enabled": True, "checkpoint_dir": ".state/checkpoints"},
        "gate_name": "Durable Execution Contract Valid",
        "gate_purpose": "durable_execution_contract declares a checkpoint_policy for resumable runs.",
        "critical_rule": "Executions must be resumable from verified checkpoints after failure.",
        "failure_impact": "Non-durable execution loses progress and breaks audit continuity.",
    },
    {
        "key": "array_mutation_policy",
        "gate_id": "GATE-AMUT-001",
        "primary": "template",
        "required_field": "mutation_rules",
        "required_value": ["identity_key_only", "no_positional_index", "fail_closed_on_missing_id"],
        "gate_name": "Array Mutation Policy Valid",
        "gate_purpose": "array_mutation_policy bans positional array-index edits and requires identity-key mutations.",
        "critical_rule": "Array mutations must use stable identity keys, never positional indexes.",
        "failure_impact": "Positional array edits silently corrupt documents when order changes.",
    },
    {
        "key": "path_resolution_policy",
        "gate_id": "GATE-PRES-001",
        "primary": "template",
        "required_field": "resolver_ref",
        "required_value": "scripts/paths_resolve.py",
        "gate_name": "Path Resolution Policy Valid",
        "gate_purpose": "path_resolution_policy references a resolver script for governed path lookups.",
        "critical_rule": "Governed paths must be resolved through the declared resolver, never hardcoded.",
        "failure_impact": "Hardcoded paths break when the filesystem layout changes.",
    },
    {
        "key": "canonical_document_resolution",
        "gate_id": "GATE-CDOC-001",
        "primary": "template",
        "required_field": "canonical_files",
        "required_value": [
            "NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_3.json",
            "NEWPHASEPLANPROCESS_TECHNICAL_SPECIFICATION_V3_3.json",
            "NEWPHASEPLANPROCESS_INSTRUCTION_DOCUMENT_V3_3.json",
        ],
        "gate_name": "Canonical Document Resolution Valid",
        "gate_purpose": "canonical_document_resolution names the authoritative V3_3 files.",
        "critical_rule": "Only the declared canonical filenames are authoritative sources of truth.",
        "failure_impact": "Ambiguous document identity causes divergent governance state.",
    },
    {
        "key": "command_object_schema",
        "gate_id": "GATE-CMD-001",
        "primary": "template",
        "required_field": "required_fields",
        "required_value": ["shell", "cwd", "timeout_sec", "failure_mode", "evidence_path"],
        "gate_name": "Command Object Schema Valid",
        "gate_purpose": "command_object_schema declares required fields for executable commands.",
        "critical_rule": "All executable commands must declare shell, cwd, timeout, failure mode, and evidence path.",
        "failure_impact": "Under-specified commands cannot be deterministically replayed or audited.",
    },
    {
        "key": "pattern_resolution_policy",
        "gate_id": "GATE-PATT-001",
        "primary": "template",
        "required_field": "approved_patterns",
        "required_value": [
            {"condition": "has_approved_pattern", "action": "use_pattern"},
            {"condition": "no_pattern", "action": "fail_closed"},
        ],
        "gate_name": "Pattern Resolution Policy Valid",
        "gate_purpose": "pattern_resolution_policy provides approved_patterns with fail-closed fallback.",
        "critical_rule": "Tasks without an approved pattern must fail closed, not improvise execution.",
        "failure_impact": "Unapproved execution patterns bypass governance and audit controls.",
    },
    {
        "key": "fallback_policy",
        "gate_id": "GATE-FALL-001",
        "primary": "template",
        "required_field": "authorized_fallbacks",
        "required_value": ["FALLBACK-ESCALATE-001"],
        "gate_name": "Fallback Policy Valid",
        "gate_purpose": "fallback_policy declares at least one authorized fallback outcome.",
        "critical_rule": "Fallback behavior must be pre-authorized; ad-hoc fallbacks are forbidden.",
        "failure_impact": "Unauthorized fallbacks produce unauditable and potentially unsafe outcomes.",
    },
    {
        "key": "permission_tiers",
        "gate_id": "GATE-PERM-001",
        "primary": "template",
        "required_field": "tiers",
        "required_value": ["read_only", "safe_edit", "trusted", "destructive"],
        "gate_name": "Permission Tiers Valid",
        "gate_purpose": "permission_tiers declares the four capability tiers.",
        "critical_rule": "Operations must be classified into a declared permission tier before execution.",
        "failure_impact": "Unclassified operations bypass capability controls.",
    },
    {
        "key": "provenance_contract",
        "gate_id": "GATE-PROV-001",
        "primary": "template",
        "required_field": "required_provenance_fields",
        "required_value": ["producer", "sha256", "timestamp_utc"],
        "gate_name": "Provenance Contract Valid",
        "gate_purpose": "provenance_contract requires producer, sha256, and timestamp_utc on all outputs.",
        "critical_rule": "All artifact outputs must carry traceable provenance metadata.",
        "failure_impact": "Missing provenance breaks audit chains and prevents tamper detection.",
    },
    {
        "key": "change_archival_policy",
        "gate_id": "GATE-ARCH-001",
        "primary": "template",
        "required_field": "archive_targets",
        "required_value": [".state/evidence", "patches"],
        "gate_name": "Change Archival Policy Valid",
        "gate_purpose": "change_archival_policy lists directories that must be archived before destructive changes.",
        "critical_rule": "Evidence and patch artifacts must be archived before any destructive operation.",
        "failure_impact": "Unarchived evidence cannot support rollback or compliance review.",
    },
    {
        "key": "affected_execution_policy",
        "gate_id": "GATE-AFF-001",
        "primary": "template",
        "required_field": "dependency_graph_ref",
        "required_value": "scripts/gate_dependencies.json",
        "gate_name": "Affected Execution Policy Valid",
        "gate_purpose": "affected_execution_policy references a dependency graph for affected-only gate execution.",
        "critical_rule": "Selective gate execution must be driven by a declared dependency graph.",
        "failure_impact": "Arbitrary gate skipping misses required checks and invalidates the evidence chain.",
    },
    # Spec-primary mechanisms
    {
        "key": "policy_as_code",
        "gate_id": "GATE-POL-001",
        "primary": "spec",
        "required_field": "policy_engine",
        "required_value": "python",
        "gate_name": "Policy As Code Valid",
        "gate_purpose": "policy_as_code declares a machine-evaluable policy_engine and policy_dir.",
        "critical_rule": "Acceptance rules must be expressed as machine-evaluable policies over structured input.",
        "failure_impact": "Prose-only acceptance rules cannot be mechanically enforced.",
    },
    {
        "key": "github_enforcement_mapping",
        "gate_id": "GATE-GH-001",
        "primary": "spec",
        "required_field": "merge_protection",
        "required_value": "ruleset",
        "gate_name": "GitHub Enforcement Mapping Valid",
        "gate_purpose": "github_enforcement_mapping declares merge_protection binding NPP gates to branch rules.",
        "critical_rule": "NPP validation must be bound to GitHub merge protection before PR merges.",
        "failure_impact": "Unbound gates allow merges that bypass governance checks.",
    },
    {
        "key": "tool_context_generation",
        "gate_id": "GATE-CTX-001",
        "primary": "spec",
        "required_field": "output_files",
        "required_value": ["AGENTS.md", "CLAUDE.md"],
        "gate_name": "Tool Context Generation Valid",
        "gate_purpose": "tool_context_generation declares output_files generated from the NPP source of truth.",
        "critical_rule": "Tool context files must be generated from the NPP source of truth, not hand-authored.",
        "failure_impact": "Manually authored tool context diverges from the authoritative governance documents.",
    },
]

# Ordered list of gate IDs (preserves insertion order in both arrays)
GATE_IDS = [m["gate_id"] for m in MECHANISMS]


# ---------------------------------------------------------------------------
# Template patch
# ---------------------------------------------------------------------------

def build_template_patch(doc: dict) -> list:
    ops = []

    # 16 root-level mechanism keys (template-primary only)
    template_mechs = [m for m in MECHANISMS if m["primary"] == "template"]
    for m in template_mechs:
        assert_absent(doc, m["key"], TEMPLATE_FILE.name)
        stub = {
            "enabled": True,
            "enforcement_mode": "fail_closed",
            m["required_field"]: m["required_value"],
            "validator_ref": f"scripts/validate_{m['key']}.py",
        }
        ops.append({"op": "add", "path": f"/{m['key']}", "value": stub})

    # 19 validation_gates entries (one per mechanism, all IDs)
    pointer_get(doc, "/validation_gates")  # asserts parent exists
    for m in MECHANISMS:
        gate_stub = {
            "gate_id": m["gate_id"],
            "phase": "PH-03",
            "step_id": None,
            "purpose": m["gate_purpose"],
            "command": (
                f"python scripts/validate_{m['key']}.py "
                + ("--plan-file {plan_file}" if m["primary"] == "template" else "--spec {spec_file}")
                + f" --evidence-dir .state/evidence/{m['gate_id']}"
            ),
            "timeout_sec": 120,
            "retries": 0,
            "expect_exit_code": 0,
            "expect_stdout_regex": [f"{m['gate_id']} PASSED"],
            "forbid_stdout_regex": [f"{m['gate_id']} FAILED"],
            "expect_files": [
                {
                    "path": f".state/evidence/{m['gate_id']}/validation.json",
                    "content_regex": ['"passed": true'],
                }
            ],
            "evidence": f".state/evidence/{m['gate_id']}",
        }
        ops.append({"op": "add", "path": "/validation_gates/-", "value": gate_stub})

    return ops


# ---------------------------------------------------------------------------
# Spec patch
# ---------------------------------------------------------------------------

def build_spec_patch(doc: dict) -> list:
    ops = []

    # Test guard: the positional /1 index is baked into _npp_checks.py and
    # index_generator.py ARRAY_RULES. This guard makes the entire patch fail
    # if the components array order ever changes.
    ops.append({
        "op": "test",
        "path": "/architecture/system_layers/layer_2_validation/components/1/component_id",
        "value": "COMP-L2-02",
    })

    # Validate gate_registry parent exists
    gate_registry_ptr = (
        "/architecture/system_layers/layer_2_validation/components/1/gate_registry"
    )
    pointer_get(doc, gate_registry_ptr)

    # 19 spec gate_registry entries
    for m in MECHANISMS:
        spec_gate = {
            "id": m["gate_id"],
            "name": m["gate_name"],
            "script": f"validate_{m['key']}.py",
            "purpose": m["gate_purpose"],
            "critical_rule": m["critical_rule"],
            "failure_impact": m["failure_impact"],
        }
        ops.append({"op": "add", "path": f"{gate_registry_ptr}/-", "value": spec_gate})

    # mechanism_registry root key (dict, keyed by mechanism name)
    assert_absent(doc, "mechanism_registry", SPEC_FILE.name)
    mechanism_registry = {
        "registry_version": "1.0.0",
        "mechanisms": {
            m["key"]: {
                "owner_doc": m["primary"],
                "gate_id": m["gate_id"],
                "validator": f"validate_{m['key']}.py",
            }
            for m in MECHANISMS
        },
    }
    ops.append({"op": "add", "path": "/mechanism_registry", "value": mechanism_registry})

    # 3 spec-primary root keys
    spec_mechs = [m for m in MECHANISMS if m["primary"] == "spec"]
    for m in spec_mechs:
        assert_absent(doc, m["key"], SPEC_FILE.name)
        stub = {
            "enabled": True,
            "enforcement_mode": "fail_closed",
            m["required_field"]: m["required_value"],
            "validator_ref": f"scripts/validate_{m['key']}.py",
        }
        # policy_as_code also needs policy_dir
        if m["key"] == "policy_as_code":
            stub["policy_dir"] = "scripts"
        ops.append({"op": "add", "path": f"/{m['key']}", "value": stub})

    return ops


# ---------------------------------------------------------------------------
# Instruction doc patch
# ---------------------------------------------------------------------------

def build_instruction_patch(doc: dict) -> list:
    ops = []

    assert_absent(doc, "instruction_rule_index", INSTR_FILE.name)
    assert_absent(doc, "cross_document_pointers", INSTR_FILE.name)

    instruction_rule_index = {
        "version": "1.0.0",
        "mechanisms": {
            m["key"]: {
                "rule_text": m["critical_rule"],
                "gate_id": m["gate_id"],
                "owner_doc": m["primary"],
            }
            for m in MECHANISMS
        },
    }
    ops.append({"op": "add", "path": "/instruction_rule_index", "value": instruction_rule_index})

    cross_document_pointers = {
        "template_mechanism_root": "/<mechanism_key> (16 root keys)",
        "spec_mechanism_registry": "/mechanism_registry",
        "spec_gate_registry": (
            "/architecture/system_layers/layer_2_validation/components/1/gate_registry"
        ),
        "template_validation_gates": "/validation_gates",
        "instruction_rule_index": "/instruction_rule_index",
    }
    ops.append({"op": "add", "path": "/cross_document_pointers", "value": cross_document_pointers})

    return ops


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("Loading documents...")
    template_doc = load_doc(TEMPLATE_FILE)
    spec_doc = load_doc(SPEC_FILE)
    instr_doc = load_doc(INSTR_FILE)

    print("Building template patch...")
    template_ops = build_template_patch(template_doc)
    save_patch("TEMPLATE_V3_3.patch.json", template_ops)
    print(f"  {len(template_ops)} ops ({sum(1 for o in template_ops if o['op'] == 'add' and '/-' not in o['path'])} root-key adds, {sum(1 for o in template_ops if '/-' in o['path'])} gate appends)")

    print("Building spec patch...")
    spec_ops = build_spec_patch(spec_doc)
    save_patch("SPEC_V3_3.patch.json", spec_ops)
    print(f"  {len(spec_ops)} ops (1 test guard, {sum(1 for o in spec_ops if '/-' in o['path'])} gate appends, {sum(1 for o in spec_ops if o['op'] == 'add' and '/-' not in o['path'])} root-key adds)")

    print("Building instruction patch...")
    instr_ops = build_instruction_patch(instr_doc)
    save_patch("INSTRUCTION_V3_3.patch.json", instr_ops)
    print(f"  {len(instr_ops)} ops")

    print("Done. Patch files written to patches/")


if __name__ == "__main__":
    main()
