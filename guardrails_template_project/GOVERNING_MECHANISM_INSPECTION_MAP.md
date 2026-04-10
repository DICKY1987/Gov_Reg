# Governing Mechanism Inspection Map

This document lists the files and folders that should receive closer inspection when assembling the pattern-first, configuration-driven governing mechanism discussed in this chat.

## 1. Highest-Value Runtime Candidates

These are the strongest implementation candidates because they already look like working runtime artifacts rather than planning-only material.

| Path | Why inspect it |
|---|---|
| `C:\Users\richg\Gov_Reg\MINI_PIPE\patterns\PATTERN_INDEX.yaml` | Closest existing pattern registry. Use it to study pattern structure, guardrail fields, and audit settings. |
| `C:\Users\richg\Gov_Reg\MINI_PIPE\patterns\atomic_create.spec.yaml` | Concrete pattern spec example. Good source for spec shape and allowed operations. |
| `C:\Users\richg\Gov_Reg\MINI_PIPE\patterns\pytest_green.spec.yaml` | Second pattern example for validation-oriented behavior. |
| `C:\Users\richg\Gov_Reg\MINI_PIPE\patterns\schemas\pattern_spec.schema.json` | Best current schema candidate for validating pattern spec files. |
| `C:\Users\richg\Gov_Reg\MINI_PIPE\src\acms\guardrails.py` | Main enforcement candidate for pattern checks, path scope, and anti-pattern blocking. |
| `C:\Users\richg\Gov_Reg\MINI_PIPE\src\cli\validate_everything.py` | Closest existing whole-run validation entrypoint. |
| `C:\Users\richg\Gov_Reg\MINI_PIPE\src\minipipe\executor.py` | Closest executor/orchestrator candidate, even though it is not the exact `execute_pattern.py` named by the template. |
| `C:\Users\richg\Gov_Reg\MINI_PIPE\src\acms\controller.py` | Produces run artifacts such as `run_status.json`; useful for runtime state wiring. |
| `C:\Users\richg\Gov_Reg\MINI_PIPE\schemas\acms\run_status.schema.json` | Best schema candidate for run status enforcement. |
| `C:\Users\richg\Gov_Reg\MINI_PIPE\tests` | Best source for expected runtime behavior and proof that existing guardrails logic is real. |

## 2. Template and Plan-Compiler Scaffolding

These paths look like the strongest source for template-side validation and plan assembly.

| Path | Why inspect it |
|---|---|
| `C:\Users\richg\Gov_Reg\newPhasePlanProcess\01260207201000001223_schemas` | Contains plan schemas, including v3.0.0 plan schema artifacts. |
| `C:\Users\richg\Gov_Reg\newPhasePlanProcess\01260207201000001225_scripts` | Contains many plan validators already referenced by the template, such as `validate_step_contracts`, `validate_file_manifest`, and `validate_gates`. |
| `C:\Users\richg\Gov_Reg\newPhasePlanProcess\01260207201000001288_sections` | Contains section-by-section instruction files and unified section JSONs; useful for plan decomposition and section contracts. |
| `C:\Users\richg\Gov_Reg\newPhasePlanProcess\.state` | Existing state/evidence directory candidate for plan-side runtime output layout. |
| `C:\Users\richg\Gov_Reg\01260207201000001312_validators` | Shared validator folder; worth checking for reusable validation patterns and naming conventions. |

## 3. Reference and Process Libraries

These paths look more like reference libraries than direct runtime code, but they may contain reusable process definitions.

| Path | Why inspect it |
|---|---|
| `C:\Users\richg\Gov_Reg\RUNTIME\process_steps\PROCESS_STEP_LIB\schemas` | Large schema library describing end-to-end process steps, registry usage, and run-status expectations. |
| `C:\Users\richg\Gov_Reg\RUNTIME\process_steps\PROCESS_STEP_LIB\tools` | Candidate source for reusable process-step tooling patterns. |
| `C:\Users\richg\ALL_AI\REFERENCE\patterns\SUB_PATTERNS\cli\DOC-PAT-CLI-PATTERN-ORCHESTRATE-001__pattern_orchestrate.py` | Closest reference to a pattern orchestration CLI. |
| `C:\Users\richg\ALL_AI\RUNTIME\process_steps\PROCESS_STEP_LIB\schemas` | Parallel reference set under `ALL_AI`; useful for cross-checking if the Gov_Reg copy is stale. |

## 4. Current Repo Files That Must Stay Aligned

These files define the target contract and should be reread while inspecting the external candidates above.

| Path | Why inspect it |
|---|---|
| `C:\Users\richg\Gov_Reg\guardrails_template_project\NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_2.json` | Defines required sections, gate names, and runtime artifact paths. |
| `C:\Users\richg\Gov_Reg\guardrails_template_project\NEWPHASEPLANPROCESS_INSTRUCTION_DOCUMENT_V3_2.json` | Defines the pattern-first and configuration-driven execution law. |
| `C:\Users\richg\Gov_Reg\guardrails_template_project\NEWPHASEPLANPROCESS_TECHNICAL_SPECIFICATION_V3_2.json` | Defines semantics and required validator/gate behavior. |
| `C:\Users\richg\Gov_Reg\guardrails_template_project\SYSTEM_INVARIANTS.md` | Defines non-negotiable invariants for patternless work, observable success, and runtime state coherence. |

## 5. Exact Gaps Still Missing

These exact files were searched for and not found in the inspected roots. They should remain explicit follow-up targets:

- `execute_pattern.py`
- `validate_pattern_completeness.py`
- `validate_engine_spec_separation.py`
- `validate_no_adhoc_execution.py`
- `validate_executor_registration.py`
- `validate_pattern_first_gap_resolution.py`
- `validate_behavior_binding_proof.py`

## 6. Suggested Inspection Order

1. Inspect `MINI_PIPE\patterns`, `MINI_PIPE\src\acms`, and `MINI_PIPE\src\cli` first.
2. Inspect `newPhasePlanProcess\01260207201000001225_scripts` and `01260207201000001223_schemas` second.
3. Use `RUNTIME` and `ALL_AI` process libraries only as reference layers after the runtime and template candidates are understood.
4. Reconcile all findings back against the current template repo before adopting anything.
