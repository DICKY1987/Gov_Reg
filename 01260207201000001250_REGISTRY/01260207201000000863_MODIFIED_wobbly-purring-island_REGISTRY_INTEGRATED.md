# Capability Mapping Plan - Modified for SSOT Registry Integration

## Overview

This plan creates a three-step system to map repository files to their capabilities, with **all authoritative data written to the existing SSOT registry** under `C:\Users\richg\Gov_Reg\REGISTRY`.

**CRITICAL: This plan does NOT create a parallel registry.** The files in `.state/purpose_mapping/` are **derived artifacts (evidence only)**, not SSOT. All durable truth is written to the existing registry files.

---

## Registry Configuration

### Authoritative Registry Files (SSOT)
- **REGISTRY_ROOT**: `C:\Users\richg\Gov_Reg\REGISTRY`
- **FILE_REGISTRY_PATH**: `01999000042260124503_REGISTRY_file.json` (723 records)
- **COLUMN_DICTIONARY_PATH**: `01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json`
- **GOVERNANCE_REGISTRY_PATH**: `01999000042260124527_COMPLETE_SSOT.json` (read-only for this plan)

### Registry Tools
- `registry_tools/snapshot.py` - Create immutable snapshots
- `registry_tools/apply_patch.py` - Apply RFC-6902 patches
- `registry_tools/diff_snapshots.py` - Compare snapshots

---

## Implementation Steps

### Step 1 — Discover Capabilities

**Purpose**: Scan repository and discover all capabilities from CLI commands, gate validators, schemas, and documentation.

**Module**: `src/capability_mapping/P_*_capability_discoverer.py`

**Output (EVIDENCE ONLY)**:
- `.state/purpose_mapping/CAPABILITIES.json`

**This is NOT SSOT** - it's a derived report used to generate registry patches.

**Schema**:
```json
{
  "capabilities": [
    {
      "capability_id": "CAP-CLI-VALIDATE_SCHEMA",
      "name": "Schema Validation",
      "domain": "cli|gate|schema|workflow",
      "status": "implemented|declared_not_implemented",
      "source_evidence": [...],
      "candidate_files": [...]
    }
  ]
}
```

---

### Step 2 — Build File Inventory

**Purpose**: Create complete inventory of all repository files with objective metadata.

**Module**: `src/capability_mapping/P_*_file_inventory_builder.py`

**Output (EVIDENCE ONLY)**:
- `.state/purpose_mapping/FILE_INVENTORY.jsonl`

**This is NOT SSOT** - it's a derived report used for mapping analysis.

**Format**: JSONL (one JSON object per line)

---

### Step 3 — Create Purpose Registry

**Purpose**: Map files to capabilities with full traceability.

**Module**: `src/capability_mapping/P_*_purpose_registry_builder.py`

**Output (EVIDENCE ONLY)**:
- `.state/purpose_mapping/FILE_PURPOSE_REGISTRY.json`

**This is NOT SSOT** - it's a derived report used to generate registry patches.

**Schema**:
```json
{
  "mappings": [
    {
      "file": "scripts/validator.py",
      "classification": "entrypoint_cli",
      "primary_capability_id": "CAP-CLI-VALIDATE",
      "called_by_observed": [...],
      "mapping_confidence": "high|medium|low"
    }
  ]
}
```

---

### Step 4 — Registry Integration (SSOT Write-Back)

**THIS IS THE AUTHORITATIVE STEP** - This writes to SSOT.

#### 4.1 Resolve Registry Records

For each mapped file in `FILE_PURPOSE_REGISTRY.json`:
1. Find the corresponding record in `FILE_REGISTRY_PATH` by:
   - `file_id` (if present in mapping)
   - Otherwise `relative_path` (exact match)
2. If not found: **BLOCKING ERROR** (file must exist in registry first)

#### 4.2 Column Strategy

**Required fields to store in registry** (use existing headers if available):
- `one_line_purpose` (short purpose description)
- `py_capability_tags` (array of capability IDs, Python-specific)
- `py_capability_facts_hash` (deterministic hash of capability facts)

**If new headers needed**:
1. Generate RFC-6902 patch for `COLUMN_DICTIONARY_PATH`
2. Add to `column_headers` section (append-only, never renumber)
3. Default presence: OPTIONAL (unless gate requires it)

#### 4.3 Generate RFC-6902 Patches

**Output patches**:
- `.state/purpose_mapping/patch_column_dictionary.json` (if needed)
- `.state/purpose_mapping/patch_file_registry.json` (required)

**Patch rules**:
- Minimal patches only (don't rewrite unrelated sections)
- Stable ordering (sort by `file_id`, tie-break by `relative_path`)
- Use JSON Pointer format: `/entities/123/one_line_purpose`

**Example patch operation**:
```json
[
  {
    "op": "add",
    "path": "/entities/42/one_line_purpose",
    "value": "Schema validation CLI command"
  },
  {
    "op": "add", 
    "path": "/entities/42/py_capability_tags",
    "value": ["CAP-CLI-VALIDATE_SCHEMA"]
  }
]
```

#### 4.4 Apply Patches (SSOT Modification)

**Commands**:
```bash
# 1) Snapshot before
python REGISTRY/registry_tools/snapshot.py \
  --in "REGISTRY/01999000042260124503_REGISTRY_file.json" \
  --out ".state/evidence/purpose_mapping/before_snapshot.json"

# 2) Apply column dictionary patch (if needed)
python REGISTRY/registry_tools/apply_patch.py \
  --target "REGISTRY/01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json" \
  --patch ".state/purpose_mapping/patch_column_dictionary.json" \
  --evidence ".state/evidence/purpose_mapping/"

# 3) Apply file registry patch (SSOT UPDATE)
python REGISTRY/registry_tools/apply_patch.py \
  --target "REGISTRY/01999000042260124503_REGISTRY_file.json" \
  --patch ".state/purpose_mapping/patch_file_registry.json" \
  --evidence ".state/evidence/purpose_mapping/"

# 4) Snapshot after
python REGISTRY/registry_tools/snapshot.py \
  --in "REGISTRY/01999000042260124503_REGISTRY_file.json" \
  --out ".state/evidence/purpose_mapping/after_snapshot.json"

# 5) Diff summary
python REGISTRY/registry_tools/diff_snapshots.py \
  --before ".state/evidence/purpose_mapping/before_snapshot.json" \
  --after ".state/evidence/purpose_mapping/after_snapshot.json" \
  --out ".state/evidence/purpose_mapping/diff_summary.json"
```

#### 4.5 Evidence Outputs

**Generated evidence**:
- `before_snapshot.json` - Registry state before changes
- `after_snapshot.json` - Registry state after changes
- `patch_file_registry.json` - Patch that was applied
- `patch_column_dictionary.json` - Column dictionary patch (if needed)
- `apply_result.json` - Application result with metadata
- `diff_summary.json` - Detailed diff between before/after

**Deterministic counts**:
- Number of records updated
- Number of files mapped
- Number of unmapped files (must be 0 or explicitly allowed)

---

## Final Outputs

### Derived/Evidence Artifacts (NON-AUTHORITATIVE)
- `.state/purpose_mapping/CAPABILITIES.json`
- `.state/purpose_mapping/FILE_INVENTORY.jsonl`
- `.state/purpose_mapping/FILE_PURPOSE_REGISTRY.json`

**These are reports, not SSOT. Do not query these for durable state.**

### SSOT Updates (AUTHORITATIVE)
- **Patched**: `C:\Users\richg\Gov_Reg\REGISTRY\01999000042260124503_REGISTRY_file.json`
- **(Optional) Patched**: `C:\Users\richg\Gov_Reg\REGISTRY\01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json`

**These are the single source of truth. Query these for capability mappings.**

### Evidence Bundle
- `.state/evidence/purpose_mapping/before_snapshot.json`
- `.state/evidence/purpose_mapping/after_snapshot.json`
- `.state/evidence/purpose_mapping/patch_file_registry.json`
- `.state/evidence/purpose_mapping/patch_column_dictionary.json` (if used)
- `.state/evidence/purpose_mapping/apply_result.json`
- `.state/evidence/purpose_mapping/diff_summary.json`

---

## Success Criteria

### SSOT Integration Validation (MANDATORY)

1. **Registry was modified**:
   - `FILE_REGISTRY_PATH` SHA256 hash changed
   - `diff_summary.json` shows `has_changes: true`
   - `diff_summary.json` shows `total_changes > 0`

2. **All mappings in SSOT**:
   - Every mapped file in `FILE_PURPOSE_REGISTRY.json` has corresponding fields in registry
   - `one_line_purpose` populated (when mapping provides it)
   - `py_capability_tags` populated (when applicable)

3. **Determinism**:
   - Re-run Step 4 without changing inputs → **identical patch** (or empty patch)
   - Diff summary identical (excluding timestamps)

4. **Evidence complete**:
   - All 6 evidence files exist
   - `apply_result.json` shows `success: true`
   - No unmapped gate-scope files (or explicitly documented as allowed)

### Additional Validation

5. **Capabilities discovered**: At least 10 capabilities found
6. **Files inventoried**: At least 100 files in inventory
7. **No parallel registry**: No SSOT queries target `.state/` files

---

## Implementation Modules

### Already Created
- ✓ `src/capability_mapping/__init__.py`
- ✓ `src/capability_mapping/P_*_argparse_extractor.py`
- ✓ `REGISTRY/registry_tools/snapshot.py`
- ✓ `REGISTRY/registry_tools/apply_patch.py`
- ✓ `REGISTRY/registry_tools/diff_snapshots.py`

### To Be Created
- ⏳ `src/capability_mapping/P_*_call_graph_builder.py`
- ⏳ `src/capability_mapping/P_*_capability_discoverer.py`
- ⏳ `src/capability_mapping/P_*_file_inventory_builder.py`
- ⏳ `src/capability_mapping/P_*_purpose_registry_builder.py`
- ⏳ `src/capability_mapping/P_*_registry_patch_generator.py` (NEW - Step 4)
- ⏳ `scripts/P_*_capability_mapper.py` (CLI orchestrator)

---

## Verification Commands

```bash
# Verify registry was updated
jq '.summary.has_changes' .state/evidence/purpose_mapping/diff_summary.json
# Expected: true

# Verify mapping count
jq '.summary.total_changes' .state/evidence/purpose_mapping/diff_summary.json
# Expected: > 0

# Verify no files in .state/ are treated as SSOT
grep -r "\.state/purpose_mapping" --include="*.py" src/ | grep -v "evidence"
# Expected: no matches (only evidence references)

# Query capability tags from SSOT
jq '.entities[] | select(.py_capability_tags != null) | {file: .relative_path, caps: .py_capability_tags}' REGISTRY/01999000042260124503_REGISTRY_file.json | head -5
# Expected: capability tags present in registry
```

---

**Document Version**: 2.0.0-registry-integrated  
**Last Updated**: 2026-02-11  
**Integration Status**: ✓ Registry tools created and tested
