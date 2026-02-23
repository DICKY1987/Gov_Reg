# REGISTRY Folder Organization Manifest

**Last Updated:** 2026-02-19  
**Consolidation Status:** ✅ Complete

---

## Directory Structure

```
01260207201000001250_REGISTRY/
├── type_registries/              → 29 registry type definitions (YAML)
├── archive/                      → Old registry versions & historical files
├── from_gov_reg_root/           → Original root-level registry files
├── from_gov_reg_subdirs/        → Registry scripts from subdirectories
├── from_all_ai/                 → AI-generated registry tooling
├── from_ssot_refactor/          → SSOT registry corrections
├── [various numbered dirs]/     → Categorized registry components
└── [root]/                      → Active registry files & main registry
```

---

## Key Registry Files (root level)

**Main Registry (Authoritative):**
- Look for most recent: `01999000042260124503_governance_registry_unified.json`
- Schema: `01999000042260124012_governance_registry_schema.v3.json`

**Active Management:**
- `P_01260207201000000865_P_01260207233100000YYY_registry_patch_generator.py`
- `P_01260207201000000834_apply_patch.py`

---

## Type Registries (`type_registries/`)

**29 Domain-Specific Registries:**
- `DOC-REGISTRY-ALERT-ID-001__ALERT_REGISTRY.yaml`
- `DOC-REGISTRY-BENCHMARK-ID-001__BENCHMARK_REGISTRY.yaml`
- `DOC-REGISTRY-CHAIN-ID-001__CHAIN_REGISTRY.yaml`
- `DOC-REGISTRY-CONFIG-ID-001__CONFIG_REGISTRY.yaml`
- `DOC-REGISTRY-CONTRACT-ID-001__CONTRACT_REGISTRY.yaml`
- `DOC-REGISTRY-GATE-ID-001__GATE_REGISTRY.yaml`
- `DOC-REGISTRY-METRIC-ID-001__METRIC_REGISTRY.yaml`
- `DOC-REGISTRY-POLICY-ID-001__POLICY_REGISTRY.yaml`
- `DOC-REGISTRY-WORKSTREAM-ID-001__WORKSTREAM_REGISTRY.yaml`
- ... and 20 more type registries

---

## Subdirectory Organization

### `from_gov_reg_subdirs/`
**Registry management scripts organized by function:**
- `scripts/utilities/` - Registry CLI, normalization, store management
- `scripts/validation/` - Registry validation tools
- `scripts/migration/` - Registry migration scripts
- `scripts/registry_writer/` - Registry write operations
- `scripts/registry_transition/` - Registry transition management
- `scripts/path_registry/` - Path registry watchers
- `scripts/govreg_core/` - Core registry schema and reconciliation
- `tests/` - Registry test suites
- `config/` - Registry configuration

### `from_all_ai/`
**AI-generated registry tooling:**
- `runtime/doc_id/` - DOC_ID registry runtime
- `runtime/path_registry/` - Path registry runtime
- `scripts/generators/` - Registry generators
- `scripts/migration/` - Migration planning
- `modules/` - Path abstraction modules
- `mini_pipe/` - Lightweight registry tools

### `from_ssot_refactor/`
**SSOT registry correction artifacts:**
- `phase_a1_registry_correction.py` - Registry correction script
- Registry patches and reports (RFC6902 format)

---

## Archive Structure (`archive/`)

**old_registry_versions/** - Superseded registry JSON files:
- `01260207201000000855_governance_registry.json`
- `01260207201000000862_master_registry.json`
- `01999000042260124527_governance_registry.json`

---

## Registry Scripts by Function

### Registry Population & Sync
- `from_gov_reg_subdirs/scripts/utilities/P_01999000042260125062_normalize_registry.py`
- `from_gov_reg_subdirs/scripts/utilities/P_01999000042260125063_registry_cli.py`
- `from_gov_reg_root/P_01260207201000000199_sync_registry_recursive.py`

### Registry Validation
- `from_gov_reg_subdirs/scripts/validation/P_01260207233100000247_validate_artifact_registry.py`
- `from_all_ai/migrations/DOC-SCRIPT-1289__validate_path_registry.py`

### Registry Writers
- `from_gov_reg_subdirs/scripts/registry_writer/P_01260207233100000335_registry_writer_service_v2.py`
- `from_gov_reg_subdirs/scripts/registry_transition/P_01260207233100000325_registry_writer.py`

### Path Registry
- `from_gov_reg_subdirs/scripts/path_registry/P_01260207233100000026_path_registry.py`
- `from_gov_reg_subdirs/scripts/path_registry/P_01999000042260126009_path_registry_watcher.py`

### Registry TUI
- `01260207201000001270_scripts/P_01999000042260126011_registry_tui.py` - Interactive registry browser

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

**Files Moved In:** 77 registry-related files from:
- ID folder (44 files)
- SSOT_REFACTOR (4 files)
- Various locations

**Organization Applied:**
- Type registries → dedicated subfolder
- Old versions → archive
- Domain scripts → function-based subdirectories

**Result:** Clean, navigable registry structure with clear separation between active, archived, and type-specific files.

---

**Manifest Version:** 1.0  
**Maintenance:** Update when registry structure changes
