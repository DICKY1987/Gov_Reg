# Execution Readiness Review

Reviewed file: `C:\Users\richg\Gov_Reg\greedy-stirring-tower.md`
Review date: `2026-04-07`

## Conclusion

The plan is not execution-ready in a strict sense.

It is close to usable as a human or agent runbook, but it still has hard blockers that prevent deterministic, fully reproducible execution.

Update: `phase_b_override_map.md` and `reserved_id_namespaces.json` have since been authored in this same directory, and the runbook's bad support-plan paths have been corrected. The remaining strict-run blockers are now validator/tooling drift and the dirty repo state.

## Hard issues

### 1. `phase_b_override_map.md` is required but missing

The plan says Phase B has this precondition:

- `phase_b_override_map.md` and `reserved_id_namespaces.json` must both be committed before Phase B.

Why this matters:

- `phase_b_override_map.md` decides registry path, version bump policy, extend-vs-replace behavior, and gate-count recomputation timing.
- Multiple later steps branch on those decisions.
- Without this file, different operators can make different choices and still claim to be following the plan.
- That breaks determinism, auditability, and cross-file consistency.

Status:

- Missing from `C:\Users\richg\Gov_Reg`
- Missing from `C:\Users\richg\Gov_Reg\guardrails_template_project`

### 2. `reserved_id_namespaces.json` is not present yet

The plan defines this as a B.0 deliverable, but also requires it to be committed before Phase B.

Why this matters:

- Phase A can still begin without it.
- Phase B cannot start cleanly until it exists.
- For strict execution, the handoff from B.0 to B must be explicit and unambiguous.

Status:

- Missing from `C:\Users\richg\Gov_Reg`
- Missing from `C:\Users\richg\Gov_Reg\guardrails_template_project`

### 3. Source-plan paths in `greedy-stirring-tower.md` are wrong

The plan references:

- `plansforthis\FINAL_EDIT_PLAN_V3_2_TO_V3_3.md`
- `plansforthis\MERGED_CORRECTED_FINAL_EDIT_PLAN.md`
- `plansforthis\cli_blocker_fix_guide.md`
- `plansforthis\final_indexing_implementation_plan.json`
- `plansforthis\v3_3_patch_plan_machine_style.json`
- `plansforthis\v3_3_patch_plan_machine_layer2.json`

Why this matters:

- Those files are part of the execution contract, not optional context.
- Any runner that validates dependencies from the paths written in the plan will fail.
- A human operator can recover, but a strict run should not require path guesswork.

Actual locations found:

- `C:\Users\richg\Gov_Reg\guardrails_template_project\FINAL_EDIT_PLAN_V3_2_TO_V3_3.md`
- `C:\Users\richg\Gov_Reg\guardrails_template_project\MERGED_CORRECTED_FINAL_EDIT_PLAN.md`
- `C:\Users\richg\Gov_Reg\guardrails_template_project\cli_blocker_fix_guide.md`
- `C:\Users\richg\Gov_Reg\guardrails_template_project\final_indexing_implementation_plan.json`
- `C:\Users\richg\Gov_Reg\guardrails_template_project\v3_3_patch_plan_machine_style.json`
- `C:\Users\richg\Gov_Reg\guardrails_template_project\v3_3_patch_plan_machine_layer2.json`

No `plansforthis` directory was found under `C:\Users\richg\Gov_Reg` or under `C:\Users\richg\Gov_Reg\guardrails_template_project`.

### 4. The repo is already dirty

The plan requires each phase to land as its own commit so any phase can be reverted independently.

Why this matters:

- Existing unrelated deletions and untracked files reduce commit isolation.
- Phase-by-phase auditability is weaker if the worktree already contains unrelated changes.
- This is an operational blocker for clean execution, even if it is not a logical blocker in the plan text.

## Core files confirmed present

- `C:\Users\richg\Gov_Reg\NEWPHASEPLANPROCESS_TECHNICAL_SPECIFICATION_V3_2.json`
- `C:\Users\richg\Gov_Reg\NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_2.json`
- `C:\Users\richg\Gov_Reg\NEWPHASEPLANPROCESS_INSTRUCTION_DOCUMENT_V3_2.json`

## Other files needed for strict execution

These are the non-core files that matter for strict execution readiness.

### Must exist before or by Phase B

- `phase_b_override_map.md` - missing; true prerequisite
- `reserved_id_namespaces.json` - missing; B.0 deliverable that must exist before Phase B proceeds

### Required support plans

- `C:\Users\richg\Gov_Reg\guardrails_template_project\FINAL_EDIT_PLAN_V3_2_TO_V3_3.md`
- `C:\Users\richg\Gov_Reg\guardrails_template_project\MERGED_CORRECTED_FINAL_EDIT_PLAN.md`
- `C:\Users\richg\Gov_Reg\guardrails_template_project\cli_blocker_fix_guide.md`
- `C:\Users\richg\Gov_Reg\guardrails_template_project\final_indexing_implementation_plan.json`

### Deferred support plans

- `C:\Users\richg\Gov_Reg\guardrails_template_project\v3_3_patch_plan_machine_style.json`
- `C:\Users\richg\Gov_Reg\guardrails_template_project\v3_3_patch_plan_machine_layer2.json`

These are not applied in v3.3, but the plan still references them and should point to their real locations.

### Validators and helper scripts referenced by the plan/spec

Located under `C:\Users\richg\Gov_Reg\newPhasePlanProcess\01260207201000001225_scripts\`:

- `P_01260207233100000263_validate_structure.py`
- `P_01260207233100000253_validate_gates.py`
- `P_01260207233100000250_validate_automation_spec.py`
- `P_01260207233100000226_build_automation_index.py`

Why they matter:

- The plan's verification section expects regression and validation runs.
- Strict execution requires these scripts to be locatable and callable, not just mentioned abstractly.

## Minimum changes to make the plan strict-run ready

1. Fix the support-plan paths in `greedy-stirring-tower.md`.
2. Author and commit `phase_b_override_map.md`.
3. Make the B.0 to Phase B dependency explicit for `reserved_id_namespaces.json`.
4. Start from a clean enough git state, or isolate execution on a dedicated branch/worktree.
