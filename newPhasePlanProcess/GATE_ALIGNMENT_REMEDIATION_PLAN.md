# Gate Alignment Remediation Plan

**Plan ID:** PLAN-GATE-ALIGN-001  
**Created:** 2026-03-05T07:50:52Z  
**Status:** PROPOSED  
**Priority:** CRITICAL  
**Estimated Duration:** 4-6 hours  

---

## Executive Summary

**Problem:** Gate ID semantics, file mutation paths, and validator interfaces are inconsistent across technical spec, template, and implementation scripts, causing execution failures.

**Solution:** Normalize all gate definitions to match the technical spec (authoritative source), update template gate IDs, standardize mutation set paths, and create missing validators.

**Impact:** Enables deterministic, automated plan execution with consistent gate enforcement.

---

## Conflict Matrix

| Gate ID | Technical Spec | Template | Script | Status |
|---------|---------------|----------|--------|---------|
| GATE-003 | Step Contracts Complete | Unit tests pass | Step Contracts (self-ID) | ❌ CONFLICT |
| GATE-004 | Assumptions Documented | Coverage threshold | Assumptions | ❌ CONFLICT |
| GATE-FILE-MUTATIONS | (not in spec registry) | File mutations | validate_file_mutations.py | ⚠️ PATH MISMATCH |

---

## Phase Plan

### Phase 1: Authority Establishment (15 min)
**Objective:** Confirm technical spec as Single Source of Truth (SSOT)

**Steps:**
1. ✅ Declare `NEWPHASEPLANPROCESS_TECHNICAL_SPECIFICATION_V3.json` as authoritative gate registry
2. ✅ All other sources (template, MCP contracts, scripts) must align to it
3. ✅ Document decision in decision ledger

**Deliverables:**
- `DECISION-GATE-SSOT-001.md` with rationale

---

### Phase 2: Gate Registry Normalization (45 min)
**Objective:** Align template gate definitions to technical spec

#### Step 2.1: Remap Template Gates
**File:** `NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3.json`

**Changes:**

| Current Gate | New Gate | Purpose | Command |
|-------------|----------|---------|---------|
| GATE-003 (unit tests) | GATE-005 | Unit tests pass | `pytest -q --junit-xml=...` |
| GATE-004 (coverage) | GATE-006 | Coverage threshold | `pytest -q --cov=src...` |
| GATE-003 (NEW) | GATE-003 | Step Contracts Complete | `python scripts/P_01260207233100000262_validate_step_contracts.py --plan-file {plan}` |
| GATE-004 (NEW) | GATE-004 | Assumptions Documented | `python scripts/P_01260207233100000248_validate_assumptions.py --plan-file {plan}` |

**Action:**
```json
// Delete old GATE-003 and GATE-004 entries (lines 822-900)
// Insert corrected entries matching technical spec
```

**Evidence:**
- `evidence/phase2/template_gate_diff.patch`
- `evidence/phase2/gate_registry_after.json`

---

#### Step 2.2: Update Technical Spec Registry (if needed)
**File:** `NEWPHASEPLANPROCESS_TECHNICAL_SPECIFICATION_V3.json`

**Add missing gates to registry:**
- GATE-005: Unit Tests Pass
- GATE-006: Coverage Threshold

**Ensure completeness:**
```json
{
  "id": "GATE-005",
  "name": "Unit Tests Pass",
  "script": "pytest",
  "purpose": "Verify unit tests pass",
  "critical_rule": "All unit tests must pass before phase completion",
  "failure_impact": "Code quality cannot be verified"
},
{
  "id": "GATE-006",
  "name": "Coverage Threshold",
  "script": "pytest --cov",
  "purpose": "Verify test coverage meets minimum threshold",
  "checks": ["coverage >= 80%"]
}
```

---

### Phase 3: File Mutation Path Standardization (30 min)
**Objective:** Pick one canonical mutation set path and update all references

#### Step 3.1: Choose Path Convention

**Recommendation:** Use `{plan_id}` version for multi-plan safety

**Canonical Path:**
```
.state/planning/{plan_id}/file_mutations.json
```

**Rationale:**
- Enables multiple concurrent plans
- Prevents path collisions
- Aligns with evidence path patterns (`.state/evidence/{phase}/{step_id}/...`)

---

#### Step 3.2: Update All References

**Files to modify:**

1. **Technical Spec** (already correct)
   - ✅ No change needed
   - Location: `.state/planning/{plan_id}/file_mutations.json`

2. **Template GATE-FILE-MUTATIONS**
   - File: `NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3.json`
   - Line ~869
   - Change FROM:
     ```json
     "command": "python scripts/P_01260207233100000290_validate_file_mutations.py .state/planning/file_mutations.json"
     ```
   - Change TO:
     ```json
     "command": "python scripts/P_01260207233100000290_validate_file_mutations.py .state/planning/{plan_id}/file_mutations.json"
     ```

3. **MCP Tool Contracts**
   - File: `npp_mcp_tool_contracts.v1.json`
   - Tool: `planning.extract_file_mutation_set`
   - Update default `mutation_set_path` template

4. **Script Documentation**
   - File: `P_01260207233100000290_validate_file_mutations.py`
   - Update usage string and docstring to reflect canonical path

**Evidence:**
- `evidence/phase3/path_standardization.json` (all changed references)

---

### Phase 4: Validator Interface Standardization (60 min)
**Objective:** Ensure all validators use consistent interfaces

#### Step 4.1: Document Standard Validator Patterns

**Pattern 1: Plan-Wide Validation**
```bash
python scripts/validate_{name}.py --plan-file <path> --evidence-dir <path>
```

**Used by:** GATE-001, GATE-002, GATE-003, GATE-004, GATE-FILE-MUTATIONS

**Pattern 2: Phase-Scoped Validation** (future)
```bash
python scripts/validate_{name}.py --plan-file <path> --phase-id <id> --evidence-dir <path>
```

**Pattern 3: Step-Scoped Validation** (future)
```bash
python scripts/validate_{name}.py --plan-file <path> --phase-id <id> --step-id <id> --evidence-dir <path>
```

---

#### Step 4.2: Create Missing Validators

**Missing Validator:** `check_step_file_scope.py`

**Specification:**
- **Purpose:** Validate step's file mutations are within declared `file_scope`
- **Interface:** `--plan-file <path> --phase-id <phase> --step-id <step> --evidence-dir <path>`
- **Checks:**
  - All step mutations are in `allowed_paths`
  - No mutations in `forbidden_paths`
  - No write mutations to `read_only_paths`
  - Step scope is subset of phase scope

**Implementation:**
```python
#!/usr/bin/env python3
"""
Step File Scope Validator

Validates that a step's file mutations are within its declared file_scope.

Exit codes:
  0 = All mutations within scope
  1 = Scope violation detected
  2 = Plan structure error
"""

import json
import argparse
import sys
from pathlib import Path
from typing import Dict, Any, List

def validate_step_file_scope(plan: Dict[str, Any], phase_id: str, step_id: str) -> tuple[bool, List[str]]:
    """Validate step file scope against mutations."""
    defects = []
    
    # Extract phase and step
    phase = find_phase(plan, phase_id)
    if not phase:
        defects.append(f"Phase {phase_id} not found in plan")
        return False, defects
    
    step = find_step(phase, step_id)
    if not step:
        defects.append(f"Step {step_id} not found in phase {phase_id}")
        return False, defects
    
    # Get file scope
    file_scope = step.get("file_scope", {})
    allowed = file_scope.get("allowed_paths", [])
    forbidden = file_scope.get("forbidden_paths", [])
    read_only = file_scope.get("read_only_paths", [])
    
    # Get step outputs (files this step creates/modifies)
    outputs = step.get("outputs", [])
    
    # Validate each output against scope
    for output in outputs:
        path = output.get("path", "")
        output_type = output.get("type", "")
        
        if output_type in ["file", "dir"]:
            # Check allowed
            if not matches_any_pattern(path, allowed):
                defects.append(f"Output {path} not in allowed_paths")
            
            # Check forbidden
            if matches_any_pattern(path, forbidden):
                defects.append(f"Output {path} matches forbidden_paths")
            
            # Check read-only (for modifications)
            if output.get("mutation_type") == "modify" and matches_any_pattern(path, read_only):
                defects.append(f"Cannot modify read-only path {path}")
    
    return len(defects) == 0, defects

def matches_any_pattern(path: str, patterns: List[str]) -> bool:
    """Check if path matches any glob pattern in list."""
    from fnmatch import fnmatch
    return any(fnmatch(path, pattern) for pattern in patterns)

def find_phase(plan: Dict[str, Any], phase_id: str) -> Dict[str, Any] | None:
    """Find phase by ID."""
    phases = plan.get("plan", {}).get("phases", [])
    for phase in phases:
        if phase.get("phase_id") == phase_id:
            return phase
    return None

def find_step(phase: Dict[str, Any], step_id: str) -> Dict[str, Any] | None:
    """Find step by ID within phase."""
    steps = phase.get("steps", [])
    for step in steps:
        if step.get("step_id") == step_id:
            return step
    return None

def main():
    parser = argparse.ArgumentParser(description="Validate step file scope")
    parser.add_argument("--plan-file", required=True, help="Path to plan JSON")
    parser.add_argument("--phase-id", required=True, help="Phase ID (e.g., PH-03A)")
    parser.add_argument("--step-id", required=True, help="Step ID (e.g., STEP-001)")
    parser.add_argument("--evidence-dir", default=".state/evidence/file_scope", help="Evidence directory")
    
    args = parser.parse_args()
    
    # Load plan
    try:
        with open(args.plan_file, 'r') as f:
            plan = json.load(f)
    except Exception as e:
        print(f"Error loading plan: {e}", file=sys.stderr)
        sys.exit(2)
    
    # Validate
    passed, defects = validate_step_file_scope(plan, args.phase_id, args.step_id)
    
    # Write evidence
    evidence_dir = Path(args.evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    
    evidence = {
        "phase_id": args.phase_id,
        "step_id": args.step_id,
        "passed": passed,
        "defects": defects,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    evidence_file = evidence_dir / f"{args.phase_id}_{args.step_id}_file_scope.json"
    with open(evidence_file, 'w') as f:
        json.dump(evidence, f, indent=2)
    
    # Exit
    if passed:
        print(f"✓ File scope validation PASSED for {args.step_id}")
        sys.exit(0)
    else:
        print(f"✗ File scope validation FAILED for {args.step_id}:")
        for defect in defects:
            print(f"  - {defect}")
        sys.exit(1)

if __name__ == "__main__":
    from datetime import datetime
    main()
```

**Deliverables:**
- `scripts/check_step_file_scope.py` (new file)
- Unit tests for validator
- Evidence path registration in template

---

### Phase 5: MCP Tool Contract Alignment (30 min)
**Objective:** Update MCP contracts to match normalized gate IDs and paths

#### Step 5.1: Update Tool Contracts

**File:** `npp_mcp_tool_contracts.v1.json`

**Changes:**

1. **Add explicit gate ID mapping** in tool metadata:
```json
{
  "tools": [
    {
      "tool": "plan.validate_structure",
      "gate_id": "GATE-001",
      "gate_name": "Schema Validation"
    },
    {
      "tool": "plan.validate_step_contracts",
      "gate_id": "GATE-003",
      "gate_name": "Step Contracts Complete"
    }
  ]
}
```

2. **Update mutation extractor default path**:
```json
{
  "tool": "planning.extract_file_mutation_set",
  "default_evidence_path_template": ".state/evidence/mcp/{run_id}/planning_extract_file_mutation_set.json",
  "input_schema": {
    "properties": {
      "mutation_set_path": {
        "type": "string",
        "minLength": 1,
        "description": "Where to write PFMS JSON artifact (under repo_root).",
        "default": ".state/planning/{plan_id}/file_mutations.json"
      }
    }
  }
}
```

---

### Phase 6: Gate Dependency Graph Update (20 min)
**Objective:** Update gate execution order to reflect new gate IDs

#### Step 6.1: Update Gate Dependencies

**File:** `scripts/gate_dependencies.json`

**Ensure correct ordering:**
```json
{
  "gates": [
    {
      "id": "GATE-000",
      "depends_on": []
    },
    {
      "id": "GATE-001",
      "depends_on": ["GATE-000"]
    },
    {
      "id": "GATE-002",
      "depends_on": ["GATE-001"]
    },
    {
      "id": "GATE-003",
      "name": "Step Contracts Complete",
      "script": "P_01260207233100000262_validate_step_contracts.py",
      "depends_on": ["GATE-001", "GATE-002"]
    },
    {
      "id": "GATE-004",
      "name": "Assumptions Documented",
      "script": "P_01260207233100000248_validate_assumptions.py",
      "depends_on": ["GATE-001"]
    },
    {
      "id": "GATE-005",
      "name": "Unit Tests Pass",
      "script": "pytest",
      "depends_on": ["GATE-003"]
    },
    {
      "id": "GATE-006",
      "name": "Coverage Threshold",
      "script": "pytest --cov",
      "depends_on": ["GATE-005"]
    },
    {
      "id": "GATE-FILE-MUTATIONS",
      "name": "File Mutations Valid",
      "script": "P_01260207233100000290_validate_file_mutations.py",
      "depends_on": ["GATE-003"]
    }
  ]
}
```

---

### Phase 7: Documentation Updates (30 min)
**Objective:** Update all documentation to reflect normalized gate definitions

#### Files to Update:

1. **AI_AGENT_INSTRUCTIONS.md**
   - Update gate ID references
   - Update file mutation path examples
   - Add validator interface patterns

2. **README_PLANNING_LOOP.md**
   - Update gate execution examples
   - Update path conventions

3. **QUICK_COMMAND_REFERENCE.md**
   - Update gate command examples

4. **CRITICAL_ISSUES_FIXED.md**
   - Add entry for this remediation

---

### Phase 8: Validation and Testing (60 min)
**Objective:** Verify all changes work end-to-end

#### Step 8.1: Unit Tests

**Test Coverage:**
- ✅ Each validator runs with correct interface
- ✅ Gate IDs map correctly to scripts
- ✅ File mutation paths resolve correctly
- ✅ MCP tools call correct validators
- ✅ Evidence paths are created correctly

#### Step 8.2: Integration Test

**Test Scenario:** Run full gate suite against a sample plan

```bash
# 1. Generate a test plan
python scripts/generate_test_plan.py --output test_plan.json

# 2. Run all gates in sequence
python scripts/run_gates.py --plan-file test_plan.json

# Expected output:
# ✓ GATE-000 PASSED
# ✓ GATE-001 PASSED
# ✓ GATE-002 PASSED
# ✓ GATE-003 PASSED (Step Contracts)
# ✓ GATE-004 PASSED (Assumptions)
# ✓ GATE-005 PASSED (Unit Tests)
# ✓ GATE-006 PASSED (Coverage)
# ✓ GATE-FILE-MUTATIONS PASSED
```

#### Step 8.3: Evidence Validation

**Verify evidence structure:**
```bash
# Check evidence paths exist and contain required files
python scripts/validate_evidence_completeness.py .state/evidence/
```

---

## File Modification Checklist

| File | Change Type | Lines | Status |
|------|------------|-------|--------|
| `NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3.json` | MODIFY (gate remapping) | 769-900 | ⏳ Pending |
| `NEWPHASEPLANPROCESS_TECHNICAL_SPECIFICATION_V3.json` | ADD (GATE-005, GATE-006) | Registry section | ⏳ Pending |
| `npp_mcp_tool_contracts.v1.json` | MODIFY (path defaults) | Multiple tools | ⏳ Pending |
| `scripts/gate_dependencies.json` | MODIFY (gate order) | Full file | ⏳ Pending |
| `scripts/check_step_file_scope.py` | CREATE | N/A (new) | ⏳ Pending |
| `AI_AGENT_INSTRUCTIONS.md` | MODIFY (gate references) | Multiple sections | ⏳ Pending |
| `README_PLANNING_LOOP.md` | MODIFY (examples) | Command examples | ⏳ Pending |

---

## Success Criteria

### Mandatory (Must Pass)
- [ ] All gate IDs in template match technical spec registry
- [ ] All validators use standardized interfaces (`--plan-file`, `--evidence-dir`)
- [ ] File mutation set path is consistent across all sources
- [ ] Missing `check_step_file_scope.py` validator exists and works
- [ ] MCP tool contracts reference correct gate IDs and paths
- [ ] Full gate suite runs successfully on test plan
- [ ] All evidence files are generated in expected locations

### Recommended (Should Pass)
- [ ] Gate dependency graph is topologically sorted
- [ ] All documentation references updated gate IDs
- [ ] Unit tests exist for all new/modified validators
- [ ] Evidence validation passes for all gates

### Optional (Nice to Have)
- [ ] Visual gate execution diagram generated
- [ ] Gate execution timing metrics collected
- [ ] Automated gate alignment checker created

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Breaking existing plans | HIGH | CRITICAL | Version gate IDs (support v2.4 and v3.0 simultaneously) |
| Script interface changes break MCP tools | MEDIUM | HIGH | Update MCP tools in same commit |
| Evidence path changes break CI | MEDIUM | MEDIUM | Update CI config in same PR |
| Missing edge cases in new validator | MEDIUM | MEDIUM | Comprehensive unit tests + manual review |
| Documentation drift | HIGH | LOW | Single-commit update of all docs |

---

## Rollback Plan

**If remediation fails:**

1. **Revert all file changes** via git:
   ```bash
   git checkout HEAD -- newPhasePlanProcess/
   git checkout HEAD -- scripts/P_01260207233100000290_validate_file_mutations.py
   ```

2. **Restore gate dependency graph** from backup:
   ```bash
   cp scripts/gate_dependencies.json.backup scripts/gate_dependencies.json
   ```

3. **Remove new validator** (if created):
   ```bash
   rm scripts/check_step_file_scope.py
   ```

4. **Document rollback** in decision ledger

---

## Evidence Requirements

**Per-phase evidence artifacts:**

- Phase 1: `DECISION-GATE-SSOT-001.md`
- Phase 2: `evidence/phase2/template_gate_diff.patch`
- Phase 3: `evidence/phase3/path_standardization.json`
- Phase 4: `evidence/phase4/validator_interface_tests.xml`
- Phase 5: `evidence/phase5/mcp_tool_contract_diff.patch`
- Phase 6: `evidence/phase6/gate_dependency_graph_validation.json`
- Phase 7: `evidence/phase7/documentation_diff.patch`
- Phase 8: `evidence/phase8/integration_test_results.json`

**Final bundle:**
- `evidence/GATE_ALIGNMENT_REMEDIATION_COMPLETE.json` with:
  - All file hashes (before/after)
  - Validation results
  - Test coverage report
  - Checklist completion status

---

## Execution Commands

### Quick Start (Run All Phases)
```bash
# From repo root
cd newPhasePlanProcess

# Run remediation script (when implemented)
python scripts/execute_gate_alignment_remediation.py \
  --plan-file GATE_ALIGNMENT_REMEDIATION_PLAN.md \
  --evidence-dir .state/evidence/gate_alignment \
  --interactive
```

### Phase-by-Phase Execution
```bash
# Phase 2: Update template
python scripts/remediation/phase2_normalize_template_gates.py

# Phase 3: Standardize paths
python scripts/remediation/phase3_standardize_mutation_paths.py

# Phase 4: Create missing validators
python scripts/remediation/phase4_create_validators.py

# Phase 5: Update MCP contracts
python scripts/remediation/phase5_update_mcp_contracts.py

# Phase 6: Update gate dependencies
python scripts/remediation/phase6_update_gate_dependencies.py

# Phase 8: Run validation
python scripts/run_gates.py --plan-file test_plan.json
```

---

## Approval and Sign-Off

**Plan Author:** GitHub Copilot CLI  
**Plan Reviewer:** (Human review required)  
**Approved By:** (Awaiting approval)  
**Execution Start:** (Not yet scheduled)  

**Notes:**
- This plan is deterministic and mechanically verifiable
- All changes are reversible via git
- Evidence trail enables audit of all modifications
- Plan follows NO IMPLIED BEHAVIOR principle

---

## Next Steps

1. **Human review** of this plan
2. **Approval decision** (approve, request changes, or reject)
3. **Phase execution** (manual or automated)
4. **Evidence collection** after each phase
5. **Final validation** and sign-off

**Estimated total time:** 4-6 hours (can be parallelized for some phases)

**Recommended approach:** Execute phases sequentially with validation after each phase to catch issues early.

---

*End of Remediation Plan*
