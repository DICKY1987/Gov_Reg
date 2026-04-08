# Phase B Override Map

This file is the pre-Phase-B override authority required by `greedy-stirring-tower.md`.

Source order:

1. `FINAL_EDIT_PLAN_V3_2_TO_V3_3.md` is the step list.
2. `MERGED_CORRECTED_FINAL_EDIT_PLAN.md` supplies corrections and narrowing.
3. `greedy-stirring-tower.md` scope decisions and rulings control any unresolved conflict.

Interpretation:

- `ACCEPT` means execute the named step as written, subject to the global rulings below.
- `OVERRIDE` means replace the raw step text with the corrected instruction in this file.

## Global rulings

- Edit order for governance migration is `spec -> template -> instruction`, regardless of the order in `FINAL_EDIT_PLAN_V3_2_TO_V3_3.md`.
- Default version policy is `no forced v3.3.0`. Only apply version-history and metadata bumps if a later explicit release decision changes this.
- Keep the current filenames. The migration edits the existing `V3_2` JSONs; it does not rename the files during Phase B.
- Keep `PATTERN_INDEX.yaml` as the canonical registry path.
- `execution_patterns` is extended, not replaced.
- `planning_hierarchy` is extended, not replaced.
- Layer 1 and Layer 2 contract families remain out of scope for v3.3:
  - `implementation_behavior_contract`
  - `shared_core_architecture_contract`
  - `agent_context_contract`
  - `compatibility_enforcement_stack`
  - `GATE-BEH-*`
  - `GATE-CFGCTX-*`
- Existing array-element `replace` and `remove` edits must route through the Phase A.2 semantic resolver.
- `executor_function` is replaced wholesale by the canonical compound binding:
  - `executor_binding`
  - `behavior_spec`
  - `behavior_binding_proof`
- Spec gate-count math and any `"All N validation gates"` prose are recomputed once at the end of B.1 from the final post-edit `gate_registry`.

## Step map

### Template steps

| Step | Status | Effective instruction |
| --- | --- | --- |
| T-01 | OVERRIDE | Apply template version metadata changes only if an explicit release decision selects `v3.3.0`; otherwise preserve the current `3.2.0` metadata. |
| T-02 | ACCEPT | Strengthen `critical_constraint.rules` with fail-closed pattern and executor restrictions. |
| T-03 | ACCEPT | Add `configuration_driven_development` as a new top-level section. |
| T-04 | OVERRIDE | Add `pattern_governance`, but keep it limited to the canonical v3.3 mainline: `pattern_resolution_phase`, `pattern_creation_contract`, `manual_exception_policy`, `required_step_fields`, and `enforcement_gates`. Do not introduce Layer 1 or Layer 2 sections. |
| T-05 | ACCEPT | Add pattern-resolution outputs to `task_analysis`. |
| T-06 | ACCEPT | Add pattern provenance fields to `file_manifest`. |
| T-07 | OVERRIDE | Extend `execution_patterns`; do not replace it. Keep `PATTERN_INDEX.yaml`. Replace `executor_function` with the canonical required package and fail-closed policy flags. |
| T-08 | ACCEPT | Add `executor_registry` with concrete `EXEC-*` examples. |
| T-09 | ACCEPT | Expand `pipeline_boundary_contract` with explicit allowed inputs and forbiddances. |
| T-10 | OVERRIDE | Extend executable step examples with `implementation_mode`, `executor_binding`, `behavior_spec`, `behavior_binding_proof`, `allowed_extension_slots`, and `bespoke_logic_allowed`; point examples at concrete `PAT-*` and `EXEC-*` IDs. |
| T-11 | OVERRIDE | Extend `planning_hierarchy` without reshaping the existing structure. Add only the additive fields required by the merged plan. |
| T-12 | ACCEPT | Expand `traceability` with pattern and executor mappings. |
| T-13 | OVERRIDE | Append only `GATE-CFG-001` through `GATE-CFG-006`, and only after those gate IDs exist in the spec. Also add them to `pipeline_boundary_contract.validation_required_before_execution`. |
| T-14 | ACCEPT | Expand `anti_pattern_detection` triggers. |
| T-15 | ACCEPT | Expand AI intake instructions with pattern-first behavior. |
| T-16 | ACCEPT | Expand `ai_instructions.do_not`. |
| T-17 | ACCEPT | Expand `ai_instructions.remember`. |

### Specification steps

| Step | Status | Effective instruction |
| --- | --- | --- |
| S-01 | ACCEPT | Add Configuration-Driven Development to design principles. |
| S-02 | ACCEPT | Add executor and config-binding capabilities to the executive summary. |
| S-03 | OVERRIDE | Add the v3.3 governance architecture components only: Pattern Registry, Executor Registry, Configuration Schema Validator, Behavior Binding Validator, Pattern Creation Workflow, and CDD Enforcement Gates. Do not add Layer 1 or Layer 2 contract families. |
| S-04 | OVERRIDE | Replace `executor_function` as the sole binding primitive with the canonical compound binding and the full required pattern package. |
| S-05 | ACCEPT | Add the `configuration_driven_development` top-level section. |
| S-06 | OVERRIDE | Expand `GATE-003.required_fields` to the final executable-step contract and recompute stale field-count and gate-count prose in the same phase. |
| S-07 | ACCEPT | Expand `step_contract.required_fields` with the canonical v3.3 executable-step fields. |
| S-08 | ACCEPT | Add `pattern_governance` to the spec with the canonical substructure. |
| S-09 | ACCEPT | Reframe `development_guidelines.adding_new_features` around registered executor plus validated spec/config plus evidence plus pass/fail condition. |
| S-10 | OVERRIDE | Add version history and migration-guide changes only if an explicit release decision selects `v3.3.0`; otherwise keep version labels unchanged while still applying governance edits. |

### Instruction steps

| Step | Status | Effective instruction |
| --- | --- | --- |
| I-01 | OVERRIDE | Apply instruction-document metadata version changes only if an explicit release decision selects `v3.3.0`. |
| I-02 | OVERRIDE | Apply the versioned overview paragraph update only if an explicit release decision selects `v3.3.0`; otherwise update the overview prose without changing the version label. |
| I-03 | ACCEPT | Add the CDD general principle. |
| I-04 | ACCEPT | Strengthen the pattern-first execution guidance. |
| I-05 | ACCEPT | Add the PATTERN-FIRST EXECUTION LAW block. |
| I-06 | ACCEPT | Update `task_analysis` instructions with pattern-resolution outputs. |
| I-07 | ACCEPT | Update `planning_hierarchy` instructions to match the additive hierarchy fields. |
| I-08 | OVERRIDE | Rewrite `execution_patterns` instructions to require the canonical pattern package, fail-closed policy, and removal of `executor_function` as an authoritative binding. |
| I-09 | OVERRIDE | Rewrite `step_contracts` instructions to require `executor_binding`, `behavior_spec`, and `behavior_binding_proof` using the canonical field names. |
| I-10 | ACCEPT | Expand `pipeline_boundary_contract` instructions with allowed inputs and forbiddances. |
| I-11 | OVERRIDE | Expand `validation_gates` instructions using only `GATE-CFG-001` through `GATE-CFG-006`. Do not mention `GATE-BEH-*` or `GATE-CFGCTX-*`. |
| I-12 | ACCEPT | Expand AI prohibitions. |
| I-13 | ACCEPT | Expand AI mnemonics. |
| I-14 | ACCEPT | Add the required AI decision sequence. |

## Release decision

Current decision: no explicit `v3.3.0` release bump has been selected.

That means Phase B should:

- apply the governance edits,
- keep existing filenames,
- keep current version labels,
- and leave version-history/migration-label updates dormant unless a later explicit release decision changes this file.
