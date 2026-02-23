# Planning Loop Implementation: Quick Start Guide
## Template-Enhanced Version 2.0

**Source Document**: `PLANNING_LOOP_IMPLEMENTATION_PLAN.md`
**For**: Developers starting implementation of Planning-Only Refinement Loop

---

## What You're Building

A **deterministic, auditable planning refinement system** that:
- Takes vague requirements → produces validated, executable plans
- Uses iterative planner-critic loops to fix defects
- Enforces contracts at every step
- Collects cryptographic evidence chains
- Self-heals common failures with bounded retries

---

## Critical Path (Start Here)

### Week 1: Create 12 Schemas ⚡ CRITICAL
**Why first**: Everything validates against these schemas
**Files**: `schemas/PLAN.schema.json`, `CRITIC_REPORT.schema.json`, `PATCH.schema.json`, etc.
**Command**: `python scripts/validate_all_schemas.py`
**Success**: All schemas validate, sample docs pass/fail correctly

### Week 2: Build CLI Foundation
**Files**: `src/plan_refine_cli/main.py`, `run_directory.py`, `hash_utils.py`, `schema_validator.py`
**Command**: `plan_refine_cli --help` shows all commands
**Success**: Can create run directories, compute hashes, validate schemas

### Week 3: Policy + Context Infrastructure
**Files**: `policy_manager.py`, `context_generator.py`, `config/baseline_planning_policy.json`
**Command**: `plan_refine_cli context --run-id test-001`
**Success**: Context bundle captures repo state, policy freezes correctly

### Week 4-6: Core Loop (Planner + Critic + Patch + Orchestrator)
**Files**: `agents/planner.py`, `agents/critic.py`, `patch_engine.py`, `orchestrator.py`
**Command**: `plan_refine_cli loop --run-id test-001 --max-iters 10`
**Success**: Loop executes skeleton → lint → refine → terminate

### Week 7-8: Enforcement (Authority + Safety + Envelopes)
**Files**: `authority/`, `protectors/`, `gates/`, `envelopes/`
**Success**: Circuit breakers work, oscillation detected, evidence sealed

### Week 9-10: Commands (Full CLI Implementation)
**Commands**: init, context, skeleton, lint, loop, finalize
**Success**: All commands functional end-to-end

### Week 11-12: Testing + Documentation
**Tests**: 40+ test files, 95% coverage
**Docs**: 10 documentation files
**Success**: All tests pass, documentation complete

---

## The Loop in 6 Commands

```bash
# 1. Initialize a planning run
plan_refine_cli init --repo-root . --policy-version 1.0 --max-iters 10

# 2. Generate context bundle (repo inventory)
plan_refine_cli context --run-id PLAN-20260218-001

# 3. Generate initial plan skeleton
plan_refine_cli skeleton --run-id PLAN-20260218-001 --idea "Implement feature X"

# 4. Lint the plan (optional standalone)
plan_refine_cli lint --run-id PLAN-20260218-001 --plan-file plan_skeleton.json

# 5. Run refinement loop (main event)
plan_refine_cli loop --run-id PLAN-20260218-001 --max-iters 10

# 6. Finalize and package results
plan_refine_cli finalize --run-id PLAN-20260218-001
```

**Output**: `planning_runs/PLAN-20260218-001/99_final/` contains validated plan package

---

## Key Files You'll Create (Top 20)

### Must Have First (Foundation):
1. `schemas/PLAN.schema.json` - defines valid plan structure
2. `schemas/CRITIC_REPORT.schema.json` - defines defect reports
3. `schemas/PATCH.schema.json` - RFC-6902 patch format
4. `src/plan_refine_cli/main.py` - CLI entry point
5. `src/plan_refine_cli/run_directory.py` - manages planning_runs/ structure
6. `src/plan_refine_cli/hash_utils.py` - deterministic hashing
7. `src/plan_refine_cli/schema_validator.py` - schema validation

### Must Have Second (Policy + Context):
8. `config/baseline_planning_policy.json` - 25 rules, defect taxonomy
9. `src/plan_refine_cli/policy_manager.py` - freeze policy snapshots
10. `src/plan_refine_cli/context_generator.py` - scan repo, build context bundle

### Must Have Third (Agents):
11. `src/plan_refine_cli/agents/planner.py` - LLM planner agent
12. `src/plan_refine_cli/agents/critic.py` - LLM/deterministic critic
13. `src/plan_refine_cli/llm_client.py` - OpenAI integration with audit
14. `prompts/planner_skeleton.md` - skeleton generation prompt
15. `prompts/planner_refine.md` - refinement prompt
16. `prompts/critic_llm.md` - critic prompt

### Must Have Fourth (Loop Engine):
17. `src/plan_refine_cli/patch_engine.py` - authoritative patch application
18. `src/plan_refine_cli/orchestrator.py` - main loop coordinator
19. `src/plan_refine_cli/evaluators/termination.py` - termination logic
20. `src/plan_refine_cli/linters/deterministic_linters.py` - 7+ linters

---

## Critical Decisions You'll Make

### Decision 1: Critic Mode
**Options**:
- Deterministic (rule-based, 100% reproducible)
- LLM (GPT-4, better quality, 1-2% non-determinism)
- Hybrid (deterministic first, LLM for complex cases)

**Recommendation**: Start deterministic, add LLM as optional

### Decision 2: Schema Validation Library
**Options**:
- `jsonschema` (standard, slower)
- `fastjsonschema` (compiled, 10x faster)

**Recommendation**: jsonschema for compatibility, fastjsonschema for production

### Decision 3: Evidence Storage
**Options**:
- Individual JSON files (simple, auditable)
- SQLite database (queryable, compact)

**Recommendation**: Individual files for transparency

### Decision 4: Loop Termination Strategy
**Options**:
- Hard defects only (strict)
- Hard + soft threshold (balanced)
- Configurable per policy (flexible)

**Recommendation**: Configurable with defaults

### Decision 5: Parallel vs Sequential Phases
**Options**:
- Sequential only (simple, safe)
- Parallel with worktrees (complex, faster)

**Recommendation**: Sequential for Phase A, parallel ready for Phase B

---

## Common Pitfalls to Avoid

### ❌ Don't:
1. Skip step contracts (every step needs full contract)
2. Leave TODO/TBD placeholders (violates NO IMPLIED BEHAVIOR)
3. Write command descriptions instead of executable commands
4. Forget to seal hashes after each iteration
5. Allow planner to directly mutate plan (only via patches)
6. Skip evidence collection (breaks audit trail)
7. Hard-code file paths (use RunDirectoryManager)
8. Forget to validate patch before applying
9. Skip rollback procedures
10. Leave defect JSON pointers unvalidated

### ✅ Do:
1. Write executable shell commands (not descriptions)
2. Validate everything against schemas
3. Seal evidence with hashes
4. Use ToolCall/ToolResult envelopes
5. Enforce file scopes
6. Track all metrics
7. Test idempotency
8. Document decisions
9. Follow critical path
10. Run all 23 validation gates

---

## Test-Driven Development Order

### Day 1: Schema Tests First
```bash
pytest tests/schemas/test_all_schemas.py -v
```
**Why**: Catch schema errors before implementation

### Week 2: Foundation Tests
```bash
pytest tests/unit/test_hash_utils.py -v
pytest tests/unit/test_cli_foundation.py -v
```
**Why**: Verify deterministic hashing and CLI routing

### Week 6: Integration Tests
```bash
pytest tests/integration/test_full_loop.py -v
```
**Why**: Verify loop cycle works end-to-end

### Week 12: E2E Tests
```bash
pytest tests/e2e/ -v --junit-xml=.planning_loop_state/evidence/e2e_results.xml
```
**Why**: Verify complete system with realistic scenarios

---

## Validation Checkpoints

### After Week 3 (Foundation):
```bash
python scripts/run_all_gates.py --phase PH-01
pytest tests/unit/ -v --cov=src/plan_refine_cli --cov-report=term-missing
```
**Pass Criteria**: All gates pass, coverage >= 80%

### After Week 6 (Core Loop):
```bash
plan_refine_cli loop --run-id test-simple --max-iters 5
python scripts/validate_evidence_chain.py planning_runs/test-simple/
```
**Pass Criteria**: Loop completes, evidence chain valid

### After Week 10 (All Commands):
```bash
# Full workflow test
plan_refine_cli init --repo-root . --policy-version 1.0
plan_refine_cli context --run-id $RUN_ID
plan_refine_cli skeleton --run-id $RUN_ID
plan_refine_cli loop --run-id $RUN_ID --max-iters 10
plan_refine_cli finalize --run-id $RUN_ID
python scripts/run_all_gates.py --run-id $RUN_ID
```
**Pass Criteria**: All 23 gates pass, plan package complete

---

## Quick Reference: File Locations

```
Planning Loop Project Structure:
├── config/
│   ├── baseline_planning_policy.json      ← 25 rules, defect taxonomy
│   └── critic_contract_template.json      ← critic configuration
├── schemas/
│   ├── PLAN.schema.json                   ← plan structure
│   ├── CRITIC_REPORT.schema.json          ← defect reports
│   ├── PATCH.schema.json                  ← RFC-6902 patches
│   └── [9 more schemas]
├── src/plan_refine_cli/
│   ├── main.py                            ← CLI entry point
│   ├── run_directory.py                   ← run management
│   ├── hash_utils.py                      ← SHA256 utilities
│   ├── schema_validator.py                ← JSON schema validation
│   ├── policy_manager.py                  ← policy freezing
│   ├── context_generator.py               ← repo scanning
│   ├── orchestrator.py                    ← main loop
│   ├── patch_engine.py                    ← authoritative patcher
│   ├── agents/
│   │   ├── planner.py                     ← LLM planner
│   │   └── critic.py                      ← LLM/deterministic critic
│   ├── linters/
│   │   └── deterministic_linters.py       ← 7+ linters
│   ├── analyzers/
│   │   └── plan_analyzers.py              ← dependency graphs
│   ├── authority/
│   │   └── mutation_controller.py         ← patch authority
│   ├── protectors/
│   │   ├── oscillation_detector.py        ← detect loops
│   │   ├── circuit_breaker.py             ← prevent runaway
│   │   └── attempt_cap.py                 ← enforce limits
│   ├── envelopes/
│   │   ├── tool_call.py                   ← tool invocation tracking
│   │   └── tool_result.py                 ← tool result tracking
│   └── [20+ more modules]
├── prompts/
│   ├── planner_skeleton.md                ← skeleton generation
│   ├── planner_refine.md                  ← refinement iteration
│   └── critic_llm.md                      ← critic evaluation
├── scripts/
│   ├── run_all_gates.py                   ← execute 23 gates
│   ├── validate_step_contract.py          ← contract validation
│   ├── validate_evidence_chain.py         ← chain verification
│   └── [20+ validators]
├── tests/
│   ├── unit/ (20+ files)
│   ├── integration/ (10+ files)
│   └── e2e/ (10+ files)
├── planning_runs/                         ← runtime artifacts
│   └── {planning_run_id}/
│       ├── 00_run/                        ← manifest + policy
│       ├── 01_context/                    ← context bundle
│       ├── 02_skeleton/                   ← initial plan
│       ├── 03_iterations/                 ← loop cycles
│       │   └── {N}/                       ← per iteration
│       └── 99_final/                      ← result package
└── .planning_loop_state/
    ├── evidence/                          ← proof artifacts
    ├── metrics/                           ← metrics.jsonl
    └── planning/                          ← decision ledger
```

---

## Success Indicators

### ✅ Foundation Complete (Week 3):
- All 12 schemas validate
- CLI commands registered
- Context bundle generates correctly
- Policy freezes without errors
- Unit tests: 80%+ coverage

### ✅ Core Loop Complete (Week 6):
- Loop executes full cycle
- Patches apply deterministically
- Defects tracked across iterations
- Integration tests pass

### ✅ Enforcement Complete (Week 8):
- Circuit breakers prevent runaway
- Oscillation detected
- Evidence chain validates
- File scopes enforced

### ✅ QA Ready (Week 12):
- All 23 gates pass
- 95%+ test coverage
- E2E scenarios pass
- Documentation complete
- Sample run produces valid package

---

## Getting Started Today

### Step 1: Set up environment
```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install jsonschema jsonpatch click pyyaml rich
pip install pytest pytest-cov ruff mypy
```

### Step 2: Create project structure
```bash
mkdir -p src/plan_refine_cli schemas config prompts scripts tests
touch src/plan_refine_cli/__init__.py
```

### Step 3: Start with first schema
```bash
# Create schemas/PLAN.schema.json
# Validate it works:
python -c "import jsonschema; import json; jsonschema.Draft202012Validator(json.load(open('schemas/PLAN.schema.json')))"
```

### Step 4: Build iteratively
- Day 1-5: Finish all 12 schemas
- Day 6-10: CLI foundation + tests
- Day 11-15: Policy + context + tests
- Continue through critical path...

---

## Need Help?

### Common Questions:

**Q: What's the minimum viable loop?**
A: Skeleton generation + 1 lint pass + 1 refinement iteration + termination check. No self-healing, no enforcement.

**Q: Can I skip step contracts?**
A: No. Step contracts are how the system achieves determinism. Every step needs all 14 fields.

**Q: Do I need LLM for critic?**
A: No. Start with deterministic critic (rule-based). LLM is optional enhancement.

**Q: What if I can't hit 95% coverage?**
A: 80% is acceptable for MVP, but document why 95% not achievable.

**Q: Can I change the directory structure?**
A: Use the template structure exactly. It's designed for evidence chain validation.

### References:
- Full Plan: `PLANNING_LOOP_IMPLEMENTATION_PLAN.md`
- Template: `NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3.json`
- Tech Spec: `NEWPHASEPLANPROCESS_TECHNICAL_SPECIFICATION_V3.json`

---

**START IMPLEMENTATION**: Week 1, Day 1 - Create schemas/PLAN.schema.json

**FIRST VALIDATION**: After Day 5 - All schemas must validate

**FIRST GATE**: After Week 3 - Foundation validation gate must pass

**END GOAL**: Week 12 - QA functional version with all 23 gates passing

---

**Document Version**: 1.0
**Created**: 2026-02-18
**Status**: Ready for Implementation
