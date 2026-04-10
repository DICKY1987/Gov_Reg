# Next Development Steps — NPP v3.2 → v3.3 Governance Migration + Phase C Follow-on

## Context

`C:\Users\richg\Gov_Reg\` is at a clean checkpoint after Phase A.1 (blocker remediation) and Phase A.2 (semantic indexing). Evidence under `evidence/PH-03..PH-09` and `evidence/final_blocker_resolution_report.json` confirms PASS on the four blockers and on the five indexing gates (`IDX-GATE-01..05`).

The remaining work is **already fully authored** in the runbook set under `C:\Users\richg\Gov_Reg\guardrails_template_project\`:

- `greedy-stirring-tower.md` — the 7-phase runbook with 5 binding scope decisions and phase-by-phase acceptance criteria.
- `phase_b_override_map.md` — pre-B authority that maps each `FINAL_EDIT_PLAN_V3_2_TO_V3_3.md` step to `ACCEPT` or `OVERRIDE` with the effective instruction.
- `FINAL_EDIT_PLAN_V3_2_TO_V3_3.md` — the raw S-01..S-10, T-01..T-17, I-01..I-14 operation list.
- `MERGED_CORRECTED_FINAL_EDIT_PLAN.md` — 20 rulings (R-1..R-20) that narrow scope.
- `reserved_id_namespaces.json` — B.0 deliverable declaring the four post-B identity regexes (all `must_be_non_empty_after_phase_b: true`).
- `cli_blocker_fix_guide.md` — already executed in Phase A.1.
- `final_indexing_implementation_plan.json` — already executed in Phase A.2.
- `v3_3_patch_plan_machine_style.json`, `v3_3_patch_plan_machine_layer2.json` — **explicitly deferred to Phase C** per runbook scope decision 1; NOT applied in this plan.

**This plan does not invent new work.** It consolidates the authored runbook into an executable sequence, applies the user's release-decision override (v3.3.0 IS bumped, overriding override-map R-1), fixes two operational gaps flagged by `GREEDY_STIRRING_TOWER_EXECUTION_READINESS.md` (stale path references and dirty worktree), and delimits what is in scope vs Phase C follow-on.

### User release decision (overrides `phase_b_override_map.md` §"Release decision")

The override map's current decision is `no explicit v3.3.0 release bump has been selected`. **User has now explicitly selected a v3.3.0 bump.** This activates the conditional branches in the override map:

- S-10 OVERRIDE gate is SATISFIED → apply version history and migration-guide changes in B.1.
- T-01 OVERRIDE gate is SATISFIED → update `template_metadata.version`, `template_metadata.last_updated`, and `template_metadata.breaking_changes` in B.2.
- I-01 / I-02 OVERRIDE gates are SATISFIED → update `document_metadata.version`, `document_metadata.title`, and the versioned overview paragraph in B.3.

**Filename policy stays unchanged** per override map global ruling #3 — the three source files remain `*_V3_2.json` (version bump lives in content only), so `index_generator.py` `SOURCE_FILES` mapping does NOT need editing.

---

## Five Binding Scope Decisions (from `greedy-stirring-tower.md` §"Scope decisions")

These supersede any conflicting wording anywhere else in the runbook set. The plan enforces them throughout.

1. **Single canonical mainline.** Layer 1 (`implementation_behavior_contract`, `GATE-BEH-*`) and Layer 2 (`shared_core_architecture_contract`, `agent_context_contract`, `compatibility_enforcement_stack`, `GATE-CFGCTX-*`) are **out of scope for v3.3**. They remain on side branches and may ship as v3.4. `v3_3_patch_plan_machine_style.json` (Layer 1) and `v3_3_patch_plan_machine_layer2.json` (Layer 2) are **not applied** anywhere in this plan.
2. **Spec `gate_registry` is the single source of truth.** Template `validation_gates[]` and instruction-doc narrative may only **reference** gate IDs that already exist in spec `gate_registry`. Containment is **one-way** (spec → template/instruction), not bidirectional.
3. **`executor_function` migration is wholesale, not hedged.** It is replaced in all three files by the canonical compound binding:
   - `executor_binding` → `executor_id`, `executor_version`, `invocation_ref`
   - `behavior_spec` → `pattern_id`, `pattern_version`, `spec_file`, `config_instance_file`, `config_schema_file`, `parameter_schema_file`
   - `behavior_binding_proof` → `command`, `evidence`
   - `execution_patterns.required_pattern_components` canonical full set: `["spec_file", "config_schema_file", "parameter_schema_file", "executor_id", "pattern_index_entry", "guardrails_block", "output_contract_ref", "golden_test_fixture"]`
   - **No back-compat shim. No invented field names.**
4. **Two-pass indexing.** Phase A.2 indexes only IDs that exist post-A.1. New ID families introduced by Phase B (`PAT-*`, `EXEC-*`, `GATE-CFG-*`) are indexed in Phase A.3, after B.3.
5. **BLK-003 is inventory-only.** No in-source `execution_phases_classification` sentinel; classification lives only in `inventory.json` as `structural`. Source JSON for `execution_phases` is not touched.

---

## Phase Map

| Phase | Name | Status | Evidence Path |
|---|---|---|---|
| A.1 | Blocker remediation (BLK-001..004) | ✅ **DONE** | `evidence/blocker_*/`, `evidence/final_blocker_resolution_report.json` |
| A.2 | Index infrastructure + `IDX-GATE-01..05` | ✅ **DONE** | `evidence/PH-03..PH-09/` |
| B.0 | Reserve ID namespaces | ✅ **DONE** | `guardrails_template_project/reserved_id_namespaces.json` |
| PRE-B | Operational readiness (worktree + path fix) | ⏳ **TODO** | `evidence/PRE-B/readiness.json` |
| B.1 | Spec edits S-01..S-10 + gate-count recompute | ⏳ **TODO** | `evidence/B1/spec_edit_report.json` |
| B.2 | Template edits T-01..T-17 | ⏳ **TODO** | `evidence/B2/template_edit_report.json` |
| B.3 | Instruction-doc edits I-01..I-14 | ⏳ **TODO** | `evidence/B3/instruction_edit_report.json` |
| A.3 | Reindex over post-B corpus + namespace validation | ⏳ **TODO** | `evidence/PH-03..PH-09/` regenerated |
| CONSISTENCY | Post-A.3 consistency pass | ⏳ **TODO** | `evidence/CONSISTENCY/consistency_report.json` |
| C (deferred) | PH-04, Layer 1, Layer 2, GATE-CFG validator implementations, runtime `.state` wiring | 🔒 **Out of scope** | Future plan |

Each of B.1, B.2, B.3, A.3, CONSISTENCY lands as its own git commit per runbook §"Verification" item 7, so any phase is independently revertible.

---

## PRE-B — Operational Readiness (from `GREEDY_STIRRING_TOWER_EXECUTION_READINESS.md`)

The readiness review flagged two execution-blockers that are not yet fixed:

1. **Stale path references in `greedy-stirring-tower.md`** — the runbook still references `plansforthis\...` paths for `FINAL_EDIT_PLAN_V3_2_TO_V3_3.md`, `MERGED_CORRECTED_FINAL_EDIT_PLAN.md`, `cli_blocker_fix_guide.md`, `final_indexing_implementation_plan.json`, `v3_3_patch_plan_machine_style.json`, `v3_3_patch_plan_machine_layer2.json`. Actual locations are all under `C:\Users\richg\Gov_Reg\guardrails_template_project\`. No `plansforthis\` directory exists.
2. **Dirty worktree** — current branch `migration/consolidation-files-v3.1` has many uncommitted changes unrelated to Phase B, which weakens per-phase commit isolation required by the runbook.

**Steps:**
1. **Path correction (runbook-only edit):** In `C:\Users\richg\Gov_Reg\guardrails_template_project\greedy-stirring-tower.md`, rewrite the six `plansforthis\` references to the actual `C:\Users\richg\Gov_Reg\guardrails_template_project\...` paths. This is a documentation-only fix; it does not touch the three source JSONs. Commit as `docs(runbook): fix plansforthis paths after file relocation`.
2. **Worktree isolation:** Create a dedicated git worktree branched from a clean point, e.g.:
   ```
   git worktree add ..\gov_reg_phase_b -b phase-b/v3_2-to-v3_3 main
   ```
   Execute B.1→B.3→A.3 inside the worktree so the dirty state on `migration/consolidation-files-v3.1` does not contaminate Phase B commits. This matches the NPP template's own `worktree_isolation` contract.
3. Write `evidence/PRE-B/readiness.json` recording: SHA-256 of each of the three source JSONs, git HEAD of the new worktree, override-map release-decision flag (`v3.3.0: true`), confirmation that `reserved_id_namespaces.json` and `phase_b_override_map.md` are both committed.

**Gate:** Clean `git status` inside the worktree, all three source JSONs parse, `python index_generator.py` still exits 0 against the baseline.

---

## PH-B.1 — Technical Specification Edits

**Target:** `C:\Users\richg\Gov_Reg\NEWPHASEPLANPROCESS_TECHNICAL_SPECIFICATION_V3_2.json`

**Authority:** `FINAL_EDIT_PLAN_V3_2_TO_V3_3.md` ops S-01..S-10, subject to `phase_b_override_map.md` §"Specification steps". Global ruling: edit order `spec → template → instruction`.

**Per override map — S-01..S-10 application:**

| Step | Mode | Effective instruction |
|---|---|---|
| S-01 | ACCEPT | Add Configuration-Driven Development to `executive_summary.design_principles`. |
| S-02 | ACCEPT | Add executor / config-binding capabilities to `executive_summary.key_capabilities`. |
| S-03 | OVERRIDE | Add v3.3 governance architecture components only: Pattern Registry, Executor Registry, Configuration Schema Validator, **Behavior Binding Validator**, Pattern Creation Workflow, CDD Enforcement Gates. Each new component gets a `component_id` under `^COMP-L\d-\d{2}$` at creation. **Do not** add Layer 1 or Layer 2 contract families. |
| S-04 | OVERRIDE | Replace `executor_function` as the sole binding primitive with the canonical compound binding and the full 8-field required pattern package (scope decision 3). No back-compat shim. |
| S-05 | ACCEPT | Add `configuration_driven_development` as a new top-level spec section (separation model, glossary, pattern-creation lifecycle, validation guarantees). |
| S-06 | OVERRIDE | Expand `gate_registry.GATE-003.required_fields` to the final executable-step contract (`implementation_mode`, `executor_binding`, `behavior_spec`, `behavior_binding_proof`, `allowed_extension_slots`, `bespoke_logic_allowed`, plus any other `step_contract.required_fields` additions). **Update `critical_rule` in lockstep — kill the stale "All 13 contract fields" wording.** |
| S-07 | ACCEPT | Expand `data_structures.plan_document.step_contract.required_fields` with the canonical v3.3 executable-step fields. |
| S-08 | ACCEPT | Add top-level `pattern_governance` section with canonical substructure: `pattern_resolution_phase`, `pattern_creation_contract`, `manual_exception_policy`, `required_step_fields`, `enforcement_gates`. |
| S-09 | ACCEPT | Reframe `development_guidelines.adding_new_features` around "registered executor + validated spec/config + evidence + pass/fail condition." |
| S-10 | OVERRIDE — **now active** | Apply version history and migration-guide changes: `document_metadata.version` 3.2.0 → 3.3.0, `document_metadata.title` updated, `executive_summary.system_name` updated, `appendix.version_history.v3.3.0` appended, `appendix.migration_guide.from_v3_2_to_v3_3` appended. |

**Additional B.1 obligations from `greedy-stirring-tower.md` §B.1:**
- Add top-level spec `configuration_driven_development`, `pattern_governance`, and `executor_registry` sections so the spec actually matches the required-section contract (S-05, S-08 extended).
- `data_structures.plan_document.root_structure.required_sections`: add `pattern_governance`, `configuration_driven_development`, `executor_registry`. **Do not** add Layer 1/Layer 2 sections.
- `pipeline_boundary_contract`: add `allowed_execution_inputs` and explicit forbiddances (prompt-only binding, unregistered executors, direct ad hoc mutation).
- `execution_patterns.structure.pattern_validation.required_pattern_components` at spec line 1216: **replace** `executor_function` with full 8-field set. Add `missing_pattern_action: fail_closed_create_pattern_task`, `require_executor_binding_per_pattern: true`, `require_behavior_binding_proof: true`, fail-closed `guardrail_policy`.
- `traceability`: add `requirement_to_pattern`, `component_to_pattern`, `step_to_executor`, `pattern_to_config_schema`, `pattern_to_output_contract`.
- `anti_pattern_detection`: add CDD / patternless-execution triggers.
- `gate_registry`: append `GATE-CFG-001..006`. **Do not** append `GATE-BEH-*` or `GATE-CFGCTX-*`.

**Gate-count recomputation (runs ONCE at end of B.1, per override-map global ruling #9):**
After all S-* ops land, compute `len(gate_registry)` and overwrite:
- `total_gates`, `mandatory_gates`, `optional_gates` at spec lines 144–146
- Every `"All N validation gates"` narrative string (current hits at spec ~1548, 1572, 1840)

Do not guess values up front — recompute from the final live `gate_registry` array.

**Execution mechanics:**
- All `replace` / `remove` ops on existing array elements route through the A.2 resolver (`resolver.py`) per ruling R-19. `add` ops with `/-` tails or to known object keys do not need resolver calls.
- After each S-* op, run `python index_generator.py --inventory-only` and diff array shape against PRE-B baseline. Unexpected shape drift halts the phase.
- Write `evidence/B1/spec_edit_report.json` with per-op: step_id, JSON pointer, override mode, before_hash, after_hash, new IDs introduced.

**Gate:** Spec still parses; `IDX-GATE-03` (source hash freshness) will fail by design — this is expected and re-established in A.3. No Layer 1 / Layer 2 section appears anywhere. GATE-003.required_fields and critical_rule text are synchronized.

---

## PH-B.2 — Autonomous Delivery Template Edits

**Target:** `C:\Users\richg\Gov_Reg\NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_2.json`

**Authority:** `FINAL_EDIT_PLAN_V3_2_TO_V3_3.md` ops T-01..T-17, subject to `phase_b_override_map.md` §"Template steps".

**Per override map — T-01..T-17 application:**

| Step | Mode | Effective instruction |
|---|---|---|
| T-01 | OVERRIDE — **now active** | Apply `template_metadata.version` 3.2.0 → 3.3.0, update `template_metadata.last_updated`, append new items to `template_metadata.breaking_changes` reflecting the governance migration. |
| T-02 | ACCEPT | Strengthen `critical_constraint.rules` with fail-closed pattern and executor restrictions (patternless execution, null/blank `pattern_id`, ad hoc behavior, unregistered executors). |
| T-03 | ACCEPT | Add `configuration_driven_development` as a new top-level section. |
| T-04 | OVERRIDE | Add `pattern_governance` top-level section, limited to canonical mainline: `pattern_resolution_phase`, `pattern_creation_contract`, `manual_exception_policy`, `required_step_fields`, `enforcement_gates`. **Do not** introduce Layer 1/Layer 2 sections. |
| T-05 | ACCEPT | Add pattern-resolution outputs to `task_analysis` (`pattern_resolution_decision`, `existing_pattern_match`, `new_pattern_required`, `executor_family`, `config_driven_feasibility`). |
| T-06 | ACCEPT | Add pattern provenance fields to `file_manifest`. |
| T-07 | OVERRIDE | **Extend** `execution_patterns` (don't replace). Keep `PATTERN_INDEX.yaml` canonical. Replace `executor_function` with full 8-field required package. Add `allow_null_pattern_id: false`, `require_validated_pattern_before_execution: true`, `missing_pattern_action: fail_closed_create_pattern_task`, `require_executor_binding_per_pattern: true`, `require_behavior_binding_proof: true`, fail-closed `guardrail_policy`. |
| T-08 | ACCEPT | Add `executor_registry` with concrete `EXEC-*` examples matching `^EXEC-[A-Z0-9-]+$` (so Phase A.3 namespace check has a real target). |
| T-09 | ACCEPT | Expand `pipeline_boundary_contract` with `allowed_execution_inputs: ["plan_json", "registered_pattern_spec", "schema_validated_config"]` plus four forbiddances. |
| T-10 | OVERRIDE | Extend executable step examples with `implementation_mode`, `executor_binding`, `behavior_spec`, `behavior_binding_proof`, `allowed_extension_slots`, `bespoke_logic_allowed`. **Migrate example `pattern_id` values from `PATTERN-EXAMPLE-*` → `PAT-EXAMPLE-*`.** Point example `executor_binding.executor_id` at the concrete `EXEC-*` entries from T-08. |
| T-11 | OVERRIDE | **Extend** `planning_hierarchy` without reshaping existing structure at template lines 1563–1568. Add additive fields: `implementation_style`, `engine_component_id`, `config_schema_artifacts`, `executor_dependencies`, `approved_extension_slots`. |
| T-12 | ACCEPT | Expand `traceability` with pattern and executor mappings (mirror spec additions from S-B1). |
| T-13 | OVERRIDE | Append **only** `GATE-CFG-001..006` to `validation_gates`, and **only after** those gate IDs exist in spec `gate_registry` from B.1 (one-way containment, scope decision 2). Also add them to `pipeline_boundary_contract.validation_required_before_execution`. |
| T-14 | ACCEPT | Expand `anti_pattern_detection` triggers with CDD / patternless-execution rules. |
| T-15 | ACCEPT | Expand AI intake instructions with pattern-first behavior. |
| T-16 | ACCEPT | Expand `ai_instructions.do_not`. |
| T-17 | ACCEPT | Expand `ai_instructions.remember`. |

**Hard prohibitions from `greedy-stirring-tower.md` §B.2:**
- Skip Layer 1 and Layer 2 machine-patch application entirely. `v3_3_patch_plan_machine_style.json` and `v3_3_patch_plan_machine_layer2.json` are **not applied**.
- **Do not** add `implementation_behavior_contract`, `shared_core_architecture_contract`, `agent_context_contract`, or `compatibility_enforcement_stack`.
- `protected_paths.paths` at template line 1852: leave `PATTERN_INDEX.yaml` unchanged.
- New identity-bearing elements must have IDs valid under their reserved namespace regex (`reserved_id_namespaces.json`). Duplicate identity actions in `inventory.json` are `fail_closed` — violation halts Phase B.

**Execution mechanics:**
- After each T-* op, run `python index_generator.py` full run (NOT inventory-only). The sandbox-reorder test in `index_generator.py:443` must still pass after every edit.
- Write `evidence/B2/template_edit_report.json` with per-op record.

**Gate:** `index_generator.py` exits 0 after final T-17; cross-file integrity check (`validate_cross_file_integrity` at `index_generator.py:360`) finds every referenced `gate_id`, `pattern_id`, `executor_id` in the semantic indexes.

---

## PH-B.3 — Instruction Document Edits

**Target:** `C:\Users\richg\Gov_Reg\NEWPHASEPLANPROCESS_INSTRUCTION_DOCUMENT_V3_2.json`

**Authority:** `FINAL_EDIT_PLAN_V3_2_TO_V3_3.md` ops I-01..I-14, subject to `phase_b_override_map.md` §"Instruction steps".

**Storage model:** The instruction doc is markdown-in-JSON. The markdown text lives inside a `content` string field. Phase B.3 **deserializes `content`**, **edits the markdown**, **re-serializes**. JSON structure outside `content` is touched only for metadata updates (I-01 / I-02).

**Per override map — I-01..I-14 application:**

| Step | Mode | Effective instruction |
|---|---|---|
| I-01 | OVERRIDE — **now active** | Update instruction-doc metadata: `document_metadata.version` 3.2.0 → 3.3.0, `document_metadata.title` updated. |
| I-02 | OVERRIDE — **now active** | Apply versioned overview paragraph update summarizing v3.3 governance changes. |
| I-03 | ACCEPT | Add the CDD general principle. |
| I-04 | ACCEPT | Strengthen pattern-first execution guidance. |
| I-05 | ACCEPT | Add the PATTERN-FIRST EXECUTION LAW block, front-loaded near NO_IMPLIED_BEHAVIOR. |
| I-06 | ACCEPT | Update `task_analysis` instructions with pattern-resolution outputs. |
| I-07 | ACCEPT | Update `planning_hierarchy` instructions to match the additive hierarchy fields from T-11. |
| I-08 | OVERRIDE | Rewrite `execution_patterns` instructions to require the canonical 8-field pattern package, fail-closed policy, and **removal** of `executor_function` as an authoritative binding. |
| I-09 | OVERRIDE | Rewrite `step_contracts` instructions to require `executor_binding`, `behavior_spec`, and `behavior_binding_proof` using the canonical field names. |
| I-10 | ACCEPT | Expand `pipeline_boundary_contract` instructions with allowed inputs and forbiddances. |
| I-11 | OVERRIDE | Expand `validation_gates` instructions using only `GATE-CFG-001..006`. **Do not mention `GATE-BEH-*` or `GATE-CFGCTX-*`.** |
| I-12 | ACCEPT | Expand AI prohibitions (blank `pattern_id`, prompt-only binding, bespoke scripts, silent pattern composition, pre-creation implementation). |
| I-13 | ACCEPT | Expand AI mnemonics. |
| I-14 | ACCEPT | Add the required AI decision sequence. |

**Write `evidence/B3/instruction_edit_report.json`** with before/after SHA-256 on the full JSON file and on the inner `content` markdown.

**Gate:** Outer JSON still parses; inner `content` markdown still parses structurally; metadata version strings are `"3.3.0"`.

---

## PH-A.3 — Reindex Over Post-B Corpus

**Goal:** Regenerate all index artifacts against the post-B.3 files and prove cross-file integrity holds.

**Critical files (all reused, not edited except `ARRAY_RULES` delta):**
- `C:\Users\richg\Gov_Reg\index_generator.py`
- `C:\Users\richg\Gov_Reg\resolver.py`
- `C:\Users\richg\Gov_Reg\inventory.json` (regenerated output)
- `C:\Users\richg\Gov_Reg\indexes\*.index.json` (regenerated)
- `C:\Users\richg\Gov_Reg\evidence\PH-03..PH-09\` (regenerated)

**Steps:**
1. If Phase B introduced new identity-bearing array paths not already covered by `ARRAY_RULES` in `index_generator.py` (lines 23–87), add the new rule entries **before** running the full regen. Document any `ARRAY_RULES` delta in `evidence/A3/array_rules_delta.json`. Expected new rules: none, because B.1 additions to `task_pattern_mappings` and `executor_registry.registered_executors` reuse existing array paths already classified as `index_eligible`; new gate-registry entries also reuse an existing `index_eligible` path.
2. Run `python index_generator.py` (full run).
3. Confirm `IDX-GATE-01..05` all PASS in the regenerated `evidence/PH-08/validation_gate_report.json`.
4. Confirm `validate_reserved_namespaces()` at `index_generator.py:342` returns `PASS` with all four counts (`GATE-CFG`, `PAT`, `EXEC`, `COMP`) non-zero — this validates the `reserved_id_namespaces.json` contract.
5. Confirm `validate_cross_file_integrity()` at `index_generator.py:360` returns `errors: []` — every `pattern_id`, `executor_id`, gate reference in template resolves through the semantic indexes of template or spec.
6. Confirm `run_sandbox_reorder_test()` at `index_generator.py:443` returns PASS — key sets are invariant under array reordering across `validation_gates`, `enhancements`, `task_pattern_mappings`, `registered_executors`, and `gate_registry`.
7. Confirm `evidence/PH-09/final_readiness_report.json` top-level `status == "PASS"`.

**Gate:** All of 3–7 above PASS. No collision between pre-A.1 IDs and post-B IDs.

---

## CONSISTENCY — Post-A.3 Cross-File Consistency Pass

**Per `greedy-stirring-tower.md` §"Consistency pass (after A.3)"**, assert all of the following:

1. **Required-section parity:** Spec `data_structures.plan_document.root_structure.required_sections` set equals the template's top-level key set for the v3.3-introduced sections (`pattern_governance`, `configuration_driven_development`, `executor_registry`). Both spec and template have concrete top-level sections with those names, and `pattern_governance` contains `pattern_resolution_phase`, `pattern_creation_contract`, and `manual_exception_policy`.
2. **Pattern package fullness:** `execution_patterns.required_pattern_components` in both spec and template contains the full canonical 8-field set. `executor_function` appears nowhere in any of the three files.
3. **Executable step contract:** Every executable-step example carries `executor_binding`, `behavior_spec`, and `behavior_binding_proof` with canonical field names. No null/blank `pattern_id` on any executable step.
4. **GATE-003 lockstep:** Spec `gate_registry.GATE-003.required_fields` matches final B.1 `step_contract.required_fields`; `critical_rule` text reflects the final field count (no stale "13-field" wording).
5. **One-way gate containment:** Every gate ID in template `validation_gates` and instruction narrative exists in spec `gate_registry`. Spec may contain gates not referenced by template/instruction (none expected in v3.3).
6. **Gate-count math:** `total_gates` / `mandatory_gates` / `optional_gates` in spec match actual `len(gate_registry)` decomposition. No stale `"All 19 validation gates"` string remains.
7. **Provenance fields:** `file_manifest`, `traceability`, `anti_pattern_detection` include pattern-aware provenance in both spec and template.
8. **Version metadata consistency:** All three files report `version == "3.3.0"`; spec `appendix.version_history.v3.3.0` is present; spec `appendix.migration_guide.from_v3_2_to_v3_3` is present; template `template_metadata.breaking_changes` includes the v3.3 governance entries; instruction doc versioned overview paragraph is updated.
9. **Instruction doc — prose coverage only (NOT header parity):** The instruction doc's inner `content` markdown **references** each of `configuration_driven_development`, `pattern_governance`, `executor_registry` by name, and references their canonical sub-fields (`pattern_resolution_phase`, `pattern_creation_contract`, `manual_exception_policy`). **Do NOT require matching `###` headings** — per the prior code-review finding, B.3 updates narrative under existing headings rather than adding new headings; header parity would fail even on a correct migration.
10. **No forbidden families:** No `implementation_behavior_contract`, `shared_core_architecture_contract`, `agent_context_contract`, `compatibility_enforcement_stack`, `GATE-BEH-*`, or `GATE-CFGCTX-*` anywhere.

**Regression validators** (invoked against edited files, existing scripts, no code changes):
- `C:\Users\richg\Gov_Reg\newPhasePlanProcess\01260207201000001225_scripts\P_01260207233100000263_validate_structure.py`
- `C:\Users\richg\Gov_Reg\newPhasePlanProcess\01260207201000001225_scripts\P_01260207233100000253_validate_gates.py`
- `C:\Users\richg\Gov_Reg\newPhasePlanProcess\01260207201000001225_scripts\P_01260207233100000250_validate_automation_spec.py`
- `C:\Users\richg\Gov_Reg\newPhasePlanProcess\01260207201000001225_scripts\P_01260207233100000226_build_automation_index.py`

Assert: zero new failures beyond intentional schema changes in v3.3. Write `evidence/CONSISTENCY/consistency_report.json` with per-check PASS/FAIL + per-validator exit codes.

---

## Phase C — Explicitly Deferred (Out of Scope for this Plan)

Listed so future planning has a named follow-on target. **None of the below are executed by this plan:**

- **PH-04 — Instruction-document refactor** into structured (non-markdown-in-JSON) form.
- **Layer 1** — `implementation_behavior_contract`, `GATE-BEH-*` (from `v3_3_patch_plan_machine_style.json`).
- **Layer 2** — `shared_core_architecture_contract`, `agent_context_contract`, `compatibility_enforcement_stack`, `GATE-CFGCTX-*` (from `v3_3_patch_plan_machine_layer2.json`).
- **GATE-CFG-001..006 validator implementations** — The six CDD enforcement gates are defined in the spec gate registry and referenced by the template `validation_gates` after B.1/B.2, but no existing source plan authors the `validate_pattern_completeness.py` / `validate_engine_spec_separation.py` / etc. scripts themselves. The runbook does not cover them. These should ship as a Phase C follow-on plan once v3.3 is stable.
- **Runtime `.state/` wiring** — `run_status.json` (schema already authored at `guardrails_template_project/run_status_schema.json`), `mutation_ledger.jsonl`, behavior-binding proof writers, evidence-chain writers. Schema exists but runtime producers are absent.
- **External `executor_registry.yaml`** — registry stays inline in the template for v3.3; externalization deferred.

---

## Critical Files

**Edited by this plan:**
- `C:\Users\richg\Gov_Reg\NEWPHASEPLANPROCESS_TECHNICAL_SPECIFICATION_V3_2.json` (PH-B.1)
- `C:\Users\richg\Gov_Reg\NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_2.json` (PH-B.2)
- `C:\Users\richg\Gov_Reg\NEWPHASEPLANPROCESS_INSTRUCTION_DOCUMENT_V3_2.json` (PH-B.3)
- `C:\Users\richg\Gov_Reg\inventory.json` (regenerated PH-A.3)
- `C:\Users\richg\Gov_Reg\indexes\*.index.json` (regenerated PH-A.3)
- `C:\Users\richg\Gov_Reg\guardrails_template_project\greedy-stirring-tower.md` (docs-only path fix in PRE-B)
- New: `C:\Users\richg\Gov_Reg\evidence\PRE-B\readiness.json`, `evidence\B1\spec_edit_report.json`, `evidence\B2\template_edit_report.json`, `evidence\B3\instruction_edit_report.json`, `evidence\A3\array_rules_delta.json`, `evidence\CONSISTENCY\consistency_report.json`

**Read-only authority — never edited:**
- `C:\Users\richg\Gov_Reg\guardrails_template_project\greedy-stirring-tower.md` (after PRE-B fix)
- `C:\Users\richg\Gov_Reg\guardrails_template_project\phase_b_override_map.md`
- `C:\Users\richg\Gov_Reg\guardrails_template_project\FINAL_EDIT_PLAN_V3_2_TO_V3_3.md`
- `C:\Users\richg\Gov_Reg\guardrails_template_project\MERGED_CORRECTED_FINAL_EDIT_PLAN.md`
- `C:\Users\richg\Gov_Reg\guardrails_template_project\reserved_id_namespaces.json`

**Reused tooling — never edited unless `ARRAY_RULES` delta in A.3:**
- `C:\Users\richg\Gov_Reg\index_generator.py` (functions: `build_inventory`, `build_indexes`, `validate_indexes`, `validate_reserved_namespaces`, `validate_cross_file_integrity`, `run_sandbox_reorder_test`)
- `C:\Users\richg\Gov_Reg\resolver.py`

**Never applied in this plan (deferred to Phase C):**
- `C:\Users\richg\Gov_Reg\guardrails_template_project\v3_3_patch_plan_machine_style.json`
- `C:\Users\richg\Gov_Reg\guardrails_template_project\v3_3_patch_plan_machine_layer2.json`

---

## End-to-End Verification

Runs after every phase commit; final pass must hold after CONSISTENCY commit.

1. **PRE-B:** Clean `git status` inside `phase-b/v3_2-to-v3_3` worktree; `evidence/PRE-B/readiness.json` written.
2. **Phase A.1 still holds:** `evidence/final_blocker_resolution_report.json` remains PASS (untouched by Phase B).
3. **Phase A.2 re-established post-B:** `python index_generator.py` exits 0; `evidence/PH-09/final_readiness_report.json` status == `PASS`; `IDX-GATE-01..05` all PASS; sandbox reorder test PASS.
4. **Namespace contract:** `validate_reserved_namespaces()` counts for `GATE-CFG`, `PAT`, `EXEC`, `COMP` are all non-zero — satisfies `reserved_id_namespaces.json` `must_be_non_empty_after_phase_b`.
5. **Cross-file integrity:** `validate_cross_file_integrity()` returns zero errors across all `step_contracts[*].pattern_id`, `step_contracts[*].executor_binding.executor_id`, `step_contracts[*].behavior_spec.pattern_id`, `task_pattern_mappings[*].{pattern_id, executor_id}`, `pipeline_boundary_contract.validation_required_before_execution[]`, and `validation_gates[*].gate_id`.
6. **Version metadata:** `grep '"version"' *.json` returns `3.3.0` across all three source files; spec `appendix.version_history.v3.3.0` exists; migration guide exists.
7. **Gate containment one-way:** For every `gate_id` in template `validation_gates` and every gate reference in the instruction doc markdown, the ID resolves in spec `gate_registry` via `by_gate_id`. Reverse direction not asserted.
8. **Gate-count math:** Spec `total_gates`, `mandatory_gates`, `optional_gates` match `len(gate_registry)` decomposition; no stale `"All 19 validation gates"` string remains.
9. **Instruction-doc prose coverage:** The three v3.3 section names and canonical sub-fields all appear at least once in the inner `content` markdown.
10. **No forbidden families:** `grep` across all three files returns zero hits for `implementation_behavior_contract`, `shared_core_architecture_contract`, `agent_context_contract`, `compatibility_enforcement_stack`, `GATE-BEH-`, `GATE-CFGCTX-`.
11. **Existing validators:** `validate_structure.py` and `validate_gates.py` (under `newPhasePlanProcess\01260207201000001225_scripts\`) produce zero new failures beyond intentional v3.3 schema changes.
12. **Git hygiene:** Each of PRE-B, B.1, B.2, B.3, A.3, CONSISTENCY landed as a separate commit on `phase-b/v3_2-to-v3_3`; any phase is individually revertible via `git revert`.

A green full pass means: v3.2.0 → v3.3.0 governance migration complete on an isolated branch, cross-file integrity held, semantic-ID addressing still works, no Layer 1/Layer 2 contamination, and the corpus is ready for merge into `main` plus a Phase C follow-on plan to actually implement the `GATE-CFG` validator scripts, externalize the executor registry, and wire runtime `.state` producers.
