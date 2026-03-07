# AI Execution Instructions: Registry Automation Plan V3

**For:** Claude Code or any AI agent executing `PLAN-20260305-UNIFIED-V3-MERGED`
**Created:** 2026-03-06
**Plan documents:**
- Narrative plan: `01260207201000001250_REGISTRY/UNIFIED_SOLUTION_PLAN_V3_MERGED.md`
- Machine-readable steps: `01260207201000001250_REGISTRY/UNIFIED_SOLUTION_PLAN_V3_REMAINING_STEPS.json`
- Architecture detail: `01260207201000001250_REGISTRY/docs/ARCHITECTURE_RUNTIME_ENGINE.md`
- Project conventions: `01260207201000001250_REGISTRY/01260202173939000109_CLAUDE.md`

---

## Before You Start: Mandatory Context Load

Read these files before taking any action:

1. `01260207201000001250_REGISTRY/01260202173939000109_CLAUDE.md` — project conventions and constraints (MUST follow throughout)
2. `01260207201000001250_REGISTRY/UNIFIED_SOLUTION_PLAN_V3_MERGED.md` — the full plan
3. `01260207201000001250_REGISTRY/UNIFIED_SOLUTION_PLAN_V3_REMAINING_STEPS.json` — task list (use this to track what is done/not done)
4. `01260207201000001250_REGISTRY/docs/KNOWN_ISSUES.md` — known blockers before touching scripts
5. `01260207201000001250_REGISTRY/docs/ARCHITECTURE_RUNTIME_ENGINE.md` — implementation pseudocode for Phase 0 and Week 2 scripts

---

## Repo Root

All relative paths in these instructions are relative to: `C:\Users\richg\Gov_Reg\`

All commands run from this directory unless otherwise noted.

---

## Execution Order

Execute phases strictly in this order. Do not start a later phase until the current phase validates cleanly.

```
Phase 0 (Pre-flight)
  → Week 1 (Tactical wins)
    → Week 2 Track A + Track B (parallel if separate context; serial if single agent)
      → Week 3 (Integration)
```

Week 2 Track A (Runtime Engine) and Track B (Entity Canonicalization) are independent and can run in parallel, but both must finish before Week 3 begins.

---

## Phase 0: Pre-Flight Stabilization (3 days estimated)

**Goal:** Clean baseline — 0 enum drift, all analyzers complete, all scripts produce correct output keys.

**Scripts in scope (all in `01260207201000001250_REGISTRY/01260207201000001313_capability_mapping_system/01260207220000001318_mapp_py/`):**

---

### Step 0.1 — Enum Canon + Drift Gate

**New script to create:** `P_01999000042260305000_enum_drift_gate.py`
**Location:** `01260207201000001250_REGISTRY/01260207201000001313_capability_mapping_system/01260207220000001318_mapp_py/`
**Implementation detail:** `docs/ARCHITECTURE_RUNTIME_ENGINE.md` § "Day 0.1"

**What it does:**
- Builds `REGISTRY_ENUMS_CANON.json` with canonical enum values and legacy aliases
- Validates `01999000042260124503_REGISTRY_file.json` for drift in `repo_root_id` and `canonicality`
- Generates RFC-6902 normalization patches for auto-fixable violations

**Validation gate:**
```bash
python 01260207201000001250_REGISTRY/01260207201000001313_capability_mapping_system/01260207220000001318_mapp_py/P_01999000042260305000_enum_drift_gate.py
```
Expected: `No enum drift detected - GATE PASSED` (after applying patches)

**Before applying patches:** Back up the registry:
```bash
cp "01260207201000001250_REGISTRY/01999000042260124503_REGISTRY_file.json" \
   "01260207201000001133_backups/REGISTRY_file_pre_enum_norm_$(date +%Y%m%d_%H%M%S).json"
```

**Stop if:** Any drift violations cannot be auto-fixed (no alias mapping). Report to human.

---

### Step 0.2 — Finish 7 Stubbed Analyzers

**Files to implement (all stubs — read each before writing):**

| Script | Location |
|--------|----------|
| `P_01260202173939000061_component_extractor.py` | `mapp_py/` |
| `P_01260202173939000062_generate_component_signature.py` | `mapp_py/` |
| `P_01260202173939000063_dependency_analyzer.py` | `mapp_py/` |
| `P_01260202173939000064_i_o_surface_visitor.py` | `mapp_py/` |
| `P_01260202173939000066_structural_feature_extractor.py` | `mapp_py/` |
| `P_01260202173939000067_extract_semantic_features.py` (also: `semantic_similarity.py`) | `mapp_py/` |
| `P_01260202173939000068_file_comparator.py` | `mapp_py/` |

**Implementation notes:**
- Read the stub file fully before implementing — stubs may have partial signatures
- Follow the output key schema from `docs/ARCHITECTURE_RUNTIME_ENGINE.md`
- Do NOT use `eval()` anywhere
- All scripts must accept a file path as the first positional argument

**Validation gate:**
```bash
python 01260207201000001250_REGISTRY/01260207201000001313_capability_mapping_system/01260207220000001318_mapp_py/P_01260202173939000084_registry_integration_pipeline.py \
  --file 01260207201000001250_REGISTRY/01260207201000001313_capability_mapping_system/01260207220000001318_mapp_py/P_01260202173939000060_text_normalizer.py \
  --registry 01260207201000001250_REGISTRY/01999000042260124503_REGISTRY_file.json \
  --phase A --dry-run --output .state/test_phase_a.json
```
Expected: Phase A complete with 21 columns populated per file. No import errors.

---

### Step 0.3 — Fix Column-Name Mismatches in 4 Scripts

**Read each script before editing. Make only the exact renames listed.**

| Script | Change |
|--------|--------|
| `P_01260202173939000060_text_normalizer.py` | `py_text_normalized_hash` → `py_canonical_text_hash` (lines ~161, 170, 179) |
| `P_01260202173939000061_component_extractor.py` | `py_classes_count` → `py_defs_classes_count`; `py_functions_count` → `py_defs_functions_count`; `py_methods_count` → `py_component_count` (compute as `len(classes)+len(functions)+len(methods)`); `py_components_hash` → `py_defs_public_api_hash`. Apply same renames in error-return block. |
| `P_01260202173939000071_complexity_visitor.py` | `py_cyclomatic_complexity` → `py_complexity_cyclomatic` (lines ~161, 176, 187) |
| `P_01260202173939000069_analyze_tests.py` | Add `py_tests_executed: True`; add `py_pytest_exit_code: result["returncode"]`; rename `py_test_coverage_pct` → `py_coverage_percent` |

**Validation:** Run each modified script standalone on a sample `.py` file and verify the output JSON contains only the new key names.

---

### Step 0.4 — Add `--json` Flag to 11 Scripts

**Pattern to add to each script's `main()` after computing `result`:**
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

**Scripts (read each before editing):**
1. `P_01260202173939000060_text_normalizer.py`
2. `P_01260202173939000061_component_extractor.py`
3. `P_01260202173939000062_generate_component_signature.py` (special — see below)
4. `P_01260202173939000063_dependency_analyzer.py`
5. `P_01260202173939000064_i_o_surface_visitor.py`
6. `P_01260202173939000065_deliverable_analyzer.py`
7. `P_01260202173939000076_capability_detector.py`
8. `P_01260202173939000079_analyze_file.py`
9. `P_01260202173939000069_analyze_tests.py`
10. `P_01260202173939000070_run_pylint_on_file.py`
11. `P_01260202173939000071_complexity_visitor.py`

**Special case — script 3 (`generate_component_signature.py`):**
This script uses positional args `<file_id> <components_json>`. Add `--json` support AFTER those args are processed, not before. The `--json` handler checks `sys.argv` after normal arg parsing completes.

**Validation:** Call each script with `--json /tmp/test_out.json` and a sample file. Verify the output file is written and is valid JSON.

---

### Step 0.5 — Fix capability_detector Hash + quality_scorer Breakdown

**Script 1: `P_01260202173939000076_capability_detector.py`**

Read the file. In `tag_file_capabilities()`, after building the capabilities set:
```python
import hashlib
facts = {"capability_tags": sorted(list(capabilities))}
facts_json = json.dumps(facts, sort_keys=True, separators=(',', ':'))
facts_hash = hashlib.sha256(facts_json.encode('utf-8')).hexdigest()
```
Add `"py_capability_facts_hash": facts_hash` to the return dict.
Add `"py_capability_facts_hash": None` to the error-return dict.

**Script 2: `P_01260202173939000085_quality_scorer.py`**

Read the file. Find `generate_breakdown()`. Replace the `# Continue for other components...` stub (line ~149) with working breakdown logic for:
- **Docstrings** — mirror the docstring scoring logic from `calculate_score()`
- **Lint** — mirror the lint scoring logic
- **Complexity** — mirror the complexity scoring logic

Each breakdown component needs `weight`, `earned`, and `notes` fields.

**Validation:** Call each script standalone, verify output JSON contains the new fields.

---

### Phase 0 Gate (all steps must pass before proceeding)

```bash
# 1. Enum drift clear
python .../P_01999000042260305000_enum_drift_gate.py
# 2. Phase A pipeline works end-to-end
python .../P_01260202173939000084_registry_integration_pipeline.py \
  --file .../P_01260202173939000060_text_normalizer.py \
  --registry .../01999000042260124503_REGISTRY_file.json \
  --phase A --dry-run --output .state/test_phase_a.json
# 3. Inspect .state/test_phase_a.json — must have 21 py_* columns
```

---

## Week 1: Tactical Wins (5-7 days estimated)

**Goal:** 27 py_* columns populated for all Python files.

---

### Step 1.1 — Execute Capability Mapping Step 3

```bash
python 01260207201000001250_REGISTRY/01260207201000001313_capability_mapping_system/P_01260207220000001315_capability_mapper.py \
  --step 3 --repo-root .
```

**Validation:** `.state/purpose_mapping/FILE_PURPOSE_REGISTRY.json` exists with >= 500 files mapped.

**Stop if:** Step 3 fails with import or data errors. Inspect `capability_mapper.py` before re-running.

---

### Step 1.2 — Build File ID Reconciliation Layer

**New script to create:** `P_01999000042260305001_file_id_reconciler.py`
**Location:** `01260207201000001250_REGISTRY/01260207201000001313_capability_mapping_system/01260207220000001318_mapp_py/`
**Detail:** `docs/ARCHITECTURE_RUNTIME_ENGINE.md` § "Phase 1 / 1.3 File ID Reconciliation"

**What it does:**
- Reads registry JSON, builds `sha256 → file_id` and `file_id → sha256` dicts
- Writes `SHA256_TO_FILE_ID.json` to `.state/purpose_mapping/`
- Validates: all file_ids are 20-digit numeric, all sha256 values are 64-char hex

**Critical constraint:** Component IDs must use `file_id` (20-digit), never `doc_id` or `content_sha256`.

---

### Step 1.3 — Build Transformation Layer for Phase A Columns

**New script to create:** `P_01999000042260305002_py_column_transformer.py`
**Location:** `mapp_py/`
**Detail:** `docs/ARCHITECTURE_RUNTIME_ENGINE.md` § "Phase 1 / 1.1 Intake Orchestrator"

**What it does:**
- Reads `FILE_INVENTORY.jsonl` entries (from Step 2 of capability mapping, already run)
- Transforms `facts` dict → registry `py_*` column format
- Handles DIRECT (use as-is), RENAME (key remapping), and PARTIAL (compute from multiple facts) column types
- Covers all 21 Phase A columns

---

### Step 1.4 — Add Run Metadata Collection

**File to modify:** `registry_promoter.py` (read it first to locate the right insertion point)

Add `_collect_run_metadata()` method that returns:
```python
{
    "py_analysis_run_id": "<uuid4>",
    "py_analyzed_at_utc": "<ISO8601 UTC>",
    "py_analysis_success": True,
    "py_toolchain_id": "registry_automation_v3",
    "py_tool_versions": {"python": sys.version, ...},
    "py_component_artifact_path": "<path to inventory>"
}
```

---

### Step 1.5 — Generate and Apply Comprehensive Patches

**File to modify:** `registry_promoter.py` — add `promote_unified()` method.

**Sequence:**
1. Load `FILE_PURPOSE_REGISTRY.json` (capability mapping output)
2. Load transformed py_* columns from transformer
3. Load `SHA256_TO_FILE_ID.json` (reconciliation map)
4. Generate RFC-6902 patch set (~1500 operations expected)
5. **Back up registry before applying:**
   ```bash
   cp "01260207201000001250_REGISTRY/01999000042260124503_REGISTRY_file.json" \
      "01260207201000001133_backups/REGISTRY_file_pre_week1_$(date +%Y%m%d_%H%M%S).json"
   ```
6. Dry-run first (`--dry-run`), inspect output
7. Apply if dry-run clean

**Validation:** 27 py_* columns populated in registry for Python files.

---

## Week 2: Foundation + Entity Canonicalization (5-7 days estimated)

**Two parallel tracks:**

---

### Track A: Column Runtime Engine (Days 1-5)

Create 7 new scripts in `mapp_py/`. Implementation detail in `docs/ARCHITECTURE_RUNTIME_ENGINE.md`.

| Script | Purpose |
|--------|---------|
| `P_01999000042260305010_column_runtime_loader.py` | Load + merge 4 governance sources; detect inconsistencies |
| `P_01999000042260305011_dependency_scheduler.py` | Topological sort of column dependencies |
| `P_01999000042260305012_trigger_dispatcher.py` | Route derivations by trigger type |
| `P_01999000042260305013_derivation_executor.py` | Execute column derivation formulas |
| `P_01999000042260305014_lookup_resolver.py` | Cross-registry field lookups |
| `P_01999000042260305015_patch_generator.py` | RFC-6902 patch generation |
| `P_01999000042260305016_evidence_writer.py` | SHA-256 evidence trail writer |

**Governance source files (inputs to loader):**
- `01260207201000001250_REGISTRY/COLUMN_HEADERS/COLUMN_DICTIONARY_184_COLUMNS.csv`
- `01260207201000001250_REGISTRY/COLUMN_HEADERS/01260207201000000193_UNIFIED_SSOT_REGISTRY_WRITE_POLICY.yaml`
- `01260207201000001250_REGISTRY/COLUMN_HEADERS/formula_sheet_classification.csv`
- `01260207201000001250_REGISTRY/COLUMN_HEADERS/PY_COLUMN_PIPELINE_MAPPING.csv`

**Track A validation gate:**
```bash
python .../P_01999000042260305010_column_runtime_loader.py --validate-only
```
Expected before inconsistency resolution: exactly 51 inconsistencies detected.
Expected after resolution (Step 2.C): 0 inconsistencies.

**Dependency graph must be acyclic** — the scheduler must raise `ValueError` on cycles.

---

### Track B: Entity Canonicalization (Days 1-2)

**Step 2.B.1 — Canonicalize entity set**

**New script:** `P_01999000042260305025_canonicalize_entity_set.py`

**What it does:**
- Reads `01999000042260124503_REGISTRY_file.json`
- Declares `files[]` array as authoritative
- Moves `entities[]` and `entries[]` to `LEGACY_OVERLAYS.json` (non-authoritative)
- Creates `01260207201000001250_REGISTRY/canonical_v4/REGISTRY_ENTITIES.json`

**Back up before running:**
```bash
cp "01260207201000001250_REGISTRY/01999000042260124503_REGISTRY_file.json" \
   "01260207201000001133_backups/REGISTRY_file_pre_canonicalize_$(date +%Y%m%d_%H%M%S).json"
```

**Step 2.B.2 — Create entity schema v4**

**New artifact:** `01260207201000001250_REGISTRY/canonical_v4/schema.entities.v4.json`

Schema must include expanded enums:
- `repo_root_id`: `["GOV_REG_WORKSPACE", "ALL_AI", "AI_PROD_PIPELINE"]`
- `canonicality`: `["CANONICAL", "LEGACY", "ALTERNATE", "EXPERIMENTAL"]`

Entity-only schema — do NOT include edge or generator fields (those are deferred).

---

### Resolve 51 Inconsistencies (Days 3-5, after Track A loader is working)

Four resolution types (full detail in `UNIFIED_SOLUTION_PLAN_V3_MERGED.md` § "Days 3-5"):

**Type A — 18 editorial columns:** Update `WRITE_POLICY.yaml` to set `update_policy: manual_patch_only` for: `description`, `one_line_purpose`, `short_description`, `notes`, `function_code_1/2/3`, `deliverables`, `inputs`, `outputs`, `tags`, `step_refs`, `superseded_by`, `validation_rules`, `bundle_key`, `bundle_role`, `bundle_version`, `resolver_hint`

**Type B — 14 inferrable columns:** Add formulas to `formula_sheet_classification.csv` for: `status` (default `'active'`), `entity_kind`, `canonicality` (default `'CANONICAL'`), and others. Update `DerivationExecutor` to evaluate these.

**Type C — 9 immutable fields:** Document in `WRITE_POLICY.yaml` as `update_policy: immutable`, `trigger: on_create_only`. Fields: `created_by`, `record_kind`, `source_file_id`, `target_file_id`, `source_entity_id`, `target_entity_id`, `directionality`, `rel_type`, `edge_type`

**Type D — 10 lookup columns:** Implement in `P_01999000042260305014_lookup_resolver.py`: `asset_id`, `asset_family`, `asset_version`, `external_ref`, `external_system`, `declared_dependencies`, `path_aliases`, `metadata`, `input_filters`, `output_path_pattern`

**Week 2 validation gate (all tracks):**
```bash
python .../P_01999000042260305010_column_runtime_loader.py --validate-only
# Expected: 0 inconsistencies found
```

---

## Week 3: Integration + Pipeline Completion (5-7 days estimated)

**Goal:** ALL 37 py_* columns operational. Entity-level automation deployed.

---

### Step 3.1 — Fix file_id Resolver in Pipeline

**File to modify:** `P_01260202173939000084_registry_integration_pipeline.py`

Add to `RegistryIntegrationPipeline.__init__()`:
```python
self.file_id_lookup = self._build_file_id_lookup()
```

Add `_build_file_id_lookup()` method:
- Reads registry JSON
- Returns dict: `{relative_path: file_id, absolute_path: file_id}`
- Normalizes paths (forward slashes)

In `analyze_file()`: resolve `file_id` by exact path match, then normalized path match. Set `results['file_id']` or record error.

Also add `analyze_file.py` to the Phase A script list (it was missing).

---

### Step 3.2 — Implement Phase B in Pipeline

**File to modify:** `P_01260202173939000084_registry_integration_pipeline.py`

Replace Phase B `pass` no-op with actual script execution:
- 60-second timeout (tests take longer than Phase A)
- `quality_scorer.py` runs LAST

Add `_build_script_args()` helper:
- Default: `[python, script, file_path, '--json', output_file]`
- `quality_scorer.py`: write accumulated Phase A+B results to temp JSON, invoke as `python quality_scorer.py --metrics-json <temp> --output <output>`

Phase B script order:
```python
['test_runner.py', 'linter_runner.py', 'complexity_analyzer.py', 'quality_scorer.py']
```

**Columns produced:** `py_tests_executed`, `py_pytest_exit_code`, `py_coverage_percent`, `py_static_issues_count`, `py_complexity_cyclomatic`, `py_quality_score`

---

### Step 3.3 — Implement Phase C in Pipeline

**File to modify:** `P_01260202173939000084_registry_integration_pipeline.py`

Add `run_phase_c(all_results)` method with two stages:

**Stage 1 — Batch (all files):**
1. Merge all per-file results into `{"files": [...]}` format → write `tmp/batch_registry.json`
2. Run `similarity_clusterer.py --registry-json tmp/batch_registry.json --output tmp/clusters.json` → `py_overlap_group_id`
3. Run `canonical_ranker.py --registry-json tmp/batch_registry.json --clusters-json tmp/clusters.json --output tmp/rankings.json` → `py_canonical_candidate_score`

**Stage 2 — Per-cluster pairwise (multi-file clusters only):**
4. Read `tmp/clusters.json`, identify clusters with 2+ files
5. For each file in a multi-file cluster, run structural + semantic extractors against cluster peers:
   ```
   python structural_feature_extractor.py <target> <peer1> <peer2> ...
   python extract_semantic_features.py <target> <peer1> <peer2> ...
   ```
   Capture stdout, parse the JSON scores object from the `"All scores:"` block, write to `tmp/<file_id>_structural.json` and `tmp/<file_id>_semantic.json`
6. Run `file_comparator.py <target> tmp/<file_id>_structural.json tmp/<file_id>_semantic.json` → `py_overlap_similarity_max`, `py_overlap_best_match_file_path`
7. Map `py_overlap_best_match_file_path` → `py_overlap_best_match_file_id` using `self.file_id_lookup`

**Columns produced:** `py_overlap_group_id`, `py_overlap_similarity_max`, `py_overlap_best_match_file_id`, `py_canonical_candidate_score`

---

### Step 3.4 — File Intake Orchestrator (Entity-Only)

**New script:** `P_01999000042260305020_file_intake_orchestrator.py`
**Detail:** `docs/ARCHITECTURE_RUNTIME_ENGINE.md` § "Phase 1 / 1.1 Intake Orchestrator"

Writes to `canonical_v4/REGISTRY_ENTITIES.json` ONLY.
Loads capability registry from Week 1 output.
Uses Week 2 runtime engine components.
Does NOT write to edge or generator registries (those are deferred).

**Test:**
```bash
python .../P_01999000042260305020_file_intake_orchestrator.py \
  --file "01260207201000001250_REGISTRY/01260207201000001313_capability_mapping_system/01260207220000001318_mapp_py/P_01260202173939000060_text_normalizer.py" \
  --event-type file_create
```

---

### Step 3.5 — Timestamp Clustering + Convergent Report

**New script:** `P_01999000042260305003_timestamp_cluster_analyzer.py`

Generates: `.state/purpose_mapping/TIMESTAMP_CLUSTERS.json`

Convergent scoring (5 entity signals — edges are deferred):
```python
signals = {
    "fs_primitives": record.get("sha256") is not None,           # +1
    "artifact_kind_inferred": record.get("artifact_kind") is not None,  # +1
    "py_analysis_complete": record.get("py_analysis_success") == True,  # +2
    "capability_tagged": len(record.get("py_capability_tags", [])) > 0, # +2
    "temporal_clustered": record.get("temporal_cluster_id") is not None, # +1
}
# HIGH >= 5, MEDIUM 3-4, LOW < 3
```

---

### Step 3.6 — End-to-End Validation

Run all validation tests. All must pass before Week 3 is declared complete:

```bash
# 1. Full entity intake
python .../P_01999000042260305020_file_intake_orchestrator.py --file new_test_file.py

# 2. Runtime consistency
python .../P_01999000042260305010_column_runtime_loader.py --validate-only

# 3. Count py_* columns in canonical registry
python -c "
import json
r = json.load(open('01260207201000001250_REGISTRY/canonical_v4/REGISTRY_ENTITIES.json'))
sample = r['files'][0]
py_cols = [k for k in sample.keys() if k.startswith('py_')]
print(f'py_* columns found: {len(py_cols)} of 37')
assert len(py_cols) == 37, 'FAIL: not all 37 py_* columns populated'
"

# 4. Phase B dry-run
python .../P_01260202173939000084_registry_integration_pipeline.py \
  --file .../P_01260202173939000060_text_normalizer.py \
  --registry .../01999000042260124503_REGISTRY_file.json \
  --phase B --dry-run

# 5. Phase C batch dry-run
python .../P_01260202173939000084_registry_integration_pipeline.py \
  --batch \
  --registry .../01999000042260124503_REGISTRY_file.json \
  --phase C --dry-run

# 6. Hash determinism — run same file twice, compare *_hash columns
# 7. file_id format — verify all results['file_id'] are 20-digit numeric
```

---

## Safety Rules (from CLAUDE.md — enforce at every step)

1. **Always back up the registry before any write.** Use the backup path `01260207201000001133_backups/REGISTRY_file_pre_<operation>_<timestamp>.json`
2. **Always dry-run before applying patches.** Never apply RFC-6902 patches without first running `--dry-run` and inspecting the output.
3. **Never hardcode absolute paths.** Use `path_registry.py` (`resolve_path()`) or relative paths from repo root.
4. **Never use `eval()` in derivations.** Only the safe DSL.
5. **Never create duplicate 20-digit IDs.** Check `01260207201000001250_REGISTRY/01260207201000001116_COUNTER_STORE.json` (or equivalent allocator) before allocating.
6. **Never write to registry without validating against write policy** (`COLUMN_HEADERS/01260207201000000193_UNIFIED_SSOT_REGISTRY_WRITE_POLICY.yaml`).
7. **Run tests after any schema or validator changes:** `pytest tests/ -v`
8. **New script naming:** Follow the 20-digit prefix convention: `P_01999000042260305XXX_name.py`. Use IDs in sequence starting at `...305000` (Phase 0). Check for conflicts before creating.
9. **Scope constraint:** Do NOT implement edge registries, generator registries, bundle manifests, or bundle-commit protocol in this plan. Those are deferred. If encountered in existing code, leave them alone.

---

## Stop Conditions — Pause and Ask Human Before Continuing

Stop and report immediately if any of the following occur:

| Condition | Reason |
|-----------|--------|
| Enum drift violations that cannot be auto-fixed | Manual schema decision required |
| Registry JSON fails schema validation after a patch | Potential data corruption |
| Circular dependencies detected in column dependency graph | Architecture decision required |
| Step 3 (capability mapping) fails with < 500 files mapped | Data quality issue — may need manual mapping |
| Any script produces duplicate 20-digit file_ids | Critical governance violation |
| Week 1 patch application produces unexpected field overwrites on immutable columns | Write policy violation |
| Phase B external tools (pytest, ruff/pylint) are missing | Graceful NULL is acceptable but confirm with human |
| canonical_v4/REGISTRY_ENTITIES.json is missing after Track B | Track B did not complete |
| Any test in `pytest tests/ -v` fails after a change | Do not proceed — fix the test |

---

## What Is Deferred (Do Not Implement)

The following are explicitly out of scope for this plan:

- `REGISTRY_EDGES.json`
- `REGISTRY_GENERATORS.json`
- `REGISTRY_BUNDLE_MANIFEST.json`
- Edge discovery pipeline
- Inverted path index
- Convergent evidence scorer (edge-weighted variant)
- Bundle-commit protocol
- Anti-duplication rules (require edge pipeline)

These require entity canonicalization (this plan) to be complete first.

---

## Summary: 37 py_* Columns by Phase

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
