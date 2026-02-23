# Plan: Consolidate Capability Mapping System

## Context
The Capability Mapping System is a 4-step pipeline that auto-classifies every Python file in Gov_Reg and tags capabilities into the SSOT registry. Its files are currently scattered across at least 6 different directories. The user wants all of them in one top-level folder with a README.

---

## Target Structure

```
Gov_Reg/
  01260207201000001313_capability_mapping_system/
    README.md                         ← new
    capability_mapper.py              ← moved + sys.path patched
    src/                              ← moved from 01260207201000001289_src/01260207201000001290_capability_mapping/
      __init__.py
      argparse_extractor.py
      call_graph_builder.py
      capability_discoverer.py
      file_inventory_builder.py
      purpose_registry_builder.py
      registry_promoter.py
    mapp_py/                          ← moved from 01260207201000001250_REGISTRY/01260207201000001265_mapp_py/
      (all 30+ files)
    schemas/                          ← moved from newPhasePlanProcess/01260207201000001223_schemas/
      CAPABILITIES.schema.v1.json
      COMPONENT_CAPABILITY_VOCAB.json
    docs/                             ← collected from various locations
      CAPABILITY_MAPPING_PIPELINE_COMPLETE_REPORT.md
      CAPABILITY_MAPPING_FINAL_COMPLETION_REPORT.md
      CAPABILITY_MAPPING_IMPLEMENTATION_SUMMARY.md
      capability_mapping_status_report.md    ← from newPhasePlanProcess/
    archive/                          ← moved from REGISTRY/archive/.../capability_mapping/
      purpose_registry_builder.py     (older version)
      registry_promoter.py            (older version)
```

---

## Implementation Steps

### Step 1 — Create the folder
```bash
mkdir -p "Gov_Reg/01260207201000001313_capability_mapping_system/src"
mkdir -p "Gov_Reg/01260207201000001313_capability_mapping_system/mapp_py"
mkdir -p "Gov_Reg/01260207201000001313_capability_mapping_system/schemas"
mkdir -p "Gov_Reg/01260207201000001313_capability_mapping_system/docs"
mkdir -p "Gov_Reg/01260207201000001313_capability_mapping_system/archive"
```

### Step 2 — Move files

**Orchestrator:**
```
Gov_Reg/01260207201000001276_scripts/P_01260207201000000934_P_01260207233100000XXX_capability_mapper.py
  → 01260207201000001313_capability_mapping_system/capability_mapper.py
```

**Pipeline src modules (all 7 files + .dir_id):**
```
Gov_Reg/01260207201000001289_src/01260207201000001290_capability_mapping/*
  → 01260207201000001313_capability_mapping_system/src/
```

**mapp_py library (all 30+ files + .dir_id):**
```
Gov_Reg/01260207201000001250_REGISTRY/01260207201000001265_mapp_py/*
  → 01260207201000001313_capability_mapping_system/mapp_py/
```

**REGISTRY support scripts (3 files):**
```
01260207201000001250_REGISTRY/01260207201000001270_scripts/P_01260207201000000850_capability_mapping_init.py
01260207201000001250_REGISTRY/01260207201000001270_scripts/P_01260207201000000864_*_argparse_extractor.py
01260207201000001250_REGISTRY/01260207201000001270_scripts/P_01260207201000000865_*_registry_patch_generator.py
  → 01260207201000001313_capability_mapping_system/src/
```

**Schemas:**
```
newPhasePlanProcess/01260207201000001223_schemas/01260207201000000529_CAPABILITIES.schema.v1.json
newPhasePlanProcess/01260207201000001223_schemas/COMPONENT_CAPABILITY_VOCAB.json
  → 01260207201000001313_capability_mapping_system/schemas/
```

**Docs (from root + newPhasePlanProcess):**
```
Gov_Reg/CAPABILITY_MAPPING_PIPELINE_COMPLETE_REPORT.md
Gov_Reg/CAPABILITY_MAPPING_FINAL_COMPLETION_REPORT.md
Gov_Reg/CAPABILITY_MAPPING_IMPLEMENTATION_SUMMARY.md
Gov_Reg/newPhasePlanProcess/01260207201000000454_capability_mapping_status_report.md
  → 01260207201000001313_capability_mapping_system/docs/
```
Note: `.state/.../01260207201000000269_capability_mapping_status_report.md` is a duplicate of the newPhasePlanProcess copy — leave in `.state/`.

**Archive (old versions):**
```
01260207201000001250_REGISTRY/archive/.../capability_mapping/P_01260207201000000984_*_purpose_registry_builder.py
01260207201000001250_REGISTRY/archive/.../capability_mapping/P_01260207201000000985_*_registry_promoter.py
  → 01260207201000001313_capability_mapping_system/archive/
```

### Step 3 — Patch `capability_mapper.py` sys.path block

**File:** `01260207201000001313_capability_mapping_system/capability_mapper.py`

After the move, `Path(__file__).parents[1]` still correctly resolves to `Gov_Reg/`. Only these two lines need updating:

```python
# BEFORE
sys.path.insert(0, str(repo_root / "01260207201000001289_src" / "01260207201000001290_capability_mapping"))
sys.path.insert(0, str(repo_root / "01260207201000001250_REGISTRY" / "01260207201000001265_mapp_py"))
sys.path.insert(0, str(repo_root / "01260207201000001250_REGISTRY" / "01260207201000001270_scripts"))

# AFTER
_here = Path(__file__).parent
sys.path.insert(0, str(_here / "src"))
sys.path.insert(0, str(_here / "mapp_py"))
# 01260207201000001270_scripts no longer needed (relevant files moved to src/)
```

Also fix the hardcoded absolute path:
```python
# BEFORE
DEFAULT_REGISTRY_ROOT = Path(r"C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY")

# AFTER
DEFAULT_REGISTRY_ROOT = repo_root / "01260207201000001250_REGISTRY"
```

### Step 4 — Fix the one external mapp_py dependency

**File:** `01260207201000001276_scripts/01260207201000001283_parsers/P_01260207233100000307_*_integration_bridge.py`

This file imports `from file_comparator import FileComparator, ComparisonResult` but does not add mapp_py to sys.path itself. After the move, add to its sys.path block:

```python
_repo_root = Path(__file__).parents[2]
sys.path.insert(0, str(_repo_root / "01260207201000001313_capability_mapping_system" / "mapp_py"))
```

### Step 5 — Create README.md

Write `01260207201000001313_capability_mapping_system/README.md` covering:
- System purpose (4-step pipeline: discover → inventory → map → promote)
- Folder layout (src/, mapp_py/, schemas/, docs/, archive/)
- How to run (`python capability_mapper.py --step all`)
- Key inputs/outputs (CAPABILITIES.json, FILE_PURPOSE_REGISTRY.json, SSOT registry patch)
- Configuration files (COMPONENT_CAPABILITY_VOCAB.json, SCRIPT_CLASSIFIER_OVERRIDES.json)
- State outputs location (`.state/purpose_mapping/`)
- Status: complete as of 2026-02-20 (574 files tagged, 796 patch ops)

---

## Files NOT moved (intentional)
- `caps_keyword_archiver.py` — unrelated file-organization utility
- `.state/purpose_mapping/*` — runtime outputs, stay in `.state/`
- `.state/evidence/purpose_mapping/*` — audit evidence, stays in `.state/`
- `newPhasePlanProcess/.state/.../RUN-CAPMAP*` — execution run history, stays in `.state/`
- `01260207201000001250_REGISTRY/01260207201000001270_scripts/` other 21 files — not capability-mapping-specific

---

## Verification
1. Run `python 01260207201000001313_capability_mapping_system/capability_mapper.py --step 1` and confirm it produces CAPABILITIES.json without import errors.
2. Confirm `integration_bridge.py` still imports `file_comparator` without error.
3. Confirm no other script references the old locations by grepping for `01260207201000001265_mapp_py` and `01260207201000001290_capability_mapping` in sys.path additions.
