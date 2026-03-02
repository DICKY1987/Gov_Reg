# QUICK COMMAND REFERENCE
## Planning Loop Implementation - Essential Commands

---

## 🚀 START IMPLEMENTATION

```bash
# 1. Create feature branch
git checkout -b feature/planning-loop

# 2. Create directory structure
mkdir -p schemas tests/schemas src/plan_refine_cli/{agents,linters,analyzers,authority,protectors,gates,envelopes,evaluators,validators}
mkdir -p config prompts scripts .planning_loop_state/{evidence,metrics,planning,llm_calls,escalation}

# 3. Create requirements files
touch requirements.txt requirements-dev.txt

# 4. Start Week 1, Day 1
touch schemas/PLAN.schema.json
touch tests/schemas/test_plan_schema.py
```

---

## 📋 VERIFICATION COMMANDS

### Before Starting (Pre-Week 1):
```bash
# Automated verification
python 01260207201000001139_docs/01260207201000001145_planning/verify_ready_to_start.py

# Expected: Exit code 0, "ALL CHECKS PASSED"
```

### After Week 3 (Foundation Complete):
```bash
# Run foundation validation gate
python scripts/run_all_gates.py --phase PH-01

# Run unit tests with coverage
pytest tests/unit/ -v --cov=src/plan_refine_cli --cov-report=term-missing --cov-report=json:.planning_loop_state/evidence/PH-01/coverage.json

# Expect: All gates pass, coverage >= 80%
```

### After Week 6 (Core Loop Complete):
```bash
# Test full loop execution
plan_refine_cli init --repo-root . --policy-version 1.0 --critic-mode deterministic
plan_refine_cli context --run-id test-simple-001
plan_refine_cli skeleton --run-id test-simple-001 --idea "Simple test plan"
plan_refine_cli loop --run-id test-simple-001 --max-iters 5
plan_refine_cli finalize --run-id test-simple-001

# Validate evidence chain
python scripts/validate_evidence_chain.py planning_runs/test-simple-001/

# Expect: Loop completes, evidence chain valid
```

### After Week 10 (All Commands Complete):
```bash
# Full workflow test
plan_refine_cli init --repo-root . --policy-version 1.0
plan_refine_cli context --run-id full-test-001
plan_refine_cli skeleton --run-id full-test-001
plan_refine_cli loop --run-id full-test-001 --max-iters 10
plan_refine_cli finalize --run-id full-test-001

# Run all gates
python scripts/run_all_gates.py --run-id full-test-001

# Expect: All 24 gates pass
```

### After Week 12 (QA Complete):
```bash
# Full test suite
pytest tests/ -v --cov=src/plan_refine_cli --cov-report=term-missing --cov-report=html:reports/coverage

# E2E scenarios
pytest tests/e2e/ -v --junit-xml=.planning_loop_state/evidence/PH-05/e2e_results.xml

# All gates
python scripts/run_all_gates.py --plan-file planning_runs/final-test-001/99_final/plan.json

# Expect: Coverage >= 95%, all tests pass, all gates pass
```

---

## 🔍 INSPECTION COMMANDS

### Check Schema Validity:
```bash
# Single schema
python -c "import jsonschema, json; jsonschema.Draft202012Validator(json.load(open('schemas/PLAN.schema.json')))"

# All schemas
python scripts/P_01260207201000000004_validate_all_schemas.py
```

### Check Plan Consistency:
```bash
# Check version
grep "Version 2.0" 01260207201000001139_docs/01260207201000001145_planning/PLANNING_LOOP_IMPLEMENTATION_PLAN.md

# Check GATE-009
grep "GATE-009" 01260207201000001139_docs/01260207201000001145_planning/PLANNING_LOOP_IMPLEMENTATION_PLAN.md

# Check 14 fields
grep "14 required fields" 01260207201000001139_docs/01260207201000001145_planning/PLANNING_LOOP_IMPLEMENTATION_PLAN.md

# Check state isolation
grep ".planning_loop_state/" 01260207201000001139_docs/01260207201000001145_planning/PLANNING_LOOP_IMPLEMENTATION_PLAN.md | head -5
```

### Check State Directory Isolation:
```bash
# Verify existing state preserved
ls .state/ | head -10

# Verify planning loop state separate (will be created)
ls .planning_loop_state/ 2>/dev/null || echo "Not yet created (will be created during init)"
```

### Check Template Files:
```bash
# Verify template files exist
ls -lh newPhasePlanProcess/01260207201000000510_NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3.json
ls -lh newPhasePlanProcess/01260207201000000180_NEWPHASEPLANPROCESS_TECHNICAL_SPECIFICATION_V3.json
```

---

## 🧪 TESTING COMMANDS

### Unit Tests (Week 2+):
```bash
# Single module
pytest tests/unit/test_hash_utils.py -v

# All unit tests
pytest tests/unit/ -v

# With coverage
pytest tests/unit/ -v --cov=src/plan_refine_cli --cov-report=term-missing
```

### Integration Tests (Week 6+):
```bash
# Single integration test
pytest tests/integration/test_planner_agent.py -v

# All integration tests
pytest tests/integration/ -v
```

### E2E Tests (Week 12):
```bash
# Single scenario
pytest tests/e2e/test_simple_refinement.py -v

# All E2E tests
pytest tests/e2e/ -v --junit-xml=.planning_loop_state/evidence/PH-05/e2e_results.xml
```

### Coverage Report:
```bash
# Generate HTML coverage report
pytest tests/ --cov=src/plan_refine_cli --cov-report=html:reports/coverage

# View: open reports/coverage/index.html
```

---

## 🛠️ DEVELOPMENT COMMANDS

### Create New Schema:
```bash
# Template
cat > schemas/NEW_SCHEMA.schema.json << 'EOF'
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://govreg.local/schemas/NEW_SCHEMA.schema.json",
  "title": "Schema Title",
  "type": "object",
  "required": [],
  "properties": {}
}
EOF

# Validate
python -c "import jsonschema, json; jsonschema.Draft202012Validator(json.load(open('schemas/NEW_SCHEMA.schema.json')))"
```

### Create New Module:
```bash
# With contract stub
cat > src/plan_refine_cli/new_module.py << 'EOF'
"""
Module: new_module
Purpose: Brief description

Step Contract: STEP-XXX
Inputs: List inputs
Outputs: List outputs
"""

def main():
    pass

if __name__ == "__main__":
    main()
EOF
```

### Create New Test:
```bash
cat > tests/unit/test_new_module.py << 'EOF'
import pytest
from plan_refine_cli.new_module import main

def test_main():
    """Test basic functionality"""
    result = main()
    assert result is not None
EOF

# Run test
pytest tests/unit/test_new_module.py -v
```

---

## 📊 MONITORING COMMANDS

### Check Gate Status:
```bash
# Run all gates for a phase
python scripts/run_all_gates.py --phase PH-01

# Run single gate
python scripts/gates/GATE-003_step_contracts.py --plan-file plan.json

# View gate results
cat .planning_loop_state/evidence/gates/gate_execution_summary.json | jq '.gates[] | select(.status=="FAIL")'
```

### Check Metrics:
```bash
# View latest metrics
tail -20 .planning_loop_state/metrics/metrics.jsonl | jq

# Phase summary
cat .planning_loop_state/metrics/PH-01/summary.json | jq

# Validate metrics against targets
python scripts/validate_metrics.py .planning_loop_state/metrics/metrics.jsonl
```

### Check Evidence Chain:
```bash
# Validate phase evidence chain
python scripts/validate_evidence_chain.py .planning_loop_state/evidence/PH-01/

# Check specific step evidence
ls .planning_loop_state/evidence/PH-01/STEP-003/

# Verify hashes
python scripts/verify_artifact_hashes.py planning_runs/{run_id}/03_iterations/{N}/hashes.json
```

---

## 🔄 LOOP EXECUTION COMMANDS

### Run Complete Loop:
```bash
# Full workflow
plan_refine_cli init --repo-root . --policy-version 1.0 --critic-mode deterministic --max-iters 10
export RUN_ID=$(cat .planning_loop_state/planning/latest_run_id.txt)

plan_refine_cli context --run-id $RUN_ID
plan_refine_cli skeleton --run-id $RUN_ID --idea "Your project objective"
plan_refine_cli loop --run-id $RUN_ID --max-iters 10
plan_refine_cli finalize --run-id $RUN_ID

# Output in: planning_runs/$RUN_ID/99_final/
```

### Run With LLM Mode (optional):
```bash
# Requires OPENAI_API_KEY environment variable
export OPENAI_API_KEY="sk-..."

plan_refine_cli init --repo-root . --policy-version 1.0 --critic-mode llm --max-iters 10 --cost-cap 5.0

# Continue as above...
```

### Debug Loop Iteration:
```bash
# Run single lint pass
plan_refine_cli lint --run-id $RUN_ID --plan-file planning_runs/$RUN_ID/02_skeleton/plan_skeleton.json

# View lint report
cat planning_runs/$RUN_ID/03_iterations/001/plan_lint_report.json | jq '.hard_defects'

# Check defect resolution
cat planning_runs/$RUN_ID/03_iterations/001/defect_resolution_report.json | jq
```

---

## 🐛 DEBUGGING COMMANDS

### Check Why Gate Failed:
```bash
# View gate evidence
cat .planning_loop_state/evidence/gates/GATE-003/result.json | jq

# Re-run gate with verbose output
python scripts/gates/GATE-003_step_contracts.py --plan-file plan.json --verbose
```

### Check Why Test Failed:
```bash
# Run single test with full output
pytest tests/unit/test_hash_utils.py::test_deterministic_hash -v -s

# Run with debugger
pytest tests/unit/test_hash_utils.py::test_deterministic_hash -v --pdb
```

### Check Loop Termination:
```bash
# View termination record
cat planning_runs/$RUN_ID/99_final/refinement_termination_record.json | jq

# Check defect trajectory
cat planning_runs/$RUN_ID/99_final/summary.json | jq '.defect_trajectory'
```

### Check Cost (LLM mode):
```bash
# View LLM call log
cat .planning_loop_state/llm_calls/$RUN_ID/calls.jsonl | jq -s 'map(.cost_usd) | add'

# View cost summary
cat .planning_loop_state/llm_calls/$RUN_ID/cost_summary.json | jq
```

---

## 📦 PACKAGING COMMANDS

### Create Final Package:
```bash
# Finalize run (already done via command)
plan_refine_cli finalize --run-id $RUN_ID

# Verify package completeness
python scripts/validate_final_package.py planning_runs/$RUN_ID/99_final/

# Package structure:
# planning_runs/$RUN_ID/99_final/
#   ├── plan.json                      (validated plan)
#   ├── plan_lint_report.json          (no hard defects)
#   ├── summary.json                   (run summary)
#   ├── refinement_termination_record.json
#   └── hashes.json                    (artifact hashes)
```

---

## 🎯 CRITICAL PATH COMMANDS

### Week 1 (Schemas):
```bash
python scripts/P_01260207201000000004_validate_all_schemas.py
# Expect: All 12 schemas valid
```

### Week 3 (Foundation):
```bash
python scripts/run_all_gates.py --phase PH-01
pytest tests/unit/ -v --cov=src/plan_refine_cli
# Expect: Gates pass, coverage >= 80%
```

### Week 6 (Core Loop):
```bash
plan_refine_cli loop --run-id test-001 --max-iters 5
python scripts/validate_evidence_chain.py planning_runs/test-001/
# Expect: Loop completes, evidence valid
```

### Week 12 (QA Ready):
```bash
python scripts/run_all_gates.py --phase PH-05
pytest tests/ -v --cov=src/plan_refine_cli --cov-report=term-missing
# Expect: All 24 gates pass, coverage >= 95%
```

---

## 🔧 UTILITY COMMANDS

### View Run Status:
```bash
# List all runs
ls planning_runs/

# View run manifest
cat planning_runs/$RUN_ID/00_run/planning_run_manifest.json | jq

# Check iteration count
ls planning_runs/$RUN_ID/03_iterations/ | wc -l
```

### Clean Up:
```bash
# Remove test runs
rm -rf planning_runs/test-*

# Clean evidence (careful!)
rm -rf .planning_loop_state/evidence/test_*

# Clean metrics
rm .planning_loop_state/metrics/metrics.jsonl
```

### Lint/Format Code:
```bash
# Run ruff linter
ruff check src/plan_refine_cli/

# Format code
ruff format src/plan_refine_cli/

# Type checking
mypy src/plan_refine_cli/ --strict
```

---

## 📚 DOCUMENTATION COMMANDS

### Generate API Docs:
```bash
# Generate module documentation
python -m pydoc -w src/plan_refine_cli/main

# Generate full API reference (if sphinx setup)
cd docs/ && make html
```

### View Inline Help:
```bash
# CLI help
plan_refine_cli --help
plan_refine_cli init --help
plan_refine_cli loop --help

# Module help
python -m plan_refine_cli.agents.planner --help
```

---

## ⚡ SHORTCUTS

### Quick Schema Validation:
```bash
# Validate all at once
for schema in schemas/*.schema.json; do 
  python -c "import jsonschema, json, sys; jsonschema.Draft202012Validator(json.load(open('$schema'))); print('✓ $schema')" || echo "✗ $schema"; 
done
```

### Quick Test All:
```bash
# Run all tests with brief output
pytest tests/ -v --tb=short --junit-xml=.planning_loop_state/evidence/test_results.xml

# View failures only
pytest tests/ -v --tb=short -x  # Stop on first failure
```

### Quick Loop Test (Offline):
```bash
# Test loop without LLM (deterministic mode)
plan_refine_cli loop --run-id quick-test --max-iters 3 --critic-mode deterministic --no-llm

# Verify result
cat planning_runs/quick-test/99_final/refinement_termination_record.json | jq .reason
```

---

## 🆘 EMERGENCY COMMANDS

### Rollback Last Step:
```bash
# View step rollback procedure
cat .planning_loop_state/evidence/PH-XX/STEP-XXX/step_contract.json | jq .rollback

# Execute rollback
# (follow commands from rollback.commands[])
```

### Stop Runaway Loop:
```bash
# Kill loop process (if stuck)
# Control-C to stop gracefully

# Force terminate
pkill -f "plan_refine_cli loop"

# Check if stopped
ps aux | grep plan_refine_cli
```

### Reset Run:
```bash
# Delete run directory (careful!)
rm -rf planning_runs/$RUN_ID

# Start over
plan_refine_cli init --repo-root . --policy-version 1.0
```

---

## 📍 FILE LOCATIONS

### Configuration:
- `config/baseline_planning_policy.json` - Policy rules
- `config/critic_contract_template.json` - Critic config
- `requirements.txt` - Python dependencies

### Schemas:
- `schemas/*.schema.json` - 12 core schemas

### Source:
- `src/plan_refine_cli/` - All source modules

### Tests:
- `tests/unit/` - Unit tests
- `tests/integration/` - Integration tests
- `tests/e2e/` - End-to-end tests

### Scripts:
- `scripts/validate_*.py` - Validation scripts
- `scripts/gates/GATE-*.py` - Gate scripts
- `scripts/run_all_gates.py` - Gate runner

### Prompts:
- `prompts/planner_skeleton.md` - Skeleton prompt
- `prompts/planner_refine.md` - Refine prompt
- `prompts/critic_llm.md` - Critic prompt

### Runtime:
- `planning_runs/{run_id}/` - Per-run artifacts
- `.planning_loop_state/` - Evidence, metrics, planning

### Documentation:
- `docs/README_PLANNING_LOOP.md` - System README
- `docs/OPERATOR_GUIDE.md` - Operations manual
- `docs/SCHEMA_REFERENCE.md` - Schema docs

---

## 🎯 MILESTONE GATES

| Week | Gate | Command | Pass Criteria |
|------|------|---------|---------------|
| 3 | PR-GATE-PH01 | `python scripts/run_all_gates.py --phase PH-01` | All gates pass, 80%+ coverage |
| 6 | PR-GATE-PH02 | `plan_refine_cli loop --run-id test` | Loop completes, integration tests pass |
| 8 | PR-GATE-PH03 | `pytest tests/integration/test_self_healing.py` | Circuit breakers work |
| 10 | PR-GATE-PH04 | `plan_refine_cli --help` | All 6 commands functional |
| 12 | PR-GATE-PH05 | `python scripts/run_all_gates.py` | All 24 gates pass, 95%+ coverage |

---

## 🚦 GO/NO-GO: ✅ GO

**Verification**: All checks passed (exit code 0)
**Readiness**: 10/10 prerequisites met
**Risk**: LOW (all mitigated)
**Timeline**: 10-12 weeks (realistic)
**Recommendation**: **START IMMEDIATELY**

---

**First Command**:
```bash
git checkout -b feature/planning-loop
```

**First Task**:
```bash
touch schemas/PLAN.schema.json
```

**Target**: Week 12 - QA functional version with all 24 gates passing

---

**Document**: QUICK_COMMAND_REFERENCE.md
**Version**: 1.0
**Date**: 2026-02-18
