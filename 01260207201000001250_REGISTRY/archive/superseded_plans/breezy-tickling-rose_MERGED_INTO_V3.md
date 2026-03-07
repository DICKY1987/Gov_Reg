# Plan: Rewrite UNIFIED_SOLUTION_PLAN.md (V2 → V3, Entity-Scoped)

## Context

The current UNIFIED_SOLUTION_PLAN.md (V2) tries to solve four problems at once: py_* column population, 51 inconsistencies, file intake automation, AND a full registry split into Entities/Edges/Generators with bundle-commit protocol. This is overloaded.

**User decision:** The registry should split, but this plan should only deal with real files/entities. Edges, generators, bundle manifests, and convergent evidence scoring are deferred to a future plan.

**Target file:** `C:\Users\richg\Gov_Reg\UNIFIED_SOLUTION_PLAN.md` (full rewrite, 2432 lines → ~1400 lines)

---

## What Changes (V2 → V3)

### Kept As-Is
- **Phase 0** (2 days): Enum canon + 7 stubbed analyzers
- **Week 1** (5-7 days): Capability mapping Steps 3-4, file ID reconciliation, py_* column transforms
- **Week 2 Track A** (5 days): Column Runtime Engine (7 components)
- **51 Inconsistency Resolution**: Types A-D unchanged

### Narrowed
- **Week 2 Track B**: Entity canonicalization ONLY (1-2 days, was 5 days)
  - KEEP: `P_01999000042260305025_canonicalize_entity_set.py` — declare `files[]` authoritative, move `entities[]`/`entries[]` to `LEGACY_OVERLAYS.json`, create `REGISTRY_ENTITIES.json`
  - KEEP: `schema.entities.v4.json`
  - CUT: `REGISTRY_EDGES.json`, `REGISTRY_GENERATORS.json`, `REGISTRY_BUNDLE_MANIFEST.json`
  - CUT: `P_01999000042260305026_split_registries.py`, `P_01999000042260305028_edge_discovery.py`
  - CUT: `schema.edges.v4.json`, `schema.generators.v4.json`, `schema.bundle_manifest.v4.json`

- **Week 3** (5-7 days, was 7-10 days)
  - KEEP: File Intake Orchestrator (entity-only writes to `REGISTRY_ENTITIES.json`)
  - KEEP: Capability mapping migration to runtime engine
  - KEEP: Timestamp clustering / provenance (entity-level)
  - MODIFY: Convergent report uses 5 entity signals (not 7), removes edge-dependent signals
  - CUT: Edge generation pipeline, scored edges, bundle-commit protocol, inverted path index, anti-duplication rules

### Removed Entirely
- `P_01999000042260305004_inverted_path_index.py` — edge dependency
- `P_01999000042260305005_convergent_evidence_scorer.py` — edge dependency
- `P_01999000042260305026_split_registries.py` — no edge/gen split
- `P_01999000042260305028_edge_discovery.py` — no edge pipeline
- Bundle-commit protocol code
- Anti-duplication rules

### Timeline Impact
| Phase | V2 | V3 | Delta |
|-------|----|----|-------|
| Phase 0 | 2 days | 2 days | 0 |
| Week 1 | 5-7 days | 5-7 days | 0 |
| Week 2 | 7-10 days | 5-7 days | -2 to -3 |
| Week 3 | 7-10 days | 5-7 days | -2 to -3 |
| **Total** | **21-29 days** | **17-23 days** | **-4 to -6** |

### Script Count
- V2: 23 new scripts → V3: 17 new scripts (-6 deferred)

---

## Implementation Steps

### Step 1: Rewrite Header + Executive Summary
- Change Plan ID to `PLAN-20260305-UNIFIED-V3`
- Scope statement: "ENTITIES ONLY (edges, generators, bundles deferred)"
- Three problems solved (not four): py_* columns, 51 inconsistencies, entity intake
- Problem 4 partially addressed: entity canonicalization only

### Step 2: Rewrite Phase Structure Diagram
- Remove edge/generator/bundle-manifest from Week 2 Track B
- Remove edge generation, scored edges, bundle-commit, inverted path index, anti-dup from Week 3
- Update Week 2 label: "FOUNDATION + ENTITY CANONICALIZATION"
- Update Week 3 label: "INTEGRATION + ENTITY-LEVEL EVIDENCE"
- Update durations: Week 2 → 5-7 days, Week 3 → 5-7 days

### Step 3: Keep Phase 0 + Week 1 Sections Intact
- Copy Phase 0 (lines 99-400) verbatim — enum canon + stubbed analyzers
- Copy Week 1 (lines 404-913) verbatim — capability mapping + py_* columns

### Step 4: Rewrite Week 2
- **Track A** (Days 1-5): Keep Column Runtime Engine section as-is (lines 930-1083)
- **Track B** (Days 1-2): Keep ONLY Day B.1 entity canonicalization (lines 1097-1191)
  - Remove Days B.2-B.5 (split registries, edge discovery, schemas v4 family)
  - Add `schema.entities.v4.json` creation (entity schema only)
- **Integration** (Days 3-5): Move inconsistency resolution earlier (was Days 6-7)
  - Keep Types A-D resolution (lines 980-1072) unchanged

### Step 5: Rewrite Week 3
- **Days 1-2**: File Intake Orchestrator — modify to write to `REGISTRY_ENTITIES.json` only
  - Remove references to edge_registry, generator_registry, bundle_manifest
- **Day 3**: Capability mapping migration — keep, remove bundle-commit wrapper
- **Days 4-5**: Timestamp clustering + provenance — keep as-is
- **Days 5-6**: Simplified convergent report — 5 signals instead of 7:
  - Keep: fs_primitives (+1), artifact_kind (+1), py_analysis (+2), capability_tagged (+2), temporal_clustered (+1)
  - Remove: provenance_linked, runtime_validated (edge-dependent)
  - Revised bands: HIGH ≥5, MEDIUM 3-4, LOW <3
- **Day 7**: End-to-end validation + documentation
- Remove: duplicate "Day 4-5" section conflict from V2

### Step 6: Rewrite Success Criteria
- Three problems (not four)
- Remove edge-related quality gates (scored edges, bundle integrity, referential integrity)
- Add entity-specific gates (REGISTRY_ENTITIES.json canonical, legacy overlays archived)

### Step 7: Update Risk Table
- Remove bundle-commit risks
- Add: entity canonicalization data loss, scope creep into edges, convergent report accuracy (5 signals)

### Step 8: Add Future Work Section
Explicitly list all deferred items with prerequisites:
- REGISTRY_EDGES.json → needs entity canonicalization complete
- REGISTRY_GENERATORS.json → needs entity canonicalization complete
- Bundle Manifest → needs edge + generator registries
- Edge Discovery Pipeline → needs entity registry stable
- Inverted Path Index → needs edge pipeline
- Convergent Evidence Scorer → needs edge registry
- Bundle-Commit Protocol → needs multiple registries
- Recommended sequence: Entities (this plan) → Edges → Generators → Bundle → Convergent Scoring

### Step 9: Update Timeline Summary + Next Steps
- 17-23 days total
- Milestones: Day 2 (Phase 0), Day 9 (Week 1), Day 16 (Week 2), Day 23 (Week 3)

---

## Key Files

| File | Action |
|------|--------|
| `UNIFIED_SOLUTION_PLAN.md` | Full rewrite (V2 → V3) |

### Reference Files (read-only during rewrite)
| File | Purpose |
|------|---------|
| `01260207201000001250_REGISTRY/01999000042260124503_REGISTRY_file.json` | Registry structure (files[]/entities[]/entries[]) |
| `01260207201000001250_REGISTRY/COLUMN_HEADERS/01260207201000000193_UNIFIED_SSOT_REGISTRY_WRITE_POLICY.yaml` | Write policy |
| `01260207201000001250_REGISTRY/COLUMN_HEADERS/PY_COLUMN_PIPELINE_MAPPING.csv` | py_* column status |
| `01260207201000001250_REGISTRY/COLUMN_HEADERS/formula_sheet_classification.csv` | Formula classifications |
| `01260207201000001250_REGISTRY/01999000042260124012_governance_registry_schema.v3.json` | Current schema |
| `CAPABILITY_MAPPING_COMPLETION_PLAN.md` | Reference for Week 1 steps |
| `COMPLETE_REGISTRY_AUTOMATION_PLAN.md` | Reference for runtime engine design |

---

## Verification

After rewriting:
1. **Scope check**: grep for "edge", "generator", "bundle" — should only appear in "Future Work" section or explicitly marked as deferred
2. **Consistency check**: All script references match the 17-script inventory (not 23)
3. **Timeline check**: Total adds up to 17-23 days
4. **No duplicate day numbering**: Week 3 should not have two "Day 4-5" sections
5. **Success criteria**: Only 3 problems listed (not 4), no edge-related quality gates
6. **Phase structure diagram**: No edge/generator/bundle references in active phases
