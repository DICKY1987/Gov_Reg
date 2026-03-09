# Plan: Parallel Workstreams Execution — Full 7-Phase Implementation

## Context

The Parallel Workstreams Execution feature enables deterministic, conflict-free parallel execution
of independent development workstreams using isolated git worktrees. The feature guide
(`01260207201000001250_REGISTRY\docs\PARALLEL_WORKSTREAMS_FEATURE_GUIDE.md`) catalogs 31 missing
files across 7 implementation phases.

Prior attempts built the scheduling and patch-handling layer but never implemented the two novel
safety-critical components: conflict graph computation and isolated worktree provisioning. All
existing code treats workstreams as sequentially-scheduled batches in a shared workspace.

**Goal:** Implement all 31 files end-to-end following the 12-gate pipeline defined in the guide.

---

## Target Directory Structure

All implementation lives under:
```
C:\Users\richg\Gov_Reg\01260207201000001221_Multi CLI\
  01260207201000001275_schemas\          ← 6 core JSON schemas
  01260207201000001276_scripts\          ← 7 execution tool scripts
  01260207201000001277_orchestrator\     ← 3 LangGraph adapter tools
    src\acms_orchestrator\tools\
  01260207201000001278_tests\            ← 5 test fixtures + 2 golden files
    fixtures\
    golden\
  01260207201000001279_registries\       ← 2 registry JSON files
  01260207201000001280_template_extensions\ ← 3 template extension files
  docs\                                  ← 2 doc files (use existing docs\ in REGISTRY)
```

Note: `orchestrator_langgraph/` from guide maps to `01260207201000001277_orchestrator\`.
Note: `tools/` from guide maps to `01260207201000001276_scripts\`.

---

## Reusable Components (Do Not Rewrite)

| Existing File | What to Reuse |
|--------------|---------------|
| `RUNTIME\engine\PHASE_5_EXECUTION\engine\DOC-CORE-ENGINE-PATCH-APPLIER-338__patch_applier.py` | `_create_worktree()`, `_cleanup_worktree()` — the only existing `git worktree add` implementation; use as basis for `provision_worktrees.py` |
| `RUNTIME\engine\PHASE_5_EXECUTION\engine\DOC-CORE-ENGINE-PATCH-LEDGER-153__patch_ledger.py` | `PatchLedger` class, `ValidationResult` dataclass, SQLite state machine pattern |
| `RUNTIME\engine\PHASE_5_EXECUTION\engine\DOC-CORE-ENGINE-PATCH-CONVERTER-152__patch_converter.py` | `UnifiedPatch` dataclass, `PatchConverter.validate_unified_diff()` |
| `RUNTIME\engine\PHASE_5_EXECUTION\engine\DOC-CORE-ENGINE-INTEGRATION-WORKER-150__integration_worker.py` | `MergeConflict`, `MergeResult` dataclasses; baseline for `integrate_patches.py` (add topological ordering on top) |
| `RUNTIME\engine\PHASE_5_EXECUTION\engine\DOC-CORE-ENGINE-ORCHESTRATOR-151__orchestrator.py` | `Orchestrator.create_run(workstream_id=...)` pattern for run tracking |
| `MINI_PIPE\src\acms\uet_tool_adapters.py` | `ToolRunRequestV1` / `ToolRunResultV1` contract — all new tool scripts must follow this never-raises pattern |
| `MINI_PIPE\tests\e2e\test_determinism.py` | Determinism test pattern: normalize timestamps/run_ids before comparison |
| `01260207201000001221_Multi CLI\schemas_langgraph\envelope.schema.json` | ArtifactEnvelope format for evidence bundling |

---

## Prompt Template Consolidation (Pre-Phase-1)

Three copies of the multi-workstream prompt template must be consolidated before Phase 6 LangGraph
integration to prevent divergence:
1. `RUNTIME\engine\PHASE_5_EXECUTION\contracts\DOC-CONFIG-EXECUTION-PROMPT-TEMPLATE-V2-DAG-MULTI-484__EXECUTION_PROMPT_TEMPLATE_V2_DAG_MULTI_WORKSTREAM.json`
2. `RUNTIME\process_steps\PROCESS_STEP_LIB\config\DOC-CONFIG-EXECUTION-PROMPT-TEMPLATE-V2-DAG-MULTI-785__EXECUTION_PROMPT_TEMPLATE_V2_DAG_MULTI_WORKSTREAM.json`
3. `MINI_PIPE\docs\analysis_frameworks\EXECUTION_PROMPT_TEMPLATE_V2_DAG_MULTI_WORKSTREAM.json`

Action: Diff all three, pick canonical version, add a note in the other two pointing to canonical.
Do this before writing Phase 6 adapter code.

---

## Implementation Phases

### Phase 1 — Schema & Validation Foundation
**Output dir:** `01260207201000001275_schemas\`

Create 6 JSON Schema Draft-07 files:

| File | Key Fields |
|------|-----------|
| `parallel_workstreams.schema.json` | `workstreams[]` with `workstream_id`, `write_manifest`, `dependencies[]`, `exclusive_resources[]` |
| `write_manifest.schema.json` | `workstream_id`, `declared_writes[]` (file paths), `declared_reads[]`, `exclusive_locks[]` |
| `conflict_graph.schema.json` | `nodes[]` (workstream_id), `edges[]` (source, target, conflict_type), `parallel_groups[][]` |
| `worktree_execution_report.schema.json` | `workstream_id`, `worktree_path`, `exit_code`, `touched_files[]`, `patches[]`, `evidence_path` |
| `integration_report.schema.json` | `applied_patches[]`, `failed_patches[]`, `conflicts[]`, `rollback_log[]`, `integration_order[]` |
| `evidence_bundle.schema.json` | `run_id`, `workstream_id`, `gate_results[]`, `artifacts[]`, `hash_manifest{}` |

Then create `01260207201000001276_scripts\validate_parallel_workstreams.py`:
- Load plan JSON, validate `parallel_workstreams` section against `parallel_workstreams.schema.json`
- Validate each workstream's write manifest against `write_manifest.schema.json`
- Exit 0 on pass, 1 on fail, write gate result JSON to `evidence/gates/GATE_PWE_001.result.json`
- Follow `ToolRunRequestV1`/`ToolRunResultV1` contract (never raises)

Create `01260207201000001278_tests\fixtures\parallel_workstreams_minimal_case\`:
- `plan.json` — minimal valid plan with 2 independent workstreams, non-overlapping write sets
- `expected_gate_001.json` — expected GATE-PWE-001 pass result

**Gates:** GATE-PWE-001 (scope validate), GATE-PWE-002 (write manifest validate)

---

### Phase 2 — Conflict Analysis Engine
**Output dir:** `01260207201000001276_scripts\`

Create `compute_conflict_graph.py`:
- Parse write manifests for all workstreams in plan
- Detect file-level overlaps: if `ws_A.declared_writes ∩ ws_B.declared_writes ≠ ∅` → conflict edge
- Build directed graph: dependency edges from plan's `dependencies[]` field
- Compute parallel groups via Kahn's topological sort (groups = batches of no-predecessor nodes)
- Output `artifacts/conflict_graph/conflict_graph.json` (validated against `conflict_graph.schema.json`)
- Output `artifacts/conflict_graph/parallel_groups.json`
- Enforce `max_parallel_workstreams: 4` limit from patch spec invariants

Create test fixtures:
- `01260207201000001278_tests\fixtures\conflict_case_overlap_writes\` — two workstreams touching same file; expect conflict edge, no parallel group
- `01260207201000001278_tests\golden\expected_conflict_graph.json` — golden artifact for determinism check

**Gates:** GATE-PWE-003 (conflict graph build), GATE-PWE-004 (parallel group authorization)

---

### Phase 3 — Worktree Isolation
**Output dir:** `01260207201000001276_scripts\`

Create `provision_worktrees.py`:
- Basis: `PatchApplier._create_worktree()` from patch_applier.py (the only existing `git worktree add` impl)
- For each workstream in authorized parallel group: `git worktree add <path> <base_commit> --detach`
- Naming: deterministic — `worktrees/{run_id}/{workstream_id}/`
- Validate: base commit is clean, worktree is isolated (no shared index)
- Generate `artifacts/worktrees/worktree_map.json` mapping `workstream_id → worktree_path`
- Cleanup utility: `git worktree remove --force` with retry on Windows file locks
- Enforce `max_total_worktrees: 8` from patch spec

**Gate:** GATE-PWE-005 (worktree provision)

---

### Phase 4 — Parallel Execution Engine
**Output dir:** `01260207201000001276_scripts\`

Create `enforce_declared_writes.py`:
- After workstream execution: `git -C <worktree_path> diff --name-only HEAD`
- Compare actual touched files against `declared_writes[]` from write manifest
- Any file in actual but NOT in declared → violation → fail gate, write evidence
- Fixture: `01260207201000001278_tests\fixtures\undeclared_write_case\`

Create `collect_workstream_evidence.py`:
- Gather: execution logs, patches (from `PatchConverter`), gate results, touched_files.json
- Compute SHA-256 hash of each artifact
- Package into `evidence/workstreams/{workstream_id}/evidence_bundle.json`
- Validate against `evidence_bundle.schema.json`
- Use `envelope.schema.json` from `schemas_langgraph\` as envelope wrapper

**Gates:** GATE-PWE-006 (execute), GATE-PWE-007 (declared writes enforcement), GATE-PWE-008 (evidence bundle validate)

---

### Phase 5 — Integration & Merge
**Output dir:** `01260207201000001276_scripts\`

Create `integrate_patches.py`:
- Basis: `IntegrationWorker` from integration_worker.py (`MergeConflict`, `MergeResult` dataclasses)
- Key addition over existing: apply patches in **topological order** from `parallel_groups.json`
- For each patch in order: `git apply --check` first, then `git apply`
- On conflict: record to `integration_report.json`, trigger rollback
- Rollback: reverse applied patches in reverse topological order, restore control checkout
- Write `artifacts/integration/integration_report.json` (validated against `integration_report.schema.json`)
- Write `artifacts/integration/rollback_log.json` if rollback occurred

Create `validate_determinism.py`:
- Re-run `compute_conflict_graph.py` with same inputs, compare output hashes
- Normalize volatile fields (timestamps, run_id) — reuse pattern from `MINI_PIPE\tests\e2e\test_determinism.py`
- Validate conflict graph hash matches across two runs
- Write `evidence/determinism/determinism_report.json`

Golden file: `01260207201000001278_tests\golden\expected_evidence_bundle.json`

**Gates:** GATE-PWE-009 (integrate patches), GATE-PWE-010 (integration validate), GATE-PWE-011 (determinism validate)

---

### Phase 6 — LangGraph Integration
**Output dir:** `01260207201000001277_orchestrator\src\acms_orchestrator\tools\`

Consolidate 3 prompt template copies first (see pre-requisite above).

Create 3 LangGraph adapter tools following the `ToolRunRequestV1`/`ToolRunResultV1` contract:

`conflict_graph.py`:
- Wraps `compute_conflict_graph.py` as a LangGraph tool node
- Input: plan path, output dir; Output: conflict_graph path, parallel_groups path
- Adds to orchestrator state: `conflict_graph`, `parallel_groups`

`worktree_provision.py`:
- Wraps `provision_worktrees.py` as a LangGraph tool node
- Input: run_id, parallel_groups, base_commit; Output: worktree_map path
- Adds to orchestrator state: `worktree_map`

`dispatch_workers.py`:
- Spawns parallel workstream execution using process pool (basis: `ProcessSpawner` from MINI_PIPE)
- Dispatches each parallel group, waits for completion, collects evidence bundles
- Adds to orchestrator state: `workstream_results[]`

Extend orchestrator state model with fields: `workstreams`, `conflict_graph`, `worktree_map`, `parallel_groups`, `workstream_results`.

Add `TOOL_MAPPING.json` entries for: `conflict_graph_cli`, `worktree_provision_cli`, `dispatch_workers_cli`.

**Gate:** GATE-PWE-012 (registry reconcile) — rebuild_registries.py reads all artifacts and reconciles `registries/` state.

---

### Phase 7 — Registries, Template Extensions & Docs
**Output dirs:** `01260207201000001279_registries\`, `01260207201000001280_template_extensions\`, REGISTRY `docs\`

`01260207201000001279_registries\artifact_inventory.json`:
- Inventory of all parallel workstream artifacts with SHA-256 hashes and provenance (run_id, gate, workstream_id)

`01260207201000001279_registries\policy_registry.json`:
- Active policies from patch spec invariants (isolation, single_writer, delta_only_workers, explicit_scope, declared_write_enforcement, completion_by_evidence)
- Versions and effective dates

`01260207201000001280_template_extensions\parallel_workstreams.section.json`:
- Plan section schema: workstream declarations format for newPhasePlanProcess v3.0.0

`01260207201000001280_template_extensions\parallel_workstreams.gates.json`:
- Gate catalog entries GATE-PWE-001 through GATE-PWE-012

`01260207201000001280_template_extensions\parallel_workstreams.artifacts.json`:
- Artifact catalog with schema bindings (which artifact validates against which schema)

Docs (in `01260207201000001250_REGISTRY\docs\`):
- `PARALLEL_WORKSTREAMS_ARCHITECTURE.md`
- `PARALLEL_WORKSTREAMS_RUNBOOK.md`

---

## Key Design Constraints (from patch_parallel_workstream_execution_v3.json)

- `max_parallel_workstreams: 4`, `max_total_worktrees: 8`
- Circuit breakers: `max_failed_workstreams: 1`, `max_total_failures: 3`
- Invariants: isolation, single_writer, delta_only_workers, explicit_scope, declared_write_enforcement, completion_by_evidence
- Auto-enable when: `complexity=moderate AND touches_state=true` OR `complexity=complex`
- Disable when: `complexity=simple AND estimated_file_writes_max<=4`

---

## Verification

**Phase 1:** `python validate_parallel_workstreams.py --plan fixtures/parallel_workstreams_minimal_case/plan.json` → exit 0, GATE-PWE-001.result.json written.

**Phase 2:** `python compute_conflict_graph.py --plan fixtures/conflict_case_overlap_writes/plan.json` → conflict edge detected, no parallel groups authorized. Compare output against `golden/expected_conflict_graph.json`.

**Phase 3:** `python provision_worktrees.py --run-id test-001 --plan fixtures/parallel_workstreams_minimal_case/plan.json` → two worktrees created, `worktree_map.json` written, `git worktree list` shows them. Cleanup removes them.

**Phase 4:** `python enforce_declared_writes.py --worktree fixtures/undeclared_write_case/worktree --manifest fixtures/undeclared_write_case/write_manifest.json` → exit 1, violation logged.

**Phase 5:** Run `validate_determinism.py` twice with identical inputs → identical output hashes. `integrate_patches.py` with conflicting patches → rollback_log.json written, control checkout clean.

**Phase 6:** Orchestrator end-to-end run with minimal_case fixture → all 12 gate results written, evidence bundles present, determinism report passes.

**Phase 7:** `artifact_inventory.json` hashes match actual artifact SHA-256s. Policy registry version matches patch spec version.
