# Gate ID Migration Guide - v3.0.0 to v3.1.0

**Migration Date:** 2026-03-05  
**Version Change:** Template v3.0.0 → v3.1.0 (gate alignment)  
**Breaking Changes:** YES (gate ID remapping)  
**Migration Required:** For all existing plans using old gate IDs  

---

## Summary of Changes

The gate ID mappings in the template have been corrected to align with the Technical Specification v3.0.0 (authoritative source). This fixes critical semantic conflicts where gate IDs meant different things in different files.

---

## Gate ID Remapping

### Old → New Mappings

| Old Gate ID | Old Meaning (Template v3.0.0) | → | New Gate ID | New Meaning (v3.1.0) | Script |
|------------|-------------------------------|---|------------|---------------------|---------|
| **GATE-003** | Unit tests pass | → | **GATE-005** | Unit tests pass | `pytest` |
| **GATE-004** | Coverage threshold | → | **GATE-006** | Coverage threshold | `pytest --cov` |
| - | *(not in template)* | → | **GATE-003** | Step Contracts Complete | `P_01260207233100000262_validate_step_contracts.py` |
| - | *(not in template)* | → | **GATE-004** | Assumptions Documented | `P_01260207233100000248_validate_assumptions.py` |

---

## Why This Changed

### Problem
**Template and Technical Spec had different gate ID semantics:**
- Template GATE-003 = "Unit tests" BUT Technical Spec GATE-003 = "Step Contracts"
- Template GATE-004 = "Coverage" BUT Technical Spec GATE-004 = "Assumptions"
- Scripts self-identified with Technical Spec IDs (e.g., `P_262` says "GATE-003")

### Root Cause
Template was created before formal gate registry; gate IDs were assigned ad-hoc.

### Solution
**Technical Specification v3.0.0 declared authoritative** for gate definitions (see decision document: `DECISION-GATE-SSOT-001.md`).

All other sources (template, MCP contracts, scripts) now align to it.

---

## Migration Instructions

### For New Plans
**✅ No action required.** Use the updated template v3.1.0.

### For Existing Plans Created with Template v3.0.0

**Option 1: Update Gate References (Recommended)**

If your plan references gate IDs directly, update them:

```json
// OLD (template v3.0.0)
{
  "validation_gates": [
    {"gate_id": "GATE-003", "purpose": "Unit tests pass"},
    {"gate_id": "GATE-004", "purpose": "Coverage threshold"}
  ]
}

// NEW (template v3.1.0)
{
  "validation_gates": [
    {"gate_id": "GATE-003", "purpose": "Step Contracts Complete"},
    {"gate_id": "GATE-004", "purpose": "Assumptions Documented"},
    {"gate_id": "GATE-005", "purpose": "Unit tests pass"},
    {"gate_id": "GATE-006", "purpose": "Coverage threshold"}
  ]
}
```

**Option 2: Leave As-Is (Legacy Mode)**

If your plan is complete and already validated, you may leave gate IDs as-is. However, any NEW validation runs will use the updated gate mappings and may produce different results.

---

## Impact on Execution

### Before Migration
Running GATE-003 on an old plan:
- ❌ **Expected:** Step contract validation
- ❌ **Actually ran:** Unit tests (pytest)
- **Result:** Wrong validation, misleading pass/fail

### After Migration
Running GATE-003 on a migrated plan:
- ✅ **Expected:** Step contract validation
- ✅ **Actually runs:** Step contract validation (`P_262`)
- **Result:** Correct validation

---

## File Mutation Path Change

### Old Path (template v3.0.0)
```
.state/planning/file_mutations.json
```

### New Path (template v3.1.0)
```
.state/planning/{plan_id}/file_mutations.json
```

**Reason:** Enables multiple concurrent plans without path collisions.

### Migration Action
Update any hardcoded paths in your plans:
```bash
# Find old paths
grep -r "\.state/planning/file_mutations\.json" your_plan.json

# Replace with
.state/planning/{plan_id}/file_mutations.json
```

---

## Breaking Changes Checklist

- [ ] Gate ID references updated (GATE-003/004 → GATE-005/006)
- [ ] New gates added to plan (GATE-003/004 for contracts/assumptions)
- [ ] File mutation paths updated to include `{plan_id}`
- [ ] Validation scripts reference correct gate IDs
- [ ] Evidence paths updated for new gate structure
- [ ] Documentation updated with new gate IDs

---

## Backward Compatibility

### What Still Works
- ✅ Old plan files can be **read** without errors
- ✅ Old evidence paths are still valid
- ✅ Scripts unchanged (they already used correct IDs)

### What Breaks
- ❌ Running old GATE-003 expects unit tests, gets step contracts
- ❌ Running old GATE-004 expects coverage, gets assumptions
- ❌ File mutation validator expects new path format

### Compatibility Mode (Not Implemented)
A future version could detect plan version and apply gate ID translation automatically. For now, manual migration required.

---

## Testing Your Migration

### Step 1: Validate Schema
```bash
python scripts/P_01260207233100000263_validate_structure.py --plan-file your_plan.json
```

### Step 2: Validate Gate Definitions
```bash
python scripts/P_01260207233100000253_validate_gates.py your_plan.json
```

### Step 3: Run Full Gate Suite
```bash
python scripts/run_gates.py --plan-file your_plan.json
```

### Expected Results
- ✅ GATE-001: Schema Validation PASSED
- ✅ GATE-002: Gate Definitions Valid PASSED
- ✅ GATE-003: Step Contracts Complete PASSED (NEW)
- ✅ GATE-004: Assumptions Documented PASSED (NEW)
- ✅ GATE-005: Unit Tests Pass PASSED (was GATE-003)
- ✅ GATE-006: Coverage Threshold PASSED (was GATE-004)

---

## Rollback Instructions

If migration causes issues:

### Revert Template
```bash
cd newPhasePlanProcess
git checkout <previous_commit> 01260207201000000510_NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3.json
```

### Revert Technical Spec
```bash
git checkout <previous_commit> 01260207201000000180_NEWPHASEPLANPROCESS_TECHNICAL_SPECIFICATION_V3.json
```

### Revert MCP Contracts
```bash
git checkout <previous_commit> 01260207201000000512_npp_mcp_tool_contracts.v1.json
```

### Remove New Files
```bash
rm 01260207201000001225_scripts/check_step_file_scope.py
rm 01260207201000001225_scripts/gate_dependencies.json
```

---

## Support

**Questions?** Refer to:
- `.state/evidence/gate_alignment/EXECUTION_SUMMARY.md` (detailed changes)
- `.state/evidence/gate_alignment/phase1/DECISION-GATE-SSOT-001.md` (authority decision)
- `NEWPHASEPLANPROCESS_TECHNICAL_SPECIFICATION_V3.json` (authoritative gate registry)

**Issues?** File a bug report with:
- Plan file that fails
- Expected gate behavior
- Actual gate behavior
- Gate execution logs

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 3.1.0 | 2026-03-05 | Gate ID alignment; file mutation path standardization |
| 3.0.0 | 2026-02-03 | Initial template with step contracts |

---

**Migration Status:** Required for all plans using gate IDs GATE-003/004  
**Estimated Migration Time:** 15-30 minutes per plan  
**Risk Level:** MEDIUM (breaking change, but deterministic)  

---

*End of Migration Guide*
