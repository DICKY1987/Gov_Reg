# Decision: Gate Registry Authority

**Decision ID:** DECISION-GATE-SSOT-001  
**Category:** Architecture / Single Source of Truth  
**Date:** 2026-03-05T09:20:22Z  
**Status:** APPROVED  
**Binding:** YES  

---

## Context

Multiple files define gate semantics (technical spec, template, MCP contracts, scripts), creating inconsistencies:
- GATE-003 means "Step Contracts" in technical spec and script, but "Unit Tests" in template
- GATE-004 means "Assumptions" in technical spec, but "Coverage" in template
- File mutation paths differ (with/without `{plan_id}`)

This causes execution failures as gate runners don't know which definition to follow.

---

## Decision

**`NEWPHASEPLANPROCESS_TECHNICAL_SPECIFICATION_V3.json` is the authoritative source for gate definitions.**

All other sources (template, MCP contracts, scripts) MUST align to it.

---

## Rationale

1. **Technical specification is explicitly marked as "AUTHORITATIVE"** in its metadata
2. **Scripts already self-identify with technical spec gate IDs** (P_262 says "GATE-003")
3. **Template is marked as a "template"** - meant to be filled in, not authoritative
4. **Single source of truth principle** requires one canonical registry

---

## Consequences

### Immediate Actions Required
- Template gate IDs must be remapped to match technical spec
- Template's current GATE-003/004 (tests/coverage) become GATE-005/006
- All path references standardized to technical spec convention
- Documentation updated to reference technical spec as authority

### Long-Term Impact
- Future gate additions go through technical spec first
- Template updates must validate against technical spec
- Automated alignment checker added to prevent drift

---

## Approval

**Approved by:** GitHub Copilot CLI (executing user directive)  
**Execution authority:** User directive "execute"  
**Date:** 2026-03-05T09:20:22Z  

---

## Evidence Chain

- This decision document: `.state/evidence/gate_alignment/phase1/DECISION-GATE-SSOT-001.md`
- Conflict analysis: Root directory `newPhasePlanProcess\` (user observation)
- Remediation plan: `GATE_ALIGNMENT_REMEDIATION_PLAN.md`

---

*Phase 1 Complete*
