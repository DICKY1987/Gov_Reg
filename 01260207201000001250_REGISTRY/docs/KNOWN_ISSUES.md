# Registry Known Issues

**Created:** 2026-03-04
**Source:** Extracted from ChatGPT/audit analysis sessions before archival

---

## Redundant / Overlapping Fields

| Issue | Fields | Recommended Action |
|-------|--------|--------------------|
| Duplicate relationship type | `edge_type` vs `rel_type` | Standardize on `edge_type`; deprecate `rel_type` (20+ code refs — requires code review) |
| Duplicate generated flag | `generated` vs `is_generated` | Pick one; remove the other |
| Redundant directory flag | `is_directory` redundant with `entity_kind=directory` | Remove `is_directory` |
| Four description fields | `description`, `short_description`, `one_line_purpose`, `notes` | Define strict contracts for each or consolidate |
| Test/coverage overlap | General (`has_tests`, `coverage_status`) vs Python-specific (`py_pytest_exit_code`, `py_coverage_percent`) | Risk of contradictory states; need precedence rules |

## Scope & Enum Problems

| Issue | Detail |
|-------|--------|
| 40 headers have empty `record_kinds_in` scope | Many are obviously edge-only or entity-only — assign explicit scopes |
| `"core"` used in scopes but isn't a valid record_kind | Valid enum is `entity\|edge\|generator` only |
| `status` enum mixes lifecycle + runtime states | `active`, `archived`, `pending`, `running`, `failed` — should split into separate fields |

## ID Format Fragmentation

| Format | Where Used | Status |
|--------|-----------|--------|
| 20-digit numeric `^\d{20}$` | Canonical: schema, gates, contracts, allocator | **CANONICAL** |
| `DIR-{slug}-{hash}` derived string | Legacy generator output | **DEPRECATED** — update generators |
| `P_\d{20}` (22 chars) | `doc_id` for Python files | Valid composite, not separate type |
| `content_sha256` (64-char hex) | Pipeline `file_id` output | **BLOCKER** — pipeline produces wrong format for registry |

## Integration Gaps

| Issue | Detail | Status |
|-------|--------|--------|
| Pipeline file_id mismatch | Pipeline sets `file_id = content_sha256` (64-char hex); registry requires 20-digit allocated ID | **OPEN BLOCKER** for py_* column promotion |
| py_* column coverage | Only 4/37 py_* columns have direct pipeline support; 23 require new analyzers | Known gap |
| DOC_ID registry schema drift | Validator expects `docs` key; sync script uses `documents` | Unresolved |
| Hard-coded paths in scripts | `P_RENAME_REMOVE_DOC_TOKEN.py` has Windows absolute paths | Contradicts path-indirection spec |

## Path Field Overlap

`absolute_path`, `relative_path`, `canonical_path`, `directory_path`, `filename`, `path_aliases` — need clear precedence rules documented.

---

*Extracted from: ChatGPT-Registry Explanation.md, ChatGPT-ID System Sources.md, Repository Source File Description and Dependency Audi.md*
