# Parallel Workstreams Execution Runbook

## Quick Start

This runbook provides step-by-step procedures for using the Parallel Workstreams Execution (PWE) system.

## Prerequisites

- Git repository with clean working directory
- Python 3.8+ with `jsonschema` package installed
- All PWE scripts in `01260207201000001276_scripts/`
- All PWE schemas in `01260207201000001275_schemas/`

## Procedure 1: Create Parallel Workstreams Plan

### Step 1: Define Workstreams

Create a plan JSON file with `parallel_workstreams` section:

```json
{
  "parallel_workstreams": {
    "workstreams": [
      {
        "workstream_id": "ws_feature_a",
        "write_manifest": "manifests/ws_feature_a.json",
        "dependencies": [],
        "priority": 5
      },
      {
        "workstream_id": "ws_feature_b",
        "write_manifest": "manifests/ws_feature_b.json",
        "dependencies": [],
        "priority": 5
      }
    ],
    "max_parallel_workstreams": 4,
    "circuit_breakers": {
      "max_failed_workstreams": 1,
      "max_total_failures": 3
    }
  }
}
```

### Step 2: Create Write Manifests

For each workstream, create a write manifest declaring all file writes:

```json
{
  "workstream_id": "ws_feature_a",
  "declared_writes": [
    "src/feature_a/module.py",
    "tests/test_feature_a.py"
  ],
  "declared_reads": [
    "src/config/settings.py"
  ],
  "exclusive_locks": [],
  "intent": "Implement feature A",
  "estimated_duration_seconds": 120,
  "created_at": "2026-03-07T00:00:00Z",
  "schema_version": "1.0.0"
}
```

**Critical**: Ensure declared_writes is complete and accurate. Undeclared writes will fail GATE-PWE-007.

## Procedure 2: Validate Configuration

### Step 1: Run Validation Script

```powershell
python 01260207201000001276_scripts\validate_parallel_workstreams.py `
  --plan plan.json `
  --output-dir .
```

### Step 2: Check Gate Results

Verify both gates passed:
- `evidence/gates/GATE-PWE-001.result.json` - passed: true
- `evidence/gates/GATE-PWE-002.result.json` - passed: true

### Troubleshooting

**Error: "Duplicate workstream_id"**
- Fix: Ensure all workstream_ids are unique

**Error: "Write manifest not found"**
- Fix: Verify write_manifest paths are correct relative to plan directory

**Error: "Empty declared_writes"**
- Fix: Add at least one file to declared_writes array

## Procedure 3: Compute Conflict Graph

### Step 1: Run Conflict Graph Computation

```powershell
python 01260207201000001276_scripts\compute_conflict_graph.py `
  --plan plan.json `
  --output-dir . `
  --max-parallel 4
```

### Step 2: Review Conflict Graph

Check `artifacts/conflict_graph/conflict_graph.json`:
- **nodes**: All workstreams
- **edges**: Conflicts detected (write-write, write-read, resource_lock, dependency)
- **parallel_groups**: Groups of workstreams that can execute in parallel

### Step 3: Review Parallel Groups

Check `artifacts/conflict_graph/parallel_groups.json`:
- Each group contains workstreams that have no conflicts with each other
- Groups execute sequentially, workstreams within a group execute in parallel

### Troubleshooting

**Issue: All workstreams in separate groups (no parallelism)**
- Cause: Write conflicts detected between all pairs
- Fix: Review write manifests - ensure workstreams touch different files

**Error: "Max parallelism exceeds limit"**
- Cause: A single parallel group has more workstreams than max_parallel
- Fix: Reduce max_parallel or split workstreams

## Procedure 4: Provision Worktrees

### Step 1: Run Worktree Provisioning

```powershell
python 01260207201000001276_scripts\provision_worktrees.py `
  --run-id run_001 `
  --plan plan.json `
  --base-commit HEAD `
  --output-dir .
```

### Step 2: Verify Worktrees Created

```powershell
git worktree list
```

Should show worktrees at:
- `worktrees/run_001/ws_feature_a/`
- `worktrees/run_001/ws_feature_b/`

### Step 3: Check Worktree Map

Verify `artifacts/worktrees/worktree_map.json` contains paths for all workstreams.

### Troubleshooting

**Error: "Would exceed max_total_worktrees limit"**
- Cause: Too many existing worktrees
- Fix: Clean up old worktrees with `git worktree prune`

**Error: "Base commit has uncommitted changes"**
- Cause: Working directory is dirty
- Fix: Commit or stash changes before provisioning

## Procedure 5: Execute Workstreams (Manual)

For each workstream:

### Step 1: Navigate to Worktree

```powershell
cd worktrees\run_001\ws_feature_a
```

### Step 2: Execute Workstream Tasks

Perform the development work (coding, testing, etc.)

### Step 3: Verify Changes Match Manifest

```powershell
git diff --name-only HEAD
```

Ensure all modified files are in declared_writes.

## Procedure 6: Enforce Declared Writes

### Step 1: Run Enforcement Check

```powershell
python 01260207201000001276_scripts\enforce_declared_writes.py `
  --worktree worktrees\run_001\ws_feature_a `
  --manifest manifests\ws_feature_a.json `
  --output-dir .
```

### Step 2: Check Gate Result

Verify `evidence/gates/GATE-PWE-007.result.json` shows passed: true

### Troubleshooting

**Error: "Found undeclared writes"**
- Cause: Workstream modified files not in declared_writes
- Fix: Either add files to manifest (if intentional) or revert the changes

## Procedure 7: Collect Evidence

### Step 1: Run Evidence Collection

```powershell
python 01260207201000001276_scripts\collect_workstream_evidence.py `
  --run-id run_001 `
  --workstream-id ws_feature_a `
  --evidence-dir evidence `
  --artifacts-dir artifacts
```

### Step 2: Verify Evidence Bundle

Check `evidence/workstreams/ws_feature_a/evidence_bundle.json`:
- **gate_results**: All gates passed
- **artifacts**: All execution artifacts listed
- **hash_manifest**: SHA-256 hashes computed

## Procedure 8: Integrate Patches

### Step 1: Generate Patches

For each worktree, create unified diff patches:

```powershell
cd worktrees\run_001\ws_feature_a
git diff HEAD > ..\..\..\..\artifacts\patches\ws_feature_a\feature.patch
```

### Step 2: Run Integration

```powershell
python 01260207201000001276_scripts\integrate_patches.py `
  --parallel-groups artifacts\conflict_graph\parallel_groups.json `
  --patches-dir artifacts\patches `
  --output-dir .
```

### Step 3: Review Integration Report

Check `artifacts/integration/integration_report.json`:
- **applied_patches**: All patches applied successfully
- **failed_patches**: Should be empty
- **conflicts**: Should be empty
- **rollback_occurred**: Should be false

### Troubleshooting

**Error: Patch fails to apply**
- Cause: Patch conflicts with current state
- Fix: Review integration_order - may need to rebase patches

**Issue: Rollback occurred**
- Cause: Integration conflict detected
- Fix: Review failed_patches, resolve conflicts, regenerate patches

## Procedure 9: Validate Determinism

### Step 1: Run Determinism Check

```powershell
python 01260207201000001276_scripts\validate_determinism.py `
  --plan plan.json `
  --num-runs 3 `
  --output-dir .
```

### Step 2: Check Determinism Report

Verify `evidence/determinism/determinism_report.json`:
- **determinism_validated**: true
- **hash_match**: true
- **hashes**: All identical

### Troubleshooting

**Error: "Hash mismatch across runs"**
- Cause: Non-deterministic computation (timestamps, randomness)
- Fix: Review compute_conflict_graph.py - ensure all fields are deterministic

## Procedure 10: Cleanup

### Step 1: Remove Worktrees

```powershell
git worktree remove --force worktrees\run_001\ws_feature_a
git worktree remove --force worktrees\run_001\ws_feature_b
```

### Step 2: Prune Stale References

```powershell
git worktree prune
```

### Step 3: Archive Evidence

Move evidence bundles to permanent storage:

```powershell
Move-Item evidence\workstreams archive\run_001\
```

## Emergency Procedures

### Rollback Failed Integration

If integration fails and rollback doesn't complete:

```powershell
git reset --hard HEAD
git clean -fd
```

### Cleanup Stuck Worktrees (Windows)

If worktree removal fails due to file locks:

```powershell
# Stop any processes using the worktree
# Then force remove
Remove-Item -Recurse -Force worktrees\run_001\ws_feature_a
git worktree prune
```

### Recover from Circuit Breaker Trip

If circuit breaker halts execution:

1. Review failed workstream logs
2. Fix the issue
3. Reset circuit breaker counters (if supported)
4. Re-run from last successful gate

## Performance Tips

### Reduce Worktree Overhead

- Use `--shallow-clone` for large repositories
- Provision worktrees on fast SSD storage
- Limit max_parallel_workstreams to available CPU cores

### Speed Up Conflict Detection

- Keep write manifests small and precise
- Use file path prefixes to quickly rule out conflicts
- Cache conflict graph results for unchanged plans

### Optimize Patch Integration

- Combine small patches to reduce git apply overhead
- Use `--3way` merge for better conflict resolution
- Apply patches in batches per parallel group

## Monitoring

### Key Metrics

- **Parallel Efficiency**: workstreams_parallel / total_workstreams
- **Conflict Rate**: conflict_edges / possible_edges
- **Gate Pass Rate**: passed_gates / total_gates
- **Integration Success Rate**: applied_patches / total_patches

### Health Checks

Run after each execution:

```powershell
# Check all gates passed
Get-ChildItem evidence\gates\*.json | ForEach-Object {
  $gate = Get-Content $_ | ConvertFrom-Json
  if (-not $gate.passed) {
    Write-Warning "Gate $($gate.gate_id) failed: $($gate.error)"
  }
}

# Verify determinism
python 01260207201000001276_scripts\validate_determinism.py --plan plan.json
```

## Support

For issues not covered in this runbook:
- Review architecture doc: `docs/PARALLEL_WORKSTREAMS_ARCHITECTURE.md`
- Check gate results in `evidence/gates/` for detailed errors
- Examine integration report for patch application failures
- Validate evidence bundles have correct SHA-256 hashes

## Version

- Runbook Version: 1.0.0
- Compatible with: PWE System v1.0.0
- Last Updated: 2026-03-07
