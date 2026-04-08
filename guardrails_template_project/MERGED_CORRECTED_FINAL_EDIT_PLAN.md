# Merged Corrected Final Edit Plan

Use the two evaluation documents as one unified change set: enforce `pattern_governance` plus `configuration_driven_development`, but keep the edits grounded in the current v3.2 file structure and avoid speculative changes. Default to minimal scope: keep the existing filenames and current version labels unless an explicit release bump to `v3.3.0` is desired.

## 1. Define the merged target model before editing

- Treat the shared goal as: no executable step may proceed without validated pattern binding, registered executor binding, and approved external behavior artifacts.
- Add three canonical governance surfaces across the docs: `pattern_governance`, `configuration_driven_development`, and `executor_registry`.
- Keep existing `execution_patterns`; extend it rather than replace it.
- Keep `pattern_id` and `pattern_parameters`, but add executable-step binding fields: `implementation_mode`, `executor_binding`, `behavior_spec`, `behavior_binding_proof`, `allowed_extension_slots`, and `bespoke_logic_allowed`.
- Use one gate family only: `GATE-CFG-001` through `GATE-CFG-006`. Do not introduce a separate `GATE_PATTERN_BINDING` name.

## 2. Edit the technical specification first so the semantics are defined

- In `NEWPHASEPLANPROCESS_TECHNICAL_SPECIFICATION_V3_2.json`, add configuration-driven development to `executive_summary.design_principles` and add executor/config-binding capabilities to `key_capabilities`.
- In `architecture`, add the architecture components needed by the evaluations: Pattern Registry, Executor Registry, Configuration Schema Validator, Behavior Binding Validator, Pattern Creation Workflow, and CDD Enforcement Gates.
- In `data_structures.plan_document.root_structure.required_sections`, add the new top-level sections so the spec matches the template.
- In `data_structures.plan_document.step_contract.required_fields`, add the new executable-step fields and change `pattern_id` semantics from "reference" to "mandatory binding for executable steps."
- In `pipeline_boundary_contract`, add `allowed_execution_inputs` and explicit forbiddance of prompt-only binding, unregistered executors, and direct ad hoc mutation.
- In `execution_patterns`, replace `executor_function` as the sole binding primitive with `executor_id` plus required config/schema/output-contract fields.
- In `traceability`, add `requirement_to_pattern`, `component_to_pattern`, `step_to_executor`, `pattern_to_config_schema`, and `pattern_to_output_contract`.
- In `anti_pattern_detection`, add the CDD/patternless execution triggers.
- In `development_guidelines.adding_new_features`, replace the old "config entry + executable command" rule with "registered executor + validated spec/config + evidence + pass/fail condition."
- In the spec's existing gate registry and appendix sections, add the six `GATE-CFG-*` entries and a migration note only if this is treated as a breaking revision.

## 3. Edit the autonomous delivery template second so the concrete JSON contract matches the spec

- In `critical_constraint.rules`, add hard fail-closed rules for patternless execution, null/blank pattern IDs on executable steps, ad hoc behavior sources, and unregistered executors.
- Add top-level `configuration_driven_development`, `pattern_governance`, and `executor_registry` sections to `NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_2.json`.
- Under `pattern_governance`, fold in the useful ideas from the alternate plan and the evaluation docs: pattern-first mode, pattern creation contract, pre-plan pattern resolution phase, and manual exception policy.
- In `task_analysis`, add required outputs such as `pattern_resolution_decision`, `existing_pattern_match`, `new_pattern_required`, `executor_family`, and `config_driven_feasibility`.
- In `file_manifest`, add pattern provenance fields so each file change declares whether it is a pattern artifact, pattern output, or approved manual exception.
- In `step_contracts`, extend the example steps with the new executable-step fields instead of replacing the section shape.
- In `planning_hierarchy`, add metadata for `implementation_style`, `engine_component_id`, `behavior_spec_artifacts`, `config_schema_artifacts`, `executor_dependencies`, and `approved_extension_slots`.
- In `pipeline_boundary_contract`, add `allowed_execution_inputs`, `forbid_direct_source_mutation_without_pattern`, `forbid_unregistered_executor_invocation`, `forbid_runtime_behavior_override`, and `forbid_prompt_only_behavior_binding`.
- In `execution_patterns`, extend the current block with `allow_null_pattern_id: false`, `require_validated_pattern_before_execution: true`, executor/config/schema requirements, and output-contract/golden-fixture requirements.
- In `traceability`, add the new pattern/executor mappings.
- In `anti_pattern_detection`, add the new patternless/config-violation triggers.
- In `validation_gates`, append the six `GATE-CFG-*` objects and include them in `pipeline_boundary_contract.validation_required_before_execution`.
- In `ai_instructions`, add the pattern-first intake step plus the new `do_not` and `remember` rules.

## 4. Edit the instruction document last, because it is stored as a JSON string

- In `NEWPHASEPLANPROCESS_INSTRUCTION_DOCUMENT_V3_2.json`, replace the current "identify the gap" and "leave blank when documenting a gap" guidance with hard pattern-creation-before-implementation rules.
- Add a front-loaded PATTERN-FIRST and CONFIGURATION-DRIVEN law near the existing `NO IMPLIED BEHAVIOR` section.
- Update the narrative instructions for `task_analysis`, `planning_hierarchy`, `execution_patterns`, `step_contracts`, `pipeline_boundary_contract`, and `validation_gates` so the AI is required to emit pattern-resolution decisions, executor binding, approved behavior surfaces, and the six `GATE-CFG-*` gates.
- Add explicit prohibitions against blank `pattern_id`, prompt-only binding, bespoke scripts where a registered pattern exists, silent pattern composition, and implementation before pattern creation/validation.
- Preserve this file's current storage model: edit the prose logically, then serialize back into the JSON `content` string.

## 5. Run a consistency pass after all edits

- Confirm the spec's `required_sections` match the template's top-level keys.
- Confirm no document still allows null or blank `pattern_id` on executable steps.
- Confirm `execution_patterns` now requires executor/config/schema/output binding everywhere.
- Confirm `file_manifest`, `traceability`, and `anti_pattern_detection` all include pattern-aware provenance.
- Confirm the same `GATE-CFG-001` through `GATE-CFG-006` names appear in the spec, template, and instruction document.
- Confirm any version bump, if chosen, is reflected consistently in metadata, appendix history, and migration notes.

## Corrections applied from the comparison

- Do not hardcode `registry/pattern_registry.yaml` unless there is an intentional decision to introduce a new canonical registry path; the current materials reference `PATTERN_INDEX.yaml`.
- Do not replace `execution_patterns` wholesale; extend it.
- Do not use a separate `GATE_PATTERN_BINDING` name.
- Do not rely on stale field-count math from older gate text.
- Do not skip `file_manifest` changes; they are required by the template-validation memo.
- Do not force a `v3.3.0` release unless that is an explicit goal.
