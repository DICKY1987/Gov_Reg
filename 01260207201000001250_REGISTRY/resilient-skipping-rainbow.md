# Master Plan: Registry Automation — All 4 Work Streams

## Context
The REGISTRY_AUTOMATION folder contains 19 Python scripts that work as a toolkit but are not yet
a config-driven, contract-enforced automation platform. The COLUMN_HEADERS folder contains the
authoritative governance contracts (185-column dictionary, write policy, derivation specs) that
SHOULD drive runtime behavior but currently don't. The ChatGPT alignment assessment confirmed the
system is 35–45% structurally aligned and 15–25% operationally aligned with the target
ProgramSpec-based architecture described in:
  `C:\Users\richg\Gov_Reg\01260207201000001221_Multi CLI\Reusable gates and automation.txt`

This plan covers all 4 requested work streams in dependency order.

---

## Critical File Paths

| Role | Path |
|------|------|
| Scripts dir | `...\REGISTRY\REGISTRY_AUTOMATION\scripts\` |
| Column Dictionary | `...\REGISTRY\COLUMN_HEADERS\01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json` |
| Write Policy YAML | `...\REGISTRY\COLUMN_HEADERS\01260207201000000193_UNIFIED_SSOT_REGISTRY_WRITE_POLICY.yaml` |
| ProgramSpec reference | `C:\Users\richg\Gov_Reg\01260207201000001221_Multi CLI\Reusable gates and automation.txt` |
| Issues report | `...\REGISTRY_AUTOMATION\ADDITIONAL_ISSUES_REPORT.md` |
| ChatGPT assessment | `C:\Users\richg\Gov_Reg\ChatGPT-Automation Alignment Assessment.md` |

---

## Work Stream 1: Fix Critical Bugs (Do First — Unblocks Everything Else)

### Bug 1 — pipeline_runner.py silent-fail (HIGH — blocks all staging)
**File:** `scripts/P_01999000042260305017_pipeline_runner.py` line 79
**Root cause:** `transform_phase_a_output()` returns a flat dict `{col: val}`.
  Pipeline checks `transformed.get("data")` which is ALWAYS False.
  The `"data"` wrapper only exists in `transform_file()` output, which is never called here.

**Fix:** Change lines 76–87 staging block:
```python
# BEFORE (broken):
transformed = result.get("transformed", {})
if file_id and transformed.get("data"):
    ...write transformed["data"]...

# AFTER (fixed):
transformed = result.get("transformed", {})
if file_id and transformed:   # flat dict is truthy when non-empty
    staging_dir = self.output_dir / "staging"
    staging_dir.mkdir(exist_ok=True)
    staging_file = staging_dir / f"{file_name}.json"
    with open(staging_file, 'w', encoding='utf-8') as sf:
        json.dump({"file_id": file_id, "data": transformed}, sf, indent=2)
```

### Bug 2 — timestamp_clusterer.py field name mismatch (MEDIUM)
**File:** `scripts/P_01999000042260305015_timestamp_clusterer.py` lines 18, 24–25
**Root cause:** Code reads `f.get("created_at", "")` but registry field is `allocated_at`
  (confirmed by COLUMN_DICTIONARY and write policy YAML).

**Fix:** Replace all `"created_at"` references with `"allocated_at"` (or `"created_utc"` —
  confirm the actual field name in the live registry JSON before patching).

### Bug 3 — 4 CRITICAL data quality issues (via new backfill scripts)
Requires new scripts (part of Work Stream 4, but listed here as bugs):
1. Missing `doc_id`, `file_size`, `canonicality` on 100% of records → `metadata_backfill.py`
2. Empty `edges[]` array → `edges_builder.py`
3. 243/245 `entries[]` records orphaned → `entries_pruner.py`
4. 46 files missing `repo_root_id` → `repo_root_inferrer.py`

---

## Work Stream 2: Contract-Gap Matrix

### Purpose
Convert each known issue from "script bug" language into ProgramSpec/framework language.
Output is a machine-readable matrix that becomes the authoritative issue catalog.

### Output File
`C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY\REGISTRY_AUTOMATION\docs\CONTRACT_GAP_MATRIX.md`

### Matrix Schema (one row per issue)
| Field | Description |
|-------|-------------|
| `issue_id` | FCA-001, FCA-002, ... |
| `current_component` | Script filename |
| `framework_category` | Gate / Phase / Mutation / Transport / Executor |
| `broken_contract` | One of 8 standard contract types (see below) |
| `symptom` | Observable failure behavior |
| `root_cause` | Technical explanation |
| `required_runner_capability` | What a shared runner should enforce |
| `required_spec_fields` | ProgramSpec fields that should declare the rule |
| `evidence_required` | Artifacts that prove the issue is fixed |
| `remediation_type` | code_fix / schema_fix / spec_fix / runner_fix / policy_fix / data_backfill |
| `verification_test` | Deterministic pass/fail test description |
| `priority` | critical / high / medium |

### Standard Contract Types (taxonomy section of matrix)
1. `input_contract` — required inputs present and valid before execution
2. `identity_contract` — file_id resolution and canonicalization
3. `output_result_envelope_contract` — consistent result shape between components
4. `evidence_contract` — artifacts proving execution outcome
5. `pass_fail_criteria_contract` — binary gate decision rules
6. `mutation_safety_contract` — lock, backup, rollback before writes
7. `rollback_contract` — undo artifacts required before commit
8. `fingerprint_idempotency_contract` — skip-if-same-inputs behavior

### Pre-seeded rows (from confirmed analysis)
| issue_id | component | category | broken_contract | remediation_type | priority |
|----------|-----------|----------|-----------------|------------------|----------|
| FCA-001 | pipeline_runner.py | Executor | output_result_envelope_contract | code_fix | critical |
| FCA-002 | default_injector.py | Phase | input_contract + pass_fail_criteria | schema_fix + data_backfill | medium |
| FCA-003 | e2e_validator.py | Gate | evidence_contract + pass_fail_criteria | runner_fix + schema_fix | high |
| FCA-004 | timestamp_clusterer.py | Phase | input_contract (wrong field name) | code_fix | medium |
| FCA-005 | pipeline_runner.py | Executor | identity_contract (FILE_ID_MISMATCH) | spec_fix + code_fix | critical |
| FCA-006 | doc_id_resolver.py | Gate+Mutation | mutation_safety_contract (read-only, no write) | runner_fix | medium |
| FCA-007 | module_dedup.py | Gate+Mutation | mutation_safety_contract (read-only, no write) | runner_fix | medium |
| FCA-008 | e2e_validator.py | Gate | fingerprint_idempotency_contract (missing) | spec_fix | high |
| FCA-009 | all scripts | Executor | fingerprint_idempotency_contract (no skip logic) | runner_fix | high |
| FCA-010 | registry (data) | Mutation | identity_contract (missing metadata 100%) | data_backfill | critical |
| FCA-011 | registry (data) | Mutation | identity_contract (repo_root_id 31.5% missing) | data_backfill | critical |
| FCA-012 | registry (data) | Mutation | evidence_contract (edges[] empty) | data_backfill | critical |
| FCA-013 | registry (data) | Mutation | identity_contract (243/245 entries orphaned) | data_backfill | critical |

---

## Work Stream 3: Wire COLUMN_HEADERS Governance to Runtime

### Problem
The COLUMN_HEADERS folder contains the authoritative contract for every column:
- What type is expected (`value_schema`)
- Whether it's required or optional (`presence.policy`)
- How defaults should behave (`derivation`)
- Write rules (`update_policy`, `writable_by`, `null_policy`)

None of this is read by the REGISTRY_AUTOMATION scripts at runtime. Scripts hardcode behavior.

### What already exists (reuse these)
- `P_01999000042260305005_column_loader.py` — already loads 185 columns from COLUMN_DICTIONARY.json
  - Has: `get_all_columns()`, `get_default_value()`, `load_columns()`, phase-specific filtering
  - IS imported by `default_injector.py` and `column_validator.py`
- `P_01999000042260305006_column_validator.py` — validates types against loaded schema
- Write Policy YAML — defines `null_policy`, `update_policy`, `writable_by`, `merge_strategy` per column

### Work to do
**Step 3a — Extend column_loader.py to expose write policy fields**
  Read from `UNIFIED_SSOT_REGISTRY_WRITE_POLICY.yaml` in addition to COLUMN_DICTIONARY.json.
  Add methods: `get_update_policy(col)`, `get_null_policy(col)`, `get_writable_by(col)`.

**Step 3b — Fix default_injector.py to use column dictionary defaults**
  Current: all defaults are `None` → injector is inert.
  Fix: read `derivation.null_policy` and `derivation.default_value` from column_loader.
  If `null_policy = forbid_null` and no value, treat as missing and flag in output.

**Step 3c — Strengthen e2e_validator.py with column dictionary enforcement**
  Current: shallow structure check only.
  Add: check REQUIRED columns (where `presence.policy = REQUIRED`) are non-null in every record.
  Read the list of REQUIRED columns from column_loader at validation time.

**Step 3d — Fix null_coalescer.py** (inert because default_injector is inert)
  Once 3b is fixed, null_coalescer will have real defaults to coalesce to. No code change needed.

**Step 3e — Wire write policy into patch_generator.py**
  Before applying an RFC-6902 patch, verify each modified column has `writable_by ≠ never`.
  Block immutable column writes (where `update_policy = immutable` and record already exists).

---

## Work Stream 4: ProgramSpec Framework Design

### Target Architecture (from `Reusable gates and automation.txt`)
```
REGISTRY_AUTOMATION/
├── programs/           # *.spec.json — one per automation unit
├── runners/            # GateRunner, PhaseRunner, MutationRunner, ExecutorRunner
├── schemas/            # ProgramSpec schema, GateResult schema, PhaseResult schema
├── library/            # Shared imperative code (move existing scripts here as modules)
├── results/            # GateResult, PhaseResult stable output envelopes
├── heal_sequences/     # Remediation templates
└── scripts/            # KEEP existing scripts as-is during transition
```

### ProgramSpec fields (per reference document)
```json
{
  "program_id": "ENUM-DRIFT-GATE-001",
  "category": "Gate",
  "version": "1.0.0",
  "inputs": [...],
  "steps": [...],
  "locks_write_policy": {...},
  "evidence_contract": {...},
  "pass_criteria": {...},
  "fingerprint_contract": {...},
  "outputs": {...},
  "remediation": {...}
}
```

### Component-to-Category mapping (current scripts → future specs)
| Current Script | Category | Spec ID |
|---------------|----------|---------|
| enum_drift_gate.py | Gate | ENUM-DRIFT-GATE-001 |
| e2e_validator.py | Gate | E2E-VALIDATE-GATE-001 |
| doc_id_resolver.py | Gate | DOCID-COLLISION-GATE-001 |
| module_dedup.py | Gate | MODULE-DEDUP-GATE-001 |
| phase_a_transformer.py | Phase | PHASE-A-TRANSFORM-001 |
| default_injector.py | Phase | DEFAULT-INJECT-PHASE-001 |
| null_coalescer.py | Phase | NULL-COALESCE-PHASE-001 |
| sha256_backfill.py | Mutation | SHA256-BACKFILL-MUT-001 |
| patch_generator.py | Mutation | RFC6902-PATCH-MUT-001 |
| file_id_reconciler.py | Mutation | FILE-ID-RECON-MUT-001 |
| pipeline_runner.py | Executor | BATCH-INTAKE-EXEC-001 |
| intake_orchestrator.py | Executor | FILE-INTAKE-EXEC-001 |
| run_metadata_collector.py | Executor (support) | RUN-META-EXEC-001 |
| timestamp_clusterer.py | Phase | TIMESTAMP-CLUSTER-PHASE-001 |

### New scripts needed (from ADDITIONAL_ISSUES_REPORT.md)
| Script | Category | Priority |
|--------|----------|----------|
| metadata_backfill.py | Mutation | Critical |
| repo_root_inferrer.py | Phase | Critical |
| edges_builder.py | Mutation | High |
| entries_pruner.py | Mutation | High |
| file_id_mapping_layer.py | Phase | High (unblocks py_* promotion) |

### Migration approach (3 phases, no breaking changes)
**Phase A — Wrap existing scripts behind specs (no code changes to scripts)**
  - Create `programs/` directory
  - Write `.spec.json` for each existing script using the mapping table above
  - Write a `ProgramSpec` JSON schema in `schemas/`
  - Write a spec-discovery CLI (`scan_programs.py`) that validates all specs against the schema

**Phase B — Build shared runners**
  - `runners/gate_runner.py` — reads GateSpec, runs validation, enforces exit codes, writes GateResult
  - `runners/mutation_runner.py` — reads MutationSpec, acquires locks, applies with backup, writes MutationResult
  - Scripts become library modules (move logic into `library/`, keep thin CLI wrappers)

**Phase C — Fingerprint + idempotency**
  - Add `fingerprint_contract` to each spec
  - Runner computes fingerprint from inputs + spec version
  - Store fingerprints in `results/fingerprints.json`
  - Skip execution if fingerprint already exists (unless `--force`)

---

## Execution Order

1. **Work Stream 1, Bug 1** — Fix pipeline_runner.py (1 line change, immediate unblock)
2. **Work Stream 1, Bug 2** — Fix timestamp_clusterer.py field name
3. **Work Stream 2** — Write CONTRACT_GAP_MATRIX.md (research/writing task)
4. **Work Stream 3a + 3b** — Extend column_loader, fix default_injector
5. **Work Stream 3c** — Strengthen e2e_validator with REQUIRED column enforcement
6. **Work Stream 3e** — Wire write policy into patch_generator
7. **Work Stream 4, Phase A** — Write program specs for all existing scripts
8. **Work Stream 1, Bug 3** — New backfill scripts (metadata, repo_root, edges, entries_pruner)
9. **Work Stream 4, Phase B** — Build shared runners
10. **Work Stream 4, Phase C** — Fingerprint + idempotency

---

## Verification

| Step | Verification |
|------|-------------|
| Bug 1 fix | Run pipeline_runner on test file → staging/ directory has output files (not empty) |
| Bug 2 fix | Run timestamp_clusterer → clusters are non-empty and timestamps parse without error |
| WS3a | column_loader.get_update_policy("file_id") returns "immutable" |
| WS3b | default_injector output contains non-None values for columns with declared defaults |
| WS3c | e2e_validator fails on record missing a REQUIRED column |
| WS3e | patch_generator rejects patch modifying an immutable column |
| WS2 matrix | CONTRACT_GAP_MATRIX.md has ≥13 rows, each with all 11 fields populated |
| WS4A | scan_programs.py validates all *.spec.json with 0 schema errors |
| WS4B | gate_runner.py runs enum_drift_gate spec and produces GateResult JSON |
