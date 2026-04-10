# File Analysis Summary

**User:** bill reed (richgwilks@gmail.com)  
**Created:** 4/4/2026 15:45:13  
**Updated:** 4/4/2026 17:09:35  
**Exported:** 4/4/2026 17:15:51  
**Link:** [https://chatgpt.com/g/g-p-69123063d95c819197adfc91fffb052b-plan/c/69d17834-ba34-8333-956b-c2298b8a024e](https://chatgpt.com/g/g-p-69123063d95c819197adfc91fffb052b-plan/c/69d17834-ba34-8333-956b-c2298b8a024e)  

## Response:
I’m pulling the current uploaded files and checking what each one actually contains, not just the filenames.

I have the four files identified. I’m opening the actual bodies now so I can give a clean description of what each one does, instead of guessing from fragments.

Thought for 1m 23s

Here is what each uploaded file is.

**1) `idprocess_NPP.txt`**  
This is not a clean spec or template. It is a **working transcript / build log** from an AI-assisted planning session around Gov\_Reg ID/runtime-authority work. It shows patch failures, creation of `gap_closure_verification_report.json`, repeated reads of the NPP template/spec files, and then generation of a concrete plan file named `gov_reg_runtime_authority_template_plan_v3.json`. In plain English: this file is evidence of the planning process being carried out, not the canonical planning artifact itself.

idprocess\_NPP

idprocess\_NPP

**2) `NEWPHASEPLANPROCESS_INSTRUCTION_DOCUMENT_V3_2.json`**  
This is the **AI filling guide** for the planning system. It tells an AI agent how to complete the template: keep everything explicit, obey `NO IMPLIED BEHAVIOR`, decompose work across system/module/component/execution-packet levels, use pattern-first execution, define mutation types, enforce pipeline boundaries, capture traceability, baseline/drift controls, rollback, canonicalization, merge policy, and platform-awareness. This file is about **how to populate the plan correctly**, not the plan structure itself.

NEWPHASEPLANPROCESS\_INSTRUCTION…

**3) `NEWPHASEPLANPROCESS_TECHNICAL_SPECIFICATION_V3_2.json`**  
This is the **authoritative technical spec / architecture document** for the whole newPhasePlanProcess system. It defines the system purpose, the planning/validation/execution layers, the CLI commands, the gate system, required contract fields, validation guarantees, and the top-level section map the template is expected to follow. It is the semantic reference that explains what the template sections mean and how the framework is supposed to operate.

NEWPHASEPLANPROCESS\_TECHNICAL\_S…

NEWPHASEPLANPROCESS\_TECHNICAL\_S…

**4) `NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_2.json`**  
This is the **actual machine-editable plan template**. It is the skeleton a user or AI fills in to create a concrete project plan. It includes the standard top-level planning sections such as task analysis, assumptions, file manifest, phase plan, self-healing, contracts, validation gates, metrics, planning hierarchy, pipeline boundary contract, execution patterns, mutation model, task intake, traceability, plus the newer v3.2-style sections like `execution_baseline`, `concurrency_control`, `rollback_plan`, `evidence_requirements`, `lifecycle_states`, `state_transitions`, `reconciliation_states`, `canonicalization_contract`, `merge_policy`, and `platform_profile`.

NEWPHASEPLANPROCESS\_AUTONOMOUS\_…

**Important issue in the template**  
The file is named `V3_2`, and the spec/instructions both treat it as v3.2, but the template’s own `template_metadata.version` still says **`3.1.0`**. So the file appears to be a **v3.2-capable template with stale top-level version metadata**. That is a real consistency problem, not just a cosmetic one.

NEWPHASEPLANPROCESS\_AUTONOMOUS\_…

NEWPHASEPLANPROCESS\_INSTRUCTION…

NEWPHASEPLANPROCESS\_TECHNICAL\_S…

**How they fit together**  
The clean relationship is:

*   **Template** = the blank plan structure to fill.
    NEWPHASEPLANPROCESS\_AUTONOMOUS\_…
*   **Instruction document** = rules for how an AI should fill that structure.
    NEWPHASEPLANPROCESS\_INSTRUCTION…
*   **Technical specification** = architecture/semantics explaining what the structure means and how the framework executes and validates it.
    NEWPHASEPLANPROCESS\_TECHNICAL\_S…
*   **`idprocess_NPP.txt`** = a transcript showing this planning system being used to produce a concrete Gov\_Reg-specific plan instance.
    idprocess\_NPP

Net: the three NPP files are the formal set; `idprocess_NPP.txt` is supporting process evidence. The one thing that sticks out immediately is the version drift inside the template file.

## Response:
Thought for 7s

These files are all part of an **error/governance layer**, but they do different jobs:

*   **`Errors in ChatGPT research .txt`** — a **manual defect review** of a planning/CLI loop. It lists concrete runtime-breaking bugs, logic/design flaws, and missing artifacts, then ranks the most critical ones. It is basically an audit memo of what is wrong and why it matters.
    Errors in ChatGPT research
*   **`DOC-CONFIG-DIR-MANIFEST-RUNTIME-ERRORS-1024__DIR_MANIFEST.yaml`** — a **directory manifest** for an error-taxonomy folder. It declares the folder’s identity, ownership, purpose, and expected contents such as `README.md`, `DIR_MANIFEST.yaml`, `.dir_id`, and an error registry. This is inventory/config metadata, not the error content itself.
    DOC-CONFIG-DIR-MANIFEST-RUNTIME…
*   **`DOC_ERROR_CATALOG.md`** — a **human-readable troubleshooting guide**. It organizes 25 documented errors into categories like database, workstream, plugin, spec-resolution, tool-adapter, and configuration errors, with symptoms, root causes, recovery steps, and prevention notes. This is an operator/developer handbook.
    DOC\_ERROR\_CATALOG
*   **`ERROR-TAXONOMY-491__ERROR_TAXONOMY.json`** — a **machine-readable taxonomy** for classifying errors into a small finite set of categories such as parse/shape, format-rule violation, uniqueness/allocation, sync drift, and environment/execution. This is a classification model, not a log.
    ERROR-TAXONOMY-491\_\_ERROR\_TAXON…
*   **`error_registry.json`** — an **actual error event registry / log sample**. It contains timestamped records keyed by IDs, with system type, error type, message, traceback, severity, and context. The entries show repeated Python syntax issues, MQL4 parameter errors, and PowerShell execution-policy failures.
    error\_registry
*   **`copy_error_AGENTS.md`** — despite the name, this is mostly a **repository/agent operating guide**. It describes project structure, approved module locations, setup/test commands, coding style, testing rules, commit/PR expectations, security/config guidance, and Windows-first agent instructions. It is broader than errors; it is a repo behavior contract.
    copy\_error\_AGENTS
*   **`error-codes.md`** — a **simple end-user/developer error code reference**. It defines standardized codes like `E1001`, `E2001`, `E3002` with short descriptions and basic resolution advice. It is lightweight compared with the larger catalog.
    error-codes
*   **`error.contract.v1.json`** — a **JSON schema for a single error object**. It requires `code`, `message`, and `retriable`, and allows optional `details`. This is the contract for how an error payload should be structured.
    error.contract.v1
*   **`SYSTEM_INVARIANTS.md`** — a **hard-governance document** defining non-negotiable invariants for ACMS + MINI\_PIPE. It covers isolation, ground truth, pattern governance, consistency, resource limits, anti-pattern detection, and audit/verification, with explicit enforcement and violation responses. This is the strongest policy/control document in the set.
    SYSTEM\_INVARIANTS
*   **`DOC-CONFIG-OPERATION-TAXONOMY-332__operation_taxonomy.yaml`** — a **machine taxonomy for operation kinds**, not errors. It collapses many raw operation labels into 15 universal categories like initialization, discovery, analysis, validation, execution, persistence, synchronization, maintenance, and reporting, with mappings, regex patterns, and context rules.
    DOC-CONFIG-OPERATION-TAXONOMY-3…

How they fit together:

*   **Governance/rules:** `SYSTEM_INVARIANTS.md`, `copy_error_AGENTS.md`
    SYSTEM\_INVARIANTS
    copy\_error\_AGENTS
*   **Taxonomies/contracts:** `ERROR-TAXONOMY-491__ERROR_TAXONOMY.json`, `error.contract.v1.json`, `DOC-CONFIG-OPERATION-TAXONOMY-332__operation_taxonomy.yaml`
    ERROR-TAXONOMY-491\_\_ERROR\_TAXON…
    error.contract.v1
    DOC-CONFIG-OPERATION-TAXONOMY-3…
*   **Human reference docs:** `DOC_ERROR_CATALOG.md`, `error-codes.md`, `Errors in ChatGPT research .txt`
    DOC\_ERROR\_CATALOG
    error-codes
    Errors in ChatGPT research
*   **Runtime/config records:** `error_registry.json`, `DOC-CONFIG-DIR-MANIFEST-RUNTIME-ERRORS-1024__DIR_MANIFEST.yaml`
    error\_registry
    DOC-CONFIG-DIR-MANIFEST-RUNTIME…

Net: this bundle is not one thing. It is a mixed stack of **error policy, error classification, error reference material, runtime error data, and repo operating rules**.

## Response:
I’m mapping each invariant in `SYSTEM_INVARIANTS.md` against the current NPP template and the instruction/spec files, then I’ll call out what is already covered versus what is absent.

Thought for 1m 16s

Focused on `SYSTEM_INVARIANTS.md`, here is the direct mapping against `NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_2.json`, with the instruction doc used to confirm intended semantics.

Bottom line
-----------

The template already covers a lot of the **execution-safety mechanics**: worktree isolation, file scopes, ground-truth levels, validation gates, rollback, evidence, retries, lifecycle states, and concurrency.

NEWPHASEPLANPROCESS\_AUTONOMOUS\_…

NEWPHASEPLANPROCESS\_AUTONOMOUS\_…

NEWPHASEPLANPROCESS\_AUTONOMOUS\_…

What it does **not** yet cover well are the more ACMS-specific **governance chokepoints**:

*   explicit clean-git preflight on base branch,
*   global protected paths,
*   mandatory manual review hooks,
*   explicit audit trail contract,
*   anti-pattern detector registry,
*   patch ledger state machine,
*   explicit per-task `pattern_id` governance,
*   explicit run-status contract.
    SYSTEM\_INVARIANTS

Invariant-by-invariant mapping
------------------------------

| SYSTEM\_INVARIANT | Status in NPP template | Where it exists now | What is missing / where it should go |
| --- | --- | --- | --- |
| **I-1 Branch Isolation** | **Present** | `worktree_isolation.enabled`, `base_ref`, worktree naming, create/execute/merge lifecycle, and rule `No direct commits to base_ref; merge via squash-merge`.
NEWPHASEPLANPROCESS\_AUTONOMOUS\_…

NEWPHASEPLANPROCESS\_AUTONOMOUS\_…

 | Good enough. |
| **I-2 Clean State Entry** | **Partial** | Merge precondition says `no uncommitted changes in {worktree_path}`.

NEWPHASEPLANPROCESS\_AUTONOMOUS\_…

 | Missing the invariant’s stronger rule: clean state on **main/base branch before run starts**. Best place: add `preflight` under `worktree_isolation`, or extend `execution_baseline` with `clean_git_required`, `git_status_command`, `on_dirty_action`. |
| **I-3 Run Directory Containment** | **Partial** | NPP strongly standardizes outputs under `.state/...` and evidence paths under `.state/evidence/...`.

NEWPHASEPLANPROCESS\_INSTRUCTION…

NEWPHASEPLANPROCESS\_AUTONOMOUS\_…

 | The exact invariant `.acms_runs/{run_id}/` is absent. Best place: add a new top-level `run_artifact_policy` section, or extend `evidence_requirements` with `run_root`, `allowed_artifact_roots`, `leak_detection`. |
| **GT-1 Test-Backed Changes** | **Present** | `ground_truth_levels`, unit/integration/e2e levels, phase transition enforcement, test gates, and instruction requirement to set ground-truth by phase/step.

NEWPHASEPLANPROCESS\_AUTONOMOUS\_…

NEWPHASEPLANPROCESS\_INSTRUCTION…

 | Good. |
| **GT-2 Schema Compliance** | **Present** | `schema_version`, validation gates, `schema_validate` required check in worktree validation, and instruction that gates must pass before execution.

NEWPHASEPLANPROCESS\_AUTONOMOUS\_…

NEWPHASEPLANPROCESS\_AUTONOMOUS\_…

NEWPHASEPLANPROCESS\_INSTRUCTION…

 | Good. |
| **GT-3 Observable Success** | **Present** | Step postconditions, gate `expect_files`, evidence directories, step evidence, and `evidence_requirements`.

NEWPHASEPLANPROCESS\_AUTONOMOUS\_…

NEWPHASEPLANPROCESS\_AUTONOMOUS\_…

 | Good enough, though an explicit `success_requires_evidence=true` flag would make it harder to weaken later. |
| **PG-1 Patternless Work Forbidden** | **Partial** | `execution_patterns.required_for_task_kinds = true`, `pattern_registry_reference`, `task_pattern_mappings`; instructions say every task kind should map to a pattern.

NEWPHASEPLANPROCESS\_AUTONOMOUS\_…

NEWPHASEPLANPROCESS\_INSTRUCTION…

 | ACMS invariant is stricter: every **task** has a `pattern_id`. NPP maps **task kinds**, not individual steps/tasks. Best fix: add `pattern_id` field to each execution packet / step contract, or add `execution_packet_pattern_mappings`. |
| **PG-2 Pattern Spec Completeness** | **Missing / weak** | Only the existence of pattern mappings and registry reference is modeled.

NEWPHASEPLANPROCESS\_AUTONOMOUS\_…

 | Missing validation that a pattern has spec, schema, executor, registry entry, guardrails. Best place: extend `execution_patterns` with `required_pattern_components`, `pattern_validation_gate`, `registry_check_command`. |
| **PG-3 Guardrails Non-Bypassable** | **Missing / weak** | NPP enforces file scopes and validation gates, but there is no explicit “guardrails cannot be bypassed” contract.

NEWPHASEPLANPROCESS\_AUTONOMOUS\_…

 | Best place: add `guardrail_policy` under `execution_patterns` or `worktree_isolation`, with `bypass_allowed: false`, `override_requires_manual_review: true`. |
| **C-1 Gap-Task Consistency** | **Partial** | `traceability` maps requirement → module → component → execution packet.

NEWPHASEPLANPROCESS\_AUTONOMOUS\_…

NEWPHASEPLANPROCESS\_INSTRUCTION…

 | NPP has no explicit `gap_id` concept in template. Best place: extend `traceability` with `gap_to_execution_packet`, or add `gap_id` to step contracts/execution packets. |
| **C-2 Run Status Coherence** | **Partial** | `lifecycle_states`, `state_transitions`, `metrics` summaries, reconciliation states.

NEWPHASEPLANPROCESS\_AUTONOMOUS\_…

NEWPHASEPLANPROCESS\_AUTONOMOUS\_…

 | Missing an explicit `run_status.json` contract and coherence validator. Best place: add new top-level `run_status_contract` with required fields, transition rules, and validation command. |
| **C-3 Ledger Integrity** | **Partial** | NPP has `lifecycle_states`, `state_transitions`, file mutation evidence, before/after hashes, diff/apply logs.

NEWPHASEPLANPROCESS\_AUTONOMOUS\_…

NEWPHASEPLANPROCESS\_AUTONOMOUS\_…

 | Missing a real **patch ledger state machine**. Best place: add top-level `patch_ledger` or `mutation_ledger` with allowed transitions and atomic-write/lock requirements. |
| **RL-1 Bounded Execution** | **Partial to strong** | Step `timeout_sec`, `retries`, ground-truth level timeouts, gate timeouts, self-healing budgets.

NEWPHASEPLANPROCESS\_AUTONOMOUS\_…

 | Missing explicit limits for max file size / max files / max LOC. Best place: add `resource_limits` top-level section, and optionally per-pattern/per-step overrides. |
| **RL-2 Scope Boundaries** | **Present** | `file_manifest`, conflict analysis, step `file_scope.allowed/forbidden/read_only_paths`, worktree file-scope enforcement.

NEWPHASEPLANPROCESS\_AUTONOMOUS\_…

NEWPHASEPLANPROCESS\_AUTONOMOUS\_…

NEWPHASEPLANPROCESS\_AUTONOMOUS\_…

 | Good. |
| **RL-3 Protected Paths Inviolate** | **Missing / weak** | NPP has step-level `forbidden_paths` and `read_only_paths`, but no global protected path list.

NEWPHASEPLANPROCESS\_AUTONOMOUS\_…

 | Best place: add top-level `protected_paths` section, plus a mandatory validation gate and worktree runtime enforcement. |
| **AP-1 Known Failures Detected** | **Partial** | `self_healing.failure_types`, convergence detection, escalation, bounded retries.

NEWPHASEPLANPROCESS\_AUTONOMOUS\_…

NEWPHASEPLANPROCESS\_AUTONOMOUS\_…

 | Missing explicit anti-pattern triggers like hallucinated success, empty-file creation, over-engineering, worktree contamination. Best place: new `anti_pattern_detection` section plus gate(s). |
| **AP-2 Failure Transparency** | **Partial** | Attempt evidence requires timestamp, phase, step\_id, failure\_type, action\_taken, result, abort\_reason.

NEWPHASEPLANPROCESS\_AUTONOMOUS\_…

 | Missing explicit requirement for stack trace / stderr preservation / no-silent-failure policy. Best place: extend `self_healing.attempt_evidence.required_fields_in_result_json` and add `failure_logging_policy`. |
| **AP-3 Recovery Paths Exist** | **Partial** | `rollback_plan`, step `rollback_strategy`, self-healing failure types and actions, `NOT_AUTOMATABLE` guidance.

NEWPHASEPLANPROCESS\_INSTRUCTION…

NEWPHASEPLANPROCESS\_INSTRUCTION…

NEWPHASEPLANPROCESS\_AUTONOMOUS\_…

 | Missing an explicit table mapping **every failure mode** to a required recovery path. Best place: add top-level `recovery_matrix` or extend `self_healing` with `required_recovery_for_failure_types`. |
| **V-1 Audit Trail Complete** | **Partial** | NPP has evidence chains, metrics JSONL sink, gate evidence, step evidence.

NEWPHASEPLANPROCESS\_AUTONOMOUS\_…

NEWPHASEPLANPROCESS\_TECHNICAL\_S…

 | Missing one explicit audit-trail object for every execution event. Best place: add top-level `audit_trail` with `path`, `required_fields`, `append_mode`, `atomic_append`. |
| **V-2 Validation Gates Enforced** | **Present** | `pipeline_boundary_contract.validation_required_before_execution`, `validation_gates`, worktree validation checks before merge.

NEWPHASEPLANPROCESS\_INSTRUCTION…

NEWPHASEPLANPROCESS\_AUTONOMOUS\_…

NEWPHASEPLANPROCESS\_AUTONOMOUS\_…

 | Good. |
| **V-3 Manual Review Hooks** | **Missing / weak** | `merge_policy.review_required = true` exists, and instructions say use human review for `NOT_AUTOMATABLE`.

NEWPHASEPLANPROCESS\_TECHNICAL\_S…

NEWPHASEPLANPROCESS\_INSTRUCTION…

 | Missing explicit `requires_manual_review: true` trigger at step/gate level for high-risk ops. Best place: add this field to `step_contracts`, `validation_gates`, and optionally `merge_policy.manual_review_triggers`. |

What is already clearly aligned
-------------------------------

These invariants already have solid NPP equivalents:

*   **I-1 Branch isolation** → `worktree_isolation` is a real match.
    NEWPHASEPLANPROCESS\_AUTONOMOUS\_…
*   **GT-1 / GT-2 / GT-3 Ground truth and evidence** → covered by `ground_truth_levels`, gates, evidence, and step contracts.
    NEWPHASEPLANPROCESS\_AUTONOMOUS\_…
*   **RL-2 Scope boundaries** → strongly covered by step `file_scope` and worktree enforcement.
    NEWPHASEPLANPROCESS\_AUTONOMOUS\_…
*   **V-2 Validation gates enforced** → strongly covered by `pipeline_boundary_contract` and `validation_gates`.
    NEWPHASEPLANPROCESS\_INSTRUCTION…
    NEWPHASEPLANPROCESS\_AUTONOMOUS\_…

What is only partially aligned
------------------------------

These exist in spirit, but not at invariant-strength:

*   **I-2 Clean state entry**
*   **I-3 Run directory containment**
*   **PG-1 Patternless work forbidden**
*   **C-1 Gap-task consistency**
*   **C-2 Run status coherence**
*   **C-3 Ledger integrity**
*   **RL-1 Bounded execution**
*   **AP-1 / AP-2 / AP-3**
*   **V-1 Audit trail complete**  
    These all need either a stronger field model or a dedicated gate.
    SYSTEM\_INVARIANTS
    NEWPHASEPLANPROCESS\_AUTONOMOUS\_…

What is genuinely missing
-------------------------

These are the biggest holes if you want the NPP template to encode `SYSTEM_INVARIANTS.md` faithfully:

1.  **Global protected paths**  
    Add top-level:
    ```
    "protected_paths": {
      "paths": [".git/objects/**", ".git/refs/heads/main", "schemas/*.schema.json"],
      "violation_action": "halt_and_rollback",
      "validator_command": "..."
    }
    ```
2.  **Manual review hooks**  
    Add to `step_contracts` and `validation_gates`:
    ```
    "requires_manual_review": false,
    "manual_review_triggers": [],
    "approval_evidence": []
    ```
3.  **Audit trail contract**  
    Add top-level:
    ```
    "audit_trail": {
      "path": ".state/audit/pattern_audit.jsonl",
      "required_fields": ["pattern_id","step_id","start_ts","end_ts","inputs","outputs","status"],
      "atomic_append": true
    }
    ```
4.  **Patch / mutation ledger state machine**  
    Add top-level:
    ```
    "mutation_ledger": {
      "states": ["created","validated","queued","applied","verified","committed","rolled_back","rejected","failed"],
      "allowed_transitions": [...],
      "lock_required": true,
      "evidence_path": ".state/ledger/"
    }
    ```
5.  **Anti-pattern detector section**  
    Add top-level:
    ```
    "anti_pattern_detection": {
      "triggers": ["hallucinated_success","empty_artifact","worktree_contamination","complexity_exceeded"],
      "actions": ["halt","self_heal","escalate"],
      "validator_command": "..."
    }
    ```
6.  **Preflight clean-state contract**  
    Best added under `worktree_isolation` or `execution_baseline`:
    ```
    "preflight": {
      "clean_base_branch_required": true,
      "git_status_command": "git status --porcelain",
      "on_dirty_action": "fail_or_stash_prompt"
    }
    ```
7.  **Per-step pattern binding**  
    If you want true ACMS-style invariant parity, `execution_patterns` is not enough. Add `pattern_id` to each execution packet / step contract.

Best single-sentence assessment
-------------------------------

`NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_2.json` already captures the **execution mechanics** behind many of the invariants, but it does **not yet encode the full governance-strength invariant layer** that `SYSTEM_INVARIANTS.md` demands. The biggest missing pieces are explicit **preflight cleanliness, protected paths, audit trail, anti-pattern detection, mutation-ledger state machine, and manual-review hooks**.

SYSTEM\_INVARIANTS

NEWPHASEPLANPROCESS\_AUTONOMOUS\_…

I can turn this into a patch plan showing the exact JSON sections and fields to add to the template.

## Response:
I’m pulling the exact template sections now so I can give you the concrete patch targets instead of general advice.

Thought for 57s

Here is the concrete patch plan for hardening `NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_2.json` against `SYSTEM_INVARIANTS.md`.

What is already covered well enough
-----------------------------------

These invariants already have a real home in the template/spec/instructions and do not need a new top-level section:

**I-1 Branch Isolation**  
Keep it in `worktree_isolation`. The spec already defines isolated git worktrees, merge discipline, and “No direct commits to base\_ref.”

NEWPHASEPLANPROCESS\_TECHNICAL\_S…

**GT-1 Test-Backed Changes / GT-2 Schema Compliance / GT-3 Observable Success**  
These are already spread across `ground_truth_levels`, `validation_gates`, `step_contracts`, and `evidence_requirements`. The spec requires schema validation, step contracts, rollback completeness, verification completeness, and evidence-driven validation.

NEWPHASEPLANPROCESS\_TECHNICAL\_S…

**RL-2 Scope Boundaries**  
This already belongs in `step_contracts.file_scope` and worktree enforcement. The template/spec already enforce allowed/forbidden/read-only paths and worktree file-scope enforcement.

**V-2 Validation Gates Enforced**  
This already belongs in `pipeline_boundary_contract` plus `validation_gates`. The instructions explicitly say execution must only use the declared plan input and required validation gates must pass first.

NEWPHASEPLANPROCESS\_INSTRUCTION…

Existing sections that should be extended
-----------------------------------------

### 1) `worktree_isolation`

Add what is missing for **I-2 Clean State Entry** and strengthen **I-1**.

What exists now: isolated worktrees, base ref, lifecycle, concurrency rules.

NEWPHASEPLANPROCESS\_TECHNICAL\_S…

What to add:

```
"worktree_isolation": {
  "...existing": "...",
  "preflight": {
    "clean_base_branch_required": true,
    "base_branch_name": "main",
    "clean_check_command": "git status --porcelain",
    "on_dirty_action": "fail_or_require_manual_cleanup",
    "forbid_untracked_sensitive_files": true
  },
  "post_run_verification": {
    "verify_base_ref_unchanged_before_merge": true,
    "verify_no_direct_writes_to_base_ref": true
  }
}
```

Why: `SYSTEM_INVARIANTS.md` requires clean entry on `main` before run start, not just a clean worktree during merge.

SYSTEM\_INVARIANTS

* * *

### 2) `execution_baseline`

Use this to encode **I-2 Clean State Entry** and part of **I-3 Run Directory Containment**.

What exists now: commit hash, dependencies, scripts. The instructions already say baseline is for drift detection and rollback reference.

What to add:

```
"execution_baseline": {
  "...existing": "...",
  "git_state": {
    "required_clean": true,
    "check_commands": [
      "git rev-parse HEAD",
      "git status --porcelain"
    ],
    "must_match_base_ref": true
  },
  "artifact_root_baseline": {
    "allowed_roots": [
      ".state/",
      ".worktrees/"
    ]
  }
}
```

Why: this is the most natural place to record “what state must be true before execution begins.”

NEWPHASEPLANPROCESS\_INSTRUCTION…

* * *

### 3) `step_contracts`

This is the main place to encode missing pattern governance and manual review rules.

What exists now: purpose, inputs, outputs, invariants, preconditions, postconditions, file\_scope, failure\_modes, evidence, ground\_truth\_level, timeout, retries, rollback\_strategy, idempotency, backup\_requirements, mutation guards, before/after hash controls. The instructions also explicitly say steps should reference `pattern_id` when using a pattern.

What to add to every step:

```
"step_contracts": {
  "PH-XX": {
    "STEP-YYY": {
      "...existing": "...",
      "pattern_id": "",
      "pattern_parameters": {},
      "requires_manual_review": false,
      "manual_review_reason": "",
      "high_risk_operation": false,
      "path_scope": {
        "protected_paths_respected": true
      },
      "runtime_limits": {
        "max_files_touched": null,
        "max_total_loc_changed": null,
        "max_file_size_mb": null
      },
      "audit_fields": {
        "emit_audit_record": true,
        "audit_event_type": "step_execution"
      },
      "failure_logging": {
        "require_error_message": true,
        "require_stack_trace": true,
        "require_retry_history": true
      }
    }
  }
}
```

Why:

*   **PG-1 Patternless Work Forbidden** needs a real `pattern_id` field, not just task-kind mappings.
*   **V-3 Manual Review Hooks** belongs at the step level for high-risk actions.
    SYSTEM\_INVARIANTS
*   **RL-1 Bounded Execution** needs per-step caps beyond timeout.
    SYSTEM\_INVARIANTS
*   **AP-2 Failure Transparency** needs explicit logging requirements per step.
    SYSTEM\_INVARIANTS

* * *

### 4) `execution_patterns`

This is where to encode **PG-1**, **PG-2**, and **PG-3** properly.

What exists now: `pattern_registry_reference`, `required_for_task_kinds`, `task_pattern_mappings`. The instructions already require pattern-first execution.

NEWPHASEPLANPROCESS\_INSTRUCTION…

What to add:

```
"execution_patterns": {
  "...existing": "...",
  "pattern_validation": {
    "require_pattern_id_per_step": true,
    "required_pattern_components": [
      "spec_file",
      "schema_file",
      "executor_function",
      "pattern_index_entry",
      "guardrails_block"
    ],
    "validation_command": "python scripts/validate_pattern_registry.py"
  },
  "guardrail_policy": {
    "bypass_allowed": false,
    "runtime_override_allowed": false,
    "missing_guardrails_action": "fail_closed"
  }
}
```

Why:

*   `SYSTEM_INVARIANTS.md` requires every task to have a `pattern_id`, every pattern to have spec/schema/executor/index/guardrails, and guardrails to be non-bypassable.
    SYSTEM\_INVARIANTS

* * *

### 5) `traceability`

Extend this to cover **C-1 Gap-Task Consistency**.

What exists now: requirement→module, module→component, component→execution packet.

NEWPHASEPLANPROCESS\_INSTRUCTION…

What to add:

```
"traceability": {
  "...existing": "...",
  "gap_to_execution_packet": [],
  "deferred_gaps": [],
  "gap_closure_validation": {
    "require_all_gaps_resolved_or_deferred": true,
    "validation_command": "python scripts/validate_gap_traceability.py"
  }
}
```

Why: `SYSTEM_INVARIANTS.md` explicitly requires gap→task→result tracking. The current template does not model gaps directly.

SYSTEM\_INVARIANTS

* * *

### 6) `lifecycle_states` and `state_transitions`

Use these to absorb **C-2 Run Status Coherence** and **C-3 Ledger Integrity**, but they need explicit specialization.

What exists now: generic task/artifact lifecycle states and allowed/invalid transitions.

What to add:

```
"lifecycle_states": {
  "...existing": "...",
  "run_status_states": [
    "pending",
    "running",
    "blocked",
    "failed",
    "completed",
    "rolled_back"
  ],
  "mutation_ledger_states": [
    "created",
    "validated",
    "queued",
    "applied",
    "verified",
    "committed",
    "rejected",
    "failed",
    "rolled_back"
  ]
},
"state_transitions": {
  "...existing": "...",
  "run_status_allowed": [],
  "mutation_ledger_allowed": [],
  "lock_required_for_mutation_ledger": true,
  "atomic_update_required": true
}
```

Why: the current sections are generic, but `SYSTEM_INVARIANTS.md` requires explicit run-status coherence and a patch-ledger state machine with atomic locked transitions.

SYSTEM\_INVARIANTS

* * *

### 7) `rollback_plan`

Use this to strengthen **AP-3 Recovery Paths Exist**.

What exists now: global, per-phase, and per-step rollback procedures. The instructions already require safe/idempotent rollback and manual recovery for non-automatable steps.

NEWPHASEPLANPROCESS\_INSTRUCTION…

What to add:

```
"rollback_plan": {
  "...existing": "...",
  "failure_mode_to_recovery_mapping": [
    {
      "failure_mode": "TEST_FAIL",
      "recovery_patterns": ["self_heal", "rollback"]
    },
    {
      "failure_mode": "SCHEMA_VIOLATION",
      "recovery_patterns": ["fix_schema", "fail_fast"]
    }
  ],
  "fail_if_no_recovery_path": true
}
```

Why: the current template supports rollback, but not the invariant that every recognized failure mode must have a defined recovery path.

* * *

### 8) `evidence_requirements`

Use this to strengthen **GT-3 Observable Success** and **V-1 Audit Trail Complete**.

What exists now: phase and step evidence requirements. The instructions explicitly call for required artifacts proving success.

NEWPHASEPLANPROCESS\_INSTRUCTION…

What to add:

```
"evidence_requirements": {
  "...existing": "...",
  "audit_trail": {
    "path": ".state/audit/pattern_audit.jsonl",
    "required_fields": [
      "pattern_id",
      "step_id",
      "start_timestamp",
      "end_timestamp",
      "inputs",
      "outputs",
      "guardrail_results",
      "success_failure_status"
    ],
    "atomic_append": true
  },
  "observable_success_requirements": {
    "require_exit_code": true,
    "require_expected_files": true,
    "require_validation_proof": true,
    "require_ledger_update": true
  }
}
```

Why: `SYSTEM_INVARIANTS.md` explicitly requires audit trail completeness and observable success evidence.

SYSTEM\_INVARIANTS

* * *

### 9) `merge_policy`

Use this to partially cover **V-3 Manual Review Hooks**.

What exists now: strategy, squash, review\_required. The instructions already mention review requirements here.

NEWPHASEPLANPROCESS\_INSTRUCTION…

What to add:

```
"merge_policy": {
  "...existing": "...",
  "manual_review_triggers": [
    "bulk_rename_over_threshold",
    "schema_change",
    "pattern_addition",
    "protected_path_request"
  ],
  "approval_evidence_required": true
}
```

Why: review is already modeled here, but only globally and weakly. High-risk triggers need to be enumerated.

SYSTEM\_INVARIANTS

New top-level sections that should be added
-------------------------------------------

These are the real missing pieces.

### A) `protected_paths`

This is the cleanest place for **RL-3 Protected Paths Inviolate**.

Add:

```
"protected_paths": {
  "paths": [
    ".git/objects/**",
    ".git/refs/heads/main",
    "PATTERN_INDEX.yaml",
    "schemas/*.schema.json",
    "SYSTEM_INVARIANTS.md"
  ],
  "enforcement": {
    "runtime_block": true,
    "post_run_verification": true,
    "violation_action": "halt_and_rollback"
  }
}
```

Why: step-level forbidden paths are not enough. This needs to be global and non-overrideable.

SYSTEM\_INVARIANTS

* * *

### B) `run_artifact_policy`

This is where **I-3 Run Directory Containment** belongs.

Add:

```
"run_artifact_policy": {
  "run_root_pattern": ".acms_runs/{run_id}/",
  "all_artifacts_must_be_under_run_root": true,
  "leak_detection_command": "python scripts/check_artifact_containment.py",
  "on_leak_action": "move_to_run_root_and_warn"
}
```

Why: the current template standardizes `.state/...` evidence but does not express a single run root invariant.

SYSTEM\_INVARIANTS

* * *

### C) `anti_pattern_detection`

This is where **AP-1 Known Failures Detected** should live.

Add:

```
"anti_pattern_detection": {
  "enabled": true,
  "triggers": [
    "hallucinated_success",
    "planning_loop_over_threshold",
    "empty_implementation_artifact",
    "complexity_limit_exceeded",
    "worktree_contamination"
  ],
  "checkpoints": [
    "post_task",
    "post_phase",
    "pre_commit"
  ],
  "actions": {
    "critical": "halt",
    "recoverable": "self_heal_or_escalate"
  }
}
```

Why: the tech spec has a general failure-mode checker, but the template does not currently encode anti-pattern detection as a first-class contract.

* * *

### D) `run_status_contract`

This is the cleanest place for **C-2 Run Status Coherence**.

Add:

```
"run_status_contract": {
  "path": ".state/run_status.json",
  "required_fields": [
    "run_id",
    "current_phase",
    "phase_counts",
    "task_counts",
    "status",
    "timestamps"
  ],
  "coherence_checks": [
    "task_counts_match_actual_tasks",
    "phase_progression_valid",
    "timestamps_monotonic",
    "status_matches_reality"
  ],
  "validation_command": "python scripts/validate_run_status.py"
}
```

Why: current lifecycle modeling is too generic for the explicit invariant.

SYSTEM\_INVARIANTS

* * *

### E) `mutation_ledger`

This is the cleanest place for **C-3 Ledger Integrity**.

Add:

```
"mutation_ledger": {
  "path": ".state/ledger/mutation_ledger.jsonl",
  "states": [
    "created",
    "validated",
    "queued",
    "applied",
    "verified",
    "committed",
    "rejected",
    "failed",
    "rolled_back"
  ],
  "allowed_transitions": [
    {"from": "created", "to": "validated"},
    {"from": "validated", "to": "queued"},
    {"from": "queued", "to": "applied"},
    {"from": "applied", "to": "verified"},
    {"from": "verified", "to": "committed"},
    {"from": "created", "to": "rejected"},
    {"from": "queued", "to": "failed"},
    {"from": "applied", "to": "rolled_back"}
  ],
  "atomic_update_required": true,
  "lock_required": true,
  "validation_command": "python scripts/validate_mutation_ledger.py"
}
```

Why: `SYSTEM_INVARIANTS.md` defines a specific ledger state machine that the current template does not model directly.

SYSTEM\_INVARIANTS

Priority order
--------------

If you do this in the right order, patch these first:

1.  **`protected_paths`**
2.  **`run_artifact_policy`**
3.  **`step_contracts.pattern_id` + `execution_patterns.pattern_validation`**
4.  **`run_status_contract`**
5.  **`mutation_ledger`**
6.  **`anti_pattern_detection`**
7.  Extend `worktree_isolation`, `execution_baseline`, `evidence_requirements`, `merge_policy`

That order closes the biggest governance holes first. The template already handles execution mechanics; what it lacks is the hard fail-closed governance layer.

If you want, I’ll turn this into a literal RFC-6902 patch plan against the template JSON.



---
Powered by [ChatGPT Exporter](https://www.chatgptexporter.com)