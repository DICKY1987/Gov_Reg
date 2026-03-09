# Registry Automation System - Audit Summary & Execution Plan

**Date:** 2026-03-09  
**Status:** ⚠️ PARTIAL IMPLEMENTATION - NOT PRODUCTION READY  
**Audit Scope:** 16-item repair list validation

---

## AUDIT RESULTS BY REPAIR ITEM

### ✅ Item 6: Pipeline Runner Staging Bug - **CONFIRMED**
- **File:** `P_01999000042260305017_pipeline_runner.py:79`
- **Root Cause:** Checks `transformed.get("data")` but `PhaseATransformer.transform_phase_a_output()` returns flat dict, not wrapped
- **Evidence:** Line 55 stores return directly; line 79 checks for nested structure
- **Impact:** Valid transformed output silently skipped from staging
- **Fix Complexity:** LOW (1 file, ~5 lines changed)
- **Priority:** 🔴 CRITICAL - Blocks all pipeline execution

### ❌ Item 8: Defaults and Null Handling - **BROKEN**
- **Files:** `column_loader.py`, `default_injector.py`, `null_coalescer.py`
- **Root Cause:** COLUMN_DICTIONARY missing from expected path
- **Evidence:** 
  - Line 38 column_loader: Points to non-existent `COLUMN_HEADERS/` directory
  - Test output: Only BASE (148) and PHASE_A (37) columns found
  - default_injector calls `get_all_columns()` and `get_default_value()` - methods don't exist in ColumnLoader
- **Impact:** Cannot inject defaults or coalesce nulls
- **Fix Complexity:** MEDIUM (3 files, locate/create dictionary, add methods)
- **Priority:** 🔴 CRITICAL - Breaks data integrity

### ⚠️ Item 7: SHA256 → file_id Promotion - **INCOMPLETE**
- **Files Found:** `sha256_backfill.py` (exists), `file_id_reconciler.py` (incomplete)
- **Root Cause:** Reconciler only validates records that ALREADY have both sha256 AND file_id
- **Evidence:** Lines 63-80 of reconciler only map existing valid pairs
- **Gap:** No promotion logic for new analyzer output → file_id resolution
- **Fix Complexity:** MEDIUM (2 files, add promotion step with tests)
- **Priority:** 🟡 HIGH - Blocks new record ingestion

### ⚠️ Item 9: E2E Validation - **SHALLOW**
- **File:** `P_01999000042260305016_e2e_validator.py`
- **Current:** Only checks top-level structure (files, edges) and per-field validation
- **Missing:**
  - Required columns enforcement
  - Duplicate ID detection
  - Invalid promotion states
  - Write-policy violations
  - Invalid patch semantics
  - Malformed edge relationships
- **Fix Complexity:** MEDIUM (1 file, ~150 lines added)
- **Priority:** 🟡 HIGH - Corrupted data passes validation

### ⚠️ Item 10: Timestamp Authority - **HARDCODED**
- **File:** `P_01999000042260305015_timestamp_clusterer.py` (documented but not viewed)
- **Issue:** Hardcodes `created_at` field instead of configurable authority field
- **Fix Complexity:** LOW (1 file, add config parameter)
- **Priority:** 🟢 MEDIUM - Reduces flexibility

### ⚠️ Items 11-12: Entity Resolution - **ANALYSIS-ONLY**
- **Files:** `doc_id_resolver.py`, `module_dedup.py`
- **Current:** Generate reports and resolution maps only
- **Gap:** No patch generation, no apply mode, no audit evidence, no promotion blocking
- **Evidence:** Lines 1-80 of doc_id_resolver show report generation only
- **Fix Complexity:** HIGH (2 files, add mutation flows with audit)
- **Priority:** 🟡 HIGH - Collisions remain unresolved in registry

### ❌ Item 14: Phase B/C Integration - **SKIPPED**
- **File:** `P_01999000042260305014_intake_orchestrator.py`
- **Evidence:** Lines 72-80 show Phase A only; no Phase B/C wiring
- **Gap:** Claims of "end-to-end" are misleading
- **Fix Complexity:** HIGH (2 files, wire analyzers + tests)
- **Priority:** 🟡 HIGH - Single-phase limitation

### ❌ Item 3: Preflight Checks - **MISSING**
- **Required Files:**
  - `.state/gates/gates_spec.json` ❌
  - `.state/remediation/remediation_plan.json` ❌
  - `.state/normalized_issues.json` ❌
- **Evidence:** No `.state/` directory found in REGISTRY
- **Impact:** No fail-closed validation before mutations
- **Fix Complexity:** MEDIUM (create .state structure, add preflight script)
- **Priority:** 🔴 CRITICAL - Data safety violation

### ❌ Items 1-2: Schema Normalization & PH-03 Strategy - **NOT ASSESSED**
- **Reason:** Cannot verify gate/step schemas without remediation_plan.json
- **Status:** Blocked by missing .state/ infrastructure
- **Priority:** 🟢 MEDIUM - Depends on Item 3

### ❌ Item 13: Evidence Contracts - **WEAK**
- **Gap:** No standardized evidence artifact schema across 19 scripts
- **Fix Complexity:** MEDIUM (define schema, update scripts)
- **Priority:** 🟢 MEDIUM - Audit trail incomplete

### ❌ Item 15: Documentation Drift - **CONFIRMED**
- **Files:** `README.md`, `SCRIPT_INDEX.md`
- **Claim:** "Production-Ready ✅" (README line 7)
- **Reality:** Critical bugs, zero tests, missing features
- **Discrepancy:** Docs claim 18 scripts, found 19 (sha256_backfill not documented)
- **Fix Complexity:** LOW (2 files, update claims and inventory)
- **Priority:** 🔴 CRITICAL - Misleading stakeholders

### ❌ Item 16: Test Coverage - **ZERO**
- **Evidence:**
  - Test files in REGISTRY_AUTOMATION/: **0**
  - Unit tests: **0**
  - Integration tests: **0**
  - Fixture registries: **0**
- **Impact:** Cannot validate fixes, no regression prevention
- **Fix Complexity:** HIGH (~50 tests, 2 fixture registries)
- **Priority:** 🔴 CRITICAL - Cannot verify any fix works

### ❓ Items 4, 5: Deterministic Wave Assignment & Status Claims
- **Status:** Cannot assess without remediation_plan.json in .state/
- **Priority:** 🟢 MEDIUM

---

## CRITICAL BLOCKERS SUMMARY

### 🔴 CRITICAL (Immediate Action Required)
1. **Missing COLUMN_DICTIONARY** - Defaults system non-functional
2. **Pipeline staging bug** - Valid data silently dropped
3. **No test suite** - Cannot validate any fix safely
4. **No preflight checks** - Mutations can corrupt state
5. **Documentation claims "Production-Ready"** - Misleading

### 🟡 HIGH (Blocks Key Workflows)
6. **SHA256 promotion incomplete** - New files cannot enter system
7. **Entity resolution analysis-only** - Collisions not auto-cleaned
8. **E2E validation shallow** - Bad data passes through
9. **Phase B/C not wired** - Limited to single-phase analysis

### 🟢 MEDIUM (Quality Reduction)
10. **Timestamp authority hardcoded** - Fragile assumptions
11. **Evidence contracts weak** - Incomplete audit trail
12. **Schema normalization not assessed** - Depends on .state/

---

## FILE INVENTORY

### Scripts Present: 19 Total
| Script | Purpose | Status | Tests |
|--------|---------|--------|-------|
| P_...305000_enum_drift_gate.py | Enum validation | ✅ Working | ❌ None |
| P_...305001_file_id_reconciler.py | ID mapping | ⚠️ Incomplete | ❌ None |
| P_...305002_phase_a_transformer.py | Column transform | ✅ Working | ❌ None |
| P_...305003_run_metadata_collector.py | Audit trail | ✅ Working | ❌ None |
| P_...305004_patch_generator.py | RFC-6902 patches | ✅ Working | ❌ None |
| P_...305005_column_loader.py | Dictionary loader | ❌ Broken path | ❌ None |
| P_...305006_column_validator.py | Type validation | ✅ Working | ❌ None |
| P_...305007_default_injector.py | Default values | ❌ Broken calls | ❌ None |
| P_...305008_null_coalescer.py | Null handling | ❌ Broken calls | ❌ None |
| P_...305009_phase_selector.py | Phase extraction | ✅ Working | ❌ None |
| P_...305010_missing_reporter.py | Coverage report | ✅ Working | ❌ None |
| P_...305011_column_introspector.py | Usage analysis | ✅ Working | ❌ None |
| P_...305012_doc_id_resolver.py | Entity resolution | ⚠️ Analysis-only | ❌ None |
| P_...305013_module_dedup.py | Module dedup | ⚠️ Analysis-only | ❌ None |
| P_...305014_intake_orchestrator.py | Pipeline orchestration | ⚠️ Phase A only | ❌ None |
| P_...305015_timestamp_clusterer.py | Time clustering | ⚠️ Hardcoded | ❌ None |
| P_...305016_e2e_validator.py | End-to-end validation | ⚠️ Shallow | ❌ None |
| P_...305017_pipeline_runner.py | Batch processing | ❌ Staging bug | ❌ None |
| P_...305018_sha256_backfill.py | Hash computation | ✅ Working | ❌ None |

**Status:** 9 working, 5 incomplete, 5 broken  
**Test Coverage:** 0/19 (0%)

### Critical Missing Artifacts
- ❌ `COLUMN_DICTIONARY.json` (expected: `COLUMN_HEADERS/01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json`)
- ❌ `.state/` directory and all contents
- ❌ `test_*.py` files (all scripts untested)
- ❌ Golden path fixture registry
- ❌ Broken fixture registry (for negative tests)

---

## EXECUTION PLAN (Recommended Order)

### **Phase 1: Foundation & Safety** (Week 1 - Days 1-5)
**Goal:** Stop claiming production-ready, add safety net, fix critical bugs

#### Day 1: Documentation & Quick Wins
1. ✅ **Update README.md** (30 min)
   - Change status from "Production-Ready ✅" to "⚠️ Development - Undergoing Remediation"
   - Add warnings about test coverage
   - Document P_...305018_sha256_backfill.py (missing from index)

2. ✅ **Fix pipeline_runner staging bug** (30 min)
   - Change line 79: `if file_id and transformed:` (remove `.get("data")`)
   - Update staging payload to match transform output structure
   - Verify staged output contains expected columns

#### Days 2-3: Test Infrastructure
3. ✅ **Create test directory structure** (2 hours)
   ```
   REGISTRY_AUTOMATION/
   ├── tests/
   │   ├── unit/           # Per-script unit tests
   │   ├── integration/    # Multi-script workflows
   │   ├── fixtures/       # Test data
   │   │   ├── golden_registry.json
   │   │   └── broken_registry.json
   │   └── conftest.py     # Pytest configuration
   ```

4. ✅ **Write smoke tests** (1 day)
   - `test_pipeline_runner_smoke.py` - Proves staging works
   - `test_enum_drift_gate_smoke.py` - Validates enum fixing
   - `test_phase_a_transformer_smoke.py` - Transform output structure

#### Days 4-5: Preflight Checks
5. ✅ **Create .state/ infrastructure** (4 hours)
   ```
   01260207201000001250_REGISTRY/
   └── .state/
       ├── gates/
       │   └── gates_spec.json
       ├── remediation/
       │   └── remediation_plan.json
       └── issues/
           └── normalized_issues.json
   ```

6. ✅ **Add preflight_checker.py** (1 day)
   - Validate required files exist and parse
   - Check file_id uniqueness
   - Verify sha256 format
   - Fail-closed on any validation error
   - Record preflight evidence

---

### **Phase 2: Data Integrity** (Week 2 - Days 6-10)

#### Day 6: Column Dictionary
7. ✅ **Locate or regenerate COLUMN_DICTIONARY** (4 hours)
   - Search for existing dictionary in backups/archives
   - If missing, generate from registry schema + docs
   - Place at expected path: `COLUMN_HEADERS/01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json`

8. ✅ **Add missing ColumnLoader methods** (2 hours)
   - `get_all_columns() -> List[str]`
   - `get_default_value(col_name: str) -> Any`
   - Update tests to verify methods work

#### Days 7-8: Defaults and Nulls
9. ✅ **Fix default_injector.py** (4 hours)
   - Use corrected ColumnLoader methods
   - Add unit tests for string, int, bool, array defaults
   - Test with missing-heavy fixture

10. ✅ **Fix null_coalescer.py** (4 hours)
    - Use corrected ColumnLoader methods
    - Add unit tests for null → default coalescing
    - Test with null-heavy fixture

#### Days 9-10: SHA256 Promotion
11. ✅ **Add promotion logic to file_id_reconciler** (1 day)
    - `promote_sha256_to_file_id(sha256: str) -> Optional[str]`
    - Fail-closed if sha256 maps to multiple file_ids
    - Add regression test proving new records resolve

12. ✅ **Integration test: sha256_backfill → promotion** (4 hours)
    - Prove new file → backfill hash → resolve file_id
    - Test collision detection and blocking

---

### **Phase 3: Validation & Resolution** (Week 3 - Days 11-15)

#### Days 11-12: Strengthen E2E Validator
13. ✅ **Enhance e2e_validator.py** (1 day)
    - Add required columns check
    - Add duplicate ID detection
    - Add promotion state validation
    - Add edge relationship validation
    - Fail-closed on any violation

14. ✅ **Add e2e_validator tests** (4 hours)
    - Golden registry passes
    - Broken registry fails with specific errors
    - Partial registry blocked from promotion

#### Days 13-15: Entity Resolution Mutation
15. ✅ **Convert doc_id_resolver to mutation** (1 day)
    - Add resolution plan output
    - Add patch generation
    - Add apply mode with backup
    - Add audit evidence
    - Block promotion on unresolved collisions

16. ✅ **Convert module_dedup to mutation** (1 day)
    - Add resolution plan output
    - Add patch generation
    - Add apply mode with backup
    - Add audit evidence
    - Block promotion on unresolved duplicates

17. ✅ **Integration test: resolution → patch → apply** (4 hours)
    - Prove collision resolution writes patches
    - Prove apply mode updates registry
    - Prove backup created before changes

---

### **Phase 4: Completeness** (Week 4 - Days 16-20)

#### Days 16-17: Phase B/C or Disclosure
18. ✅ **Option A: Wire Phase B/C** (2 days)
    - Update intake_orchestrator lines 72-150
    - Call Phase B/C analyzer scripts
    - Merge outputs into unified result
    - Add integration tests

19. ✅ **Option B: Downgrade claims** (2 hours)
    - Remove "end-to-end" language if Phase B/C not wired
    - Update README to clarify Phase A-only scope
    - Document Phase B/C as "planned future work"

#### Day 18: Remaining Fixes
20. ✅ **Fix timestamp_clusterer** (2 hours)
    - Add `--timestamp-field` parameter
    - Default to registry authority field
    - Update docs

21. ✅ **Implement registry path cleanup** (4 hours)
    - Add governed cleanup for `FILE WATCHER` pollution
    - Update relative_path, file_path, module_name
    - Re-run dedup after cleanup
    - Block promotion if pollution remains

#### Days 19-20: Schemas and Evidence
22. ✅ **Define evidence artifact schema** (4 hours)
    ```json
    {
      "artifact_type": "enum_drift_fix",
      "schema_version": "1.0.0",
      "source_files": ["REGISTRY_file.json"],
      "timestamp": "2026-03-09T18:00:00Z",
      "before": {...},
      "after": {...},
      "validation_result": "pass",
      "operator": "pipeline_runner",
      "ground_truth_level": 3
    }
    ```

23. ✅ **Update all scripts to emit standardized evidence** (1 day)
    - Update each of 19 scripts
    - Add schema validation to preflight_checker

24. ✅ **Final integration test run** (4 hours)
    - Full pipeline: intake → transform → staging → patch → apply
    - Golden path passes
    - Error path fails gracefully
    - All evidence artifacts generated

---

## EFFORT ESTIMATE

| Phase | Tasks | Days | LOC Impact | Files Changed | Tests Added |
|-------|-------|------|-----------|---------------|-------------|
| Phase 1 | 6 | 5 | ~300 | 5 | ~10 |
| Phase 2 | 6 | 5 | ~400 | 5 | ~15 |
| Phase 3 | 5 | 5 | ~450 | 3 | ~15 |
| Phase 4 | 5 | 5 | ~270 | 19 | ~10 |
| **TOTAL** | **22** | **20** | **~1,420** | **32** | **~50** |

**Calendar Time:** 4 weeks (assuming 1 developer)  
**Risk Buffer:** Add 20% for unexpected issues (total: 24 days)

---

## SUCCESS CRITERIA

### Phase 1 Complete
- [ ] README updated with honest status
- [ ] Pipeline staging bug fixed
- [ ] 3+ smoke tests passing
- [ ] Preflight checker blocks bad state
- [ ] .state/ infrastructure exists

### Phase 2 Complete
- [ ] COLUMN_DICTIONARY located/created
- [ ] Defaults system functional
- [ ] SHA256 → file_id promotion works
- [ ] 15+ tests passing

### Phase 3 Complete
- [ ] E2E validator catches corruption
- [ ] Entity resolution mutates registry
- [ ] Collisions auto-resolved
- [ ] 30+ tests passing

### Phase 4 Complete
- [ ] Phase B/C wired OR claims downgraded
- [ ] All 19 scripts emit standard evidence
- [ ] 50+ tests passing
- [ ] Golden path end-to-end passes
- [ ] Error paths fail gracefully

### Production-Ready Criteria
- [ ] All 16 repair items addressed
- [ ] Test coverage ≥80% (lines)
- [ ] All critical blockers resolved
- [ ] Documentation accurate
- [ ] Evidence trail complete
- [ ] Preflight checks enforced
- [ ] No data loss in pipeline
- [ ] Entity collisions auto-resolved

---

## RISK MITIGATION

### Technical Risks
| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| COLUMN_DICTIONARY cannot be recreated | MEDIUM | HIGH | Extract schema from existing registry |
| Phase B/C analyzers don't exist | LOW | HIGH | Use Option B (downgrade claims) |
| Test fixtures too complex | MEDIUM | MEDIUM | Start with minimal golden registry |
| Breaking changes to registry schema | LOW | CRITICAL | Version all patches, keep backups |

### Schedule Risks
| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Underestimated LOC impact | MEDIUM | MEDIUM | 20% buffer already added |
| Unexpected dependencies | MEDIUM | HIGH | Phase gates prevent cascade |
| Testing takes longer than expected | HIGH | MEDIUM | Prioritize critical path tests |

---

## IMMEDIATE NEXT STEPS (Today)

1. **Approve this execution plan** (15 min)
2. **Update README.md** (30 min) - Remove "Production-Ready" claim
3. **Fix pipeline_runner.py line 79** (30 min) - Remove `.get("data")`
4. **Commit changes with message:** "chore: honest status + fix staging bug"
5. **Begin Phase 1 Day 2:** Create test infrastructure

---

**END AUDIT SUMMARY**
