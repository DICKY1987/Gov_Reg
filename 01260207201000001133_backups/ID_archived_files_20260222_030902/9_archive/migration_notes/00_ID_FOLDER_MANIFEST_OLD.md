# ID Folder Organization Manifest

**Last Updated:** 2026-02-19  
**Cleanup Status:** ✅ Complete (Phases 1-5)

---

## Directory Structure

```
ID/
├── runtime/           → Core ID allocation & management (9 scripts)
├── tests/            → Test suites (4 scripts)
├── config/           → Configuration & schemas (4 files)
├── docs/             → Primary documentation (5 docs)
├── archive/          → Historical/deprecated files (25 files)
└── [root]/           → Active automation scripts (27 scripts)
```

---

## Core Runtime Components (`runtime/`)

**ID Allocation:**
- `P_01999000042260124031_unified_id_allocator.py` - Core 20-digit ID allocator (SSOT)
- `P_01999000042260125006_id_allocator_facade.py` - Simplified allocation interface
- `P_01999000042260126000__idpkg_runtime.py` - IDPKG unified runtime engine

**Directory ID Management:**
- `P_01999000042260125068_dir_id_handler.py` - .dir_id file read/write operations
- `P_01260207233100000070_dir_identity_resolver.py` - Directory identity resolution
- `P_01999000042260125067_zone_classifier.py` - Zone classification (governed/staging/excluded)

**Automation & Repair:**
- `P_01999000042260125104_dir_id_auto_repair.py` - Auto-repair corrupted .dir_id files
- `P_01999000042260125105_dir_id_watcher.py` - Filesystem watcher for continuous enforcement
- `P_01999000042260125106_registry_filesystem_reconciler.py` - Registry/filesystem sync

**Maintenance:**
- `P_01999000042260125111_orphan_purger.py` - Cleanup orphaned entries

---

## Active Automation Scripts (root level)

**Directory ID Generation:**
- `P_01999000042260125100_generate_dir_ids_gov_reg.py` - Generate .dir_id files
- `P_01999000042260125101_validate_dir_ids.py` - Validate .dir_id files
- `P_01999000042260125103_rename_dirs_with_id.py` - Rename dirs with ID prefix

**File ID Assignment:**
- `P_01260207201000000109_add_file_ids.py` - Add IDs to current directory files
- `P_01260207201000000198_add_ids_recursive.py` - Recursive file ID assignment
- `P_01260207233100000287_batch_assign_file_ids.py` - Batch file ID operations

**Git Hooks:**
- `P_01999000042260125106_pre_commit_dir_id_check.py` - Pre-commit validation
- `P_01999000042260125107_pre_push_governance_check.py` - Pre-push validation

**Monitoring:**
- `P_01999000042260125113_healthcheck.py` - Nightly health monitoring

**Registry Integration:**
- `P_01999000042260125102_populate_registry_dir_ids.py` - Populate registry with dir_ids
- `P_01999000042260125110_populate_registry_dir_ids_enhanced.py` - Enhanced population + coverage
- `P_01999000042260125104_update_registry_paths.py` - Update registry paths

**Installation:**
- `install_automation.py` - Setup automation components

---

## Configuration & Schemas (`config/`)

- `IDPKG_CONFIG.schema.json` - IDPKG configuration schema
- `01260207201000000877_DIR_ID_ANCHOR.schema.json` - .dir_id file format schema
- `01260207201000000123_DOC-CONFIG-1208__ChatGPT-Stable ID Types.json` - ID type definitions

---

## Primary Documentation (`docs/`)

1. `01260207201000000122_DIR_ID_SYSTEM_DOCUMENTATION.md` - Complete system documentation
2. `01260207201000000174_ID_IDENTITY_CONTRACT.md` - ID contract specification
3. `ID_AUTOMATION_COMPLETE.md` - Automation implementation guide
4. `README_CONSOLIDATION.md` - Consolidation guide
5. `CONSOLIDATION_COMPLETE.md` - Consolidation completion report

---

## Test Suites (`tests/`)

- `P_01999000042260124029_test_id_allocator.py` - ID allocator tests
- `P_01999000042260124040_test_reservation_system.py` - Reservation system tests
- `P_01260207201000001009_test_directory_identity.py` - Directory identity tests
- `P_01260207233100000050_test_identity_resolver.py` - Identity resolver tests

---

## Archive (`archive/`)

**legacy_scripts/** - Superseded implementations  
**historical_docs/** - Historical documentation and analysis  
**aider_docs/** - AIDER AI tool documentation

---

## Quick Start

**Generate .dir_id for all governed directories:**
```bash
python ID/P_01999000042260125100_generate_dir_ids_gov_reg.py --config .idpkg/config.json
```

**Add file IDs recursively:**
```bash
python ID/P_01260207201000000198_add_ids_recursive.py
```

**Install automation (Git hooks, watchers):**
```bash
python ID/install_automation.py
```

**Run health check:**
```bash
python ID/P_01999000042260125113_healthcheck.py --config automation_config.json
```

---

## Related Folders

- **`01260207201000001250_REGISTRY/`** - All registry files and management scripts
- **`01260207201000001148_evidence/`** - Evidence artifacts, validation reports, analysis
- **`01260207201000001173_govreg_core/`** - Core governance modules (non-ID specific)

---

**Cleanup Completed:** 2026-02-19  
**Files Organized:** 87 operations across 5 phases  
**Structure Status:** ✅ Clean, navigable, maintainable
