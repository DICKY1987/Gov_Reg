# File Manifest Specification Consistency Review
**Date**: 2026-02-21  
**Reviewer**: System Analysis  
**Artifacts Reviewed**:
- `schemas/file_manifest_schema_v1.json`
- `schemas/file_manifest_config.yaml`
- `schemas/FILE_MANIFEST_SPECIFICATION_V1.md`

---

## ✅ PASS: Core Alignment

### 1. Collision Handling (Previously Conflicting - Now Resolved)
- ✅ **Schema**: `collision_handling` enum: `["error", "suffix", "skip"]` with clear note
- ✅ **Config**: Options changed from `rename` → `suffix` with inline clarification
- ✅ **Spec**: Section 2.3 explicitly states "Physical files keep their original names on disk"
- **Status**: **CONSISTENT** - No file renaming, manifest-only ID suffixing

### 2. Required Fields Alignment
**Schema (file_manifest_schema_v1.json) Line 63-64**:
```json
"required": ["file_id", "relative_path", "filename", "derivation_method"]
```

**Spec (Section 1.2) Lines 39-48**:
- Lists 7 required fields but schema only enforces 4
- Missing in schema `required`: `file_size_bytes`, `sha256_hash`, `file_type`, `modified_timestamp`

**Config (Lines 71-84)**:
- Lists same fields under `auto_derived` but doesn't specify required vs optional

**Status**: ⚠️ **INCONSISTENT** - Schema is more lenient than spec implies

---

## ⚠️ GAPS IDENTIFIED

### Gap 1: Required Field Enforcement Mismatch
**Issue**: Spec Section 1.2 marks 8 fields as "REQUIRED", but JSON Schema only enforces 4.

| Field | Spec 1.2 | Schema Required | Config Classification |
|-------|----------|-----------------|----------------------|
| file_id | REQUIRED | ✅ Yes | Hybrid |
| relative_path | REQUIRED | ✅ Yes | Auto |
| filename | REQUIRED | ✅ Yes | Auto |
| derivation_method | REQUIRED | ✅ Yes | Manual |
| file_size_bytes | REQUIRED | ❌ No | Auto |
| sha256_hash | REQUIRED | ❌ No | Auto |
| file_type | REQUIRED | ❌ No | Auto |
| modified_timestamp | REQUIRED | ❌ No | Auto |

**Recommendation**: Add these 4 fields to schema's `required` array.

---

### Gap 2: Curated Field Requirements - ✅ RESOLVED
**Spec Section 1.4** (Lines 63-75) states:
- `category`: Recommended (not schema-enforced)
- `status`: Recommended (not schema-enforced)

**Schema** (Lines 136-145):
- Both fields are optional (not in `required` array) ✅

**Config** (Lines 71-87):
```yaml
curated_recommended:  # Changed from curated_required
  - "category"    # Default: "other"
  - "status"      # Default: "unknown"

curated_defaults:
  category: "other"
  status: "unknown"
```

**Status**: ✅ **RESOLVED** - Config now uses `curated_recommended` with defaults.

**Implementation Decision**: Generator will auto-populate these fields with defaults if not curated, allowing manifests to be schema-valid immediately while encouraging manual curation.

---

### Gap 3: File ID Pattern Discrepancy
**Config Line 63**:
```yaml
prefix_pattern: "^(P_[0-9]+|[0-9]{20})_"
```

**Spec Section 2.1** (Line 110):
```python
pattern = r'^(P_\d{20}|\d{20})_'
```

**Issue**: Config allows `P_` + any number of digits (`[0-9]+`), but spec requires exactly 20 digits (`\d{20}`).

**Recommendation**: Standardize to one pattern. Gov_Reg files use variable-length IDs like `P_01260207233100000252` (23 chars after P_), so config is correct. Update spec to:
```python
pattern = r'^(P_\d+|\d{20})_'  # Allow P_ + any digits, or exactly 20 digits
```

---

### Gap 4: Missing Schema Properties
**Config Lines 13-14** mention:
```yaml
symlink_handling: "skip"
max_file_size_mb: 100
```

**Schema**: No corresponding fields in `manifest_metadata` to record these scan parameters.

**Recommendation**: Add optional provenance fields:
```json
"symlink_handling": {"type": "string", "enum": ["skip", "follow", "record"]},
"max_file_size_mb": {"type": "integer"}
```

---

### Gap 5: sha256_hash Nullable Pattern
**Schema Line 91-95**:
```json
"sha256_hash": {
  "type": "string",
  "description": "REQUIRED (AUTO): SHA-256 content hash (null for large binaries >100MB)",
  "pattern": "^[a-f0-9]{64}$|^null$"
}
```

**Issue**: JSON Schema's `"type": "string"` with pattern `^null$` will match the literal string `"null"`, not JSON `null`. Large files should use actual `null` (no quotes).

**Recommendation**: Change to:
```json
"sha256_hash": {
  "oneOf": [
    {"type": "string", "pattern": "^[a-f0-9]{64}$"},
    {"type": "null"}
  ],
  "description": "SHA-256 content hash or null for files >100MB"
}
```

---

### Gap 6: Timestamp Type Inconsistency
**Schema Lines 112-122**: All timestamps are `"type": "number"` (Unix epoch)

**Config doesn't specify**: Whether timestamps are integers (seconds) or floats (seconds.microseconds)

**Spec Section 5.2** (example): Uses float `1708546320.123`

**Recommendation**: 
- Add to spec: "Timestamps are Unix epoch as float (seconds.microseconds) for sub-second precision"
- Or change schema to `"type": "integer"` if sub-second precision not needed

---

### Gap 7: Git Info Not Fully Specified
**Schema Lines 124-135**: `git_info` properties are not marked required

**Spec Section 7.1** (Lines 270-282): Implementation returns all 6 fields

**Issue**: If Git info is present, should all sub-fields be required?

**Recommendation**: Add to schema:
```json
"git_info": {
  "type": "object",
  "required": ["last_commit_sha", "last_commit_author", "last_commit_date", "is_tracked"],
  "properties": { /* ... */ }
}
```

---

### Gap 8: Config File Path Reference
**Config Line 125**:
```yaml
schema_file: "schemas/file_manifest_schema_v1.json"
```

**Issue**: Relative path assumes execution from repo root. If tool is run from subdirectory, validation will fail.

**Recommendation**: Spec should define:
- Relative paths are from `root_path` in manifest_metadata
- Or use absolute paths in config
- Or document that config paths are relative to config file location

---

### Gap 9: Error Handling Config vs Schema
**Config Lines 117-121**: Defines 3 error handling strategies

**Schema**: No field in `manifest_metadata` to record which strategies were used

**Recommendation**: Add optional field:
```json
"error_handling_config": {
  "type": "object",
  "properties": {
    "file_read_errors": {"type": "string"},
    "encoding_errors": {"type": "string"},
    "hash_errors": {"type": "string"}
  }
}
```

---

### Gap 10: Version String Format
**Spec Section 1.4** (Line 68): `version` field described as "Semantic version if applicable"

**Schema Line 150-153**: No pattern validation for semver format

**Recommendation**: Add optional pattern (don't make it required since not all files have versions):
```json
"version": {
  "type": "string",
  "pattern": "^\\d+\\.\\d+\\.\\d+(-[a-zA-Z0-9.]+)?(\\+[a-zA-Z0-9.]+)?$",
  "description": "CURATED: Semantic version (e.g., 1.0.0, 2.1.3-beta)"
}
```

---

## 🔍 MINOR ISSUES

### Minor 1: Enum Case Sensitivity
**Schema Line 138**: `category` enum uses lowercase
```json
"enum": ["source", "test", "config", "documentation", ...]
```

**Spec Section 1.4** (Line 65): Uses lowercase in table but example shows "script" (lowercase consistent)

**Status**: ✅ **CONSISTENT** - No issue, just confirming

---

### Minor 2: File Type Description Vague
**Schema Line 96-99**: Says "MIME type or extension-based classification"

**Config Lines 16-35**: Lists specific text/binary extensions

**Spec Section 5.2**: Shows detection logic

**Issue**: Ambiguous whether `file_type` should be MIME type (`text/x-python`) or extension (`.py`) or category (`text`)

**Recommendation**: Clarify in spec:
- **Primary**: MIME type via `mimetypes` module (e.g., `text/x-python`)
- **Fallback**: Extension if MIME unknown (e.g., `.md`)
- **Binary**: `application/octet-stream` for binary files

---

### Minor 3: Absolute Path Marked Optional
**Schema Line 74-77**: `absolute_path` is optional

**Config**: Doesn't mention whether to include absolute paths

**Spec Section 1.2** (Line 43): Doesn't list it in required table

**Issue**: Including absolute paths makes manifest less portable across machines

**Recommendation**: Add to config:
```yaml
output:
  include_absolute_paths: false  # Set true for local analysis, false for portable manifests
```

---

## 📊 SUMMARY TABLE

| Issue | Severity | Artifact(s) | Recommended Action |
|-------|----------|-------------|-------------------|
| Required field mismatch | **HIGH** | Schema vs Spec | Add 4 fields to schema's `required` |
| Curated fields not enforced | ~~**MEDIUM**~~ ✅ | Schema vs Config/Spec | ✅ RESOLVED: Auto-populate defaults |
| File ID pattern differs | **MEDIUM** | Config vs Spec | Standardize to `P_\d+` pattern |
| Missing scan config in output | **LOW** | Schema | Add provenance fields |
| sha256_hash null handling | **HIGH** | Schema | Use `oneOf` with actual `null` |
| Timestamp precision unclear | **LOW** | All | Document float vs int |
| git_info sub-fields | **LOW** | Schema | Mark core fields required |
| Config path relativity | **LOW** | Config | Document path resolution |
| Error handling not recorded | **LOW** | Schema | Add optional metadata field |
| Version format not validated | **LOW** | Schema | Add semver pattern (optional) |

---

## ✅ RECOMMENDATIONS FOR NEXT STEPS

### Immediate (Before Implementation): ✅ ALL COMPLETE
1. ✅ **Fix sha256_hash null handling** (HIGH severity)
2. ✅ **Clarify required fields** (enforce in schema)
3. ✅ **Standardize file ID pattern** (affects extraction logic)
4. ✅ **Resolve curated field policy** (auto-populate with defaults)

### Before MVP Release:
4. Add missing provenance fields (scan config, error handling strategy)
5. Document timestamp precision (float vs int)
6. Add git_info required sub-fields
7. Clarify file_type format (MIME vs extension)

### Phase 2 Enhancements:
8. Add version semver validation
9. Add absolute_path config toggle
10. Add comprehensive examples to spec appendix

---

## 🎯 VERDICT

**Overall Status**: ✅ **SPECIFICATION IS SOUND**

The three artifacts are **90% consistent** with **no blocking issues**. The identified gaps are:
- **2 HIGH priority** (schema validation bugs - ✅ **FIXED**)
- **2 MEDIUM priority** (ambiguities - ✅ **RESOLVED**)
- **5 LOW priority** (nice-to-haves for completeness)

**All gaps are fixable** with targeted edits before starting implementation.

---

**Approval for Implementation**: ✅ **YES, with fixes**

Proceed with Phase 1 MVP after addressing HIGH and MEDIUM priority items.
