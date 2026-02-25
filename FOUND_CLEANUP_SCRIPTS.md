# Found Cleanup Scripts - Location Summary

**Date:** 2026-02-24
**Source:** External archive directories

## ✅ Files Found

### A) safe_cleanup_deprecated_folders.py

**Locations:**
1. `C:\Users\richg\CENTRAL_ARCHIVE\ARCHIVE_LEGACY_BACKUPS\20260109_123529\UTI_Archives\migration_tools_2026\safe_cleanup_deprecated_folders.py`
2. `C:\Users\richg\CENTRAL_ARCHIVE\UTI_Archives_ALL_AI\Complete_AI_Pipeline_Legacy_20251217_163705\scripts\safe_cleanup_deprecated_folders.py`

**Confirmed Features (from file inspection):**
- SAFE_TO_ARCHIVE dictionary with folder targets
- NEEDS_REVIEW dictionary for manual verification
- Timestamped archive creation
- JSON summary generation
- README creation in archive
- Move (not delete) pattern

**Status:** ✅ Found and verified

---

### C) cleanup_invalid_doc_ids.py

**Location:**
`C:\Users\richg\CENTRAL_ARCHIVE\UTI_Archives_ALL_AI\Complete_AI_Pipeline_Legacy_20251217_163705\doc_id\cleanup_invalid_doc_ids.py`

**Confirmed Features (from file inspection):**
- DOC_ID regex validation pattern: `^DOC-[A-Z0-9]+-[A-Z0-9]+(-[A-Z0-9]+)*-[0-9]{3}$`
- Scan mode for detection
- Fix mode with --dry-run and --backup flags
- Detects: malformed, duplicates, orphaned doc_ids
- Supports eligible file types: .py, .md, .yaml, .yml, .json, .ps1, .sh, .txt
- Excludes standard directories: .git, __pycache__, .venv, node_modules, .pytest_cache

**Status:** ✅ Found and verified

---

## ❌ Files NOT Found

### B) cleanup_orphans.py
**Status:** Not found in searched locations

### test_orphan_cleanup.py  
**Status:** Not found in searched locations

### cleanup_archive_and_obsolete.ps1
**Status:** Not found in searched locations

### run_cleanup_now.ps1
**Status:** Not found in searched locations

---

## 🔍 Search Locations Checked

1. ✅ `C:\Users\richg\ALL_AI` - Partial match (cleanup_invalid_doc_ids references found)
2. ✅ `C:\Users\richg\CENTRAL_ARCHIVE` - **Primary source** (2 key scripts found)
3. ✅ `C:\Users\richg\Downloads` - No matches
4. ✅ `C:\Users\richg\eafix-modular\Directory management system` - No matches
5. ✅ `C:\Users\richg\Gov_Reg` - No original scripts (has similar newer implementations)

---

## 📊 Related Scripts in Current Gov_Reg Repository

### Similar functionality exists in:

1. **P_01999000042260125111_orphan_purger.py**
   - Location: `01260207201000001250_REGISTRY\ID\1_runtime\watchers\`
   - Features: Quarantine, dry-run, evidence logging, zone classification
   - More advanced than the missing cleanup_orphans.py

2. **P_01260207233100000277_check_orphans.py**
   - Location: `newPhasePlanProcess\01260207201000001225_scripts\01260207201000001226_wiring\`
   - Simpler orphan detection for plan artifacts

3. **01260207233100000388_cleanup_duplicates.ps1**
   - Location: `files_to_review\scripts\`
   - Handles duplicate validation files with backup strategy

---

## 🎯 Recommendation

**To use the found scripts:**

1. **Copy scripts to Gov_Reg:**
   ```powershell
   Copy-Item "C:\Users\richg\CENTRAL_ARCHIVE\UTI_Archives_ALL_AI\Complete_AI_Pipeline_Legacy_20251217_163705\scripts\safe_cleanup_deprecated_folders.py" "C:\Users\richg\Gov_Reg\scripts\"
   Copy-Item "C:\Users\richg\CENTRAL_ARCHIVE\UTI_Archives_ALL_AI\Complete_AI_Pipeline_Legacy_20251217_163705\doc_id\cleanup_invalid_doc_ids.py" "C:\Users\richg\Gov_Reg\scripts\"
   ```

2. **Generalize as planned:**
   - Replace hardcoded dictionaries with YAML/JSON config
   - Add CLI arguments: --target-dir, --archive-base-dir, --dry-run
   - Implement automated reference scanning
   - Split into scan/fix modes with patch logs

3. **Missing scripts:**
   - cleanup_orphans.py: Use existing P_01999000042260125111_orphan_purger.py as superior replacement
   - PowerShell cleanup scripts: Either locate in another archive or recreate from patterns
