# REGISTRY Folder Organization Manifest

**Last Updated:** 2026-02-27  
**Consolidation Status:** ✅ Complete (Post-Remediation)

---

## Directory Structure

```
01260207201000001250_REGISTRY/
├── archive/                                          → Old registry versions & historical files
├── COLUMN_HEADERS/                                   → Registry column definitions & mappings
├── docs/                                             → Registry documentation & reports
├── ID/                                               → ID system integration scripts
├── src_modules/                                      → Registry source modules
├── scripts/                                          → Registry management scripts
├── tests/                                            → Registry test suites
├── FILE WATCHER/                                     → File system monitoring integration
├── 01260207201000001313_capability_mapping_system/  → Capability discovery & mapping
└── [root]/                                          → Active registry files & schemas
```

---

## Key Registry Files (root level)

**Main Registry (Authoritative):**
- Registry file: `01999000042260124503_REGISTRY_file.json`
- Schema: `01999000042260124012_governance_registry_schema.v3.json`

**Active Management:**
- `P_01260207201000000865_P_01260207233100000YYY_registry_patch_generator.py`
- `P_01260207201000000834_apply_patch.py`

---

## Subdirectory Organization

### `COLUMN_HEADERS/`
**Registry column definitions and derivations:**
- `01260207201000000192_UNIFIED_SSOT_REGISTRY_DERIVATIONS.yaml` - Computed field formulas (safe DSL)
- `01260207201000000193_UNIFIED_SSOT_REGISTRY_WRITE_POLICY.yaml` - Column write rules
- `REGISTRY_COLUMN_HEADERS.md` - Column documentation
- `PY_COLUMN_PIPELINE_MAPPING.csv` - Python pipeline mappings

### `ID/`
**ID system integration:**
- `1_runtime/` - ID runtime validators & watchers
- `2_cli_tools/` - ID maintenance CLI tools
- `7_automation/` - ID automation scripts & reconcilers

### `src_modules/`
**Registry source modules:**
- Field precedence logic
- Gate implementations
- State machine components

### `scripts/`
**Registry management scripts:**
- Utilities (registry CLI, normalization)
- Validators (schema validation, compliance checks)

### `tests/`
**Registry test suites:**
- Unit tests for registry components
- Integration tests for registry operations

### `FILE WATCHER/`
**File system monitoring integration:**
- Real-time registry sync watchers
- Event emission handlers

### `01260207201000001313_capability_mapping_system/`
**Capability discovery and mapping:**
- `mapp_py/` - Python analysis tools (29 modules)
- `capability_system_scripts/` - Registry patch generators
- `01260207220000001322_src/` - Source capability builders

---

## Archive Structure (`archive/`)

**old_registry_versions/** - Superseded registry JSON files:
- `01260207201000000855_governance_registry.json`
- `01260207201000000862_master_registry.json`
- `01999000042260124527_governance_registry.json`

---

## Registry Scripts by Function

### Registry CLI & TUI
- `01260207201000001270_scripts/P_01999000042260126011_registry_tui.py` - Interactive registry browser

### Registry Validation
- `scripts/` - Schema validation and compliance checks
- ID system validators in `ID/1_runtime/validators/`

### Capability Mapping
- `01260207201000001313_capability_mapping_system/` - Full capability discovery pipeline

---

## Key Integrations

**ID System Integration:**
- Registry files link to `../ID/` for ID allocation
- Dir IDs are populated into registry entries
- File IDs are tracked in registry metadata

**Evidence System:**
- Registry operations emit evidence to `../01260207201000001148_evidence/`
- Validation reports stored in evidence structure

**SSOT Governance:**
- Registry is the Single Source of Truth for file metadata
- All file tracking flows through registry
- Registry schema enforces data contracts

---

## Consolidation Summary

**Post-Remediation Structure (2026-02-27):**
- Eliminated 5 non-existent directories from manifest
- Added 8 actual directories (FILE WATCHER, scripts, tests, etc.)
- Registry structure now accurately documented
- Capability mapping system fully integrated

**Organization Applied:**
- Core registry files at root level
- Column definitions in COLUMN_HEADERS/
- Historical files in archive/
- Domain-specific systems in numbered subdirectories

**Result:** Clean, navigable registry structure with accurate documentation matching filesystem reality.

---

**Manifest Version:** 1.0  
**Maintenance:** Update when registry structure changes
