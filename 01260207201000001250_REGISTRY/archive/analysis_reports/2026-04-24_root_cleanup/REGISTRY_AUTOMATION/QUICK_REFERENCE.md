# Registry Automation Remediation - Quick Reference

**Created:** 2026-03-09  
**Plan File:** `REGISTRY_AUTOMATION_REMEDIATION_PLAN_V3.json`  
**Audit Source:** `AUDIT_SUMMARY_AND_EXECUTION_PLAN.md`

---

## 📋 OVERVIEW

**Goal:** Fix 16 critical issues in Registry Automation System  
**Duration:** 24 days (29 with buffer)  
**Phases:** 6 sequential phases  
**Target:** 0 broken scripts, 50+ tests, 80%+ coverage

---

## 🎯 QUICK START (5 MINUTES)

```powershell
# 1. Navigate to repo
cd C:\Users\richg\Gov_Reg

# 2. Create backup
git checkout -b backup/pre-remediation-20260309

# 3. Create work branch
git checkout -b feature/registry-automation-remediation

# 4. Begin Phase 0
cd 01260207201000001250_REGISTRY
mkdir -p .state/gates .state/remediation .state/issues
```

---

## 📅 PHASE SCHEDULE

| Phase | Purpose | Days | Key Deliverable |
|-------|---------|------|----------------|
| **PH-00** | Bootstrap | 1 | .state/ infrastructure |
| **PH-01** | Foundation | 5 | Fixed docs, staging bug, 3 smoke tests |
| **PH-02** | Data Integrity | 5 | Defaults system, SHA256 promotion |
| **PH-03** | Validation | 5 | Enhanced E2E, entity resolution |
| **PH-04** | Completeness | 5 | Timestamp, cleanup, evidence schema |
| **PH-05** | Verification | 3 | 50+ tests, 80%+ coverage |

---

## ✅ SUCCESS CRITERIA

### Phase Gates
- [x] **PH-00:** .state/ files parse as valid JSON
- [ ] **PH-01:** 3 smoke tests pass, staging bug fixed
- [ ] **PH-02:** Defaults inject correctly, SHA256 resolves to file_id
- [ ] **PH-03:** Entity collisions auto-resolve with patches
- [ ] **PH-05:** 50+ tests pass, 80%+ coverage

### Definition of Done
- [ ] All 16 repair items addressed
- [ ] Test coverage ≥80%
- [ ] All critical blockers resolved
- [ ] Documentation matches reality
- [ ] Evidence trail complete
- [ ] Preflight checks enforced
- [ ] No data loss in pipeline
- [ ] Entity collisions auto-resolved

---

## 🔴 CRITICAL FIXES (PH-01)

### 1. Fix README.md (30 min)
```diff
- **Status:** Production-Ready ✅
+ **Status:** ⚠️ Development - Undergoing Remediation
```

### 2. Fix Pipeline Staging Bug (30 min)
**File:** `scripts/P_01999000042260305017_pipeline_runner.py`  
**Line:** 79
```python
# Before:
if file_id and transformed.get("data"):

# After:
if file_id and transformed:
```

### 3. Add Smoke Tests (1 day)
- `tests/unit/test_pipeline_runner_smoke.py`
- `tests/unit/test_enum_drift_gate_smoke.py`
- `tests/unit/test_phase_a_transformer_smoke.py`

---

## 📊 PROGRESS TRACKING

### Current State
- **Scripts:** 9 working, 5 incomplete, 5 broken
- **Tests:** 0
- **Coverage:** 0%
- **Critical Blockers:** 5

### Target State
- **Scripts:** 19 working, 0 broken
- **Tests:** 50+
- **Coverage:** 80%+
- **Critical Blockers:** 0

---

## 🛡️ KEY CONTRACTS

### File Scope Rules
- Each step declares allowed/forbidden paths
- Violations abort step execution
- Evidence recorded for all changes

### Validation Gates
- Phase cannot complete until gate passes
- Gates check: exit codes, file existence, regex patterns
- Evidence stored in `.state/evidence/{phase}/`

### Evidence Requirements
Every step produces:
- `precondition_checks.log`
- `postcondition_checks.log`
- `file_scope_validation.json`
- `step_result.json`
- File diffs for mutations

---

## 🚨 RISK MITIGATION

| Risk | Probability | Mitigation |
|------|------------|-----------|
| COLUMN_DICTIONARY missing | MEDIUM | Search backups → extract from registry → manual create |
| Test writing slow | HIGH | Prioritize critical tests, accept 75% if needed |
| SHA256 collisions | LOW | Fail-closed, manual resolution with audit |
| Unforeseen dependencies | MEDIUM | 20% time buffer, fix in order |

---

## 📞 DECISION LOG

### DEC-001: Worktree vs Feature Branches
**Decision:** Feature branches  
**Rationale:** Single dev, sequential execution, simpler workflow

### DEC-002: Wire Phase B/C or Downgrade?
**Decision:** Downgrade claims  
**Rationale:** Low risk, fast, can add later

### DEC-003: Test Coverage Target?
**Decision:** 80%  
**Rationale:** Enterprise standard, achievable in timeline

---

## 📁 KEY FILES

### Plan & Audit
- `REGISTRY_AUTOMATION_REMEDIATION_PLAN_V3.json` - Full plan (59KB)
- `AUDIT_SUMMARY_AND_EXECUTION_PLAN.md` - Detailed audit
- `REGISTRY_AUTOMATION_AUDIT_REPORT.md` - Concise findings

### Evidence Location
```
.state/
├── evidence/
│   ├── PH-00/
│   ├── PH-01/
│   ├── PH-02/
│   ├── PH-03/
│   ├── PH-04/
│   └── PH-05/
├── gates/
│   └── gates_spec.json
├── remediation/
│   └── remediation_plan.json
└── issues/
    └── normalized_issues.json
```

---

## 🔧 SELF-HEALING

### Enabled Failure Types
1. **DEP_INSTALL_FAIL** - Retry pip install (max 2)
2. **TEST_FAIL** - Run `pytest --last-failed` (max 2)
3. **PREFLIGHT_FAIL** - Create missing .state/ files (max 1)

### Escalation Triggers
- Max attempts exceeded
- Abort condition met (e.g., permission denied)
- Not converging after 2 attempts

### Evidence Per Attempt
- `.state/attempts/{phase}/{step}/attempt_{n}/stdout.log`
- `.state/attempts/{phase}/{step}/attempt_{n}/stderr.log`
- `.state/attempts/{phase}/{step}/attempt_{n}/result.json`

---

## 🎓 GROUND TRUTH LEVELS

| Level | Meaning | Example |
|-------|---------|---------|
| L0 | No verification | Documentation |
| L1 | Static checks | Lint, parse JSON |
| L2 | Unit tests | Isolated function tests |
| L3 | Integration tests | Multi-component workflows |
| L4 | End-to-end | Full pipeline simulation |

**Phase Requirements:**
- PH-00: L1
- PH-01, PH-02, PH-04: L2
- PH-03: L3
- PH-05: L4

---

## 📞 EXECUTION COMMANDS

### Run Phase Gate
```powershell
# Example: PH-01 gate
pytest 01260207201000001250_REGISTRY/REGISTRY_AUTOMATION/tests/unit/test_*_smoke.py -v
```

### Check Coverage
```powershell
pytest tests/ --cov=scripts --cov-report=json --cov-report=term
```

### Validate .state/ Files
```powershell
python -c "import json; json.load(open('.state/gates/gates_spec.json'))"
```

---

## 🎯 NEXT ACTIONS

1. ✅ **Review this document** (5 min)
2. ✅ **Review full plan** `REGISTRY_AUTOMATION_REMEDIATION_PLAN_V3.json` (30 min)
3. ✅ **Get approval** from project owner
4. ▶️ **Create backup branch** (2 min)
5. ▶️ **Begin PH-00-BOOTSTRAP** (1 day)

---

## 📝 NOTES

- **Template Used:** `NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3.json`
- **Classification:** Enterprise (32+ files, contracts required, 80%+ coverage)
- **Parallel Execution:** Disabled (single dev, complex dependencies)
- **Git Strategy:** Feature branch with backup tags
- **Approval Required:** Yes, at 4 checkpoints

---

**END QUICK REFERENCE**
