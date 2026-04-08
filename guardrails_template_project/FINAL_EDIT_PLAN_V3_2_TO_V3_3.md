# Final Edit Plan: v3.2 → v3.3.0 — CDD + Pattern-First Enforcement

## Context

Two ChatGPT evaluation documents identify a shared gap in the v3.2 governance system:

- **ChatGPT-Configuration-Driven Development Evaluation.md** — Technical/granular. The template enforces governance of _work_ but not _architecture_. Patterns can point to ad hoc executor functions; `pattern_id` may be null; gaps can be "flagged" instead of resolved. Proposes exact JSON field additions for all three files.
- **ChatGPT-Template Feature Validation.md** — Architectural. The system is constraint-driven (validation + determinism) but not pattern-constrained. A "PATTERN LAYER" is missing above the template. Proposes `pattern_governance`, mandatory decision sequence, and pattern-creation contracts.

Both describe the same fix from complementary angles. **Source reconciliation rule:** Use File 1's field names and structures; use File 2's conceptual framing in `description`/`purpose` fields. File 2's `pattern_creation_contract`, `manual_exception_policy`, and `file_manifest_entry_extensions` are additive — include all. Critically: the six GATE-CFG-* gates satisfy File 2's three pattern-gate requirements — do NOT create a separate gate registry for them.

**Core constraint being added:** Every automatable task must execute through a registered executor consuming approved external spec/config. Behavioral variability lives in config/spec/parameters, not ad hoc code. If no pattern exists → create and validate it first, then implement. Null `pattern_id` on executable steps is forbidden.

---

## Pre-Edit: Define the Unified Model

Before touching any file, establish these canonical decisions:

1. **Three new top-level sections**: `pattern_governance`, `configuration_driven_development`, `executor_registry`.
2. **Structural consolidation**: `pattern_resolution_phase`, `pattern_creation_contract`, and `manual_exception_policy` all live **under `pattern_governance`** — not as separate peers.
3. **Step-level binding fields**: `implementation_mode`, `executor_binding`, `behavior_spec`, `allowed_extension_slots`, `bespoke_logic_allowed`, `behavior_binding_proof` extend existing steps. Existing `pattern_id` and `pattern_parameters` are kept and strengthened.
4. **Gate deduplication**: GATE-CFG-001–006 are the canonical pattern enforcement gates. They satisfy File 2's three pattern-gate requirements. No second registry.
5. **Executor primitive**: `executor_function` is replaced as the sole binding primitive everywhere. The replacement is: `executor_id` + `config_schema_file` + `parameter_schema_file` + `output_contract_ref`.
6. **Registry path**: Canonical value is `"registry/pattern_registry.yaml"` in all three files (replacing inconsistent `"PATTERN_INDEX.yaml"`).
7. **Version bump**: All three files move from `3.2.0` to `3.3.0`.

---

## Execution Order

```
1. AUTONOMOUS_DELIVERY_TEMPLATE  — concrete contract surface; defines fields first
2. TECHNICAL_SPECIFICATION       — spec prose written to match the template's structure
3. INSTRUCTION_DOCUMENT          — edited as plain text, re-serialized into JSON last
```

**JSON validation after every single edit:**
```bash
node -e "JSON.parse(require('fs').readFileSync('<file>','utf8')); console.log('OK')"
```

---

## STEP 1 — NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_2.json

### T-01 · Version metadata
**Key path:** `template_metadata`
- `version`: `"3.2.0"` → `"3.3.0"`
- `last_updated`: `"2026-04-04"` → `"2026-04-05"`
- `breaking_changes` array — append:
  - `"pattern_governance section added; pattern_resolution_phase, pattern_creation_contract, manual_exception_policy moved under it"`
  - `"configuration_driven_development section added with fail_closed enforcement"`
  - `"executor_registry section added; executor_function replaced by executor_id + config/schema/contract binding"`
  - `"execution_patterns: allow_null_pattern_id now false; require_validated_pattern_before_execution required"`
  - `"step_contracts: implementation_mode, executor_binding, behavior_spec, behavior_binding_proof, bespoke_logic_allowed mandatory for PATTERN_EXECUTION steps"`
  - `"GATE-CFG-001 through GATE-CFG-006 added to validation_gates and to pipeline_boundary_contract.validation_required_before_execution"`
  - `"anti_pattern_detection.triggers expanded with 8 new CDD-violation triggers"`
  - `"traceability extended with requirement_to_pattern, component_to_pattern, step_to_executor"`
  - `"planning_hierarchy module/component levels extended with implementation_style, engine_component_id, behavior_spec_artifacts"`
  - `"file_manifest entries extended with pattern provenance fields"`
  - `"registry/pattern_registry.yaml is now the canonical registry path (was PATTERN_INDEX.yaml)"`

---

### T-02 · Strengthen `critical_constraint.rules`
**Key path:** `critical_constraint.rules` (currently 3 items)
Append 5 items:
```json
"All AUTOMATABLE behavior MUST execute through a registered executor consuming an approved external specification or configuration artifact",
"Inline bespoke task logic is FORBIDDEN unless the step is explicitly marked PATTERN_CREATION or NOT_AUTOMATABLE",
"Executable steps MUST NOT have a null or blank pattern_id; null is permitted only for PATTERN_CREATION steps",
"If no approved pattern exists for a task kind, the plan MUST include a PATTERN_CREATION step that creates and validates the pattern before any implementation step begins",
"Behavioral variability MUST live in spec/config/parameters, not in ad hoc executor code or prompt-only instructions"
```

---

### T-03 · Add `configuration_driven_development` section
**Insertion point:** After `critical_constraint` closing `}`, before `usage_instructions`. New key becomes 3rd top-level key.
```json
"configuration_driven_development": {
  "enabled": true,
  "enforcement_mode": "fail_closed",
  "engine_spec_separation_required": true,
  "allowed_behavior_sources": [
    "pattern_parameters",
    "config_file",
    "spec_file",
    "schema_validated_defaults"
  ],
  "forbidden_behavior_sources": [
    "inline_ad_hoc_logic",
    "runtime_prompt_override",
    "manual_command_substitution",
    "unregistered_executor"
  ],
  "no_pattern_policy": {
    "implementation_blocked_until_pattern_validated": true,
    "required_action": "create_pattern_first"
  },
  "validator_command": "python scripts/validate_configuration_driven_development.py",
  "expect_exit_code": 0,
  "evidence": ".state/evidence/configuration_driven_development_validation.json"
}
```

---

### T-04 · Add `pattern_governance` section
**Insertion point:** After `configuration_driven_development`, before `usage_instructions`.

`pattern_resolution_phase`, `pattern_creation_contract`, and `manual_exception_policy` are **sub-fields of this section**, not separate top-level keys.

```json
"pattern_governance": {
  "mode": "PATTERN_FIRST_REQUIRED",
  "registry_path": "registry/pattern_registry.yaml",
  "unknown_pattern_policy": "CREATE_AND_VALIDATE_BEFORE_EXECUTION",
  "ad_hoc_execution_policy": "FORBIDDEN",
  "pre_execution_gate": "GATE-CFG-001",
  "pattern_resolution_phase": {
    "required": true,
    "steps": [
      "classify_task_archetype",
      "search_pattern_registry",
      "select_best_matching_pattern",
      "validate_pattern_applicability",
      "if_no_match_create_pattern_candidate",
      "validate_new_pattern",
      "register_pattern",
      "bind_task_to_pattern"
    ],
    "required_decision_outputs": [
      "pattern_resolution_decision",
      "existing_pattern_match",
      "new_pattern_required",
      "executor_family",
      "config_driven_feasibility"
    ]
  },
  "pattern_creation_contract": {
    "trigger": "NO_MATCHING_PATTERN_FOUND",
    "required_outputs": [
      "execution_pattern_file",
      "pattern_registry_entry",
      "pattern_validation_report",
      "pattern_applicability_statement"
    ],
    "must_complete_before": [
      "task_decomposition",
      "file_modification",
      "tool_execution"
    ]
  },
  "manual_exception_policy": {
    "allowed": false,
    "override_requires": [
      "human_approved_variance_id",
      "documented_reason",
      "temporary_expiration"
    ]
  },
  "required_step_fields": [
    "pattern_id",
    "pattern_status",
    "pattern_source",
    "pattern_justification",
    "pattern_validation_evidence"
  ],
  "enforcement_gates": [
    "GATE-CFG-001",
    "GATE-CFG-002",
    "GATE-CFG-003",
    "GATE-CFG-004",
    "GATE-CFG-005",
    "GATE-CFG-006"
  ]
}
```

---

### T-05 · Extend `task_analysis` pattern-resolution outputs
**Key path:** `task_analysis.objective` or the analysis output fields section (line ~98)
Add required output fields:
```json
"pattern_resolution_decision": "",
"existing_pattern_match": "",
"new_pattern_required": false,
"executor_family": "",
"config_driven_feasibility": ""
```

---

### T-06 · Extend file manifest entries with pattern provenance
**Key path:** `file_manifest` entry schema (line ~202)
Add to each file entry:
```json
"pattern_id": "",
"generated_from_pattern": false,
"pattern_role": ""
```
`pattern_role` enum: `pattern_artifact` | `pattern_output` | `manual_exception`

---

### T-07 · Harden `execution_patterns`
**Key path:** `execution_patterns` (line ~1575) — **replace** the entire object value.
- `pattern_registry_reference`: `"registry/pattern_registry.yaml"` (canonical)
- `required_for_task_kinds`: `true` (unchanged)
- Add: `"allow_null_pattern_id": false`
- Add: `"require_validated_pattern_before_execution": true`
- Add: `"require_executor_binding_per_pattern": true`
- Add: `"missing_pattern_action": "fail_closed_create_pattern_task"`
- Replace `required_pattern_components` — remove `executor_function`; use:
  ```json
  ["spec_file", "config_schema_file", "parameter_schema_file", "executor_id",
   "pattern_index_entry", "guardrails_block", "output_contract_ref", "golden_test_fixture"]
  ```
- Add: `"require_behavior_binding_proof": true`
- Add: `"guardrail_policy": { "bypass_allowed": false, "runtime_override_allowed": false, "missing_guardrails_action": "fail_closed" }`

---

### T-08 · Add `executor_registry` section
**Insertion point:** After `execution_patterns` closing `}`, before `mutation_model`.
```json
"executor_registry": {
  "registered_executors": [
    {
      "executor_id": "",
      "executor_entrypoint": "",
      "supported_pattern_ids": [],
      "supported_config_schema_versions": [],
      "determinism_requirements": [],
      "forbidden_capabilities": []
    }
  ],
  "validation_command": "python scripts/validate_executor_registry.py",
  "expect_exit_code": 0
}
```

---

### T-09 · Expand `pipeline_boundary_contract`
**Key path:** `pipeline_boundary_contract` (line ~1569) — add 4 fields:
```json
"allowed_execution_inputs": ["plan_json", "registered_pattern_spec", "schema_validated_config"],
"forbid_direct_source_mutation_without_pattern": true,
"forbid_unregistered_executor_invocation": true,
"forbid_runtime_behavior_override": true
```

---

### T-10 · Expand step contracts — executable step fields
**Key path:** `step_contracts.PH-00.STEP-001` and `PH-02.STEP-001` (line ~671 and ~912)
Append after `failure_logging` block:
```json
"implementation_mode": "PATTERN_EXECUTION",
"executor_binding": {
  "executor_id": "",
  "executor_version": "",
  "invocation_ref": ""
},
"behavior_spec": {
  "pattern_id": "",
  "pattern_version": "",
  "spec_file": "",
  "config_instance_file": "",
  "config_schema_file": "",
  "parameter_schema_file": ""
},
"behavior_binding_proof": {
  "command": "",
  "evidence": ""
},
"bespoke_logic_allowed": false,
"allowed_extension_slots": [],
"engine_invariants": []
```
`implementation_mode` enum: `PATTERN_EXECUTION` | `PATTERN_CREATION` | `NOT_AUTOMATABLE`

---

### T-11 · Expand `planning_hierarchy`
**Key path:** `planning_hierarchy` (line ~1563) — replace with structured version:
```json
{
  "system_level": {},
  "module_level": [{
    "module_id": "",
    "name": "",
    "purpose": "",
    "implementation_style": "",
    "engine_component_id": "",
    "behavior_spec_artifacts": [],
    "config_schema_artifacts": [],
    "executor_dependencies": [],
    "approved_extension_slots": []
  }],
  "component_level": [{
    "component_id": "",
    "module_id": "",
    "name": "",
    "implementation_style": "",
    "engine_component_id": "",
    "behavior_spec_artifacts": [],
    "config_schema_artifacts": []
  }],
  "execution_packet_level": []
}
```
`implementation_style` enum: `CONFIGURATION_DRIVEN` | `HYBRID` | `MANUAL_ONLY`

---

### T-12 · Expand `traceability`
**Key path:** `traceability` (line ~1613) — append 3 arrays:
```json
"requirement_to_pattern": [],
"component_to_pattern": [],
"step_to_executor": []
```

---

### T-13 · Add GATE-CFG-001–006 to `validation_gates`
**Key path:** `validation_gates` array — append after last existing gate entry.

For each gate, use the shared gate object structure already present in the file:

| gate_id | name | purpose | script |
|---|---|---|---|
| GATE-CFG-001 | Pattern Completeness | Every executable step has pattern_id, executor_id, spec_file, config_schema_file | `validate_pattern_completeness.py` |
| GATE-CFG-002 | Engine-Spec Separation | Behavior supplied by external spec/config, not step prose or custom commands | `validate_engine_spec_separation.py` |
| GATE-CFG-003 | No Ad Hoc Execution | Reject bespoke commands where a registered pattern exists for the task kind | `validate_no_adhoc_execution.py` |
| GATE-CFG-004 | Registered Executor Only | Reject executor_ids not present in executor_registry | `validate_executor_registration.py` |
| GATE-CFG-005 | Pattern-First Gap Resolution | Implementation steps cannot be scheduled before PATTERN_CREATION step when no pattern exists | `validate_pattern_first_gap_resolution.py` |
| GATE-CFG-006 | Behavior-Binding Proof | Executor + spec + config + expected outputs are mechanically linked | `validate_behavior_binding_proof.py` |

All 6 gates: `timeout_sec: 120`, `retries: 0`, `expect_exit_code: 0`, evidence under `.state/evidence/GATE-CFG-00N/`.

Also add all 6 gate IDs to `pipeline_boundary_contract.validation_required_before_execution`.

---

### T-14 · Expand `anti_pattern_detection.triggers`
**Key path:** `anti_pattern_detection.triggers` — append 8 strings:
```json
"patternless_execution",
"null_pattern_id_on_executable_step",
"unregistered_executor_invocation",
"inline_behavior_logic_outside_extension_slot",
"runtime_override_of_guardrailed_parameters",
"spec_without_engine_binding",
"executor_without_config_schema",
"freehand_script_created_where_pattern_exists"
```

---

### T-15 · Expand `ai_instructions.when_receiving_project_request`
Insert after the "Classify the project" element:
```json
"For every task kind: search the pattern registry for a matching approved pattern; if found, bind the task; if not found, create a PATTERN_CREATION step before any implementation step for that task kind; record pattern_resolution_decision in task_analysis before proceeding"
```

### T-16 · Expand `ai_instructions.do_not`
Append 7 strings:
```json
"Do not leave pattern_id blank on executable steps",
"Do not propose bespoke scripts where a registered pattern exists",
"Do not treat prose instructions as a substitute for config/schema",
"Do not start implementation before pattern creation/validation when no pattern exists",
"Do not bind behavior through runtime prompt overrides",
"Do not create or invoke unregistered executors",
"Do not place unique behavior in arbitrary code outside approved extension slots"
```

### T-17 · Expand `ai_instructions.remember`
Append 4 strings:
```json
"All automatable behavior = executor + spec/config + schema + evidence",
"Pattern gap => create pattern first, then implement",
"Executable step without validated pattern = invalid plan",
"Configuration is the behavior surface; code is the engine surface"
```

---

## STEP 2 — NEWPHASEPLANPROCESS_TECHNICAL_SPECIFICATION_V3_2.json

### S-01 · Add CDD design principle
**Key path:** `executive_summary.design_principles` — append:
> `"CONFIGURATION-DRIVEN DEVELOPMENT: Executable behavior must be determined by approved external specifications and configurations consumed by registered executors; ad hoc imperative task logic is prohibited by default"`

### S-02 · Add key capabilities
**Key path:** `executive_summary.key_capabilities` — append 5 items:
- `"Registered executor model with pattern-to-executor binding and config schema enforcement"`
- `"Configuration schema validation for every executable pattern instance"`
- `"Mandatory pattern creation before implementation when no matching pattern exists in registry"`
- `"Behavior-binding proof chain from requirement to pattern to config to executor to evidence"`
- `"Ad hoc implementation detection and rejection via GATE-CFG series"`

### S-03 · Add CDD Control Plane to Layer 2 architecture (line ~60)
**Key path:** `architecture.system_layers.layer_2_validation.components` — append component object:
```json
{
  "name": "CDD Control Plane",
  "purpose": "Enforce Configuration-Driven Development as an architectural constraint at plan-validation time",
  "sub_components": [
    { "name": "Pattern Registry", "role": "SSOT for approved execution patterns", "file": "registry/pattern_registry.yaml" },
    { "name": "Executor Registry", "role": "Binding between pattern IDs and executors", "file": "registry/executor_registry.yaml" },
    { "name": "Configuration Schema Validator", "role": "Validates config instances against pattern config schemas", "script": "scripts/validate_configuration_driven_development.py" },
    { "name": "Behavior Binding Validator", "role": "Verifies executor+spec+config+outputs are mechanically linked", "script": "scripts/validate_behavior_binding.py" },
    { "name": "Pattern Creation Workflow", "role": "Governs the mandatory procedure when no matching pattern exists", "trigger": "NO_MATCHING_PATTERN_FOUND" },
    { "name": "CDD Enforcement Gates", "role": "GATE-CFG-001 through GATE-CFG-006 — block execution until CDD constraints satisfied" }
  ]
}
```

### S-04 · Replace `executor_function` as sole binding primitive (line ~1208, ~1198, ~1248, ~1380)
Search for every occurrence of `executor_function` in the spec. Replace with the compound binding: `executor_id` + `config_schema_file` + `parameter_schema_file` + `output_contract_ref`. Update `required_pattern_components` descriptions to match T-07.

### S-05 · Add new `configuration_driven_development` top-level section (before `development_guidelines`, line ~2192)
Content mirrors the template's section (T-03) plus a spec-specific extended block:
- `definition`, `core_principle`, `mandatory_separation` (engine / behavior_surface / extension_surface)
- `glossary` (10 terms: executor, pattern, config_schema, parameter_schema, behavior_binding_proof, extension_slot, pattern_creation_step, executable_step, ad_hoc_logic, variance_path)
- `pattern_creation_lifecycle` — 8-step normative procedure:
  1. `detect_no_matching_pattern` → gap_detection_report
  2. `create_pattern_spec_file` → pattern_spec.yaml
  3. `create_config_schema_file` → config_schema.json
  4. `create_parameter_schema_file` → parameter_schema.json
  5. `register_executor_binding` → executor_registry_entry
  6. `create_golden_fixture` → golden_test_fixture.json
  7. `pass_pattern_validation_gates` (GATE-CFG-001, GATE-CFG-004, GATE-CFG-006)
  8. `implementation_steps_now_permitted` (precondition: all pattern gates passed)
- `validation_guarantees` (5 items)

### S-06 · Expand GATE-003 required_fields + update gate count (line ~684, ~969)
- Append to GATE-003 `required_fields`: `implementation_mode`, `executor_binding`, `behavior_spec`, `behavior_binding_proof`, `bespoke_logic_allowed`, `allowed_extension_slots`, `pattern_version` (total 13 → 21 fields)
- Update `critical_rule` string to reflect 21 fields
- Append 6 GATE-CFG-* entries to `gate_registry` (same content as T-13)
- Update `total_gates`: 19 → 25; `mandatory_gates`: 17 → 23

### S-07 · Expand `step_contract.required_fields` (line ~969)
Add 7 new field definition objects after `failure_logging`:
- `pattern_version` (string)
- `executor_binding` (object: executor_id, executor_version, invocation_ref)
- `behavior_spec` (object: pattern_id, pattern_version, spec_file, config_instance_file, config_schema_file, parameter_schema_file)
- `implementation_mode` (enum: PATTERN_EXECUTION | PATTERN_CREATION | NOT_AUTOMATABLE, with per-value rules)
- `behavior_binding_proof` (object: command, evidence)
- `bespoke_logic_allowed` (boolean, default: false)
- `allowed_extension_slots` (array with slot_id, description, runtime_limits)

### S-08 · Add `pattern_governance` section to spec (line ~684)
Mirror T-04 structure. Note that `pattern_resolution_phase`, `pattern_creation_contract`, and `manual_exception_policy` are sub-fields of `pattern_governance`, not separate sections.

### S-09 · Reframe `development_guidelines.adding_new_features.requirements` (line ~2192)
- Replace element 0 with: `"Feature must be expressible as: registered executor + validated spec/config artifact + evidence artifact + pass/fail condition"`
- Append: `"If no pattern exists, first create a pattern package (spec, config schema, parameter schema, executor binding, golden fixture) and validate it"`
- Append: `"No plan may schedule PATTERN_EXECUTION steps against a task kind lacking a validated registered pattern"`
- Append: `"Spec-only pattern definitions are invalid unless a corresponding executor binding exists in executor_registry"`

### S-10 · Add version history and migration guide
**Key path:** `appendix.version_history` — add `"v3.3.0"` entry (date: 2026-04-05) listing all changes.
**Key path:** `appendix.migration_guide` — add `"from_v3_2_to_v3_3"` entry:
> Breaking change: plans without GATE-CFG-001–006 will fail validation. Plans with null `pattern_id` on executable steps are invalid. `executor_function` references must be converted to `executor_id` + config/schema binding. Add `pattern_governance`, `configuration_driven_development`, and `executor_registry` top-level sections.

**Version update:** `document_metadata.version` → `"3.3.0"`; `executive_summary.system_name` → `"newPhasePlanProcess v3.3.0"`

---

## STEP 3 — NEWPHASEPLANPROCESS_INSTRUCTION_DOCUMENT_V3_2.json

### Serialization strategy
The entire instruction text lives as a single JSON string under `"content"`. **Do not edit JSON string escapes by hand.**

**Procedure:**
1. Extract the `content` string value to a plain `.md` temp file (strip surrounding JSON, unescape `\"` → `"` and `\n` → real newlines)
2. Make all text edits to the plain `.md` file
3. Re-serialize: escape all `"` → `\"`, replace real newlines with `\n`, wrap in the JSON envelope
4. Validate: `node -e "JSON.parse(require('fs').readFileSync('<file>','utf8')); console.log('OK')"`

---

### I-01 · Metadata
- `document_metadata.version`: `"3.2.0"` → `"3.3.0"`
- `document_metadata.title`: `"newPhasePlanProcess v3.2 Instructions..."` → `"...v3.3..."`

### I-02 · Overview paragraph
Append a v3.3 sentence after the last sentence (ends with `"mutation_ledger."`):
> Version 3.3 adds mandatory Configuration-Driven Development enforcement: `configuration_driven_development`, `pattern_governance`, and `executor_registry` top-level sections, and six GATE-CFG-* validation gates. The pattern-first execution model is now fully mandatory; null `pattern_id` on executable steps is forbidden; implementation may not begin until a validated pattern exists.

### I-03 · Add CDD general principle to `## General principles`
Insert new bullet **after** the `Pattern-first execution` bullet:
> **Configuration-driven development** — Every automatable behavior must be implemented through a registered executor consuming approved external specification and configuration artifacts. Keep behavioral variability in config/spec/parameters. Do not encode task-specific behavior in bespoke executor logic or prompt prose. If no pattern exists, create and validate one first — never substitute prose instructions for a missing pattern.

### I-04 · Strengthen `Pattern-first execution` bullet
Replace the soft closing sentence `"If no pattern exists, identify the gap so one can be added."` with:
> If no pattern exists, you MUST create a dedicated PATTERN_CREATION step before any implementation step. You MUST NOT leave `pattern_id` null for any executable step. You MUST NOT plan freehand implementation as a substitute for a missing pattern.

### I-05 · Add PATTERN-FIRST EXECUTION LAW block
Insert near the `NO_IMPLIED_BEHAVIOR` / general principles area, as a prominently titled block:
```
## PATTERN-FIRST EXECUTION LAW

Before any task planning or execution:
1. Classify the task into an archetype.
2. Search the approved pattern registry (registry/pattern_registry.yaml).
3. If a matching pattern exists, bind the task to it.
4. If no matching pattern exists, create a PATTERN_CREATION step first.
5. Validate and register the new pattern.
6. Only then plan or execute the task.

Ad hoc execution is forbidden.
No task may proceed with freeform implementation design.
If no valid pattern is bound to the task, abort planning.
Do not continue with a provisional design.
Do not substitute freeform reasoning for a missing pattern.
```

### I-06 · Update `task_analysis` instructions
After the sentence ending `"raise any NOT_AUTOMATABLE sections for human review."`, append:
> Also determine: whether an existing pattern covers the requested work; whether a PATTERN_CREATION step is required; what executor family should own the behavior; and what config/spec artifacts will control behavior. Record as mandatory outputs: `pattern_resolution_decision`, `existing_pattern_match`, `new_pattern_required`, `executor_family`, `config_driven_feasibility`. If `new_pattern_required` is true, the plan must include a PATTERN_CREATION step as its first non-intake step.

### I-07 · Update `planning_hierarchy` instructions — module/component level
Append to the Module-level sub-bullet:
> Also declare: `implementation_style` (CONFIGURATION_DRIVEN, HYBRID, or MANUAL_ONLY), `engine_component_id`, `behavior_spec_artifacts`, `config_schema_artifacts`, `executor_dependencies`, and `approved_extension_slots`. HYBRID components require manual review. MANUAL_ONLY requires justification.

### I-08 · Rewrite `execution_patterns` instructions
Replace the null-pattern sentence with:
> `pattern_id` is mandatory for every executable step. Null is permitted only for PATTERN_CREATION steps. When no pattern exists, create a pattern package first: the package must include `spec_file`, `config_schema_file`, `parameter_schema_file`, `executor_id`, `guardrails_block`, `output_contract_ref`, and `golden_test_fixture`. No implementation step may begin until this package is validated. Set `allow_null_pattern_id` to `false`, `require_validated_pattern_before_execution` to `true`, and `missing_pattern_action` to `fail_closed_create_pattern_task`.

### I-09 · Rewrite `step_contracts` instructions
Replace the soft pattern-reference sentence with:
> Every executable step MUST use a registered pattern. Every executable step MUST declare `executor_binding` (executor_id, executor_version, invocation_ref) and `behavior_spec` (spec_file, config_instance_file, config_schema_file, parameter_schema_file). Set `implementation_mode` to `PATTERN_EXECUTION` by default. Use `PATTERN_CREATION` only when the step exists solely to create a new pattern. Use `NOT_AUTOMATABLE` only for work that cannot be automated. Set `bespoke_logic_allowed` to `false` by default. Only declare free-form logic inside named `allowed_extension_slots` defined by the pattern, capped with `runtime_limits` and a `behavior_binding_proof`.

### I-10 · Expand `pipeline_boundary_contract` instructions
Append after existing closing sentence:
> Set `allowed_execution_inputs` to `["plan_json", "registered_pattern_spec", "schema_validated_config"]`. Set `forbid_direct_source_mutation_without_pattern`, `forbid_unregistered_executor_invocation`, and `forbid_runtime_behavior_override` all to `true`. Execution may consume only approved plan JSON, registered pattern specs, and schema-valid config instances.

### I-11 · Expand `validation_gates` instructions
Append:
> For every plan that includes executable work, include GATE-CFG-001 through GATE-CFG-006. Add all six to `pipeline_boundary_contract.validation_required_before_execution`. These gates are mandatory; they cannot be bypassed.

### I-12 · Expand AI prohibitions (`do_not`)
Add to the `do_not` list:
- Do not leave `pattern_id` blank on executable steps.
- Do not propose bespoke scripts where a registered pattern exists.
- Do not treat prose instructions as a substitute for config/schema.
- Do not start implementation before pattern creation/validation when no pattern exists.
- Do not bind behavior through runtime prompt overrides.
- Do not create or invoke unregistered executors.
- Do not place unique behavior in arbitrary code outside approved extension slots.

### I-13 · Expand AI mnemonics (`remember`)
Add to the `remember` list:
- All automatable behavior = executor + spec/config + schema + evidence.
- Pattern gap ⟹ create pattern first, then implement.
- Executable step without validated pattern = invalid plan.
- Configuration is the behavior surface; code is the engine surface.

### I-14 · Add required AI decision sequence
Insert a new block in the `ai_instructions` section titled "Required decision sequence for every task":
```
For every task, you must emit:
  task_archetype:               (the classified archetype)
  registry_search_result:       (what was found, or "NO_MATCH")
  selected_pattern_id:          (pattern ID, or "NONE — new pattern required")
  new_pattern_required:         true | false
  pattern_validation_result:    PASSED | PENDING (if new pattern)
  pattern_binding_complete:     true | false

If pattern_binding_complete is false, abort. Do not proceed.
```

---

## Post-Edit Consistency Pass

Run these checks after all three files are edited:

| Check | What to verify |
|---|---|
| JSON validity | All 3 files parse without error |
| Gate IDs | GATE-CFG-001–006 in both template `validation_gates` and spec `gate_registry`; no duplicate gate registry |
| Field parity | All spec `step_contract.required_fields` appear in template `step_contracts.PH-00.STEP-001` |
| Section parity | Every section named in instruction `content` exists as a top-level key in template |
| `do_not` / `remember` | Items in template `ai_instructions` arrays match instruction `content` lists |
| No `executor_function` | Zero remaining occurrences across all 3 files |
| No null `pattern_id` permission | No document says executable steps may have null/blank `pattern_id` |
| Version agreement | `"version": "3.3.0"` in all 3 files |
| Registry path | `"registry/pattern_registry.yaml"` everywhere; no remaining `"PATTERN_INDEX.yaml"` |
| `pattern_governance` structure | `pattern_resolution_phase`, `pattern_creation_contract`, `manual_exception_policy` are sub-fields of `pattern_governance`, not separate top-level keys |
| Gate counts | Spec `total_gates` = 25, `mandatory_gates` = 23 |
| `validation_required_before_execution` | All 6 GATE-CFG-* IDs present in this array in template |
