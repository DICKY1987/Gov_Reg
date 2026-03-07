# Parallel Workstreams Execution Architecture

## Overview

The Parallel Workstreams Execution (PWE) system enables deterministic, conflict-free parallel execution of independent development workstreams using isolated git worktrees. This architecture document describes the design, components, and safety guarantees of the system.

## Architecture Principles

### 1. Isolation
Each workstream executes in a completely isolated git worktree, preventing any cross-contamination between parallel tasks.

### 2. Determinism
All operations are deterministic and repeatable. The conflict graph computation produces identical results given identical inputs (normalized for timestamps).

### 3. Safety-First
The system enforces six core policies through 12 validation gates to ensure safe parallel execution:
- **Isolation**: Workstream isolation via git worktrees
- **Single Writer**: No file write conflicts between parallel workstreams
- **Delta-Only Workers**: Workstreams produce patches, not direct commits
- **Explicit Scope**: All writes must be pre-declared
- **Declared Write Enforcement**: Actual writes match declared writes
- **Completion by Evidence**: Cryptographic proof of completion

## System Components

### Phase 1: Schema & Validation Foundation
**Location**: `01260207201000001275_schemas/`

Six JSON Schema Draft-07 files define the data contracts:
- `parallel_workstreams.schema.json` - Workstream configuration
- `write_manifest.schema.json` - File write declarations
- `conflict_graph.schema.json` - Conflict analysis graph
- `worktree_execution_report.schema.json` - Execution results
- `integration_report.schema.json` - Patch integration results
- `evidence_bundle.schema.json` - Complete execution evidence

**Gates**: GATE-PWE-001 (scope validate), GATE-PWE-002 (write manifest validate)

### Phase 2: Conflict Analysis Engine
**Location**: `01260207201000001276_scripts/compute_conflict_graph.py`

Analyzes write manifests to build a conflict graph:
1. Detects file-level write-write conflicts
2. Detects write-read dependencies
3. Enforces exclusive resource locks
4. Computes topological ordering for integration
5. Groups workstreams into parallel execution batches

**Algorithm**: Kahn's topological sort with conflict detection
**Constraints**: max_parallel_workstreams = 4

**Gates**: GATE-PWE-003 (conflict graph build), GATE-PWE-004 (parallel group authorization)

### Phase 3: Worktree Isolation
**Location**: `01260207201000001276_scripts/provision_worktrees.py`

Provisions isolated git worktrees for each workstream:
```bash
git worktree add --detach <path> <base_commit>
```

**Naming Convention**: `worktrees/{run_id}/{workstream_id}/`

**Cleanup**: Automatic cleanup with retry logic for Windows file locks

**Constraints**: max_total_worktrees = 8

**Gate**: GATE-PWE-005 (worktree provision)

### Phase 4: Parallel Execution Engine
**Location**: `01260207201000001276_scripts/`

#### enforce_declared_writes.py
Post-execution validation that actual touched files match declared writes:
```python
actual_writes = git_diff(worktree_path, base_commit)
violations = actual_writes - declared_writes
```

#### collect_workstream_evidence.py
Collects execution artifacts into cryptographically-verified evidence bundle:
- Gate results
- Execution logs
- Patches (unified diff format)
- SHA-256 hash manifest

**Gates**: GATE-PWE-006 (execute), GATE-PWE-007 (declared writes), GATE-PWE-008 (evidence bundle)

### Phase 5: Integration & Merge
**Location**: `01260207201000001276_scripts/`

#### integrate_patches.py
Applies patches in topological order with automatic rollback on conflict:
1. Load integration order from parallel groups
2. For each workstream in order:
   - `git apply --check` for safety
   - `git apply` to integrate
3. On failure: rollback all applied patches in reverse order

#### validate_determinism.py
Verifies conflict graph computation is deterministic:
1. Run computation twice with identical inputs
2. Normalize volatile fields (timestamps, run_ids)
3. Compare SHA-256 hashes of normalized output
4. Pass if hashes match

**Gates**: GATE-PWE-009 (integrate), GATE-PWE-010 (validate), GATE-PWE-011 (determinism)

### Phase 6: LangGraph Integration
**Location**: `01260207201000001277_orchestrator/src/acms_orchestrator/tools/`

Three adapter tools expose PWE functionality to LangGraph orchestrator:

#### conflict_graph.py
Wraps conflict graph computation as LangGraph tool node.
**Input**: plan_path, output_dir, max_parallel
**Output**: conflict_graph_path, parallel_groups_path

#### worktree_provision.py
Wraps worktree provisioning as LangGraph tool node.
**Input**: run_id, parallel_groups, base_commit
**Output**: worktree_map_path, worktree_map

#### dispatch_workers.py
Spawns parallel workstream execution using process pool.
**Input**: parallel_groups, worktree_map, manifests_dir
**Output**: workstream_results[]

All tools follow `ToolRunRequestV1`/`ToolRunResultV1` contract (never raises exceptions).

### Phase 7: Registries & Templates
**Location**: `01260207201000001279_registries/`, `01260207201000001280_template_extensions/`

#### artifact_inventory.json
Catalog of all PWE artifacts with SHA-256 hashes and provenance tracking.

#### policy_registry.json
Active policies with enforcement levels and validation gates.

#### Template Extensions
- `parallel_workstreams.section.json` - Plan section schema
- `parallel_workstreams.gates.json` - Gate catalog (GATE-PWE-001 through 012)
- `parallel_workstreams.artifacts.json` - Artifact catalog with schema bindings

**Gate**: GATE-PWE-012 (registry reconcile)

## Data Flow

```
1. Plan with parallel_workstreams section
   ↓ GATE-PWE-001, 002
2. Write manifests validated
   ↓
3. Conflict graph computed
   ↓ GATE-PWE-003, 004
4. Parallel groups authorized
   ↓
5. Worktrees provisioned
   ↓ GATE-PWE-005
6. Parallel execution (per group)
   ↓ GATE-PWE-006, 007, 008
7. Evidence collected (per workstream)
   ↓
8. Patches integrated in topological order
   ↓ GATE-PWE-009, 010
9. Determinism validated
   ↓ GATE-PWE-011
10. Registry reconciled
    ↓ GATE-PWE-012
11. Complete
```

## Safety Guarantees

### Isolation Guarantee
No workstream can observe or modify another workstream's state during execution. Each operates in a completely isolated git worktree.

### Conflict-Free Guarantee
The conflict graph ensures no two parallel workstreams write to the same file. Write-write conflicts force sequential execution.

### Rollback Guarantee
Integration failure triggers automatic rollback of all applied patches, restoring the repository to clean state.

### Evidence Guarantee
Every workstream completion is proven by a cryptographically-verified evidence bundle with SHA-256 hashes.

## Circuit Breakers

The system includes configurable circuit breakers to halt execution on widespread failures:
- `max_failed_workstreams: 1` - Stop if any single workstream fails
- `max_total_failures: 3` - Stop if total failure count reaches threshold

## Auto-Enable Conditions

Parallel execution automatically enables when:
- `complexity ≥ moderate` AND `touches_state = true`, OR
- `complexity = complex`

Automatically disables when:
- `complexity = simple` AND `estimated_file_writes ≤ 4`

## Integration with Existing Systems

### PatchApplier (DOC-CORE-ENGINE-PATCH-APPLIER-338)
Reuses `_create_worktree()` and `_cleanup_worktree()` as basis for `provision_worktrees.py`.

### PatchLedger (DOC-CORE-ENGINE-PATCH-LEDGER-153)
Reuses `ValidationResult` dataclass and SQLite state machine pattern.

### IntegrationWorker (DOC-CORE-ENGINE-INTEGRATION-WORKER-150)
Reuses `MergeConflict` and `MergeResult` dataclasses as basis for `integrate_patches.py`.

### UET Tool Adapters (MINI_PIPE/src/acms/uet_tool_adapters.py)
All scripts follow the `ToolRunRequestV1`/`ToolRunResultV1` never-raises contract.

## Performance Characteristics

- **Max Parallel Workstreams**: 4 per group
- **Max Total Worktrees**: 8 across all groups
- **Worktree Creation**: O(n) where n = number of workstreams
- **Conflict Detection**: O(n²) where n = number of workstreams (pairwise comparison)
- **Topological Sort**: O(V + E) where V = workstreams, E = conflict edges
- **Patch Integration**: O(p) where p = total patches (sequential)

## Testing Strategy

Three test fixture categories:
1. **Minimal Case**: Two independent workstreams, no conflicts
2. **Conflict Case**: Two workstreams with overlapping writes
3. **Undeclared Write Case**: Workstream writes undeclared file

Golden files provide determinism validation baseline.

## Versioning

- **Schema Version**: 1.0.0
- **Policy Version**: 1.0.0
- **Compatible with**: newPhasePlanProcess v3.0.0

## References

- Full feature guide: `01260207201000001250_REGISTRY/docs/PARALLEL_WORKSTREAMS_FEATURE_GUIDE.md`
- Patch specification: `patch_parallel_workstream_execution_v3.json`
- Implementation plan: `lazy-questing-thompson.md`
