# Configuration-Driven Development Evaluation

**User:** bill reed (richgwilks@gmail.com)  
**Created:** 4/4/2026 22:03:52  
**Updated:** 4/4/2026 22:37:33  
**Exported:** 4/4/2026 22:51:11  
**Link:** [https://chatgpt.com/g/g-p-69123063d95c819197adfc91fffb052b-plan/c/69d1d084-f7a8-8329-83ac-ac813b981e76](https://chatgpt.com/g/g-p-69123063d95c819197adfc91fffb052b-plan/c/69d1d084-f7a8-8329-83ac-ac813b981e76)  

## Response:
I’m checking whether the template merely supports this style or actually forces it, and whether that requirement exists in the template, the spec, the instructions, or only in your pasted design text.

There’s enough in the files to make a call now: the system clearly pushes pattern-first, plan-as-canonical-input execution. I’m checking whether it also mandates the stronger “static engine + external spec controls behavior” model for the actual implementation itself.

Thought for 1m 13s

Verdict: **not fully**.

The current v3.2 template **does force configuration-driven planning and pattern-governed execution**, but it does **not yet force full Configuration-Driven Development** in the stronger sense from your pasted text, where a **stable generic engine** performs work and **external configuration/specification fully determines behavior**.

What it already forces:

*   The plan itself is treated as a canonical machine-readable contract. The instruction document says each plan is a self-contained JSON document that serves as the canonical contract between planning and execution, and it requires every rule, gate, and contract to be expressible as configuration entry + executable command + evidence + pass/fail.
    NEWPHASEPLANPROCESS\_INSTRUCTION…
*   It explicitly bans ad hoc execution inputs. The instructions require a `pipeline_boundary_contract` whose `input_exclusivity_rule` makes the declared plan document the **only** permissible execution input, preventing ad hoc or mutated inputs.
    NEWPHASEPLANPROCESS\_INSTRUCTION…
*   It is explicitly **pattern-first**. The instruction document says, “Do not invent bespoke scripts for common tasks,” and instead requires mapping task kinds to reusable patterns from a pattern registry.
*   The template hardens that requirement structurally: `required_for_task_kinds` is `true`, `require_pattern_id_per_step` is `true`, and guardrails are fail-closed with `bypass_allowed: false`, `runtime_override_allowed: false`, and `missing_guardrails_action: "fail_closed"`.
*   Step instructions say that if a task uses a pattern, it should reference its `pattern_id` and pass `pattern_parameters` **instead of ad hoc scripts**.
    NEWPHASEPLANPROCESS\_INSTRUCTION…
*   The technical spec describes `execution_patterns` as a mechanism to “reduce variability and enforce consistent execution by referencing pattern contracts.”

So the template already enforces this much:

**plan-driven orchestration**  
→ **pattern-bound task execution**  
→ **guardrailed, fail-closed execution**  
→ **no informal, freehand task execution**

That is real progress toward your goal.

Why it still falls short of full Configuration-Driven Development:

*   The template enforces **pattern use**, but not that the underlying implementation must be a **fixed universal engine** whose behavior is entirely driven by external configuration. It still allows patterns to point to an `executor_function`, which means behavior can still live in custom imperative code behind the pattern.
    NEWPHASEPLANPROCESS\_AUTONOMOUS\_…
*   The instruction document still allows a missing pattern to be documented as a gap: when no pattern exists, set `pattern_id` to `null` and flag that a new pattern is needed. That is weaker than “no implementation may begin until a pattern exists.”
    NEWPHASEPLANPROCESS\_INSTRUCTION…
*   The system is clearly an **Autonomous Project Planning & Execution Framework** with a generic plan execution engine, but that generic engine is for **executing plans**, not for guaranteeing that each developed process inside the product uses an engine/spec separation model.
    NEWPHASEPLANPROCESS\_TECHNICAL\_S…

Bluntly: the template currently forces **configuration-driven governance of work**, not **configuration-driven architecture of the resulting processes**.

That distinction matters.

Your pasted text defines a stronger rule set:

*   engine is stable
*   behavior lives in external spec/config
*   code changes are minimized
*   debugging shifts from code to config/spec

The template does not yet make that a mandatory architectural invariant for the processes being built.

The attached planning text in your library is actually closer to the stronger model than the template is. It defines patterns as **contracts for file/script archetypes**, includes config-loading rules, and treats uniqueness as parameters plus constrained slots rather than freeform structure.

Planning file

So the real answer is:

**The template partially enforces Configuration-Driven Development, but only at the planning/execution-control layer. It does not yet force it at the implementation-architecture layer.**

To make it truly force CDD, the template would need a few hard additions:

*   A top-level invariant that says: **process behavior must be implemented through declarative spec/config consumed by a fixed engine or approved pattern executor; bespoke imperative implementations are forbidden unless explicitly exempted**.
*   A rule that says: **if no pattern exists, create and validate the pattern before the task can enter executable state**. Right now it only says to flag the gap.
    NEWPHASEPLANPROCESS\_INSTRUCTION…
*   A required distinction in each step between:
    *   engine/executor
    *   external spec/config
    *   parameters
    *   evidence of config-to-behavior mapping
*   A validation gate that rejects steps whose behavior is implemented as direct ad hoc logic instead of pattern + config + guarded executor.
*   A pattern schema that requires:
    *   executor identity
    *   config schema
    *   parameter schema
    *   allowed mutation surface
    *   invariants
    *   validation commands
*   A pipeline rule that AI tools may only execute tasks through the pattern executor wrapper, never directly.

So the clean summary is:

**Current state:** pattern-first, plan-as-contract, fail-closed, anti–ad hoc execution.  
**Missing state:** mandatory engine-vs-spec separation for the actual processes being built.

If you want, I’ll turn that into a precise list of template/spec/instruction-document modifications to make Configuration-Driven Development a hard constraint instead of a soft tendency.

## Response:
I’m pulling the exact sections that need to change so the modification list is tied to the current v3.2 structure, not a generic redesign.

Thought for 1m 8s

Use this as a **breaking-change patch scope for v3.3.0**.

The reason this has to be a breaking change is that the current system already enforces pattern-first execution and fail-closed guardrails, but the instructions still allow “no pattern exists, flag the gap,” which leaves room for patternless implementation.

1\. Template changes
--------------------

**File:** `NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_2.json`

### A. Strengthen `critical_constraint`

Add these rules under `critical_constraint.rules`:

*   `All AUTOMATABLE behavior MUST be executed through a registered executor consuming an approved external specification/configuration artifact.`
*   `Inline bespoke task logic is FORBIDDEN unless the step is explicitly marked PATTERN_CREATION or NOT_AUTOMATABLE.`
*   `Executable steps MUST NOT have null or blank pattern_id.`
*   `If no approved pattern exists, the plan MUST create and validate the pattern before any implementation step begins.`
*   `Behavioral variability MUST live in spec/config/parameters, not in ad hoc executor code or prompt-only instructions.`

This is the core shift from “pattern-preferred” to “configuration-driven required.”

### B. Add a new top-level section

Add a mandatory top-level section:

```
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

### C. Harden `execution_patterns`

The current template already has `required_for_task_kinds: true`, `require_pattern_id_per_step: true`, and fail-closed guardrails.  
Modify it to remove loopholes.

Add or require:

```
"execution_patterns": {
  "pattern_registry_reference": "",
  "required_for_task_kinds": true,
  "allow_null_pattern_id": false,
  "require_validated_pattern_before_execution": true,
  "missing_pattern_action": "fail_closed_create_pattern_task",
  "task_pattern_mappings": [
    {
      "task_kind": "",
      "pattern_id": "",
      "pattern_version": "",
      "executor_id": "",
      "spec_file": "",
      "config_schema_file": "",
      "parameter_schema_file": "",
      "output_contract_ref": "",
      "validation_command": "",
      "golden_test_fixture": ""
    }
  ],
  "pattern_validation": {
    "require_pattern_id_per_step": true,
    "required_pattern_components": [
      "spec_file",
      "config_schema_file",
      "parameter_schema_file",
      "executor_id",
      "pattern_index_entry",
      "guardrails_block",
      "output_contract_ref",
      "golden_test_fixture"
    ],
    "require_executor_registration": true,
    "require_behavior_binding_proof": true,
    "validation_command": "python scripts/validate_pattern_registry.py",
    "expect_exit_code": 0
  },
  "guardrail_policy": {
    "bypass_allowed": false,
    "runtime_override_allowed": false,
    "missing_guardrails_action": "fail_closed"
  }
}
```

### D. Add a mandatory `executor_registry` section

```
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

This is needed because a pattern without a bound executor is exactly the “spec with no engine backing it” failure mode seen in your historical error taxonomy.

Error Taxonomy Across Historica…

### E. Expand `pipeline_boundary_contract`

The current section only locks execution to the plan artifact.  
Add fields that lock execution to registered config/spec surfaces too.

```
"pipeline_boundary_contract": {
  "planning_stage_output": "",
  "execution_stage_input": "",
  "validation_required_before_execution": [],
  "input_exclusivity_rule": "",
  "allowed_execution_inputs": [
    "plan_json",
    "registered_pattern_spec",
    "schema_validated_config"
  ],
  "forbid_direct_source_mutation_without_pattern": true,
  "forbid_unregistered_executor_invocation": true,
  "forbid_runtime_behavior_override": true
}
```

### F. Expand `step_contracts`

Current step contracts include `pattern_id` and `pattern_parameters`, but they do not force engine/spec separation.  
Make these fields mandatory for every executable step:

```
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
"implementation_mode": "PATTERN_EXECUTION",
"engine_invariants": [],
"behavior_binding_proof": {
  "command": "",
  "evidence": ""
},
"allowed_extension_slots": [],
"bespoke_logic_allowed": false
```

Add enum for `implementation_mode`:

*   `PATTERN_EXECUTION`
*   `PATTERN_CREATION`
*   `NOT_AUTOMATABLE`

Rule:

*   `PATTERN_EXECUTION` steps require full executor/config/spec binding.
*   `PATTERN_CREATION` steps are the only steps allowed to create a new pattern.
*   `NOT_AUTOMATABLE` requires manual routing and no direct AI freehand execution.

### G. Expand `planning_hierarchy`

At module and component level, add:

*   `implementation_style`
*   `engine_component_id`
*   `behavior_spec_artifacts`
*   `config_schema_artifacts`
*   `executor_dependencies`
*   `approved_extension_slots`

Mandatory rule:

*   every component must declare whether it is `CONFIGURATION_DRIVEN`, `HYBRID`, or `MANUAL_ONLY`
*   `HYBRID` must trigger manual review
*   `MANUAL_ONLY` must be justified

### H. Expand `traceability`

Add:

*   `requirement_to_pattern`
*   `component_to_pattern`
*   `step_to_executor`
*   `pattern_to_config_schema`
*   `pattern_to_output_contract`

This makes CDD auditable instead of rhetorical.

### I. Expand `anti_pattern_detection`

Current anti-patterns do not target ad hoc implementation directly.

NEWPHASEPLANPROCESS\_AUTONOMOUS\_…

Add triggers:

*   `patternless_execution`
*   `null_pattern_id_on_executable_step`
*   `unregistered_executor_invocation`
*   `inline_behavior_logic_outside_extension_slot`
*   `runtime_override_of_guardrailed_parameters`
*   `spec_without_engine_binding`
*   `executor_without_config_schema`
*   `freehand_script_created_where_pattern_exists`

### J. Add new validation gates

Add these gate definitions to `validation_gates` and make them mandatory in `pipeline_boundary_contract.validation_required_before_execution`:

*   `GATE-CFG-001` Pattern completeness  
    Verifies every executable step has `pattern_id`, `pattern_version`, `executor_id`, `spec_file`, `config_schema_file`.
*   `GATE-CFG-002` Engine/spec separation  
    Verifies behavior is supplied by external spec/config, not encoded only in step prose or custom commands.
*   `GATE-CFG-003` No ad hoc execution  
    Rejects executable steps using bespoke commands when a registered pattern exists.
*   `GATE-CFG-004` Registered executor only  
    Rejects unregistered executor references.
*   `GATE-CFG-005` Pattern-first gap resolution  
    Rejects plans that attempt implementation before pattern creation/validation when no pattern exists.
*   `GATE-CFG-006` Behavior-binding proof  
    Verifies executor + spec + config + expected outputs are mechanically linked.

2\. Technical specification changes
-----------------------------------

**File:** `NEWPHASEPLANPROCESS_TECHNICAL_SPECIFICATION_V3_2.json`

### A. Add a new design principle

Under `executive_summary.design_principles`, add:

*   `CONFIGURATION-DRIVEN DEVELOPMENT: Executable behavior must be determined by approved external specifications/configurations consumed by registered executors; ad hoc imperative task logic is prohibited by default.`

### B. Add new key capabilities

Under `executive_summary.key_capabilities`, add:

*   `Registered executor model with pattern-to-executor binding`
*   `Configuration schema validation for every executable pattern`
*   `Pattern creation before implementation when no pattern exists`
*   `Behavior-binding proof from requirement -> pattern -> config -> executor -> evidence`
*   `Ad hoc implementation detection and rejection`

### C. Add a new architecture component set

In `architecture.system_layers`, add components for:

*   `Pattern Registry`
*   `Executor Registry`
*   `Configuration Schema Validator`
*   `Behavior Binding Validator`
*   `Pattern Creation Workflow`
*   `CDD Enforcement Gates`

The current spec describes a generic plan execution engine and pattern-first execution, but it needs an explicit CDD control plane to make the rule architectural, not advisory.

NEWPHASEPLANPROCESS\_TECHNICAL\_S…

### D. Redefine `execution_patterns` in the spec

Change its stated purpose from “reducing variability” to:

*   `mandatory execution path for all automatable task kinds`
*   `registered binding between task kind, external spec/config, and approved executor`
*   `blocking mechanism for patternless implementation`

### E. Expand `step_contract.required_fields`

The current spec’s required field set is too weak for CDD enforcement.

NEWPHASEPLANPROCESS\_TECHNICAL\_S…

Add these as required for executable steps:

*   `pattern_id`
*   `pattern_version`
*   `executor_binding`
*   `behavior_spec`
*   `implementation_mode`
*   `behavior_binding_proof`
*   `bespoke_logic_allowed`
*   `allowed_extension_slots`

### F. Add a dedicated “Configuration-Driven Development” section

Add a new major section with definitions for:

*   executor
*   pattern
*   config schema
*   parameter schema
*   behavior-binding proof
*   extension slot
*   pattern creation step
*   executable step
*   ad hoc logic
*   exception / variance path

### G. Add a new validator and gate registry entries

Extend the gate registry with the six `GATE-CFG-*` gates above, and document:

*   purpose
*   exact checks
*   failure impact
*   expected evidence

### H. Add a “pattern creation lifecycle” procedure

Add a normative procedure:

1.  detect no matching pattern
2.  create pattern spec
3.  create config schema
4.  register executor binding
5.  create golden fixture
6.  pass pattern validation gates
7.  only then allow implementation steps

### I. Update development guidelines

The current guidance says features must be expressible as config + command + evidence + pass/fail.

NEWPHASEPLANPROCESS\_TECHNICAL\_S…

Strengthen it to:

*   `Feature must be expressible as registered executor + validated spec/config + evidence + pass/fail condition.`
*   `If no pattern exists, first create a pattern package and validate it.`
*   `No plan may schedule PATTERN_EXECUTION against a task kind lacking a validated pattern.`
*   `Spec-only pattern definitions are invalid unless an executor binding exists.`

That last line is directly justified by the historical failure you already documented: YAML/spec with no Python engine backing it.

Error Taxonomy Across Historica…

### J. Add validation guarantees

Add these to `validation_guarantees`:

*   `No executable step is patternless`
*   `No executable behavior depends on prompt-only or prose-only logic`
*   `All executable behavior is bound to registered executors`
*   `All configuration-driven steps have schema-validated config inputs`
*   `Pattern gaps are resolved before implementation begins`

3\. Instruction document changes
--------------------------------

**File:** `NEWPHASEPLANPROCESS_INSTRUCTION_DOCUMENT_V3_2.json`

### A. Replace the weak pattern-gap rule

Current wording says: if no pattern exists, identify the gap so one can be added.  
Replace it with:

*   `If no pattern exists, you MUST create a dedicated pattern-creation phase before any implementation phase.`
*   `You MUST NOT leave pattern_id null for any executable step.`
*   `You MUST NOT plan freehand implementation as a substitute for a missing pattern.`

### B. Add a new general principle

Add:

*   **Configuration-driven development** — Every automatable behavior must be implemented through a registered executor consuming approved external specification/configuration artifacts. Keep business variability in config/spec/parameters. Do not encode task-specific behavior primarily in bespoke executor logic or prompt prose.

### C. Modify `task_analysis`

Require the AI to determine:

*   whether an existing pattern already covers the requested work
*   whether the request requires `PATTERN_CREATION`
*   what executor family should own the behavior
*   what configuration/spec artifacts will control the behavior

Add mandatory outputs:

*   `pattern_resolution_decision`
*   `existing_pattern_match`
*   `new_pattern_required`
*   `executor_family`
*   `config_driven_feasibility`

### D. Modify `planning_hierarchy`

Require each module/component to document:

*   `implementation_style`
*   `engine component`
*   `behavior spec artifacts`
*   `config schema artifacts`
*   `approved extension slots`
*   `pattern dependencies`

### E. Rewrite `execution_patterns` instructions

Replace the current “pattern\_id may be null if no pattern exists” instruction with:

*   `pattern_id is mandatory for every executable step`
*   `null pattern_id is allowed only for PATTERN_CREATION steps`
*   `when no pattern exists, create a pattern package first`
*   `a valid pattern package must include spec_file, config_schema_file, parameter_schema_file, executor_id, guardrails, output_contract_ref, and golden_test_fixture`

### F. Rewrite `step_contracts` instructions

Current guidance says to use `pattern_id` and `pattern_parameters` instead of ad hoc scripts if a task uses a pattern.

NEWPHASEPLANPROCESS\_INSTRUCTION…

Strengthen it to:

*   `Every executable step MUST use a pattern.`
*   `Every executable step MUST declare executor_binding and behavior_spec.`
*   `Set implementation_mode to PATTERN_EXECUTION unless the step exists solely to create/register a new pattern.`
*   `Set bespoke_logic_allowed to false by default.`
*   `Only declare free-form logic inside approved extension slots defined by the pattern.`
*   `If extension slots are used, describe them explicitly and cap them with runtime limits and validation proof.`

### G. Expand `pipeline_boundary_contract` instructions

Add:

*   execution may consume only:
    *   the approved plan JSON
    *   registered pattern specs
    *   schema-valid config instances
*   direct source mutation by unregistered tools is forbidden
*   runtime prompt edits that change behavior outside config/spec are forbidden

### H. Expand `validation_gates` instructions

Require the AI to include the `GATE-CFG-*` gates in every plan where executable work exists.

### I. Expand `do_not`

Add these prohibitions to the instruction doc and the template’s `ai_instructions.do_not`:

*   `Do not leave pattern_id blank on executable steps`
*   `Do not propose bespoke scripts where a registered pattern exists`
*   `Do not treat prose instructions as a substitute for config/schema`
*   `Do not start implementation before pattern creation/validation when no pattern exists`
*   `Do not bind behavior through runtime prompt overrides`
*   `Do not create unregistered executors`
*   `Do not hide unique behavior in arbitrary code outside approved extension slots`

### J. Expand `remember`

Add:

*   `All automatable behavior = executor + spec/config + schema + evidence`
*   `Pattern gap => create pattern first, then implement`
*   `Executable step without validated pattern = invalid plan`
*   `Configuration is the behavior surface; code is the engine surface`

4\. Minimal policy outcome after these changes
----------------------------------------------

After this patch set, the system rule becomes:

*   if a pattern exists, AI must use it
*   if a pattern does not exist, AI must create it first
*   AI cannot proceed with freehand executable logic as a workaround
*   executable behavior must be externally specified and mechanically validated
*   exceptions must be explicit, rare, and routed through `NOT_AUTOMATABLE` or formal variance handling

That is what turns Configuration-Driven Development into a **hard constraint**.

The single most important fix is this one:

**Replace “if no pattern exists, flag the gap” with “if no pattern exists, create and validate the pattern before implementation; otherwise fail closed.”**

That one change removes the loophole.

If you want, I’ll turn this into an RFC-6902 patch plan targeting all three JSON files.

## Response:
I’ve checked the actual v3.2 files. The main difference from my earlier answer is that some pattern-first scaffolding is already present, so the remaining work is narrower and more specific.

Thought for 19s

These current versions confirm the gap is **real but narrower** than before.

You already have several CDD-adjacent pieces in place:

*   the template already requires `execution_patterns.required_for_task_kinds: true`, `pattern_validation.require_pattern_id_per_step: true`, and fail-closed guardrails in `guardrail_policy`
*   step contracts already carry `pattern_id` and `pattern_parameters` fields
*   the instruction document already pushes “pattern-first execution” and bans bypassable guardrails, but it still says that when no pattern exists, the AI should identify the gap so one can be added, and it explicitly allows `pattern_id` to be left blank when documenting a gap
    NEWPHASEPLANPROCESS\_INSTRUCTION…
*   the technical specification still frames `execution_patterns` as reducing variability and enforcing consistency, not as the only legal execution path for automatable work
    NEWPHASEPLANPROCESS\_TECHNICAL\_S…

So the exact problem is:

**the system currently enforces pattern-awareness, but not pattern-mandatory, executor-bound, config/schema-driven implementation.**

Below is the corrected modification list against the **actual current files**.

* * *

1\. Template: precise modifications
-----------------------------------

**File:** `NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_2.json`

NEWPHASEPLANPROCESS\_AUTONOMOUS\_…

### 1.1 Strengthen `critical_constraint.rules`

Keep the section. Add these rules:

*   `All AUTOMATABLE behavior MUST execute through a registered executor consuming approved external specification/configuration artifacts.`
*   `Executable steps MUST use implementation_mode = PATTERN_EXECUTION unless they are explicitly PATTERN_CREATION or NOT_AUTOMATABLE.`
*   `Null, blank, or placeholder pattern_id values are FORBIDDEN on executable steps.`
*   `If no approved pattern exists, implementation MUST pause until a pattern package is created, validated, and registered.`
*   `Behavioral variability MUST live in spec/config/parameters, not in ad hoc step prose, prompt-only instructions, or unregistered executor logic.`

This is the single most important template change.

### 1.2 Add a new top-level section

Add a new required top-level section:

```
"configuration_driven_development": {
  "enabled": true,
  "enforcement_mode": "fail_closed",
  "engine_spec_separation_required": true,
  "behavior_sources_allowed": [
    "registered_pattern_spec",
    "validated_config_instance",
    "validated_parameter_object",
    "schema_validated_defaults"
  ],
  "behavior_sources_forbidden": [
    "inline_ad_hoc_logic",
    "runtime_prompt_override",
    "manual_command_substitution",
    "unregistered_executor"
  ],
  "missing_pattern_policy": {
    "implementation_blocked": true,
    "required_action": "create_pattern_first"
  },
  "validator_command": "python scripts/validate_configuration_driven_development.py --plan-file {plan_file}",
  "expect_exit_code": 0,
  "evidence": ".state/evidence/configuration_driven_development_validation.json"
}
```

### 1.3 Harden `execution_patterns`

Do not replace the section. Extend the existing one.

Add these fields:

```
"allow_null_pattern_id": false,
"require_validated_pattern_before_execution": true,
"missing_pattern_action": "fail_closed_create_pattern_task",
"require_executor_binding_per_pattern": true,
"require_config_schema_per_pattern": true,
"require_parameter_schema_per_pattern": true,
"require_output_contract_per_pattern": true,
"require_golden_fixture_per_pattern": true
```

Expand each item in `task_pattern_mappings` to include:

```
{
  "task_kind": "",
  "pattern_id": "",
  "pattern_version": "",
  "executor_id": "",
  "spec_file": "",
  "config_schema_file": "",
  "parameter_schema_file": "",
  "output_contract_ref": "",
  "golden_test_fixture": "",
  "constraints": {}
}
```

Replace `required_pattern_components`:

Current list:

*   `spec_file`
*   `schema_file`
*   `executor_function`
*   `pattern_index_entry`
*   `guardrails_block`

Replace with:

*   `spec_file`
*   `config_schema_file`
*   `parameter_schema_file`
*   `executor_id`
*   `pattern_index_entry`
*   `guardrails_block`
*   `output_contract_ref`
*   `golden_test_fixture`

Also replace `executor_function` with `executor_id`. That change matters because a bare function reference is too weak; it does not create a real registered execution surface.

### 1.4 Add a new top-level `executor_registry`

Add:

```
"executor_registry": {
  "registered_executors": [
    {
      "executor_id": "",
      "executor_entrypoint": "",
      "supported_pattern_ids": [],
      "supported_config_schema_versions": [],
      "supported_parameter_schema_versions": [],
      "determinism_requirements": [],
      "forbidden_capabilities": []
    }
  ],
  "validation_command": "python scripts/validate_executor_registry.py --plan-file {plan_file}",
  "expect_exit_code": 0,
  "evidence": ".state/evidence/executor_registry_validation.json"
}
```

### 1.5 Expand `pipeline_boundary_contract`

Current fields are too weak. They only bind execution to the plan document.

Add:

```
"allowed_execution_inputs": [
  "plan_json",
  "registered_pattern_spec",
  "validated_config_instance",
  "validated_parameter_object"
],
"forbid_direct_source_mutation_without_pattern": true,
"forbid_unregistered_executor_invocation": true,
"forbid_runtime_behavior_override": true,
"forbid_prompt_only_behavior_binding": true
```

### 1.6 Expand `step_contracts`

Keep existing fields. Add these required fields for executable steps:

```
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
"allowed_extension_slots": [],
"bespoke_logic_allowed": false,
"behavior_binding_proof": {
  "command": "",
  "expect_exit_code": 0,
  "evidence": ""
}
```

Allowed enum for `implementation_mode`:

*   `PATTERN_EXECUTION`
*   `PATTERN_CREATION`
*   `NOT_AUTOMATABLE`

Rules:

*   `PATTERN_EXECUTION` requires full executor/config/spec binding
*   `PATTERN_CREATION` is the only legal mode when no pattern exists yet
*   `NOT_AUTOMATABLE` means no direct autonomous implementation path

### 1.7 Expand `planning_hierarchy`

Add to module/component records:

*   `implementation_style`
*   `engine_component_id`
*   `behavior_spec_artifacts`
*   `config_schema_artifacts`
*   `executor_dependencies`
*   `approved_extension_slots`

Allowed `implementation_style`:

*   `CONFIGURATION_DRIVEN`
*   `HYBRID`
*   `MANUAL_ONLY`

Rules:

*   `HYBRID` requires manual review
*   `MANUAL_ONLY` requires explicit justification

### 1.8 Expand `traceability`

Add arrays:

*   `requirement_to_pattern`
*   `component_to_pattern`
*   `step_to_executor`
*   `pattern_to_config_schema`
*   `pattern_to_output_contract`

### 1.9 Expand `anti_pattern_detection.triggers`

Add:

*   `patternless_execution`
*   `null_pattern_id_on_executable_step`
*   `unregistered_executor_invocation`
*   `spec_without_engine_binding`
*   `executor_without_config_schema`
*   `inline_behavior_logic_outside_extension_slot`
*   `runtime_override_of_guardrailed_parameters`
*   `freehand_script_created_where_pattern_exists`

### 1.10 Add new validation gates

Add these to `validation_gates`:

*   `GATE-CFG-001` Pattern completeness
*   `GATE-CFG-002` Engine/spec separation
*   `GATE-CFG-003` No ad hoc execution
*   `GATE-CFG-004` Registered executor only
*   `GATE-CFG-005` Pattern-first gap resolution
*   `GATE-CFG-006` Behavior-binding proof

Also add them to `pipeline_boundary_contract.validation_required_before_execution`.

* * *

2\. Instruction document: precise modifications
-----------------------------------------------

**File:** `NEWPHASEPLANPROCESS_INSTRUCTION_DOCUMENT_V3_2.json`

NEWPHASEPLANPROCESS\_INSTRUCTION…

This file contains the **largest loophole**.

### 2.1 Replace the current pattern-gap rule

Current instruction:

*   “If no pattern exists, identify the gap so one can be added.”
*   “When no pattern exists, set `pattern_id` to `null` and flag that a new pattern is needed.”
*   step-contract guidance also allows `pattern_id` to be left blank when documenting a gap
    NEWPHASEPLANPROCESS\_INSTRUCTION…

Replace all of that with:

*   `If no pattern exists, you MUST create a PATTERN_CREATION phase before any implementation phase.`
*   `You MUST NOT leave pattern_id null or blank for any executable step.`
*   `You MUST NOT use freehand implementation as a substitute for a missing pattern.`
*   `Pattern creation and validation MUST complete before PATTERN_EXECUTION steps may appear in the plan.`

### 2.2 Add a new general principle

Add:

*   **Configuration-driven development** – Every automatable behavior must be implemented through a registered executor consuming approved external specification/configuration artifacts. Keep business variability in config/spec/parameters. Do not encode task-specific behavior primarily in bespoke executor logic or step prose.

### 2.3 Update `task_analysis`

Add required outputs:

*   `pattern_resolution_decision`
*   `existing_pattern_match`
*   `new_pattern_required`
*   `executor_family`
*   `config_driven_feasibility`
*   `approved_behavior_surface`

### 2.4 Update `execution_patterns`

Replace the current “null pattern is allowed when documenting a gap” instruction with:

*   `pattern_id is mandatory for every executable step`
*   `null pattern_id is allowed only for PATTERN_CREATION steps`
*   `every pattern must define executor_id, spec_file, config_schema_file, parameter_schema_file, output_contract_ref, and golden_test_fixture`
*   `executor_function is not sufficient as the sole binding primitive; use executor_id`

### 2.5 Update `step_contracts`

Strengthen the current wording.

Add:

*   `Every executable step MUST use implementation_mode = PATTERN_EXECUTION unless it is PATTERN_CREATION or NOT_AUTOMATABLE.`
*   `Every executable step MUST declare executor_binding and behavior_spec.`
*   `Set bespoke_logic_allowed to false by default.`
*   `Only place free-form logic in approved extension slots defined by the pattern.`
*   `If extension slots are used, they must be declared and bounded by runtime limits and validation proof.`

### 2.6 Update `pipeline_boundary_contract`

Add instructions that execution may consume only:

*   the approved plan JSON
*   registered pattern specs
*   schema-valid config instances
*   schema-valid parameter objects

And explicitly forbid:

*   prompt-only behavior overrides
*   unregistered executors
*   direct ad hoc source mutation

### 2.7 Expand `ai_instructions.do_not`

Add:

*   `Do not leave pattern_id blank on executable steps`
*   `Do not propose bespoke scripts where a registered pattern exists`
*   `Do not treat prose instructions as a substitute for config/schema`
*   `Do not start implementation before pattern creation/validation when no pattern exists`
*   `Do not bind behavior through runtime prompt overrides`
*   `Do not use unregistered executors`
*   `Do not hide unique behavior in arbitrary code outside approved extension slots`

### 2.8 Expand `ai_instructions.remember`

Add:

*   `All automatable behavior = executor + spec/config + schema + evidence`
*   `Pattern gap => create pattern first, then implement`
*   `Executable step without validated pattern = invalid plan`
*   `Configuration is the behavior surface; code is the engine surface`

* * *

3\. Technical specification: precise modifications
--------------------------------------------------

**File:** `NEWPHASEPLANPROCESS_TECHNICAL_SPECIFICATION_V3_2.json`

NEWPHASEPLANPROCESS\_TECHNICAL\_S…

### 3.1 Add a new design principle

Under `executive_summary.design_principles`, add:

*   `CONFIGURATION-DRIVEN DEVELOPMENT: Executable behavior must be determined by approved external specifications/configurations consumed by registered executors; ad hoc imperative task logic is prohibited by default.`

### 3.2 Add new key capabilities

Under `executive_summary.key_capabilities`, add:

*   `Registered executor model with pattern-to-executor binding`
*   `Configuration schema validation for every executable pattern`
*   `Pattern creation before implementation when no pattern exists`
*   `Behavior-binding proof from requirement -> pattern -> config -> executor -> evidence`
*   `Ad hoc implementation detection and rejection`

### 3.3 Reframe `execution_patterns`

Current wording says it reduces variability and enforces consistency.

NEWPHASEPLANPROCESS\_TECHNICAL\_S…

Replace that purpose with:

*   `mandatory execution path for all automatable task kinds`
*   `registered binding between task kind, external spec/config, and approved executor`
*   `blocking mechanism for patternless implementation`

### 3.4 Expand `data_structures.step_contract.required_fields`

Add:

*   `implementation_mode`
*   `executor_binding`
*   `behavior_spec`
*   `allowed_extension_slots`
*   `bespoke_logic_allowed`
*   `behavior_binding_proof`

Also change `pattern_id` semantics from “reference” to “mandatory binding for executable steps”.

### 3.5 Add a new architecture subsection

Under architecture, add components for:

*   `Pattern Registry`
*   `Executor Registry`
*   `Configuration Schema Validator`
*   `Behavior Binding Validator`
*   `Pattern Creation Workflow`
*   `CDD Enforcement Gates`

### 3.6 Add new validation guarantees

Add:

*   `No executable step is patternless`
*   `No executable behavior depends on prompt-only or prose-only logic`
*   `All executable behavior is bound to registered executors`
*   `All configuration-driven steps have schema-validated config inputs`
*   `Pattern gaps are resolved before implementation begins`

### 3.7 Add a “pattern creation lifecycle”

Add a normative sequence:

1.  detect missing pattern
2.  create pattern spec
3.  create config schema
4.  create parameter schema
5.  register executor binding
6.  create golden fixture
7.  pass pattern validation gates
8.  only then allow implementation steps

### 3.8 Update `development_guidelines.adding_new_features.requirements`

Current requirement is still:

*   `Feature must be expressible as: config entry + executable command + evidence artifact + pass/fail condition`
    NEWPHASEPLANPROCESS\_TECHNICAL\_S…

Replace with:

*   `Feature must be expressible as: registered executor + validated spec/config + evidence artifact + pass/fail condition`
*   `If no pattern exists, a pattern package must be created and validated before implementation proceeds`
*   `Spec-only pattern definitions are invalid unless an executor binding exists`

That last rule directly closes the “spec exists but no engine backs it” failure mode.

### 3.9 Add the six `GATE-CFG-*` gates to the spec gate registry

Document:

*   purpose
*   checks
*   required evidence
*   failure impact

* * *

4\. What does **not** need to be changed
----------------------------------------

Because these parts are already present, they only need extension, not replacement:

*   `pattern_id` in step contracts
*   `required_for_task_kinds: true`
*   `require_pattern_id_per_step: true`
*   fail-closed guardrail policy
*   audit trail fields tied to `pattern_id` and `step_id`

So the real job is not “add pattern-first.”  
That is already there.

The real job is:

**remove the remaining escape hatches that still permit patternless or executor-unbound implementation.**

5\. The single most important fix
---------------------------------

This is the one sentence that matters most:

**Replace every instruction that says “if no pattern exists, flag the gap” with “if no pattern exists, create and validate the pattern first; otherwise fail closed.”**

That is the exact change that turns CDD into a hard constraint.

Next step should be an **RFC-6902 patch plan against these three exact v3.2 files**.



---
Powered by [ChatGPT Exporter](https://www.chatgptexporter.com)