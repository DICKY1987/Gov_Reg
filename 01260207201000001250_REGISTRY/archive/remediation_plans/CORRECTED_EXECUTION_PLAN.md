# CORRECTED Plan: Organize REGISTRY + Execute Spec Remediation
**Created:** 2026-02-26T17:10:00Z  
**Status:** CORRECTED after risk analysis  
**Changes:** Added reference update steps, fixed B2 verification, corrected file counts, Windows-compatible commands

---

## Pre-Execution Findings & Answers

### ✅ Questions Answered:

1. **py_capability_* in COLUMN_DICTIONARY?** YES (both present, enhanced in pre-remediation Step 3)
2. **path_aliases in specs?** 
   - WRITE_POLICY: YES
   - DERIVATIONS: NO (needs to be added in B7)
   - Schema: YES
3. **B2 undeclared fields?** 19 fields found (B2 is NOT complete - needs execution)
4. **dir_id\ exists?** YES (contains 2 items - keep for now, don't delete)
5. **Archive file count?** All 15 files found

### 🔴 Critical Fixes Applied:

1. **Added reference update sweep** after file moves
2. **B2 execution included** (19 undeclared fields confirmed)
3. **Keep REGISTRY_SPEC_REMEDIATION_EXECUTION_PLAN.md active** until after remediation
4. **Archive it in final commit** after all work complete
5. **Windows PowerShell commands** for all verification
6. **path_aliases derivation** added to B7 scope
7. **Preserve dir_id\** (not empty, may be needed)

---

## Part 1: Directory Organization (~20 min)

### 1.1: Move 4 Python Scripts → `01260207201000001270_scripts/`

```powershell
cd C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY

Move-Item "P_01999000042260124033_validate_plan_reservations.py" "01260207201000001270_scripts\"
Move-Item "P_01999000042260124034_validate_ingest_commitments.py" "01260207201000001270_scripts\"
Move-Item "P_01999000042260125100_test_enhanced_scanner.py" "01260207201000001270_scripts\"
Move-Item "P_01999000042260125101_test_enhanced_scanner_standalone.py" "01260207201000001270_scripts\"
```

**Keep at root:** `P_RENAME_REMOVE_DOC_TOKEN.py` (actively used)

---

### 1.2: Create `docs/` → Move 8 Reference Docs

```powershell
New-Item -ItemType Directory -Path "docs" -Force

Move-Item "END_TO_END_REGISTRY_PROCESS.md" "docs\"
Move-Item "01260202173939000111_INGEST_SPEC_UNIFIED_REGISTRY.txt" "docs\"
Move-Item "01260207201000000866_REGISTRY_TUI_TECHNICAL_SPEC.txt" "docs\"
Move-Item "01260207201000000849_BACKUP_MANIFEST.txt" "docs\"
Move-Item "BACKUP_HIERARCHY.md" "docs\"
Move-Item "DUPLICATE_ID_PREVENTION.md" "docs\"
Move-Item "P_01999000042260125105_README_ENHANCED_SCANNER.md" "docs\"
Move-Item "00_REPORTS_INDEX.md" "docs\"
```

---

### 1.3: Create `archive/remediation_plans/` → Move 8 Implementation Guides

**⚠️ CRITICAL:** Keep active remediation docs at root until Part 2 completes:
- `REGISTRY_SPEC_REMEDIATION_EXECUTION_PLAN.md` (ACTIVE - needed for Part 2)
- `PRE_REMEDIATION_FIX_REQUIRED.md` (reference during execution)
- `PRE_REMEDIATION_FIX_COMPLETION_REPORT.md` (recent history)

```powershell
New-Item -ItemType Directory -Path "archive\remediation_plans" -Force

# Archive only completed implementation guides
Move-Item "B1_IMPLEMENTATION_GUIDE.txt" "archive\remediation_plans\"
Move-Item "B3_IMPLEMENTATION_GUIDE.txt" "archive\remediation_plans\"
Move-Item "B4_IMPLEMENTATION_GUIDE.txt" "archive\remediation_plans\"
Move-Item "B5_IMPLEMENTATION_GUIDE.txt" "archive\remediation_plans\"
Move-Item "B6_IMPLEMENTATION_GUIDE.txt" "archive\remediation_plans\"
Move-Item "B7_IMPLEMENTATION_GUIDE.txt" "archive\remediation_plans\"
Move-Item "B8_IMPLEMENTATION_GUIDE.txt" "archive\remediation_plans\"
Move-Item "B9_IMPLEMENTATION_GUIDE.txt" "archive\remediation_plans\"

# Archive old cleanup plans
Move-Item "IMPLEMENTATION_MASTER_INDEX.md" "archive\remediation_plans\"
Move-Item "REGISTRY_CLEANUP_DECISIONS_REQUIRED.md" "archive\remediation_plans\"
Move-Item "UNIFIED_REGISTRY_CLEANUP_AND_REMEDIATION_PLAN.md" "archive\remediation_plans\"
Move-Item "CLEANUP_EXECUTION_SUMMARY.md" "archive\remediation_plans\"

# Check if this exists (may be named differently)
if (Test-Path "Registry Issues Remediation Plan.md") {
    Move-Item "Registry Issues Remediation Plan.md" "archive\remediation_plans\"
}
```

---

### 1.4: Move `PHASE_0_A11_SOLUTION/` → `archive/`

```powershell
if (Test-Path "PHASE_0_A11_SOLUTION") {
    Move-Item "PHASE_0_A11_SOLUTION" "archive\"
}
```

---

### 1.5: 🔍 Update References After File Moves

**Critical step to avoid broken links:**

```powershell
# Search for references to moved files
Write-Host "=== Checking for broken references ===" -ForegroundColor Yellow

# Check scripts directory for references to moved Python files
Select-String -Path "01260207201000001270_scripts\*.py" `
              -Pattern "P_01999000042260124033|P_01999000042260124034|P_01999000042260125100|P_01999000042260125101" `
              -Context 1

# Check docs for references to moved markdown files
Select-String -Path "docs\*.md" `
              -Pattern "END_TO_END_REGISTRY_PROCESS|BACKUP_HIERARCHY|DUPLICATE_ID_PREVENTION" `
              -Context 1

# Check for references to archived guides (should be minimal since they're old)
Select-String -Path "*.md","*.py","*.txt" -Exclude "archive\*" `
              -Pattern "B[1-9]_IMPLEMENTATION_GUIDE" `
              -Context 1

# Manual review required if matches found - update paths in affected files
```

**If references found:** Update import statements, relative paths, and documentation links before committing.

---

### 1.6: Commit Part 1

```powershell
git add -A
git status  # Review changes
git commit -m "refactor(registry): Organize root directory structure

- Move 4 Python scripts -> scripts/
- Move 8 reference docs -> docs/
- Move 8 implementation guides + 4 cleanup plans -> archive/remediation_plans/
- Move PHASE_0_A11_SOLUTION -> archive/
- Preserve dir_id/ (contains 2 items, may be needed)
- Keep active remediation docs at root (REGISTRY_SPEC_REMEDIATION_EXECUTION_PLAN, PRE_REMEDIATION_FIX_*)
- Verify and update file references where needed"
```

---

## Part 2: Spec Remediation Execution (~4 hours)

**Target Files:**
- `COLUMN_HEADERS/01260207201000000193_UNIFIED_SSOT_REGISTRY_WRITE_POLICY.yaml`
- `COLUMN_HEADERS/01260207201000000192_UNIFIED_SSOT_REGISTRY_DERIVATIONS.yaml`
- `COLUMN_HEADERS/01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json`
- `01999000042260124012_governance_registry_schema.v3.json`

---

### Phase B2: Add 19 Undeclared Fields to Schema (30 min) ⚠️ NEW - CRITICAL

**Status:** NOT complete (19 fields confirmed undeclared)

**Fields to add to schema:**
`absolute_path`, `artifact_path`, `created_time`, `created_utc`, `entity_kind`, `extension`, `file_type`, `filename`, `modified_time`, `module_id`, `notes`, `py_capability_facts_hash`, `py_capability_tags`, `record_kind`, `registered_by`, `registration_time`, `size_bytes`, `status`, `updated_utc`

**Note:** py_capability_* are in COLUMN_DICTIONARY but missing from schema - B2 will add them.

**File:** `01999000042260124012_governance_registry_schema.v3.json`

Add to `definitions.FileRecord.properties`:

```json
"absolute_path": {"type": ["string", "null"]},
"artifact_path": {"type": ["string", "null"]},
"created_time": {"type": ["string", "null"], "format": "date-time"},
"created_utc": {"type": ["string", "null"], "format": "date-time"},
"entity_kind": {"type": ["string", "null"]},
"extension": {"type": ["string", "null"]},
"file_type": {"type": ["string", "null"]},
"filename": {"type": ["string", "null"]},
"modified_time": {"type": ["string", "null"], "format": "date-time"},
"module_id": {"type": ["string", "null"]},
"notes": {"type": ["string", "null"]},
"py_capability_facts_hash": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
"py_capability_tags": {"type": "array", "items": {"type": "string"}},
"record_kind": {"type": "string", "enum": ["entity", "edge", "metadata", "generator"]},
"registered_by": {"type": ["string", "null"]},
"registration_time": {"type": ["string", "null"], "format": "date-time"},
"size_bytes": {"type": ["integer", "null"], "minimum": 0},
"status": {"type": ["string", "null"]},
"updated_utc": {"type": ["string", "null"], "format": "date-time"}
```

**Verification:**
```powershell
python -c "import json; reg=json.load(open('01999000042260124503_REGISTRY_file.json', encoding='utf-8')); schema=json.load(open('01999000042260124012_governance_registry_schema.v3.json', encoding='utf-8')); undeclared=set(k for r in reg['files'] for k in r.keys()) - set(schema['definitions']['FileRecord']['properties'].keys()); print(f'Undeclared: {len(undeclared)}'); exit(0 if len(undeclared)==0 else 1)"
# Should print "Undeclared: 0" and exit 0
```

**Commit:**
```powershell
git add 01999000042260124012_governance_registry_schema.v3.json
git commit -m "feat(registry): B2 - Add 19 undeclared fields to schema

- Add absolute_path, artifact_path, created_time, created_utc, entity_kind
- Add extension, file_type, filename, modified_time, module_id, notes
- Add py_capability_facts_hash (with SHA-256 pattern), py_capability_tags
- Add record_kind (with enum), registered_by, registration_time
- Add size_bytes, status, updated_utc
- Fixes: All live data fields now in schema (0 undeclared)"
```

---

### Phase B1: Register py_capability_* in WRITE_POLICY & DERIVATIONS (20 min)

**Note:** Already in COLUMN_DICTIONARY and now in schema (B2). Just need WRITE_POLICY and DERIVATIONS.

**File 1:** `COLUMN_HEADERS/01260207201000000193_UNIFIED_SSOT_REGISTRY_WRITE_POLICY.yaml`

Append to `columns:` section:

```yaml
  py_capability_facts_hash:
    rationale: SHA-256 hash of capability facts extracted from Python file
    null_policy: allow_null
    update_policy: recompute_on_build
    writable_by: tool_only

  py_capability_tags:
    rationale: Capability tags derived from Python code analysis
    null_policy: allow_null
    update_policy: recompute_on_build
    writable_by: tool_only
    merge_strategy: set_union
```

**File 2:** `COLUMN_HEADERS/01260207201000000192_UNIFIED_SSOT_REGISTRY_DERIVATIONS.yaml`

Append:

```yaml
  py_capability_facts_hash:
    depends_on: []
    error_policy: set_null
    type: string
    trigger: recompute_on_build
    null_behavior: allow
    formula: COALESCE(INPUT.py_capability_facts_hash, NULL)
    rationale: Provided directly by Python analysis tool; null for non-Python files

  py_capability_tags:
    depends_on: []
    error_policy: set_null
    type: array
    trigger: recompute_on_build
    null_behavior: set_empty_array
    formula: COALESCE(INPUT.py_capability_tags, [])
    rationale: Provided directly by Python analysis tool; null for non-Python files
```

**Verification:**
```powershell
Select-String -Path "COLUMN_HEADERS\01260207201000000193_UNIFIED_SSOT_REGISTRY_WRITE_POLICY.yaml" -Pattern "py_capability" | Measure-Object | Select-Object -ExpandProperty Count
# Should be 2

Select-String -Path "COLUMN_HEADERS\01260207201000000192_UNIFIED_SSOT_REGISTRY_DERIVATIONS.yaml" -Pattern "py_capability" | Measure-Object | Select-Object -ExpandProperty Count
# Should be 2
```

**Commit:**
```powershell
git add COLUMN_HEADERS\01260207201000000193_UNIFIED_SSOT_REGISTRY_WRITE_POLICY.yaml `
        COLUMN_HEADERS\01260207201000000192_UNIFIED_SSOT_REGISTRY_DERIVATIONS.yaml
git commit -m "feat(registry): B1 - Register py_capability_* in WRITE_POLICY and DERIVATIONS

- Add py_capability_facts_hash to WRITE_POLICY (tool_only, recompute_on_build)
- Add py_capability_tags to WRITE_POLICY (tool_only, set_union merge)
- Add both to DERIVATIONS with INPUT passthrough formulas
- Completes registration (already in COLUMN_DICTIONARY + schema)"
```

---

### Phase B3: Add 9 Immutable Field Derivations (20 min)

**File:** `COLUMN_HEADERS/01260207201000000192_UNIFIED_SSOT_REGISTRY_DERIVATIONS.yaml`

See B3_IMPLEMENTATION_GUIDE.txt for full entries. Append 9 field definitions with `trigger: on_create_only`.

**Commit:**
```powershell
git add COLUMN_HEADERS\01260207201000000192_UNIFIED_SSOT_REGISTRY_DERIVATIONS.yaml
git commit -m "feat(registry): B3 - Add derivations for 9 immutable fields

- created_by, directionality, edge_type, record_kind, rel_type
- source_entity_id, source_file_id, target_entity_id, target_file_id
- All set to trigger: on_create_only (immutable after creation)"
```

---

### Phase B5: Fix 49 Scope Issues (1.5 hours)

**File:** `COLUMN_HEADERS/01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json`

**Step 1:** Replace 9 invalid `"core"` → `"entity"`  
**Step 2:** Assign scopes to 40 empty fields (see B5_IMPLEMENTATION_GUIDE.txt)

**Verification:**
```powershell
# No empty scopes
python -c "import json; d=json.load(open('COLUMN_HEADERS/01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json', encoding='utf-8')); empty=sum(1 for v in d['headers'].values() if v.get('scope',{}).get('record_kinds_in')==[]); print(f'Empty scopes: {empty}'); exit(0 if empty==0 else 1)"

# No 'core' values
python -c "import json; content=open('COLUMN_HEADERS/01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json', encoding='utf-8').read(); count=content.count('\"core\"'); print(f'core refs: {count}'); exit(0 if count==0 else 1)"
```

**Commit:**
```powershell
git add COLUMN_HEADERS\01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json
git commit -m "fix(registry): B5 - Fix 49 scope issues in COLUMN_DICTIONARY

- Replace 9 invalid 'core' values with 'entity'
- Assign scopes to 40 empty fields (entity/edge/generator/universal)
- All fields now have valid record_kinds_in values"
```

---

### Phase B6: Add Serialization + Fix data_transformation Type (1 hour)

**File:** `COLUMN_HEADERS/01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json`

**Pre-check:**
```powershell
python -c "import json; reg=json.load(open('01999000042260124503_REGISTRY_file.json', encoding='utf-8')); bools=[r.get('data_transformation') for r in reg['files'] if 'data_transformation' in r and type(r['data_transformation'])==bool]; print(f'Boolean values: {len(bools)}'); exit(1 if len(bools)>0 else 0)"
# Should print "Boolean values: 0"
```

**Changes:**
1. Fix `data_transformation` type (remove boolean, add enum)
2. Add serialization to 35 array fields (200 chars, 500 for imports)
3. Add serialization to 6 object fields (500 chars)

**Verification:**
```powershell
python -c "import json; d=json.load(open('COLUMN_HEADERS/01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json', encoding='utf-8')); dt_type=d['headers']['data_transformation']['value_schema']['type']; has_bool='boolean' in str(dt_type); print(f'Has boolean: {has_bool}'); exit(1 if has_bool else 0)"
```

**Commit:**
```powershell
git add COLUMN_HEADERS\01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json
git commit -m "feat(registry): B6 - Add serialization to 41 fields, fix data_transformation type

- Fix data_transformation: remove boolean type, add enum
- Add serialization.flat_table to 35 array fields (json_array_string, 200/500 chars)
- Add serialization.flat_table to 6 object fields (json_object_string, 500 chars)
- Import fields use 500 char limit (others 200)"
```

---

### Phase B7+B9: Precedence Documentation (30 min)

**File 1:** `COLUMN_HEADERS/01260207201000000192_UNIFIED_SSOT_REGISTRY_DERIVATIONS.yaml`

**Test YAML parser first:**
```powershell
python -c "import yaml; test='_metadata:\n  test: value\nfield1:\n  type: string\n'; yaml.safe_load(test); print('_metadata supported')" 2>&1
```

If supported, add `_metadata` block with path + test coverage precedence. If not, use comment block (see B7_IMPLEMENTATION_GUIDE.txt).

**Add path_aliases derivation:**
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

**File 2:** `COLUMN_HEADERS/01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json`

Add `precedence_group` tags to 6 test coverage fields (see B9_IMPLEMENTATION_GUIDE.txt).

**Commit:**
```powershell
git add COLUMN_HEADERS\01260207201000000192_UNIFIED_SSOT_REGISTRY_DERIVATIONS.yaml `
        COLUMN_HEADERS\01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json
git commit -m "feat(registry): B7+B9 - Document path/test precedence, add path_aliases derivation

- Add field precedence rules to DERIVATIONS (path + test coverage)
- Add path_aliases derivation (manual_patch_only)
- Add precedence_group tags to 6 test coverage fields in COLUMN_DICTIONARY
- Documents field resolution order for consumers"
```

---

### Phase B4: Reclassify 6 Manual Fields (15 min) ⚠️ Review Required

**Pre-check for automation tool impact:**
```powershell
Get-ChildItem C:\Users\richg\Gov_Reg -Recurse -Include *.py,*.js,*.ts -Exclude "*REGISTRY*","*backup*" |
    Select-String -Pattern "description|one_line_purpose|short_description|superseded_by|supersedes_entity_id|bundle_version" -Context 2,2 |
    Where-Object {$_.Line -match "(patch|write|update)"}
# Review results - if automation tools found, add compatibility shims
```

**File:** `COLUMN_HEADERS/01260207201000000193_UNIFIED_SSOT_REGISTRY_WRITE_POLICY.yaml`

Change 6 fields from `manual_or_automated` → `manual_patch_only` (see B4_IMPLEMENTATION_GUIDE.txt).

**Verification:**
```powershell
Select-String -Path "COLUMN_HEADERS\01260207201000000193_UNIFIED_SSOT_REGISTRY_WRITE_POLICY.yaml" `
              -Pattern "manual_or_automated" |
    Where-Object {$_.Line -match "(description|one_line_purpose|short_description|superseded_by|supersedes_entity_id|bundle_version)"}
# Should return 0 matches
```

**Commit:**
```powershell
git add COLUMN_HEADERS\01260207201000000193_UNIFIED_SSOT_REGISTRY_WRITE_POLICY.yaml
git commit -m "fix(registry): B4 - Reclassify 6 fields to manual_patch_only

- Change update_policy for: description, one_line_purpose, short_description
- Change update_policy for: superseded_by, supersedes_entity_id, bundle_version
- From: manual_or_automated -> To: manual_patch_only
- Breaking: Automated tools expecting write access will be blocked"
```

---

### Phase B8: Design Decisions ⏭️ DEFERRED

**Status:** Requires stakeholder review  
**Reason:** rel_type deprecation found in 20+ locations  
**Action:** Skip for now, execute later after code review

---

## Part 3: Final Cleanup & Verification

### 3.1: Archive Active Remediation Docs (Now That Work Is Complete)

```powershell
# Now safe to archive since remediation is complete
Move-Item "REGISTRY_SPEC_REMEDIATION_EXECUTION_PLAN.md" "archive\remediation_plans\"
Move-Item "PRE_REMEDIATION_FIX_REQUIRED.md" "archive\remediation_plans\"
Move-Item "PRE_REMEDIATION_FIX_COMPLETION_REPORT.md" "archive\remediation_plans\"
```

---

### 3.2: Update 00_REGISTRY_FOLDER_MANIFEST.md

Document new structure:
- `docs/` - Reference documentation
- `archive/remediation_plans/` - Historical cleanup plans
- `scripts/` - Validation and test scripts
- `COLUMN_HEADERS/` - Specification files
- Root files reduced to essentials

---

### 3.3: Comprehensive Verification Suite

```powershell
Write-Host "`n=== VERIFICATION SUITE ===" -ForegroundColor Cyan

# 1. Schema validates against live data
Write-Host "`n1. Schema validation:" -ForegroundColor Yellow
python -m jsonschema --instance 01999000042260124503_REGISTRY_file.json `
                     01999000042260124012_governance_registry_schema.v3.json
if ($LASTEXITCODE -eq 0) { Write-Host "  ✓ PASS" -ForegroundColor Green } else { Write-Host "  ✗ FAIL" -ForegroundColor Red }

# 2. No undeclared fields (B2 complete)
Write-Host "`n2. Undeclared fields check:" -ForegroundColor Yellow
python -c "import json; reg=json.load(open('01999000042260124503_REGISTRY_file.json', encoding='utf-8')); schema=json.load(open('01999000042260124012_governance_registry_schema.v3.json', encoding='utf-8')); undeclared=len(set(k for r in reg['files'] for k in r.keys())-set(schema['definitions']['FileRecord']['properties'].keys())); print(f'  Undeclared: {undeclared}'); exit(0 if undeclared==0 else 1)"
if ($LASTEXITCODE -eq 0) { Write-Host "  ✓ PASS" -ForegroundColor Green } else { Write-Host "  ✗ FAIL" -ForegroundColor Red }

# 3. No empty scopes (B5 complete)
Write-Host "`n3. Empty scopes check:" -ForegroundColor Yellow
python -c "import json; d=json.load(open('COLUMN_HEADERS/01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json', encoding='utf-8')); empty=sum(1 for v in d['headers'].values() if v.get('scope',{}).get('record_kinds_in')==[]); print(f'  Empty scopes: {empty}'); exit(0 if empty==0 else 1)"
if ($LASTEXITCODE -eq 0) { Write-Host "  ✓ PASS" -ForegroundColor Green } else { Write-Host "  ✗ FAIL" -ForegroundColor Red }

# 4. No 'core' values (B5 complete)
Write-Host "`n4. Invalid 'core' check:" -ForegroundColor Yellow
python -c "import json; content=open('COLUMN_HEADERS/01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json', encoding='utf-8').read(); count=content.count('\"core\"'); print(f'  core refs: {count}'); exit(0 if count==0 else 1)"
if ($LASTEXITCODE -eq 0) { Write-Host "  ✓ PASS" -ForegroundColor Green } else { Write-Host "  ✗ FAIL" -ForegroundColor Red }

# 5. data_transformation type fixed (B6 complete)
Write-Host "`n5. data_transformation type check:" -ForegroundColor Yellow
python -c "import json; d=json.load(open('COLUMN_HEADERS/01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json', encoding='utf-8')); has_bool='boolean' in str(d['headers']['data_transformation']['value_schema']['type']); print(f'  Has boolean: {has_bool}'); exit(1 if has_bool else 0)"
if ($LASTEXITCODE -eq 0) { Write-Host "  ✓ PASS" -ForegroundColor Green } else { Write-Host "  ✗ FAIL" -ForegroundColor Red }

# 6. Root directory clean
Write-Host "`n6. Root directory structure:" -ForegroundColor Yellow
Get-ChildItem -Directory | Select-Object -ExpandProperty Name | ForEach-Object { Write-Host "    $_" }
Get-ChildItem -File | Where-Object { $_.Name -notmatch "COUNTER_STORE|\.json$" } | Select-Object -First 5 | ForEach-Object { Write-Host "    $($_.Name)" }

# 7. Git commits
Write-Host "`n7. Recent commits:" -ForegroundColor Yellow
git log --oneline -10

Write-Host "`n=== VERIFICATION COMPLETE ===" -ForegroundColor Cyan
```

---

### 3.4: Final Commit

```powershell
git add 00_REGISTRY_FOLDER_MANIFEST.md
git commit -m "docs(registry): Archive remediation docs, update manifest

- Move REGISTRY_SPEC_REMEDIATION_EXECUTION_PLAN.md -> archive/remediation_plans/
- Move PRE_REMEDIATION_FIX_*.md -> archive/remediation_plans/
- Update 00_REGISTRY_FOLDER_MANIFEST.md with new directory structure
- Remediation complete: B2, B1, B3, B5, B6, B7+B9, B4 (B8 deferred)"
```

---

## Expected Commit Sequence (10 commits)

1. `refactor(registry): Organize root directory structure`
2. `feat(registry): B2 - Add 19 undeclared fields to schema`
3. `feat(registry): B1 - Register py_capability_* in WRITE_POLICY and DERIVATIONS`
4. `feat(registry): B3 - Add derivations for 9 immutable fields`
5. `fix(registry): B5 - Fix 49 scope issues in COLUMN_DICTIONARY`
6. `feat(registry): B6 - Add serialization to 41 fields, fix data_transformation type`
7. `feat(registry): B7+B9 - Document path/test precedence, add path_aliases derivation`
8. `fix(registry): B4 - Reclassify 6 fields to manual_patch_only`
9. `docs(registry): Archive remediation docs, update manifest`

---

## Risk Mitigation Summary

### ✅ Addressed from Review:

1. **Reference update sweep** - Added explicit check for broken links after moves
2. **B2 execution** - Added (was incorrectly assumed complete, 19 fields confirmed)
3. **Active doc preservation** - Keep execution plan active until Part 2 done
4. **Windows compatibility** - All PowerShell commands, no bash syntax
5. **path_aliases completeness** - Added derivation in B7 (was missing)
6. **File count accuracy** - Confirmed 15 files, list corrected
7. **Manifest timing** - Moved to final commit after all work complete
8. **dir_id preservation** - Not deleting (contains 2 items, may be needed)
9. **jsonschema dependency** - Documented in verification
10. **Commit type accuracy** - `feat` for data model changes, `docs` only for pure documentation

---

**Plan Status:** CORRECTED AND READY  
**Estimated Duration:** 5-6 hours (20 min organization + 4-5 hours remediation + verification)  
**Breaking Changes:** B4 only (automated writers blocked - review required first)  
**Deferred:** B8 (rel_type deprecation - stakeholder review needed)
