# Unified Registry Cleanup & Remediation Plan
## Combined Optimal Execution Strategy

**Directory:** `C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY`  
**Created:** 2026-02-22T23:33:54Z  
**Revised:** 2026-02-22T23:55:43Z (final validation pass)  
**Status:** Ready for execution (remediation not yet started)  
**Total Estimated Time:** 12-16 hours (revised from 24h after realistic time assessment)  
**Breaking Changes:** Low-risk policy changes (see Compatibility Notes below)

---

## Executive Summary

This plan combines:
1. **Physical cleanup** - Remove duplicates, cache, organize files (Phases A1-A7)
2. **Specification remediation** - Fix schema inconsistencies (Phases B1-B9)

**Key Finding:** Remediation plan not yet started (no `py_*` entries found in WRITE_POLICY.yaml)

---

## Compatibility Notes

**Potentially Breaking Changes:**
1. **Phase B4:** Fields changed from `manual_or_automated` → `manual_patch_only` may break automated tools expecting write access to `description`, `one_line_purpose`, `short_description`, `superseded_by`, `supersedes_entity_id`, `bundle_version`
   - **Mitigation:** Review automation before B4; add compatibility shims if needed
2. **Phase B6:** `data_transformation` type tightened from `boolean|string|null` → `string|null` 
   - **Risk:** If any records have `data_transformation: true/false`, validation will fail
   - **Mitigation:** Pre-check live data in B6.1 before schema change
3. **Phase B8:** `rel_type` deprecated in favor of `edge_type`
   - **Mitigation:** B8.0 code search required; existing reads still work (field not removed)

**All other changes are purely additive or organizational.**

---

## Pre-Flight: File Authority Verification (15 min)

**Status:** ✅ COMPLETED

### Registry Files Found:
| File | Hash | Status |
|------|------|--------|
| `01999000042260124503_REGISTRY_file.json` | 41849220... | **LIVE DATA - READ ONLY** |
| `01999000042260124012_governance_registry_schema.v3.json` | 8DC527E1... | **ACTIVE SCHEMA** |
| Backup schemas (2 copies) | 91E18932... | Duplicates - safe to archive |
| Backup unified (2 copies) | DFC455398..., B64A21CA... | Old backups - safe to archive |

**Decision:** Root-level files are authoritative. Backup copies can be safely archived.

---

## STAGE 1: SAFE FOUNDATION WORK (Risk: ZERO)
**Duration:** 1 hour  
**Can run independently in parallel**

---

### **Phase A1: Remove Cache & Temporary Files** (10 min)
**Risk:** ZERO | **Space Saved:** ~0.1 MB

**Actions:**
```powershell
# Remove pytest cache
Remove-Item -Recurse -Force "C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY\.pytest_cache"

# Remove stale lock files
Remove-Item "C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY\01999000042260124026_REGISTRY_file.lock"
Remove-Item "C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY\01260207201000001269_reservations\RES-TESTPLAN001.json.lock"
```

**Verification:**
```powershell
Test-Path "C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY\.pytest_cache"  # Should be False
```

---

### **Phase A2: Cleanup Redundant .dir_id Files** (15 min)
**Risk:** ZERO | **Files Removed:** ~15

**Actions:**
```powershell
# Remove .dir_id from backup directories (not needed)
Get-ChildItem -Path "C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY\01260207201000001253_BACKUP_FILES" -Recurse -Filter ".dir_id" | Remove-Item -Force

# Remove .dir_id from pytest cache (already deleting cache)
# (covered by Phase A1)
```

**Keep .dir_id in:**
- Active working directories (scripts, src_modules, tests, etc.)
- Root REGISTRY directory

**Verification:**
```powershell
Get-ChildItem -Path "C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY\01260207201000001253_BACKUP_FILES" -Recurse -Filter ".dir_id" | Measure-Object | Select Count  # Should be 0
```

---

### **Phase A3: Archive Pre-Apply State Files** (10 min)
**Risk:** LOW | **Files Moved:** 3

These are one-time backup files from a previous operation:
- `01260207201000000831_.pre_apply_backup_path.txt`
- `01260207201000000832_.pre_apply_backup_timestamp.txt`
- `01260207201000000833_.pre_apply_state.json`

**Actions:**
```powershell
# Move to backup directory
Move-Item "C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY\01260207201000000831_.pre_apply_backup_path.txt" `
          "C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY\01260207201000001253_BACKUP_FILES\"
Move-Item "C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY\01260207201000000832_.pre_apply_backup_timestamp.txt" `
          "C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY\01260207201000001253_BACKUP_FILES\"
Move-Item "C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY\01260207201000000833_.pre_apply_state.json" `
          "C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY\01260207201000001253_BACKUP_FILES\"
```

---

### **Phase A4: Organize Scripts** (10 min)
**Risk:** ZERO

**Actions:**
```powershell
# Move cleanup scripts to scripts directory
Move-Item "C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY\01260207233100000388_cleanup_duplicates.ps1" `
          "C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY\01260207201000001270_scripts\"
Move-Item "C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY\consolidate_registry_files.ps1" `
          "C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY\01260207201000001270_scripts\"
```

---

## STAGE 2: CRITICAL SCHEMA FIXES (Risk: LOW-MEDIUM)
**Duration:** 2.5 hours  
**Must complete before data validation**

---

### **Phase B1: Register `py_*` Fields** ⚠️ CRITICAL (1.5 hours)
**Risk:** LOW-MEDIUM | **Priority:** HIGHEST | **Addresses:** Active Violation B5

**Problem:** Python analysis fields exist in live data but have zero spec coverage. JSON schema validation fails, write policy rejects Python records.

**Files to modify:**
1. `01260207201000000193_UNIFIED_SSOT_REGISTRY_WRITE_POLICY.yaml`
2. `01260207201000000192_UNIFIED_SSOT_REGISTRY_DERIVATIONS.yaml`
3. `01999000042260124012_governance_registry_schema.v3.json`

#### **B1.0: DATA-DRIVEN FIELD DISCOVERY** ⚠️ REQUIRED FIRST

**DO NOT use hardcoded field list. Discover actual fields from live data:**

```python
import json

# Discover all py_* fields actually in use
reg = json.load(open("01999000042260124503_REGISTRY_file.json"))
schema = json.load(open("01999000042260124012_governance_registry_schema.v3.json"))

# Find all py_* fields in live data
py_fields_in_data = set()
for record in reg["files"]:
    for key in record.keys():
        if key.startswith("py_"):
            py_fields_in_data.add(key)

# Find py_* fields already in schema
schema_keys = set(schema["definitions"]["FileRecord"]["properties"].keys())
py_fields_in_schema = {k for k in schema_keys if k.startswith("py_")}

# Fields that need registration
missing_py_fields = py_fields_in_data - py_fields_in_schema

print(f"Total py_* fields in live data: {len(py_fields_in_data)}")
print(f"Already in schema: {len(py_fields_in_schema)}")
print(f"Need to register: {len(missing_py_fields)}")
print(f"\nFields to add: {sorted(missing_py_fields)}")

# Infer types from data
for field in sorted(missing_py_fields):
    values = [r.get(field) for r in reg["files"] if field in r]
    types = set(type(v).__name__ for v in values if v is not None)
    print(f"  {field}: {types}")
```

**DECISION POINT:** If count differs from expected ~37, STOP and review. The plan's hardcoded list may be stale.

#### **B1.1: Update WRITE_POLICY.yaml**

Append 37 entries with pattern:
```yaml
  py_<field>:
    rationale: <one-line description>
    null_policy: allow_null
    update_policy: recompute_on_build
    writable_by: tool_only
```

Array fields also get:
```yaml
    merge_strategy: set_union
```

#### **B1.2: Update DERIVATIONS.yaml**

Append 37 entries with INPUT passthrough pattern:
```yaml
  py_<field>:
    depends_on: []
    error_policy: set_null
    type: string|boolean|integer|number|array  # per field
    trigger: recompute_on_build
    null_behavior: allow  # or set_empty_array for arrays
    formula: COALESCE(INPUT.py_<field>, NULL)
    rationale: Provided directly by Python analysis tool; null for non-Python files
```

**Type mapping:**
- **string|null:** run_id, timestamps, hashes, path, group_id, match_file_id
- **boolean|null:** analysis_success, ast_parse_ok, tests_executed
- **integer|null:** defs counts, component_count, pytest_exit_code, static_issues_count
- **number|null:** quality_score, coverage_percent, similarity_max, candidate_score, cyclomatic
- **array:** capability_tags, component_ids, deliverable_kinds/inputs/outputs/interfaces, imports_*, io_surface_flags, security_risk_flags, tool_versions

#### **B1.3: Update governance_registry_schema.v3.json**

Add all 37 properties to `definitions.FileRecord.properties`:

```json
"py_analysis_run_id": {"type": ["string", "null"]},
"py_analysis_success": {"type": ["boolean", "null"]},
"py_analyzed_at_utc": {"type": ["string", "null"], "format": "date-time"},
"py_capability_tags": {"type": "array", "items": {"type": "string"}},
"py_coverage_percent": {"type": ["number", "null"], "minimum": 0, "maximum": 100},
...
```

**Verification:**
```powershell
# Count new entries (use actual discovered count, not hardcoded 37)
Select-String -Path "01260207201000000193_UNIFIED_SSOT_REGISTRY_WRITE_POLICY.yaml" -Pattern "^  py_" | Measure-Object
Select-String -Path "01260207201000000192_UNIFIED_SSOT_REGISTRY_DERIVATIONS.yaml" -Pattern "^  py_" | Measure-Object

# Validate schema against live data
python -m jsonschema --instance 01999000042260124503_REGISTRY_file.json 01999000042260124012_governance_registry_schema.v3.json
```

**Git Checkpoint:**
```powershell
# Capture count first (Python variable won't work in PowerShell)
$pyFieldCount = (Select-String -Path "01260207201000000193_UNIFIED_SSOT_REGISTRY_WRITE_POLICY.yaml" -Pattern "^  py_").Count

git add 01260207201000000193_UNIFIED_SSOT_REGISTRY_WRITE_POLICY.yaml `
        01260207201000000192_UNIFIED_SSOT_REGISTRY_DERIVATIONS.yaml `
        01999000042260124012_governance_registry_schema.v3.json
git commit -m "B1: Register py_* fields from live data ($pyFieldCount fields)"
```

---

### **Phase B2: Add Undeclared Fields to Schema** ⚠️ HIGH PRIORITY (1 hour)
**Risk:** LOW | **Addresses:** Active Violation B7

**Problem:** Fields used in live records but absent from `FileRecord.properties`. Causes `additionalProperties` validation failures.

#### **B2.1: Discover Undeclared Fields** ⚠️ DATA-DRIVEN

```python
import json
reg = json.load(open("01999000042260124503_REGISTRY_file.json"))
schema = json.load(open("01999000042260124012_governance_registry_schema.v3.json"))
schema_keys = set(schema["definitions"]["FileRecord"]["properties"].keys())
live_keys = set(k for r in reg["files"] for k in r.keys())
undeclared = live_keys - schema_keys
print(f"Undeclared fields ({len(undeclared)}): {sorted(undeclared)}")

# Infer types for each undeclared field
for field in sorted(undeclared):
    values = [r.get(field) for r in reg["files"] if field in r]
    non_null_values = [v for v in values if v is not None]
    types = set(type(v).__name__ for v in non_null_values)
    unique_vals = set(non_null_values) if len(non_null_values) < 20 else f"{len(set(non_null_values))} unique"
    print(f"  {field}: types={types}, sample={unique_vals}")
```

**DECISION POINT:** Review output. If fields differ from expected (`record_kind`, `one_line_purpose`, `notes`, `short_description`, `status`, `entity_kind`, `scope`, `created_by`), STOP and assess impact before proceeding.

#### **B2.2: Update governance_registry_schema.v3.json**

Add each confirmed field to `FileRecord.properties`:

```json
"record_kind": {
  "type": "string",
  "enum": ["entity", "edge", "metadata", "generator"]
},
"one_line_purpose": {
  "type": ["string", "null"],
  "maxLength": 120
},
"notes": {
  "type": ["string", "null"]
},
"status": {
  "type": ["string", "null"],
  "enum": ["active", "archived", "deprecated", "legacy_read_only", null]
},
"entity_kind": {
  "type": ["string", "null"]
},
"scope": {
  "type": ["string", "null"]
},
"short_description": {
  "type": ["string", "null"],
  "maxLength": 250
},
"created_by": {
  "type": ["string", "null"]
}
```

**Verification:**
```powershell
python -m jsonschema --instance 01999000042260124503_REGISTRY_file.json 01999000042260124012_governance_registry_schema.v3.json
# Expect 0 additionalProperties errors
```

**Git Checkpoint:**
```powershell
# Run discovery script to get count, then commit
python -c "import json; reg=json.load(open('01999000042260124503_REGISTRY_file.json')); schema=json.load(open('01999000042260124012_governance_registry_schema.v3.json')); print(len(set(k for r in reg['files'] for k in r.keys()) - set(schema['definitions']['FileRecord']['properties'].keys())))" > .undeclared_count.tmp
$undeclaredCount = Get-Content .undeclared_count.tmp
Remove-Item .undeclared_count.tmp

git add 01999000042260124012_governance_registry_schema.v3.json
git commit -m "B2: Add undeclared fields to schema ($undeclaredCount fields)"
```

---

## STAGE 3: FILE DEDUPLICATION (Risk: LOW)
**Duration:** 1 hour  
**Now safe - authority established**

---

### **Phase A5: Resolve Duplicate Schema Files** (30 min)
**Risk:** LOW | **Space Saved:** ~0.5 MB

**Duplicates identified:**
1. `governance_registry_schema.v3.json` - 1 root + 1 backup copy
2. `governance_registry_unified.json` - Multiple backup copies

**Actions:**
```powershell
# Verify root files are most recent
$rootSchema = Get-Item "C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY\01999000042260124012_governance_registry_schema.v3.json"
$backupSchemas = Get-ChildItem -Path "C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY\01260207201000001253_BACKUP_FILES" -Recurse -Filter "*governance_registry*.json"

# Keep only root versions, remove backup duplicates
foreach ($backup in $backupSchemas) {
    Write-Host "Removing duplicate: $($backup.FullName)"
    Remove-Item $backup.FullName -Force
}
```

**Keep:**
- `01999000042260124503_REGISTRY_file.json` (live data)
- `01999000042260124012_governance_registry_schema.v3.json` (active schema)

**Verification:**
```powershell
Get-ChildItem -Path "C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY" -Recurse -Filter "*governance_registry*.json" | Measure-Object | Select Count
# Should be 2 (live data + schema only)
```

---

### **Phase A6: Consolidate Test Directories** (30 min)
**Risk:** LOW

**Problem:** Two test directories exist:
- `01260207201000001273_TEST`
- `01260207201000001274_tests`

**Actions:**
```powershell
# CHECK FOR NAME COLLISIONS FIRST
$testFiles = Get-ChildItem "C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY\01260207201000001273_TEST" -Recurse -File
$testsFiles = Get-ChildItem "C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY\01260207201000001274_tests" -Recurse -File

$testNames = $testFiles | ForEach-Object { $_.Name }
$testsNames = $testsFiles | ForEach-Object { $_.Name }
$collisions = $testNames | Where-Object { $testsNames -contains $_ }

if ($collisions.Count -gt 0) {
    Write-Warning "NAME COLLISIONS DETECTED: $($collisions -join ', ')"
    Write-Warning "MANUAL REVIEW REQUIRED. Stopping A6."
    # DECISION POINT: Review collisions, rename or merge manually
} else {
    # Safe to proceed - no collisions
    Get-ChildItem "C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY\01260207201000001273_TEST" | 
        Move-Item -Destination "C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY\01260207201000001274_tests"
    
    # Remove empty TEST directory
    Remove-Item "C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY\01260207201000001273_TEST" -Recurse -Force
}
```

**Verification:**
```powershell
Test-Path "C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY\01260207201000001273_TEST"  # Should be False
Test-Path "C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY\01260207201000001274_tests"  # Should be True
```

---

**Git Checkpoint:**
```powershell
# Stage only REGISTRY directory changes (not full repo)
Push-Location "C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY"
git add .
git commit -m "A5-A6: Remove duplicate schemas, consolidate test directories"
Pop-Location
```

---

## STAGE 4: SPECIFICATION CONSISTENCY (Risk: LOW)
**Duration:** 2.5 hours (revised from 6h)

---

### **Phase B3: Fix Immutable Fields Without Derivations** (20 min)
**Risk:** LOW | **Addresses:** Formula Sheet B1

**Problem:** 9 INPUT-passthrough fields are set once at creation but lack derivation entries.

**Fields:** `created_by`, `directionality`, `edge_type`, `record_kind`, `rel_type`, `source_entity_id`, `source_file_id`, `target_entity_id`, `target_file_id`

**Actions:**

Update `01260207201000000192_UNIFIED_SSOT_REGISTRY_DERIVATIONS.yaml`:

```yaml
  created_by:
    depends_on: []
    error_policy: set_null
    type: string
    trigger: on_create_only
    null_behavior: allow
    formula: COALESCE(INPUT.created_by, NULL)
    rationale: User or tool that created the record; set at creation time only

  edge_type:
    depends_on: []
    error_policy: fail
    type: string
    trigger: on_create_only
    null_behavior: error
    formula: INPUT.edge_type
    rationale: Required edge relationship type; immutable after creation

  # ... repeat for remaining 7 fields
```

**Verification:**
```powershell
# Check if formula sheet generator exists first
if (Test-Path "scripts/generate_formula_sheet.py") {
    python scripts/generate_formula_sheet.py
    # Expect 0 rows with "immutable but no derivation"
} else {
    Write-Warning "Formula sheet generator not found - manual verification needed"
    # Manual: grep for immutable fields without trigger: on_create_only
}
```

**Git Checkpoint:**
```powershell
git add 01260207201000000192_UNIFIED_SSOT_REGISTRY_DERIVATIONS.yaml
git commit -m "B3: Add derivations for 9 immutable fields"
```

---

### **Phase B4: Reclassify manual_or_automated Fields** (15 min)
**Risk:** LOW-MEDIUM | **Addresses:** Formula Sheet B2

**Problem:** ~6 fields marked `manual_or_automated` have no derivation formula. They should be `manual_patch_only`.

**Confirmed changes:**
- `description`
- `one_line_purpose`
- `short_description`
- `superseded_by`
- `supersedes_entity_id`
- `bundle_version`

**Actions:**

Update `01260207201000000193_UNIFIED_SSOT_REGISTRY_WRITE_POLICY.yaml`:

```yaml
  description:
    rationale: Long-form documentation (max 2000 chars)
    null_policy: allow_null
    update_policy: manual_patch_only  # Changed from manual_or_automated
    writable_by: authorized_user

  # ... repeat for remaining 5 fields
```

**Verification:**
```powershell
Select-String -Path "01260207201000000193_UNIFIED_SSOT_REGISTRY_WRITE_POLICY.yaml" -Pattern "manual_or_automated" | 
    Where-Object { $_.Line -match "(description|one_line_purpose|short_description|superseded_by|supersedes_entity_id|bundle_version)" }
# Should return 0 matches
```

**Git Checkpoint:**
```powershell
git add 01260207201000000193_UNIFIED_SSOT_REGISTRY_WRITE_POLICY.yaml
git commit -m "B4: Reclassify 6 fields from manual_or_automated to manual_patch_only"
```

---

### **Phase B7: Path Precedence & path_aliases Derivation** (30 min)
**Risk:** LOW | **Addresses:** C8

**Actions:**

#### B7.1: Document path precedence in DERIVATIONS.yaml

**⚠️ VALIDATOR COMPATIBILITY CHECK REQUIRED:**
Before adding `_metadata` key, verify the DERIVATIONS.yaml parser accepts non-field keys. If not, document precedence rules in a comment block or separate `FIELD_PRECEDENCE_RULES.md` file instead.

**Option A - If _metadata is supported:**
```yaml
# Metadata: Field Precedence Rules
# This section documents field precedence rules but is not processed as field definitions
_metadata:
  path_field_precedence:
    # When multiple path fields are present, use this order to determine canonical path:
    # 1. absolute_path (highest precedence - full filesystem path)
    # 2. relative_path (project-relative)
    # 3. canonical_path (normalized/simplified)
    # 4. directory_path (parent directory)
    # 5. filename (basename only)
    # 6. path_aliases (alternate names/symlinks)
    order: [absolute_path, relative_path, canonical_path, directory_path, filename, path_aliases]
  
  test_coverage_field_precedence:
    # For Python files where py_analysis_success=true:
    #   Python-specific fields are authoritative over general fields
    python_specific:
      precedence_group: test_coverage_python
      authoritative_for: ["*.py"]
      fields: [py_tests_executed, py_pytest_exit_code, py_coverage_percent]
    general:
      precedence_group: test_coverage_general
      fields: [has_tests, test_status, coverage_status]
```

**Option B - If _metadata not supported (use comment block):**
```yaml
# =============================================================================
# FIELD PRECEDENCE RULES (Documentation Only - Not Processed)
# =============================================================================
#
# Path Field Precedence:
#   When multiple path fields are present, use this order to determine canonical path:
#   1. absolute_path (highest precedence - full filesystem path)
#   2. relative_path (project-relative)
#   3. canonical_path (normalized/simplified)
#   4. directory_path (parent directory)
#   5. filename (basename only)
#   6. path_aliases (alternate names/symlinks)
#
# Test Coverage Field Precedence:
#   For Python files where py_analysis_success=true:
#   Python-specific fields (py_tests_executed, py_pytest_exit_code, py_coverage_percent)
#   are authoritative over general fields (has_tests, test_status, coverage_status)
#
# =============================================================================
```

**Recommended:** Test Option A with a dry-run validation before committing.

#### B7.2: Add path_aliases derivation

```yaml
  path_aliases:
    depends_on: []
    error_policy: set_null
    type: array
    trigger: manual_patch_only
    null_behavior: set_empty_array
    formula: COALESCE(INPUT.path_aliases, [])
    rationale: Alternate file paths or symlinks; manually maintained
```

#### B7.3: Update COLUMN_DICTIONARY.json

Ensure all 6 path fields have:
```json
"scope": {
  "record_kinds_in": ["entity"]
}
```

**Git Checkpoint:**
```powershell
git add 01260207201000000192_UNIFIED_SSOT_REGISTRY_DERIVATIONS.yaml `
        01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json
git commit -m "B7: Document path precedence and add path_aliases derivation"
```

---

### **Phase B9: Test Coverage Precedence** (30 min)
**Risk:** LOW | **Addresses:** C9 | **Depends on:** Phase B1, B7

**Problem:** Python-specific test fields conflict with general test fields.

**Actions:**

#### B9.1: Add test coverage precedence to DERIVATIONS.yaml

**Note:** This is already handled in B7.1 within the single `_metadata` block (or comment block if validator doesn't support `_metadata`). Do not add a second `_metadata` key - YAML will reject duplicate keys.

**Verify precedence documentation includes test coverage rules from B7.1.**

#### B9.2: Update COLUMN_DICTIONARY.json

Add to all 6 test coverage fields:
```json
"precedence_group": "test_coverage_general"  // or test_coverage_python
```

**Git Checkpoint:**
```powershell
git add 01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json
git commit -m "B9: Add test coverage precedence groups to COLUMN_DICTIONARY"
```

---

## STAGE 5: SCOPE & TYPE CORRECTIONS (Risk: LOW)
**Duration:** 4 hours (revised from 7h)

---

### **Phase B5: Fix Scope Issues** (1.5 hours)
**Risk:** LOW | **Addresses:** C4, C5

**Problems:**
- **C5:** 9 fields use invalid `"core"` in `record_kinds_in` enum
- **C4:** 40 fields have empty `record_kinds_in: []`

**Actions:**

Update `01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json`:

#### B5.1: Fix invalid "core" values (9 fields)

Replace `"core"` with `"entity"` in all occurrences.

#### B5.2: Assign scopes to empty fields (40 fields)

**Edge fields:**
```json
"edge_type": {
  "scope": {"record_kinds_in": ["edge"]}
},
"source_file_id": {
  "scope": {"record_kinds_in": ["edge"]}
},
// ... etc for all edge-specific fields
```

**Entity fields:**
```json
"file_id": {
  "scope": {"record_kinds_in": ["entity"]}
},
"sha256": {
  "scope": {"record_kinds_in": ["entity"]}
},
// ... etc for all entity-specific fields
```

**Universal fields:**
```json
"record_id": {
  "scope": {"record_kinds_in": ["entity", "edge", "generator", "metadata"]}
},
"created_utc": {
  "scope": {"record_kinds_in": ["entity", "edge", "generator", "metadata"]}
},
// ... etc
```

**Verification:**
```python
import json
d = json.load(open('01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json'))

# No empty scopes
empties = [h for h, v in d['headers'].items() if v.get('scope', {}).get('record_kinds_in') == []]
print(f"Empty scopes: {len(empties)}")  # expect 0

# No 'core' values
import re
with open('01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json') as f:
    content = f.read()
    core_count = len(re.findall(r'"core"', content))
    print(f"'core' occurrences: {core_count}")  # expect 0
```

**Git Checkpoint:**
```powershell
git add 01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json
git commit -m "B5: Fix scope issues (remove 'core', assign 40 empty scopes)"
```

---

### **Phase B6: Fix data_transformation Type & Add Serialization** (2.5 hours)
**Risk:** LOW | **Addresses:** C6, C7

**Problems:**
- **C6:** `data_transformation` incorrectly typed as `boolean|string|null` (should be `string|null`)
- **C7:** 35 array fields + 6 object fields lack flat-table serialization specs

**Actions:**

Update `01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json`:

#### B6.1: Fix data_transformation type

**⚠️ PRE-CHECK REQUIRED:** Verify no boolean values in live data before schema change:

```python
import json
reg = json.load(open('01999000042260124503_REGISTRY_file.json'))
boolean_values = [r.get('data_transformation') for r in reg['files'] 
                  if 'data_transformation' in r and isinstance(r['data_transformation'], bool)]
if boolean_values:
    print(f"WARNING: {len(boolean_values)} records have boolean data_transformation values")
    print("DECISION POINT: Migrate these to string or leave type as-is")
else:
    print("Safe to proceed - no boolean values found")
```

**If safe, update COLUMN_DICTIONARY.json:**

```json
"data_transformation": {
  "value_schema": {
    "type": ["string", "null"],
    "enum": ["normalize", "aggregate", "filter", "transform", "enrich", null]
  }
}
```

#### B6.2: Add serialization to array fields (35 fields)

For each array field, add (adjust max_display_length by field):
```json
"serialization": {
  "flat_table": {
    "strategy": "json_array_string",
    "separator": ",",
    "max_display_length": 200  // Use 500 for import fields (py_imports_*, imports_*)
  }
}
```

**Array fields include:** `capability_tags`, `component_ids`, `deliverable_kinds`, `py_imports_stdlib`, `py_capability_tags`, etc.

**NOTE:** Import-related fields (`py_imports_stdlib`, `py_imports_third_party`, `py_imports_local`, `imports_*`) should use `max_display_length: 500` due to longer module paths.

#### B6.3: Add serialization to object fields (6 fields)

For each object field, add:
```json
"serialization": {
  "flat_table": {
    "strategy": "json_object_string",
    "max_display_length": 500
  }
}
```

**Verification:**
```python
import json
d = json.load(open('01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json'))

# Check data_transformation type
dt_type = d['headers']['data_transformation']['value_schema']['type']
assert 'boolean' not in dt_type, "data_transformation still has boolean type"

# Check all array/object fields have serialization
for header, spec in d['headers'].items():
    val_type = spec.get('value_schema', {}).get('type', '')
    if 'array' in str(val_type) or 'object' in str(val_type):
        assert 'serialization' in spec, f"{header} missing serialization"
```

**Validate COLUMN_DICTIONARY structure:**
```powershell
# Check if column dictionary schema exists
if (Test-Path "schemas/column_dictionary_schema.json") {
    python -m jsonschema --instance 01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json schemas/column_dictionary_schema.json
} else {
    Write-Warning "No column dictionary schema found - manual review recommended"
}
```

**Git Checkpoint:**
```powershell
git add 01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json
git commit -m "B6: Fix data_transformation type and add serialization to 41 fields"
```

---

## STAGE 6: DESIGN DECISIONS (Risk: MEDIUM)
**Duration:** 4 hours  
**Run last - requires stakeholder review**

---

### **Phase B8: Structural Design Decisions** (2 hours)
**Risk:** MEDIUM | **Addresses:** C1, C2, C3

**⚠️ REQUIRES REVIEW BEFORE EXECUTION** - involves deprecations and semantic contracts.

#### **B8.0: Pre-Deprecation Code Search** ⚠️ REQUIRED

Before deprecating `rel_type`, search codebase for usage:

```powershell
# Search for rel_type references
Get-ChildItem -Path "C:\Users\richg\Gov_Reg" -Recurse -Include *.py,*.js,*.ts,*.yaml,*.json -Exclude "*REGISTRY*" |
    Select-String -Pattern "rel_type" -CaseSensitive

# If matches found, review each for migration/compatibility needs
# DECISION POINT: Add shims or migrate code before deprecating field
```

#### **B8.1: Resolve Duplicate Concepts (C1)**

**`edge_type` vs `rel_type`:**

Update `01260207201000000193_UNIFIED_SSOT_REGISTRY_WRITE_POLICY.yaml`:
```yaml
  rel_type:
    rationale: DEPRECATED - Use edge_type instead
    deprecated: true
    superseded_by: edge_type
    null_policy: allow_null
    update_policy: manual_patch_only
    writable_by: authorized_user
```

Update `01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json`:
```json
"rel_type": {
  "deprecated": true,
  "superseded_by": "edge_type",
  "deprecation_date": "2026-02-22",
  "removal_target": "2026-06-01"
}
```

**`generated` vs `is_generated`:**

Both kept - add semantic clarification to COLUMN_DICTIONARY.json:
```json
"generated": {
  "semantic_note": "Path/pattern-based detection (e.g., *.generated.py, build/ directories)"
},
"is_generated": {
  "semantic_note": "Registry-reference-based (explicit generator_id linkage)"
}
```

**`entity_kind` vs `is_directory`:**

Document relationship in DERIVATIONS.yaml:
```yaml
  entity_kind:
    depends_on: [is_directory, file_extension, file_type]
    formula: |
      CASE 
        WHEN is_directory = true THEN 'directory'
        WHEN file_extension IN ['.py', '.js', '.java'] THEN 'source_code'
        WHEN file_type = 'documentation' THEN 'documentation'
        ELSE 'file'
      END
    rationale: is_directory is INPUT primitive used to derive semantic entity_kind
```

#### **B8.2: Description Field Contracts (C2)**

Update `01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json`:

```json
"one_line_purpose": {
  "constraints": {
    "max_length": 120,
    "purpose": "Complete the sentence 'This file...' with a single clause"
  }
},
"short_description": {
  "constraints": {
    "max_length": 250,
    "purpose": "One paragraph summary suitable for tooltips or list views"
  }
},
"description": {
  "constraints": {
    "max_length": 2000,
    "purpose": "Long-form documentation with context, usage, dependencies"
  }
},
"notes": {
  "constraints": {
    "max_length": 4000,
    "purpose": "Operator-only technical notes, troubleshooting, history"
  }
}
```

Update `01999000042260124012_governance_registry_schema.v3.json`:

```json
"one_line_purpose": {
  "type": ["string", "null"],
  "maxLength": 120
},
"short_description": {
  "type": ["string", "null"],
  "maxLength": 250
},
"description": {
  "type": ["string", "null"],
  "maxLength": 2000
},
"notes": {
  "type": ["string", "null"],
  "maxLength": 4000
}
```

#### **B8.3: Scope status Enum (C3)**

**Pre-check live data:**
```python
import json
reg = json.load(open('01999000042260124503_REGISTRY_file.json'))
statuses = set(r.get('status') for r in reg['files'] if 'status' in r)
print(f"Live status values: {statuses}")
# Expected: {'active', 'legacy_read_only', None}
```

If safe, update `01999000042260124012_governance_registry_schema.v3.json`:

```json
"status": {
  "type": ["string", "null"],
  "enum": ["active", "archived", "deprecated", "legacy_read_only", null]
}
```

**Verification:**
```powershell
# Test schema still validates
python -m jsonschema --instance 01999000042260124503_REGISTRY_file.json 01999000042260124012_governance_registry_schema.v3.json
```

**Git Checkpoint:**
```powershell
git add 01260207201000000193_UNIFIED_SSOT_REGISTRY_WRITE_POLICY.yaml `
        01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json `
        01999000042260124012_governance_registry_schema.v3.json
git commit -m "B8: Design decisions - deprecate rel_type, add description contracts, scope status enum"
```

---

## STAGE 7: FINAL CLEANUP (Risk: LOW)
**Duration:** 1 hour

---

### **Phase A7: Archive Old Reports & Backups** (1 hour)
**Risk:** LOW | **Space Saved:** ~0.3 MB

**Actions:**

```powershell
# Create timestamped archive (ensure parent exists)
$archiveDate = Get-Date -Format "yyyyMMdd_HHmmss"
$archivePath = "C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY\archive\pre_cleanup_${archiveDate}"
New-Item -ItemType Directory -Path $archivePath -Force

# Move old analysis reports (check existence first)
$reportFiles = @(
    "C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY\01260202173939000112_NON_AUTHORITATIVE_FILES_ANALYSIS.md",
    "C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY\01260207201000000854_GEU_SETS_ANALYSIS.md"
)
foreach ($report in $reportFiles) {
    if (Test-Path $report) {
        Move-Item $report $archivePath
    }
}

# Compress old backups (keep structure but save space)
$backupPath = "C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY\01260207201000001253_BACKUP_FILES\01260207201000001255_backups"
if (Test-Path $backupPath) {
    Compress-Archive -Path "$backupPath\*" `
                     -DestinationPath "$archivePath\legacy_backups_${archiveDate}.zip" `
                     -Force
    
    # Keep only last 3 most recent backups in uncompressed form
    Get-ChildItem $backupPath |
        Sort-Object LastWriteTime -Descending |
        Select-Object -Skip 3 |
        Remove-Item -Force -Recurse
}
```

**Git Checkpoint:**
```powershell
# Stage only REGISTRY directory changes
Push-Location "C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY"
git add .
git commit -m "A7: Archive old reports and compress legacy backups"
Pop-Location
```

---

## POST-EXECUTION VALIDATION

### **Validation Suite** (30 min)

```powershell
# 1. Schema validation
python -m jsonschema --instance 01999000042260124503_REGISTRY_file.json 01999000042260124012_governance_registry_schema.v3.json

# 2. Count registered py_* fields (use actual discovered count)
(Select-String -Path "01260207201000000193_UNIFIED_SSOT_REGISTRY_WRITE_POLICY.yaml" -Pattern "^  py_").Count

# 3. No empty scopes
python -c "import json; d=json.load(open('01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json')); print('Empty scopes:', sum(1 for v in d['headers'].values() if v.get('scope',{}).get('record_kinds_in')==[]))"

# 4. No stale lock files
(Get-ChildItem -Path "C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY" -Recurse -Filter "*.lock").Count  # expect 0

# 5. File count
(Get-ChildItem -Path "C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY" -Recurse -File).Count
# Expected: ~180 files (down from 257)

# 6. Regenerate formula sheet (if tool available)
if (Test-Path "scripts/generate_formula_sheet.py") {
    python scripts/generate_formula_sheet.py
    # Expect 0 inconsistent rows
}

# 7. Validate COLUMN_DICTIONARY structure (if schema exists)
if (Test-Path "schemas/column_dictionary_schema.json") {
    python -m jsonschema --instance 01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json schemas/column_dictionary_schema.json
}

# 8. Check git status
git status
# All changes should be committed
```

---

## ROLLBACK PLAN

**Before starting any phase:**
```powershell
# Create full backup
$backupDate = Get-Date -Format "yyyyMMdd_HHmmss"
Copy-Item -Path "C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY" `
          -Destination "C:\Users\richg\Gov_Reg\01260207201000001133_backups\REGISTRY_pre_unified_cleanup_${backupDate}" `
          -Recurse
```

**To rollback:**
```powershell
# Restore from backup (replace $backupDate with actual timestamp)
Remove-Item "C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY" -Recurse -Force
Copy-Item -Path "C:\Users\richg\Gov_Reg\01260207201000001133_backups\REGISTRY_pre_unified_cleanup_${backupDate}" `
          -Destination "C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY" `
          -Recurse
```

---

## EXECUTION CHECKLIST

### Pre-Execution
- [ ] Full backup created
- [ ] File authority verified (completed ✅)
- [ ] Remediation plan status checked (not started ✅)
- [ ] Team notified (if multi-user environment)

### Stage 1: Foundation (1 hour)
- [ ] A1: Cache removed
- [ ] A2: .dir_id cleanup
- [ ] A3: Pre-apply files archived
- [ ] A4: Scripts organized

### Stage 2: Critical Schema (2.5 hours)
- [ ] B1: py_* fields registered (count from discovery script)
- [ ] B2: Undeclared fields added (count from discovery script)

### Stage 3: Deduplication (1 hour)
- [ ] A5: Schema duplicates resolved
- [ ] A6: Test directories consolidated

### Stage 4: Consistency (2.5 hours)
- [ ] B3: Immutable field derivations (9 fields)
- [ ] B4: manual_or_automated reclassified (6 fields)
- [ ] B7: Path/test precedence documented in single _metadata block (or comments)
- [ ] B9: Test coverage precedence groups added to COLUMN_DICTIONARY

### Stage 5: Scope & Type (4 hours)
- [ ] B5: Scopes fixed (9 'core' → 'entity', 40 empty → assigned)
- [ ] B6: Pre-check boolean values, fix data_transformation type, add serialization (41 fields)

### Stage 6: Design Decisions (2 hours)
- [ ] B8.0: Pre-deprecation code search for rel_type usage
- [ ] B8.1: Duplicates resolved (rel_type deprecated if safe)
- [ ] B8.2: Description contracts added (4 fields with maxLength)
- [ ] B8.3: Status enum scoped (verify live data first)

### Stage 7: Final Cleanup (1 hour)
- [ ] A7: Reports archived, old backups compressed

### Post-Execution
- [ ] Validation suite passed
- [ ] Documentation updated
- [ ] Backup retention verified

---

## ESTIMATED OUTCOMES

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| **Total Files** | 257 | ~180 | -30% |
| **Total Size** | 7.50 MB | ~5.5 MB | -27% |
| **Schema Coverage** | ~148/185 cols | 185/185 cols | 100% |
| **Validation Errors** | 45+ | 0 | ✅ |
| **Duplicate Files** | 7 | 0 | ✅ |
| **Empty Scopes** | 40 | 0 | ✅ |
| **Deprecated Fields** | 0 | 1 (rel_type) | Documented |
| **Test Coverage** | Scattered | Consolidated | ✅ |
| **Git Commits** | N/A | ~10 checkpoints | Granular history |

---

## MAINTENANCE NOTES

**After completion:**
1. Update `00_REGISTRY_FOLDER_MANIFEST.md` with new structure
2. Document deprecated fields in migration guide (especially `rel_type` → `edge_type`)
3. Run weekly validation: `python scripts/validate_registry_specs.py` (if exists)
4. Archive this plan to `docs/completed_remediations/`
5. Push final changes: `git push origin main` (or appropriate branch)

**Next quarterly review items:**
- Evaluate `rel_type` removal (target: 2026-06-01)
- Review backup retention (keep last 10, compress older)
- Audit new fields added since remediation
- Check if `generate_formula_sheet.py` should be created for ongoing validation

---

## REVISION HISTORY

### Revision 2 (2026-02-22T23:55:43Z) - Final Validation Pass

**Critical fixes:**
1. ✅ **Scoped git staging** - Changed `git add -A` to `git add .` in REGISTRY dir (A5/A6, A7)
2. ✅ **Single _metadata block** - Merged B7.1 and B9.1 into one block; added validator compatibility check
3. ✅ **Fixed commit messages** - Capture counts in PowerShell, not Python interpolation (B1, B2)
4. ✅ **Breaking changes disclaimer** - Updated header and added compatibility notes
5. ✅ **Robust A7 cleanup** - Added `-Force`, existence checks, parent directory creation
6. ✅ **Pre-check for B6** - Verify no boolean `data_transformation` values before type change
7. ✅ **Updated checklist** - Aligned with data-driven approach and revised time estimates

**Questions answered:**
- **_metadata support:** Added compatibility check in B7.1; fallback to comment block if needed
- **Staging scope:** Restricted to REGISTRY directory only (`git add .` in REGISTRY path)

### Revision 1 (2026-02-22T23:41:56Z) - Incorporated Execution Feedback

1. ✅ **Data-driven field discovery** (B1.0, B2.1) - No hardcoded field lists
2. ✅ **Name collision checks** (A6) - Safe test directory merge
3. ✅ **Pre-deprecation code search** (B8.0) - Check for `rel_type` usage before deprecating
4. ✅ **Adjusted serialization limits** (B6.2) - Import fields get 500 char limit vs 200
5. ✅ **Git checkpoint strategy** - Commit after each major phase (10 total commits)
6. ✅ **PowerShell-standardized** - All verification in PowerShell (not bash)
7. ✅ **Realistic time estimates** - 12-16 hours (was 24h)
8. ✅ **COLUMN_DICTIONARY validation** - Check structure after modifications
9. ✅ **Tool existence checks** - Graceful handling if `generate_formula_sheet.py` missing
10. ✅ **Decision points added** - STOP and review when data differs from expected

---

**Plan Status:** READY FOR EXECUTION  
**Approval Required:** Phase B8 (design decisions) - stakeholder review + code search for `rel_type`  
**Estimated Total Time:** 12-16 hours (realistic)  
**Recommended Timeline:** 2 business days (6-8h/day)
