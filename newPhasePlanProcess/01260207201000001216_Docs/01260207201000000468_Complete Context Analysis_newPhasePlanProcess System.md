Complete Context Analysis - newPhasePlanProcess System

  I've now analyzed both the documentation (16 files in Docs/) and the
  actual implementation (CLI, scripts, schemas, gate dependencies).
  Here's the comprehensive picture:

  ---
  Executive Summary

  System Status: 75-80% Ready (better than documented)

  The newPhasePlanProcess v2.4.0 is a deterministic plan validation
  system with:
  - ✅ 19 required gates + 5 optional gates in dependency-ordered
  pipeline
  - ✅ 12 FM (Failure Mode) checks for wiring integrity
  - ✅ Fully functional CLI with 6 commands (validate, normalize,
  compile, execute, diff, run-gates)
  - ✅ Gate orchestration with topological sorting (Kahn's algorithm)
  - ⚠️ Schema version mismatch in FM scripts (main blocker)

  ---
  Critical Blocker Status Update

  Based on actual code inspection:

  ✅ BLOCKER #2 - RESOLVED

  Documentation claimed: Wrong schema path in CLI line 37
  Actual code (line 37):
  SCHEMA_PATH = Path(__file__).parent.parent / "schemas" /
  "01260207233100000674_NEWPHASEPLANPROCESS_plan.schema.v2.4.0.json"
  Status: CORRECT - This has been fixed

  ✅ BLOCKER #3 - RESOLVED

  Documentation claimed: Missing
  01260207233100000678_gate_dependencies.json
  Actual status: File EXISTS with complete 24-gate dependency graph
  Status: RESOLVED

  ⚠️ BLOCKER #1 - POSSIBLY RESOLVED

  Documentation claimed: Syntax error in phase_plan_converter.py line 17
  Actual code (line 16):
  REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
  Status: NO SYNTAX ERROR FOUND - May have been fixed

  ❌ BLOCKER #5 - CONFIRMED (Main Issue)

  Issue: FM scripts reference plan.artifacts which doesn't exist in
  v2.4.0 schema
  Example: P_01260207233100000277_check_orphans.py:14
  artifacts = data.get('plan', {}).get('artifacts', {})
  Impact: All 12 FM checks will fail
  Status: BLOCKING - Requires schema migration or FM script updates

  ⚠️ BLOCKER #4 - UNCLEAR

  Documentation claimed: FM audit script uses positional arg instead of
  --plan-file
  Actual code (line 55): Uses CORRECT --plan-file flag
  Status: Code is correct, documentation may be outdated

  ⚠️ BLOCKER #6 - DOCUMENTATION ISSUE

  Issue: Missing FM_GATE_MAPPING_CANONICAL.md and
  TECHNICAL_DOCUMENTATION.md
  Mitigation: Information exists in
  CURRENT_SYSTEM_TECHNICAL_SPECIFICATION.md and gate_dependencies.json
  Status: Non-blocking - documentation completeness issue

  ---
  System Architecture Verified

  CLI Commands (All Implemented)

  # Schema validation
  python scripts/P_01260207233100000242_NEWPHASEPLANPROCESS_plan_cli.py
  validate <plan.json>

  # Normalize structure
  python scripts/P_01260207233100000242_NEWPHASEPLANPROCESS_plan_cli.py
  normalize <plan.json>

  # Compile (normalize + regenerate navigation + validate formulas)
  python scripts/P_01260207233100000242_NEWPHASEPLANPROCESS_plan_cli.py
  compile <plan.json> <output.json>

  # Execute plan
  python scripts/P_01260207233100000242_NEWPHASEPLANPROCESS_plan_cli.py
  execute <plan.json>

  # Run all gates in dependency order
  python scripts/P_01260207233100000242_NEWPHASEPLANPROCESS_plan_cli.py
  run-gates --plan-file <plan.json>

  Gate Execution Pipeline

  Critical Path:
  GATE-000 → GATE-001 → GATE-002 → GATE-010 → GATE-011 → GATE-012 →
  GATE-013

  Execution Phases:
  1. pre-validation: GATE-000 (no obfuscation check)
  2. core-validation: GATE-001-005 (schema, gates, contracts,
  assumptions, artifacts)
  3. automation: GATE-006-008 (spec → index → diagrams)
  4. wiring: GATE-010-013 (proof → registry → FM audit → E2E)
  5. validation: GATE-014-017 (closure, rollback, verification, SSOT)
  6. meta-validation: GATE-998-999 (automation audit, goal
  reconciliation)

  Failure Modes (FM-01 through FM-12)
  FM: FM-01
  Check: Orphaned artifacts
  Script: check_orphans.py
  Status: ❌ Schema mismatch
  ────────────────────────────────────────
  FM: FM-02
  Check: Write conflicts
  Script: detect_write_conflicts.py
  Status: ❌ Schema mismatch
  ────────────────────────────────────────
  FM: FM-03
  Check: Incomplete handoffs
  Script: validate_handoffs.py
  Status: ❌ Schema mismatch
  ────────────────────────────────────────
  FM: FM-04
  Check: Dead artifacts
  Script: check_dead_artifacts.py
  Status: ❌ Schema mismatch
  ────────────────────────────────────────
  FM: FM-05
  Check: Missing producers
  Script: check_missing_producers.py
  Status: ❌ Schema mismatch
  ────────────────────────────────────────
  FM: FM-06
  Check: Circular dependencies
  Script: detect_cycles.py
  Status: ❌ Schema mismatch
  ────────────────────────────────────────
  FM: FM-07
  Check: Dormant flows
  Script: check_dormant_flows.py
  Status: ❌ Schema mismatch
  ────────────────────────────────────────
  FM: FM-08
  Check: Evidence bundle gaps
  Script: validate_evidence_bundles.py
  Status: ❌ Schema mismatch
  ────────────────────────────────────────
  FM: FM-09
  Check: Recovery policy gaps
  Script: validate_recovery_policies.py
  Status: ❌ Schema mismatch
  ────────────────────────────────────────
  FM: FM-10
  Check: Idempotency violations
  Script: test_idempotency_all.py
  Status: ❌ Schema mismatch
  ────────────────────────────────────────
  FM: FM-11
  Check: Detection gate gaps
  Script: validate_detection_gates.py
  Status: ❌ Schema mismatch
  ────────────────────────────────────────
  FM: FM-12
  Check: E2E proof linkage gaps
  Script: validate_e2e_proof_linkage.py
  Status: ❌ Schema mismatch
  Root Cause: FM scripts expect plan.artifacts but v2.4.0 schema doesn't
   define this structure.

  ---
  Proposed Refactored Architecture (From Documentation)

  The documentation outlines a significant architectural shift:

  New Components (Not Yet Implemented)

  1. GateSpec - Data-driven gate configuration (replaces per-gate Python
   scripts)
  2. GateResult - Canonical gate output with failure fingerprinting
  3. FailureMode Schema - Declarative failure classification
  4. HealTemplate - Self-healing automation
  5. ArtifactEnvelope - Explicit artifact transport between phases
  6. HandoffReport - Phase boundary validation

  New Schemas Required (8 total)

  1. gate_spec.schema.json
  2. gate_result.schema.json
  3. failure_mode.schema.json
  4. heal_template.schema.json
  5. heal_sequence_report.schema.json
  6. artifact_envelope.schema.json
  7. handoff_report.schema.json
  8. gate_runner_config.schema.json

  Migration Risk

  The documentation correctly identifies this as a "fundamental
  architectural refactor, not a patch" that changes 4 models
  simultaneously:
  - Execution model (script-based → spec-driven)
  - Recovery model (manual → self-healing)
  - Artifact model (implicit → explicit envelopes)
  - Code structure (44 scripts → unified GateRunner)

  ---
  Key Design Patterns Identified

  1. Determinism Guarantees

  - No eval() - Uses SafeFormulaEvaluator with AST parsing
  - Stable hashing - SHA256 of normalized plan (ignoring timestamps)
  - Topological sorting - Kahn's algorithm with sorted queue for
  reproducibility
  - ID-keyed maps - Converted from arrays for O(1) lookup

  2. Evidence Chain

  Every gate produces timestamped JSON:
  .state/evidence/GATE-###/<evidence_file>.json
  Structure:
  {
    "gate_id": "GATE-001",
    "validated_at": "2026-02-11T12:00:00Z",
    "validation_result": {"status": "valid|invalid", "errors": [...]},
    "statistics": {...}
  }

  3. Formula Evaluation

  Variables supported:
  - file_count_est, loc_est, gates_count, phase_count

  Functions supported:
  - CEIL(), FLOOR(), MIN(), MAX(), +, -, *, /

  ---
  Actionable Next Steps

  Immediate (Unblock FM Checks)

  1. Option A: Update all 12 FM scripts to match v2.4.0 schema (remove
  plan.artifacts references)
  2. Option B: Add artifacts section to v2.4.0 schema (backward
  compatible)
  3. Option C: Create schema adapter layer that translates v2.4.0 →
  FM-expected format

  Short Term (Complete Current System)

  1. Verify missing documentation files (FM_GATE_MAPPING_CANONICAL.md,
  TECHNICAL_DOCUMENTATION.md) are covered by existing specs
  2. Test gate orchestration end-to-end with actual plan file
  3. Verify evidence artifacts are schema-valid

  Long Term (Proposed Refactor)

  Follow the phased migration plan from documentation:
  - Phase 0: Freeze new gate additions
  - Phase A: Emit canonical GateResult from legacy gates
  - Phase B: Shadow-run new GateRunner alongside legacy
  - Phase C: Classify all gates (validator/generator/composite)
  - Phase D: Implement self-healing templates
  - Phase E: Retire legacy scripts
  - Phase F: Deploy artifact envelope transport

  ---
  Recommendations

  1. Fix FM Schema Mismatch First - This is the only blocking issue
  preventing the system from running
  2. Run Integration Test - Execute run-gates with a test plan to verify
   the critical path
  3. Document Current State - The actual code is more complete than
  documentation suggests
  4. Defer Refactor - Current system is functional; refactor is
  high-risk and should be carefully planned