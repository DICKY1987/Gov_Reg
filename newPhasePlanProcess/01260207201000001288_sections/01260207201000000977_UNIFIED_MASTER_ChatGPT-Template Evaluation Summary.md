# Template Evaluation Summary

**User:** bill reed (richgwilks@gmail.com)  
**Created:** 1/27/2026 19:36:03  
**Updated:** 1/27/2026 22:14:43  
**Exported:** 1/27/2026 22:59:52  
**Link:** [https://chatgpt.com/g/g-p-69123063d95c819197adfc91fffb052b-plan/c/697967f2-962c-8330-8f77-3f0594315eac](https://chatgpt.com/g/g-p-69123063d95c819197adfc91fffb052b-plan/c/697967f2-962c-8330-8f77-3f0594315eac)  

## Response:
Thought for 4m 9s

According to a document from **2026-01-27**, the **UNIFIED MASTER TEMPLATE v1.0** is a strong _conceptual_ consolidation of your five source systems, but it is **not yet mechanically executable/validatable** in the way your `plan.schema.v2.3.0.json` + `plan_cli.py` stack expects.

UNIFIED\_MASTER\_TEMPLATE\_V1\_PART1

What’s strong (keep)
--------------------

*   **“No implied behavior” is explicit and enforceable** (command + expected output + exit code) as a first-class constraint.
    UNIFIED\_MASTER\_TEMPLATE\_V1\_PART1
*   **Machine-indexed TOC with required sections** is a good pattern for deterministic completeness checks.
    UNIFIED\_MASTER\_TEMPLATE\_V1\_PART1
    UNIFIED\_MASTER\_TEMPLATE\_V1\_PART1
*   **Ground-truth validation levels (L0–L5)** are specified as commands + timeouts + exit codes + evidence paths, which is exactly the right “mechanical” posture.
    UNIFIED\_MASTER\_TEMPLATE\_V1\_PART1
*   **Phase contracts + artifact manifest + global gates**: the template explicitly centralizes file-touch truth into `artifacts[]` and cross-checks via a manifest and gates. That’s the right governance model.
    UNIFIED\_MASTER\_TEMPLATE\_V1\_PART2
    UNIFIED\_MASTER\_TEMPLATE\_V1\_PART2
    UNIFIED\_MASTER\_TEMPLATE\_V1\_PART2
*   The feature-analysis doc correctly frames why each source template exists and what this unified template is trying to capture.
    UNIFIED\_MASTERtemplate\_feature\_…

Hard blockers (fix first)
-------------------------

### 1) The “.yml” files are not valid YAML

They contain Markdown formatting and fenced code blocks (e.g., `**Template Version:**`, \`\`\`yaml fences). A YAML parser will not accept this as a pure YAML document.

UNIFIED\_MASTER\_TEMPLATE\_V1\_PART1

**Fix:** choose one:

*   **Option A (recommended):** make the canonical template **Markdown** (`.md`) and keep **YAML blocks** inside it.
*   **Option B:** make it **pure YAML** (no Markdown, no fences), and generate a rendered `.md` separately.

### 2) Phase contract structure does not match `plan.schema.v2.3.0.json`

Your template’s “Phase Contract v1.0” requires fields like `phase`, `tasks`, `artifacts`, `validations`, etc.

UNIFIED\_MASTER\_TEMPLATE\_V1\_PART2

But the schema’s `phase_contract` requires **`inputs`, `outputs`, `preconditions`, `postconditions`** (and uses `command_invocation` objects for validations).

NEWPHASEPLANPROCESS\_plan.schema…

**Fix:** either:

*   rewrite the phase-contract portion to **emit the schema’s `phase_contract` shape**, or
*   treat your Phase Contract v1.0 as a higher-level spec and build a **deterministic compiler** that converts it into the schema shape.

### 3) Gate IDs + evidence paths don’t align with the schema

*   Template gate IDs are like `GATE-STRUCTURE-001` and evidence goes to `.runs/...`.
    UNIFIED\_MASTER\_TEMPLATE\_V1\_PART2
    UNIFIED\_MASTER\_TEMPLATE\_V1\_PART2
*   Schema requires `gate_id` pattern `^G-[0-9]{3}$` and evidence paths under `.state/evidence/` (including in phase-contract outputs).
    NEWPHASEPLANPROCESS\_plan.schema…
    NEWPHASEPLANPROCESS\_plan.schema…

**Fix:** normalize:

*   `G-001`, `G-002`, … and
*   evidence paths rooted at `.state/evidence/...` (you can still _also_ mirror logs elsewhere, but schema compliance should be canonical).

### 4) Command representation is still stringly-typed

Your template uses `command: "pytest ... | grep ..."` style strings in multiple places.

UNIFIED\_MASTER\_TEMPLATE\_V1\_PART1

UNIFIED\_MASTER\_TEMPLATE\_V1\_PART2

Your schema is designed around structured command objects (`command_invocation`) and explicit command registries (`CMD-*` patterns for custom commands, evidence requirements, etc.).

NEWPHASEPLANPROCESS\_plan.schema…

**Fix:** move to:

*   `commands.standard_by_id` / `commands.custom_by_id`, then
*   gates and phase pre/post conditions reference a `command_id` + args/env/cwd (or whatever your `command_invocation` supports).

Fit vs `plan_cli.py` (current mismatch)
---------------------------------------

`plan_cli.py` executes phases by iterating `plan["phases_by_id"]` and selects gates from `plan["gates_by_id"]`.

NEWPHASEPLANPROCESS\_plan\_cli

Your unified template is not currently structured to emit that exact JSON object model as the primary artifact.

Recommended outcome
-------------------

Use this unified template as the **human-facing “super-spec”**, but produce a **compiled output** that is strictly:

*   `plan.schema.v2.3.0.json` valid, and
*   executable by `plan_cli.py`.

If you want one fast north-star rule: **make the compiler’s output the SSOT**, and treat the unified template as a spec that _must_ deterministically compile into it (with a validator gate enforcing equivalence).

## Response:
Thought for 57s

There are 3 files because they’re serving 3 different roles:

1.  **UNIFIED\_MASTER\_TEMPLATE\_V1\_PART1.yml**  
    Holds the _front half_ of the template (SEC-000 through roughly SEC-009): template metadata, machine-indexed TOC, critical constraints, plan identity, task analysis/classification, etc. It’s long, so it was split to keep the sections grouped and manageable.
2.  **UNIFIED\_MASTER\_TEMPLATE\_V1\_PART2.yml**  
    Holds the _back half_ (SEC-010 through SEC-020): phase contracts, artifact manifest, global validation gates, risk/unknowns, decision ledger, metrics/observability, testing strategy, governance, runbooks, completion checklist.
3.  **UNIFIED\_MASTERtemplate\_feature\_analysis.md**  
    This is _not the template_. It’s the “why”: feature/rationale analysis explaining what concepts were pulled from each source system and why they’re included. It’s a companion evaluation/ADR-style document.

Bottom line: two parts are the actual template content split by section range; the third is analysis/rationale. You can merge Part1+Part2 into one canonical file if you want—recommended if you’re aiming for a single SSOT artifact.

## Response:
Thought for 1m 28s

The template actually defines **SEC-000 through SEC-020** (that’s **21** total). If you meant “the 20 main sections,” that’s **SEC-001 → SEC-020**:

1.  **SEC-001:** PLAN IDENTITY + FIXED ASSUMPTIONS
2.  **SEC-002:** TASK ANALYSIS + CLASSIFICATION
3.  **SEC-003:** EXECUTIVE SUMMARY (DECISION-READY)
4.  **SEC-004:** ASSUMPTIONS & SCOPE CONTRACT
5.  **SEC-005:** PHASE DAG + PARALLEL EXECUTION
6.  **SEC-006:** GROUND TRUTH VALIDATION LEVELS (L0-L5)
7.  **SEC-007:** SELF-HEALING RULES + CIRCUIT BREAKERS
8.  **SEC-008:** WORKTREE ISOLATION + MERGE STRATEGY
9.  **SEC-009:** ENVIRONMENT + TOOL CONFIGURATION
10.  **SEC-010:** PHASE CONTRACTS (MACHINE-CHECKABLE)
11.  **SEC-011:** CROSS-PHASE ARTIFACT MANIFEST
12.  **SEC-012:** GLOBAL VALIDATION GATES
13.  **SEC-013:** RISK + UNKNOWN MANAGEMENT
14.  **SEC-014:** DECISION LEDGER
15.  **SEC-015:** METRICS + OBSERVABILITY
16.  **SEC-016:** TESTING STRATEGY
17.  **SEC-017:** GOVERNANCE + ANTI-PATTERNS
18.  **SEC-018:** GITHUB INTEGRATION (OPTIONAL)
19.  **SEC-019:** OPERATIONAL RUNBOOKS
20.  **SEC-020:** FINAL SUMMARY + COMPLETION CHECKLIST

(Extra section not counted above: **SEC-000: CRITICAL CONSTRAINTS (NON-NEGOTIABLE)**.)

## Response:
Thought for 56s

You’re not missing it — the template mostly **doesn’t explicitly define** those things yet.

### 1) “Artifact touch list”

**What exists now:** only a checklist line that says an “Artifact Touch Summary table exists.”  
**What’s missing:** the actual **required table definition**, required columns, and where it must live.

**Fix (make it real):**  
Add an explicit artifact-touch section (either as its own section or inside SEC-011).

**Recommended placement**

*   **SEC-011 (Cross-Phase Artifact Manifest)**: add a required **Artifact Touch Summary** table.

**Minimum required columns**

*   `artifact_id`
*   `path`
*   `action` (CREATE | MODIFY | DELETE | RENAME | MOVE)
*   `phase_id`
*   `owner` (human/system)
*   `reason`
*   `risk_level`
*   `validation_ref` (which gate/test proves it)
*   `evidence_path` (where proof is written)

### 2) “Testing being written as code is developed”

**What exists now:** SEC-016 is “Testing Strategy,” but it reads like a plan-level section, not a “tests must be created with implementation” enforcement mechanism.

**Fix (make it enforceable):**  
Add a hard rule in **SEC-016** and a gate in **SEC-012**:

*   **SEC-016 rule:** every implementation task must have a paired test task.
*   **SEC-012 gate:** fail if any `code` task lacks at least one linked `test` task and evidence.

### 3) “Wiring being written as code is developed”

**What exists now:** “wiring” is not treated as a first-class deliverable type. It’s implied.

**Fix (make it first-class):**  
In **SEC-010 (Phase Contracts)**, add a required task taxonomy:

*   `task_type`: `code | test | wiring | automation_test | docs | config`
*   `produces[]`: artifact\_ids
*   `touches[]`: artifact\_ids
*   `verifies_with[]`: gate\_ids / test\_ids

Then define a policy:

*   wiring changes **must land in the same phase** as the code they connect (no deferred integration).

### 4) “Automation Testing being written as code is developed”

**What exists now:** not explicit. There’s validation levels and gates, but no dedicated automation-test artifact class tied to implementation.

**Fix (make it explicit):**  
Treat automation tests as a separate task type and artifact class:

*   `task_type: automation_test`
*   Required outputs: `e2e_test_cases`, `harness_scripts`, `evidence_runs`
*   Required gate: “automation tests executed + evidence emitted”

* * *

Minimal template changes that solve all 4
-----------------------------------------

If you want the smallest, highest-impact change set:

1.  **SEC-010 (Phase Contracts):** require `tasks[]` with `task_type`, `touches[]`, `produces[]`, `verifies_with[]`
2.  **SEC-011 (Artifact Manifest):** add **Artifact Touch Summary** table with required columns
3.  **SEC-016 (Testing Strategy):** add “tests-as-you-build” + “automation-tests-as-you-build” rules
4.  **SEC-012 (Global Gates):** add gates that fail when:
    *   touched artifacts aren’t listed in the touch summary
    *   code tasks don’t have linked tests
    *   wiring tasks are deferred without an explicit approved exception
    *   automation changes don’t have automation\_test evidence

If you want, I can draft the exact insert blocks for SEC-010/011/012/016 so you can paste them into the unified template verbatim.

## Response:
### INSERT BLOCK — SEC-010 (PHASE CONTRACTS)

```md
## INSERT — SEC-010A: TASK MODEL (REQUIRED, MACHINE-CHECKABLE)

Every phase contract MUST define `tasks[]` using the following schema-like structure.
This is a mandatory interface contract; validators MUST fail if any required field is missing.

### Required Task Object (per `tasks[]` entry)

- `task_id` (string, unique within phase; recommended format: `T-###`)
- `task_name` (string)
- `task_type` (enum; REQUIRED):
  - `code` | `test` | `wiring` | `automation_test` | `docs` | `config`
- `description` (string; concise)
- `touches[]` (REQUIRED; list of `artifact_id` values from SEC-011)
  - MUST include every file/path that is created/modified/deleted/renamed/moved by this task
- `produces[]` (REQUIRED; list of `artifact_id` values from SEC-011)
  - subset of `touches[]` representing net-new or primary outputs
- `depends_on_tasks[]` (optional; list of `task_id`)
- `verifies_with[]` (REQUIRED; list of `gate_id` values from SEC-012)
  - MUST include at least one gate that produces evidence for the task
- `evidence_paths[]` (REQUIRED; list of paths)
  - MUST be rooted at `.state/evidence/`
  - MUST include at least one evidence output per `verifies_with` reference
- `owner` (REQUIRED; enum): `human` | `system`
- `risk_level` (REQUIRED; enum): `low` | `medium` | `high`
- `rollback_plan_ref` (REQUIRED; string reference to rollback instruction or section)

### Mandatory Coupling Rules (ENFORCEMENT)

R-SEC010-01 (Artifact Touch Completeness):
- Every phase MUST be able to mechanically compute:
  - `union(touches[])` across all tasks in the phase
  - and cross-check that it equals the phase’s `artifact_touch_set` derived from SEC-011
- Any touched artifact not declared in `touches[]` is a hard failure.

R-SEC010-02 (Code Requires Tests):
- For every `task_type=code`, there MUST exist at least one `task_type=test` that:
  - includes at least one of the same `artifact_id` in `touches[]` OR explicitly lists the code task in `depends_on_tasks[]`
  - and `verifies_with[]` includes a test-execution gate in SEC-012
- Exception is allowed ONLY if `decision_ledger` contains an explicit waiver entry.

R-SEC010-03 (Wiring Is First-Class):
- Any integration/configuration/plumbing change MUST be represented as `task_type=wiring`.
- Wiring tasks MUST NOT be deferred to a later phase unless:
  - a waiver exists in `decision_ledger`
  - and SEC-012 includes a gate validating the deferral boundary.

R-SEC010-04 (Automation Tests Co-Developed):
- If a phase includes any `task_type=wiring` or modifies orchestration/execution code,
  it MUST include at least one `task_type=automation_test` producing runnable automation/e2e evidence.

### REQUIRED Phase-Level Summary Fields

Each phase contract MUST also provide:

- `artifact_touch_set[]` (REQUIRED; list of `artifact_id`)
  - MUST equal `union(touches[])` across the phase
- `phase_success_evidence[]` (REQUIRED; list of evidence paths rooted at `.state/evidence/`)
  - MUST include outputs from all gates executed for the phase
```

* * *

### INSERT BLOCK — SEC-011 (CROSS-PHASE ARTIFACT MANIFEST)

```md
## INSERT — SEC-011A: ARTIFACT TOUCH LIST (REQUIRED TABLE)

SEC-011 MUST contain an explicit, canonical **Artifact Touch List**.
This is the single source of truth for “what files will be touched” across the plan.

### Artifact Touch List (REQUIRED)

| artifact_id | path | action | phase_id | task_id | owner | reason | risk_level | validation_ref | evidence_path |
|---|---|---|---|---|---|---|---|---|---|

#### Column Requirements

- `artifact_id` (REQUIRED, unique)
  - Stable identifier for the artifact.
- `path` (REQUIRED)
  - Canonical repository/worktree path.
- `action` (REQUIRED; enum)
  - `CREATE` | `MODIFY` | `DELETE` | `RENAME` | `MOVE`
- `phase_id` (REQUIRED)
  - The phase that performs the touch.
- `task_id` (REQUIRED)
  - The specific task in SEC-010 that performs the touch.
- `owner` (REQUIRED; enum)
  - `human` | `system`
- `reason` (REQUIRED)
  - One sentence: why this artifact must be touched.
- `risk_level` (REQUIRED; enum)
  - `low` | `medium` | `high`
- `validation_ref` (REQUIRED)
  - One or more `gate_id` values from SEC-012 proving correctness after the touch.
- `evidence_path` (REQUIRED)
  - MUST be rooted at `.state/evidence/`
  - MUST exist after a successful run (created by referenced gates).

### Artifact Touch Consistency Rules (ENFORCEMENT)

R-SEC011-01 (Bidirectional Linking):
- Every row MUST point to a valid `phase_id` and `task_id`.
- Every `task.touches[]` in SEC-010 MUST have a corresponding row in this table.

R-SEC011-02 (No Undeclared Touches):
- If runtime detects a filesystem touch on an artifact path not present in this table,
  execution MUST halt and emit a violation report.

R-SEC011-03 (Rename/Move Dual Accounting):
- `RENAME` and `MOVE` MUST specify both old and new paths by adding two rows:
  - old path row: `action=RENAME` or `MOVE` + `reason="source path"`
  - new path row: `action=CREATE` (or `MODIFY` if content changes) + `reason="destination path"`
- Evidence MUST include proof that references/registry/manifest are updated.

### REQUIRED Derived Views (GENERATED)

The system MUST be able to generate (or validators must be able to compute):

- `artifacts_by_phase_id`
- `artifacts_by_task_id`
- `risk_summary_by_phase` (counts by `risk_level`)
```

* * *

### INSERT BLOCK — SEC-012 (GLOBAL VALIDATION GATES)

```md
## INSERT — SEC-012A: GLOBAL GATES FOR ARTIFACT/TEST/WIRING ENFORCEMENT

The following gates are REQUIRED. They are plan-level invariants and must run at the defined points.

### Gate: G-001 — Artifact Touch Completeness (STATIC)
- Purpose:
  - Ensure every touched artifact is declared in SEC-011 and referenced by SEC-010 tasks.
- Inputs:
  - SEC-010 `tasks[].touches[]`
  - SEC-011 Artifact Touch List
- Checks:
  1) Every `artifact_id` in any `tasks[].touches[]` exists in SEC-011 table.
  2) Every SEC-011 row has a valid `phase_id` + `task_id` mapping to SEC-010.
  3) `phase.artifact_touch_set[]` equals `union(touches[])` for that phase.
- Evidence Output (REQUIRED):
  - `.state/evidence/gates/G-001_artifact_touch_completeness.json`
- Failure Policy:
  - Any mismatch is a HARD FAIL.

### Gate: G-002 — No Undeclared Filesystem Touches (RUNTIME or POST-RUN)
- Purpose:
  - Detect real filesystem writes/moves/deletes not declared in SEC-011.
- Mechanism:
  - Either filesystem event capture during run OR post-run reconciliation sweep.
- Evidence Output (REQUIRED):
  - `.state/evidence/gates/G-002_runtime_touch_audit.json`
- Failure Policy:
  - Any undeclared touch is a HARD FAIL.

### Gate: G-003 — Tests Co-Developed With Code (STATIC)
- Purpose:
  - Ensure every `code` task is paired with at least one `test` task.
- Inputs:
  - SEC-010 tasks
- Checks:
  1) For every `task_type=code`, exists `task_type=test` linked by:
     - shared artifact touch OR explicit dependency link.
  2) The test task must reference at least one test execution gate (G-004).
- Evidence Output (REQUIRED):
  - `.state/evidence/gates/G-003_test_pairing_report.json`
- Failure Policy:
  - Missing test pairing is a HARD FAIL unless a waiver exists in Decision Ledger.

### Gate: G-004 — Unit/Integration Test Execution (EXEC)
- Purpose:
  - Execute tests and emit machine-readable evidence.
- Required Fields:
  - `command` (structured invocation preferred; no implied behavior)
  - `timeout_sec`
  - `expected_exit_code=0`
- Evidence Output (REQUIRED):
  - `.state/evidence/tests/test_run.json`
  - `.state/evidence/tests/coverage.json` (if coverage applicable)
- Failure Policy:
  - Non-zero exit code is a HARD FAIL.

### Gate: G-005 — Wiring Completeness (STATIC)
- Purpose:
  - Ensure wiring is not implicit and not deferred accidentally.
- Checks:
  1) If any phase includes `task_type=code` that introduces new modules/interfaces,
     verify at least one `task_type=wiring` exists in the same phase OR waiver exists.
  2) All wiring tasks must list touched config/registry/manifest artifacts in `touches[]`.
- Evidence Output (REQUIRED):
  - `.state/evidence/gates/G-005_wiring_completeness.json`
- Failure Policy:
  - Missing wiring is a HARD FAIL unless explicitly waived.

### Gate: G-006 — Automation Test Presence (STATIC)
- Purpose:
  - Ensure automation/e2e tests are created when orchestration/wiring changes exist.
- Checks:
  - If any phase contains `task_type=wiring` OR modifies execution/orchestration code,
    there MUST exist `task_type=automation_test` in that phase (or explicit waiver).
- Evidence Output (REQUIRED):
  - `.state/evidence/gates/G-006_automation_test_presence.json`
- Failure Policy:
  - Missing automation tests is a HARD FAIL unless explicitly waived.

### Gate: G-007 — Automation/E2E Execution (EXEC)
- Purpose:
  - Run automation tests and emit deterministic evidence.
- Required Fields:
  - `command`
  - `timeout_sec`
  - `expected_exit_code=0`
- Evidence Output (REQUIRED):
  - `.state/evidence/automation/automation_test_run.json`
  - `.state/evidence/automation/artifact_diff.json` (if applicable)
- Failure Policy:
  - Non-zero exit code is a HARD FAIL.
```

* * *

### INSERT BLOCK — SEC-016 (TESTING STRATEGY)

```md
## INSERT — SEC-016A: TESTS-AS-YOU-BUILD (MANDATORY POLICY)

Testing is not a later phase. Tests are authored as code is authored.
This is enforced mechanically via SEC-012 gates.

### Required Testing Work Products (BY TASK TYPE)

For `task_type=code`:
- MUST have:
  - at least one corresponding `task_type=test`
  - at least one gate reference that executes tests (G-004)
  - evidence outputs stored under `.state/evidence/tests/`

For `task_type=wiring`:
- MUST have:
  - at least one `task_type=automation_test` OR one `task_type=test` that validates integration boundaries
  - at least one gate reference that executes automation tests (G-007) when orchestration is affected
  - evidence outputs under `.state/evidence/automation/`

For `task_type=automation_test`:
- MUST produce:
  - runnable test code (not pseudo-code)
  - a deterministic execution command (no implied behavior)
  - machine-readable pass/fail evidence

### Mandatory Coverage of Failure Modes

Each phase MUST include negative-path verification for:
- missing file / wrong path
- invalid schema/config input
- failed external command (non-zero exit)
- rollback path correctness when applicable

Evidence for negative-path testing MUST be recorded in:
- `.state/evidence/tests/negative_cases.json`

### Linking Requirements (ENFORCEMENT)

R-SEC016-01 (Traceability):
- Every test or automation test MUST reference the task(s) it verifies via:
  - `depends_on_tasks[]` OR shared `artifact_id` in `touches[]`
- Validators must be able to compute the mapping:
  - `code_task -> {test_tasks, automation_test_tasks}`

R-SEC016-02 (No Silent Pass):
- A “test strategy description” is insufficient.
- Tests MUST be executable with a declared command and produce evidence artifacts.

### Minimum Required Evidence Set (PER PHASE)

Each phase MUST produce (at minimum):
- `.state/evidence/gates/G-001_artifact_touch_completeness.json`
- `.state/evidence/gates/G-003_test_pairing_report.json`
- `.state/evidence/tests/test_run.json`
- If wiring/orchestration touched:
  - `.state/evidence/gates/G-006_automation_test_presence.json`
  - `.state/evidence/automation/automation_test_run.json`
```

## Response:
Thought for 43s

Yes. Keep each section as a **sharded source file**, then compile them into the **single plan JSON** your CLI executes.

Recommended pattern
-------------------

### 1) Source shards (edit here)

```
plan_src/
  sec_000_meta.json
  sec_010_phase_contracts.json
  sec_011_artifact_touch_list.json
  sec_012_gates.json
  sec_016_testing_policy.json
  sec_index.json
```

Each shard should be **one root key** (or a tight set) to avoid merge ambiguity.

Example shard shapes:

*   `sec_010_phase_contracts.json`
    ```json
    { "phases_by_id": { "...": { ... } } }
    ```
*   `sec_011_artifact_touch_list.json`
    ```json
    { "artifact_touch_list": [ { ... }, { ... } ] }
    ```
*   `sec_012_gates.json`
    ```json
    { "gates_by_id": { "G-001": { ... }, "G-002": { ... } } }
    ```
*   `sec_016_testing_policy.json`
    ```json
    { "testing_policy": { "rules": [ ... ], "required_evidence": [ ... ] } }
    ```

### 2) Manifest that defines merge order

`sec_index.json`

```json
{
  "compile_order": [
    "sec_000_meta.json",
    "sec_010_phase_contracts.json",
    "sec_011_artifact_touch_list.json",
    "sec_012_gates.json",
    "sec_016_testing_policy.json"
  ]
}
```

### 3) Compiled artifact (execute here)

```
plan_compiled/plan.json
```

How the compiler should work (deterministic)
--------------------------------------------

1.  Load `sec_index.json` compile\_order
2.  For each shard:
    *   validate the shard against a **section schema** (optional but recommended)
    *   deep-merge into a single in-memory plan object
3.  Run **cross-section validators** after merge:
    *   every `task.touches[]` references an artifact present in SEC-011
    *   every `task.verifies_with[]` references a gate in SEC-012
    *   every artifact touch row references a valid `phase_id` + `task_id`
4.  Validate the final compiled plan against `plan.schema.v2.3.0.json`
5.  Write `plan_compiled/plan.json` using **canonical JSON** (stable key ordering) + emit a checksum

Two viable composition strategies
---------------------------------

### A) Deep-merge shards (simplest)

Each shard contributes root keys (`phases_by_id`, `gates_by_id`, etc.). The compiler deep-merges maps and concatenates arrays with strict rules.

### B) Patch shards (most governance-friendly)

Each “section file” is an **RFC-6902 JSON Patch** array applied to a base plan:

*   `sec_012_gates.patch.json` contains `add/replace/remove` ops
*   Guarantees “patch-only” history and auditability

If you want “analysis edits to a single section,” patch shards are the cleanest.

One practical caveat
--------------------

Some sections (like SEC-016 testing policy) may not naturally fit your current `plan.schema.v2.3.0.json`. You have 2 options:

*   Put them under a schema-approved “metadata/notes/policy” field (if it exists), OR
*   Extend the schema to include `testing_policy` (recommended if you want it enforced structurally rather than as narrative)

Minimal compiler script outline (Python)
----------------------------------------

```python
import json, hashlib
from pathlib import Path

def deep_merge(a, b):
    for k, v in b.items():
        if k in a and isinstance(a[k], dict) and isinstance(v, dict):
            deep_merge(a[k], v)
        elif k in a and isinstance(a[k], list) and isinstance(v, list):
            a[k].extend(v)
        else:
            a[k] = v
    return a

src = Path("plan_src")
index = json.loads((src/"sec_index.json").read_text(encoding="utf-8"))
plan = {}

for fname in index["compile_order"]:
    shard = json.loads((src/fname).read_text(encoding="utf-8"))
    plan = deep_merge(plan, shard)

# optional: cross-section validators here

out = json.dumps(plan, sort_keys=True, separators=(",", ":")).encode("utf-8")
sha = hashlib.sha256(out).hexdigest()

Path("plan_compiled").mkdir(exist_ok=True)
(Path("plan_compiled")/"plan.json").write_bytes(out)
(Path("plan_compiled")/"plan.json.sha256").write_text(sha+"\n", encoding="utf-8")
```

If you want, I can also define the **merge rules** precisely (array uniqueness, conflict policy, duplicate ID handling) so edits to one shard can’t silently corrupt another.



---
Powered by [ChatGPT Exporter](https://www.chatgptexporter.com)