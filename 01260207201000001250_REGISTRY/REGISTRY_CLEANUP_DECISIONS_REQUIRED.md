# Registry Cleanup Decisions Required
**Document Version:** 1.0  
**Created:** 2026-02-23T04:37:52Z  
**Purpose:** Context and options for AI-assisted decision making  
**Status:** Awaiting decisions on 5 critical questions

---

## Executive Context

The Registry cleanup plan has completed all automated phases (file organization, deduplication). Manual schema editing phases (B1-B9) are documented but require decisions on architectural and compatibility issues discovered during analysis.

**Project:** Gov_Reg Registry SSOT Specification Remediation  
**Directory:** `C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY`  
**Live Data:** 1133+ file records in `01999000042260124503_REGISTRY_file.json`  
**Schema Files:** WRITE_POLICY.yaml, DERIVATIONS.yaml, schema.v3.json, COLUMN_DICTIONARY.json

---

## DECISION 1: rel_type Field Deprecation Strategy

### Background
The remediation plan proposes deprecating `rel_type` in favor of `edge_type` to eliminate duplicate concepts. However, code search revealed active usage.

### Current State
- **Usage Count:** 20+ references found across codebase
- **File Types:** Python code, JSON configurations, YAML policies
- **Key Files:**
  - `P_01260207233100000368_01999000042260125013_normalizer.py` (5 references)
  - `01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json` (7 references)
  - `01260207233100000528_input_formulas.json` (1 reference)
  - `01260207201000000284_test_snapshot.json` (1 reference)
  - Policy/mapping files: normalization_map.json, null_policy_map.json, update_policy_map.json

### Technical Details
- **Field Purpose:** Defines relationship type for edge records (record_kind="edge")
- **Data Type:** string
- **Current Policy:** Stored in WRITE_POLICY.yaml as manual field
- **Live Data Usage:** Unknown (need query: `SELECT COUNT(*) WHERE rel_type IS NOT NULL`)
- **Proposed Replacement:** `edge_type` (same purpose, clearer name)

### Impact Analysis

**If Deprecated Immediately:**
- ❌ 20+ code locations require simultaneous update
- ❌ Risk of breaking normalizer.py (core data processing)
- ❌ Test snapshots may fail validation
- ⚠️ No backward compatibility for external tools reading rel_type
- ✅ Cleaner schema going forward

**If Deferred:**
- ✅ Maintain current functionality
- ✅ Time to plan migration strategy
- ✅ Can run dual-field period (both rel_type and edge_type)
- ⚠️ Technical debt persists
- ⚠️ Duplicate concept remains in spec

**If Dual-Field Approach:**
- ✅ Gradual migration possible
- ✅ Backward compatible
- ✅ Both fields work during transition (6-12 months)
- ⚠️ Requires maintaining both fields temporarily
- ⚠️ Need reconciliation logic (edge_type takes precedence)

### Options

**Option A: Immediate Deprecation (NOT RECOMMENDED)**
- Mark `rel_type` as deprecated in WRITE_POLICY.yaml and COLUMN_DICTIONARY.json
- Set `superseded_by: edge_type`
- Set `removal_target: "2026-06-01"`
- **Requires:** Updating all 20+ code references NOW
- **Risk:** HIGH - may break normalizer, tests
- **Time:** 8-10 hours immediate work

**Option B: Deferred Deprecation (CONSERVATIVE)**
- Document `rel_type` as legacy but supported
- Add `edge_type` as preferred field
- No deprecation markers
- Schedule migration for Phase 2 (after assessment)
- **Requires:** Nothing immediate
- **Risk:** LOW - no changes
- **Time:** 0 hours now, deferred to future

**Option C: Dual-Field Transition (RECOMMENDED)**
- Add `edge_type` to schema alongside `rel_type`
- Both fields valid for 6 months
- Update normalizer.py to populate both fields
- Add reconciliation rule: `COALESCE(edge_type, rel_type)` in queries
- Gradually migrate code to use edge_type
- Deprecate rel_type in Q3 2026
- **Requires:** 2-3 hours to add edge_type, update normalizer
- **Risk:** LOW-MEDIUM - controlled migration
- **Time:** 2-3 hours now + periodic migration

**Option D: Rename in Place (ALTERNATIVE)**
- Keep `rel_type` but update documentation
- Acknowledge it as permanent (not duplicate)
- Clarify semantic distinction if any exists
- **Requires:** Documentation updates only
- **Risk:** VERY LOW
- **Time:** 30 minutes

### Data Needed for Decision
1. **Query live data:** How many records use rel_type vs edge_type?
   ```python
   import json
   with open('01999000042260124503_REGISTRY_file.json', 'r', encoding='utf-8') as f:
       reg = json.load(f)
   rel_type_count = sum(1 for r in reg['files'] if r.get('rel_type') is not None)
   edge_type_count = sum(1 for r in reg['files'] if r.get('edge_type') is not None)
   print(f"rel_type: {rel_type_count}, edge_type: {edge_type_count}")
   ```

2. **Assess normalizer.py usage:** Is rel_type critical to data ingestion pipeline?

3. **Stakeholder input:** Is there semantic difference between rel_type and edge_type?

### Recommendation Framework

**Choose Option A if:**
- Live data shows NO usage of rel_type (0 records)
- Team can update all 20+ references within 1 day
- No external systems depend on rel_type

**Choose Option B if:**
- Uncertain about migration complexity
- Want to minimize immediate risk
- Can schedule proper assessment later

**Choose Option C if:**
- Both fields are used in live data
- Need gradual migration path
- Want to maintain compatibility during transition

**Choose Option D if:**
- Semantic difference exists between fields
- Name confusion is not a real issue
- Want to avoid migration entirely

---

## DECISION 2: _metadata Key Support in DERIVATIONS.yaml

### Background
Phase B7 needs to document field precedence rules (path fields, test coverage). Two approaches exist depending on YAML parser capabilities.

### Current State
- **File:** `01260207201000000192_UNIFIED_SSOT_REGISTRY_DERIVATIONS.yaml`
- **Purpose:** Define field derivation formulas and dependencies
- **Parser:** Unknown validator (need to check codebase)
- **Current Structure:** Field-level definitions only
- **Proposed Addition:** Metadata section for documentation

### Technical Details

**Option A: _metadata Key (Structured)**
```yaml
_metadata:
  path_field_precedence:
    order: [absolute_path, relative_path, canonical_path, ...]
  test_coverage_field_precedence:
    python_specific:
      fields: [py_tests_executed, py_pytest_exit_code, ...]
    general:
      fields: [has_tests, test_status, coverage_status]

# Field definitions below
field_name:
  depends_on: []
  type: string
  ...
```

**Pros:**
- ✅ Machine-readable structure
- ✅ Can be parsed programmatically
- ✅ Easier to validate and query
- ✅ Clean separation of metadata vs fields

**Cons:**
- ❌ May fail if validator rejects unknown keys
- ❌ Unknown if current parser supports _metadata
- ❌ Risk of breaking existing tooling

**Option B: Comment Block (Safe)**
```yaml
# =============================================================================
# FIELD PRECEDENCE RULES (Documentation Only - Not Processed)
# =============================================================================
#
# Path Field Precedence:
#   1. absolute_path (highest precedence)
#   2. relative_path
#   3. canonical_path
#   ...
#
# Test Coverage Field Precedence:
#   Python-specific fields (py_tests_executed, py_pytest_exit_code, py_coverage_percent)
#   are authoritative over general fields (has_tests, test_status, coverage_status)
#
# =============================================================================

# Field definitions below
field_name:
  depends_on: []
  type: string
  ...
```

**Pros:**
- ✅ Guaranteed to work (comments always safe)
- ✅ No parser compatibility issues
- ✅ Zero risk to existing system
- ✅ Human-readable documentation

**Cons:**
- ❌ Not machine-readable
- ❌ Can't be queried programmatically
- ❌ Less structured
- ❌ May be ignored by tooling

### Impact Analysis

**Current System Dependencies:**
- Unknown if any tools parse DERIVATIONS.yaml programmatically
- Unknown if validator has schema for DERIVATIONS.yaml
- No evidence of _metadata usage elsewhere in codebase

### Data Needed for Decision
1. **Test _metadata support:**
   ```python
   import yaml
   test_yaml = '''
   _metadata:
     test: value
   field1:
     type: string
   '''
   try:
       parsed = yaml.safe_load(test_yaml)
       print("✓ _metadata key accepted:", parsed)
   except Exception as e:
       print("✗ _metadata key rejected:", e)
   ```

2. **Search for DERIVATIONS.yaml parser:**
   ```powershell
   Get-ChildItem -Path "C:\Users\richg\Gov_Reg" -Recurse -Include *.py -File | 
       Select-String -Pattern "DERIVATIONS.yaml" -Context 2,2
   ```

3. **Check for existing _metadata usage:**
   ```powershell
   Get-ChildItem -Path "C:\Users\richg\Gov_Reg" -Recurse -Include *.yaml,*.yml -File |
       Select-String -Pattern "^_metadata:" -CaseSensitive
   ```

### Options

**Option A: Use _metadata Key**
- Test parser first with small sample
- If successful, use structured approach
- **Risk:** LOW if tested, HIGH if not tested
- **Benefit:** Future-proof, machine-readable

**Option B: Use Comment Block**
- Immediately safe, no testing required
- Works regardless of parser
- **Risk:** ZERO
- **Benefit:** Guaranteed compatibility

**Option C: Separate Documentation File**
- Create `FIELD_PRECEDENCE_RULES.md` in docs/
- Keep DERIVATIONS.yaml pristine
- Reference doc file in comments
- **Risk:** ZERO to existing system
- **Benefit:** Most flexible, can include examples

### Recommendation Framework

**Choose Option A if:**
- Test confirms _metadata is supported
- Future tooling will benefit from structured metadata
- Want to keep everything in one file

**Choose Option B if:**
- Cannot test parser compatibility now
- Want zero-risk approach
- Documentation is primarily for humans

**Choose Option C if:**
- Want most flexibility for documentation
- Precedence rules need extensive examples
- Prefer separation of concerns

---

## DECISION 3: Empty Scope Assignment Strategy (40 Fields)

### Background
Phase B5 identified 40 fields with empty `record_kinds_in: []` scopes in COLUMN_DICTIONARY.json. Each must be assigned to record types: entity, edge, generator, or metadata.

### Current State
- **File:** `01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json`
- **Issue:** 40 fields have `"record_kinds_in": []` (invalid - should never be empty)
- **Impact:** Validation failures, unclear field applicability

### Technical Details

**Record Types:**
- **entity:** File/directory records (most common, ~90% of data)
- **edge:** Relationship records (dependencies, references)
- **generator:** Generator/template records (creates other files)
- **metadata:** System metadata records (scans, configurations)

**Universal Fields (apply to all record types):**
- `record_id`, `record_kind`, `created_utc`, `updated_utc`, `scan_id`, `created_by`, `registered_by`, `registration_time`

### Affected Fields (40 total)

**Likely Entity-Specific (files/directories):**
```
anchor_file_id, artifact_kind, canonicality, deliverables, depends_on_file_ids,
description, one_line_purpose, short_description, notes, status, file_type,
entity_kind, layer, module_id, bundle_key, bundle_role, bundle_version,
superseded_by, supersedes_entity_id, capabilities, coverage_metrics,
schema_fields, test_metadata, is_directory, filename, extension, size_bytes,
absolute_path, relative_path, canonical_path, directory_path, path_aliases,
sha256, collected_by
```

**Likely Edge-Specific (relationships):**
```
edge_type, source_file_id, target_file_id, source_entity_id, target_entity_id,
directionality, rel_type, confidence, relationships, edge_flags, edges
```

**Likely Generator-Specific:**
```
generator_id, generator_ids, generated_files, generated_by_file_ids
```

**Possibly Universal:**
```
column_headers, contracts_consumed, contracts_produced, declared_dependencies,
enforced_by_file_ids, enforces_rule_ids, file_ids, geu_ids, geu_set_ids,
implements_geu_ids, layer_ids, outputs, policy_ids, produces_geu_ids
```

### Assignment Strategies

**Strategy A: Conservative (Entity-Only)**
- Assign most fields to `["entity"]` unless clearly edge/generator-specific
- **Reasoning:** 90%+ of records are entities
- **Risk:** LOW - most restrictive
- **Downside:** May need to expand scopes later if fields used in edges

**Strategy B: Generous (Multiple Types)**
- Assign universal fields to all 4 types: `["entity", "edge", "generator", "metadata"]`
- Assign ambiguous fields to 2-3 types
- **Reasoning:** Better to be permissive initially
- **Risk:** MEDIUM - may allow invalid combinations
- **Downside:** Less validation enforcement

**Strategy C: Data-Driven (Query Live Data)**
- Query actual record_kind distribution for each field
- Assign scopes based on observed usage
- **Reasoning:** Most accurate to reality
- **Risk:** LOW - evidence-based
- **Downside:** Requires data analysis (2-3 hours)

### Data Needed for Decision

**Option 1: Quick Heuristic (30 minutes)**
```python
import json

# Load current data
with open('01999000042260124503_REGISTRY_file.json', 'r', encoding='utf-8') as f:
    reg = json.load(f)

# Analyze record_kind distribution
record_kinds = {}
for r in reg['files']:
    kind = r.get('record_kind', 'unknown')
    record_kinds[kind] = record_kinds.get(kind, 0) + 1

print("Record kind distribution:", record_kinds)
# Expected output: {'entity': ~1000, 'edge': ~100, 'generator': ~10, 'metadata': ~10}
```

**Option 2: Field Usage Analysis (2-3 hours)**
```python
import json
from collections import defaultdict

with open('01999000042260124503_REGISTRY_file.json', 'r', encoding='utf-8') as f:
    reg = json.load(f)

# For each of the 40 empty-scope fields, find which record_kinds use it
empty_scope_fields = [
    'edge_type', 'source_file_id', 'description', # ... (all 40)
]

field_usage = defaultdict(lambda: defaultdict(int))

for record in reg['files']:
    record_kind = record.get('record_kind', 'unknown')
    for field in empty_scope_fields:
        if field in record and record[field] is not None:
            field_usage[field][record_kind] += 1

# Print results
for field, kinds in sorted(field_usage.items()):
    print(f"{field}: {dict(kinds)}")
    # Example output: edge_type: {'edge': 95, 'entity': 0}
```

### Options

**Option A: Conservative Assignment (30 min)**
- Entity-specific: 30 fields → `["entity"]`
- Edge-specific: 8 fields → `["edge"]`
- Generator-specific: 2 fields → `["generator"]`
- Universal: 0 fields (none identified)
- **Pros:** Fast, safe, clear boundaries
- **Cons:** May need revision if fields appear in other record types

**Option B: Data-Driven Assignment (3 hours)**
- Run usage analysis script
- Assign based on actual record_kind distribution
- Include record type if field appears in >5% of records of that type
- **Pros:** Most accurate, evidence-based
- **Cons:** Time-consuming, may reveal edge cases

**Option C: Hybrid (1 hour)**
- Obvious assignments (edge_type→edge, file_id→entity) done manually
- Ambiguous fields (capabilities, geu_ids) checked in data
- **Pros:** Balance of speed and accuracy
- **Cons:** Requires judgment calls

### Recommendation Framework

**Choose Option A if:**
- Need to complete B5 quickly
- Comfortable revising scopes later if needed
- Clear patterns exist (most fields are obviously entity-specific)

**Choose Option B if:**
- Have 3 hours available for analysis
- Want definitive, evidence-based assignments
- Concerned about validation false positives/negatives

**Choose Option C if:**
- Want balance of speed and accuracy
- Can identify ~20 obvious assignments, need data for ~20 ambiguous
- Willing to iterate

---

## DECISION 4: data_transformation Type Tightening

### Background
Phase B6 pre-check confirmed NO boolean values exist in live data for `data_transformation` field. Current type is `boolean|string|null`, can be tightened to `string|null`.

### Current State
- **Field:** `data_transformation` in COLUMN_DICTIONARY.json
- **Current Type:** `["boolean", "string", "null"]`
- **Live Data:** 0 records with boolean values (pre-check passed ✓)
- **Proposed Type:** `["string", "null"]`
- **Enum Values:** `["normalize", "aggregate", "filter", "transform", "enrich", null]`

### Technical Details

**Current Schema (Permissive):**
```json
"data_transformation": {
  "value_schema": {
    "type": ["boolean", "string", "null"],
    ...
  }
}
```

**Proposed Schema (Strict):**
```json
"data_transformation": {
  "value_schema": {
    "type": ["string", "null"],
    "enum": ["normalize", "aggregate", "filter", "transform", "enrich", null]
  }
}
```

### Impact Analysis

**Benefits of Tightening:**
- ✅ More precise validation
- ✅ Prevents accidental boolean assignment in future
- ✅ Clarifies valid values via enum
- ✅ Pre-check confirms safe (0 boolean values in live data)

**Risks of Tightening:**
- ⚠️ If external tools write boolean values, they'll fail validation
- ⚠️ If enum list is incomplete, valid strings may be rejected
- ⚠️ Cannot revert without schema migration

**If NOT Tightened:**
- ⚠️ Boolean type remains in spec despite never being used
- ⚠️ Future developers may mistakenly use boolean
- ✅ Maximum flexibility preserved

### Data Validation

**Pre-Check Results (Already Completed):**
```python
# This was run during B6 pre-check:
boolean_values = [r.get('data_transformation') for r in reg['files'] 
                  if 'data_transformation' in r and isinstance(r['data_transformation'], bool)]
# Result: [] (empty - no boolean values found)
```

**Additional Validation Needed:**
```python
# Check all string values match proposed enum
import json
with open('01999000042260124503_REGISTRY_file.json', 'r', encoding='utf-8') as f:
    reg = json.load(f)

dt_values = set(r.get('data_transformation') for r in reg['files'] 
                if 'data_transformation' in r and r['data_transformation'] is not None)
proposed_enum = {"normalize", "aggregate", "filter", "transform", "enrich"}
unexpected = dt_values - proposed_enum

if unexpected:
    print(f"⚠ Values not in enum: {unexpected}")
else:
    print("✓ All values match proposed enum")
```

### Options

**Option A: Tighten Type + Add Enum (RECOMMENDED)**
- Change type to `["string", "null"]`
- Add enum with 5 known values
- **Risk:** LOW (pre-check passed)
- **Benefit:** Best validation, clear contract

**Option B: Tighten Type, No Enum**
- Change type to `["string", "null"]`
- Allow any string value
- **Risk:** VERY LOW
- **Benefit:** Flexible, safe

**Option C: Keep Boolean Type**
- Leave as `["boolean", "string", "null"]`
- No changes
- **Risk:** ZERO
- **Benefit:** Maximum flexibility, no migration

**Option D: Deprecate Field**
- If unused or legacy, mark deprecated
- Set to null-only: `["null"]`
- **Risk:** MEDIUM if field is important
- **Benefit:** Cleanest if field is obsolete

### Data Needed for Decision

1. **Enum completeness check** (run script above)
2. **Usage frequency:**
   ```python
   usage_count = sum(1 for r in reg['files'] if r.get('data_transformation') is not None)
   print(f"data_transformation used in {usage_count} of {len(reg['files'])} records")
   ```
3. **Check if field is documented/important:**
   - Search for `data_transformation` in WRITE_POLICY.yaml
   - Search for usage in Python code

### Recommendation Framework

**Choose Option A if:**
- Enum validation check passes (all values in enum)
- Field is actively used and important
- Want strictest validation

**Choose Option B if:**
- Enum validation finds unexpected values
- Want to tighten type but keep flexibility
- Concerned about false positives

**Choose Option C if:**
- Uncertain about enum completeness
- Want zero-risk approach
- Boolean type removal not critical

**Choose Option D if:**
- Field is rarely used (< 1% of records)
- Field is legacy/obsolete
- Stakeholders confirm field can be deprecated

---

## DECISION 5: COLUMN_DICTIONARY Serialization Strategy (41 Fields)

### Background
Phase B6 identified 41 array/object fields lacking flat-table serialization specs. When exporting to CSV/tabular formats, these fields need serialization rules.

### Current State
- **File:** `01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json`
- **Issue:** 35 array fields + 6 object fields have no `serialization` key
- **Impact:** Undefined behavior when exporting to CSV, inconsistent display
- **Standard Strategies:** json_array_string, json_object_string, delimited_list

### Technical Details

**Array Fields (35 total):**
```
column_headers, contracts_consumed, contracts_produced, deliverables,
depends_on_file_ids, edge_flags, edges, file_ids, generated_files,
generator_ids, geu_ids, layer_ids, outputs, path_aliases, policy_ids,
py_capability_tags, py_component_ids, py_deliverable_inputs, py_imports_*,
implements_geu_ids, imports_*, produces_geu_ids, tool_versions, etc.
```

**Object Fields (6 total):**
```
capabilities, coverage_metrics, py_security_risk_flags, relationships,
schema_fields, test_metadata
```

**Proposed Default Strategy:**
- Arrays: `"strategy": "json_array_string"` with `max_display_length: 200`
- Objects: `"strategy": "json_object_string"` with `max_display_length: 500`
- Import fields: `max_display_length: 500` (longer module paths)

### Serialization Strategies Explained

**Strategy 1: json_array_string**
```json
"serialization": {
  "flat_table": {
    "strategy": "json_array_string",
    "separator": ",",
    "max_display_length": 200
  }
}
```
- Converts: `["a", "b", "c"]` → `'["a", "b", "c"]'` (JSON string in CSV cell)
- **Pros:** Reversible, preserves structure
- **Cons:** Less human-readable in CSV

**Strategy 2: delimited_list**
```json
"serialization": {
  "flat_table": {
    "strategy": "delimited_list",
    "separator": "; ",
    "max_display_length": 200
  }
}
```
- Converts: `["a", "b", "c"]` → `"a; b; c"` (plain text in CSV cell)
- **Pros:** More readable, Excel-friendly
- **Cons:** Lossy if items contain separator, not reversible

**Strategy 3: count_only**
```json
"serialization": {
  "flat_table": {
    "strategy": "count_only"
  }
}
```
- Converts: `["a", "b", "c"]` → `"3"` (just the count)
- **Pros:** Minimal, useful for metrics
- **Cons:** Loses all detail, only for large arrays

### Special Considerations

**Import Fields (py_imports_*, imports_*):**
- Module paths can be very long: `my.very.long.package.name.submodule`
- Proposed: `max_display_length: 500` (vs 200 for others)
- Alternative: Use count_only if imports are rarely inspected in CSV

**Relationship/Edge Arrays:**
- `edges`, `edge_flags`, `relationships` may be large (100+ items)
- Options:
  - json_array_string with truncation
  - count_only (just show count)
  - First 10 items + "... and N more"

**Complex Objects (capabilities, coverage_metrics):**
- Nested structure may not fit well in CSV
- json_object_string preserves structure but unreadable
- Alternative: Flatten to multiple columns or skip serialization

### Data Needed for Decision

**Array Size Analysis:**
```python
import json
from statistics import mean, median

with open('01999000042260124503_REGISTRY_file.json', 'r', encoding='utf-8') as f:
    reg = json.load(f)

array_fields = [
    'py_imports_stdlib', 'depends_on_file_ids', 'edges', 
    'py_capability_tags', # ... all 35
]

for field in array_fields:
    sizes = [len(r.get(field, [])) for r in reg['files'] if isinstance(r.get(field), list)]
    if sizes:
        print(f"{field}: min={min(sizes)}, max={max(sizes)}, avg={mean(sizes):.1f}, median={median(sizes)}")
    else:
        print(f"{field}: no data")
```

**String Length Analysis:**
```python
# Check if 200 chars is sufficient for most arrays
import json

with open('01999000042260124503_REGISTRY_file.json', 'r', encoding='utf-8') as f:
    reg = json.load(f)

for field in array_fields:
    json_lengths = [len(json.dumps(r.get(field))) for r in reg['files'] 
                    if field in r and r[field] is not None]
    if json_lengths:
        over_200 = sum(1 for l in json_lengths if l > 200)
        over_500 = sum(1 for l in json_lengths if l > 500)
        print(f"{field}: {over_200} exceed 200 chars, {over_500} exceed 500 chars")
```

### Options

**Option A: Uniform Strategy (FASTEST)**
- All 35 arrays → json_array_string, max_display_length: 200
- All 6 objects → json_object_string, max_display_length: 500
- Import fields → exception: max_display_length: 500
- **Pros:** Simple, consistent, 30 minutes to implement
- **Cons:** May truncate important data, one-size-fits-all

**Option B: Differentiated Strategy (OPTIMAL)**
- Small arrays (< 10 items avg) → delimited_list (human-readable)
- Large arrays (> 10 items avg) → json_array_string (preserves structure)
- Huge arrays (> 50 items avg) → count_only (metrics only)
- Objects → json_object_string or skip
- Import fields → 500 char limit
- **Pros:** Optimized per field characteristics
- **Cons:** Requires data analysis (2 hours), more complex

**Option C: Conservative (NO TRUNCATION)**
- All fields → json_array_string, no max_display_length
- Accept that CSV cells may be huge
- **Pros:** No data loss, simple
- **Cons:** Unwieldy CSV files, Excel may struggle

**Option D: Minimal Serialization**
- Only serialize fields used in reports/exports
- Skip serialization for internal-only fields
- Add serialization later as needed
- **Pros:** Least work, no premature decisions
- **Cons:** May cause issues when exporting

### Recommendation Framework

**Choose Option A if:**
- Need to complete B6 quickly (< 1 hour)
- CSV exports are rarely used
- Truncation is acceptable

**Choose Option B if:**
- CSV exports are important
- Have 2 hours for data analysis
- Want optimal user experience

**Choose Option C if:**
- Data loss is unacceptable
- CSV file size not a concern
- Want reversible serialization

**Choose Option D if:**
- CSV exports not used yet
- Want to defer decision
- Prefer iterative approach

---

## DECISION SUMMARY TABLE

| Decision | Priority | Risk if Wrong Choice | Time Required | Blocking |
|----------|----------|---------------------|---------------|----------|
| 1. rel_type deprecation | HIGH | Breaking changes, data loss | 2-8 hours | No |
| 2. _metadata support | LOW | Parse errors | 30 min - 1 hour | B7, B9 |
| 3. Scope assignments | MEDIUM | Validation false positives | 30 min - 3 hours | B5 |
| 4. data_transformation type | LOW | Rejected valid data | 15 min | B6 |
| 5. Serialization strategy | LOW | Poor CSV exports | 30 min - 2 hours | B6 |

---

## RECOMMENDED DECISION SEQUENCE

**Phase 1: Quick Wins (Can decide immediately)**
1. **Decision 4** - data_transformation type (Option A or B)
2. **Decision 2** - _metadata support (Option B if unsure)

**Phase 2: Data-Driven (Requires 1-2 hour analysis)**
3. **Decision 3** - Scope assignments (Option C - hybrid approach)
4. **Decision 5** - Serialization (Option A unless CSV exports critical)

**Phase 3: Strategic (Requires stakeholder input)**
5. **Decision 1** - rel_type deprecation (Option C - dual-field recommended)

---

## VALIDATION COMMANDS

After each decision is implemented, run:

```powershell
# Schema validation
python -m jsonschema --instance 01999000042260124503_REGISTRY_file.json 01999000042260124012_governance_registry_schema.v3.json

# Column dictionary validation (if schema exists)
if (Test-Path "schemas/column_dictionary_schema.json") {
    python -m jsonschema --instance 01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json schemas/column_dictionary_schema.json
}

# Git checkpoint
git add .
git commit -m "Decision N: [description]"
```

---

## APPENDIX: Quick Decision Tree

```
START HERE

Q: Do you need rel_type deprecation NOW?
├─ YES → Run full code migration (8 hours) → Option 1A
└─ NO → Is gradual migration acceptable?
   ├─ YES → Dual-field approach (2 hours) → Option 1C ✓
   └─ NO → Defer entirely → Option 1B

Q: Can you test _metadata YAML support?
├─ YES → Test, if passes → Option 2A
└─ NO → Use comments → Option 2B ✓

Q: Do you have 3 hours for scope analysis?
├─ YES → Data-driven assignments → Option 3B
└─ NO → Conservative manual assignments → Option 3A ✓

Q: Do enum values cover all data_transformation strings?
├─ YES → Tighten with enum → Option 4A ✓
└─ UNKNOWN → Tighten without enum → Option 4B

Q: Are CSV exports critical to your workflow?
├─ YES → Analyze + optimize → Option 5B
└─ NO → Uniform strategy → Option 5A ✓
```

**✓ = Recommended default choice**

---

## METADATA

**Document Type:** Decision Support  
**Intended Audience:** AI decision engine, technical lead  
**Dependencies:** B1-B9 implementation guides  
**Related Files:** 
- UNIFIED_REGISTRY_CLEANUP_AND_REMEDIATION_PLAN.md
- IMPLEMENTATION_MASTER_INDEX.md
- B1-B9_IMPLEMENTATION_GUIDE.txt files

**Change Log:**
- 2026-02-23T04:37:52Z - Initial version (5 decisions documented)
