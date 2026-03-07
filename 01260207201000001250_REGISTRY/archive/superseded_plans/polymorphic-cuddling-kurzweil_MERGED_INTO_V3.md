# Plan: Fix All Issues & Complete Phase B/C for 37 py_* Registry Columns

## Context

The capability mapping system (`01260207201000001313_capability_mapping_system/`) has 20+ Python scripts designed to populate 37 `py_*` columns in the 185-column governance registry. Currently only 11 columns work end-to-end (Phase A core). The pipeline orchestrator has broken Phase B integration (no-op `pass`), no Phase C integration, column-name mismatches between scripts and registry, a missing hash computation, and a critical file_id lookup gap that prevents writing results back to the registry.

**Goal:** Make all 37 py_* columns fully populatable end-to-end.

---

## Step 0: Fix Column-Name Mismatches (4 scripts)

Scripts output keys that don't match registry column names. Each fix is a simple rename of output dict keys.

### 0a. `P_01260202173939000060_text_normalizer.py`
- Line 161, 170, 179: Rename `py_text_normalized_hash` → `py_canonical_text_hash`

### 0b. `P_01260202173939000061_component_extractor.py`
- Line 200: `py_classes_count` → `py_defs_classes_count`
- Line 201: `py_functions_count` → `py_defs_functions_count`
- Line 202: `py_methods_count` → `py_component_count` (compute as `len(classes) + len(functions) + len(methods)`)
- Line 204: `py_components_hash` → `py_defs_public_api_hash`
- Same renames in error return (lines 211-215)

### 0c. `P_01260202173939000071_complexity_visitor.py`
- Lines 161, 176, 187: Rename `py_cyclomatic_complexity` → `py_complexity_cyclomatic`

### 0d. `P_01260202173939000069_analyze_tests.py`
- Add `py_tests_executed: True` (boolean) to return dict
- Add `py_pytest_exit_code: result["returncode"]` to return dict
- Line 151: Rename `py_test_coverage_pct` → `py_coverage_percent`
- Keep existing `py_test_pass_count` etc. as supplemental data

---

## Step 1: Fix capability_detector.py — Add Missing py_capability_facts_hash

**File:** `P_01260202173939000076_capability_detector.py`

- Add `import hashlib` at top (currently missing)
- In `tag_file_capabilities()` (after line 140), compute hash:
  ```python
  facts = {"capability_tags": sorted(list(capabilities))}
  facts_json = json.dumps(facts, sort_keys=True, separators=(',', ':'))
  facts_hash = hashlib.sha256(facts_json.encode('utf-8')).hexdigest()
  ```
- Add `"py_capability_facts_hash": facts_hash` to the return dict (line 143)
- Add `"py_capability_facts_hash": None` to error return (line 150)

---

## Step 2: Fix quality_scorer.py — Complete generate_breakdown()

**File:** `P_01260202173939000085_quality_scorer.py`

Replace line 149 (`# Continue for other components...`) with the 3 missing breakdown components:
- **Docstrings:** Mirror logic from `calculate_score()` lines 66-78
- **Lint:** Mirror logic from lines 82-98
- **Complexity:** Mirror logic from lines 101-117

Each gets `weight`, `earned`, and `notes` fields matching the tests/coverage pattern.

---

## Step 3: Add `--json <output_file>` Flag to All Scripts

The pipeline invokes scripts with `[python, script.py, file_path, '--json', output_file]` but most scripts don't support this flag. Add a minimal `--json` handler to the `main()` of each script:

**Scripts to modify (10 total):**
1. `P_01260202173939000060_text_normalizer.py`
2. `P_01260202173939000061_component_extractor.py`
3. `P_01260202173939000063_dependency_analyzer.py`
4. `P_01260202173939000064_i_o_surface_visitor.py`
5. `P_01260202173939000065_deliverable_analyzer.py`
6. `P_01260202173939000076_capability_detector.py`
7. `P_01260202173939000079_analyze_file.py`
8. `P_01260202173939000069_analyze_tests.py`
9. `P_01260202173939000070_run_pylint_on_file.py`
10. `P_01260202173939000071_complexity_visitor.py`

**Pattern for each:** In `main()`, after computing `result`, check for `--json`:
```python
if '--json' in sys.argv:
    idx = sys.argv.index('--json')
    out_path = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else None
    if out_path:
        with open(out_path, 'w') as f:
            json.dump(result, f, indent=2, sort_keys=True)
    else:
        print(json.dumps(result, indent=2, sort_keys=True))
    sys.exit(0)
```

---

## Step 4: Resolve file_id Critical Blocker

**File:** `P_01260202173939000084_registry_integration_pipeline.py`

Add `_build_file_id_lookup()` method to `RegistryIntegrationPipeline`:
- Reads existing registry JSON
- Builds dict: `relative_path → file_id` and `absolute_path → file_id`
- Called in `__init__()`, stored as `self.file_id_lookup`

In `analyze_file()`, after line 100, resolve file_id:
- Try exact match on relative_path and absolute_path
- Try normalized path match (forward slashes)
- Set `results['file_id']` or append error if not found

---

## Step 5: Implement Phase B in Pipeline

**File:** `P_01260202173939000084_registry_integration_pipeline.py`

### 5a. Replace Phase B no-op (lines 165-173)
Replace `pass` with actual script execution — same pattern as Phase A loop but with:
- 60-second timeout (tests take longer)
- Quality scorer runs LAST (needs other Phase B outputs as input)
- Quality scorer uses `--metrics-json` input from accumulated results

### 5b. Add `_build_script_args()` helper method
Returns correct CLI args per script since quality_scorer has a unique interface (`--metrics-json <input> --output <output>`):
- Most scripts: `[python, script, file_path, '--json', output_file]`
- quality_scorer: write current results to temp JSON, pass as `--metrics-json`

### 5c. Update phase_b_scripts list to use correct logical names:
```python
phase_b_scripts = [
    'test_runner.py',        # → py_tests_executed, py_pytest_exit_code, py_coverage_percent
    'linter_runner.py',      # → py_static_issues_count
    'complexity_analyzer.py', # → py_complexity_cyclomatic
    'quality_scorer.py',     # → py_quality_score (MUST be last)
]
```

---

## Step 6: Implement Phase C in Pipeline (Batch Operations)

**File:** `P_01260202173939000084_registry_integration_pipeline.py`

### 6a. Add `run_phase_c(all_results)` method
Phase C is fundamentally different — it operates on ALL files at once after per-file analysis completes.

Steps within `run_phase_c()`:
1. Write all per-file results to a batch input JSON
2. Run `similarity_clusterer.py --registry-json <batch> --output <clusters>` → `py_overlap_group_id`
3. Run `canonical_ranker.py --registry-json <batch> --clusters-json <clusters> --output <rankings>` → `py_canonical_candidate_score`
4. Run `file_comparator.py` per file using structural/semantic features → `py_overlap_similarity_max`, `py_overlap_best_match_file_id`
5. Merge batch results back into per-file result dicts

### 6b. Update `analyze_batch()` to call Phase C
After the per-file loop completes, if `phase == 'C'`, call `self.run_phase_c(results)`.

---

## Step 7: Fix Phase A Script List in Pipeline

**File:** `P_01260202173939000084_registry_integration_pipeline.py` (lines 104-112)

Add missing script: `analyze_file.py` (AST parser producing `py_ast_dump_hash`, `py_ast_parse_ok`).

Updated list:
```python
phase_a_scripts = [
    'analyze_file.py',           # py_ast_dump_hash, py_ast_parse_ok
    'text_normalizer.py',        # py_canonical_text_hash
    'component_extractor.py',    # py_defs_*, py_component_count
    'component_id_generator.py', # py_component_ids
    'dependency_analyzer.py',    # py_imports_*
    'io_surface_analyzer.py',    # py_io_surface_flags, py_security_risk_flags
    'deliverable_analyzer.py',   # py_deliverable_*
    'capability_tagger.py',      # py_capability_tags, py_capability_facts_hash
]
```

---

## Implementation Order (by dependency)

| Order | Step | Files Modified | Depends On |
|-------|------|---------------|------------|
| 1 | Step 0 (column name fixes) | 4 scripts | — |
| 2 | Step 1 (capability hash) | 1 script | — |
| 3 | Step 2 (quality breakdown) | 1 script | — |
| 4 | Step 3 (--json flags) | 10 scripts | — |
| 5 | Step 4 (file_id resolver) | pipeline.py | — |
| 6 | Step 7 (Phase A script list) | pipeline.py | Steps 0, 3 |
| 7 | Step 5 (Phase B integration) | pipeline.py | Steps 0d, 3, 4 |
| 8 | Step 6 (Phase C integration) | pipeline.py | Steps 4, 5 |

**Total files modified: ~12** (10 analyzer scripts + pipeline + script resolver is already correct)

---

## Column Coverage After All Steps

| Phase | Columns | Count |
|-------|---------|-------|
| Integration | py_analysis_run_id, py_analyzed_at_utc, py_toolchain_id, py_tool_versions, py_analysis_success, py_component_artifact_path | 6 |
| A - Text/AST | py_canonical_text_hash, py_ast_dump_hash, py_ast_parse_ok | 3 |
| A - Components | py_defs_functions_count, py_defs_classes_count, py_defs_public_api_hash, py_component_count, py_component_ids | 5 |
| A - Imports | py_imports_stdlib, py_imports_third_party, py_imports_local, py_imports_hash | 4 |
| A - IO/Security | py_io_surface_flags, py_deliverable_inputs, py_deliverable_outputs, py_security_risk_flags | 4 |
| A - Deliverable | py_deliverable_kinds, py_deliverable_signature_hash, py_deliverable_interfaces | 3 |
| A - Capability | py_capability_tags, py_capability_facts_hash | 2 |
| B - Quality | py_tests_executed, py_pytest_exit_code, py_coverage_percent, py_static_issues_count, py_complexity_cyclomatic, py_quality_score | 6 |
| C - Batch | py_overlap_group_id, py_overlap_similarity_max, py_overlap_best_match_file_id, py_canonical_candidate_score | 4 |
| **Total** | | **37** |

---

## Verification Plan

1. **Unit test each renamed script:** Run each modified script standalone on a sample .py file, verify output JSON keys match registry column names exactly
2. **Pipeline Phase A:** `python pipeline.py --file sample.py --registry REGISTRY.json --phase A --dry-run --output test_a.json` — verify all 21 Phase A columns present
3. **Pipeline Phase B:** Same with `--phase B` — verify 6 Phase B columns added
4. **Pipeline Phase C:** `--batch --phase C` — verify 4 Phase C columns populated across multiple files
5. **file_id resolution:** Verify `results['file_id']` is 20-digit numeric for every analyzed file
6. **Registry patch generation:** Verify `update_registry()` generates correct RFC-6902 patches with valid file_id paths
7. **Hash determinism:** Run same file twice, verify all `*_hash` columns produce identical values
