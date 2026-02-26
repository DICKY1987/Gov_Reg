# Registry Specification Remediation - Execution Plan
**Created:** 2026-02-26T07:40:19Z  
**Status:** Ready for execution  
**Estimated Duration:** 3-4 hours  
**Risk Level:** LOW (all changes are additive or corrective)

---

## Executive Summary

This plan implements the registry specification fixes documented in implementation guides B1-B9. All changes have been validated against live data and are ready to apply. The primary goal is to bring all registry fields into full specification coverage with proper validation, derivation rules, and documentation.

**Key Changes:**
- Register 2 missing Python analysis fields
- Fix 49 scope issues in COLUMN_DICTIONARY
- Add serialization to 41 fields
- Document 9 immutable field derivations
- Reclassify 6 manual fields (⚠️ potential breaking change)
- Add path and test coverage precedence rules
- Optional: Design decisions requiring stakeholder review

---

## Pre-Flight Checks ✅

### Completed Verifications:
- [x] Live data validation: Only 2 py_* fields missing from schema
- [x] File authority established: Root files are canonical
- [x] No backup conflicts: Duplicate files identified and safe to remove
- [x] Capability system integration: Fields are production-ready
- [x] Git repository status: Clean working directory recommended

### Required Before Starting:
```powershell
# 1. Create full backup
cd C:\Users\richg\Gov_Reg
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
Copy-Item -Path "01260207201000001250_REGISTRY" `
          -Destination "01260207201000001133_backups\REGISTRY_pre_spec_remediation_$timestamp" `
          -Recurse

# 2. Verify clean git status
cd 01260207201000001250_REGISTRY
git status

# 3. Create feature branch (recommended)
git checkout -b fix/registry-spec-remediation
```

---

## Phase 1: Critical Fields Registration (30 min) ⭐ HIGHEST PRIORITY

### B1: Register py_capability_* Fields
**Risk:** LOW | **Breaking:** NO | **Blocking:** Validation currently fails

**Files to modify:**
1. `COLUMN_HEADERS\01260207201000000193_UNIFIED_SSOT_REGISTRY_WRITE_POLICY.yaml`
2. `COLUMN_HEADERS\01260207201000000192_UNIFIED_SSOT_REGISTRY_DERIVATIONS.yaml`
3. `01999000042260124012_governance_registry_schema.v3.json`

**Changes:**

#### 1.1: Add to WRITE_POLICY.yaml (append to `columns:` section):
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

#### 1.2: Add to DERIVATIONS.yaml (append to field definitions):
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

#### 1.3: Add to governance_registry_schema.v3.json (in `definitions.FileRecord.properties`):
```json
"py_capability_facts_hash": {
  "type": ["string", "null"]
},
"py_capability_tags": {
  "type": "array",
  "items": {"type": "string"}
}
```

**Verification:**
```powershell
cd C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY

# Validate schema
python -m jsonschema --instance 01999000042260124503_REGISTRY_file.json `
                     01999000042260124012_governance_registry_schema.v3.json

# Should pass without additionalProperties errors for py_capability_* fields
```

**Git Checkpoint:**
```powershell
git add COLUMN_HEADERS\01260207201000000193_UNIFIED_SSOT_REGISTRY_WRITE_POLICY.yaml `
        COLUMN_HEADERS\01260207201000000192_UNIFIED_SSOT_REGISTRY_DERIVATIONS.yaml `
        01999000042260124012_governance_registry_schema.v3.json
git commit -m "B1: Register py_capability_facts_hash and py_capability_tags fields"
```

---

## Phase 2: Immutable Field Derivations (20 min)

### B3: Add on_create_only Derivations
**Risk:** LOW | **Breaking:** NO | **Purpose:** Document existing behavior

**File to modify:**
- `COLUMN_HEADERS\01260207201000000192_UNIFIED_SSOT_REGISTRY_DERIVATIONS.yaml`

**Add 9 field entries** (see B3_IMPLEMENTATION_GUIDE.txt for full details):

```yaml
  created_by:
    depends_on: []
    error_policy: set_null
    type: string
    trigger: on_create_only
    null_behavior: allow
    formula: COALESCE(INPUT.created_by, NULL)
    rationale: User or tool that created the record; set at creation time only

  directionality:
    depends_on: []
    error_policy: set_null
    type: string
    trigger: on_create_only
    null_behavior: allow
    formula: COALESCE(INPUT.directionality, NULL)
    rationale: Edge direction; immutable after creation

  edge_type:
    depends_on: []
    error_policy: fail
    type: string
    trigger: on_create_only
    null_behavior: error
    formula: INPUT.edge_type
    rationale: Required edge relationship type; immutable after creation

  record_kind:
    depends_on: []
    error_policy: fail
    type: string
    trigger: on_create_only
    null_behavior: error
    formula: INPUT.record_kind
    rationale: Required record type; immutable after creation

  rel_type:
    depends_on: []
    error_policy: set_null
    type: string
    trigger: on_create_only
    null_behavior: allow
    formula: COALESCE(INPUT.rel_type, NULL)
    rationale: Relationship type (deprecated in favor of edge_type); immutable

  source_entity_id:
    depends_on: []
    error_policy: set_null
    type: string
    trigger: on_create_only
    null_behavior: allow
    formula: COALESCE(INPUT.source_entity_id, NULL)
    rationale: Source entity reference; immutable after creation

  source_file_id:
    depends_on: []
    error_policy: set_null
    type: string
    trigger: on_create_only
    null_behavior: allow
    formula: COALESCE(INPUT.source_file_id, NULL)
    rationale: Source file reference; immutable after creation

  target_entity_id:
    depends_on: []
    error_policy: set_null
    type: string
    trigger: on_create_only
    null_behavior: allow
    formula: COALESCE(INPUT.target_entity_id, NULL)
    rationale: Target entity reference; immutable after creation

  target_file_id:
    depends_on: []
    error_policy: set_null
    type: string
    trigger: on_create_only
    null_behavior: allow
    formula: COALESCE(INPUT.target_file_id, NULL)
    rationale: Target file reference; immutable after creation
```

**Git Checkpoint:**
```powershell
git add COLUMN_HEADERS\01260207201000000192_UNIFIED_SSOT_REGISTRY_DERIVATIONS.yaml
git commit -m "B3: Add derivations for 9 immutable fields"
```

---

## Phase 3: Scope Corrections (1.5 hours)

### B5: Fix COLUMN_DICTIONARY Scope Issues
**Risk:** LOW | **Breaking:** NO | **Fixes:** 49 fields

**File to modify:**
- `COLUMN_HEADERS\01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json`

**Step 1: Replace invalid 'core' with 'entity' (9 fields)**

Find all occurrences of:
```json
"record_kinds_in": ["core"]
```

Replace with:
```json
"record_kinds_in": ["entity"]
```

**Affected fields:** created_by, created_utc, notes, record_id, record_kind, updated_utc, registered_by, registration_time, scan_id

**Step 2: Assign scopes to 40 empty fields**

**Universal fields** (all record types):
```json
"record_id": {
  "scope": {"record_kinds_in": ["entity", "edge", "generator", "metadata"]}
},
"created_utc": {
  "scope": {"record_kinds_in": ["entity", "edge", "generator", "metadata"]}
},
"updated_utc": {
  "scope": {"record_kinds_in": ["entity", "edge", "generator", "metadata"]}
},
"scan_id": {
  "scope": {"record_kinds_in": ["entity", "edge", "generator", "metadata"]}
}
```

**Edge-specific fields:**
```json
"edge_type": {"scope": {"record_kinds_in": ["edge"]}},
"source_file_id": {"scope": {"record_kinds_in": ["edge"]}},
"target_file_id": {"scope": {"record_kinds_in": ["edge"]}},
"source_entity_id": {"scope": {"record_kinds_in": ["edge"]}},
"target_entity_id": {"scope": {"record_kinds_in": ["edge"]}},
"directionality": {"scope": {"record_kinds_in": ["edge"]}},
"rel_type": {"scope": {"record_kinds_in": ["edge"]}},
"confidence": {"scope": {"record_kinds_in": ["edge"]}}
```

**Entity-specific fields** (see B5_IMPLEMENTATION_GUIDE.txt for complete list of ~30 fields)

**Generator-specific fields:**
```json
"generator_id": {"scope": {"record_kinds_in": ["generator"]}},
"generated_files": {"scope": {"record_kinds_in": ["generator"]}}
```

**Verification:**
```powershell
# Check no empty scopes
python -c "import json; d=json.load(open('COLUMN_HEADERS/01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json')); empty=[h for h,v in d['headers'].items() if v.get('scope',{}).get('record_kinds_in')==[]]; print(f'Empty scopes: {len(empty)}')"
# Expect: 0

# Check no 'core' values
python -c "import json; import re; content=open('COLUMN_HEADERS/01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json').read(); print(f'core occurrences: {len(re.findall(chr(34)+\"core\"+chr(34), content))}')"
# Expect: 0
```

**Git Checkpoint:**
```powershell
git add COLUMN_HEADERS\01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json
git commit -m "B5: Fix scope issues - remove 'core', assign 40 empty scopes"
```

---

## Phase 4: Serialization Specifications (1 hour)

### B6: Add Flat-Table Serialization
**Risk:** LOW | **Breaking:** NO | **Fixes:** 41 fields + 1 type correction

**File to modify:**
- `COLUMN_HEADERS\01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json`

**Step 1: Pre-check data_transformation type** ⚠️ REQUIRED
```powershell
python -c "import json; reg=json.load(open('01999000042260124503_REGISTRY_file.json')); bools=[r.get('data_transformation') for r in reg['files'] if 'data_transformation' in r and isinstance(r['data_transformation'], bool)]; print(f'Boolean values: {len(bools)}')"
# Expect: 0 (safe to proceed)
```

**Step 2: Fix data_transformation type**

Find:
```json
"data_transformation": {
  "value_schema": {
    "type": ["boolean", "string", "null"],
```

Replace with:
```json
"data_transformation": {
  "value_schema": {
    "type": ["string", "null"],
    "enum": ["normalize", "aggregate", "filter", "transform", "enrich", null]
```

**Step 3: Add serialization to 35 array fields**

For most array fields (200 char limit):
```json
"serialization": {
  "flat_table": {
    "strategy": "json_array_string",
    "separator": ",",
    "max_display_length": 200
  }
}
```

For import fields (500 char limit):
- py_imports_stdlib
- py_imports_third_party
- py_imports_local
- imports_* (any import-related fields)

```json
"serialization": {
  "flat_table": {
    "strategy": "json_array_string",
    "separator": ",",
    "max_display_length": 500
  }
}
```

**Array fields (35 total):** column_headers, contracts_consumed, contracts_produced, declared_dependencies, deliverables, depends_on_file_ids, edge_flags, edges, enforced_by_file_ids, enforces_rule_ids, file_ids, generated_files, generator_ids, generated_by_file_ids, geu_ids, geu_set_ids, implements_geu_ids, imports_local, imports_stdlib, imports_third_party, layer_ids, outputs, path_aliases, policy_ids, produces_geu_ids, py_capability_tags, py_component_ids, py_deliverable_inputs, py_deliverable_interfaces, py_deliverable_kinds, py_deliverable_outputs, py_imports_local, py_imports_stdlib, py_imports_third_party, py_tool_versions

**Step 4: Add serialization to 6 object fields**

```json
"serialization": {
  "flat_table": {
    "strategy": "json_object_string",
    "max_display_length": 500
  }
}
```

**Object fields (6 total):** capabilities, coverage_metrics, py_security_risk_flags, relationships, schema_fields, test_metadata

**Verification:**
```powershell
python -c "import json; d=json.load(open('COLUMN_HEADERS/01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json')); dt_type=d['headers']['data_transformation']['value_schema']['type']; assert 'boolean' not in dt_type; print('✓ data_transformation type fixed'); missing=[h for h,s in d['headers'].items() if ('array' in str(s.get('value_schema',{}).get('type','')) or 'object' in str(s.get('value_schema',{}).get('type',''))) and 'serialization' not in s]; print(f'Missing serialization: {len(missing)}')"
# Expect: 0 missing
```

**Git Checkpoint:**
```powershell
git add COLUMN_HEADERS\01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json
git commit -m "B6: Fix data_transformation type and add serialization to 41 fields"
```

---

## Phase 5: Precedence Documentation (30 min)

### B7: Path Precedence + B9: Test Coverage Precedence
**Risk:** LOW | **Breaking:** NO | **Purpose:** Documentation

**Files to modify:**
1. `COLUMN_HEADERS\01260207201000000192_UNIFIED_SSOT_REGISTRY_DERIVATIONS.yaml`
2. `COLUMN_HEADERS\01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json`

**Step 1: Add precedence rules to DERIVATIONS.yaml**

⚠️ **Test YAML parser first:**
```powershell
python -c "import yaml; test='_metadata:\n  test: value\nfield1:\n  type: string\n'; print(yaml.safe_load(test))"
# If works, proceed with Option A; else use Option B (comments)
```

**Option A - _metadata supported (preferred):**

Add at top of DERIVATIONS.yaml:
```yaml
# Metadata: Field Precedence Rules
_metadata:
  path_field_precedence:
    order: [absolute_path, relative_path, canonical_path, directory_path, filename, path_aliases]
    rationale: When multiple path fields present, use this order to determine canonical path
  
  test_coverage_field_precedence:
    python_specific:
      precedence_group: test_coverage_python
      authoritative_for: ["*.py"]
      fields: [py_tests_executed, py_pytest_exit_code, py_coverage_percent]
      rationale: For Python files where py_analysis_success=true, Python-specific fields override general fields
    general:
      precedence_group: test_coverage_general
      fields: [has_tests, test_status, coverage_status]
```

**Option B - _metadata not supported (fallback):**

Add comment block at top:
```yaml
# =============================================================================
# FIELD PRECEDENCE RULES (Documentation Only)
# =============================================================================
#
# Path Field Precedence:
#   1. absolute_path (highest precedence)
#   2. relative_path
#   3. canonical_path
#   4. directory_path
#   5. filename
#   6. path_aliases (lowest precedence)
#
# Test Coverage Field Precedence:
#   For Python files (py_analysis_success=true):
#     Python-specific fields are authoritative:
#       py_tests_executed, py_pytest_exit_code, py_coverage_percent
#     General fields are fallback:
#       has_tests, test_status, coverage_status
# =============================================================================
```

**Step 2: Add path_aliases derivation** (append to DERIVATIONS.yaml):
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

**Step 3: Add precedence_group tags to COLUMN_DICTIONARY.json**

For Python-specific test fields:
```json
"py_tests_executed": {
  "precedence_group": "test_coverage_python",
  ...
},
"py_pytest_exit_code": {
  "precedence_group": "test_coverage_python",
  ...
},
"py_coverage_percent": {
  "precedence_group": "test_coverage_python",
  ...
}
```

For general test fields:
```json
"has_tests": {
  "precedence_group": "test_coverage_general",
  ...
},
"test_status": {
  "precedence_group": "test_coverage_general",
  ...
},
"coverage_status": {
  "precedence_group": "test_coverage_general",
  ...
}
```

**Verification:**
```powershell
python -c "import json; d=json.load(open('COLUMN_HEADERS/01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json')); test_fields=['py_tests_executed','py_pytest_exit_code','py_coverage_percent','has_tests','test_status','coverage_status']; for f in test_fields: print(f'{f}: {d[\"headers\"][f].get(\"precedence_group\", \"MISSING\")}')"
# All should have groups assigned
```

**Git Checkpoint:**
```powershell
git add COLUMN_HEADERS\01260207201000000192_UNIFIED_SSOT_REGISTRY_DERIVATIONS.yaml `
        COLUMN_HEADERS\01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json
git commit -m "B7+B9: Document path and test coverage precedence rules"
```

---

## Phase 6: Policy Reclassification (15 min) ⚠️ REVIEW REQUIRED

### B4: Reclassify Manual Fields
**Risk:** LOW-MEDIUM | **Breaking:** YES for automation tools | **Purpose:** Correct policy

⚠️ **IMPORTANT:** This changes update_policy for 6 fields from `manual_or_automated` to `manual_patch_only`. Automated tools expecting write access will be blocked.

**Pre-check: Search for automated writers**
```powershell
cd C:\Users\richg\Gov_Reg
Get-ChildItem -Recurse -Include *.py,*.js,*.ts -Exclude "*REGISTRY*" | 
    Select-String -Pattern "description|one_line_purpose|short_description|superseded_by|supersedes_entity_id|bundle_version" -Context 2,2 |
    Where-Object {$_.Line -match "(patch|write|update)"}
# Review results - if tools exist, add compatibility shims before proceeding
```

**File to modify:**
- `COLUMN_HEADERS\01260207201000000193_UNIFIED_SSOT_REGISTRY_WRITE_POLICY.yaml`

**Update 6 fields:**
```yaml
  description:
    rationale: Long-form documentation (max 2000 chars)
    null_policy: allow_null
    update_policy: manual_patch_only  # Changed from manual_or_automated
    writable_by: authorized_user

  one_line_purpose:
    rationale: Single-line file purpose (max 120 chars)
    null_policy: allow_null
    update_policy: manual_patch_only  # Changed from manual_or_automated
    writable_by: authorized_user

  short_description:
    rationale: One paragraph summary (max 250 chars)
    null_policy: allow_null
    update_policy: manual_patch_only  # Changed from manual_or_automated
    writable_by: authorized_user

  superseded_by:
    rationale: File ID that supersedes this record
    null_policy: allow_null
    update_policy: manual_patch_only  # Changed from manual_or_automated
    writable_by: authorized_user

  supersedes_entity_id:
    rationale: Entity ID that this record supersedes
    null_policy: allow_null
    update_policy: manual_patch_only  # Changed from manual_or_automated
    writable_by: authorized_user

  bundle_version:
    rationale: Version identifier for bundled artifacts
    null_policy: allow_null
    update_policy: manual_patch_only  # Changed from manual_or_automated
    writable_by: authorized_user
```

**Verification:**
```powershell
Select-String -Path "COLUMN_HEADERS\01260207201000000193_UNIFIED_SSOT_REGISTRY_WRITE_POLICY.yaml" `
              -Pattern "manual_or_automated" | 
    Where-Object {$_.Line -match "(description|one_line_purpose|short_description|superseded_by|supersedes_entity_id|bundle_version)"}
# Should return 0 matches
```

**Git Checkpoint:**
```powershell
git add COLUMN_HEADERS\01260207201000000193_UNIFIED_SSOT_REGISTRY_WRITE_POLICY.yaml
git commit -m "B4: Reclassify 6 fields from manual_or_automated to manual_patch_only"
```

---

## Phase 7: Design Decisions (OPTIONAL - 2 hours) 🔍 STAKEHOLDER REVIEW REQUIRED

### B8: Structural Design Changes
**Risk:** MEDIUM | **Breaking:** YES (rel_type deprecation) | **Requires:** Code review + migration plan

⚠️ **DO NOT EXECUTE without stakeholder approval**

This phase includes:
1. Deprecate `rel_type` in favor of `edge_type` (found in 20+ locations)
2. Add semantic notes for `generated` vs `is_generated`
3. Document `entity_kind` derivation from `is_directory`
4. Add description field length contracts
5. Scope `status` enum values

**Pre-check: Find rel_type usage**
```powershell
cd C:\Users\richg\Gov_Reg
Get-ChildItem -Recurse -Include *.py,*.js,*.ts,*.yaml,*.json -Exclude "*REGISTRY*","*backup*" |
    Select-String -Pattern "rel_type" -CaseSensitive |
    Group-Object Path |
    Select-Object Name, Count |
    Sort-Object Count -Descending
# DECISION POINT: Review all usages before deprecation
```

**See B8_IMPLEMENTATION_GUIDE.txt for full details**

**Recommendation:** Defer B8 until:
- Migration plan created for `rel_type` → `edge_type`
- Code references updated
- Dual-field compatibility period planned (6 months)

---

## Post-Execution Validation

### Validation Suite (15 min)

```powershell
cd C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY

# 1. Schema validation against live data
python -m jsonschema --instance 01999000042260124503_REGISTRY_file.json `
                     01999000042260124012_governance_registry_schema.v3.json
# Expect: No errors

# 2. Count registered py_* fields
(Select-String -Path "COLUMN_HEADERS\01260207201000000193_UNIFIED_SSOT_REGISTRY_WRITE_POLICY.yaml" -Pattern "^  py_").Count
# Expect: 2 (py_capability_facts_hash, py_capability_tags)

# 3. Verify no empty scopes
python -c "import json; d=json.load(open('COLUMN_HEADERS/01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json')); empty=sum(1 for v in d['headers'].values() if v.get('scope',{}).get('record_kinds_in')==[]); print(f'Empty scopes: {empty}')"
# Expect: 0

# 4. Verify no 'core' values
python -c "import json; import re; content=open('COLUMN_HEADERS/01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json').read(); print(f'core occurrences: {len(re.findall(chr(34)+\"core\"+chr(34), content))}')"
# Expect: 0

# 5. Verify data_transformation type fixed
python -c "import json; d=json.load(open('COLUMN_HEADERS/01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json')); print('boolean' in str(d['headers']['data_transformation']['value_schema']['type']))"
# Expect: False

# 6. Check git status
git status
# All changes should be committed

# 7. View commit history
git log --oneline -10
# Should see 5-6 commits from this remediation
```

---

## Rollback Procedures

### If validation fails:

**Option 1: Rollback individual phase**
```powershell
# Find the commit to revert
git log --oneline -10

# Revert specific commit
git revert <commit-hash>
```

**Option 2: Full rollback**
```powershell
# Reset to branch point
git reset --hard origin/main  # or appropriate branch

# Restore from backup if needed
$timestamp = "20260226_074000"  # Use actual timestamp from Pre-Flight
Remove-Item "C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY" -Recurse -Force
Copy-Item -Path "C:\Users\richg\Gov_Reg\01260207201000001133_backups\REGISTRY_pre_spec_remediation_$timestamp" `
          -Destination "C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY" `
          -Recurse
```

---

## Success Metrics

After completion, verify:

| Metric | Before | After | Status |
|--------|--------|-------|--------|
| Schema Coverage | ~183/185 fields | 185/185 fields | ✅ Target |
| Validation Errors | 2 (py_* fields) | 0 | ✅ Target |
| Empty Scopes | 40 | 0 | ✅ Target |
| Invalid 'core' | 9 | 0 | ✅ Target |
| Serialization Specs | 0 | 41 fields | ✅ Target |
| Immutable Derivations | 0 | 9 fields | ✅ Target |
| Precedence Rules | 0 | 2 groups | ✅ Target |

---

## Execution Checklist

### Phase 1: Critical Fields (30 min)
- [ ] Pre-flight backup created
- [ ] B1: py_capability_* fields registered (3 files)
- [ ] Schema validation passes
- [ ] Git commit created

### Phase 2: Immutable Fields (20 min)
- [ ] B3: 9 derivation entries added
- [ ] Git commit created

### Phase 3: Scope Fixes (1.5 hours)
- [ ] B5: 'core' → 'entity' replaced (9 fields)
- [ ] B5: Empty scopes assigned (40 fields)
- [ ] Verification passed
- [ ] Git commit created

### Phase 4: Serialization (1 hour)
- [ ] B6: data_transformation pre-check passed
- [ ] B6: Type fixed (boolean removed)
- [ ] B6: Array field serialization added (35 fields)
- [ ] B6: Object field serialization added (6 fields)
- [ ] Verification passed
- [ ] Git commit created

### Phase 5: Precedence (30 min)
- [ ] B7: YAML parser compatibility checked
- [ ] B7: Path precedence documented
- [ ] B7: path_aliases derivation added
- [ ] B9: Test coverage precedence groups added
- [ ] Git commit created

### Phase 6: Policy Reclassification (15 min)
- [ ] B4: Automated writer search completed
- [ ] B4: 6 fields reclassified
- [ ] Verification passed
- [ ] Git commit created

### Phase 7: Design Decisions (OPTIONAL)
- [ ] B8: Stakeholder review completed
- [ ] B8: rel_type usage audit completed
- [ ] B8: Migration plan approved
- [ ] B8: Changes applied (if approved)

### Post-Execution
- [ ] All validation checks passed
- [ ] Documentation updated
- [ ] Team notified of changes
- [ ] Branch merged (or PR created)

---

## Next Steps After Completion

1. **Update documentation:**
   - Document deprecated fields (rel_type if B8 executed)
   - Update COLUMN_DICTIONARY change log
   - Update registry schema version

2. **Notify teams:**
   - Alert automation tool owners of B4 changes
   - Share validation results
   - Document new field availability

3. **Plan future work:**
   - Schedule B8 stakeholder review
   - Plan rel_type migration (if deprecation approved)
   - Quarterly review of new fields

4. **Archive artifacts:**
   - Move implementation guides to completed/
   - Archive this plan
   - Update UNIFIED_REGISTRY_CLEANUP plan status

---

## Estimated Timeline

**Minimum viable execution (Phases 1-5):**
- Duration: 3.5 hours
- Risk: LOW
- Breaking changes: None

**Full execution (Phases 1-6):**
- Duration: 4 hours
- Risk: LOW-MEDIUM
- Breaking changes: B4 only (documented)

**With design decisions (Phases 1-7):**
- Duration: 6+ hours
- Risk: MEDIUM
- Breaking changes: B4 + B8 (requires review)

**Recommended approach:** Execute Phases 1-6, defer Phase 7 for stakeholder review.

---

**Plan Status:** READY FOR EXECUTION  
**Approval Required:** Phase 6 (B4) - review for automation tool impact  
**Deferral Recommended:** Phase 7 (B8) - design decisions need stakeholder input
