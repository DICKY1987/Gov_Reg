<!-- DOC_LINK: DOC-ID-DECISION-RECORD-001 -->
---
doc_id: DOC-ID-DECISION-RECORD-001
title: "Decision Record: Continue with Structured doc_id"
status: active
version: 1.0.0
created: 2025-12-25T21:14:20Z
decision_date: 2025-12-25
authority: constitutional
supersedes:
  - UNIVERSAL_ID_SYSTEM_ROLLOUT_PLAN.md
  - THREE_SYSTEM_UNIFICATION_PHASE_PLAN.md
---

# Decision Record: Continue with Structured doc_id Approach

## Decision

**APPROVED:** Continue with pure **structured doc_id** approach for all document identity.

**REJECTED:** ULID-based universal ID system proposal.

**Date:** 2025-12-25T21:14:20Z

---

## Context

Two competing ID strategies were proposed:

### Option A: Structured doc_id (Current)
- Format: `DOC-<SYSTEM>-<DOMAIN>-<KIND>-<SEQ>`
- Example: `DOC-CORE-SCHEDULER-001`
- Status: **357 IDs deployed**, mature tooling

### Option B: ULID-based (Proposed)
- Format: `<PREFIX>-<ULID>`
- Example: `DOC-01JH7Y5QZK9M2R3D6W1A8B7C4D`
- Status: Planning only, not implemented

---

## Analysis Summary

**Technical Analysis:** `SUB_DOC_ID/ULID_VS_STRUCTURED_ANALYSIS.md`

**Weighted Scores:**
- Structured doc_id: **7.7/10**
- ULID: 3.6/10
- Hybrid: 9.6/10

**Decision:** Pure structured (no runtime tracking needed currently)

---

## Key Reasons

### 1. Human/AI Readability ✅
**Structured:** `DOC-CORE-SCHEDULER-001` - Immediately understandable
**ULID:** `DOC-01JH7Y5QZK9M2R3D6W1A8B7C4D` - Opaque, requires lookup

**Winner:** Structured by a wide margin

### 2. Existing Investment ✅
- 357 doc_ids already assigned
- Mature tooling: scanner, assigner, validator
- 60+ hours of development complete
- Tests passing, documentation complete

**Migration Cost to ULID:** 80-120 hours + HIGH risk

### 3. Design Rationale ✅
- Comprehensive 3,400-line design conversation explicitly chose structured
- Design rationale documented in `ChatGPT-ID system review.md`
- ULID explicitly reserved for runtime entities

### 4. Governance Alignment ✅
- `ID_SYSTEM_GOVERNANCE_REQUIREMENTS.md` specifies structured format
- Constitutional document (Tier 1 authority)
- ULID plans were Tier 3 (planning documents)

**Authority Chain Resolution:** Constitutional requirements override plans

### 5. Semantic Routing ✅
AI agents can route based on ID structure:
```python
if doc_id.startswith("DOC-CORE-"):
    route_to_core_documentation()
```

**ULID requires metadata lookup for every operation.**

---

## Rejected Alternative: ULID Migration

**Reasons for Rejection:**

1. **High Cost:** 80-120 hours development + testing
2. **High Risk:** Data loss, broken references (357 IDs affected)
3. **Loss of Semantic Meaning:** Cannot understand ID without lookup
4. **Human Usability:** Impossible to remember or discuss ULIDs
5. **No Clear Benefit:** Time-ordering not critical for documents
6. **Contradicts Design:** Goes against documented rationale

---

## Actions Taken

### 1. Archived ULID Plans ✅

**Archived Documents:**
- `UNIVERSAL_ID_SYSTEM_ROLLOUT_PLAN.md`
- `UNIVERSAL_ID_SYSTEM_GAP_REMEDIATION.md`
- `UNIVERSAL_ID_SYSTEM_GAP_REMEDIATION_PART2.md`
- `THREE_SYSTEM_UNIFICATION_PHASE_PLAN.md`

**Location:** `ARCHIVE/ulid_exploration_20251225-151505/`

**Status:** Marked as "archived" in original locations with reference to this decision

### 2. Updated Governance ✅

**Confirmed:** `ID_SYSTEM_GOVERNANCE_REQUIREMENTS.md` is authoritative

**R-ID-003: ULID Usage Constraints:**
> "ULIDs SHALL be used **only** for:
> - Pipeline run identifiers (`run_id`)
> - Event identifiers (`event_id`) in JSONL ledgers
> - State snapshots where time-ordering is critical
>
> **Prohibition:** ULIDs MUST NOT be used as primary document identity."

### 3. Documented Analysis ✅

**Created:** `SUB_DOC_ID/ULID_VS_STRUCTURED_ANALYSIS.md`
- Comprehensive technical comparison
- Use case analysis
- Decision matrix with weighted scoring
- Migration path analysis
- Authority chain resolution

### 4. Updated Phase Plans ✅

**Next Steps:** Continue with Phase 7 of `ID_SYSTEM_CENTRAL_DOCS/COMPREHENSIVE_PHASE_PLAN.md`
- Governance integration
- DIR_MANIFEST.yaml updates
- README.md links
- CI enforcement (R-ID-072)

---

## Future Considerations

### If Runtime Tracking Becomes Critical

If you later determine that time-ordered execution tracking is essential:

**Option:** Implement **Hybrid Approach**
- Keep structured doc_id for documents
- Add ULID support for runtime entities only
- Estimated effort: 8-12 hours (additive)
- Reference: `ULID_VS_STRUCTURED_ANALYSIS.md` Section 8

**DO NOT migrate existing doc_ids to ULID.**

---

## Implementation Status

### Completed ✅
- [x] Technical analysis
- [x] Authority chain review
- [x] ULID plans archived
- [x] Original files marked as archived
- [x] Archive README created
- [x] Decision record created (this document)

### Next Steps
- [ ] Update SUB_DOC_ID/README.md with decision reference
- [ ] Update DOCUMENTATION_INDEX.md
- [ ] Continue with Phase 7 (governance integration)
- [ ] Implement ID_TAXONOMY.yaml (structured only)

---

## Authority and Approval

**Decision Authority:** Repository Owner + Technical Lead
**Aligned With:** ID_SYSTEM_GOVERNANCE_REQUIREMENTS.md (Constitutional)
**Approved By:** Technical analysis + governance review
**Date:** 2025-12-25T21:14:20Z

**Status:** ✅ APPROVED - IMPLEMENTED

---

## References

**Decision Support:**
- `SUB_DOC_ID/ULID_VS_STRUCTURED_ANALYSIS.md` - Technical analysis
- `SUB_DOC_ID/ID_SYSTEM_GOVERNANCE_REQUIREMENTS.md` - Constitutional requirements
- `ChatGPT-ID system review.md` - Design rationale (3,400 lines)

**Archived Plans:**
- `ARCHIVE/ulid_exploration_20251225-151505/` - ULID planning documents

**Current System:**
- `SUB_DOC_ID/` - Canonical implementation directory
- `DOC_ID_REGISTRY.yaml` - Active registry (357 IDs)
- `TECHNICAL_SPECIFICATION_V2.1.md` - System specification

---

**END OF DECISION RECORD**
