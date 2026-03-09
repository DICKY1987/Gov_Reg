# Registry Automation Rewrite - Before/After Comparison

**Generated:** 2026-03-08T19:00:36Z

---

## Transformation Overview

This document demonstrates how the original narrative plan was transformed into framework-native execution artifacts.

---

## Example 1: Pipeline Runner Issue

### Before (REG_AUTO_PLAN.txt):
```
Bug: pipeline_runner.py has a silent fail bug where it stages outputs 
even when transforms return invalid results.

Proposed fix: Add validation in pipeline_runner.py
```

### After (CONTRACT_GAP_MATRIX.md):
```
| REG-001 | pipeline_runner.py | Executor | output_result_envelope_contract | 
Silent staging of invalid transform results | Executor output envelope validation 
missing; runner must validate or normalize transform results before staging | 
Output validation with schema checking | category, outputs, evidence_contract, 
pass_criteria | result_validation.log, envelope_check.json | runner_fix | 
Verify pipeline_runner rejects incomplete envelopes and generates evidence | 
Critical |
```

**Key Changes:**
- ❌ "Bug" → ✅ Framework category: "Executor"
- ❌ "Silent fail" → ✅ Broken contract: "output_result_envelope_contract"
- ❌ Implied validation → ✅ Explicit evidence requirements
- ❌ Vague "add validation" → ✅ Deterministic verification test

---

## Example 2: Default Injector Issue

### Before (REG_AUTO_PLAN.txt):
```
Issue: default_injector.py doesn't actually inject defaults.
The code exists but does nothing.

Recommendation: Make it work or remove it.
```

### After (CONTRACT_GAP_MATRIX.md):
```
| REG-002 | default_injector.py | Phase | pass_fail_criteria_contract | 
Declared defaults not applied to outputs | Phase postcondition enforcement 
missing because declared default semantics are not actionable | Postcondition 
checks after phase execution | category, steps, pass_criteria, evidence_contract | 
before_defaults.json, after_defaults.json, injection_diff.json | code_fix | 
Verify all declared defaults applied with before/after evidence | High |
```

**Key Changes:**
- ❌ "doesn't work" → ✅ Framework category: "Phase"
- ❌ "does nothing" → ✅ Broken contract: "pass_fail_criteria_contract"
- ❌ "make it work or remove it" → ✅ Specific remediation: postcondition enforcement
- ❌ No verification → ✅ Evidence-based verification test

---

## Example 3: E2E Validator Issue

### Before (REG_AUTO_PLAN.txt):
```
Problem: e2e_validator.py only checks if files exist, not if they're correct.

Suggested improvement: Add real validation logic.
```

### After (CONTRACT_GAP_MATRIX.md):
```
| REG-003 | e2e_validator.py | Gate | pass_fail_criteria_contract | 
Validation passes despite structural defects | Gate pass/fail enforcement is 
shallow; validates file existence but not internal consistency or referential 
integrity | Policy-driven validation with consistency checks | category, 
pass_criteria, evidence_contract, inputs | validation_report.json, 
consistency_checks.log, failed_rules.json | policy_fix | Verify deep validation 
catches all structural defects with test fixtures | Critical |
```

**Key Changes:**
- ❌ "only checks if files exist" → ✅ Broken contract: "pass_fail_criteria_contract"
- ❌ Framework category implied → ✅ Explicit category: "Gate"
- ❌ "add real validation" → ✅ Specific requirement: "policy-driven validation with consistency checks"
- ❌ No success criteria → ✅ Deterministic test: "catches all structural defects with test fixtures"

---

## Example 4: File ID Promotion Issue

### Before (REG_AUTO_PLAN.txt):
```
Critical blocker: file_id mapping from sha256 isn't working.
We need the 20-digit file_id but it's not being resolved.

Impact: Can't promote entities to identity layer.
```

### After (CONTRACT_GAP_MATRIX.md):
```
| REG-005 | file_id_reconciler.py | Mutation | identity_contract | 
Promotion to identity layer blocked | Identity promotion contract incomplete; 
mutation/executor paths must fail closed until official 20-digit file_id 
resolution proven | Fail-closed write policy for identity fields | category, 
fingerprint_contract, locks_write_policy, evidence_contract | file_id_proof.json, 
sha256_to_file_id_map.json, promotion_audit.log | code_fix | Verify identity 
writes blocked until file_id proven with resolution evidence | Critical |
```

**Key Changes:**
- ❌ "not working" → ✅ Broken contract: "identity_contract"
- ❌ "critical blocker" → ✅ Framework category: "Mutation" + fail-closed policy
- ❌ Implied behavior → ✅ Explicit requirement: "mutation paths must fail closed"
- ❌ No proof mechanism → ✅ Evidence: file_id_proof.json, promotion_audit.log

---

## Structural Transformation

### Before: Report-Style Organization

```
REG_AUTO_PLAN.txt (narrative):
├── Work Stream 1: Core Pipeline
│   ├── Bug 1: pipeline_runner silent fail
│   ├── Bug 2: default_injector doesn't work
│   └── Bug 3: timestamp_clusterer wrong field
├── Work Stream 2: Identity Layer
│   ├── Bug 1: file_id mapping blocked
│   └── Bug 2: doc_id collisions
├── Work Stream 3: Validation
│   └── Bug 1: e2e_validator too shallow
└── Recommendations (prose)
```

### After: Template-Native Organization

```
REG_AUTO_PLAN_REWRITTEN_TEMPLATE_NATIVE.json:
├── template_metadata
├── critical_constraint (no implied behavior)
├── task_analysis
├── assumptions_scope
├── file_manifest
├── component_inventory (11 components categorized)
├── contract_taxonomy (8 standard contract types)
├── programspec_field_mapping_rules
├── contract_gap_matrix_artifact (19 rows × 12 fields)
├── verification_strategy
├── failure_mode_catalog
├── completion_criteria
├── phase_plan
│   ├── PH-01: Source Inventory
│   ├── PH-02: Matrix Authoring
│   ├── PH-03: ProgramSpec Mapping
│   ├── PH-04: Remediation Synthesis
│   ├── PH-05: Gate Generation
│   └── PH-06: Final Assembly
├── phase_contracts (6 phases with inputs/outputs/invariants)
├── step_contracts (12+ steps with preconditions/postconditions/file_scope/evidence)
├── validation_gates (6 gates with executable criteria)
├── ground_truth_levels (L0-L3)
└── final_summary
```

---

## Contract-Gap Matrix Structure

### Before: No Matrix

Issues were scattered across work streams with informal descriptions.

### After: Authoritative Matrix

19 rows × 12 columns:

| issue_id | current_component | framework_category | broken_contract | symptom | root_cause | required_runner_capability | required_spec_fields | evidence_required | remediation_type | verification_test | priority |
|----------|-------------------|-------------------|-----------------|---------|------------|---------------------------|---------------------|------------------|-----------------|------------------|----------|
| REG-001 | pipeline_runner.py | Executor | output_result_envelope_contract | ... | ... | Output validation | category, outputs, evidence_contract | result_validation.log | runner_fix | ... | Critical |
| REG-002 | default_injector.py | Phase | pass_fail_criteria_contract | ... | ... | Postcondition enforcement | steps, pass_criteria | before_defaults.json | code_fix | ... | High |
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |

---

## ProgramSpec Mapping

### Before: No Explicit Mapping

Field responsibilities were implied or unstated.

### After: Explicit Field Assignments

**Example for REG-001 (pipeline_runner):**
```json
{
  "issue_id": "REG-001",
  "programspec_targets": {
    "category": "Executor",
    "outputs": {
      "field": "result_envelope_validation",
      "required": true,
      "description": "Must validate transform results before staging"
    },
    "evidence_contract": {
      "field": "output_validation_evidence",
      "required_files": ["result_validation.log", "envelope_check.json"]
    },
    "pass_criteria": {
      "field": "envelope_completeness_check",
      "criteria": "All required envelope fields present and valid"
    }
  }
}
```

---

## Validation Gates

### Before: No Gates

Validation was described in prose without executable criteria.

### After: Machine-Checkable Gates

**Example: GATE-002-MATRIX-COMPLETE**
```json
{
  "gate_id": "GATE-002-MATRIX-COMPLETE",
  "phase": "PH-02",
  "purpose": "Verify contract-gap matrix complete with all required fields",
  "command": "python scripts/validate_matrix_completeness.py --matrix CONTRACT_GAP_MATRIX.md",
  "timeout_sec": 60,
  "expect_exit_code": 0,
  "expect_stdout_regex": "Matrix completeness: PASS.*19 rows validated",
  "forbid_stdout_regex": "FAIL|INCOMPLETE|MISSING_FIELD",
  "expect_files": ["CONTRACT_GAP_MATRIX.md", ".state/matrix/contract_gap_matrix.json"],
  "evidence": {
    "directory": ".state/evidence/PH-02/GATE-002",
    "required_files": ["gate_execution.log", "field_completeness_check.json"]
  },
  "pass_criteria": {
    "all_12_columns_present": true,
    "no_empty_verification_test": true,
    "no_empty_evidence_required": true
  }
}
```

---

## Evidence Requirements

### Before: No Evidence Specification

Success/failure was subjective or manual.

### After: Explicit Evidence Contracts

**Example for REG-001:**
```json
{
  "evidence_directory": ".state/evidence/executor/REG-001",
  "required_files": [
    "result_validation.log",
    "envelope_check.json",
    "precondition_checks.log",
    "postcondition_checks.log",
    "step_result.json"
  ],
  "ground_truth_level": "L2",
  "validation_gate": "GATE-001-EXECUTOR-OUTPUT-VALID"
}
```

---

## Dependency Ordering

### Before: Undefined Execution Order

Issues listed without dependencies or priority reasoning.

### After: Explicit Dependency Waves

**Remediation Waves:**
1. **Wave 1 (Priority 1):** Executor output enforcement (REG-001)
   - Rationale: Foundational; blocks all downstream work
2. **Wave 2 (Priority 2):** Identity promotion (REG-005)
   - Rationale: Prerequisites for mutation/promotion paths
3. **Wave 3 (Priority 3):** Phase postconditions (REG-002, REG-004, REG-007, REG-014)
   - Rationale: Pipeline reliability
4. **Waves 4-10:** Remaining issues in dependency order

---

## Metrics Comparison

| Metric | Before | After |
|--------|--------|-------|
| **Organization** | Narrative | Template-native |
| **Issue Expression** | Script-centric | Framework-native |
| **Contract Taxonomy** | Implicit | 8 standard types |
| **Field Assignments** | Unstated | ProgramSpec mapping |
| **Validation** | Prose | 6 executable gates |
| **Evidence** | None | Explicit requirements |
| **Dependencies** | Unclear | Encoded in 3 artifacts |
| **Execution Ready** | No | Yes |

---

## Key Principles Applied

1. **No Implied Behavior**
   - Before: "Add validation"
   - After: Explicit contract, runner responsibility, evidence, pass criteria

2. **Framework-Native Language**
   - Before: "Bug in script X"
   - After: "Executor output envelope validation missing"

3. **Deterministic Verification**
   - Before: Manual review
   - After: Machine-checkable gates with regex, file checks, evidence

4. **Evidence-Driven**
   - Before: No artifacts specified
   - After: Every issue has evidence requirements

5. **Dependency-Aware**
   - Before: Flat issue list
   - After: Prioritized waves with blocking relationships

---

**End of Comparison**
