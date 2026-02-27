# REGISTRY Cleanup Plan
**Created:** 2026-02-27  
**Status:** Ready for Execution

---

## ✅ COMPLETED - Priority 1: Documentation Fixes

### 00_REGISTRY_FOLDER_MANIFEST.md
- ✅ Removed 5 non-existent directories (type_registries, from_gov_reg_root, from_gov_reg_subdirs, from_all_ai, from_ssot_refactor)
- ✅ Added 8 actual directories (FILE WATCHER, scripts, tests, COLUMN_HEADERS, ID, docs, src_modules, capability_mapping_system)
- ✅ Updated last modified date to 2026-02-27
- ✅ Fixed registry filename (governance_registry_unified.json → REGISTRY_file.json)

### CLAUDE.md (in REGISTRY)
- ✅ Fixed registry filename path
- ✅ Fixed COLUMN_HEADERS paths (write policy & derivations now correctly show subdir)
- ✅ Clarified transition_contract.bundle.yaml location (root, not REGISTRY)

---

## ✅ COMPLETED - Priority 2: Duplicate Python Files

### mapp_py/ Directory Analysis

**✅ DONE - Archived 6 duplicate files:**
- `P_01260202173939000016_text_normalizer.py` → archive/cleanup_2026-02-27/duplicates/
- `P_01260202173939000075_text_normalizer.py` → archive/cleanup_2026-02-27/duplicates/
- `P_01260202173939000078_text_normalizer.py` → archive/cleanup_2026-02-27/duplicates/
- `P_01260202173939000080_component_extractor.py` → archive/cleanup_2026-02-27/duplicates/
- `P_01260202173939000082_dependency_analyzer.py` → archive/cleanup_2026-02-27/duplicates/
- `P_01260202173939000074_cli_entry_point.py` → archive/cleanup_2026-02-27/duplicates/

**Canonical files retained:**
- `P_01260202173939000060_text_normalizer.py` ✓
- `P_01260202173939000061_component_extractor.py` ✓
- `P_01260202173939000063_dependency_analyzer.py` ✓
- `P_01260202173939000072_cli_entry_point.py` ✓

---

## ✅ COMPLETED - Priority 3: YYY Placeholder IDs (9 files)

**All 9 files finalized with proper 20-digit IDs:**

### In `01260207220000001322_src/`:
1. ✅ `P_01260207201000000864_01999000042260130001_argparse_extractor.py` (was YYY)
2. ✅ `P_01260207201000000979_01999000042260130002___init__.py` (was YYY)
3. ✅ `P_01260207201000000980_01999000042260130003_argparse_extractor.py` (was YYY)
4. ✅ `P_01260207201000000981_01999000042260130004_call_graph_builder.py` (was YYY)
5. ✅ `P_01260207201000000982_01999000042260130005_capability_discoverer.py` (was YYY)
6. ✅ `P_01260207201000000983_01999000042260130006_file_inventory_builder.py` (was YYY)

### In `capability_system_scripts/`:
7. ✅ `P_01260207201000000865_01999000042260130007_registry_patch_generator.py` (was YYY)
8. ✅ `P_01260207201000000984_01999000042260130008_purpose_registry_builder.py` (was YYY)
9. ✅ `P_01260207201000000985_01999000042260130009_registry_promoter.py` (was YYY)

**All imports updated in:**
- P_01260207201000000979___init__.py
- P_01260207220000001315_capability_mapper.py
- P_01260207201000000850_capability_mapping_init.py
- P_01260207201000000864_argparse_extractor.py
- P_01260207201000000982_capability_discoverer.py
- P_01260207201000000983_file_inventory_builder.py
- P_01260207201000000984_purpose_registry_builder.py

---

## 🟢 Priority 4: Stub/Placeholder Implementations

### Test Stubs (Pass-only bodies)
- `tests/unit/test_copilot_parser.py`
- `tests/unit/test_collector.py`

**Action:** Either implement tests or remove stubs

### Incomplete Modules
- `src_modules/.../field_precedence.py`
- `src_modules/.../gates.py`
- `ID/1_runtime/watchers/dir_id_watcher.py`
- `ID/2_cli_tools/maintenance/healthcheck.py`
- `ID/7_automation/scanner_service.py`
- `ID/7_automation/scanner.py`
- `ID/7_automation/registry_filesystem_reconciler.py`
- `ID/7_automation/populate_registry_dir_ids_enhanced.py`
- `mapp_py/registry_integration_pipeline.py`

**Action:** Review each file:
- If planned work → add TODO/PLANNED marker
- If dead code → move to archive

---

## 📋 Other Documentation Issues

### COLUMN_HEADERS/REGISTRY_COLUMN_HEADERS.md
- `data_transformation` field type shows boolean|string|null (remediation removed boolean)
- 5 fields still show "core" in scope (remediation removed all core references)
- Missing serialization specs added during Phase B6

**Action:** Update field definitions to match post-remediation state

### docs/00_REPORTS_INDEX.md
- References 16 reports as root-level, most moved to `archive/analysis_reports/`

**Action:** Update report paths

### docs/BACKUP_HIERARCHY.md
- References outdated commit hashes (e656e83, 72c2fda, ac63f85)

**Action:** Update or mark as historical reference

### README_ENHANCED_SCANNER.md
- References non-existent doc paths (`01260207201000001139_docs/...`)

**Action:** Fix paths or archive document

### REMEDIATION_EXECUTION_COMPLETE.md
- Has 3 uncompleted post-execution checklist items

**Action:** Either complete checklist or mark items as not applicable

---

## Execution Order

1. ✅ **DONE:** Fix critical documentation (00_REGISTRY_FOLDER_MANIFEST.md, CLAUDE.md)
2. ✅ **DONE:** Archive duplicate mapp_py files (6 files)
3. ✅ **DONE:** Finalize YYY placeholder files (9 files with proper IDs)
4. **IN PROGRESS:** Review and handle stub implementations (12+ files)
5. **PENDING:** Update secondary documentation issues

---

## Archive Location

All removed files should be moved to:
```
01260207201000001250_REGISTRY/archive/cleanup_2026-02-27/
├── duplicates/         ← duplicate mapp_py files
├── yyy_placeholders/   ← unfinalised YYY files (if archiving)
└── stubs/             ← incomplete stub implementations
```

---

**Current Status:** Priorities 1-3 complete. Ready for stub review and documentation updates.

**Commits:**
- `18a2367` - docs(registry): fix REGISTRY documentation and create cleanup plan
- `3ca5a56` - refactor(registry): finalize YYY placeholders and archive duplicates
