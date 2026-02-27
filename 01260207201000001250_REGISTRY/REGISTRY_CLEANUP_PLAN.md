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

## 🔴 Priority 2: Duplicate Python Files

### mapp_py/ Directory Analysis

Based on `script_name_resolver.py`, the following files are **canonical** (actively referenced):

**Canonical Files (Keep):**
- `P_01260202173939000060_text_normalizer.py` ← canonical
- `P_01260202173939000061_component_extractor.py` ← canonical  
- `P_01260202173939000063_dependency_analyzer.py` ← canonical
- `P_01260202173939000072_cli_entry_point.py` ← canonical

**Duplicate/Alternate Versions (Remove):**
- `P_01260202173939000016_text_normalizer.py` (older version, 6731 bytes)
- `P_01260202173939000075_text_normalizer.py` (alt version, 10431 bytes)
- `P_01260202173939000078_text_normalizer.py` (alt version, 4482 bytes)
- `P_01260202173939000080_component_extractor.py` (marked as v2 in resolver)
- `P_01260202173939000082_dependency_analyzer.py` (marked as v2 in resolver)
- `P_01260202173939000074_cli_entry_point.py` (duplicate)

**Action:** Move 6 duplicate files to archive before deletion

### argparse_extractor Duplicates

Located in `01260207220000001322_src/`:
- `P_01260207201000000864_P_01260207233100000YYY_argparse_extractor.py`
- `P_01260207201000000980_P_01260207233100000YYY_argparse_extractor.py`

**Action:** Both have YYY placeholders; address in Priority 3

---

## 🟡 Priority 3: YYY Placeholder IDs (9 files)

All in `capability_mapping_system/`:

### In `01260207220000001322_src/`:
1. `P_01260207201000000864_P_01260207233100000YYY_argparse_extractor.py`
2. `P_01260207201000000979_P_01260207233100000YYY___init__.py`
3. `P_01260207201000000980_P_01260207233100000YYY_argparse_extractor.py`
4. `P_01260207201000000981_P_01260207233100000YYY_call_graph_builder.py`
5. `P_01260207201000000982_P_01260207233100000YYY_capability_discoverer.py`
6. `P_01260207201000000983_P_01260207233100000YYY_file_inventory_builder.py`

### In `capability_system_scripts/`:
7. `P_01260207201000000865_P_01260207233100000YYY_registry_patch_generator.py`
8. `P_01260207201000000984_P_01260207233100000YYY_purpose_registry_builder.py`
9. `P_01260207201000000985_P_01260207233100000YYY_registry_promoter.py`

**Decision Required:**
- Option A: Finalize IDs (allocate proper 20-digit IDs to replace YYY)
- Option B: Mark as deprecated and move to archive
- Option C: Delete if not in use

**Recommended:** Check for imports/references, then either finalize or archive

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
2. **NEXT:** Archive duplicate mapp_py files (6 files)
3. **NEXT:** Decide on YYY placeholder files (9 files)
4. **LATER:** Review and handle stub implementations (12+ files)
5. **LATER:** Update secondary documentation issues

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

**Next Action:** Review YYY placeholder files for imports/usage before archiving or finalizing
