# GitHub Automation Planning Section

This file contains only the portions of the uploaded terminal transcript related to GitHub automation planning and the artifacts to create or modify for plan-to-GitHub orchestration.

## Context

The referenced conversation was described as covering:
- GitHub automation files such as `project_item_sync.py/.yml`, milestone sync, phase sync, remote sync, and quality gates
- GitHub Projects V2 features such as issue fields, iteration fields, hierarchy view, and import-by-query
- a recommended autonomous architecture with five phases:
  1. Deterministic intake
  2. Deterministic planning
  3. Execution tracking
  4. Quality / release pipeline
  5. Autonomous reporting and pattern learning

It recommended centralizing policy in one orchestrator, using GitHub as the operational SSOT for work state, and keeping MCP/AI in the reasoning plane rather than the enforcement plane.

## Artifacts to Create

### 1. Master / Portfolio Plan
- `APPLICATION_PROGRAM_PLAN.json`
  - sits above individual phase plans
  - holds application metadata, phase plan registry, dependency DAG, release milestones, GitHub project config, and rollup / reconciliation rules

### 2. Portable Plan Package Spec
- `portable_plan_package.schema.json` (or YAML)
  - defines the self-contained handoff format between CLI applications
  - should include run manifest, policy snapshot, context bundle, current plan, lint reports, dependency graph, execution DAG, GitHub projection manifest, and evidence index

### 3. Plan-to-GitHub Projection Contract
- `plan_github_projection_contract.yaml` (or JSON)
  - formal mapping of plan objects to GitHub issues, sub-issues, milestones, and fields
  - defines ownership for each field and reconciliation precedence rules

### 4. Field Ownership Matrix
- `field_ownership_matrix.yaml`
  - records which actor owns each field and state transition
  - meant to prevent automation collisions

### 5. Worktree / Parallel Execution Schemas and Policies
- `schemas/parallel_workstreams.schema.json`
- `schemas/write_manifest.schema.json`
- `policies/single_writer_policy.yaml`
- `policies/write_policy_registry.yaml`

### 6. Tooling for Parallel Execution Governance
- `tools/compute_conflict_graph.py`
- `tools/enforce_declared_writes.py`
- `tools/integrate_patches.py`
- `tools/validate_determinism.py`

### 7. ProgramSpec Definitions
A declarative, config-driven, idempotent, schema-validated automation spec family intended to replace one-off scripts for intake, sync, and gate checks.

## Artifacts to Modify

### `project_item_sync.py` / workflow
Generalize into a formal projection layer with stable plan-ID to GitHub-ID mappings and idempotency keys.

### milestone completion sync workflow
Wire it into the plan lifecycle state machine.

### splinter phase sync workflow
Evolve it into the authoritative plan-to-GitHub compiler step.

### scheduled orchestrator workflow
Expand it into the central policy and reconciliation controller for:
- drift detection
- stale items
- missing fields
- carryover handling

### phase plan template (`newPhasePlanProcess`)
Add:
- cross-phase identity fields
- `github_projection` section
- `depends_on_phase_plan_ids`
- `program_milestone_id`
- bidirectional reconciliation rules

## Summary of Gaps Identified

1. No explicit plan-to-GitHub compiler
2. No field ownership matrix
3. No formal mapping from plan lifecycle to GitHub state machine
4. No portable plan package contract
5. No `APPLICATION_PROGRAM_PLAN`
6. Other later design notes also identified missing linkage, reconciliation, and registry artifacts

## Additional Design Decisions and Build Order

### Resolved design points
- milestones should represent delivery checkpoints, not phases
- evidence should be linked back to GitHub artifacts after sealing
- reconciliation should be level-triggered and self-healing

### Open decisions blocking implementation
1. Who creates the canonical plan YAML that drives projection?
2. How should override workflow approvals and `github_override_registry.json` be handled?
3. Is a self-hosted Windows runner available, or is a Linux fallback required?

### Proposed build order
1. `config/step_issue_linkage.json`
2. schema files from the architecture delta
3. `bootstrap-github-fields.yml`
4. `GH_PROJECTION_GENERATE` and `GH_PROJECTION_APPLY`
5. update `TEMP_branch-handler`
6. `ssot-drift-reconciliation.yml`
7. `phase-advancement-evaluator.yml`
8. `policies/github_sync_governance.yaml`
