# Planning Loop - Quick Reference Card

**Version 2.0 | Beta Release | 2026-02-18**

---

## 🚀 Quick Start (5 minutes)

```bash
# 1. Install (30 seconds)
pip install jsonschema jsonpatch click pyyaml rich

# 2. Validate (30 seconds)
python scripts/validate_dependencies.py
python scripts/validate_all_schemas.py

# 3. Run Example (1 minute)
python examples/example_end_to_end.py

# 4. Test (2 minutes)
pytest tests/ -v

# ✅ You're ready!
```

---

## 📋 Essential Commands

### Initialize Run
```bash
python src/plan_refine_cli/main.py init \
  --policy config/baseline_planning_policy.json
```

### Generate Plan
```bash
python src/plan_refine_cli/main.py skeleton \
  --run-id {RUN_ID} \
  --context {CONTEXT_PATH} \
  --output plan.json
```

### Refine Plan
```bash
python src/plan_refine_cli/main.py loop \
  --run-id {RUN_ID} \
  --context {CONTEXT_PATH} \
  --max-iterations 5
```

### Export Results
```bash
python src/plan_refine_cli/main.py finalize \
  --run-id {RUN_ID} \
  --output-dir ./output
```

---

## 📐 Schema Cheat Sheet

### Plan Structure (14 fields)
```
plan_id, version, objective, scope,
assumptions, constraints, workstreams, deliverables,
acceptance_criteria, risks, dependencies, gates,
declared_new_artifacts, metadata
```

### ID Formats
```
PLAN_20260218T120000Z_abc12345
CRITIC_20260218T120000Z_xyz78901
PATCH_20260218T120000Z_def45678
CONTEXT_20260218T120000Z_ghi12345
```

### JSON Pointers
```
/workstreams/0/steps/2/command
/acceptance_criteria/1/target_value
/metadata/iteration
```

---

## 🔍 Linter Rules

| Code | Severity | Description |
|------|----------|-------------|
| COMP-001 | CRITICAL | Missing required section |
| COMP-002 | HIGH | Empty required section |
| SCHEMA-001 | CRITICAL | Schema violation |
| PATTERN-* | HIGH | Forbidden pattern detected |
| REF-001 | HIGH | Invalid artifact reference |
| AC-001 | MEDIUM | Missing measurement method |
| AC-002 | MEDIUM | Missing target value |

---

## 🚪 Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Validation error |
| 2 | Execution error |
| 3 | Manual escalation |

---

## 🛠️ Debugging

### View Run State
```bash
cat .planning_loop_state/runs/{RUN_ID}/manifest.json | jq
```

### Check Defects
```bash
cat .planning_loop_state/runs/{RUN_ID}/critic_reports/report_001.json | jq '.hard_defects'
```

### Compare Iterations
```bash
diff \
  .planning_loop_state/runs/{RUN_ID}/iterations/iter_000/plan.json \
  .planning_loop_state/runs/{RUN_ID}/iterations/iter_001/plan.json
```

---

## ✅ Validation Scripts

```bash
python scripts/validate_dependencies.py   # Check packages
python scripts/validate_all_schemas.py    # Check schemas
python scripts/check_resources.py         # Check RAM/disk
python scripts/check_permissions.py       # Check permissions
```

---

## 🧪 Testing

```bash
pytest tests/ -v                          # All tests
pytest tests/test_schemas.py -v           # Schema tests only
pytest tests/ --cov=src/plan_refine_cli   # With coverage
```

---

## 📂 Directory Structure

```
.planning_loop_state/
├── runs/{run_id}/
│   ├── manifest.json
│   ├── context_bundle.json
│   ├── policy_snapshot.json
│   ├── iterations/
│   ├── patches/
│   └── critic_reports/
├── evidence/
└── metrics/
```

---

## ⚡ Performance

| Operation | Time | Memory |
|-----------|------|--------|
| Context gen | 0.5-2s | 50 MB |
| Skeleton | 0.1-0.5s | 10 MB |
| Critic | 0.2-1s | 20 MB |
| Patch | <0.1s | 5 MB |
| Full loop | 2-10s | 100 MB |

---

## 🔧 Configuration

### Policy Settings
```json
{
  "max_iterations": 5,
  "critic_mode": "DETERMINISTIC",
  "soft_defect_improvement_threshold": 0.05,
  "forbidden_patterns": [...]
}
```

### Environment Variables
```bash
OPENAI_API_KEY=sk-...          # For LLM mode
PLANNING_LOOP_DEBUG=1          # Enable debug logging
PLANNING_LOOP_STATE_DIR=path   # Custom state directory
```

---

## 🎯 Termination Conditions

| Condition | Reason | Exit |
|-----------|--------|------|
| ZERO_HARD_DEFECTS | Success | 0 |
| MAX_ITERATIONS | Limit hit | 0 |
| CONTEXT_STALE | Refresh needed | 0 |
| PLATEAU | No progress | 0 |

---

## 📞 Support

**Documentation:**
- `README_PLANNING_LOOP.md` - User guide
- `PLANNING_LOOP_COMPLETE_DOCUMENTATION.md` - Full docs
- `PLANNING_LOOP_TECHNICAL_ARCHITECTURE.md` - Architecture
- `PLANNING_LOOP_DEVELOPER_GUIDE.md` - Developer guide

**Examples:**
- `examples/example_end_to_end.py` - Working demo

---

## 🎓 Learn More

### Implementation Plan
`01260207201000001139_docs/01260207201000001145_planning/PLANNING_LOOP_IMPLEMENTATION_PLAN.md`

### Phase B Execution
`01260207201000001139_docs/01260207201000001145_planning/PHASE_B_V1.1.0_CHANGELOG.md`

---

**Quick Reference v2.0.0**
