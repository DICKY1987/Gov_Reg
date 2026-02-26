# Registry Cleanup Implementation Master Index
**Date:** 2026-02-22 22:34:35
**Status:** Automated cleanup complete, manual schema editing required

---

## Quick Reference

| Phase | Guide File | Complexity | Est. Time | Priority | Dependencies |
|-------|-----------|------------|-----------|----------|--------------|
| B1 | B1_IMPLEMENTATION_GUIDE.txt | Medium | 30 min | HIGH | None |
| B2 | B2_IMPLEMENTATION_GUIDE.txt | High | 2 hours | HIGH | B1 complete |
| B3 | B3_IMPLEMENTATION_GUIDE.txt | Low | 20 min | Medium | None |
| B4 | B4_IMPLEMENTATION_GUIDE.txt | Low | 15 min | Medium | None |
| B5 | B5_IMPLEMENTATION_GUIDE.txt | High | 2 hours | Medium | None |
| B6 | B6_IMPLEMENTATION_GUIDE.txt | High | 2.5 hours | Medium | B5 (partial) |
| B7 | B7_IMPLEMENTATION_GUIDE.txt | Medium | 30 min | Medium | B9 (merge) |
| B8 | B8_IMPLEMENTATION_GUIDE.txt | HIGH RISK | 2 hours | LOW | Stakeholder review |
| B9 | B9_IMPLEMENTATION_GUIDE.txt | Low | 20 min | Medium | B7 (merge) |

**Total estimated time for manual work:** 9-10 hours

---

## Recommended Execution Order

### Phase 1: Critical Schema Fixes (HIGH PRIORITY)
Start with these to enable validation:

1. **B1** - Register 2 py_* fields (30 min)
   - py_capability_facts_hash
   - py_capability_tags
   - Files: WRITE_POLICY.yaml, DERIVATIONS.yaml, schema.v3.json

2. **B2** - Add 19 undeclared fields (2 hours)
   - Includes: absolute_path, entity_kind, status, etc.
   - File: schema.v3.json
   - Validate after: `python -m jsonschema --instance REGISTRY_file.json schema.v3.json`

**Git checkpoint:** `git add . && git commit -m "B1-B2: Register py_* and undeclared fields"`

### Phase 2: Consistency Fixes (MEDIUM PRIORITY)
Can be done in any order:

3. **B3** - Add 9 immutable field derivations (20 min)
   - File: DERIVATIONS.yaml

4. **B4** - Reclassify 6 policy fields (15 min)
   - File: WRITE_POLICY.yaml

5. **B7 + B9** - Path & test coverage precedence (30 min)
   - Files: DERIVATIONS.yaml, COLUMN_DICTIONARY.json
   - IMPORTANT: Merge B7 and B9 into single _metadata block

**Git checkpoint:** `git add . && git commit -m "B3-B4, B7-B9: Consistency and precedence fixes"`

### Phase 3: Scope & Type Corrections (MEDIUM PRIORITY)
Largest editing effort:

6. **B5** - Fix 49 scope issues (2 hours)
   - 9 'core' → 'entity'
   - 40 empty scopes → assigned
   - File: COLUMN_DICTIONARY.json

7. **B6** - Add serialization to 41 fields (2.5 hours)
   - Fix data_transformation type
   - Add array/object serialization
   - File: COLUMN_DICTIONARY.json
   - Validate: Check column dictionary schema if exists

**Git checkpoint:** `git add . && git commit -m "B5-B6: Scope and serialization fixes"`

### Phase 4: Design Decisions (REQUIRES REVIEW)

8. **B8** - Structural design decisions (2 hours + review)
   - ⚠️ CRITICAL: rel_type deprecation requires stakeholder decision
   - Recommendation: DEFER deprecation (see B8 guide)
   - Other changes: description contracts, semantic notes, status enum

**Git checkpoint:** `git add . && git commit -m "B8: Design decisions (rel_type deferred)"`

---

## Validation Checklist

After each phase:

- [ ] Files edited match guide instructions
- [ ] No syntax errors in YAML/JSON
- [ ] Schema validation passes:
  `powershell
  python -m jsonschema --instance 01999000042260124503_REGISTRY_file.json 01999000042260124012_governance_registry_schema.v3.json
  `
- [ ] Column dictionary validates (if schema exists):
  `powershell
  if (Test-Path "schemas/column_dictionary_schema.json") {
      python -m jsonschema --instance 01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json schemas/column_dictionary_schema.json
  }
  `
- [ ] Changes committed to git

---

## Files Reference

### Files to Edit

| File | Phases | Total Edits |
|------|--------|-------------|
| 01260207201000000193_UNIFIED_SSOT_REGISTRY_WRITE_POLICY.yaml | B1, B4, B8 | ~10 sections |
| 01260207201000000192_UNIFIED_SSOT_REGISTRY_DERIVATIONS.yaml | B1, B3, B7, B8 | ~50 entries |
| 01999000042260124012_governance_registry_schema.v3.json | B1, B2, B8 | ~25 properties |
| 01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json | B5, B6, B7, B8, B9 | ~100+ fields |

### Backup Location
Full pre-cleanup backup: `C:\Users\richg\Gov_Reg\01260207201000001133_backups\REGISTRY_pre_unified_cleanup_*`

---

## Critical Decisions Needed

1. **rel_type deprecation (B8)**
   - Currently used in 20+ locations
   - Options:
     A) Defer deprecation (recommended)
     B) Create migration plan first
     C) Run dual-field period (6 months)

2. **_metadata validator support (B7)**
   - Test if DERIVATIONS.yaml parser accepts _metadata key
   - Fallback: Use comment block instead

---

## Post-Completion Tasks

After all phases complete:

1. Update `00_REGISTRY_FOLDER_MANIFEST.md`
2. Document deprecated fields in migration guide
3. Archive implementation guides to `docs/completed_remediations/`
4. Run full validation suite
5. Update UNIFIED_REGISTRY_CLEANUP_AND_REMEDIATION_PLAN.md status

---

## Support

- Full plan: `UNIFIED_REGISTRY_CLEANUP_AND_REMEDIATION_PLAN.md`
- Execution summary: `CLEANUP_EXECUTION_SUMMARY.md`
- Implementation guides: `B[1-9]_IMPLEMENTATION_GUIDE.txt`

**Questions?** Review the original plan or guides for detailed rationale.
