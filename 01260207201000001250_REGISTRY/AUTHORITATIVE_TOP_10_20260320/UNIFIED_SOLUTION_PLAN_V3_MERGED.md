# Unified Registry Automation Plan — V3 (Merged)
## Entity-Scoped Complete Solution: Column Population, File Intake, and Governance Closure

**Plan ID:** `PLAN-20260305-UNIFIED-V3-MERGED`
**Created:** 2026-03-05
**Updated:** 2026-03-06
**Status:** ACTIVE — Supersedes V2, breezy-tickling-rose, polymorphic-cuddling-kurzweil
**Owner:** Gov_Reg Governance System
**Estimated Duration:** 18-24 days (3-4 weeks)
**Architecture Reference:** `docs/ARCHITECTURE_RUNTIME_ENGINE.md` (detailed implementation code for Phase 0 + Week 2 components)

---

## Merge Provenance

This plan merges three source documents:

| Source | Role | What Was Kept | What Was Changed/Cut |
|--------|------|---------------|----------------------|
| `UNIFIED_SOLUTION_PLAN.md` (V2) | Architecture + phases | Phase 0, Week 1, Week 2 Track A, inconsistency resolution | Week 2 Track B narrowed (entities only), Week 3 simplified, edges/generators/bundles deferred |
| `breezy-tickling-rose.md` | Scope narrowing decisions | Entity-only scope, deferred items list, timeline reduction, 17-script target | Was a meta-plan (instructions to rewrite V2); now incorporated directly |
| `polymorphic-cuddling-kurzweil.md` | Tactical py_* pipeline fixes | All 8 steps (column renames, --json flags, Phase B/C, file_id resolver) | Integrated into Phase 0 + Week 3; file_id resolver merged with V2's reconciler |

### Conflict Resolutions

| Conflict | Resolution | Rationale |
|----------|------------|-----------|
| V2 includes edges/generators/bundles; breezy defers them | **Defer** (per breezy) | Reduces scope creep; entities must be stable first |
| V2 caps py_* at 15-17; polymorphic targets all 37 | **Target all 37** (per polymorphic) | Phase B/C fixes close the gap; no reason to leave columns unpopulated |
| V2 creates standalone file_id reconciler; polymorphic adds it to pipeline | **Both**: standalone reconciler for batch use + pipeline-embedded lookup for runtime | They serve different use cases |
| V2 Phase 0 "finish stubbed analyzers" is vague; polymorphic has exact fixes | **Use polymorphic's specifics** as Phase 0 Sub-step 0.3 | Line-level fixes prevent silent failures |
| V2 Week 3 has duplicate "Day 4-5" sections | **Fixed** (per breezy verification checklist) | Numbering conflict removed |
| V2 convergent evidence uses 7 signals (2 edge-dependent); breezy uses 5 | **Use 5 signals** (per breezy) | Edge-dependent signals can't work without edge registry |

---

## Executive Summary

This plan delivers **entity-scoped registry automation** by merging tactical pipeline fixes with strategic runtime infrastructure, resolving all governance gaps in one unified execution.

### What Gets Fixed (Three Problems + Pipeline)

1. **37 `py_*` Columns** → ALL 37 populated end-to-end (Phase A: 21, Phase B: 6, Phase C: 4, Integration: 6)
2. **51 Inconsistent Columns** → All resolved (0 governance violations)
3. **File Intake Automation** → Entity-only S1-S6 pipeline operational
4. **Pipeline Completeness** → Column-name mismatches fixed, --json flags added, Phase B/C implemented

### What Is Deferred (Future Plan)

- `REGISTRY_EDGES.json` — needs entity canonicalization complete
- `REGISTRY_GENERATORS.json` — needs entity canonicalization complete
- Bundle Manifest — needs edge + generator registries
- Edge Discovery Pipeline — needs entity registry stable
- Inverted Path Index — needs edge pipeline
- Convergent Evidence Scorer (edge-weighted) — needs edge registry
- Bundle-Commit Protocol — needs multiple registries
- **Recommended future sequence:** Entities (this plan) → Edges → Generators → Bundle → Convergent Scoring

---

## Architecture: Phase Structure

```
PHASE 0: PRE-FLIGHT STABILIZATION (3 days)
├─ 0.1: Enum Canon + Drift Gate (eliminate repo_root_id/canonicality conflicts)
├─ 0.2: Finish 7 Stubbed Analyzers (~2,173 lines)
├─ 0.3: Fix Column-Name Mismatches (4 scripts, from polymorphic Step 0)
├─ 0.4: Add --json Flag to 11 Scripts (10 standard + component_id_generator)
├─ 0.5: Fix capability_detector.py hash + quality_scorer.py breakdown
│       (from polymorphic Steps 1-2)
└─ Deliverable: Clean baseline, 0 enum drift, all scripts produce correct output keys

WEEK 1: TACTICAL WINS (5-7 days)
├─ Execute Capability Mapping Steps 3-4
├─ File ID Reconciliation (SHA-256 ↔ 20-digit + enum normalization)
├─ Transform py_* columns (Phase A: 21 columns populated)
├─ Add Run Metadata Collection (6 integration columns)
└─ Deliverable: 27 py_* columns populated for 574 files

WEEK 2: FOUNDATION + ENTITY CANONICALIZATION (5-7 days)
├─ Track A: Column Runtime Engine (7 components, Days 1-5)
├─ Track B: Entity Canonicalization ONLY (Days 1-2)
│   └─ Declare files[] authoritative, move entities[]/entries[] to LEGACY_OVERLAYS.json
│   └─ Create REGISTRY_ENTITIES.json + schema.entities.v4.json
├─ Resolve 51 Inconsistencies (Types A-D, Days 3-5)
└─ Deliverable: 0 governance violations, canonical entity registry, unified runtime

WEEK 3: INTEGRATION + PIPELINE COMPLETION (5-7 days)
├─ File Intake Orchestrator (entity-only S1-S6)
├─ Implement Phase B in Pipeline (6 columns: tests, lint, complexity, quality)
├─ Implement Phase C in Pipeline (4 columns: similarity, overlap, canonical ranking)
├─ Fix file_id resolver in pipeline (from polymorphic Step 4)
├─ Simplified Convergent Report (5 entity signals)
├─ Timestamp Clustering + Provenance (entity-level)
└─ Deliverable: ALL 37 py_* columns operational, full entity automation
```

### Timeline vs. V2

| Phase | V2 | V3 Merged | Delta |
|-------|----|----|-------|
| Phase 0 | 2 days | 3 days | +1 (pipeline fixes added) |
| Week 1 | 5-7 days | 5-7 days | 0 |
| Week 2 | 7-10 days | 5-7 days | -2 to -3 (entities only) |
| Week 3 | 7-10 days | 5-7 days | -2 to -3 (no bundles) + Phase B/C added |
| **Total** | **21-29 days** | **18-24 days** | **-3 to -5** |

### Script Count

- V2: 23 new scripts → V3 Merged: 17 new scripts + 13 modified scripts
- Net: fewer new scripts, more fixes to existing code

---

## PHASE 0: Pre-Flight Stabilization (3 days)

### Goal: Eliminate enum drift + fix all script output issues + finish stubbed analyzers

---

### Day 0.1: Enum Canon + Drift Gate

*(Unchanged from V2)*

**Objective:** Create canonical enums and eliminate drift violations

**Problem Statement:**
- `repo_root_id` data: `GOV_REG_WORKSPACE` (1829), `01` (85)
- `repo_root_id` schema v3: only allows `AI_PROD_PIPELINE`, `ALL_AI`
- `canonicality` data: includes `SUPERSEDED`
- `canonicality` schema v3: only allows `CANONICAL|LEGACY|ALTERNATE|EXPERIMENTAL`

**Implementation:** `P_01999000042260305000_enum_drift_gate.py`
- Build canonical enum definitions with legacy aliases
- Validate drift across registry data and contracts
- Generate RFC-6902 normalization patches
- Apply normalization after backup

**Validation:**
```powershell
python P_01999000042260305000_enum_drift_gate.py
# Expected: ✅ No enum drift detected - GATE PASSED (after normalization)
```

---

### Day 0.2: Finish 7 Stubbed Analyzers

*(Unchanged from V2)*

**Objective:** Complete 7 stubbed scripts for Phase A pipeline (~2,173 lines)

Scripts: component_extractor, component_id_generator, dependency_analyzer, io_surface_analyzer, structural_feature_extractor, extract_semantic_features, file_comparator

> **Note:** Use canonical resolver names only. `structural_feature_extractor.py` resolves to `P_...0066`, `extract_semantic_features.py` resolves to `P_...0067` (also mapped as `semantic_similarity.py`). `component_id_generator` requires special invocation — see Day 0.4 note.

**Validation:**
```powershell
# Validate Phase A on a known repo file using the pipeline (not consolidated_runner.py):
python P_01260202173939000084_registry_integration_pipeline.py --file 01260207201000001250_REGISTRY\01260207201000001313_capability_mapping_system\01260207220000001318_mapp_py\P_01260202173939000060_text_normalizer.py --registry 01260207201000001250_REGISTRY\01999000042260124503_REGISTRY_file.json --phase A --dry-run --output test_phase_a.json
# Expected: Phase A complete: 21 columns populated per file
# Note: consolidated_runner.py is a separate whole-repo inventory tool (accepts repo_root + --output-dir), NOT the per-file pipeline.
```

---

### Day 0.3: Fix Column-Name Mismatches in 4 Scripts

*(From polymorphic Step 0 — these are CRITICAL for Week 1 to produce correct output)*

**0.3a.** `P_01260202173939000060_text_normalizer.py`
- Lines 161, 170, 179: Rename `py_text_normalized_hash` → `py_canonical_text_hash`

**0.3b.** `P_01260202173939000061_component_extractor.py`
- Line 200: `py_classes_count` → `py_defs_classes_count`
- Line 201: `py_functions_count` → `py_defs_functions_count`
- Line 202: `py_methods_count` → `py_component_count` (compute as `len(classes) + len(functions) + len(methods)`)
- Line 204: `py_components_hash` → `py_defs_public_api_hash`
- Same renames in error return (lines 211-215)

**0.3c.** `P_01260202173939000071_complexity_visitor.py`
- Lines 161, 176, 187: Rename `py_cyclomatic_complexity` → `py_complexity_cyclomatic`

**0.3d.** `P_01260202173939000069_analyze_tests.py`
- Add `py_tests_executed: True` (boolean) to return dict
- Add `py_pytest_exit_code: result["returncode"]` to return dict
- Line 151: Rename `py_test_coverage_pct` → `py_coverage_percent`

---

### Day 0.4: Add `--json <output_file>` Flag to 11 Scripts (10 standard + component_id_generator)

*(From polymorphic Step 3 — required for pipeline invocation)*

The pipeline invokes scripts with `[python, script.py, file_path, '--json', output_file]` but most scripts don't support this flag.

**Scripts to modify:**
1. `P_01260202173939000060_text_normalizer.py`
2. `P_01260202173939000061_component_extractor.py`
3. `P_01260202173939000062_generate_component_signature.py` (component_id_generator)
4. `P_01260202173939000063_dependency_analyzer.py`
5. `P_01260202173939000064_i_o_surface_visitor.py`
6. `P_01260202173939000065_deliverable_analyzer.py`
7. `P_01260202173939000076_capability_detector.py`
8. `P_01260202173939000079_analyze_file.py`
9. `P_01260202173939000069_analyze_tests.py`
10. `P_01260202173939000070_run_pylint_on_file.py`
11. `P_01260202173939000071_complexity_visitor.py`

**Pattern for each:** In `main()`, after computing `result`:
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

> **Special case — `component_id_generator.py`:** This script does NOT use the standard `--json` pattern. Its interface is `<file_id> <components_json>`. The pipeline must:
> 1. Write component_extractor output to a temp JSON file
> 2. Invoke: `python component_id_generator.py <file_id> <temp_components.json> --json <output_file>`
> 3. Add `--json` support to this script's `main()` (same pattern as above, but after the existing `file_id`/`components_json` positional args)

---

### Day 0.5: Fix capability_detector Hash + quality_scorer Breakdown

*(From polymorphic Steps 1-2)*

**0.5a. capability_detector.py** — Add missing `py_capability_facts_hash`:
- Add `import hashlib`
- In `tag_file_capabilities()`, compute SHA-256 of sorted capability tags
- Add `"py_capability_facts_hash": facts_hash` to return dict

**0.5b. quality_scorer.py** — Complete `generate_breakdown()`:
- Replace line 149 (`# Continue for other components...`) with 3 missing breakdown components:
  - Docstrings (mirror logic from `calculate_score()` lines 66-78)
  - Lint (mirror logic from lines 82-98)
  - Complexity (mirror logic from lines 101-117)

---

### Phase 0 Deliverables

- Enum Canon established (`REGISTRY_ENUMS_CANON.json`)
- 0 enum drift violations (all legacy values normalized)
- 7 stubbed analyzers complete (~2,173 lines implemented)
- 4 column-name mismatches fixed (scripts output correct registry keys)
- 11 scripts support `--json` flag (10 standard + component_id_generator)
- capability_detector produces hash; quality_scorer produces full breakdown
- Phase A pipeline operational (21 columns per file via static analysis)

---

## WEEK 1: Tactical Wins (5-7 days)

### Goal: Populate 27 `py_*` columns (21 Phase A + 6 integration metadata)

*(Unchanged from V2 except column count revised upward because Phase 0 fixes more scripts)*

---

### Day 1-2: Execute Capability Mapping Step 3

**Objective:** Generate `FILE_PURPOSE_REGISTRY.json`

```powershell
python 01260207201000001250_REGISTRY\01260207201000001313_capability_mapping_system\P_01260207220000001315_capability_mapper.py --step 3 --repo-root .
```

**Validation:**
- Output exists: `.state/purpose_mapping/FILE_PURPOSE_REGISTRY.json`
- ≥500 files mapped

---

### Day 3: Build File ID Reconciliation Layer

**Objective:** Create SHA-256 ↔ 20-digit file_id lookup WITH enum normalization

**Implementation:** `P_01999000042260305001_file_id_reconciler.py`
- Builds `sha256 → file_id` and `file_id → sha256` mappings from registry
- Captures normalized enum values per file_id
- Validates all file_ids are 20-digit, all SHA-256 are 64-hex

**Critical:** Component ID generation MUST use `file_id` (not `doc_id`)

---

### Day 4: Build Transformation Layer for Phase A Columns

**Objective:** Convert Phase A analyzer outputs to registry format

**Implementation:** `P_01999000042260305002_py_column_transformer.py`
- Transforms `FILE_INVENTORY.jsonl` facts → registry `py_*` columns
- Handles DIRECT, RENAME, and PARTIAL column mappings
- Covers 21 Phase A columns (up from V2's 11 because Phase 0 fixed naming)

---

### Day 5: Add Run Metadata Collection

**Objective:** Populate 6 orchestration fields
- `py_analysis_run_id`, `py_analyzed_at_utc`, `py_analysis_success`
- `py_toolchain_id`, `py_tool_versions`, `py_component_artifact_path`

**Implementation:** Enhanced `registry_promoter.py` with `_collect_run_metadata()`

---

### Day 6-7: Generate and Apply Comprehensive Patches

**Objective:** Combine all outputs into unified RFC-6902 promotion

**Implementation:** Enhanced `registry_promoter.py` with `promote_unified()`
- Loads capability mapping + transformed py columns + reconciliation map
- Generates ~1500 patch operations
- Backs up registry before applying
- Dry-run → validate → apply

---

### Week 1 Deliverables

- **27 py_* columns populated** (21 Phase A + 6 integration metadata)
  - Phase A: text hash, AST, components, imports, I/O flags, deliverables, capabilities
  - Integration: run_id, timestamps, toolchain, success flag
- 574 Python files tagged with capability purposes
- Evidence bundles complete (SHA-256 audit trail)
- File ID reconciliation operational

---

## WEEK 2: Foundation + Entity Canonicalization (5-7 days)

### Goal: Build column runtime engine + canonicalize entities + resolve 51 inconsistencies

**Parallel Tracks:**
- **Track A:** Column Runtime Engine (Days 1-5)
- **Track B:** Entity Canonicalization ONLY (Days 1-2)
- **Integration:** Resolve 51 inconsistencies (Days 3-5)

---

### TRACK A: Column Runtime Engine (Days 1-5)

*(Unchanged from V2)*

#### Day A.1-A.2: Column Runtime Schema Loader
**Implementation:** `P_01999000042260305010_column_runtime_loader.py`
- Load and merge 4 governance sources
- Validate policies (detect 51 inconsistencies)
- Export unified column metadata

#### Day A.3: Dependency Scheduler + Trigger Dispatcher
**Implementation:**
- `P_01999000042260305011_dependency_scheduler.py`
- `P_01999000042260305012_trigger_dispatcher.py`

#### Day A.4-A.5: Derivation Executor + Core Components
**Implementation:**
- `P_01999000042260305013_derivation_executor.py`
- `P_01999000042260305014_lookup_resolver.py`
- `P_01999000042260305015_patch_generator.py`
- `P_01999000042260305016_evidence_writer.py`

---

### TRACK B: Entity Canonicalization ONLY (Days 1-2)

*(Narrowed from V2 per breezy — entity-only, NOT full registry split)*

#### Day B.1: Canonical Entity Set

**Objective:** Stop having 3 parallel entity arrays

**Current Problem:**
- `files[]`: 2013 records (canonical-ish)
- `entities[]`: 723 stubs (schema-unvalidated)
- `entries[]`: 245 legacy overlay (schema-unvalidated)

**Implementation:** `P_01999000042260305025_canonicalize_entity_set.py`
- Declare `files[]` as authoritative
- Move `entities[]` and `entries[]` to `LEGACY_OVERLAYS.json` (non-authoritative)
- Create `REGISTRY_ENTITIES.json` with v4 schema metadata

#### Day B.2: Entity Schema v4

**Implementation:** `schema.entities.v4.json`
- Expanded enums: `repo_root_id` includes `GOV_REG_WORKSPACE`, `canonicality` includes all 4 values
- Entity-only schema (no edge or generator fields)

**NOT created (deferred):**
- `REGISTRY_EDGES.json`
- `REGISTRY_GENERATORS.json`
- `REGISTRY_BUNDLE_MANIFEST.json`
- `schema.edges.v4.json`, `schema.generators.v4.json`, `schema.bundle_manifest.v4.json`

---

### Days 3-5: Resolve 51 Inconsistencies

*(Unchanged from V2)*

**Type A:** Reclassify 18 editorial columns → `manual_patch_only`
- description, one_line_purpose, short_description, notes, function_code_1/2/3, deliverables, inputs, outputs, tags, step_refs, superseded_by, validation_rules, bundle_key, bundle_role, bundle_version, resolver_hint

**Type B:** Add 14 safe default formulas + expand schema enums
- status → default `'active'`
- entity_kind → infer from artifact_kind
- canonicality → default `'CANONICAL'`

**Type C:** Document 9 on-create immutable fields
- created_by, record_kind, source_file_id, target_file_id, source_entity_id, target_entity_id, directionality, rel_type, edge_type

**Type D:** Implement 10 lookup formulas
- `P_01999000042260305014_lookup_resolver.py`: asset_id, asset_family, asset_version, external_ref, external_system, etc.

**Validation:**
```powershell
python P_01999000042260305010_column_runtime_loader.py --validate-only
# Expected: ✅ 0 inconsistencies found
```

---

### Week 2 Deliverables

- Column Runtime Engine operational (7 components)
- 0 inconsistencies (all 51 resolved)
- 185 columns governed by unified policies
- `REGISTRY_ENTITIES.json` created (canonical, v4 schema)
- `LEGACY_OVERLAYS.json` created (non-authoritative historical reference)
- Dependency scheduler produces valid topological order
- Derivation executor tested with sample formulas

---

## WEEK 3: Integration + Pipeline Completion (5-7 days)

### Goal: Complete all 37 py_* columns + deploy entity-level automation

---

### Day 1: Fix file_id Resolver in Pipeline

*(From polymorphic Step 4)*

**File:** `P_01260202173939000084_registry_integration_pipeline.py`

- Add `_build_file_id_lookup()` method: reads registry JSON, builds `relative_path → file_id` and `absolute_path → file_id` dicts
- Called in `__init__()`, stored as `self.file_id_lookup`
- In `analyze_file()`: resolve file_id by exact path match, then normalized path match
- Fix Phase A script list: add missing `analyze_file.py`

---

### Day 2: Implement Phase B in Pipeline

*(From polymorphic Steps 5-5c)*

**File:** `P_01260202173939000084_registry_integration_pipeline.py`

- Replace Phase B no-op `pass` (lines 165-173) with actual script execution
- 60-second timeout (tests take longer than Phase A)
- Quality scorer runs LAST (needs other Phase B outputs)
- Add `_build_script_args()` helper for script-specific CLI patterns

**Phase B scripts:**
```python
phase_b_scripts = [
    'test_runner.py',        # → py_tests_executed, py_pytest_exit_code, py_coverage_percent
    'linter_runner.py',      # → py_static_issues_count
    'complexity_analyzer.py', # → py_complexity_cyclomatic
    'quality_scorer.py',     # → py_quality_score (MUST be last, SPECIAL INVOCATION)
]
```

> **quality_scorer.py invocation:** This script does NOT use `--json`. It requires:
> ```
> python quality_scorer.py --metrics-json <input.json> --output <output.json>
> ```
> The pipeline must:
> 1. After running test_runner, linter_runner, and complexity_analyzer, collect all accumulated py_* results (Phase A + Phase B so far) into a single metrics JSON
> 2. Write that JSON to a temp file (e.g., `tmp/<file_id>_metrics.json`)
> 3. Invoke quality_scorer with `--metrics-json <temp_metrics> --output <output>`
> 4. `_build_script_args()` must detect `quality_scorer.py` and return `['--metrics-json', metrics_path, '--output', output_path]` instead of the standard `[file_path, '--json', output_path]`

**Columns produced:** 6 (py_tests_executed, py_pytest_exit_code, py_coverage_percent, py_static_issues_count, py_complexity_cyclomatic, py_quality_score)

---

### Day 3: Implement Phase C in Pipeline

*(From polymorphic Step 6)*

**File:** `P_01260202173939000084_registry_integration_pipeline.py`

Phase C has two stages: **batch operations** (steps 1-4, all files at once) and **per-cluster pairwise comparison** (steps 5-9, only within overlap groups).

- Add `run_phase_c(all_results)` method:

  **Stage 1 — Batch (all files):**
  1. Merge all per-file results with existing registry data into `{"files": [...]}` format
  2. Write to `tmp/batch_registry.json`
  3. Run `similarity_clusterer.py --registry-json tmp/batch_registry.json --output tmp/clusters.json` → `py_overlap_group_id`
  4. Run `canonical_ranker.py --registry-json tmp/batch_registry.json --clusters-json tmp/clusters.json --output tmp/rankings.json` → `py_canonical_candidate_score`

  **Stage 2 - Per-cluster pairwise comparison (steps 5-9, only multi-file clusters):**
  5. Read `tmp/clusters.json`, identify multi-file clusters (group_id with 2+ files)
  6. For each file in a multi-file cluster, run structural + semantic extractors against cluster peers only:
     ```
     python structural_feature_extractor.py <target_file> <peer1> <peer2> ...
     python extract_semantic_features.py <target_file> <peer1> <peer2> ...
     ```
     Both scripts accept `<target_file> <candidate1> [candidate2 ...]` and print human-readable lines plus a JSON scores object.
     Pipeline must capture stdout, extract the JSON object from the "All scores:" block, and write clean JSON to the score files.
  7. Run `file_comparator.py <target_file> tmp/<file_id>_structural.json tmp/<file_id>_semantic.json` per file → `py_overlap_similarity_max`, `py_overlap_best_match_file_path`
  8. Map `py_overlap_best_match_file_path` → `py_overlap_best_match_file_id` using `self.file_id_lookup` (from Day 1 Step 4)
  9. Merge batch + pairwise results back into per-file dicts

> **Input format:** similarity_clusterer and canonical_ranker both expect `registry.get('files', [])` — the batch JSON MUST use `{"files": [...]}` (not `{"entities": [...]}`), consistent with the canonical array decision.
>
> **Candidate selection:** Pairwise comparison (steps 6-7) runs ONLY within multi-file overlap groups from step 3, not against all files. This bounds the comparison set and avoids O(n^2) explosion.
>
> **Score file capture:** `structural_feature_extractor.py` and `extract_semantic_features.py` print human text plus a JSON scores dict to stdout. The pipeline must capture stdout via `subprocess.run(..., capture_output=True)`, parse out the JSON scores object, and write clean JSON to `tmp/<file_id>_structural.json` / `tmp/<file_id>_semantic.json`. `file_comparator.py` then reads these JSON files via `load_similarity_scores()`.
>
> **Output key:** `file_comparator.py` emits `py_overlap_best_match_file_path` (a path string). The pipeline maps this to `py_overlap_best_match_file_id` using `self.file_id_lookup` before writing to the registry.

**Columns produced:** 4 (py_overlap_group_id, py_overlap_similarity_max, py_overlap_best_match_file_id, py_canonical_candidate_score)

---

### Day 4: File Intake Orchestrator (Entity-Only)

*(From V2 Week 3, modified per breezy — writes to REGISTRY_ENTITIES.json only)*

**Implementation:** `P_01999000042260305020_file_intake_orchestrator.py`

```python
class FileIntakeOrchestrator:
    def __init__(self, runtime_engine, registry_index, allocator):
        self.engine = runtime_engine  # Uses Week 2 runtime
        self.capability_registry = self._load_capability_registry()  # Uses Week 1 output
        # Writes to REGISTRY_ENTITIES.json ONLY (no edge/generator registries)
```

**Test:**
```powershell
python P_01999000042260305020_file_intake_orchestrator.py --file "test1.py" --event-type "file_create"
```

---

### Day 5: Capability Mapping Migration + Timestamp Clustering

- Migrate Week 1 promotion to use runtime engine (no bundle-commit wrapper)
- Generate timestamp clusters: `.state/purpose_mapping/TIMESTAMP_CLUSTERS.json`
- Link provenance (if AI CLI logs exist)

---

### Day 6: Simplified Convergent Report (5 Entity Signals)

*(Modified from V2 per breezy — 5 signals instead of 7, removes edge-dependent signals)*

```python
def compute_convergence_score(record):
    signals = {
        "fs_primitives": record.get("sha256") is not None,          # +1
        "artifact_kind_inferred": record.get("artifact_kind") is not None,  # +1
        "py_analysis_complete": record.get("py_analysis_success") == True,  # +2
        "capability_tagged": len(record.get("py_capability_tags", [])) > 0, # +2
        "temporal_clustered": record.get("temporal_cluster_id") is not None, # +1
    }
    score = sum(signals.values())
    if score >= 5: return "HIGH"
    elif score >= 3: return "MEDIUM"
    else: return "LOW"
```

**Removed signals (edge-dependent, deferred):**
- ~~provenance_linked~~ → needs edge registry
- ~~runtime_validated~~ → needs bundle-commit

**Revised bands:** HIGH ≥5, MEDIUM 3-4, LOW <3

---

### Day 7: End-to-End Validation + Documentation

**Validation Tests:**
```powershell
# Test 1: Full intake pipeline (entity-only)
python P_01999000042260305020_file_intake_orchestrator.py --file "new_test_file.py"

# Test 2: Runtime consistency
python P_01999000042260305010_column_runtime_loader.py --validate-only

# Test 3: All 37 py_* columns present
python -c "
import json
r = json.load(open('01260207201000001250_REGISTRY/canonical_v4/REGISTRY_ENTITIES.json'))
sample = r['files'][0]
py_cols = [k for k in sample.keys() if k.startswith('py_')]
print(f'py_* columns found: {len(py_cols)} of 37')
"

# Test 4: Phase B pipeline
python P_01260202173939000084_registry_integration_pipeline.py --file 01260207201000001250_REGISTRY\01260207201000001313_capability_mapping_system\01260207220000001318_mapp_py\P_01260202173939000060_text_normalizer.py --registry 01260207201000001250_REGISTRY\01999000042260124503_REGISTRY_file.json --phase B --dry-run

# Test 5: Phase C batch
python P_01260202173939000084_registry_integration_pipeline.py --batch --registry 01260207201000001250_REGISTRY\01999000042260124503_REGISTRY_file.json --phase C --dry-run

# Test 6: file_id resolution
# Verify results['file_id'] is 20-digit numeric for every analyzed file

# Test 7: Hash determinism
# Run same file twice, verify all *_hash columns produce identical values
```

---

### Week 3 Deliverables

- File Intake Orchestrator operational (entity-only S1-S6)
- **ALL 37 py_* columns operational** (Phase A: 21, Phase B: 6, Phase C: 4, Integration: 6)
- Pipeline file_id resolver working end-to-end
- Simplified convergent report (5 entity signals)
- Timestamp clustering + provenance linking (entity-level)
- Documentation updated

---

## Complete Column Coverage (37 py_* Columns)

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

## Script Inventory

### New Scripts (17)

| Script | Phase | Purpose |
|--------|-------|---------|
| `P_01999000042260305000_enum_drift_gate.py` | Phase 0 | Enum canonization + drift detection |
| `P_01999000042260305001_file_id_reconciler.py` | Week 1 | SHA-256 ↔ file_id lookup |
| `P_01999000042260305002_py_column_transformer.py` | Week 1 | Transform analyzer output → registry columns |
| `P_01999000042260305003_timestamp_cluster_analyzer.py` | Week 3 | Timestamp clustering + convergent report |
| `P_01999000042260305010_column_runtime_loader.py` | Week 2 | Load/validate 4 governance sources |
| `P_01999000042260305011_dependency_scheduler.py` | Week 2 | Topological sort of column dependencies |
| `P_01999000042260305012_trigger_dispatcher.py` | Week 2 | Event-driven derivation triggers |
| `P_01999000042260305013_derivation_executor.py` | Week 2 | Execute column derivation formulas |
| `P_01999000042260305014_lookup_resolver.py` | Week 2 | Cross-registry field lookups |
| `P_01999000042260305015_patch_generator.py` | Week 2 | RFC-6902 patch generation |
| `P_01999000042260305016_evidence_writer.py` | Week 2 | SHA-256 evidence trail writer |
| `P_01999000042260305020_file_intake_orchestrator.py` | Week 3 | Entity-only S1-S6 pipeline |
| `P_01999000042260305025_canonicalize_entity_set.py` | Week 2 | Declare files[] authoritative |

### New Artifacts (non-script)

| Artifact | Phase | Purpose |
|----------|-------|---------|
| `schema.entities.v4.json` | Week 2 | Entity schema v4 (JSON Schema, not a script) |

### Stubbed Analyzers to Complete (Phase 0)

3 of the 7 stubbed analyzers are new-only (not also in the modified list):

| Analyzer | Resolves To |
|----------|-------------|
| `dependency_analyzer.py` | `P_01260202173939000063_dependency_analyzer.py` |
| `structural_feature_extractor.py` | `P_01260202173939000066_structural_feature_extractor.py` |
| `file_comparator.py` | `P_01260202173939000068_file_comparator.py` |

The other 4 stubbed analyzers (component_extractor, component_id_generator, io_surface_analyzer, extract_semantic_features) also appear in the Modified Scripts table because they need both stub completion AND column renames/--json flags.

### Modified Scripts (13)

| Script | Phase | Changes |
|--------|-------|---------|
| `P_01260202173939000060_text_normalizer.py` | Phase 0 | Column rename + --json flag |
| `P_01260202173939000061_component_extractor.py` | Phase 0 | Column renames (4) + --json flag |
| `P_01260202173939000062_generate_component_signature.py` | Phase 0 | Add --json support (component_id_generator) |
| `P_01260202173939000063_dependency_analyzer.py` | Phase 0 | --json flag |
| `P_01260202173939000064_i_o_surface_visitor.py` | Phase 0 | --json flag |
| `P_01260202173939000065_deliverable_analyzer.py` | Phase 0 | --json flag |
| `P_01260202173939000069_analyze_tests.py` | Phase 0 | Column rename + add fields + --json |
| `P_01260202173939000070_run_pylint_on_file.py` | Phase 0 | --json flag |
| `P_01260202173939000071_complexity_visitor.py` | Phase 0 | Column rename + --json flag |
| `P_01260202173939000076_capability_detector.py` | Phase 0 | Add hash computation + --json |
| `P_01260202173939000079_analyze_file.py` | Phase 0 | --json flag |
| `P_01260202173939000085_quality_scorer.py` | Phase 0 | Complete generate_breakdown() |
| `P_01260202173939000084_registry_integration_pipeline.py` | Week 3 | file_id resolver + Phase B + Phase C |

---

## Success Criteria

### Three Problems Solved

- [ ] **37 py_* columns:** ALL 37 populated end-to-end (not 15-17)
- [ ] **51 inconsistencies:** All resolved (0 violations, includes schema enum expansion)
- [ ] **File intake automation:** Entity-only S1-S6 pipeline operational

### Entity Canonicalization (Partial Problem 4)

- [ ] `REGISTRY_ENTITIES.json` created as canonical entity store (v4 schema)
- [ ] `LEGACY_OVERLAYS.json` archives non-authoritative entity arrays
- [ ] Edge/Generator/Bundle registries — DEFERRED

### Quality Gates

- [ ] Enum canon established, 0 drift violations
- [ ] All 13 modified scripts produce correct output keys
- [ ] All 11 scripts support `--json` flag
- [ ] Schema validation: 0 inconsistencies
- [ ] Dependency graph: Acyclic
- [ ] Evidence trails: SHA-256 complete
- [ ] Registry backup: Exists before all writes
- [ ] End-to-end test: 3 files ingested via entity pipeline
- [ ] Phase B: 6 columns populated for test files
- [ ] Phase C: 4 columns populated for test batch
- [ ] file_id resolver: 20-digit numeric for every analyzed file
- [ ] Hash determinism: identical hashes for identical inputs
- [ ] Convergent report: 5-signal scoring operational
- [ ] Scope check: no edge/generator/bundle deliverables or pipeline work in Phase 0-Week 3; mentions are context-only (provenance/timeline/risk/deferred or schema field names)

---

## Risk & Mitigation

| Risk | Phase | Mitigation |
|------|-------|------------|
| Enum drift blocks Week 1 | Phase 0 | Enum canon + drift gate FIRST |
| Column-name mismatches cause silent data loss | Phase 0 | Fix all 4 scripts before any pipeline run |
| --json flag missing breaks pipeline invocation | Phase 0 | Add to all 11 scripts in Phase 0 |
| Stubbed analyzers incomplete | Phase 0 | Complete before Week 1 starts |
| Step 3 fails | Week 1 | Fallback: manual mapping |
| File ID mismatch | Week 1 | Reconciler + pipeline-embedded resolver |
| Circular dependencies | Week 2 | Scheduler detects |
| Registry corruption | All | Mandatory backups before writes |
| Phase B external tools missing (pytest/ruff) | Week 3 | Graceful fallback: mark columns as NULL |
| Phase C batch performance | Week 3 | Batch mode with configurable batch_size |
| Entity canonicalization data loss | Week 2 | Legacy arrays preserved in LEGACY_OVERLAYS.json |
| Scope creep into edges/generators | All | Explicit deferral; scope-check verification in success criteria |
| Convergent report accuracy (5 signals) | Week 3 | Simpler is safer; add signals when edge registry exists |

---

## Future Work (Explicitly Deferred)

All items below require entity canonicalization (this plan) to be complete first.

| Item | Prerequisites | Recommended Order |
|------|--------------|-------------------|
| `REGISTRY_EDGES.json` | Entity registry stable | 1st |
| Edge Discovery Pipeline | Entity registry + edge schema | 2nd |
| `REGISTRY_GENERATORS.json` | Entity registry stable | 3rd |
| Inverted Path Index | Edge pipeline operational | 4th |
| Convergent Evidence Scorer (edge-weighted) | Edge registry populated | 5th |
| Bundle Manifest | All 3 registries operational | 6th |
| Bundle-Commit Protocol | Bundle manifest + all registries | 7th |
| Anti-Duplication Rules | Edge pipeline | With edges |

**Sequence:** Entities (THIS PLAN) → Edges → Generators → Bundle → Convergent Scoring

---

## Implementation Order (Dependency Chain)

```
Phase 0 (parallel where possible):
  0.1 Enum canon ──────────────────────────────────────┐
  0.2 Stubbed analyzers ──────────────────────────────┐│
  0.3 Column-name fixes ─────────────────────────────┐││
  0.4 --json flags ──────────────────────────────────┐│││
  0.5 Hash + breakdown fixes ───────────────────────┐││││
                                                    │││││
Week 1 (sequential):                                ▼▼▼▼▼
  1.1 Capability Mapping Step 3 ──────────────────────┐
  1.2 File ID Reconciler ─────────────────────────────┤
  1.3 Transformation Layer ───────────────────────────┤
  1.4 Run Metadata ───────────────────────────────────┤
  1.5 Unified Promotion ──────────────────────────────┘ → 27 py_* columns
                                                        │
Week 2 (parallel tracks):                              ▼
  Track A: Runtime Engine (7 components) ─────────────┐
  Track B: Entity Canonicalization ───────────────────┤
  Inconsistency Resolution ───────────────────────────┘ → 0 violations
                                                        │
Week 3 (sequential):                                   ▼
  3.1 file_id resolver in pipeline ───────────────────┐
  3.2 Phase B implementation ─────────────────────────┤
  3.3 Phase C implementation ─────────────────────────┤
  3.4 File Intake Orchestrator ───────────────────────┤
  3.5 Convergent Report ──────────────────────────────┤
  3.6 Validation + Documentation ─────────────────────┘ → ALL 37 py_* columns
```

---

## Timeline Summary

| Phase | Focus | Key Deliverables | Effort |
|-------|-------|------------------|--------|
| **0** | **Pre-Flight** | Enum canon + script fixes + stubbed analyzers | **3 days** |
| **1** | **Tactical Wins** | 27 py_* columns populated | **5-7 days** |
| **2** | **Foundation + Entity** | Runtime + entity canonicalization + 0 inconsistencies | **5-7 days** |
| **3** | **Integration** | Phase B/C + entity intake + convergent report | **5-7 days** |
| **Total** | **Entity-Scoped Solution** | **All 37 py_* + 3 problems solved + entity canonical** | **18-24 days** |

**Key Milestones:**
- Day 3: Phase 0 complete (clean baseline, all scripts fixed)
- Day 10: Week 1 complete (27 py_* columns populated)
- Day 17: Week 2 complete (entity registry + runtime operational)
- Day 24: Week 3 complete (all 37 py_* columns + entity automation)

---

**Plan Status:** ACTIVE
**Supersedes:** PLAN-20260305-UNIFIED-V2, breezy-tickling-rose.md, polymorphic-cuddling-kurzweil.md
**Archived Superseded Files:** `archive/superseded_plans/`
**Architecture Reference:** `docs/ARCHITECTURE_RUNTIME_ENGINE.md`
**Machine-Readable Tasks:** `UNIFIED_SOLUTION_PLAN_V3_REMAINING_STEPS.json`
**Start Date:** TBD
**Expected Completion:** ~24 days from start (4 weeks max)
