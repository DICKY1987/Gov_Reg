# PRE-REMEDIATION FIX REQUIRED ⚠️
**Created:** 2026-02-26T09:20:00Z  
**Priority:** CRITICAL - Must execute before REGISTRY_SPEC_REMEDIATION_EXECUTION_PLAN.md  
**Status:** BLOCKING ISSUES IDENTIFIED

---

## Executive Summary

**STOP:** Do not execute REGISTRY_SPEC_REMEDIATION_EXECUTION_PLAN.md yet. A recent directory reorganization (2026-02-25) has not been committed to git, causing every file path in the remediation plan to be incorrect or unstable.

**Root Cause:** Files moved from root → COLUMN_HEADERS/ and capability_system_scripts relocated, but changes are uncommitted (showing as D/deleted in git status with new locations untracked).

**Impact:** All git add commands in remediation plan will fail or target wrong paths.

---

## Issues Identified

### 🔴 ISSUE 1: CRITICAL - File Paths Are Wrong (All Phases Blocked)

**Problem:**
```
Remediation plan expects:
  COLUMN_HEADERS\01260207201000000193_UNIFIED_SSOT_REGISTRY_WRITE_POLICY.yaml
  COLUMN_HEADERS\01260207201000000192_UNIFIED_SSOT_REGISTRY_DERIVATIONS.yaml
  COLUMN_HEADERS\01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json

Git currently shows:
  D 01260207201000000192_UNIFIED_SSOT_REGISTRY_DERIVATIONS.yaml (deleted from root)
  D 01260207201000000193_UNIFIED_SSOT_REGISTRY_WRITE_POLICY.yaml (deleted from root)
  ?? COLUMN_HEADERS/ (entire directory untracked)
```

**Impact:** Every phase will fail at git add step.

**Fix Required:** Commit the directory reorganization first.

---

### 🟠 ISSUE 2: HIGH - capability_system_scripts Relocated

**Problem:**
```
Moved from: REGISTRY/capability_system_scripts/
Moved to:   REGISTRY/01260207201000001313_capability_mapping_system/capability_system_scripts/

Git status:
  D capability_system_scripts/P_01260207201000000865_...
  D capability_system_scripts/P_01260207201000000985_...
  D capability_system_scripts/P_01260207233100000464_...
```

**Impact:** capability_mapper.py pipeline will break if import paths aren't updated.

**Fix Required:** Commit relocation and verify imports.

---

### 🟡 ISSUE 3: MEDIUM - Incomplete COLUMN_DICTIONARY Updates

**Problem:** Phase 1 adds `py_capability_facts_hash` and `py_capability_tags` to:
- ✅ WRITE_POLICY.yaml
- ✅ DERIVATIONS.yaml  
- ✅ governance_registry_schema.v3.json
- ❌ COLUMN_DICTIONARY.json (missing!)

**Impact After Execution:**
- COLUMN_DICTIONARY: 184 fields
- Schema/Policy: 186 fields
- New fields lack scope, serialization, precedence_group

**Fix Required:** Add Phase 1B to register fields in COLUMN_DICTIONARY.

---

### 🟡 ISSUE 4: MEDIUM - Dual Metadata Sources (No Cross-Reference)

**Problem:** Two files define column metadata for py_* fields:
1. `COLUMN_DICTIONARY.json` (scope, serialization, precedence)
2. `01260207220000001318_mapp_py/01260202173939000019_Column to Script Mapping.json` (producer scripts, dependencies, phases)

Neither references the other.

**Impact:** Metadata drift risk - changes to one won't propagate to the other.

**Fix Required:** Add cross-reference comments in both files.

---

### 🟡 ISSUE 5: MEDIUM - Multiple Backup Sources

**Problem:**
- Existing: `archive/pre_cleanup_20260225_173348/`
- Plan creates: `01260207201000001133_backups/REGISTRY_pre_spec_remediation_*`

No documented relationship between them.

**Impact:** Rollback confusion if remediation fails.

**Fix Required:** Document backup hierarchy.

---

### 🔵 ISSUE 6: LOW - Git Add Path Mismatch

**Problem:** Plan uses `git add COLUMN_HEADERS\...` but git doesn't know COLUMN_HEADERS/ exists yet (untracked).

**Impact:** Commits won't contain expected files.

**Fix Required:** Stage directory move before remediation.

---

### 🔵 ISSUE 7: LOW - Field Count Discrepancy

**Problem:** Plan claims "185/185 fields" but Column to Script Mapping.json defines additional fields:
- `py_analysis_run_id`
- `py_quality_score`
- `py_overlap_group_id`
- `py_ast_dump_hash`
- ...and more

**Impact:** Success metrics incomplete.

**Fix Required:** Reconcile field counts between COLUMN_DICTIONARY and mapp_py.

---

## REQUIRED PRE-REMEDIATION STEPS

### Step 1: Commit Directory Reorganization (15 min) 🔴 BLOCKING

```powershell
cd C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY

# Stage all moved files
git add -A

# Verify staging
git status
# Should show:
#   renamed: 01260207201000000192_UNIFIED_SSOT_REGISTRY_DERIVATIONS.yaml -> COLUMN_HEADERS/01260207201000000192_...
#   renamed: 01260207201000000193_UNIFIED_SSOT_REGISTRY_WRITE_POLICY.yaml -> COLUMN_HEADERS/01260207201000000193_...
#   renamed: capability_system_scripts/ -> 01260207201000001313_capability_mapping_system/capability_system_scripts/
#   deleted: (7 files from root)
#   new file: COLUMN_HEADERS/ (directory)

# Commit reorganization
git commit -m "refactor: Reorganize REGISTRY directory structure - move specs to COLUMN_HEADERS"
```

**Verification:**
```powershell
# Should return 0 deleted files
git status --short | Select-String "^D "

# Should find files in new location
Test-Path "COLUMN_HEADERS\01260207201000000193_UNIFIED_SSOT_REGISTRY_WRITE_POLICY.yaml"
# Expect: True
```

---

### Step 2: Verify capability_mapper.py Imports (10 min) 🟠

```powershell
# Check if imports are broken
cd C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY\01260207201000001313_capability_mapping_system

# Search for old import paths
Select-String -Path "P_01260207220000001315_capability_mapper.py" `
              -Pattern "capability_system_scripts" -Context 2,2

# If found, update to new relative path:
# OLD: from capability_system_scripts.P_...
# NEW: from .capability_system_scripts.P_...
```

**If imports need updating:**
```powershell
# Test import paths
python -c "import sys; sys.path.insert(0, '01260207201000001313_capability_mapping_system'); from capability_system_scripts.P_01260207201000000985_P_01260207233100000YYY_registry_promoter import RegistryPromoter; print('✓ Imports work')"
```

---

### Step 3: Add py_capability_* to COLUMN_DICTIONARY (15 min) 🟡

**File:** `COLUMN_HEADERS\01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json`

Add these entries to the `headers` object:

```json
"py_capability_facts_hash": {
  "display_name": "Python Capability Facts Hash",
  "description": "SHA-256 hash of capability facts extracted from Python file for change detection",
  "value_schema": {
    "type": ["string", "null"],
    "pattern": "^[0-9a-f]{64}$"
  },
  "scope": {
    "record_kinds_in": ["entity"]
  },
  "source": "computed",
  "producer": "mapp_py.capability_detector.py + compute_sha_256_hash_of_evidence.py",
  "derivation_policy": "recompute_on_build",
  "null_meaning": "Not a Python file or analysis not run",
  "cross_reference": "See 01260207220000001318_mapp_py/01260202173939000019_Column to Script Mapping.json for producer details"
},
"py_capability_tags": {
  "display_name": "Python Capability Tags",
  "description": "Controlled vocabulary capability tags derived from Python code analysis",
  "value_schema": {
    "type": "array",
    "items": {"type": "string"}
  },
  "scope": {
    "record_kinds_in": ["entity"]
  },
  "serialization": {
    "flat_table": {
      "strategy": "json_array_string",
      "separator": ",",
      "max_display_length": 200
    }
  },
  "source": "computed",
  "producer": "mapp_py.capability_detector.py",
  "derivation_policy": "recompute_on_build",
  "null_meaning": "Not a Python file or analysis not run",
  "controlled_vocabulary": ["data_processing", "api", "cli", "database", "testing", "async", "ml_ai", "web_scraping", "file_io", "logging", "configuration", "security"],
  "precedence_group": "python_analysis",
  "cross_reference": "See 01260207220000001318_mapp_py/01260202173939000019_Column to Script Mapping.json for producer details"
}
```

**Commit:**
```powershell
git add COLUMN_HEADERS\01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json
git commit -m "docs: Add py_capability_* fields to COLUMN_DICTIONARY with cross-references"
```

---

### Step 4: Add Cross-Reference to Column to Script Mapping (10 min) 🟡

**File:** `01260207201000001313_capability_mapping_system\01260207220000001318_mapp_py\01260202173939000019_Column to Script Mapping.json`

Add at top of JSON (after opening brace):

```json
{
  "_metadata": {
    "description": "Mapping of registry columns to mapp_py producer scripts",
    "cross_reference": "This file defines production pipeline metadata. For schema validation, scope, and serialization rules, see ../../COLUMN_HEADERS/01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json",
    "authority": {
      "producer_scripts": "this_file",
      "schema_validation": "COLUMN_DICTIONARY.json",
      "write_policy": "UNIFIED_SSOT_REGISTRY_WRITE_POLICY.yaml",
      "derivation_formulas": "UNIFIED_SSOT_REGISTRY_DERIVATIONS.yaml"
    },
    "last_updated": "2026-02-26T09:20:00Z"
  },
  "scripts": [
    ...existing content...
```

**Commit:**
```powershell
git add 01260207201000001313_capability_mapping_system\01260207220000001318_mapp_py\01260202173939000019_Column to Script Mapping.json
git commit -m "docs: Add cross-reference to COLUMN_DICTIONARY for metadata authority"
```

---

### Step 5: Document Backup Hierarchy (5 min) 🟡

**Create:** `BACKUP_HIERARCHY.md` in REGISTRY root

```markdown
# Registry Backup Hierarchy

## Active Backups

### 1. Pre-Cleanup Archive (2026-02-25)
**Location:** `archive/pre_cleanup_20260225_173348/`  
**Contents:**
- 01260207233100000466_geu_sets.regenerated.json
- 01999000042260124503_REGISTRY_file.json
- registry_decontamination_report_20260225_173348.json

**Purpose:** Snapshot before directory reorganization  
**Restore Command:**
```powershell
Copy-Item archive/pre_cleanup_20260225_173348/* . -Force
```

### 2. Pre-Remediation Backup (Upcoming)
**Location:** `C:\Users\richg\Gov_Reg\01260207201000001133_backups\REGISTRY_pre_spec_remediation_*`  
**Purpose:** Full directory backup before specification remediation  
**Created By:** REGISTRY_SPEC_REMEDIATION_EXECUTION_PLAN.md Pre-Flight step

## Backup Priority

If rollback needed:
1. **First:** Use git revert/reset (cleanest)
2. **Second:** Restore from Pre-Remediation Backup (full directory)
3. **Last Resort:** Restore from Pre-Cleanup Archive (partial, data files only)
```

**Commit:**
```powershell
git add BACKUP_HIERARCHY.md
git commit -m "docs: Document backup hierarchy and restore priority"
```

---

### Step 6: Update Remediation Plan Paths (10 min) 🟠

**Action:** The REGISTRY_SPEC_REMEDIATION_EXECUTION_PLAN.md already uses correct paths (`COLUMN_HEADERS\...`), but these only work AFTER Step 1 is complete.

**Add warning banner to plan:**

```powershell
# Insert at top of REGISTRY_SPEC_REMEDIATION_EXECUTION_PLAN.md
```

```markdown
---
## ⚠️ PRE-REQUISITE: DIRECTORY REORGANIZATION MUST BE COMMITTED FIRST

**STOP:** Before executing this plan, verify the following:

1. ✅ COLUMN_HEADERS/ directory exists and is git-tracked
2. ✅ No files showing as "D" (deleted) in root that plan references
3. ✅ `git status` shows clean or only COUNTER_STORE.json modified
4. ✅ PRE_REMEDIATION_FIX_REQUIRED.md Steps 1-5 completed

**To verify:**
```powershell
cd C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY
git status --short | Select-String "^D.*UNIFIED_SSOT"
# Should return NOTHING (0 results)

Test-Path "COLUMN_HEADERS\01260207201000000193_UNIFIED_SSOT_REGISTRY_WRITE_POLICY.yaml"
# Should return True
```

**If verification fails:** Execute PRE_REMEDIATION_FIX_REQUIRED.md first.

---
```

**Commit:**
```powershell
git add REGISTRY_SPEC_REMEDIATION_EXECUTION_PLAN.md
git commit -m "docs: Add pre-requisite verification to remediation plan"
```

---

### Step 7: Reconcile Field Counts (15 min) 🔵 OPTIONAL

**Action:** Audit all py_* fields across both metadata files.

```powershell
# Count fields in COLUMN_DICTIONARY
python -c "import json; d=json.load(open('COLUMN_HEADERS/01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json')); py_fields=[k for k in d['headers'].keys() if k.startswith('py_')]; print(f'COLUMN_DICTIONARY py_* fields: {len(py_fields)}')"

# Count fields in Column to Script Mapping
python -c "import json; d=json.load(open('01260207201000001313_capability_mapping_system/01260207220000001318_mapp_py/01260202173939000019_Column to Script Mapping.json')); cols=set(); [cols.update(s['columns_produced']) for s in d['scripts']]; py_cols=[c for c in cols if c.startswith('py_')]; print(f'Column to Script Mapping py_* fields: {len(py_cols)}')"

# Find discrepancies
python -c "
import json
col_dict = json.load(open('COLUMN_HEADERS/01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json'))
script_map = json.load(open('01260207201000001313_capability_mapping_system/01260207220000001318_mapp_py/01260202173939000019_Column to Script Mapping.json'))

dict_fields = set(k for k in col_dict['headers'].keys() if k.startswith('py_'))
map_cols = set()
for script in script_map['scripts']:
    map_cols.update(script['columns_produced'])
map_fields = set(c for c in map_cols if c.startswith('py_'))

print(f'In mapp_py but not COLUMN_DICTIONARY: {sorted(map_fields - dict_fields)}')
print(f'In COLUMN_DICTIONARY but not mapp_py: {sorted(dict_fields - map_fields)}')
"
```

**Document findings:**

Create `FIELD_COVERAGE_AUDIT.md`:

```markdown
# Field Coverage Audit

**Date:** 2026-02-26  
**Purpose:** Reconcile py_* field definitions across metadata files

## Results

**COLUMN_DICTIONARY.json:** X py_* fields  
**Column to Script Mapping.json:** Y py_* fields  

### Fields in mapp_py but not COLUMN_DICTIONARY:
- (list any missing)

### Fields in COLUMN_DICTIONARY but not mapp_py:
- (list any missing)

### Recommendation:
- Add missing fields to COLUMN_DICTIONARY in future phases
- Update remediation plan success metrics to reflect actual counts
```

---

## Execution Checklist

### Critical Path (MUST complete before remediation)
- [ ] Step 1: Commit directory reorganization ✅ VERIFIED
- [ ] Step 2: Verify capability_mapper.py imports
- [ ] Step 3: Add py_capability_* to COLUMN_DICTIONARY

### High Priority (Strongly recommended)
- [ ] Step 4: Add cross-reference to Column to Script Mapping
- [ ] Step 5: Document backup hierarchy
- [ ] Step 6: Update remediation plan with pre-requisite warning

### Optional (Improves accuracy)
- [ ] Step 7: Reconcile field counts

---

## Post-Fix Verification

After completing Steps 1-6, run:

```powershell
cd C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY

# Verify git is clean (except COUNTER_STORE.json)
git status --short | Where-Object {$_ -notmatch "COUNTER_STORE"}
# Should show nothing or only untracked files

# Verify COLUMN_HEADERS/ exists and is tracked
git ls-files COLUMN_HEADERS/ | Measure-Object
# Should return Count > 0

# Verify py_capability_* in COLUMN_DICTIONARY
python -c "import json; d=json.load(open('COLUMN_HEADERS/01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json')); assert 'py_capability_facts_hash' in d['headers']; assert 'py_capability_tags' in d['headers']; print('✓ Fields registered')"

# Verify remediation plan has warning
Select-String -Path "REGISTRY_SPEC_REMEDIATION_EXECUTION_PLAN.md" -Pattern "PRE-REQUISITE.*COMMITTED FIRST"
# Should return match

# All checks passed? Proceed to remediation plan.
```

---

## Timeline

**Critical Path:** 40 minutes  
**Full Pre-Remediation:** 1 hour 20 minutes  

**Recommended:** Complete all steps except Step 7 (field count audit) before starting remediation. Step 7 can be done post-remediation for documentation purposes.

---

**Status:** READY TO EXECUTE  
**Next Step:** Execute Steps 1-6, then proceed to REGISTRY_SPEC_REMEDIATION_EXECUTION_PLAN.md
