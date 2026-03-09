# Issue Remediation Implementation Checklist

**Quick Reference for Developers**

---

## Phase 1: Executor Output Enforcement (1 Day)

### FCA-001: Pipeline Runner Envelope Validation

**Files to Create:**
- [ ] `src/utils/envelope_normalizer.py`
- [ ] `tests/test_pipeline_runner_envelope.py`

**Files to Modify:**
- [ ] `src/pipeline_runner.py` (add validation + normalization)

**Tests to Pass:**
- [ ] Valid output without "data" wrapper → normalized and staged
- [ ] Invalid envelope → rejected with error
- [ ] Normalized envelope → staged exactly once

**Evidence:**
- [ ] `.state/evidence/phase1/envelope_validation_report.json`
- [ ] `.state/evidence/phase1/staged_output_manifest.json`

---

## Phase 2: Identity & Metadata (5 Days)

### FCA-005: file_id Resolution

**Files to Create:**
- [ ] `src/identity/file_id_resolver.py`
- [ ] `tests/test_file_id_resolution.py`

**Files to Modify:**
- [ ] `src/pipeline_runner.py` (add identity contract check)

**Tests to Pass:**
- [ ] SHA256 → 20-digit file_id mapping succeeds
- [ ] Promotion blocked without file_id resolution
- [ ] Identity contract validation passes

---

### FCA-010, FCA-011, FCA-013, FCA-015: Metadata Backfill

**Files to Create:**
- [ ] `scripts/backfill_doc_id.py`
- [ ] `scripts/backfill_file_size.py`
- [ ] `scripts/backfill_canonicality.py`
- [ ] `scripts/infer_repo_root_id.py`
- [ ] `scripts/prune_orphaned_entries.py`
- [ ] `src/identity/sha256_deduplicator.py`
- [ ] `tests/test_metadata_backfill.py`

**Tests to Pass:**
- [ ] 0 records with null doc_id after backfill
- [ ] 0 records with null file_size after backfill
- [ ] 0 records with null canonicality after backfill
- [ ] 46 repo_root_id records resolved
- [ ] 243 orphaned entries pruned
- [ ] 1 duplicate SHA256 resolved

**Evidence:**
- [ ] `.state/evidence/phase2/identity_resolution_manifest.json`
- [ ] `.state/evidence/phase2/metadata_backfill_report.json`
- [ ] `.state/evidence/phase2/duplicate_resolution.json`

---

## Phase 3: Defaults & Postconditions (2 Days)

### FCA-002, FCA-017: Default Injection & Null Coalescing

**Files to Modify:**
- [ ] `schema/COLUMN_DICTIONARY.json` (add actionable defaults)
- [ ] `src/default_injector.py` (implement default logic)
- [ ] `src/null_coalescer.py` (add precondition checks)

**Files to Create:**
- [ ] `tests/test_default_injection.py`
- [ ] `tests/test_null_coalescing.py`

**Tests to Pass:**
- [ ] Records with null fields receive declared defaults
- [ ] Postcondition validation passes after injection
- [ ] Null coalescer reduces null count
- [ ] Precondition check fails if defaults not active

**Evidence:**
- [ ] `.state/evidence/phase3/default_injection_report.json`
- [ ] `.state/evidence/phase3/default_semantics_report.json`

---

## Phase 4: Schema & Field Authority (2 Days)

### FCA-004: Timestamp Clusterer Field Fix

**Files to Modify:**
- [ ] `src/timestamp_clusterer.py` (use authoritative field name)

**Files to Create:**
- [ ] `tests/test_timestamp_clustering.py`

**Tests to Pass:**
- [ ] Clusterer uses correct timestamp field from schema
- [ ] Clusters are non-empty
- [ ] Input contract validation passes

---

### FCA-014, FCA-016: Schema Alignment

**Files to Modify:**
- [ ] `schema/COLUMN_DICTIONARY.json` (add 6 undocumented columns)
- [ ] `src/column_validator.py` (enforce schema authority)

**Files to Create:**
- [ ] `schema/governance_registry_schema.v4.json` (or downgrade plan)

**Tests to Pass:**
- [ ] All registry columns documented in schema
- [ ] Schema version matches registry version
- [ ] Column validator passes with zero drift

**Evidence:**
- [ ] `.state/evidence/phase4/schema_alignment_report.json`
- [ ] Governance approval log (for new columns)

---

## Phase 5: Validation Gates & Idempotency (3 Days)

### FCA-003: E2E Validator Enhancement

**Files to Modify:**
- [ ] `src/e2e_validator.py` (add required column validation)
- [ ] `src/pipeline_runner.py` (enforce gate before promotion)

**Files to Create:**
- [ ] `tests/test_e2e_required_columns.py`

**Tests to Pass:**
- [ ] Outputs missing required columns fail gate
- [ ] Invalid outputs blocked from promotion
- [ ] Policy-level invariants validated

---

### FCA-008, FCA-009: Fingerprint & Idempotency

**Files to Create:**
- [ ] `src/utils/fingerprint.py`
- [ ] `tests/test_idempotency.py`

**Files to Modify:**
- [ ] `src/pipeline_runner.py` (add fingerprint logic)
- [ ] All automation scripts (integrate fingerprint)

**Tests to Pass:**
- [ ] Fingerprint computed from inputs + spec version
- [ ] Identical inputs skip execution, return cached result
- [ ] Fingerprint store updated after execution

---

### FCA-018: Documentation Sync

**Files to Create:**
- [ ] `scripts/generate_script_index.py`
- [ ] `src/doc_validator.py`

**Tests to Pass:**
- [ ] SCRIPT_INDEX.md auto-generated and complete
- [ ] Documentation validator passes with zero drift
- [ ] All scripts listed in index

**Evidence:**
- [ ] `.state/evidence/phase5/validation_gate_report.json`
- [ ] `.state/evidence/phase5/fingerprint_skip_log.json`
- [ ] Updated SCRIPT_INDEX.md

---

## Phase 6: Mutation Safety & Integration (3 Days)

### FCA-006, FCA-007: Mutation Write Paths

**Files to Create:**
- [ ] `src/mutation/mutation_contract.py`
- [ ] `src/mutation/lock_manager.py`
- [ ] `src/mutation/rollback_generator.py`
- [ ] `tests/test_doc_id_mutation.py`
- [ ] `tests/test_module_dedup_mutation.py`

**Files to Modify:**
- [ ] `src/doc_id_resolver.py` (add write path + mutation contract)
- [ ] `src/module_dedup.py` (add write path + path canonicalization)

**Tests to Pass:**
- [ ] doc_id resolver writes collision resolution to registry
- [ ] module_dedup writes deduplication resolution to registry
- [ ] Rollback artifacts created before mutations
- [ ] Lock acquired before write, released after

---

### FCA-012: Relationship Generation

**Files to Create:**
- [ ] `scripts/build_edges.py`
- [ ] `tests/test_edges_generation.py`

**Tests to Pass:**
- [ ] edges[] populated with relationships
- [ ] Relationship count > 0
- [ ] Referential integrity maintained

---

### FCA-019: Phase Integration

**Files to Modify:**
- [ ] `src/phase_a_transformer.py` (define output contract)

**Files to Create:**
- [ ] `src/phase_b_processor.py` (or update existing)
- [ ] `tests/test_phase_integration.py`

**Tests to Pass:**
- [ ] Phase A output validates against contract
- [ ] Phase B consumes Phase A output successfully
- [ ] Contract validation passes

**Evidence:**
- [ ] `.state/evidence/phase6/mutation_safety_report.json`
- [ ] `.state/evidence/phase6/lock_ledger.json`
- [ ] `.state/rollback/` (rollback artifacts)

---

## Testing Commands

```bash
# Run all tests
pytest tests/

# Run tests for specific phase
pytest tests/test_pipeline_runner_envelope.py
pytest tests/test_file_id_resolution.py
pytest tests/test_metadata_backfill.py
pytest tests/test_default_injection.py
pytest tests/test_timestamp_clustering.py
pytest tests/test_e2e_required_columns.py
pytest tests/test_idempotency.py
pytest tests/test_doc_id_mutation.py
pytest tests/test_edges_generation.py
pytest tests/test_phase_integration.py

# Run with coverage
pytest --cov=src --cov-report=html tests/
```

---

## Validation Commands

```bash
# Validate matrix completeness
python scripts/validate_matrix_completeness.py \
  --matrix CONTRACT_GAP_MATRIX.md \
  --json .state/matrix/contract_gap_matrix.json

# Validate schema alignment
python scripts/validate_schema_alignment.py \
  --schema schema/COLUMN_DICTIONARY.json \
  --registry registry.json

# Validate documentation
python src/doc_validator.py \
  --scripts scripts/ \
  --index SCRIPT_INDEX.md

# Validate evidence
python scripts/validate_evidence.py \
  --phase all \
  --evidence-dir .state/evidence/
```

---

## Evidence Generation

Each phase must create:
- `execution.log`
- `validation_report.json`
- `metrics.json`
- `test_results.json`

Example:
```bash
# After Phase 1
ls .state/evidence/phase1/
# Should show:
# - execution.log
# - validation_report.json
# - metrics.json
# - test_results.json
# - envelope_validation_report.json
# - staged_output_manifest.json
```

---

## Rollback Commands

```bash
# Create snapshot before phase
python scripts/snapshot_registry.py \
  --phase 1 \
  --out .state/rollback/pre_phase1_snapshot.json

# Rollback phase
python scripts/rollback_phase.py \
  --phase 1 \
  --snapshot .state/rollback/pre_phase1_snapshot.json
```

---

## Progress Tracking

**Phase 1:** [ ] Complete  
**Phase 2:** [ ] Complete  
**Phase 3:** [ ] Complete  
**Phase 4:** [ ] Complete  
**Phase 5:** [ ] Complete  
**Phase 6:** [ ] Complete  

**Issues Closed:** 0 / 19  
**Critical Issues Remaining:** 6  
**High Priority Remaining:** 5  
**Medium Priority Remaining:** 8

---

*Last Updated: 2026-03-08*  
*For detailed plan: ISSUE_REMEDIATION_PLAN.md*
