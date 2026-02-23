# How to Identify Deprecated Files - Complete Guide
**Generated:** 2026-02-16 08:12:08

---

## 🔍 Deprecation Indicators (10 Methods)

### **1. File Location Analysis**
Files in archive/deprecated directories are usually deprecated:

**Obvious Indicators:**
- Path contains: `Archive`, `archived`, `ARCHIVE`
- Path contains: `deprecated`, `DEPRECATED`
- Path contains: `old`, `OLD`, `legacy`
- Path contains: `backup`, `BACKUP`
- Path contains: `obsolete`, `superseded`
- Path contains: `CONSOLIDATION_*` (consolidation archives)

**Example from your system:**
```
C:\Users\richg\Gov_Reg\01260207201000001118_Archive_Gov_Reg\
C:\Users\richg\Gov_Reg\01260207201000001118_Archive_Gov_Reg\01260207201000001121_id_scripts_deprecated\
C:\Users\richg\Gov_Reg\OLD_MD_DOCUMENTS_FOR_REVIEW\
```

✅ **File #3** was deprecated because:
- Located in `Archive_Gov_Reg\id_scripts_deprecated\CONSOLIDATION_*`
- Triple indicator: Archive + deprecated + CONSOLIDATION

---

### **2. Filename Patterns**
Deprecated files often have naming clues:

**Common Patterns:**
- Suffix: `_old.py`, `_backup.py`, `_deprecated.py`
- Suffix: `_v1.py` (when v2+ exists)
- Prefix: `old_*.py`, `deprecated_*.py`
- Contains: `legacy`, `obsolete`
- Date suffixes: `_20250101.py` (older than current versions)

**Example:**
```python
registry_writer.py          # Current
registry_writer_old.py      # ❌ Deprecated (has "_old")
registry_writer_v1.py       # ❌ Deprecated (v1 exists with v2)
```

---

### **3. Code Comments & Docstrings**
Check file headers for deprecation notices:

**Look for:**
```python
# DEPRECATED: Use registry_writer_service_v2.py instead
# STATUS: Deprecated as of 2026-02-16
# SUPERSEDED BY: P_01260207233100000335_registry_writer_service_v2.py
# NOTE: This file is kept for reference only
"""
DEPRECATED - DO NOT USE
Replaced by: ...
"""
```

**Common phrases:**
- "DEPRECATED"
- "DO NOT USE"
- "Superseded by"
- "Replaced by"
- "Obsolete"
- "Legacy code"
- "Archived"

---

### **4. Import Analysis**
Files that import from deprecated locations:

**Red Flags:**
```python
# Imports from archived directories
from Archive_Gov_Reg.old_module import something

# Imports deprecated modules
import deprecated_module

# Has "MIGRATION NOTE" comments about imports
# MIGRATION NOTE: This import will be removed
```

---

### **5. Duplicate Detection**
Multiple versions of the same functionality:

**Indicators:**
- Same base name with version numbers: `script_v1.py`, `script_v2.py`
- Same functionality in different locations
- Similar file sizes and structures
- Newer modification dates on one version

**How I detected duplication in your scripts:**
```
# Multiple registry writers found:
registry_writer.py                    (older)
registry_writer_service.py            (older)
registry_writer_service_v2.py         (✅ current)

# Multiple normalizers found:
normalizer.py
normalizer_v2.py
text_normalizer.py                    (✅ keep newest/most complete)
```

---

### **6. Last Modified Date**
Very old files with no recent updates:

**Analysis:**
```powershell
# Files not modified in 6+ months may be deprecated
Get-ChildItem -Recurse | Where-Object {
    \.LastWriteTime -lt (Get-Date).AddMonths(-6)
}
```

**Combined with:**
- Existence of newer versions
- Location in non-active directories
- No recent git commits

---

### **7. Git History / Commit Messages**
Git commits often document deprecation:

**Search for:**
```bash
git log --all --grep="deprecate"
git log --all --grep="obsolete"
git log --all --grep="supersede"
git log --all --grep="remove.*old"
git log --all --grep="consolidate"
```

**Example commit messages:**
- "Deprecate old registry_writer.py"
- "Archive legacy scripts"
- "Consolidate duplicate implementations"
- "Remove obsolete validation logic"

---

### **8. README / Documentation**
Check documentation files:

**Look in:**
- README.md files
- CHANGELOG.md files
- DEPRECATION.md files
- Architecture docs
- Migration guides

**Example from your system:**
```markdown
# CONSOLIDATION_COMPLETE_*.md
Lists all deprecated scripts after consolidation

# DEPRECATION_ANALYSIS_*.md
Documents deprecated code patterns
```

---

### **9. Registry/Manifest Checks**
Check if file is tracked as deprecated:

**Your system has:**
```json
// governance_registry_unified.json
{
  "files": [
    {
      "file_id": "...",
      "status": "deprecated",  // ❌ Marked as deprecated
      "superseded_by": "01260207233100000335"
    }
  ]
}
```

**Status values indicating deprecation:**
- `status: "deprecated"`
- `status: "archived"`
- `status: "obsolete"`
- `superseded_by` field present

---

### **10. Usage Analysis**
Files never imported or called:

**Check:**
```powershell
# Search for imports of a file
Select-String -Path "*.py" -Pattern "import old_script"

# If no results → possibly unused/deprecated
```

**Dead code indicators:**
- No imports found in codebase
- No test files reference it
- No documentation mentions it
- No recent execution logs

---

## 🎯 How I Identified File #3 as Deprecated

**File:** `scanner_with_registry.py`  
**Path:** `Archive_Gov_Reg\id_scripts_deprecated\CONSOLIDATION_20260216_071402\`

**Evidence (7 indicators):**

### ✅ **1. Location** (Strongest indicator)
- In `Archive_Gov_Reg` folder
- In `id_scripts_deprecated` subfolder
- In `CONSOLIDATION_20260216_071402` (recent archive event)

### ✅ **2. Archive Timestamp**
- `CONSOLIDATION_20260216` = Feb 16, 2026
- Today's date: Feb 16, 2026
- **Recently archived today!**

### ✅ **3. Directory Name**
- `id_scripts_deprecated` explicitly says "deprecated"

### ✅ **4. Newer Alternative Exists**
- Functionality replaced by modular pipeline:
  - `P_01999000042260124023_scanner.py`
  - `P_01999000042260125110_populate_registry_dir_ids_enhanced.py`
  - `P_01260207233100000073_unified_ingest_engine.py`

### ✅ **5. Consolidation Event**
- CONSOLIDATION folder = scripts were consolidated
- Old versions moved to archive
- New canonical versions established

### ✅ **6. Documentation**
- `CONSOLIDATION_COMPLETE_*.md` documents this deprecation
- Lists this file as deprecated
- Explains why it was archived

### ✅ **7. Architectural Change**
- Old: Monolithic scanner workflow
- New: Modular pipeline approach
- Clear architectural evolution

---

## 🚨 False Positives to Avoid

### **Not Always Deprecated:**

**1. Backup Files**
```
file.py.backup  # Could be active backup strategy
file.py.bak     # Might be editor auto-save
```

**2. Version Numbers**
```
module_v2.py    # If no v3 exists, v2 might be current!
```

**3. Test Files**
```
test_old_behavior.py  # Testing legacy compatibility
```

**4. Historical Documentation**
```
old_design.md   # Historical record, not deprecated code
```

---

## ✅ Deprecation Confidence Levels

### **HIGH CONFIDENCE (3+ indicators):**
- ✅ In archive/deprecated directory
- ✅ Has "deprecated" in path/name
- ✅ Documentation says deprecated
- ✅ Newer version exists
- ✅ Recent consolidation event

**Action:** Safe to ignore/remove

---

### **MEDIUM CONFIDENCE (2 indicators):**
- ⚠️ Old modification date
- ⚠️ Not imported anywhere
- ⚠️ Duplicate functionality exists

**Action:** Investigate further, check documentation

---

### **LOW CONFIDENCE (1 indicator):**
- ⚠️ Only filename suggests deprecation
- ⚠️ Only location is suspicious

**Action:** Do NOT assume deprecated, verify with team

---

## 🔧 Recommended Deprecation Workflow

### **For Your System:**

**1. Check Location First:**
```powershell
# If path contains these → likely deprecated:
if (\ -match "Archive|deprecated|old|legacy|obsolete") {
    Write-Host "⚠️ Likely deprecated"
}
```

**2. Check Consolidation Docs:**
```powershell
# Read these files for deprecation info:
Get-Content "CONSOLIDATION_COMPLETE_*.md"
Get-Content "DEPRECATION_ANALYSIS_*.md"
Get-Content "README_CONSOLIDATION.md"
```

**3. Check Registry Status:**
```powershell
# Load registry and check status field
\ = Get-Content "01999000042260124503_governance_registry_unified.json" | ConvertFrom-Json
\.files | Where-Object { \.status -eq "deprecated" }
```

**4. Verify Replacement:**
- Check if `superseded_by` field exists
- Verify newer version is active
- Confirm functionality is equivalent

---

## 📋 Summary: File #3 Deprecation Evidence

| Indicator | Status | Evidence |
|-----------|--------|----------|
| Location | ✅ YES | In `Archive_Gov_Reg\id_scripts_deprecated\` |
| Folder name | ✅ YES | Contains "deprecated" |
| Archive event | ✅ YES | `CONSOLIDATION_20260216_071402` |
| Newer version | ✅ YES | Replaced by modular pipeline |
| Documentation | ✅ YES | Listed in consolidation docs |
| Architectural change | ✅ YES | Monolithic → Modular |
| Recent timestamp | ✅ YES | Archived today (2026-02-16) |

**Confidence:** **VERY HIGH (7/7 indicators)**

**Conclusion:** File #3 is **definitively deprecated** and should NOT be used.

---

## 🎯 Quick Checklist

When evaluating if a file is deprecated:

- [ ] Is it in an Archive/deprecated folder?
- [ ] Does the filename contain deprecated/old/legacy?
- [ ] Does the code have deprecation comments?
- [ ] Is there a newer version elsewhere?
- [ ] Is the modification date very old?
- [ ] Does documentation say it's deprecated?
- [ ] Is it listed in CONSOLIDATION docs?
- [ ] Does registry mark it as deprecated?
- [ ] Is it never imported by other files?
- [ ] Was there a recent consolidation event?

**3+ Yes answers = High confidence it's deprecated**

---

**Generated:** 2026-02-16 08:12:08
