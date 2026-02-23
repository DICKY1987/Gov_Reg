 Complete Process Map: Existing Scripts and Their Location

   Based on code analysis, here's the complete mapping of existing scripts to the process flow:

   -------------------------------------------------------------------------------------------------

   Process Architecture (5 Phases)

     ┌─────────────────────────────────────────────────────────────────┐
     │                    ORCHESTRATION LAYER                          │
     │  P_01260207233100000242_NEWPHASEPLANPROCESS_plan_cli.py        │
     │  - Commands: validate, normalize, compile, execute, run-gates  │
     └─────────────────────────────────────────────────────────────────┘
                                   ↓
     ┌─────────────────────────────────────────────────────────────────┐
     │          PHASE 1: PRE-VALIDATION (Setup & Structure)            │
     └─────────────────────────────────────────────────────────────────┘
                                   ↓
     ┌─────────────────────────────────────────────────────────────────┐
     │          PHASE 2: CORE-VALIDATION (Schema & Contracts)          │
     └─────────────────────────────────────────────────────────────────┘
                                   ↓
     ┌─────────────────────────────────────────────────────────────────┐
     │          PHASE 3: AUTOMATION (Index & Diagrams)                 │
     └─────────────────────────────────────────────────────────────────┘
                                   ↓
     ┌─────────────────────────────────────────────────────────────────┐
     │          PHASE 4: WIRING (Artifact Flow & FM Checks)            │
     └─────────────────────────────────────────────────────────────────┘
                                   ↓
     ┌─────────────────────────────────────────────────────────────────┐
     │          PHASE 5: META-VALIDATION (Goal Reconciliation)         │
     └─────────────────────────────────────────────────────────────────┘

   -------------------------------------------------------------------------------------------------

   PHASE 1: PRE-VALIDATION (1 gate)

   ┌──────────┬───────────────────────────────────────────────────┬──────────────────────────────────
   ────────────────────────────────┬────────────────────┐
   │ Gate ID  │ Script                                            │ Purpose
                                   │ Dependencies       │
   ├──────────┼───────────────────────────────────────────────────┼──────────────────────────────────
   ────────────────────────────────┼────────────────────┤
   │ GATE-000 │ P_01260207233100000258_validate_plan_structure.py │ Checks for placeholders
   (TODO/TBD/FIXME), ensures no obfuscation │ None (entry point) │
   └──────────┴───────────────────────────────────────────────────┴──────────────────────────────────
   ────────────────────────────────┴────────────────────┘

   Location in Process: First checkpoint - Plan must have no placeholders before any validation

   -------------------------------------------------------------------------------------------------

   PHASE 2: CORE-VALIDATION (5 gates)

   ┌──────────┬───────────────────────────────────────────────────────┬──────────────────────────────
   ───────────────────────────────────┬──────────────┐
   │ Gate ID  │ Script                                                │ Purpose
                                      │ Dependencies │
   ├──────────┼───────────────────────────────────────────────────────┼──────────────────────────────
   ───────────────────────────────────┼──────────────┤
   │ GATE-001 │ P_01260207233100000263_validate_structure.py          │ JSON Schema validation
   against v3.0.0 spec                      │ GATE-000     │
   ├──────────┼───────────────────────────────────────────────────────┼──────────────────────────────
   ───────────────────────────────────┼──────────────┤
   │ GATE-002 │ P_01260207233100000253_validate_gates.py              │ Validates gate definitions
   (commands, patterns, evidence paths) │ GATE-001     │
   ├──────────┼───────────────────────────────────────────────────────┼──────────────────────────────
   ───────────────────────────────────┼──────────────┤
   │ GATE-003 │ P_01260207233100000262_validate_step_contracts.py     │ Validates step-level
   contracts (inputs, outputs, invariants)    │ GATE-001     │
   ├──────────┼───────────────────────────────────────────────────────┼──────────────────────────────
   ───────────────────────────────────┼──────────────┤
   │ GATE-004 │ P_01260207233100000248_validate_assumptions.py        │ Validates assumptions are
   documented                            │ GATE-001     │
   ├──────────┼───────────────────────────────────────────────────────┼──────────────────────────────
   ───────────────────────────────────┼──────────────┤
   │ GATE-005 │ P_01260207233100000257_validate_planning_artifacts.py │ Validates planning artifacts
   presence                           │ GATE-001     │
   └──────────┴───────────────────────────────────────────────────────┴──────────────────────────────
   ───────────────────────────────────┴──────────────┘

   Location in Process: Core validation layer - Ensures structural integrity and contract
   completeness

   -------------------------------------------------------------------------------------------------

   PHASE 3: AUTOMATION (3 gates)

   ┌──────────┬────────────────────────────────────────────────────────┬─────────────────────────────
   ────────┬────────────────────┐
   │ Gate ID  │ Script                                                 │ Purpose
           │ Dependencies       │
   ├──────────┼────────────────────────────────────────────────────────┼─────────────────────────────
   ────────┼────────────────────┤
   │ GATE-006 │ P_01260207233100000250_validate_automation_spec.py     │ Validates automation
   specifications │ GATE-002, GATE-003 │
   ├──────────┼────────────────────────────────────────────────────────┼─────────────────────────────
   ────────┼────────────────────┤
   │ GATE-007 │ P_01260207233100000226_build_automation_index.py       │ Builds automation index
           │ GATE-006           │
   ├──────────┼────────────────────────────────────────────────────────┼─────────────────────────────
   ────────┼────────────────────┤
   │ GATE-008 │ P_01260207233100000237_generate_automation_diagrams.py │ Generates automation
   diagrams       │ GATE-007           │
   └──────────┴────────────────────────────────────────────────────────┴─────────────────────────────
   ────────┴────────────────────┘

   Location in Process: Automation preparation - Builds execution artifacts and visualizations

   -------------------------------------------------------------------------------------------------

   PHASE 4: WIRING (8 gates + 12 FM checks)

   Main Wiring Gates

   ┌──────────┬─────────────────────────────────────────────────────────────┬────────────────────────
   ───────────────┬────────────────────┐
   │ Gate ID  │ Script                                                      │ Purpose
                  │ Dependencies       │
   ├──────────┼─────────────────────────────────────────────────────────────┼────────────────────────
   ───────────────┼────────────────────┤
   │ GATE-010 │ P_01260207233100000265_validate_wiring_proof.py             │ Validates wiring proof
   structure      │ GATE-002, GATE-003 │
   ├──────────┼─────────────────────────────────────────────────────────────┼────────────────────────
   ───────────────┼────────────────────┤
   │ GATE-011 │ P_01260207233100000247_validate_artifact_registry.py        │ Validates artifact
   registry integrity │ GATE-010           │
   ├──────────┼─────────────────────────────────────────────────────────────┼────────────────────────
   ───────────────┼────────────────────┤
   │ GATE-012 │ wiring/P_01260207233100000273_audit_failure_modes.py        │ Orchestrates all 12 FM
   checks         │ GATE-011           │
   ├──────────┼─────────────────────────────────────────────────────────────┼────────────────────────
   ───────────────┼────────────────────┤
   │ GATE-013 │ wiring/P_01260207233100000283_validate_e2e_proof_linkage.py │ Validates E2E proof
   linkage           │ GATE-012           │
   └──────────┴─────────────────────────────────────────────────────────────┴────────────────────────
   ───────────────┴────────────────────┘

   Failure Mode (FM) Scripts (Called by GATE-012)

   ┌───────┬─────────────────────────────────────────────────────────────┬───────────────────────────
   ───────────────────────────┬───────────────────────┐
   │ FM ID │ Script                                                      │ Purpose
                              │ Exit Code             │
   ├───────┼─────────────────────────────────────────────────────────────┼───────────────────────────
   ───────────────────────────┼───────────────────────┤
   │ FM-01 │ wiring/P_01260207233100000277_check_orphans.py              │ Detect orphaned artifacts
   (produced, never consumed) │ 0=pass, 1=orphans     │
   ├───────┼─────────────────────────────────────────────────────────────┼───────────────────────────
   ───────────────────────────┼───────────────────────┤
   │ FM-02 │ wiring/P_01260207233100000279_detect_write_conflicts.py     │ Detect multiple writers to
    same artifact             │ 0=pass, 1=conflicts   │
   ├───────┼─────────────────────────────────────────────────────────────┼───────────────────────────
   ───────────────────────────┼───────────────────────┤
   │ FM-03 │ wiring/P_01260207233100000285_validate_handoffs.py          │ Validate artifact handoffs
    complete                  │ 0=pass, 1=incomplete  │
   ├───────┼─────────────────────────────────────────────────────────────┼───────────────────────────
   ───────────────────────────┼───────────────────────┤
   │ FM-04 │ wiring/P_01260207233100000274_check_dead_artifacts.py       │ Detect dead artifacts
   (consumed, never produced)     │ 0=pass, 1=dead found  │
   ├───────┼─────────────────────────────────────────────────────────────┼───────────────────────────
   ───────────────────────────┼───────────────────────┤
   │ FM-05 │ wiring/P_01260207233100000276_check_missing_producers.py    │ Check all artifacts have
   producers                   │ 0=pass, 1=missing     │
   ├───────┼─────────────────────────────────────────────────────────────┼───────────────────────────
   ───────────────────────────┼───────────────────────┤
   │ FM-06 │ wiring/P_01260207233100000278_detect_cycles.py              │ Detect circular
   dependencies in phase graph          │ 0=pass, 1=cycle found │
   ├───────┼─────────────────────────────────────────────────────────────┼───────────────────────────
   ───────────────────────────┼───────────────────────┤
   │ FM-07 │ wiring/P_01260207233100000275_check_dormant_flows.py        │ Identify phases without
   validation gates             │ 0=always (warning)    │
   ├───────┼─────────────────────────────────────────────────────────────┼───────────────────────────
   ───────────────────────────┼───────────────────────┤
   │ FM-08 │ wiring/P_01260207233100000284_validate_evidence_bundles.py  │ Validate gates produce
   evidence                      │ 0=pass, 1=gaps        │
   ├───────┼─────────────────────────────────────────────────────────────┼───────────────────────────
   ───────────────────────────┼───────────────────────┤
   │ FM-09 │ wiring/P_01260207233100000286_validate_recovery_policies.py │ Ensure commands have
   retry/rollback                  │ 0=pass, 1=gaps        │
   ├───────┼─────────────────────────────────────────────────────────────┼───────────────────────────
   ───────────────────────────┼───────────────────────┤
   │ FM-10 │ wiring/P_01260207233100000281_test_idempotency_all.py       │ Detect unsafe commands
   marked idempotent             │ 0=pass, 1=violations  │
   ├───────┼─────────────────────────────────────────────────────────────┼───────────────────────────
   ───────────────────────────┼───────────────────────┤
   │ FM-11 │ wiring/P_01260207233100000282_validate_detection_gates.py   │ Ensure phases have
   validation gates                  │ 0=always (warning)    │
   ├───────┼─────────────────────────────────────────────────────────────┼───────────────────────────
   ───────────────────────────┼───────────────────────┤
   │ FM-12 │ wiring/P_01260207233100000283_validate_e2e_proof_linkage.py │ Validate gates have
   commands + success patterns      │ 0=pass, 1=gaps        │
   └───────┴─────────────────────────────────────────────────────────────┴───────────────────────────
   ───────────────────────────┴───────────────────────┘

   Additional Wiring Validation Gates

   ┌──────────┬──────────────────────────────────────────────────────────────┬───────────────────────
   ──────────────────────────────────┬──────────────┐
   │ Gate ID  │ Script                                                       │ Purpose
                                     │ Dependencies │
   ├──────────┼──────────────────────────────────────────────────────────────┼───────────────────────
   ──────────────────────────────────┼──────────────┤
   │ GATE-014 │ P_01260207233100000246_validate_artifact_closure.py          │ Subsumes
   FM-01,02,04,05 - Validates all artifacts close │ GATE-011     │
   ├──────────┼──────────────────────────────────────────────────────────────┼───────────────────────
   ──────────────────────────────────┼──────────────┤
   │ GATE-015 │ P_01260207233100000259_validate_rollback_completeness.py     │ Subsumes FM-09 -
   Validates rollback procedures          │ GATE-003     │
   ├──────────┼──────────────────────────────────────────────────────────────┼───────────────────────
   ──────────────────────────────────┼──────────────┤
   │ GATE-016 │ P_01260207233100000264_validate_verification_completeness.py │ Subsumes FM-08 -
   Validates verification methods         │ GATE-003     │
   ├──────────┼──────────────────────────────────────────────────────────────┼───────────────────────
   ──────────────────────────────────┼──────────────┤
   │ GATE-017 │ P_01260207233100000260_validate_single_source_of_truth.py    │ Validates SSOT
   integrity                                │ GATE-001     │
   └──────────┴──────────────────────────────────────────────────────────────┴───────────────────────
   ──────────────────────────────────┴──────────────┘

   Location in Process: Critical safety layer - Ensures artifact flow is complete, safe, and
   traceable

   -------------------------------------------------------------------------------------------------

   PHASE 5: META-VALIDATION (2 gates)

   ┌──────────┬────────────────────────────────────────────────────────┬─────────────────────────────
   ──────────────────────┬──────────────────────────────────┐
   │ Gate ID  │ Script                                                 │ Purpose
                         │ Dependencies                     │
   ├──────────┼────────────────────────────────────────────────────────┼─────────────────────────────
   ──────────────────────┼──────────────────────────────────┤
   │ GATE-998 │ P_01260207233100000249_validate_automation_audit.py    │ Validates automation audit
   trail                  │ GATE-008                         │
   ├──────────┼────────────────────────────────────────────────────────┼─────────────────────────────
   ──────────────────────┼──────────────────────────────────┤
   │ GATE-999 │ P_01260207233100000254_validate_goal_reconciliation.py │ Final gate - Reconciles
   goals with implementation │ GATE-002,003,004,014,015,016,017 │
   └──────────┴────────────────────────────────────────────────────────┴─────────────────────────────
   ──────────────────────┴──────────────────────────────────┘

   Location in Process: Final validation - Confirms plan achieves stated goals

   -------------------------------------------------------------------------------------------------

   OPTIONAL GATES (5 validation checks)

   ┌────────────────────┬───────────────────────────────────────────────────────┬────────────────────
   ──────────────────┬──────────────┐
   │ Gate ID            │ Script                                                │ Purpose
                     │ Dependencies │
   ├────────────────────┼───────────────────────────────────────────────────────┼────────────────────
   ──────────────────┼──────────────┤
   │ VAL-FILE-MANIFEST  │ P_01260207233100000252_validate_file_manifest.py      │ Validates file
   manifest completeness │ GATE-001     │
   ├────────────────────┼───────────────────────────────────────────────────────┼────────────────────
   ──────────────────┼──────────────┤
   │ VAL-CI-COMPAT      │ P_01260207233100000251_validate_ci_compatibility.py   │ Validates CI/CD
   compatibility        │ GATE-001     │
   ├────────────────────┼───────────────────────────────────────────────────────┼────────────────────
   ──────────────────┼──────────────┤
   │ VAL-GROUND-TRUTH   │ P_01260207233100000255_validate_ground_truth.py       │ Validates ground
   truth levels        │ GATE-001     │
   ├────────────────────┼───────────────────────────────────────────────────────┼────────────────────
   ──────────────────┼──────────────┤
   │ VAL-METRICS        │ P_01260207233100000256_validate_metrics.py            │ Validates metrics
   collection         │ GATE-001     │
   ├────────────────────┼───────────────────────────────────────────────────────┼────────────────────
   ──────────────────┼──────────────┤
   │ VAL-SPINE-COVERAGE │ P_01260207233100000261_validate_spine_coverage_map.py │ Validates spine
   coverage             │ GATE-001     │
   └────────────────────┴───────────────────────────────────────────────────────┴────────────────────
   ──────────────────┴──────────────┘

   Location in Process: Optional quality checks - Can be skipped with --only-required flag

   -------------------------------------------------------------------------------------------------

   SUPPORTING SCRIPTS (Not gates, but process utilities)

   Orchestration & Testing

   ┌─────────────────────────────────────────────────────┬──────────────────────────────────────────┬
   ─────────────────────┐
   │ Script                                              │ Purpose                                  │
    Location in Process │
   ├─────────────────────────────────────────────────────┼──────────────────────────────────────────┼
   ─────────────────────┤
   │ P_01260207233100000245_test_orchestration.py        │ Integration tests for gate orchestration │
    Testing framework   │
   ├─────────────────────────────────────────────────────┼──────────────────────────────────────────┼
   ─────────────────────┤
   │ wiring/P_01260207233100000280_run_all_e2e_proofs.py │ Runs all end-to-end proofs               │
    Called by GATE-013  │
   └─────────────────────────────────────────────────────┴──────────────────────────────────────────┴
   ─────────────────────┘

   Code Generation & Analysis

   ┌─────────────────────────────────────────────────────────────────────────────────────────────────
   ─────────────────┬───────────────────────────────────┬─────────────────────┐
   │ Script
                    │ Purpose                           │ Location in Process │
   ├─────────────────────────────────────────────────────────────────────────────────────────────────
   ─────────────────┼───────────────────────────────────┼─────────────────────┤
   │ P_01260207233100000238_generate_dag.py
                    │ Generates phase DAG visualization │ Automation phase    │
   ├─────────────────────────────────────────────────────────────────────────────────────────────────
   ─────────────────┼───────────────────────────────────┼─────────────────────┤
   │ P_01260207233100000240_generate_metrics_report.py
                    │ Generates metrics from evidence   │ Post-execution      │
   ├─────────────────────────────────────────────────────────────────────────────────────────────────
   ─────────────────┼───────────────────────────────────┼─────────────────────┤
   │ P_01260207233100000231_DOC-CORE-CONVERTERS-CCIS-TO-PHASE-PLAN-388__ccis_to_phase_plan.py
                    │ Converts CCIS to phase plan       │ Plan generation     │
   ├─────────────────────────────────────────────────────────────────────────────────────────────────
   ─────────────────┼───────────────────────────────────┼─────────────────────┤
   │ P_01260207233100000232_DOC-CORE-PHASE-1-CONVERTER-001__phase_plan_converter.py
                    │ Phase plan converter              │ Plan generation     │
   ├─────────────────────────────────────────────────────────────────────────────────────────────────
   ─────────────────┼───────────────────────────────────┼─────────────────────┤
   │ P_01260207233100000233_DOC-CORE-PHASE-PLAN-TO-WORKSTREAM-CONVERTER-PY-001__phase_plan_to_workstr
   eam_converter.py │ Converts plan to workstreams      │ Execution prep      │
   └─────────────────────────────────────────────────────────────────────────────────────────────────
   ─────────────────┴───────────────────────────────────┴─────────────────────┘

   Security & Resource Checks

   ┌──────────────────────────────────────────────────┬─────────────────────────────────┬────────────
   ──────────┐
   │ Script                                           │ Purpose                         │ Location in
    Process  │
   ├──────────────────────────────────────────────────┼─────────────────────────────────┼────────────
   ──────────┤
   │ P_01260207233100000230_check_secrets.py          │ Detects hardcoded secrets       │
   Pre-execution safety │
   ├──────────────────────────────────────────────────┼─────────────────────────────────┼────────────
   ──────────┤
   │ P_01260207233100000228_check_permissions.py      │ Validates file permissions      │
   Pre-execution safety │
   ├──────────────────────────────────────────────────┼─────────────────────────────────┼────────────
   ──────────┤
   │ P_01260207233100000229_check_resources.py        │ Checks resource availability    │
   Pre-execution safety │
   ├──────────────────────────────────────────────────┼─────────────────────────────────┼────────────
   ──────────┤
   │ P_01260207233100000227_check_file_scope.py       │ Validates file scope boundaries │ Execution
   safety     │
   ├──────────────────────────────────────────────────┼─────────────────────────────────┼────────────
   ──────────┤
   │ P_01260207233100000222_analyze_file_conflicts.py │ Analyzes file write conflicts   │ Conflict
   resolution  │
   └──────────────────────────────────────────────────┴─────────────────────────────────┴────────────
   ──────────┘

   Utilities

   ┌───────────────────────────────────────────────────┬───────────────────────────────────┬─────────
   ────────────┐
   │ Script                                            │ Purpose                           │ Location
    in Process │
   ├───────────────────────────────────────────────────┼───────────────────────────────────┼─────────
   ────────────┤
   │ P_01260207233100000243_standardize_argparse.py    │ Standardizes CLI argument parsing │
   Development utility │
   ├───────────────────────────────────────────────────┼───────────────────────────────────┼─────────
   ────────────┤
   │ P_01260207233100000224_apply_patch.py             │ Applies patches to plans          │ Plan
   modification   │
   ├───────────────────────────────────────────────────┼───────────────────────────────────┼─────────
   ────────────┤
   │ P_01260207233100000235_evaluate_criteria.py       │ Evaluates success criteria        │
   Post-execution      │
   ├───────────────────────────────────────────────────┼───────────────────────────────────┼─────────
   ────────────┤
   │ P_01260207233100000225_audit_metric_thresholds.py │ Audits metric thresholds          │ Quality
   assurance   │
   └───────────────────────────────────────────────────┴───────────────────────────────────┴─────────
   ────────────┘

   -------------------------------------------------------------------------------------------------

   Process Execution Flow

     1. USER COMMAND:
        python P_01260207233100000242_NEWPHASEPLANPROCESS_plan_cli.py run-gates --plan-file plan.json

     2. CLI LOADS:
        scripts/01260207233100000678_gate_dependencies.json

     3. TOPOLOGICAL SORT:
        Determines execution order based on depends_on relationships

     4. SEQUENTIAL EXECUTION:
        For each gate in sorted order:
          ├─ Run gate script with subprocess
          ├─ Check exit code (0=pass, 1=fail)
          ├─ Save evidence to .state/evidence/GATE-XXX/
          ├─ If fail and fail_fast: STOP
          └─ If pass: Continue to next gate

     5. FM CHECKS (at GATE-012):
        P_01260207233100000273_audit_failure_modes.py orchestrates:
          ├─ FM-01 through FM-12 scripts
          ├─ Collects all results
          ├─ Generates aggregated evidence
          └─ Returns 0 only if ALL pass

     6. EVIDENCE COLLECTION:
        All gates write to:
        .state/evidence/GATE-XXX/[gate-specific].json

     7. FINAL REPORT:
        ✅ Passed: X gates
        ❌ Failed: Y gates
        ⏭️ Skipped: Z gates (dependencies failed)

   -------------------------------------------------------------------------------------------------

   Key Architecture Insights

     - No Self-Healing: Current system stops on failure; proposed system would classify → heal →
   retry
     - Per-Gate Scripts: Each gate has its own validator (44 scripts total); proposed system would
   use 1 shared runner
     - GATE-012 as Aggregator: Acts as meta-gate orchestrating 12 FM checks
     - Dependency Enforcement: gate_dependencies.json defines strict execution order
     - Evidence-First: Every gate produces JSON evidence in .state/evidence/
     - Binary Outcomes: All gates return 0 (pass) or 1 (fail) - no partial credit

   The proposed self-healing architecture would add GateRunner, SelfHealOrchestrator, and
   FailureClassifier layers between the CLI and these individual gate scripts.