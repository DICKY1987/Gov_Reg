# Capability Mapping System Completion Plan

**Plan ID:** `PLAN-20260305-CAPABILITY-MAPPING-V1`  
**Created:** 2026-03-05T06:06:46Z  
**Status:** DRAFT - Awaiting Evaluation  
**Owner:** Gov_Reg Governance System  
**Estimated Duration:** 3-5 days (phased execution)

---

## Executive Summary

This plan completes the capability mapping system to populate **37 `py_*` registry columns** and establish end-to-end file-to-capability mapping with convergent evidence. Current state: **infrastructure 75% complete**, Step 3 incomplete, Step 4 in dry-run only.

**Key Deliverables:**
1. Complete 4-step capability mapping pipeline (finish Step 3, apply Step 4)
2. Populate 25 of 37 `py_*` columns (68% coverage) immediately
3. Create transformation layer for PARTIAL → DIRECT promotion
4. Establish file ID reconciliation (SHA-256 ↔ 20-digit registry IDs)
5. Generate convergent evidence bundles (timestamp + AST + provenance)

---

## Problem Statement

### Current Gaps
1. **Step 3 Incomplete**: `FILE_PURPOSE_REGISTRY.json` missing → `py_capability_tags` unpopulated
2. **Step 4 Dry-Run Only**: 796 patches generated but never applied to SSOT registry
3. **File ID Mismatch**: Pipeline uses SHA-256, registry expects 20-digit allocated IDs
4. **Data Transformation Needed**: 11 `py_*` columns have raw data but need derivation
5. **Missing Run Metadata**: 6 orchestration fields not captured (run_id, timestamps, versions)
6. **Advanced Analyzers Absent**: Canonical ranking, similarity clustering, quality scoring

### Impact
- Registry columns remain NULL for 574 Python files
- Feature/component mapping lacks capability context
- Convergent evidence model incomplete (missing capability + provenance layers)
- Cannot apply timestamp clustering strategy without Step 3 output

---

## Plan Architecture

### Phase 0: Pre-Flight Validation (1 hour)
**Goal:** Ensure baseline infrastructure is operational

| Task | Command | Success Criteria |
|------|---------|------------------|
| 0.1 Verify mapp_py library | `python -c "import sys; sys.path.insert(0, 'REGISTRY/01260207201000001313_capability_mapping_system/01260207220000001318_mapp_py'); from P_01260202173939000061_component_extractor import *"` | No import errors |
| 0.2 Check existing outputs | `ls .state/purpose_mapping/` | `CAPABILITIES.json` + `FILE_INVENTORY.jsonl` exist |
| 0.3 Verify registry access | `python -c "import json; r=json.load(open('REGISTRY/01999000042260124503_REGISTRY_file.json')); print(f'{len(r[\"files\"])} files')"` | Prints file count |
| 0.4 Validate schemas | Check `COLUMN_HEADERS/01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json` | 37 `py_*` columns defined |

**Exit Criteria:** All 4 tasks pass  
**Rollback:** None needed (read-only checks)

---

### Phase 1: Complete Core Pipeline (4-8 hours)

#### 1.1 Execute Step 3: Purpose Mapping
**Goal:** Generate `FILE_PURPOSE_REGISTRY.json` with confidence-scored capability assignments

**Actions:**
```powershell
cd C:\Users\richg\Gov_Reg
python 01260207201000001250_REGISTRY\01260207201000001313_capability_mapping_system\P_01260207220000001315_capability_mapper.py --step 3 --repo-root . --vocab-path REGISTRY\01260207201000001313_capability_mapping_system\01260207220000001320_schemas\01260207220000001327_COMPONENT_CAPABILITY_VOCAB.json
```

**Validation:**
- Output file exists: `.state/purpose_mapping/FILE_PURPOSE_REGISTRY.json`
- Schema valid: Contains `mappings` array with `file_path`, `purposes`, `confidence`
- Coverage: ≥500 files mapped
- Evidence generated: `.state/evidence/purpose_mapping/step3_*.json`

**Failure Modes:**
- Import errors → Check sys.path modifications in orchestrator
- Empty mappings → Review `COMPONENT_CAPABILITY_VOCAB.json` taxonomy
- Low confidence → Acceptable if evidence is present

---

#### 1.2 Build File ID Reconciliation Layer
**Goal:** Create lookup table: `SHA-256 → registry file_id (20-digit)`

**Implementation:** New script `P_01999000042260305001_file_id_reconciler.py`

**Logic:**
```python
# Read registry, build index
registry = json.load(open('REGISTRY/01999000042260124503_REGISTRY_file.json'))
sha_to_id = {}
for record in registry['files']:
    if 'sha256' in record and 'file_id' in record:
        sha_to_id[record['sha256']] = record['file_id']

# Write reconciliation map
json.dump({
    "generated_at_utc": datetime.utcnow().isoformat() + 'Z',
    "total_mappings": len(sha_to_id),
    "sha256_to_file_id": sha_to_id
}, open('.state/purpose_mapping/SHA256_TO_FILE_ID.json', 'w'))
```

**Validation:**
- Mapping count ≥ FILE_INVENTORY.jsonl line count
- All Step 2 output SHA-256s have matches
- Evidence hash stored

**Deliverable:** `.state/purpose_mapping/SHA256_TO_FILE_ID.json`

---

#### 1.3 Add Transformation Layer for PARTIAL Columns
**Goal:** Convert 11 PARTIAL columns to registry-ready format

**Implementation:** New adapter `P_01999000042260305002_py_column_transformer.py`

**Transformations:**
| Input | Output Column | Transform |
|-------|---------------|-----------|
| `FileContext.ast_tree` | `py_ast_dump_hash` | `hashlib.sha256(ast.dump(tree).encode()).hexdigest()` |
| `ast_tree is not None` | `py_ast_parse_ok` | `bool(ast_tree)` |
| `facts.deliverable.interface_signature` | `py_component_count` | `len(classes) + len(functions)` |
| `interface_signature.classes` | `py_defs_classes_count` | `len(classes)` |
| `interface_signature.functions` | `py_defs_functions_count` | `len(functions)` |
| `facts.deliverable.interface_signature` | `py_deliverable_interfaces` | Flatten `{classes: [...], functions: [...]}` to unified array |
| `facts.imports.entries` (type="relative") | `py_imports_local` | `[e['module'] for e in entries if e['type']=='relative']` |
| `facts.imports.entries` (stdlib) | `py_imports_stdlib` | `[e['module'] for e in entries if e['classification']=='stdlib']` |
| `facts.imports.entries` (external) | `py_imports_third_party` | `[e['module'] for e in entries if e['classification']=='external']` |
| `facts.io_surface.*` | `py_io_surface_flags` | Map to `['HAS_FILE_READ', 'HAS_NETWORK', ...]` |
| `facts.io_surface.security_calls` | `py_security_risk_flags` | `['HAS_SUBPROCESS', 'HAS_EVAL', ...]` if present |

**Validation:**
- Run against FILE_INVENTORY.jsonl
- Output: `.state/purpose_mapping/PY_COLUMNS_TRANSFORMED.jsonl`
- All 11 columns populated where source data exists
- NULL where source missing (acceptable)

---

#### 1.4 Add Run Metadata Collection
**Goal:** Populate 6 orchestration fields

**Implementation:** Modify `registry_integration_pipeline.py` or add to transformer

**Fields to Add:**
```python
run_metadata = {
    "py_analysis_run_id": f"RUN-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}-{os.urandom(3).hex()}",
    "py_analyzed_at_utc": datetime.utcnow().isoformat() + 'Z',
    "py_analysis_success": True,  # per-file flag after all analyzers
    "py_toolchain_id": "MAPP_PY_V1",
    "py_tool_versions": {
        "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "platform": sys.platform,
        # Add pytest, ruff, mypy if available via subprocess
    }
}
```

**Validation:**
- All records have non-NULL `py_analysis_run_id`
- Timestamps are ISO 8601 UTC
- Tool versions dictionary is valid JSON

---

### Phase 2: Registry Promotion (2-4 hours)

#### 2.1 Generate Comprehensive Patches
**Goal:** Create RFC-6902 patches for all completed columns

**Inputs:**
- `.state/purpose_mapping/FILE_PURPOSE_REGISTRY.json` (Step 3)
- `.state/purpose_mapping/PY_COLUMNS_TRANSFORMED.jsonl` (Phase 1.3)
- `.state/purpose_mapping/SHA256_TO_FILE_ID.json` (Phase 1.2)

**Script:** Enhance `P_01260207201000000985_01999000042260130009_registry_promoter.py`

**Patch Operations Per File:**
```json
[
  {"op": "add", "path": "/files/{idx}/py_capability_tags", "value": ["REGISTRY:VALIDATE", "IDS:SCAN"]},
  {"op": "add", "path": "/files/{idx}/py_imports_hash", "value": "abc123..."},
  {"op": "add", "path": "/files/{idx}/py_component_count", "value": 12},
  {"op": "add", "path": "/files/{idx}/py_analysis_run_id", "value": "RUN-20260305-060646-a3f2e1"},
  ...
]
```

**Validation:**
- Patch file valid RFC-6902 JSON
- All paths reference valid registry file indices
- No duplicate operations
- Evidence bundle includes patch SHA-256

**Deliverable:** `.state/evidence/registry_integration/purpose_mapping/patch_ssot_py_columns_complete.rfc6902.json`

---

#### 2.2 Dry-Run Validation
**Goal:** Test patches without modifying SSOT

**Command:**
```powershell
python capability_mapper.py --step 4 --registry-mode dry-run
```

**Checks:**
- No patch application errors
- Simulated registry passes schema validation
- Column counts match expectations
- Evidence report shows success

**Exit Criteria:** Zero errors in dry-run

---

#### 2.3 Apply to SSOT Registry
**Goal:** Commit patches to production registry

**Pre-Apply Backup:**
```powershell
# Backup current registry
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
Copy-Item "REGISTRY\01999000042260124503_REGISTRY_file.json" `
          "REGISTRY\01260207201000001133_backups\REGISTRY_file_pre_capability_mapping_$timestamp.json"
```

**Apply Command:**
```powershell
python capability_mapper.py --step 4 --registry-mode apply
```

**Post-Apply Validation:**
- Registry file valid JSON
- File count unchanged
- Sample 10 random files → verify `py_*` columns present
- Generate diff report: before vs after column population

**Rollback Plan:**
```powershell
# If validation fails
Copy-Item "REGISTRY\01260207201000001133_backups\REGISTRY_file_pre_capability_mapping_$timestamp.json" `
          "REGISTRY\01999000042260124503_REGISTRY_file.json" -Force
```

---

### Phase 3: Convergent Evidence Integration (2-3 hours)

#### 3.1 Add Timestamp Clustering Analysis
**Goal:** Implement timestamp-based burst detection per downloaded spec

**Implementation:** New script `P_01999000042260305003_timestamp_cluster_analyzer.py`

**Algorithm:**
```python
# Sort files by LastWriteTimeUtc
files_sorted = sorted(inventory, key=lambda f: f['mtime_utc'])

# Cluster with 120-second gap threshold
clusters = []
current_cluster = []
for i, file in enumerate(files_sorted):
    if i == 0:
        current_cluster.append(file)
        continue
    
    time_gap = (parse_iso(file['mtime_utc']) - parse_iso(files_sorted[i-1]['mtime_utc'])).total_seconds()
    
    if time_gap <= 120:  # Same burst
        current_cluster.append(file)
    else:
        clusters.append(current_cluster)
        current_cluster = [file]
```

**Output:** `.state/purpose_mapping/TIMESTAMP_CLUSTERS.json`

**Schema:**
```json
{
  "cluster_id": "BURST-20260205-143022",
  "time_span_seconds": 87,
  "file_count": 14,
  "files": ["file_id_1", "file_id_2", ...],
  "confidence_signals": {
    "shared_imports": 8,
    "same_capability_domain": true
  }
}
```

---

#### 3.2 Integrate AI Provenance Logs
**Goal:** Link files to AI editing sessions

**Use:** Existing `01999000042260125146_AI_CLI_PROVENANCE_SOLUTION`

**Actions:**
1. Run provenance collector:
   ```powershell
   python REGISTRY\01260207201000001313_capability_mapping_system\01999000042260125146_AI_CLI_PROVENANCE_SOLUTION\P_01999000042260125176_ai_cli_provenance_collector.py
   ```

2. Join provenance events to file inventory via paths

3. Add `provenance_session_id` to transformed output

**Validation:**
- Provenance DB created: `.state/provenance/ai_cli_events.db`
- Query returns file→session mappings
- Evidence hashes recorded

---

#### 3.3 Generate Convergent Mapping Report
**Goal:** Multi-signal confidence scoring

**Convergence Scoring:**
```python
for file in files:
    signals = {
        "time_cluster": file in any_burst_cluster,  # +1
        "capability_tagged": len(file['py_capability_tags']) > 0,  # +2
        "has_imports": len(file['py_imports_local']) > 0,  # +1
        "provenance_linked": file['provenance_session_id'] is not None,  # +3
        "ast_valid": file['py_ast_parse_ok'] == True  # +1
    }
    
    score = sum(signals.values())
    confidence = "HIGH" if score >= 6 else "MEDIUM" if score >= 3 else "LOW"
```

**Output:** `.state/purpose_mapping/CONVERGENT_MAPPING_REPORT.md`

**Report Sections:**
- High-confidence feature groups (≥6 signals)
- Medium-confidence candidates (3-5 signals)
- Low-confidence files needing review
- Unresolved references (ambiguous basename, broken imports)

---

### Phase 4: Validation & Documentation (1-2 hours)

#### 4.1 End-to-End Test
**Test Case:** Pick 3 Python files (simple, medium, complex) and verify full pipeline

**Verification Steps:**
1. Check CAPABILITIES.json lists file as candidate
2. Check FILE_INVENTORY.jsonl has metadata record
3. Check FILE_PURPOSE_REGISTRY.json has purpose mapping
4. Check REGISTRY_file.json has all applicable `py_*` columns populated
5. Check convergent report includes file with confidence score

**Expected Results:**
- All 3 files have 10+ `py_*` columns populated
- Capability tags present and match vocab
- Evidence trails complete (SHA-256 hashes traceable)

---

#### 4.2 Generate Completion Report
**Script:** `P_01999000042260305004_generate_completion_report.py`

**Report Contents:**
```markdown
# Capability Mapping Completion Report

Generated: 2026-03-05T10:30:00Z
Plan ID: PLAN-20260305-CAPABILITY-MAPPING-V1

## Pipeline Status
- Step 1 (Capability Discovery): ✅ COMPLETE (73 capabilities, 574 files)
- Step 2 (File Inventory): ✅ COMPLETE (574 files)
- Step 3 (Purpose Mapping): ✅ COMPLETE (574 mappings, avg confidence: 0.87)
- Step 4 (Registry Promotion): ✅ APPLIED (796 patch operations)

## Column Population Summary
| Status | Count | Percentage |
|--------|-------|------------|
| DIRECT | 1 | 3% |
| POPULATED (was RENAME) | 3 | 8% |
| POPULATED (was PARTIAL) | 11 | 30% |
| POPULATED (new metadata) | 6 | 16% |
| MISSING (advanced) | 16 | 43% |
| **TOTAL POPULATED** | **21** | **57%** |

## Evidence Artifacts
- Capability evidence: .state/evidence/purpose_mapping/step1_*.json
- Inventory evidence: .state/evidence/purpose_mapping/step2_*.json
- Mapping evidence: .state/evidence/purpose_mapping/step3_*.json
- Registry patches: .state/evidence/registry_integration/purpose_mapping/*.rfc6902.json
- Convergent report: .state/purpose_mapping/CONVERGENT_MAPPING_REPORT.md

## Known Limitations
- 16 py_* columns remain NULL (require external tools or advanced analyzers)
- Similarity clustering not implemented (py_overlap_* columns)
- Test execution columns require pytest integration
- Quality scoring requires composite analyzer
```

---

#### 4.3 Update System Documentation
**Files to Update:**

1. `REGISTRY/01260207201000001313_capability_mapping_system/01260207220000001319_README.md`
   - Change status from "dry-run only" to "APPLIED"
   - Add Phase 1-3 steps
   - Document new scripts

2. `COLUMN_HEADERS/PY_COLUMN_PIPELINE_MAPPING.md`
   - Update status table: PARTIAL→POPULATED
   - Add transformation notes

3. `COLUMN_HEADERS/REGISTRY_COLUMN_HEADERS.md`
   - Add populated percentage per column
   - Link to evidence locations

---

## Success Criteria

### Must-Have (Plan Passes)
- [ ] Step 3 completes without errors
- [ ] FILE_PURPOSE_REGISTRY.json exists with ≥500 mappings
- [ ] Transformation layer populates 11 PARTIAL columns
- [ ] File ID reconciliation complete (SHA-256 ↔ registry)
- [ ] Step 4 applies successfully to SSOT registry
- [ ] Registry backup exists and is valid
- [ ] 21+ `py_*` columns populated (57% coverage)
- [ ] Zero schema validation errors
- [ ] Evidence bundles generated with SHA-256 hashes

### Nice-to-Have (Future Enhancement)
- [ ] Timestamp clustering report generated
- [ ] AI provenance integrated
- [ ] Convergent mapping report shows HIGH confidence ≥300 files
- [ ] 25+ `py_*` columns populated (68% coverage)

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Step 3 fails (import errors) | MEDIUM | HIGH | Validate sys.path in Phase 0; use fallback imports |
| File ID reconciliation mismatches | LOW | HIGH | Validate 100% match rate before Step 4; fail-safe |
| Patch application corrupts registry | LOW | CRITICAL | Mandatory backup; dry-run validation; JSON schema check post-apply |
| Transformation errors (type mismatches) | MEDIUM | MEDIUM | Unit test transformations; allow NULL for missing data |
| Performance (574 files × 11 transforms) | LOW | LOW | Current mapp_py processes 500+ files in ~2 minutes |

---

## Rollback Procedures

### Phase 1 Rollback
- Delete intermediate files: `.state/purpose_mapping/PY_COLUMNS_TRANSFORMED.jsonl`
- No SSOT changes yet → safe to retry

### Phase 2 Rollback (If Step 4 Apply Fails)
```powershell
# Restore registry from backup
$backupFile = Get-ChildItem "REGISTRY\01260207201000001133_backups\" | 
              Where-Object { $_.Name -match "REGISTRY_file_pre_capability_mapping" } | 
              Sort-Object LastWriteTime -Descending | 
              Select-Object -First 1

Copy-Item $backupFile.FullName "REGISTRY\01999000042260124503_REGISTRY_file.json" -Force

# Verify restore
python -c "import json; r=json.load(open('REGISTRY/01999000042260124503_REGISTRY_file.json')); print('Restore OK' if 'files' in r else 'FAILED')"
```

### Phase 3 Rollback
- Evidence artifacts only → no rollback needed

---

## Resource Requirements

### Time Estimates
- Phase 0: 1 hour
- Phase 1: 4-8 hours (parallelizable if scripts independent)
- Phase 2: 2-4 hours (includes validation delays)
- Phase 3: 2-3 hours (optional but valuable)
- Phase 4: 1-2 hours
- **Total: 10-18 hours (1.5-2.5 days)**

### Dependencies
- Python 3.10+ (for sys.stdlib_module_names)
- Existing mapp_py library (30 modules)
- Registry write access
- ~500MB disk space for evidence artifacts

### Team Requirements
- Executor: 1 person with Python + Gov_Reg system knowledge
- Reviewer: 1 person for validation (can be same)
- Approval: System owner (for Step 4 apply)

---

## Next Actions

### Immediate (Today)
1. **Review this plan** with system owner
2. **Run Phase 0** pre-flight checks (1 hour)
3. **Decision point**: Proceed to Phase 1 or refine plan?

### Tomorrow
4. **Execute Phase 1** (Step 3 + transformations)
5. **Generate patches** (Phase 2.1, 2.2 dry-run)
6. **Request approval** for Step 4 apply

### Day 3
7. **Apply to SSOT** (Phase 2.3 with backup)
8. **Generate evidence** (Phase 3, optional)
9. **Completion report** (Phase 4)

---

## Plan Evaluation Checklist

When evaluating this plan, verify:

- [ ] **Clarity**: Can another engineer execute this without asking questions?
- [ ] **Safety**: Are backup/rollback procedures adequate?
- [ ] **Measurable**: Are success criteria objective and testable?
- [ ] **Scope**: Does this complete the stated goal (populate py_* columns)?
- [ ] **Evidence**: Will execution produce auditable artifacts?
- [ ] **Determinism**: Will repeated execution produce identical results?
- [ ] **Alignment**: Does this match the downloaded specs (timestamp clustering, convergent evidence)?

---

## Appendix A: File Manifest

### New Files Created by This Plan
- `P_01999000042260305001_file_id_reconciler.py` (Phase 1.2)
- `P_01999000042260305002_py_column_transformer.py` (Phase 1.3)
- `P_01999000042260305003_timestamp_cluster_analyzer.py` (Phase 3.1)
- `P_01999000042260305004_generate_completion_report.py` (Phase 4.2)

### Modified Files
- `capability_mapper.py` (add run metadata collection)
- `registry_promoter.py` (integrate transformer output)

### Output Artifacts
- `.state/purpose_mapping/FILE_PURPOSE_REGISTRY.json`
- `.state/purpose_mapping/SHA256_TO_FILE_ID.json`
- `.state/purpose_mapping/PY_COLUMNS_TRANSFORMED.jsonl`
- `.state/purpose_mapping/TIMESTAMP_CLUSTERS.json`
- `.state/purpose_mapping/CONVERGENT_MAPPING_REPORT.md`
- `.state/evidence/registry_integration/purpose_mapping/patch_ssot_py_columns_complete.rfc6902.json`
- `REGISTRY/01260207201000001133_backups/REGISTRY_file_pre_capability_mapping_*.json`

---

## Appendix B: Column Coverage Detail

### Immediately Achievable (21 columns, 57%)
**DIRECT (1):** `py_imports_hash`  
**RENAME (3):** `py_complexity_cyclomatic`, `py_deliverable_kinds`, `py_deliverable_signature_hash`  
**PARTIAL→POPULATED (11):** `py_ast_dump_hash`, `py_ast_parse_ok`, `py_component_count`, `py_defs_classes_count`, `py_defs_functions_count`, `py_deliverable_interfaces`, `py_imports_local`, `py_imports_stdlib`, `py_imports_third_party`, `py_io_surface_flags`, `py_security_risk_flags`  
**NEW METADATA (6):** `py_analysis_run_id`, `py_analysis_success`, `py_analyzed_at_utc`, `py_tool_versions`, `py_toolchain_id`, `py_capability_tags`

### Future Work (16 columns, 43%)
**Advanced Analyzers Needed (7):** `py_canonical_candidate_score`, `py_canonical_text_hash`, `py_component_artifact_path`, `py_component_ids`, `py_defs_public_api_hash`, `py_deliverable_inputs`, `py_deliverable_outputs`, `py_capability_facts_hash`  
**Similarity/Clustering (3):** `py_overlap_best_match_file_id`, `py_overlap_group_id`, `py_overlap_similarity_max`  
**Quality/Testing (4):** `py_quality_score`, `py_coverage_percent`, `py_pytest_exit_code`, `py_tests_executed`  
**External Tools (2):** `py_static_issues_count` (ruff/pylint)

---

**Plan Status:** ✅ READY FOR EVALUATION  
**Approval Required:** System Owner → Proceed to Phase 0  
**Expected Completion:** 2026-03-07 (if started 2026-03-05)
