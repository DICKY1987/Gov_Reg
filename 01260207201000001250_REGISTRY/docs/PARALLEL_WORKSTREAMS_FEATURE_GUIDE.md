# Parallel Workstreams Execution Feature Guide

**Document ID:** PARALLEL_WORKSTREAMS_FEATURE_GUIDE  
**Version:** 1.0.0  
**Status:** PLANNING (Future Work)  
**Created:** 2026-03-06  
**Purpose:** AI execution guide for implementing parallel workstream execution with git worktrees

---

## Executive Summary

The **Parallel Workstream Execution with Git Worktrees** feature enables deterministic, conflict-free parallel execution of independent development workstreams using isolated git worktrees. This feature is **not part of the active entity-scoped solution plan** but represents future work to accelerate automation through parallelization.

### Key Capabilities
- ✅ Automatic conflict detection via declared write manifests
- ✅ Deterministic conflict graph generation for safe parallel grouping
- ✅ Isolated git worktree provisioning per workstream
- ✅ Parallel execution with full evidence chains
- ✅ Deterministic merge integration with rollback support
- ✅ Complete LangGraph orchestrator integration

---

## Feature Architecture

### High-Level Flow

```
Plan with Workstreams
    ↓
[GATE-PWE-001] Validate Workstream Scope
    ↓
[GATE-PWE-002] Validate Write Manifests
    ↓
[GATE-PWE-003] Build Conflict Graph
    ↓
[GATE-PWE-004] Authorize Parallel Groups
    ↓
[GATE-PWE-005] Provision Worktrees
    ↓
[GATE-PWE-006] Execute Workstreams (Parallel)
    ↓
[GATE-PWE-007] Enforce Declared Writes
    ↓
[GATE-PWE-008] Validate Evidence Bundles
    ↓
[GATE-PWE-009] Integrate Patches (Sequential)
    ↓
[GATE-PWE-010] Validate Integration
    ↓
[GATE-PWE-011] Validate Determinism
    ↓
[GATE-PWE-012] Reconcile Registries
    ↓
Evidence-Sealed Parallel Run
```

### Core Components

1. **Write Manifest System**: Declares what each workstream will modify
2. **Conflict Graph Builder**: Computes overlaps and dependency edges
3. **Worktree Provisioner**: Creates isolated git worktrees deterministically
4. **Parallel Executor**: Runs independent workstreams concurrently
5. **Write Enforcer**: Validates no undeclared modifications occurred
6. **Merge Integrator**: Applies patches in control checkout with ordering
7. **Evidence Bundler**: Packages logs, patches, validation results

---

## Missing Files Inventory

### Status: **31 Total Files Missing**

#### Group 1: Core Schemas (6 files)

| File Path | Purpose | Consuming Gates |
|-----------|---------|-----------------|
| `schemas/parallel_workstreams.schema.json` | Validates plan section workstream declarations | GATE_PLAN_SCHEMA_VALIDATE, GATE_WORKSTREAM_SCOPE_VALIDATE |
| `schemas/write_manifest.schema.json` | Validates per-workstream declared write sets | GATE_WRITE_MANIFEST_VALIDATE, GATE_CONFLICT_GRAPH_BUILD |
| `schemas/conflict_graph.schema.json` | Validates conflict graph/DAG output | GATE_CONFLICT_GRAPH_BUILD, GATE_PARALLEL_GROUP_AUTHZ |
| `schemas/worktree_execution_report.schema.json` | Validates workstream execution reports | GATE_WORKSTREAM_EXECUTE, GATE_EVIDENCE_BUNDLE_VALIDATE |
| `schemas/integration_report.schema.json` | Validates merge integration reports | GATE_INTEGRATE_PATCHES, GATE_INTEGRATION_VALIDATE |
| `schemas/evidence_bundle.schema.json` | Validates complete evidence bundle structure | GATE_EVIDENCE_BUNDLE_VALIDATE |

#### Group 2: Template Extensions (3 files)

| File Path | Purpose |
|-----------|---------|
| `template_extensions/parallel_workstreams.section.json` | Defines plan section schema for workstream declarations |
| `template_extensions/parallel_workstreams.gates.json` | Defines gate catalog entries (GATE-PWE-001 through 012) |
| `template_extensions/parallel_workstreams.artifacts.json` | Defines artifact catalog with schema bindings |

#### Group 3: Execution Tools (7 files)

| File Path | Purpose | Produced By Gate | Consumed By Gate |
|-----------|---------|------------------|------------------|
| `tools/validate_parallel_workstreams.py` | Validates workstream scope and required fields | - | GATE_WORKSTREAM_SCOPE_VALIDATE |
| `tools/compute_conflict_graph.py` | Computes conflict graph and parallel groups | GATE_CONFLICT_GRAPH_BUILD | GATE_PARALLEL_GROUP_AUTHZ |
| `tools/provision_worktrees.py` | Creates deterministic git worktrees | GATE_WORKTREE_PROVISION | GATE_WORKSTREAM_EXECUTE |
| `tools/enforce_declared_writes.py` | Validates no undeclared modifications | - | GATE_DECLARED_WRITES_ENFORCEMENT |
| `tools/collect_workstream_evidence.py` | Packages workstream evidence bundles | GATE_WORKSTREAM_EXECUTE | GATE_EVIDENCE_BUNDLE_VALIDATE |
| `tools/integrate_patches.py` | Applies patches in control checkout | GATE_INTEGRATE_PATCHES | GATE_INTEGRATION_VALIDATE |
| `tools/validate_determinism.py` | Validates deterministic outcomes | - | GATE_DETERMINISM_VALIDATE |

#### Group 4: Registries (2 files)

| File Path | Purpose |
|-----------|---------|
| `registries/artifact_inventory.json` | Inventory of produced artifacts with hashes and provenance |
| `registries/policy_registry.json` | SSOT registry of active policies and versions |

#### Group 5: Test Fixtures (3 fixtures + 2 golden files)

| File Path | Purpose |
|-----------|---------|
| `tests/fixtures/parallel_workstreams_minimal_case/` | Golden happy-path fixture |
| `tests/fixtures/conflict_case_overlap_writes/` | Test overlapping write detection |
| `tests/fixtures/undeclared_write_case/` | Test undeclared write enforcement |
| `tests/golden/expected_conflict_graph.json` | Expected conflict graph for validation |
| `tests/golden/expected_evidence_bundle.json` | Expected evidence bundle structure |

#### Group 6: LangGraph Orchestrator Adapters (3 files)

| File Path | Purpose |
|-----------|---------|
| `orchestrator_langgraph/src/acms_orchestrator/tools/conflict_graph.py` | LangGraph adapter for conflict_graph_cli |
| `orchestrator_langgraph/src/acms_orchestrator/tools/worktree_provision.py` | LangGraph adapter for worktree_provision_cli |
| `orchestrator_langgraph/src/acms_orchestrator/tools/dispatch_workers.py` | LangGraph adapter for parallel worker dispatch |

#### Group 7: Documentation (2 files - may exist)

| File Path | Purpose |
|-----------|---------|
| `docs/PARALLEL_WORKSTREAMS_ARCHITECTURE.md` | Architecture and design documentation |
| `docs/PARALLEL_WORKSTREAMS_RUNBOOK.md` | Operator runbook for parallel execution |

---

## Gate Catalog

### Phase: Validate & Authorize

| Gate ID | Name | Script | Purpose |
|---------|------|--------|---------|
| GATE-PWE-001 | Workstream Scope Validate | validate_parallel_workstreams.py | Validate workstream scope and required fields |
| GATE-PWE-002 | Write Manifest Validate | validate_parallel_workstreams.py | Validate declared write manifests |
| GATE-PWE-003 | Conflict Graph Build | compute_conflict_graph.py | Compute conflict graph from write sets |
| GATE-PWE-004 | Parallel Group Authorization | compute_conflict_graph.py | Authorize safe parallel execution groups |

### Phase: Provision & Execute

| Gate ID | Name | Script | Purpose |
|---------|------|--------|---------|
| GATE-PWE-005 | Worktree Provision | provision_worktrees.py | Provision isolated git worktrees |
| GATE-PWE-006 | Workstream Execute | workstream_executor.py | Execute workstreams in parallel |
| GATE-PWE-007 | Declared Writes Enforcement | enforce_declared_writes.py | Validate no undeclared modifications |
| GATE-PWE-008 | Evidence Bundle Validate | collect_workstream_evidence.py | Validate evidence bundles |

### Phase: Integrate & Validate

| Gate ID | Name | Script | Purpose |
|---------|------|--------|---------|
| GATE-PWE-009 | Integrate Patches | integrate_patches.py | Apply patches in control checkout |
| GATE-PWE-010 | Integration Validate | integrate_patches.py | Validate merge results |
| GATE-PWE-011 | Determinism Validate | validate_determinism.py | Validate deterministic outcomes |
| GATE-PWE-012 | Registry Reconcile | rebuild_registries.py | Reconcile registry state |

---

## Key Artifacts Produced

### Planning Artifacts
- `artifacts/workstreams/write_manifests/{workstream_id}.json` - Declared write sets per workstream
- `artifacts/conflict_graph/conflict_graph.json` - Complete conflict/dependency graph
- `artifacts/conflict_graph/parallel_groups.json` - Authorized parallel execution groups

### Execution Artifacts
- `artifacts/worktrees/worktree_map.json` - Worktree ID to path mappings
- `artifacts/workstreams/{workstream_id}/execution_report.json` - Per-workstream execution results
- `artifacts/workstreams/{workstream_id}/patches/` - Generated patches
- `artifacts/workstreams/{workstream_id}/touched_files.json` - Modified files list

### Integration Artifacts
- `artifacts/integration/integration_report.json` - Merge results and conflicts
- `artifacts/integration/applied_patches.json` - Successfully applied patches
- `artifacts/integration/rollback_log.json` - Rollback actions if needed

### Evidence Artifacts
- `evidence/workstreams/{workstream_id}/evidence_bundle.json` - Complete evidence bundle
- `evidence/gates/GATE_*.result.json` - Gate execution results
- `evidence/determinism/determinism_report.json` - Determinism validation results

---

## Implementation Phases

### Phase 1: Schema & Validation Foundation (Week 1)
**Goal:** Establish schemas and basic validation

**Tasks:**
1. Create 6 core schemas (parallel_workstreams, write_manifest, conflict_graph, worktree_execution_report, integration_report, evidence_bundle)
2. Implement `validate_parallel_workstreams.py` with schema validation
3. Create minimal test fixture
4. Write schema validation tests

**Success Criteria:**
- All schemas validate against JSON Schema Draft-07
- Can parse and validate a minimal workstream plan
- GATE-PWE-001 and GATE-PWE-002 pass with test fixture

### Phase 2: Conflict Analysis Engine (Week 2)
**Goal:** Build conflict detection and parallel group authorization

**Tasks:**
1. Implement `compute_conflict_graph.py`
   - Parse write manifests
   - Detect file overlaps
   - Build dependency graph
   - Compute parallel groups via topological sort
2. Create conflict test fixtures
3. Implement golden conflict_graph validation
4. Add GATE-PWE-003 and GATE-PWE-004 execution

**Success Criteria:**
- Conflict graph correctly identifies overlapping writes
- Parallel groups respect dependencies
- Golden conflict_graph test passes deterministically

### Phase 3: Worktree Isolation (Week 3)
**Goal:** Provision isolated execution environments

**Tasks:**
1. Implement `provision_worktrees.py`
   - Create git worktrees deterministically
   - Validate base commit and cleanliness
   - Generate worktree_map.json
2. Implement worktree cleanup utilities
3. Add GATE-PWE-005 execution
4. Test worktree provisioning with multiple workstreams

**Success Criteria:**
- Worktrees created with deterministic names
- Isolated from control checkout
- Can be cleaned up reliably

### Phase 4: Parallel Execution Engine (Week 4)
**Goal:** Execute workstreams in parallel with evidence

**Tasks:**
1. Implement parallel workstream executor
2. Implement `enforce_declared_writes.py`
3. Implement `collect_workstream_evidence.py`
4. Add GATE-PWE-006, GATE-PWE-007, GATE-PWE-008
5. Create undeclared write test fixture

**Success Criteria:**
- Multiple workstreams execute in parallel
- Undeclared writes detected and rejected
- Complete evidence bundles generated

### Phase 5: Integration & Merge (Week 5)
**Goal:** Deterministic merge back to control checkout

**Tasks:**
1. Implement `integrate_patches.py`
   - Apply patches in topological order
   - Detect and report conflicts
   - Support rollback on failure
2. Implement `validate_determinism.py`
3. Add GATE-PWE-009, GATE-PWE-010, GATE-PWE-011
4. Test conflict resolution and rollback

**Success Criteria:**
- Patches applied in correct order
- Conflicts reported with evidence
- Rollback leaves clean state

### Phase 6: LangGraph Integration (Week 6)
**Goal:** Integrate with orchestrator

**Tasks:**
1. Create LangGraph adapter tools
2. Update orchestrator graph with parallel workstream nodes
3. Add checkpoint support for parallel execution
4. Update TOOL_MAPPING.json
5. Test end-to-end orchestrator run

**Success Criteria:**
- Orchestrator can execute parallel workstreams
- Checkpointing works across parallel phases
- Evidence chains properly linked

### Phase 7: Documentation & Hardening (Week 7)
**Goal:** Production-ready feature

**Tasks:**
1. Write PARALLEL_WORKSTREAMS_ARCHITECTURE.md
2. Write PARALLEL_WORKSTREAMS_RUNBOOK.md
3. Create template extensions (3 files)
4. Add registries (artifact_inventory, policy_registry)
5. Comprehensive testing across all fixtures
6. Performance benchmarking

**Success Criteria:**
- Complete documentation
- All 12 gates operational
- Performance improvement >50% for parallel workstreams

---

## Integration with Existing Systems

### newPhasePlanProcess v3.0.0
- Parallel workstreams are an **optional plan section**
- If present, triggers parallel execution path in orchestrator
- If absent, falls back to sequential execution
- All evidence requirements remain the same

### LangGraph Orchestrator
- Add new nodes: `ProvisionWorktrees`, `ExecuteParallel`, `IntegratePatches`
- Extend state model with `workstreams`, `conflict_graph`, `worktree_map`
- Checkpoint support for parallel phase resume
- Tool adapters map to conflict_graph_cli, worktree_provision_cli, etc.

### Registry System
- `registries/artifact_inventory.json` tracks all parallel artifacts
- `registries/policy_registry.json` stores policies used for validation
- Registry reconciliation gate ensures consistency after merge

---

## Prerequisites

### Before Implementation
1. ✅ Entity-scoped solution plan complete (UNIFIED_SOLUTION_PLAN_V3)
2. ✅ Registry runtime engine operational
3. ✅ Evidence sealing system mature
4. ✅ LangGraph orchestrator base implementation stable

### Required Capabilities
- Git worktree support (Git 2.5+)
- Parallel process execution
- File locking for registries
- SHA-256 hashing for evidence
- RFC-6902 JSON patch support

---

## Risks & Mitigations

### Risk 1: Race Conditions in Registry Access
**Mitigation:** Single-writer pattern - only control checkout modifies registries

### Risk 2: Worktree Cleanup Failures
**Mitigation:** Implement robust cleanup with force removal fallback

### Risk 3: Complex Conflict Detection
**Mitigation:** Start with file-level conflicts, expand to semantic conflicts later

### Risk 4: Evidence Chain Complexity
**Mitigation:** Use ArtifactEnvelope pattern consistently, validate at each gate

### Risk 5: Parallel Execution Timeouts
**Mitigation:** Per-workstream timeout policies with graceful degradation

---

## Success Metrics

### Performance
- 50%+ reduction in execution time for 4+ independent workstreams
- Linear scaling up to available CPU cores

### Reliability
- 100% conflict detection rate in test fixtures
- Zero undeclared write escapes
- Complete evidence chains for all parallel runs

### Determinism
- Identical conflict graphs across runs
- Identical merge results given same inputs
- Reproducible evidence bundles

---

## Reference Documents

### Primary Sources
- `C:\Users\richg\Gov_Reg\01260207201000000187_Required Files + Gates + Evidence Map.txt` - Complete requirements map
- `C:\Users\richg\Gov_Reg\01260207201000001221_Multi CLI\patch_parallel_workstream_execution_v3.json` - Feature patch specification
- `C:\Users\richg\Gov_Reg\UNIFIED_SOLUTION_MANIFEST.md` - LangGraph adapter specifications

### Registry References
- File ID: `01260207233100000621` - "Parallel Workstream Execution with Git Worktrees.json"
- Located in: `C:\Users\richg\Gov_Reg\LP_LONG_PLAN\newPhasePlanProcess\`

### Related Plans
- UNIFIED_SOLUTION_PLAN_V3_MERGED.md - Active entity-scoped plan (parallel workstreams NOT included)
- UNIFIED_SOLUTION_PLAN_V3_REMAINING_STEPS.json - Active task list (parallel workstreams NOT included)

---

## AI Execution Guidance

### When to Implement This Feature
1. **After** entity canonicalization is complete
2. **After** registry runtime engine is stable
3. **When** you have multiple independent workstreams that could benefit from parallelization
4. **Before** scaling to 10+ concurrent development efforts

### Implementation Approach
1. Follow the 7-phase implementation plan sequentially
2. Implement schemas first (contract-driven development)
3. Build test fixtures before implementation
4. Validate each gate independently before integration
5. Use golden test artifacts to prove determinism
6. Integrate with LangGraph orchestrator last

### Key Design Principles
- **Fail-closed**: Any conflict detection failure aborts parallel execution
- **Single-writer**: Only control checkout modifies shared state
- **Evidence-first**: Every gate produces evidence before proceeding
- **Deterministic**: Same inputs always produce same conflict graph and merge results
- **Isolated**: Worktrees are completely independent until merge phase

### Testing Strategy
1. Unit tests for each tool script
2. Integration tests for each gate
3. End-to-end tests for complete parallel runs
4. Golden artifact tests for determinism validation
5. Conflict detection tests with overlapping writes
6. Undeclared write enforcement tests

### Common Pitfalls to Avoid
- ❌ Don't allow worktrees to modify registries directly
- ❌ Don't skip conflict graph validation
- ❌ Don't merge patches without topological ordering
- ❌ Don't ignore undeclared write violations
- ❌ Don't proceed without complete evidence bundles

---

## Quick Start Checklist

When ready to implement:

- [ ] Read UNIFIED_SOLUTION_PLAN_V3_MERGED.md (understand prerequisite work)
- [ ] Review `01260207201000000187_Required Files + Gates + Evidence Map.txt` (complete requirements)
- [ ] Study `patch_parallel_workstream_execution_v3.json` (feature specification)
- [ ] Create working branch: `feature/parallel-workstreams`
- [ ] Start with Phase 1: Schema & Validation Foundation
- [ ] Follow 7-phase implementation plan
- [ ] Test against all 3 fixtures at each phase
- [ ] Integrate with LangGraph orchestrator in Phase 6
- [ ] Complete documentation in Phase 7

---

**End of Guide**

*This document is authoritative for implementing the Parallel Workstreams Execution feature. All 31 missing files are cataloged above. Follow the 7-phase plan for successful implementation.*
