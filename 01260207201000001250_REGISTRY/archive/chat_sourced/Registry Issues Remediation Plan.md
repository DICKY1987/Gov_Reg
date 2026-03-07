# Registry Issues Remediation Plan

## Context

This plan addresses all registry spec inconsistencies identified in the current chat session. Issues were surfaced from three sources:
1. **ChatGPT audit** (`ChatGPT-Registry Explanation.md`) — structural schema problems flagged 2026-02-21/22
2. **Phase 0 next-steps** (`PHASE_0_A11_SOLUTION/README.md`) — two confirmed active violations (B5, B7) left as Phase 1 work
3. **Formula sheet audit** (`formula_sheet_classification.csv`) — 47 columns classified "inconsistent"

**No live data (`REGISTRY_file.json`) is modified in any phase.** All changes are to spec/policy files only.

---

## Critical Files

| File | Role |
|------|------|
| `01260207201000001250_REGISTRY/01260207201000000193_UNIFIED_SSOT_REGISTRY_WRITE_POLICY.yaml` | Write policies — missing all 37 `py_*` entries |
| `01260207201000001250_REGISTRY/01260207201000000192_UNIFIED_SSOT_REGISTRY_DERIVATIONS.yaml` | Derivation formulas — missing `py_*` and immutable INPUT fields |
| `01260207201000001250_REGISTRY/01999000042260124012_governance_registry_schema.v3.json` | JSON Schema (draft-07, `additionalProperties: false`) — no `py_*` properties |
| `01260207201000001250_REGISTRY/01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json` | Master 185-column dictionary — scope, type, serialization issues |
| `01260207201000001250_REGISTRY/01999000042260124503_REGISTRY_file.json` | **READ ONLY** — used for discovery in Phase 2 only |

---

## Phase 1 — Register 37 `py_*` Fields (Active Violation B5)
**Risk: LOW-MEDIUM | Effort: ~3h | Priority: CRITICAL**

These fields exist in live data but have zero spec coverage — write policy validator fails, JSON schema rejects all Python records.

### Changes

**`WRITE_POLICY.yaml`** — Append 37 entries, all with pattern:
```yaml
  py_<field>:
    rationale: <one-line>
    null_policy: allow_null
    update_policy: recompute_on_build
    writable_by: tool_only
```
Array-typed fields also get `merge_strategy: set_union`.

Fields: `py_analysis_run_id`, `py_analysis_success`, `py_analyzed_at_utc`, `py_ast_dump_hash`, `py_ast_parse_ok`, `py_canonical_candidate_score`, `py_canonical_text_hash`, `py_capability_facts_hash`, `py_capability_tags`, `py_complexity_cyclomatic`, `py_component_artifact_path`, `py_component_count`, `py_component_ids`, `py_coverage_percent`, `py_defs_classes_count`, `py_defs_functions_count`, `py_defs_public_api_hash`, `py_deliverable_inputs`, `py_deliverable_interfaces`, `py_deliverable_kinds`, `py_deliverable_outputs`, `py_deliverable_signature_hash`, `py_imports_hash`, `py_imports_local`, `py_imports_stdlib`, `py_imports_third_party`, `py_io_surface_flags`, `py_overlap_best_match_file_id`, `py_overlap_group_id`, `py_overlap_similarity_max`, `py_pytest_exit_code`, `py_quality_score`, `py_security_risk_flags`, `py_static_issues_count`, `py_tests_executed`, `py_tool_versions`, `py_toolchain_id`

**`DERIVATIONS.yaml`** — Append 37 entries with `INPUT` passthrough pattern:
```yaml
  py_<field>:
    depends_on: []
    error_policy: set_null
    type: string|boolean|integer|number|array   # per field
    trigger: recompute_on_build
    null_behavior: allow  # (set_empty_array for array types)
    formula: COALESCE(INPUT.py_<field>, NULL)
    rationale: Provided directly by Python analysis tool; null for non-Python files
```

**`governance_registry_schema.v3.json`** — Add all 37 as properties in `FileRecord.properties`. Types:
- `string|null`: run_id, timestamps, hashes, path, group_id, match_file_id
- `boolean|null`: analysis_success, ast_parse_ok, tests_executed
- `integer|null`: defs counts, component_count, pytest_exit_code, static_issues_count
- `number|null` (0.0–1.0 or 0–100): quality_score, coverage_percent, similarity_max, candidate_score, cyclomatic (use `minimum: 0`)
- `array` (items: string): capability_tags, component_ids, deliverable_kinds, deliverable_inputs, deliverable_outputs, deliverable_interfaces, imports_stdlib, imports_third_party, imports_local, io_surface_flags, security_risk_flags, tool_versions

### Verification
```bash
# Count new entries in write policy
grep -c "^  py_" WRITE_POLICY.yaml  # expect 37

# Count new entries in derivations
grep -c "^  py_" DERIVATIONS.yaml  # expect 37

# JSON schema validation against live registry — expect 0 additionalProperties errors
python -m jsonschema --instance REGISTRY_file.json governance_registry_schema.v3.json
```

---

## Phase 2 — Add 8 Undeclared Fields to Schema (Active Violation B7)
**Risk: LOW | Effort: ~2h | Priority: HIGH**

Fields used in live records but absent from `FileRecord.properties` in `governance_registry_schema.v3.json`. Causes hard `additionalProperties` failures.

### Pre-work (required)
Diff live registry keys against schema `FileRecord.properties` keys:
```python
import json
reg = json.load(open("REGISTRY_file.json"))
schema = json.load(open("governance_registry_schema.v3.json"))
schema_keys = set(schema["definitions"]["FileRecord"]["properties"].keys())
live_keys = set(k for r in reg["files"] for k in r.keys())
print(live_keys - schema_keys)  # exact 8+ undeclared fields
```
Likely candidates: `record_kind`, `one_line_purpose`, `notes`, `short_description`, `status`, `entity_kind`, `scope`, `created_by`. Confirm before editing.

### Changes
**`governance_registry_schema.v3.json`** — Add each confirmed undeclared field to `FileRecord.properties` with correct type from WRITE_POLICY rationale. Example:
```json
"record_kind": {"type": "string", "enum": ["entity","relationship","metadata","generator"]},
"one_line_purpose": {"type": ["string","null"], "maxLength": 120},
"notes": {"type": ["string","null"]},
"status": {"type": ["string","null"], "enum": ["active","archived","deprecated","legacy_read_only",null]}
```

### Verification
Re-run JSON schema validation — expect 0 `additionalProperties` errors.

---

## Phase 3 — Fix 9 "Immutable But No Derivation" Fields (Formula Sheet B1)
**Risk: LOW | Effort: ~1h**

These INPUT-passthrough fields are set once at record creation and never recomputed. They need `on_create_only` derivation entries to resolve the formula sheet "inconsistent" flag.

Fields: `created_by`, `directionality`, `edge_type`, `record_kind`, `rel_type`, `source_entity_id`, `source_file_id`, `target_entity_id`, `target_file_id`

### Changes
**`DERIVATIONS.yaml`** — Add 9 entries with `trigger: on_create_only` and `formula: COALESCE(INPUT.<field>, NULL)` (or `INPUT.<field>` for required fields like `record_kind`).

### Verification
Regenerate `formula_sheet_classification.csv` — expect 0 rows with "immutable but no derivation."

---

## Phase 4 — Fix ~6 "manual_or_automated Requires Derivation" Fields (Formula Sheet B2)
**Risk: LOW-MEDIUM | Effort: ~2h**

Many `manual_or_automated` fields have no derivation formula. Most should be reclassified to `manual_patch_only` (they are genuinely user-only editable). A few already have DERIVATIONS shadow-column entries (`canonicality`, `status`, `entity_kind`, `bundle_key`, `bundle_role`, `artifact_kind`, `layer`) — those stay as `manual_or_automated`.

### Pre-work (required)
Cross-check each "inconsistent" B2 row in `formula_sheet_classification.csv` against both WRITE_POLICY.yaml (current policy) and DERIVATIONS.yaml (existing formula). Identify exact fields still at `manual_or_automated` without a derivation entry.

Confirmed changes needed:
- `description`, `one_line_purpose`, `short_description`, `superseded_by`, `supersedes_entity_id`, `bundle_version` → change to `manual_patch_only`

### Changes
**`WRITE_POLICY.yaml`** — Change `update_policy: manual_or_automated` → `manual_patch_only` for the confirmed set.

### Verification
Regenerate `formula_sheet_classification.csv` — expect 0 remaining "inconsistent" rows total (combined with Phase 3).

---

## Phase 5 — Fix Scope Issues: Empty Scopes (C4) and Invalid `core` Enum (C5)
**Risk: LOW | Effort: ~3h | Run after Phases 1–2**

**C5 (quick):** 9 fields use `record_kinds_in: ["core", ...]` but `core` is not a valid `record_kind`. Replace `"core"` with `"entity"` in all 9 occurrences.

**C4 (systematic):** 40 fields have `record_kinds_in: []`. Assign correct scopes per semantics:
- Edge fields (`edge_type`, `edge_id`, `source_file_id`, `target_file_id`, `directionality`, `rel_type`, `confidence`) → `["edge"]`
- File entity fields (`file_id`, `sha256`, `size_bytes`, `is_directory`, etc.) → `["entity"]`
- Universal fields (`record_id`, `record_kind`, `created_utc`, `updated_utc`, `scan_id`) → `["entity","edge","generator","metadata"]`

### Changes
**`COLUMN_DICTIONARY.json`** — Update `record_kinds_in` for all 49 affected fields (40 empty + 9 `core`).

### Verification
```bash
# No empty scopes
python -c "import json; d=json.load(open('COLUMN_DICTIONARY.json')); empties=[h for h,v in d['headers'].items() if v.get('scope',{}).get('record_kinds_in')==[]]; print(len(empties))"  # expect 0

# No 'core' values
grep -c '"core"' COLUMN_DICTIONARY.json  # expect 0
```

---

## Phase 6 — Fix `data_transformation` Type and Add Serialization Specs (C6, C7)
**Risk: LOW | Effort: ~4h**

**C6:** `data_transformation` declared as `boolean|string|null` — incorrect. Derivation only ever produces a string or null.

**C7:** 35 array fields and 6 object fields have no flat-table serialization rule — causes inconsistent CSV output.

### Changes
**`COLUMN_DICTIONARY.json`**:
- Fix `data_transformation.value_schema.type`: remove `boolean`, change to `["string","null"]` with a string enum of observed values
- Add `"serialization": {"flat_table": {"strategy": "json_array_string"}}` to all 35 array-type fields
- Add `"serialization": {"flat_table": {"strategy": "json_object_string"}}` to all 6 object-type fields

### Verification
- `data_transformation` type field contains no `boolean`
- All array/object fields in COLUMN_DICTIONARY.json have a `serialization` key
- JSON validates cleanly after changes

---

## Phase 7 — Document Path Precedence and Fix `path_aliases` Derivation (C8)
**Risk: LOW | Effort: ~1.5h**

### Changes
**`DERIVATIONS.yaml`**:
- Add top-level `path_precedence:` documentation block (absolute_path → relative_path → canonical_path → directory_path → filename → path_aliases)
- Add missing derivation for `path_aliases`: `trigger: manual_patch_only, formula: COALESCE(INPUT.path_aliases, [])`

**`COLUMN_DICTIONARY.json`**:
- Set `record_kinds_in: ["entity"]` for all 6 path fields if not already set

### Verification
- `path_aliases` has a derivation entry
- `path_precedence:` section exists in DERIVATIONS.yaml

---

## Phase 8 — Structural Design Decisions: Duplicates, Description Contracts, Status Enum (C1, C2, C3)
**Risk: MEDIUM | Effort: ~4h**

### C1 — Resolve Duplicate Concepts
- **`edge_type` vs `rel_type`**: Deprecate `rel_type` (keep data, mark as superseded). Add `deprecated: true` + `superseded_by: edge_type` to `rel_type` in WRITE_POLICY.yaml and COLUMN_DICTIONARY.json.
- **`generated` vs `is_generated`**: Keep both, add `semantic_note` to COLUMN_DICTIONARY.json distinguishing them (path/pattern-based vs registry-reference-based).
- **`entity_kind` vs `is_directory`**: Document `is_directory` as INPUT primitive used to derive `entity_kind`. No deprecation — they serve different layers.

### C2 — Description Field Contracts
**`COLUMN_DICTIONARY.json`** — Add `constraints.max_length` and `constraints.purpose` to all 4 description fields:
- `one_line_purpose`: max 120 chars, completes "This file…"
- `short_description`: max 250 chars, one paragraph
- `description`: max 2000 chars, long-form
- `notes`: max 4000 chars, operator-only

**`governance_registry_schema.v3.json`** — Add `"maxLength"` to the string definitions of each.

### C3 — Scope `status` Enum
**`governance_registry_schema.v3.json`** — Change `FileRecord.status` from open `string` to:
```json
"enum": ["active", "archived", "deprecated", "legacy_read_only", null]
```
(Confirmed safe: live data uses only `"active"` and `"legacy_read_only"`.)

### Verification
- `rel_type` has `deprecated: true` in both spec files
- All 4 description fields have `maxLength` in JSON schema
- `FileRecord.status` enum rejects `"running"`, accepts `"active"`

---

## Phase 9 — Test Coverage Precedence Rule (C9)
**Risk: LOW | Effort: ~1.5h | Run after Phase 1**

### Changes
**`DERIVATIONS.yaml`** — Add `field_precedence_rules.test_coverage` section documenting: for `.py` files where `py_analysis_success=true`, Python-specific fields (`py_tests_executed`, `py_pytest_exit_code`, `py_coverage_percent`) are authoritative over general fields (`has_tests`, `coverage_status`). Include reconciliation formula.

**`COLUMN_DICTIONARY.json`** — Add `precedence_group` to all 6 involved fields: `test_coverage_general` (3 fields) and `test_coverage_python` (3 fields).

### Verification
- `field_precedence_rules.test_coverage` section exists in DERIVATIONS.yaml
- All 6 fields have `precedence_group` set in COLUMN_DICTIONARY.json

---

## Execution Order & Summary

| Phase | Issues | Files Changed | Risk | Effort |
|-------|--------|---------------|------|--------|
| 1 | 37 `py_*` fields unregistered | WRITE_POLICY, DERIVATIONS, schema.v3 | LOW-MED | ~3h |
| 2 | 8 undeclared fields in schema | schema.v3 | LOW | ~2h |
| 3 | 9 immutable fields without derivations | DERIVATIONS | LOW | ~1h |
| 4 | ~6 manual_or_automated reclassifications | WRITE_POLICY | LOW-MED | ~2h |
| 5 | 40 empty scopes + 9 invalid `core` enum | COLUMN_DICTIONARY | LOW | ~3h |
| 6 | `data_transformation` type + serialization specs | COLUMN_DICTIONARY | LOW | ~4h |
| 7 | Path precedence + `path_aliases` derivation | DERIVATIONS, COLUMN_DICTIONARY | LOW | ~1.5h |
| 8 | Duplicate columns, description contracts, status enum | WRITE_POLICY, COLUMN_DICTIONARY, schema.v3 | MEDIUM | ~4h |
| 9 | Test coverage contradiction rule | DERIVATIONS, COLUMN_DICTIONARY | LOW | ~1.5h |

**Total estimated effort: ~22 hours**
**Breaking changes: 0** (all changes are additive, deprecation-only, or tightening of open types confirmed safe against live data)

**Recommended order:** 1 → 2 → 3 → 7 → 9 → 4 → 5 → 6 → 8
(Highest-severity violations first, then consistency fixes, design decisions last)
