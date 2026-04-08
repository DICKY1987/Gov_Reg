# Plan: Edit Three `newPhasePlanProcess` JSON Files (v3.2 → v3.3)

## Context

The user is upgrading the `newPhasePlanProcess` framework from v3.2 to v3.3 to enforce Configuration-Driven Development (CDD), pattern-first execution, fail-closed guardrails, and deterministic semantic indexing. Six planning documents have been reconciled into a Resolved Authority Spec (16 rulings) plus four supplemental rulings (R-17..R-20). The three source files to be edited are:

- `C:\Users\richg\Gov_Reg\NEWPHASEPLANPROCESS_TECHNICAL_SPECIFICATION_V3_2.json`
- `C:\Users\richg\Gov_Reg\NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_2.json`
- `C:\Users\richg\Gov_Reg\NEWPHASEPLANPROCESS_INSTRUCTION_DOCUMENT_V3_2.json`

Pre-edit blockers (duplicate `GATE-008`, ordinal enhancement IDs, plain-string `execution_phases`, missing `component_id`) must be fixed first because no semantic-ID indexer can run while they exist. Governance edits (pattern binding, executor registry, CDD enforcement) must be driven through a semantic-ID resolver, not positional JSON Pointers.

Intended outcome: a v3.3 JSON set in which every executable step is bound to a registered pattern + executor + validated config through `executor_binding`, `behavior_spec`, and `behavior_binding_proof`, every validation gate name is consistent across all three files, and every edit is reproducible by a CLI through a semantic-ID → JSON-Pointer resolver.

## Scope decisions (binding)

These decisions answer the open questions from review and supersede any conflicting wording elsewhere in this plan:

1. **Single canonical mainline.** Layer 1 (`implementation_behavior_contract`, `GATE-BEH-*`) and Layer 2 (`shared_core_architecture_contract`, `agent_context_contract`, `compatibility_enforcement_stack`, `GATE-CFGCTX-*`) are **out of scope** for v3.3. They remain on side branches and may ship as v3.4. This plan does not edit them, does not require them in `required_sections`, does not add their gate families anywhere, and does not extend `step_contract.required_fields` with Layer 2-only bindings (`context_binding`, `boundary_contract_binding`, `packaging_binding`, `state_coordination_binding`).
2. **Spec `gate_registry` is the single source of truth for every gate family.** Template `validation_gates` and instruction-doc narrative may only **reference** gate IDs that already exist in spec `gate_registry`. Verification is a one-way containment check, not bidirectional.
3. **`executor_function` migration is completed, not hedged.** It is replaced wholesale by the canonical compound binding from the authority spec. For executable steps, that means `executor_binding` (`executor_id`, `executor_version`, `invocation_ref`), `behavior_spec` (`pattern_id`, `pattern_version`, `spec_file`, `config_instance_file`, `config_schema_file`, `parameter_schema_file`), and `behavior_binding_proof` (`command`, `evidence`). For `execution_patterns.required_pattern_components`, the canonical full set is `["spec_file", "config_schema_file", "parameter_schema_file", "executor_id", "pattern_index_entry", "guardrails_block", "output_contract_ref", "golden_test_fixture"]`. No back-compat shim. No invented field names. This full set supersedes any shorter list elsewhere in this plan.
4. **Two-pass indexing.** Phase A.2 indexes only IDs that exist post-A.1. New ID families introduced by Phase B (`pattern_id`, `executor_id`, `GATE-CFG-*`) are indexed in Phase A.3 after B.3 completes.
5. **BLK-003 classification lives in the A.2 inventory only.** No in-source `execution_phases_classification` sentinel, no narrative note, and no schema change. The source spec remains unchanged for this blocker.

## Governing authority

- **Resolved Authority Spec rulings 1–16** are the primary contract.
- **Rulings 17–20** close gaps:
  - **R-17**: `execution_phases` classified structural (inventory-only per scope decision 5).
  - **R-18**: `FINAL_EDIT_PLAN_V3_2_TO_V3_3.md` is the operation list; `MERGED_CORRECTED_FINAL_EDIT_PLAN.md` is the override layer; `phase_b_override_map.md` must exist before Phase B.
  - **R-19**: Phase B array-element edits route through `resolve(file, semantic_id)`; positional pointers rewritten.
  - **R-20**: Phase A is split into A.1 (blockers) and A.2 (index infrastructure); governance (Phase B) gated on A.2; PH-04 deferred to Phase C.
- Edit order across files: **spec → template → instruction** (per MERGED_CORRECTED §2–4).

## Phased execution

### Phase A.1 — Blocker remediation (`cli_blocker_fix_guide.md`)

Goal: make the three JSONs index-eligible. No governance edits.

1. **BLK-001 — Duplicate `GATE-008` in tech spec**
   - File: `NEWPHASEPLANPROCESS_TECHNICAL_SPECIFICATION_V3_2.json`
   - Location: `/architecture/system_layers/layer_2_validation/components[1]/gate_registry`, the two `GATE-008` entries currently at lines 248–259.
   - Keep `GATE-008 = "Automation Index"` (`build_automation_index.py`) as canonical.
   - Delete the earlier stray `GATE-008` (`"Automation Spec"` / `validate_automation_spec.py`); it duplicates `GATE-007`.
   - Update narrative cross-references in the spec.
   - Emit `evidence/blocker_1_gate_registry_fix/{pre,post,validation}.json`.

2. **BLK-002 — Ordinal enhancement IDs in template**
   - File: `NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_2.json`
   - Location: `/final_summary/what_was_delivered/enhancements[*]/id`.
   - Rewrite numeric `1..10` → `ENH-001..ENH-010` (zero-padded).
   - Emit `old_id → new_id` migration map.

3. **BLK-003 — Plain-string `execution_phases`** (per R-17 and scope decision 5)
   - File: `NEWPHASEPLANPROCESS_TECHNICAL_SPECIFICATION_V3_2.json`
   - Location: `/architecture/system_layers/layer_2_validation/components[1]/execution_phases` (lines 148–155).
   - **Source-file change**: none. Do **not** add any sentinel field, description field, or narrative note for this blocker.
   - Classification is recorded only in the Phase A.2 `inventory.json` as `structural`, excluded from generated `by_*` indexes, and updated by whole-array replacement if a later phase ever changes the phase list.

4. **BLK-004 — Missing `component_id` on system-layer components**
   - File: `NEWPHASEPLANPROCESS_TECHNICAL_SPECIFICATION_V3_2.json`
   - Location: every element under `/architecture/system_layers/*/components`.
   - Add `component_id` in pattern `COMP-L{layer}-{NN}` by current order, preserving existing `name`.
   - This must precede any Phase B step that adds a new component (those new components are authored with `component_id` from inception).

**Exit criteria**: all four blockers PASS; `final_blocker_resolution_report.json` emitted.

### Phase A.2 — Index infrastructure (subset of `final_indexing_implementation_plan.json`)

Goal: stand up a semantic-ID → JSON-Pointer resolver over **only the IDs that exist post-A.1**. PH-04 is deferred to Phase C.

Deliverables:
- `inventory.json` — classifies every array in all three files as `index_eligible` or `structural`. Classification of `execution_phases` lives here and only here.
- `index_generator.py` — builds `by_gate_id`, `by_component_id`, `by_enhancement_id`, `by_step_id`. **Does not** build `by_pattern_id` or `by_executor_id` yet (those IDs don't exist until Phase B).
- `resolver.py` exporting `resolve(file, semantic_id) -> JSON Pointer (string)`.
- CLI wiring so every `replace` / `remove` op in Phase B takes a semantic ID, not a positional index. `add` ops with `/-` tails or to known object keys do not require resolution.
- Validation gates `IDX-GATE-01..IDX-GATE-05` from the indexing plan, evaluated only against the post-A.1 ID set.

**Exit criteria**: resolver round-trips for every gate / component / enhancement / step ID present in the corpus; sandbox-reorder test confirms the resolver returns the same element after a shuffle.

### Phase B.0 — Reserve new ID namespaces

Authoring task only; no source edits.

- Write `reserved_id_namespaces.json` declaring the regex patterns the post-B resolver will be required to handle:
  - `^GATE-CFG-\d{3}$`
  - `^PAT-[A-Z0-9-]+$`
  - `^EXEC-[A-Z0-9-]+$`
  - `^COMP-L\d-\d{2}$` (extended range to include components added in B.1)
- Phase B must instantiate at least one concrete `PAT-*` example pattern reference and at least one concrete `EXEC-*` executor entry so Phase A.3 can validate those namespaces as non-empty.
- Phase A.3 will validate each reserved namespace is non-empty after Phase B.

### Phase B — Governance migration (edit order: spec → template → instruction)

Precondition: `phase_b_override_map.md` and `reserved_id_namespaces.json` both committed. The override map must list, minimally:

- Registry path = `PATTERN_INDEX.yaml` (overrides any `registry/pattern_registry.yaml` reference).
- Version bump policy = conditional (default = no forced `v3.3.0`). If the override map elects a `v3.3.0` release, run the explicit metadata/history/migration updates listed in B.1/B.2/B.3; otherwise preserve current version labels while still applying the governance edits.
- `execution_patterns` strategy = **extend**, not replace.
- `planning_hierarchy` strategy = **extend** (preserve current shape at template lines 1563–1568).
- Gate-count math: recompute `total_gates`, `mandatory_gates`, `optional_gates`, and every "All N validation gates" narrative string in the spec (currently `19 / 17 / 5` at lines 144–146 and references at ~1548, 1572, 1840) **once**, at the end of B.1, from the final post-edit `gate_registry`.
- Edit order = spec → template → instruction.
- New components introduced in B.1 are authored with `component_id` from inception.
- All `replace` / `remove` ops on existing array elements use the A.2 resolver.
- `executor_function` is replaced wholesale (no back-compat).
- `gate_registry.GATE-003.required_fields` and its `critical_rule` count text must be updated in lockstep with the final `data_structures.plan_document.step_contract.required_fields` contract; no stale "All 13 contract fields" text may survive B.1.

#### B.1 — Technical specification

Apply `FINAL_EDIT_PLAN_V3_2_TO_V3_3.md` operations **S-01 through S-10**, with overrides:

- `executive_summary.design_principles`: add `configuration_driven_development`.
- `executive_summary.key_capabilities`: add executor / config-binding capabilities.
- `architecture`: add Pattern Registry, Executor Registry, Configuration Schema Validator, Behavior Binding Validator, Pattern Creation Workflow, CDD Enforcement Gates as new components, each with `component_id` assigned on creation.
- `data_structures.plan_document.root_structure.required_sections`: add `pattern_governance`, `configuration_driven_development`, `executor_registry`. **Do not** add Layer 1/Layer 2 sections.
- Add spec top-level `configuration_driven_development`, `pattern_governance`, and `executor_registry` sections so the spec actually matches the required-section contract. `configuration_driven_development` must include the separation model, glossary, pattern-creation lifecycle, and validation guarantees. `pattern_governance` must include `pattern_resolution_phase`, `pattern_creation_contract`, `manual_exception_policy`, `required_step_fields`, and `enforcement_gates`. `executor_registry` must define the registered executor contract and its supported pattern/config surfaces.
- `data_structures.plan_document.step_contract.required_fields`: add `implementation_mode`, `executor_binding`, `behavior_spec`, `behavior_binding_proof`, `allowed_extension_slots`, `bespoke_logic_allowed`. **Do not** add any Layer 2 binding.
- Canonical step-binding shapes in the spec are: `executor_binding` (`executor_id`, `executor_version`, `invocation_ref`), `behavior_spec` (`pattern_id`, `pattern_version`, `spec_file`, `config_instance_file`, `config_schema_file`, `parameter_schema_file`), and `behavior_binding_proof` (`command`, `evidence`).
- `gate_registry.GATE-003`: expand `required_fields` to cover the final executable-step contract surface after B.1 (`implementation_mode`, `executor_binding`, `behavior_spec`, `behavior_binding_proof`, `allowed_extension_slots`, `bespoke_logic_allowed`, plus any other field added to `step_contract.required_fields` during B.1). Update `critical_rule` to match the final computed field count rather than preserving the stale `13`-field wording.
- `pipeline_boundary_contract`: add `allowed_execution_inputs` and explicit forbiddances (prompt-only binding, unregistered executors, direct ad hoc mutation).
- `execution_patterns.structure.pattern_validation.required_pattern_components` at line 1216: **replace** `executor_function` with the full canonical set `["spec_file", "config_schema_file", "parameter_schema_file", "executor_id", "pattern_index_entry", "guardrails_block", "output_contract_ref", "golden_test_fixture"]`. Also add `missing_pattern_action: fail_closed_create_pattern_task`, `require_executor_binding_per_pattern: true`, `require_behavior_binding_proof: true`, and a fail-closed `guardrail_policy`. No back-compat shim. No invented field names — use only the names the authority spec defines.
- `traceability`: add `requirement_to_pattern`, `component_to_pattern`, `step_to_executor`, `pattern_to_config_schema`, `pattern_to_output_contract`.
- `anti_pattern_detection`: add CDD / patternless-execution triggers.
- `development_guidelines.adding_new_features`: replace the old rule with "registered executor + validated spec/config + evidence + pass/fail condition."
- `gate_registry`: append `GATE-CFG-001..006`. **Do not** append `GATE-BEH-*` or `GATE-CFGCTX-*`.
- After all additions, recompute `total_gates` / `mandatory_gates` / `optional_gates` at lines 144–146 from the final `gate_registry`, and update narrative strings at ~1548, 1572, 1840.
- If the override map selects a `v3.3.0` release, also update spec version metadata in this same phase: `document_metadata.version`, `document_metadata.title`, `executive_summary.system_name`, `appendix.version_history.v3.3.0`, and `appendix.migration_guide.from_v3_2_to_v3_3`. If no bump is selected, leave those version labels unchanged.
- All array-element touches use `resolve(file, semantic_id)`.

#### B.2 — Autonomous delivery template

Apply FINAL_EDIT_PLAN ops **T-01 through T-17**, overrides applied, **excluding** any op that introduces Layer 1 or Layer 2 contracts:

- `critical_constraint.rules`: add fail-closed rules for patternless execution, null/blank pattern IDs on executable steps, ad hoc behavior sources, unregistered executors.
- Add top-level `configuration_driven_development`, `pattern_governance`, `executor_registry`. **Do not** add `implementation_behavior_contract`, `shared_core_architecture_contract`, `agent_context_contract`, or `compatibility_enforcement_stack`.
- Under `pattern_governance`, add the canonical pattern-first substructure: `pattern_resolution_phase`, `pattern_creation_contract`, `manual_exception_policy`, `required_step_fields`, and `enforcement_gates`.
- Seed `executor_registry` examples with at least one concrete `executor_id` matching `^EXEC-[A-Z0-9-]+$` so example bindings and Phase A.3 namespace checks have a real target.
- Skip Layer 1 and Layer 2 machine-patch application entirely. `v3_3_patch_plan_machine_style.json` and `v3_3_patch_plan_machine_layer2.json` are **not applied** in v3.3.
- `task_analysis`: add `pattern_resolution_decision`, `existing_pattern_match`, `new_pattern_required`, `executor_family`, `config_driven_feasibility`.
- `file_manifest`: add pattern-provenance fields.
- `step_contracts`: extend example steps with `implementation_mode`, `executor_binding`, `behavior_spec`, `behavior_binding_proof`, `allowed_extension_slots`, and `bespoke_logic_allowed`; preserve section shape. Migrate example `pattern_id` values from `PATTERN-EXAMPLE-*` to `PAT-EXAMPLE-*` and point example `executor_binding.executor_id` values at the concrete `EXEC-*` entries introduced in `executor_registry`.
- `planning_hierarchy`: **extend** (do not reshape lines 1563–1568); add `implementation_style`, `engine_component_id`, `config_schema_artifacts`, `executor_dependencies`, `approved_extension_slots` as additive fields.
- `pipeline_boundary_contract`: add `allowed_execution_inputs` and the four forbiddances.
- `execution_patterns`: **extend** (keep `PATTERN_INDEX.yaml`). Add `allow_null_pattern_id: false`, `require_validated_pattern_before_execution: true`, `missing_pattern_action: fail_closed_create_pattern_task`, `require_executor_binding_per_pattern: true`, `require_behavior_binding_proof: true`, and fail-closed `guardrail_policy`. In `required_pattern_components` at lines 1582–1587, **replace** `executor_function` with the full canonical set `["spec_file", "config_schema_file", "parameter_schema_file", "executor_id", "pattern_index_entry", "guardrails_block", "output_contract_ref", "golden_test_fixture"]`. No back-compat.
- `traceability`, `anti_pattern_detection`: mirror spec additions.
- `validation_gates`: append references to `GATE-CFG-001..006` only. Every gate ID referenced here must already exist in the spec `gate_registry` from B.1. Add the new gate IDs to `pipeline_boundary_contract.validation_required_before_execution`.
- `ai_instructions`: add pattern-first intake step, new `do_not` and `remember` rules.
- `protected_paths.paths` at line 1852: leave `PATTERN_INDEX.yaml` unchanged.
- If the override map selects a `v3.3.0` release, update template metadata in this phase as well: `template_metadata.version`, `template_metadata.last_updated`, and `template_metadata.breaking_changes` so the template reflects the actual governance migration applied.

#### B.3 — Instruction document

Apply FINAL_EDIT_PLAN ops **I-01 through I-14**, respecting the file's "markdown-in-JSON-`content`-string" storage model:

- Deserialize `content`, edit the markdown, re-serialize.
- Replace the "set `pattern_id` to `null` and flag a new pattern is needed" wording with **pattern-creation-before-implementation** rules.
- Front-load PATTERN-FIRST and CONFIGURATION-DRIVEN laws near `NO IMPLIED BEHAVIOR`.
- Update narrative for `pattern_governance`, `configuration_driven_development`, `executor_registry`, `task_analysis`, `planning_hierarchy`, `execution_patterns`, `step_contracts`, `pipeline_boundary_contract`, and `validation_gates` to require `pattern_resolution_phase`, `pattern_creation_contract`, `manual_exception_policy`, and the full pattern-package requirements (`spec_file`, `config_schema_file`, `parameter_schema_file`, `executor_id`, `pattern_index_entry`, `guardrails_block`, `output_contract_ref`, `golden_test_fixture`), plus `executor_binding`, `behavior_spec`, `behavior_binding_proof`, and references to `GATE-CFG-001..006`. **Do not** mention `GATE-BEH-*` or `GATE-CFGCTX-*`.
- Add prohibitions: blank `pattern_id`, prompt-only binding, bespoke scripts where a registered pattern exists, silent pattern composition, implementation before pattern creation/validation.
- Remove any narrative that names `executor_function` as authoritative; replace with the canonical compound binding.
- If the override map selects a `v3.3.0` release, update instruction-doc metadata and overview text in this phase: `document_metadata.version`, `document_metadata.title`, and the versioned overview paragraph summarizing the v3.3 governance changes.

### Phase A.3 — Reindex after governance migration

Run after B.3 completes.

- Re-run `index_generator.py` over all three files.
- Build `by_pattern_id`, `by_executor_id`, and the expanded `by_gate_id` (now including `GATE-CFG-001..006`).
- Acceptance:
  - Every reserved namespace from B.0 is non-empty.
  - `resolve(file, id)` succeeds for every ID that any other file references (cross-file integrity).
  - No collision between pre-A.1 IDs and post-B IDs.
  - `IDX-GATE-01..IDX-GATE-05` PASS against the regenerated indexes.

### Phase C — Deferred

- PH-04 (instruction-document refactor into structured form).
- Layer 1 (`implementation_behavior_contract`, `GATE-BEH-*`).
- Layer 2 (`shared_core_architecture_contract`, `agent_context_contract`, `compatibility_enforcement_stack`, `GATE-CFGCTX-*`).
- Revisit after v3.3 is stable.

## Consistency pass (after A.3)

- Spec `required_sections` set equals template top-level keys for the sections introduced in v3.3.
- No document allows null/blank `pattern_id` on executable steps.
- Spec and template both contain concrete top-level `configuration_driven_development`, `pattern_governance`, and `executor_registry` sections, and `pattern_governance` contains `pattern_resolution_phase`, `pattern_creation_contract`, and `manual_exception_policy`.
- `execution_patterns` requires `executor_id`, `config_schema_file`, `parameter_schema_file`, `output_contract_ref`, `guardrails_block`, and `golden_test_fixture`; also requires `missing_pattern_action`, `require_executor_binding_per_pattern`, `require_behavior_binding_proof`, and fail-closed `guardrail_policy`; executable steps require `executor_binding`, `behavior_spec`, and `behavior_binding_proof` (no `executor_function` remains in any file).
- Spec `gate_registry.GATE-003.required_fields` and its `critical_rule` text are synchronized with the final B.1 executable-step contract; no stale field-count wording remains.
- `file_manifest`, `traceability`, `anti_pattern_detection` include pattern-aware provenance.
- One-way containment: every gate ID in template `validation_gates` and instruction narrative exists in spec `gate_registry`. Spec `gate_registry` may contain gates not yet referenced by template/instruction (none expected in v3.3).
- `total_gates` / `mandatory_gates` / `optional_gates` math matches the actual composition of spec `gate_registry`.
- No stale "All 19 validation gates" strings remain.
- If the override map selected a `v3.3.0` release, all three files reflect it consistently in metadata, titles/system names, appendix history, and migration notes.

## Critical files to modify

- `C:\Users\richg\Gov_Reg\NEWPHASEPLANPROCESS_TECHNICAL_SPECIFICATION_V3_2.json`
- `C:\Users\richg\Gov_Reg\NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_2.json`
- `C:\Users\richg\Gov_Reg\NEWPHASEPLANPROCESS_INSTRUCTION_DOCUMENT_V3_2.json`

## Planning artifacts to author (new files, not source edits)

- `phase_b_override_map.md` — required before Phase B.
- `reserved_id_namespaces.json` — required before Phase B (B.0 deliverable).
- `evidence/blocker_{1..4}_*/` and `evidence/final_blocker_resolution_report.json`.
- `inventory.json`, `index_generator.py`, `resolver.py` — Phase A.2.

## Source plans referenced

- `plansforthis\FINAL_EDIT_PLAN_V3_2_TO_V3_3.md` — T-01..T-17, S-01..S-10, I-01..I-14 operation list.
- `plansforthis\MERGED_CORRECTED_FINAL_EDIT_PLAN.md` — override layer.
- `plansforthis\cli_blocker_fix_guide.md` — BLK-001..004 acceptance checks.
- `plansforthis\final_indexing_implementation_plan.json` — PH-03, PH-05..PH-09 for index infrastructure.
- `plansforthis\v3_3_patch_plan_machine_style.json` — **deferred to Phase C**, not applied in v3.3.
- `plansforthis\v3_3_patch_plan_machine_layer2.json` — **deferred to Phase C**, not applied in v3.3.

## Verification

1. **Phase A.1**: blocker scanner reports PASS for BLK-001..004. `GATE-008` appears exactly once in `gate_registry`. Every enhancement `id` matches `^ENH-\d{3}$`. Every component has `component_id`. `execution_phases` remains unchanged in source and is classified `structural` in `inventory.json`.
2. **Phase A.2**: for every gate / component / enhancement / step ID in the post-A.1 corpus, `resolve(file, id)` returns a pointer that dereferences to the expected element. Sandbox-reorder round-trip passes.
3. **Phase B**: each of the three files parses (instruction doc: parse outer JSON, then parse `content` markdown structurally). Every new top-level section is present where required in both spec and template. No Layer 1/2 section appears in any file. Spec architecture includes `Behavior Binding Validator`. No `executor_function` reference remains. `pattern_governance` contains `pattern_resolution_phase`, `pattern_creation_contract`, and `manual_exception_policy`. Every executable-step example carries `executor_binding`, `behavior_spec`, and `behavior_binding_proof` with the canonical field names. `execution_patterns` contains the full fail-closed package requirements and policy flags. `gate_registry.GATE-003.required_fields` and its `critical_rule` text reflect the final expanded executable-step contract rather than stale 13-field wording. Every gate ID referenced in template `validation_gates` or instruction narrative exists in spec `gate_registry`. Recomputed `total_gates`, `mandatory_gates`, and `optional_gates` match the final `gate_registry`. If the override map selected `v3.3.0`, the spec/template/instruction metadata and migration history updates are all present.
4. **Phase A.3**: every reserved ID namespace from B.0 is non-empty. Cross-file ID references all resolve. `IDX-GATE-01..05` PASS.
5. **Cross-file consistency**: assert that spec `required_sections` ↔ template top-level keys agree on the v3.3-introduced sections (`pattern_governance`, `configuration_driven_development`, `executor_registry`). For the instruction doc, assert *prose coverage* only: the `content` markdown must reference each of those three section names and their canonical sub-fields (`pattern_resolution_phase`, `pattern_creation_contract`, `manual_exception_policy`). Do **not** require matching `###` headings in the instruction doc — B.3 updates narrative under existing headings, not by adding new headings.
6. **Regression**: run existing validators under `scripts/` referenced by the spec (e.g., `validate_structure.py`, `validate_gates.py`) against the edited template; assert zero new failures beyond intentional schema changes.
7. **Git**: each phase (A.1, A.2, B.0, B.1, B.2, B.3, A.3) lands as a separate commit so any phase is individually revertible.
