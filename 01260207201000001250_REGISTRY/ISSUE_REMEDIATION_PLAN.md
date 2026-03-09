# Registry Automation Issue Remediation Plan

**Date:** 2026-03-08  
**Status:** ACTIVE  
**Based On:** CONTRACT_GAP_MATRIX.md (19 issues)  
**Execution Model:** Phased, dependency-ordered delivery

---

## Executive Summary

This plan addresses all 19 issues identified in the Contract-Gap Matrix by organizing them into 6 dependency-ordered remediation phases. Each phase is independently executable and builds on the outputs of prior phases.

**Total Issues:** 19  
**Critical Issues:** 6  
**High Priority:** 5  
**Medium Priority:** 8  
**Estimated Duration:** 16 days (10 days with parallelization)

---

## Remediation Phases

### Phase 1: Executor Output Enforcement (Day 1)
**Duration:** 1 day  
**Prerequisites:** None  
**Goal:** Unblock all staging operations

#### Issues Addressed
- **FCA-001** (Critical) - pipeline_runner.py output envelope validation

#### Work Items
1. **Validate Executor Result Envelope**
   - **File:** `src/pipeline_runner.py`
   - **Change:** Add result envelope schema validation before staging
   - **Test:** `tests/test_pipeline_runner_envelope.py`
   - **Acceptance:** Valid transform outputs without "data" wrapper are normalized and staged

2. **Add Envelope Normalization**
   - **File:** `src/utils/envelope_normalizer.py` (new)
   - **Purpose:** Normalize raw payloads into standard envelope
   - **Schema:** `{"data": payload, "status": "success", "metadata": {...}}`

3. **Update Staging Logic**
   - **File:** `src/pipeline_runner.py`
   - **Change:** Call normalizer before staging
   - **Evidence:** `.state/evidence/phase1/staged_output_manifest.json`

#### Success Criteria
- ✓ Executor validates result envelope schema before staging
- ✓ Raw payloads are normalized into standard envelope
- ✓ Test proves executor stages valid output exactly once
- ✓ No valid transformation outputs are lost

#### Deliverables
- [ ] `src/utils/envelope_normalizer.py`
- [ ] Updated `src/pipeline_runner.py`
- [ ] `tests/test_pipeline_runner_envelope.py`
- [ ] `.state/evidence/phase1/envelope_validation_report.json`

---

### Phase 2: Identity and Promotion Prerequisites (Days 2-6)
**Duration:** 5 days  
**Prerequisites:** Phase 1 complete  
**Goal:** Establish identity resolution and complete core metadata

#### Issues Addressed
- **FCA-005** (Critical) - file_id resolution and promotion blocker
- **FCA-010** (Critical) - missing doc_id, file_size, canonicality
- **FCA-011** (Critical) - missing repo_root_id
- **FCA-013** (Critical) - orphaned entries[]
- **FCA-015** (High) - duplicate SHA256 hash

#### Work Items

##### 2.1 Identity Resolution Layer (Days 2-3)
1. **Create file_id Resolver**
   - **File:** `src/identity/file_id_resolver.py` (new)
   - **Purpose:** Map SHA256 → official 20-digit file_id
   - **Input:** Registry with SHA256 hashes
   - **Output:** `file_id_mapping.json`
   - **Test:** `tests/test_file_id_resolution.py`

2. **Identity Contract Enforcement**
   - **File:** `src/pipeline_runner.py`
   - **Change:** Block promotion unless file_id resolved
   - **Rule:** Fail closed if identity_contract not met

3. **SHA256 Deduplication**
   - **File:** `src/identity/sha256_deduplicator.py` (new)
   - **Purpose:** Detect duplicate SHA256, resolve canonical file
   - **Evidence:** `.state/evidence/phase2/duplicate_resolution.json`

##### 2.2 Metadata Backfill (Days 4-5)
1. **doc_id Population**
   - **File:** `scripts/backfill_doc_id.py` (new)
   - **Logic:** Generate unique doc_id for each record
   - **Validation:** Zero records with null doc_id after execution

2. **file_size Calculation**
   - **File:** `scripts/backfill_file_size.py` (new)
   - **Logic:** Read file, compute size, update registry
   - **Validation:** All records have non-null file_size

3. **Canonicality Assignment**
   - **File:** `scripts/backfill_canonicality.py` (new)
   - **Logic:** Mark canonical vs. duplicate/derivative
   - **Validation:** All records have canonicality flag

4. **repo_root_id Inference**
   - **File:** `scripts/infer_repo_root_id.py` (new)
   - **Logic:** Infer from file paths and parent directories
   - **Target:** 46 missing repo_root_id records resolved

##### 2.3 Entry Reconciliation (Day 6)
1. **Orphaned Entry Pruning**
   - **File:** `scripts/prune_orphaned_entries.py` (new)
   - **Logic:** Remove entries[] without corresponding files
   - **Target:** 243/245 orphaned entries cleaned
   - **Safety:** Maintain referential integrity

#### Success Criteria
- ✓ All files have official 20-digit file_id before promotion
- ✓ Zero records missing doc_id, file_size, canonicality
- ✓ 46 repo_root_id records resolved
- ✓ 1 duplicate SHA256 resolved to canonical file
- ✓ Orphaned entries pruned with referential integrity maintained

#### Deliverables
- [ ] `src/identity/file_id_resolver.py`
- [ ] `src/identity/sha256_deduplicator.py`
- [ ] `scripts/backfill_doc_id.py`
- [ ] `scripts/backfill_file_size.py`
- [ ] `scripts/backfill_canonicality.py`
- [ ] `scripts/infer_repo_root_id.py`
- [ ] `scripts/prune_orphaned_entries.py`
- [ ] `.state/evidence/phase2/identity_resolution_manifest.json`
- [ ] `.state/evidence/phase2/metadata_backfill_report.json`

---

### Phase 3: Phase Postconditions and Default Semantics (Days 7-8)
**Duration:** 2 days  
**Prerequisites:** Phase 2 complete  
**Goal:** Ensure phase outputs meet declared contracts

#### Issues Addressed
- **FCA-002** (Medium) - default_injector inert defaults
- **FCA-017** (Medium) - null_coalescer depends on broken defaults

#### Work Items

##### 3.1 Default Injection Fix (Day 7)
1. **Schema Default Definitions**
   - **File:** `schema/COLUMN_DICTIONARY.json`
   - **Change:** Add actionable default values for all eligible columns
   - **Format:** `{"column": "status", "default": "pending", "applies_when": "null"}`

2. **Default Injector Implementation**
   - **File:** `src/default_injector.py`
   - **Change:** Read defaults from schema, apply to records
   - **Test:** `tests/test_default_injection.py`
   - **Acceptance:** Records with null fields receive declared defaults

3. **Postcondition Validation**
   - **File:** `src/default_injector.py`
   - **Change:** Assert required fields populated after execution
   - **Evidence:** `.state/evidence/phase3/default_injection_report.json`

##### 3.2 Null Coalescer Activation (Day 8)
1. **Precondition Check**
   - **File:** `src/null_coalescer.py`
   - **Change:** Verify upstream default_injector postconditions met
   - **Rule:** Fail if preconditions not satisfied

2. **Null Reduction Logic**
   - **File:** `src/null_coalescer.py`
   - **Change:** Coalesce nulls with context-aware defaults
   - **Test:** `tests/test_null_coalescing.py`

#### Success Criteria
- ✓ Schema defines actionable defaults for all eligible columns
- ✓ default_injector populates defaults from schema
- ✓ Records missing required fields receive declared defaults
- ✓ null_coalescer reduces null count to target level
- ✓ Postcondition validation passes

#### Deliverables
- [ ] Updated `schema/COLUMN_DICTIONARY.json`
- [ ] Updated `src/default_injector.py`
- [ ] Updated `src/null_coalescer.py`
- [ ] `tests/test_default_injection.py`
- [ ] `tests/test_null_coalescing.py`
- [ ] `.state/evidence/phase3/default_semantics_report.json`

---

### Phase 4: Input Schema and Field Authority Enforcement (Days 9-10)
**Duration:** 2 days  
**Prerequisites:** Phase 3 complete  
**Goal:** Ensure components use authoritative field names and schema

#### Issues Addressed
- **FCA-004** (Medium) - timestamp_clusterer wrong field name
- **FCA-014** (High) - 6 undocumented columns in registry
- **FCA-016** (High) - schema version mismatch (registry v4.0 vs schema v3)

#### Work Items

##### 4.1 Timestamp Clusterer Fix (Day 9)
1. **Field Name Validation**
   - **File:** `src/timestamp_clusterer.py`
   - **Change:** Read authoritative timestamp field from schema
   - **Before:** `f.get("created_at")`
   - **After:** `f.get(schema.timestamp_field)` where `schema.timestamp_field = "allocated_at"`

2. **Input Contract Validation**
   - **File:** `src/timestamp_clusterer.py`
   - **Change:** Validate input schema contract before execution
   - **Rule:** Fail if authoritative field missing

3. **Cluster Population Test**
   - **Test:** `tests/test_timestamp_clustering.py`
   - **Acceptance:** Clusterer produces non-empty clusters

##### 4.2 Schema Alignment (Day 10)
1. **Document Undocumented Columns**
   - **File:** `schema/COLUMN_DICTIONARY.json`
   - **Change:** Add 6 undocumented columns with governance approval
   - **Process:** Document column purpose, type, constraints
   - **Evidence:** Governance approval log

2. **Schema Version Sync**
   - **File:** `schema/governance_registry_schema.v4.json` (new)
   - **Change:** Update schema to v4.0 to match registry
   - **Or:** Downgrade registry to v3 if v4 changes not justified
   - **Validation:** Version consistency check passes

3. **Column Validator**
   - **File:** `src/column_validator.py`
   - **Change:** Validate all registry columns exist in schema
   - **Rule:** Fail on undocumented columns unless governance approved

#### Success Criteria
- ✓ timestamp_clusterer uses authoritative field name
- ✓ Clusters are non-empty and populated correctly
- ✓ All 6 undocumented columns documented in schema
- ✓ Schema version matches registry version
- ✓ Column validator passes with zero drift

#### Deliverables
- [ ] Updated `src/timestamp_clusterer.py`
- [ ] Updated `schema/COLUMN_DICTIONARY.json` (6 new columns)
- [ ] `schema/governance_registry_schema.v4.json` or downgrade plan
- [ ] Updated `src/column_validator.py`
- [ ] `tests/test_timestamp_clustering.py`
- [ ] `.state/evidence/phase4/schema_alignment_report.json`
- [ ] Governance approval log

---

### Phase 5: Evidence-Driven Validation and Promotion Gates (Days 11-13)
**Duration:** 3 days  
**Prerequisites:** Phase 4 complete  
**Goal:** Prevent invalid outputs from reaching promotion

#### Issues Addressed
- **FCA-003** (High) - e2e_validator shallow policy enforcement
- **FCA-008** (High) - no fingerprint/idempotency mechanism
- **FCA-018** (Medium) - documentation drift

#### Work Items

##### 5.1 Enhanced E2E Validation (Day 11)
1. **Required Column Validation**
   - **File:** `src/e2e_validator.py`
   - **Change:** Load required columns from schema
   - **Rule:** Fail if any required column is null
   - **Test:** `tests/test_e2e_required_columns.py`

2. **Policy-Level Invariants**
   - **File:** `src/e2e_validator.py`
   - **Change:** Validate policy-level invariants from schema
   - **Examples:** unique constraints, foreign keys, enum values
   - **Evidence:** `.state/evidence/phase5/policy_validation_report.json`

3. **Gate Enforcement**
   - **File:** `src/pipeline_runner.py`
   - **Change:** Block promotion unless e2e_validator passes
   - **Rule:** Mandatory gate before promotion path

##### 5.2 Fingerprint and Idempotency (Day 12)
1. **Fingerprint Contract**
   - **File:** `src/utils/fingerprint.py` (new)
   - **Purpose:** Compute fingerprint from inputs + spec version
   - **Algorithm:** `SHA256(inputs + spec_version + salt)`

2. **Fingerprint Store**
   - **File:** `.state/fingerprints/fingerprint_store.json`
   - **Format:** `{"fingerprint": "abc123", "result": {...}, "timestamp": "..."}`

3. **Runner Skip Logic**
   - **File:** `src/pipeline_runner.py`
   - **Change:** Check fingerprint before execution
   - **Rule:** Skip if match found unless forced
   - **Evidence:** `.state/evidence/phase5/fingerprint_skip_log.json`

4. **All Script Integration**
   - **Files:** All automation scripts
   - **Change:** Add fingerprint computation at entry point
   - **Test:** `tests/test_idempotency.py`

##### 5.3 Documentation Sync (Day 13)
1. **Auto-Generate Script Index**
   - **File:** `scripts/generate_script_index.py` (new)
   - **Purpose:** Scan scripts/, generate SCRIPT_INDEX.md
   - **Input:** scripts/ directory
   - **Output:** Updated SCRIPT_INDEX.md

2. **Documentation Validator**
   - **File:** `src/doc_validator.py` (new)
   - **Purpose:** Validate docs against implementation
   - **Rule:** Fail if script not listed or description outdated

3. **CI Integration**
   - **File:** `.github/workflows/validate-docs.yml` (if applicable)
   - **Change:** Run doc validator on every commit
   - **Rule:** Block merge if documentation drift detected

#### Success Criteria
- ✓ e2e_validator enforces required columns and policy invariants
- ✓ Outputs missing required fields fail gate and do not promote
- ✓ Fingerprint computed for all executions
- ✓ Identical inputs + spec version skip execution and return cached result
- ✓ SCRIPT_INDEX.md auto-generated and validated
- ✓ Documentation validator passes with zero drift

#### Deliverables
- [ ] Updated `src/e2e_validator.py`
- [ ] `src/utils/fingerprint.py`
- [ ] Fingerprint integration in all scripts
- [ ] `scripts/generate_script_index.py`
- [ ] `src/doc_validator.py`
- [ ] `tests/test_e2e_required_columns.py`
- [ ] `tests/test_idempotency.py`
- [ ] `.state/evidence/phase5/validation_gate_report.json`
- [ ] Updated SCRIPT_INDEX.md

---

### Phase 6: Mutation-Safety and Write-Path Governance (Days 14-16)
**Duration:** 3 days  
**Prerequisites:** Phase 5 complete  
**Goal:** Safe registry writes with rollback capability

#### Issues Addressed
- **FCA-006** (Medium) - doc_id_resolver analysis-only mode
- **FCA-007** (Medium) - module_dedup analysis-only mode
- **FCA-012** (Critical) - empty edges[] relationship tracking
- **FCA-019** (Medium) - incomplete phase B/C integration

#### Work Items

##### 6.1 Mutation Contract Framework (Day 14)
1. **Mutation Safety Contract**
   - **File:** `src/mutation/mutation_contract.py` (new)
   - **Purpose:** Define write-path ownership, locks, rollback
   - **Fields:** `locks_write_policy`, `rollback_artifacts`, `validation_rules`

2. **Write Lock Manager**
   - **File:** `src/mutation/lock_manager.py` (new)
   - **Purpose:** Acquire locks before writes, release after
   - **Evidence:** `.state/evidence/phase6/lock_ledger.json`

3. **Rollback Artifact Generator**
   - **File:** `src/mutation/rollback_generator.py` (new)
   - **Purpose:** Create rollback artifacts before mutation
   - **Format:** `.state/rollback/{timestamp}_{component}.json`

##### 6.2 doc_id and Module Mutation (Day 15)
1. **doc_id Resolver Write Path**
   - **File:** `src/doc_id_resolver.py`
   - **Change:** Add mutation contract and registry write capability
   - **Process:** Detect collisions → generate resolution plan → write to registry
   - **Test:** `tests/test_doc_id_mutation.py`

2. **Module Dedup Write Path**
   - **File:** `src/module_dedup.py`
   - **Change:** Add path canonicalization and mutation contract
   - **Process:** Canonicalize paths → detect true duplicates → write resolution
   - **Fix:** FILE WATCHER path prefix pollution
   - **Test:** `tests/test_module_dedup_mutation.py`

##### 6.3 Relationship and Phase Integration (Day 16)
1. **Edges Builder**
   - **File:** `scripts/build_edges.py` (new)
   - **Purpose:** Generate edges[] relationships from file references
   - **Input:** Registry with empty edges[]
   - **Output:** Populated edges[] array
   - **Test:** `tests/test_edges_generation.py`

2. **Phase B/C Output Contract**
   - **File:** `src/phase_a_transformer.py`
   - **Change:** Define formal output contract
   - **Schema:** `{"data": {...}, "metadata": {...}, "version": "..."}`

3. **Phase B Integration**
   - **File:** `src/phase_b_processor.py` (new or update)
   - **Change:** Validate phase A output against contract before processing
   - **Test:** `tests/test_phase_integration.py`

#### Success Criteria
- ✓ Mutation contract defined with locks, rollback, validation
- ✓ doc_id resolver writes collision resolution to registry
- ✓ module_dedup writes deduplication resolution to registry
- ✓ edges[] populated with relationships
- ✓ Phase A/B/C integration validated with formal contracts
- ✓ All writes logged with rollback artifacts

#### Deliverables
- [ ] `src/mutation/mutation_contract.py`
- [ ] `src/mutation/lock_manager.py`
- [ ] `src/mutation/rollback_generator.py`
- [ ] Updated `src/doc_id_resolver.py` (with write path)
- [ ] Updated `src/module_dedup.py` (with write path)
- [ ] `scripts/build_edges.py`
- [ ] Updated `src/phase_a_transformer.py`
- [ ] `src/phase_b_processor.py`
- [ ] `tests/test_doc_id_mutation.py`
- [ ] `tests/test_module_dedup_mutation.py`
- [ ] `tests/test_edges_generation.py`
- [ ] `tests/test_phase_integration.py`
- [ ] `.state/evidence/phase6/mutation_safety_report.json`

---

## Dependency Graph

```
Phase 1 (Executor Output)
  └─> Phase 2 (Identity + Metadata)
       └─> Phase 3 (Defaults + Postconditions)
            └─> Phase 4 (Schema + Field Authority)
                 └─> Phase 5 (Validation Gates + Idempotency)
                      └─> Phase 6 (Mutation Safety + Integration)
```

**Critical Path:** FCA-001 → FCA-005 → FCA-010 → FCA-003 → FCA-012

---

## Parallel Execution Opportunities

### Days 2-3 (Phase 2.1)
Can parallelize:
- file_id resolver development
- SHA256 deduplicator development

### Days 4-5 (Phase 2.2)
Can parallelize all metadata backfill scripts:
- doc_id population
- file_size calculation
- canonicality assignment
- repo_root_id inference

**Parallel Duration:** 2 days instead of 5 days (3-day savings)

### Days 11-13 (Phase 5)
Can parallelize:
- E2E validator enhancements (Day 11)
- Fingerprint implementation (Day 12)
- Documentation sync (Day 13)

**Parallel Duration:** 1 day instead of 3 days (2-day savings)

**Total Savings:** 5 days  
**Sequential Duration:** 16 days  
**Parallel Duration:** 11 days (with 3-4 developers)

---

## Testing Strategy

### Unit Tests
- Every new file has corresponding test file
- Every modified file has test coverage added
- Target: 80% code coverage minimum

### Integration Tests
- Phase handoff tests (Phase A → Phase B)
- Gate enforcement tests (invalid output blocked)
- Mutation contract tests (rollback artifacts created)

### End-to-End Tests
- Full pipeline execution with all phases
- Idempotency test (run twice, same result)
- Rollback test (mutation fails, registry restored)

### Validation Tests
- Schema validation (registry matches schema)
- Evidence validation (all evidence files present)
- Contract validation (all contracts satisfied)

---

## Evidence Requirements

Every phase must produce:
1. **Execution Log:** `.state/evidence/phase{N}/execution.log`
2. **Validation Report:** `.state/evidence/phase{N}/validation_report.json`
3. **Before/After Metrics:** `.state/evidence/phase{N}/metrics.json`
4. **Test Results:** `.state/evidence/phase{N}/test_results.json`

---

## Rollback Strategy

### Phase-Level Rollback
1. **Snapshot Before Phase:** `.state/rollback/pre_phase{N}_snapshot.json`
2. **Changes Ledger:** `.state/rollback/phase{N}_changes.log`
3. **Rollback Script:** `scripts/rollback_phase{N}.py`

### Mutation-Level Rollback
1. **Pre-Mutation State:** `.state/rollback/{timestamp}_{component}_before.json`
2. **Mutation Diff:** `.state/rollback/{timestamp}_{component}_diff.json`
3. **Rollback Command:** Stored in mutation contract

---

## Success Metrics

### Quantitative
- ✓ 19/19 issues closed with verification tests passing
- ✓ 0 critical issues remaining
- ✓ 100% of records have complete metadata
- ✓ 0 orphaned entries remaining
- ✓ 0 undocumented columns in registry
- ✓ Schema version matches registry version
- ✓ All validation gates pass

### Qualitative
- ✓ Pipeline is idempotent (safe to re-run)
- ✓ All mutations have rollback capability
- ✓ Documentation auto-generated and validated
- ✓ Phase contracts formally defined
- ✓ Identity resolution layer operational

---

## Risk Mitigation

### High-Risk Items
1. **Data Backfill at Scale**
   - **Risk:** Backfill may take longer than estimated on large dataset
   - **Mitigation:** Run on sample first, measure performance, parallelize if needed

2. **Breaking Changes**
   - **Risk:** Schema or API changes may break downstream consumers
   - **Mitigation:** Version all contracts, maintain backward compatibility for 1 release

3. **Rollback Complexity**
   - **Risk:** Rollback may fail if state is corrupted
   - **Mitigation:** Test rollback in staging, verify integrity before production

### Medium-Risk Items
1. **Test Coverage**
   - **Risk:** Insufficient test coverage may miss edge cases
   - **Mitigation:** Require 80% coverage minimum, add integration tests

2. **Documentation Drift**
   - **Risk:** Auto-generated docs may be incomplete
   - **Mitigation:** Manual review after generation, CI validation

---

## Go-Live Checklist

- [ ] All 19 verification tests pass
- [ ] All phases executed in sequence
- [ ] All evidence files generated and validated
- [ ] Rollback tested successfully
- [ ] Documentation updated and validated
- [ ] Staging environment validated
- [ ] Production deployment plan approved
- [ ] Rollback plan tested and ready

---

## Next Steps

1. **Week 1:** Execute Phases 1-2 (Executor + Identity)
2. **Week 2:** Execute Phases 3-4 (Defaults + Schema)
3. **Week 3:** Execute Phases 5-6 (Gates + Mutation)
4. **Week 4:** Integration testing and deployment

**Start Date:** TBD  
**Target Completion:** 16 business days (3-4 weeks)

---

*Plan Generated: 2026-03-08*  
*Based On: CONTRACT_GAP_MATRIX.md (19 issues)*  
*Status: Ready for Execution*
