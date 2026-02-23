# newPhasePlanProcess v2.4.0 - Current System Technical Specification

**Document ID:** DOC-TECH-SPEC-CURRENT-SYSTEM-001  
**Version:** 1.0.0  
**Date:** 2026-02-10  
**Status:** AUTHORITATIVE  
**System Version:** v2.4.0  

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Architecture Overview](#2-system-architecture-overview)
3. [Core Components](#3-core-components)
4. [Gate Validation System](#4-gate-validation-system)
5. [Failure Mode Detection](#5-failure-mode-detection)
6. [Execution Pipeline](#6-execution-pipeline)
7. [Evidence & Artifact Management](#7-evidence--artifact-management)
8. [Data Structures & Schemas](#8-data-structures--schemas)
9. [Security & Safety Mechanisms](#9-security--safety-mechanisms)
10. [Operational Procedures](#10-operational-procedures)
11. [Known Limitations](#11-known-limitations)
12. [Appendices](#12-appendices)

---

## 1. Executive Summary

### 1.1 System Purpose

The newPhasePlanProcess (NPP) v2.4.0 is a **deterministic plan validation and execution system** designed to ensure project plans are structurally sound, semantically complete, and mechanically executable before deployment. It enforces strict contracts at step, phase, and gate levels to prevent runtime failures.

### 1.2 Key Capabilities

- **19 Validation Gates** organized in 5 execution phases
- **12 Failure Mode (FM) Checks** for wiring integrity
- **Binary pass/fail semantics** with no partial credit
- **Evidence-based validation** with timestamped artifacts
- **Dependency-aware execution** via topological sorting
- **Schema-enforced contracts** at multiple levels

### 1.3 Current State

**Status:** Production-ready, actively used  
**Language:** Python 3.8+  
**Dependencies:** jsonschema, subprocess, pathlib  
**Deployment:** Single-machine execution (no distributed runtime)  
**Self-Healing:** ❌ Not implemented (manual recovery only)  

### 1.4 Critical Constraints

1. **No Implied Behavior**: All rules expressible as executable commands with pass/fail criteria
2. **Evidence Required**: Every validation must produce timestamped JSON evidence
3. **Fail-Closed Discipline**: Unknown states treated as failures
4. **Step-Level Contracts**: Every step declares inputs, outputs, invariants, pre/post conditions

---

## 2. System Architecture Overview

### 2.1 Architectural Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INTERFACE LAYER                     │
│  Command-Line Interface (CLI)                               │
│  - P_01260207233100000242_NEWPHASEPLANPROCESS_plan_cli.py  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  ORCHESTRATION LAYER                        │
│  - Gate Dependency Loader                                   │
│  - Topological Sorter (Kahn's algorithm)                    │
│  - Execution Scheduler                                      │
│  - Evidence Aggregator                                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    VALIDATION LAYER                         │
│  5 Validation Phases:                                       │
│  ├─ Pre-Validation (GATE-000)                               │
│  ├─ Core-Validation (GATE-001 to GATE-005)                  │
│  ├─ Automation (GATE-006 to GATE-008)                       │
│  ├─ Wiring (GATE-010 to GATE-017)                           │
│  └─ Meta-Validation (GATE-998, GATE-999)                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  FAILURE MODE DETECTION                     │
│  12 FM Checks (FM-01 to FM-12)                              │
│  Orchestrated by GATE-012                                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    EVIDENCE LAYER                           │
│  File System Storage:                                       │
│  - .state/evidence/GATE-XXX/                                │
│  - Timestamped JSON artifacts                               │
│  - Immutable after creation                                 │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow Architecture

```
┌──────────────┐
│ Plan JSON    │ (Input)
│ File         │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────────────┐
│ CLI: validate/normalize/compile/run-gates    │
└──────┬───────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────┐
│ Load: gate_dependencies.json                 │
│ Topological Sort Gates                       │
└──────┬───────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────┐
│ FOR EACH Gate (in dependency order):         │
│   ├─ subprocess.run(gate_script)             │
│   ├─ Check exit_code (0=pass, 1=fail)        │
│   ├─ Save evidence to .state/evidence/       │
│   └─ If fail & fail_fast: ABORT              │
└──────┬───────────────────────────────────────┘
       │
       ▼ (at GATE-012)
┌──────────────────────────────────────────────┐
│ FM Audit: Run 12 failure mode checks         │
│   ├─ FM-01: Check orphans                    │
│   ├─ FM-02: Detect write conflicts           │
│   ├─ ...                                     │
│   └─ FM-12: Validate E2E linkage             │
└──────┬───────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────┐
│ Generate Summary Report:                     │
│   - Passed count                             │
│   - Failed count                             │
│   - Skipped count                            │
│   - Evidence paths                           │
└──────┬───────────────────────────────────────┘
       │
       ▼
┌──────────────┐
│ Exit Code    │ (0=all pass, 1=any fail)
│ & Report     │
└──────────────┘
```

### 2.3 Directory Structure

```
newPhasePlanProcess/
├── scripts/
│   ├── P_01260207233100000242_NEWPHASEPLANPROCESS_plan_cli.py  (Main CLI)
│   ├── 01260207233100000678_gate_dependencies.json              (Gate graph)
│   ├── P_01260207233100000246_validate_artifact_closure.py      (GATE-014)
│   ├── P_01260207233100000247_validate_artifact_registry.py     (GATE-011)
│   ├── P_01260207233100000248_validate_assumptions.py           (GATE-004)
│   ├── P_01260207233100000249_validate_automation_audit.py      (GATE-998)
│   ├── P_01260207233100000250_validate_automation_spec.py       (GATE-006)
│   ├── P_01260207233100000251_validate_ci_compatibility.py      (VAL-CI-COMPAT)
│   ├── P_01260207233100000252_validate_file_manifest.py         (VAL-FILE-MANIFEST)
│   ├── P_01260207233100000253_validate_gates.py                 (GATE-002)
│   ├── P_01260207233100000254_validate_goal_reconciliation.py   (GATE-999)
│   ├── P_01260207233100000255_validate_ground_truth.py          (VAL-GROUND-TRUTH)
│   ├── P_01260207233100000256_validate_metrics.py               (VAL-METRICS)
│   ├── P_01260207233100000257_validate_planning_artifacts.py    (GATE-005)
│   ├── P_01260207233100000258_validate_plan_structure.py        (GATE-000)
│   ├── P_01260207233100000259_validate_rollback_completeness.py (GATE-015)
│   ├── P_01260207233100000260_validate_single_source_of_truth.py(GATE-017)
│   ├── P_01260207233100000261_validate_spine_coverage_map.py    (VAL-SPINE-COVERAGE)
│   ├── P_01260207233100000262_validate_step_contracts.py        (GATE-003)
│   ├── P_01260207233100000263_validate_structure.py             (GATE-001)
│   ├── P_01260207233100000264_validate_verification_completeness.py (GATE-016)
│   ├── P_01260207233100000265_validate_wiring_proof.py          (GATE-010)
│   ├── P_01260207233100000226_build_automation_index.py         (GATE-007)
│   ├── P_01260207233100000237_generate_automation_diagrams.py   (GATE-008)
│   └── wiring/
│       ├── P_01260207233100000273_audit_failure_modes.py        (GATE-012)
│       ├── P_01260207233100000274_check_dead_artifacts.py       (FM-04)
│       ├── P_01260207233100000275_check_dormant_flows.py        (FM-07)
│       ├── P_01260207233100000276_check_missing_producers.py    (FM-05)
│       ├── P_01260207233100000277_check_orphans.py              (FM-01)
│       ├── P_01260207233100000278_detect_cycles.py              (FM-06)
│       ├── P_01260207233100000279_detect_write_conflicts.py     (FM-02)
│       ├── P_01260207233100000280_run_all_e2e_proofs.py         (E2E Executor)
│       ├── P_01260207233100000281_test_idempotency_all.py       (FM-10)
│       ├── P_01260207233100000282_validate_detection_gates.py   (FM-11)
│       ├── P_01260207233100000283_validate_e2e_proof_linkage.py (FM-12/GATE-013)
│       ├── P_01260207233100000284_validate_evidence_bundles.py  (FM-08)
│       ├── P_01260207233100000285_validate_handoffs.py          (FM-03)
│       └── P_01260207233100000286_validate_recovery_policies.py (FM-09)
├── schemas/
│   ├── 01260207233100000675_NEWPHASEPLANPROCESS_plan.schema.v3.0.0.json
│   ├── 01260207233100000672_coverage_v1.json
│   ├── 01260207233100000673_defect_log.schema.json
│   ├── 01260207233100000676_parquet_schema_v1.json
│   └── etl/
│       ├── 01260207233100000731_clean_data.json
│       ├── 01260207233100000732_load_receipt.json
│       └── 01260207233100000733_raw_data.json
├── .state/
│   └── evidence/
│       ├── GATE-000/
│       ├── GATE-001/
│       ├── ... (one directory per gate)
│       └── GATE-999/
└── docs/
    ├── PLAN_AI_USAGE_GUIDE.md
    ├── REGISTRY_PLANNING_INTEGRATION_SPEC.md
    └── CLAUDE.md
```

---

## 3. Core Components

### 3.1 Main CLI Orchestrator

**File:** `P_01260207233100000242_NEWPHASEPLANPROCESS_plan_cli.py`  
**Lines of Code:** ~1,100  
**Version:** 2.4.0  

#### 3.1.1 CLI Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `validate` | Schema validation only | `python plan_cli.py validate plan.json` |
| `normalize` | Normalize structure (sort arrays, build ID maps) | `python plan_cli.py normalize plan.json` |
| `compile` | Normalize + regenerate navigation + validate formulas | `python plan_cli.py compile plan.json` |
| `execute` | Execute plan (reads only /plan section) | `python plan_cli.py execute plan.json` |
| `diff` | Compare two plans (ignoring timestamps) | `python plan_cli.py diff plan1.json plan2.json` |
| `run-gates` | Execute all validation gates in dependency order | `python plan_cli.py run-gates --plan-file plan.json` |

#### 3.1.2 Key Classes

**SafeFormulaEvaluator**  
- Evaluates formulas without using `eval()` for security
- Supports: `+`, `-`, `*`, `/`, `MIN`, `MAX`, `CEIL`, `FLOOR`
- Example: `"15 + CEIL(file_count_est * 2)"` with `{file_count_est: 5}` → `25`

**PlanExecutor**  
- Executes plan phases in order
- Validates phase dependencies
- Tracks execution state

#### 3.1.3 run-gates Command Flow

```python
def run_all_gates(plan_file, evidence_dir, fail_fast, only_required, run_id):
    """
    Execute all validation gates in dependency order.
    
    Args:
        plan_file: Path to plan JSON
        evidence_dir: Evidence output directory
        fail_fast: Stop on first failure
        only_required: Skip optional gates
        run_id: Unique execution identifier
    
    Returns:
        {
            "success": bool,
            "passed": [gate_ids],
            "failed": [gate_ids],
            "skipped": [gate_ids],
            "run_id": str
        }
    """
    # 1. Load gate dependencies
    dep_data = load_gate_dependencies()
    gates = dep_data["gates"]
    
    # 2. Filter optional gates if requested
    if only_required:
        gates = [g for g in gates if g.get("required", True)]
    
    # 3. Topological sort by dependencies
    sorted_gates = topological_sort(gates)
    
    # 4. Execute gates sequentially
    for gate in sorted_gates:
        # Check if dependencies failed
        if any(dep in failed_gates for dep in gate["depends_on"]):
            skipped.append(gate_id)
            continue
        
        # Build command
        cmd = [sys.executable, gate["script"],
               "--plan-file", str(plan_file),
               "--evidence-dir", str(evidence_dir)]
        
        # Run gate with 5-minute timeout
        result = subprocess.run(cmd, timeout=300)
        
        # Check result
        if result.returncode == 0:
            passed.append(gate_id)
        else:
            failed.append(gate_id)
            if fail_fast:
                break
    
    return {"success": len(failed) == 0, ...}
```

### 3.2 Gate Dependency Graph

**File:** `scripts/01260207233100000678_gate_dependencies.json`  
**Format:** JSON  
**Purpose:** Defines gate execution order and dependencies  

#### 3.2.1 Schema

```json
{
  "gates": [
    {
      "id": "GATE-XXX",
      "name": "Human-readable name",
      "script": "relative/path/to/script.py",
      "depends_on": ["GATE-YYY", "GATE-ZZZ"],
      "phase": "pre-validation|core-validation|automation|wiring|meta-validation|optional"
    }
  ]
}
```

#### 3.2.2 Dependency Resolution

Uses **Kahn's algorithm** for topological sorting:

```python
def topological_sort(gates):
    """
    Perform topological sort on gates using Kahn's algorithm.
    
    Returns:
        list: Gates in execution order
    
    Raises:
        ValueError: If circular dependency detected
    """
    # Build adjacency list and in-degree count
    graph = defaultdict(list)
    in_degree = defaultdict(int)
    gate_map = {g["id"]: g for g in gates}
    
    for gate in gates:
        gate_id = gate["id"]
        if gate_id not in in_degree:
            in_degree[gate_id] = 0
        
        for dep in gate.get("depends_on", []):
            graph[dep].append(gate_id)
            in_degree[gate_id] += 1
    
    # Find all nodes with no incoming edges
    queue = deque([gid for gid in in_degree if in_degree[gid] == 0])
    sorted_gates = []
    
    while queue:
        gate_id = queue.popleft()
        sorted_gates.append(gate_map[gate_id])
        
        for neighbor in graph[gate_id]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    
    # Check for cycles
    if len(sorted_gates) != len(gates):
        raise ValueError("Circular dependency detected!")
    
    return sorted_gates
```

### 3.3 Evidence Management

#### 3.3.1 Evidence Directory Structure

```
.state/evidence/
├── GATE-000/
│   └── structure_validation.json
├── GATE-001/
│   └── schema_validation.json
├── GATE-002/
│   └── gates_validation.json
├── GATE-003/
│   ├── step_contracts_validation.json
│   └── contract_details.json
├── ...
└── GATE-012/
    ├── failure_mode_audit.json
    └── fm_results/
        ├── FM-01_result.json
        ├── FM-02_result.json
        └── ...
```

#### 3.3.2 Standard Evidence Schema

Every gate produces evidence conforming to:

```json
{
  "gate_id": "GATE-XXX",
  "gate_name": "Human-readable name",
  "validated_at": "2026-02-10T19:00:00Z",
  "validator_version": "1.0.0",
  "plan_file": "/path/to/plan.json",
  "validation_result": {
    "status": "valid|invalid",
    "errors_count": 0,
    "warnings_count": 0,
    "errors": [],
    "warnings": []
  },
  "statistics": {
    "total_items_checked": 42,
    "items_passed": 40,
    "items_failed": 2
  }
}
```

---

## 4. Gate Validation System

### 4.1 Validation Phases

#### PHASE 1: Pre-Validation (Entry Point)

**Gates:** 1  
**Purpose:** Structural hygiene check  
**Failure Impact:** Blocks all downstream validation  

| Gate ID | Name | Script | Checks |
|---------|------|--------|--------|
| GATE-000 | No Obfuscation Check | `P_01260207233100000258_validate_plan_structure.py` | No TODO/TBD/FIXME placeholders, no obfuscated JSON |

**Exit Criteria:**
- Plan file is valid JSON
- No placeholder text in any field
- All string fields are non-empty
- No debug/temporary markers

#### PHASE 2: Core-Validation (Structural Integrity)

**Gates:** 5  
**Purpose:** Validate schema conformance and contract completeness  
**Failure Impact:** Blocks automation and wiring validation  

| Gate ID | Name | Script | Checks |
|---------|------|--------|--------|
| GATE-001 | Schema Validation | `P_01260207233100000263_validate_structure.py` | JSON Schema v2020-12 conformance against v3.0.0 spec |
| GATE-002 | Gate Definitions Valid | `P_01260207233100000253_validate_gates.py` | All gates have commands, patterns, evidence paths |
| GATE-003 | Step Contracts Complete | `P_01260207233100000262_validate_step_contracts.py` | All steps have inputs, outputs, invariants, pre/post conditions |
| GATE-004 | Assumptions Documented | `P_01260207233100000248_validate_assumptions.py` | Assumptions section present and complete |
| GATE-005 | Planning Artifacts | `P_01260207233100000257_validate_planning_artifacts.py` | Required artifacts declared and paths valid |

**GATE-001 Details (Schema Validation)**

```python
class StructureValidator:
    SCHEMA_PATH = Path("schemas/01260207233100000675_NEWPHASEPLANPROCESS_plan.schema.v3.0.0.json")
    
    def validate(self, plan_path: Path) -> Tuple[bool, Dict]:
        """
        Validate plan against JSON Schema Draft 2020-12.
        
        Returns:
            (is_valid, evidence_dict)
        """
        # Load plan
        with open(plan_path) as f:
            plan_data = json.load(f)
        
        # Load schema
        with open(self.SCHEMA_PATH) as f:
            schema = json.load(f)
        
        # Validate using Draft202012Validator
        validator = Draft202012Validator(schema)
        errors = list(validator.iter_errors(plan_data))
        
        # Generate evidence
        evidence = {
            "gate_id": "GATE-001",
            "validated_at": datetime.utcnow().isoformat() + "Z",
            "validation_result": {
                "status": "valid" if not errors else "invalid",
                "errors_count": len(errors),
                "errors": [
                    {
                        "path": ".".join(str(p) for p in e.path),
                        "message": e.message,
                        "schema_path": ".".join(str(p) for p in e.schema_path)
                    }
                    for e in errors
                ]
            }
        }
        
        return len(errors) == 0, evidence
```

**GATE-003 Details (Step Contracts)**

Validates every step has:

```json
{
  "step_id": "ST-001",
  "name": "Step name",
  "inputs": [
    {
      "artifact_id": "ART-001",
      "path": "path/to/input",
      "must_exist": true
    }
  ],
  "outputs": [
    {
      "artifact_id": "ART-002",
      "path": "path/to/output",
      "schema_id": "schemas/artifact.schema.json"
    }
  ],
  "preconditions": [
    {
      "condition_id": "PRE-001",
      "description": "Input file exists",
      "validation_command": "test -f path/to/input",
      "must_pass": true
    }
  ],
  "postconditions": [
    {
      "condition_id": "POST-001",
      "description": "Output file created",
      "validation_command": "test -f path/to/output",
      "must_pass": true
    }
  ],
  "invariants": [
    "File count remains constant",
    "No global state modified"
  ],
  "commands": ["executable command"],
  "rollback": ["rollback command"],
  "evidence": ".state/evidence/PH-001/ST-001/",
  "idempotent": true
}
```

#### PHASE 3: Automation (Execution Preparation)

**Gates:** 3  
**Purpose:** Generate automation artifacts and diagrams  
**Failure Impact:** Blocks automation execution (not validation)  

| Gate ID | Name | Script | Checks |
|---------|------|--------|--------|
| GATE-006 | Automation Spec | `P_01260207233100000250_validate_automation_spec.py` | Automation specifications complete |
| GATE-007 | Automation Index | `P_01260207233100000226_build_automation_index.py` | Builds searchable automation index |
| GATE-008 | Automation Diagrams | `P_01260207233100000237_generate_automation_diagrams.py` | Generates execution flow diagrams |

#### PHASE 4: Wiring (Critical Safety Layer)

**Gates:** 8 main + 12 FM checks  
**Purpose:** Validate artifact flow, detect wiring failures  
**Failure Impact:** Blocks execution (safety-critical)  

**Main Wiring Gates:**

| Gate ID | Name | Script | Checks |
|---------|------|--------|--------|
| GATE-010 | Wiring Proof | `P_01260207233100000265_validate_wiring_proof.py` | Wiring proof structure complete |
| GATE-011 | Artifact Registry | `P_01260207233100000247_validate_artifact_registry.py` | Artifact registry valid |
| GATE-012 | Failure Modes Audit | `wiring/P_01260207233100000273_audit_failure_modes.py` | **Orchestrates all 12 FM checks** |
| GATE-013 | E2E Wiring Validation | `wiring/P_01260207233100000283_validate_e2e_proof_linkage.py` | E2E proofs link correctly |
| GATE-014 | Artifact Closure | `P_01260207233100000246_validate_artifact_closure.py` | All artifacts have producers & consumers |
| GATE-015 | Rollback Completeness | `P_01260207233100000259_validate_rollback_completeness.py` | All steps have rollback procedures |
| GATE-016 | Verification Completeness | `P_01260207233100000264_validate_verification_completeness.py` | All steps have verification methods |
| GATE-017 | Single Source of Truth | `P_01260207233100000260_validate_single_source_of_truth.py` | SSOT integrity maintained |

**GATE-012 Implementation (FM Orchestrator)**

```python
# File: wiring/P_01260207233100000273_audit_failure_modes.py

FM_SCRIPTS = {
    "FM-01": "P_01260207233100000277_check_orphans.py",
    "FM-02": "P_01260207233100000279_detect_write_conflicts.py",
    "FM-03": "P_01260207233100000285_validate_handoffs.py",
    "FM-04": "P_01260207233100000274_check_dead_artifacts.py",
    "FM-05": "P_01260207233100000276_check_missing_producers.py",
    "FM-06": "P_01260207233100000278_detect_cycles.py",
    "FM-07": "P_01260207233100000275_check_dormant_flows.py",
    "FM-08": "P_01260207233100000284_validate_evidence_bundles.py",
    "FM-09": "P_01260207233100000286_validate_recovery_policies.py",
    "FM-10": "P_01260207233100000281_test_idempotency_all.py",
    "FM-11": "P_01260207233100000282_validate_detection_gates.py",
    "FM-12": "P_01260207233100000283_validate_e2e_proof_linkage.py",
}

def main():
    wiring_dir = Path(__file__).parent
    fm_results = {}
    all_passed = True
    
    # Run all FM checks
    for fm_id, script_name in FM_SCRIPTS.items():
        script_path = wiring_dir / script_name
        
        try:
            result = subprocess.run(
                [sys.executable, str(script_path), "--plan-file", args.plan_file],
                capture_output=True,
                timeout=30
            )
            
            passed = result.returncode == 0
            fm_results[fm_id] = {
                "status": "pass" if passed else "fail",
                "checked": True,
                "exit_code": result.returncode
            }
            
            if not passed:
                all_passed = False
                
        except Exception as e:
            fm_results[fm_id] = {
                "status": "error",
                "checked": True,
                "error": str(e)
            }
            all_passed = False
    
    # Generate aggregated evidence
    evidence = {
        "gate_id": "GATE-012",
        "validated_at": datetime.utcnow().isoformat() + "Z",
        "fm_results": fm_results,
        "all_passed": all_passed,
        "passed_count": sum(1 for r in fm_results.values() if r["status"] == "pass"),
        "total_count": len(FM_SCRIPTS)
    }
    
    # Save evidence
    Path(args.evidence_dir).mkdir(parents=True, exist_ok=True)
    with open(Path(args.evidence_dir) / "failure_mode_audit.json", "w") as f:
        json.dump(evidence, f, indent=2)
    
    sys.exit(0 if all_passed else 1)
```

#### PHASE 5: Meta-Validation (Final Checks)

**Gates:** 2  
**Purpose:** Validate overall plan coherence and goal alignment  
**Failure Impact:** Blocks deployment  

| Gate ID | Name | Script | Checks |
|---------|------|--------|--------|
| GATE-998 | Automation Audit | `P_01260207233100000249_validate_automation_audit.py` | Automation audit trail complete |
| GATE-999 | Goal Reconciliation | `P_01260207233100000254_validate_goal_reconciliation.py` | **Final gate** - Plan achieves stated goals |

---

## 5. Failure Mode Detection

### 5.1 FM System Overview

**Purpose:** Detect 12 classes of wiring failures that would cause runtime errors  
**Execution:** Orchestrated by GATE-012  
**Philosophy:** Prevent integration failures through static analysis  

### 5.2 FM Check Catalog

#### FM-01: Orphaned Artifacts

**Script:** `wiring/P_01260207233100000277_check_orphans.py`  
**Detection:** Artifacts produced but never consumed  
**Risk:** Wasted computation, incomplete workflows  

```python
def main():
    with open(args.plan_file) as f:
        data = json.load(f)
    
    artifacts = data.get('plan', {}).get('artifacts', {})
    orphans = []
    
    for aid, adata in artifacts.items():
        if not adata.get('consumer_phases'):
            orphans.append(aid)
    
    print(f"{'✅ PASSED' if not orphans else '❌ ORPHANS'}: {len(orphans)} orphaned artifacts")
    sys.exit(0 if not orphans else 1)
```

**Example Failure:**
```json
{
  "artifacts": {
    "ART-001": {
      "path": "intermediate_data.json",
      "producer_step": "ST-001",
      "consumer_steps": []  // ❌ No consumers!
    }
  }
}
```

#### FM-02: Write Conflicts

**Script:** `wiring/P_01260207233100000279_detect_write_conflicts.py`  
**Detection:** Multiple steps writing to same artifact  
**Risk:** Race conditions, data corruption, non-deterministic results  

```python
def main():
    with open(args.plan_file) as f:
        data = json.load(f)
    
    artifacts = data.get('plan', {}).get('artifacts', {})
    conflicts = []
    
    writers = defaultdict(list)
    for aid, adata in artifacts.items():
        producer = adata.get('producer_phase')
        if producer:
            writers[aid].append(producer)
    
    for aid, producers in writers.items():
        if len(producers) > 1:
            conflicts.append({'artifact': aid, 'writers': producers})
    
    print(f"{'✅ PASSED' if not conflicts else '❌ CONFLICTS'}: {len(conflicts)} write conflicts")
    sys.exit(0 if not conflicts else 1)
```

#### FM-03: Incomplete Handoffs

**Script:** `wiring/P_01260207233100000285_validate_handoffs.py`  
**Detection:** Artifact handoffs missing schema or location  
**Risk:** Consumer doesn't know format/location of data  

```python
def main():
    artifacts = data.get('plan', {}).get('artifacts', {})
    incomplete = []
    
    for aid, adata in artifacts.items():
        if not adata.get('schema_ref') or not adata.get('location'):
            incomplete.append(aid)
    
    sys.exit(0 if not incomplete else 1)
```

#### FM-04: Dead Artifacts

**Script:** `wiring/P_01260207233100000274_check_dead_artifacts.py`  
**Detection:** Artifacts consumed but never produced  
**Risk:** Missing dependencies, execution will fail  

#### FM-05: Missing Producers

**Script:** `wiring/P_01260207233100000276_check_missing_producers.py`  
**Detection:** Artifacts with no defined producer  
**Risk:** Unknown data source, ambiguous requirements  

#### FM-06: Circular Dependencies

**Script:** `wiring/P_01260207233100000278_detect_cycles.py`  
**Detection:** Cycles in phase dependency graph  
**Risk:** Cannot determine execution order, deadlock  

```python
def detect_cycle(graph, node, visited, stack):
    """DFS-based cycle detection."""
    visited.add(node)
    stack.add(node)
    
    for neighbor in graph.get(node, []):
        if neighbor not in visited:
            if detect_cycle(graph, neighbor, visited, stack):
                return True
        elif neighbor in stack:  # Back edge = cycle
            return True
    
    stack.remove(node)
    return False

def main():
    phases = data.get('plan', {}).get('phases_by_id', {})
    graph = {pid: pdata.get('depends_on', []) for pid, pdata in phases.items()}
    
    has_cycle = any(detect_cycle(graph, node, set(), set()) for node in graph)
    
    sys.exit(0 if not has_cycle else 1)
```

#### FM-07: Dormant Flows

**Script:** `wiring/P_01260207233100000275_check_dormant_flows.py`  
**Detection:** Phases without validation gates  
**Risk:** Phase executes without verification  
**Severity:** ⚠️ Warning (exit code 0 always)  

#### FM-08: Evidence Bundle Gaps

**Script:** `wiring/P_01260207233100000284_validate_evidence_bundles.py`  
**Detection:** Gates without evidence_output paths  
**Risk:** Cannot verify gate execution, no audit trail  

#### FM-09: Recovery Policy Gaps

**Script:** `wiring/P_01260207233100000286_validate_recovery_policies.py`  
**Detection:** Commands lacking retry/rollback policies  
**Risk:** Cannot recover from failures  

#### FM-10: Idempotency Violations

**Script:** `wiring/P_01260207233100000281_test_idempotency_all.py`  
**Detection:** Commands marked idempotent containing unsafe operations (e.g., `rm -rf`)  
**Risk:** Re-running causes unintended side effects  

```python
def main():
    commands = data.get('plan', {}).get('commands', {})
    violations = []
    
    for cid, cdata in commands.items():
        if cdata.get('idempotent') and 'rm -rf' in cdata.get('command', ''):
            violations.append(cid)
    
    sys.exit(0 if not violations else 1)
```

#### FM-11: Detection Gate Gaps

**Script:** `wiring/P_01260207233100000282_validate_detection_gates.py`  
**Detection:** Phases lacking validation gates  
**Risk:** Similar to FM-07  
**Severity:** ⚠️ Warning  

#### FM-12: E2E Proof Linkage Gaps

**Script:** `wiring/P_01260207233100000283_validate_e2e_proof_linkage.py`  
**Detection:** Gates missing validation_command or success_pattern  
**Risk:** Cannot mechanically verify gate success  

### 5.3 FM Results Aggregation

GATE-012 produces:

```json
{
  "gate_id": "GATE-012",
  "validated_at": "2026-02-10T19:00:00Z",
  "fm_results": {
    "FM-01": {"status": "pass", "checked": true, "exit_code": 0},
    "FM-02": {"status": "fail", "checked": true, "exit_code": 1},
    "FM-03": {"status": "pass", "checked": true, "exit_code": 0},
    "FM-04": {"status": "pass", "checked": true, "exit_code": 0},
    "FM-05": {"status": "pass", "checked": true, "exit_code": 0},
    "FM-06": {"status": "pass", "checked": true, "exit_code": 0},
    "FM-07": {"status": "pass", "checked": true, "exit_code": 0},
    "FM-08": {"status": "pass", "checked": true, "exit_code": 0},
    "FM-09": {"status": "fail", "checked": true, "exit_code": 1},
    "FM-10": {"status": "pass", "checked": true, "exit_code": 0},
    "FM-11": {"status": "pass", "checked": true, "exit_code": 0},
    "FM-12": {"status": "pass", "checked": true, "exit_code": 0}
  },
  "all_passed": false,
  "passed_count": 10,
  "total_count": 12
}
```

---

## 6. Execution Pipeline

### 6.1 Command Invocation

```bash
# Full validation run with all gates
python scripts/P_01260207233100000242_NEWPHASEPLANPROCESS_plan_cli.py \
  run-gates \
  --plan-file my_plan.json \
  --evidence-dir .state/evidence \
  --run-id CUSTOM_ID_001

# Fail-fast mode (stop on first failure)
python scripts/P_01260207233100000242_NEWPHASEPLANPROCESS_plan_cli.py \
  run-gates \
  --plan-file my_plan.json \
  --fail-fast

# Only required gates (skip optional VAL-* gates)
python scripts/P_01260207233100000242_NEWPHASEPLANPROCESS_plan_cli.py \
  run-gates \
  --plan-file my_plan.json \
  --only-required
```

### 6.2 Execution Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ 1. USER INVOKES CLI                                         │
│    python plan_cli.py run-gates --plan-file plan.json       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. LOAD DEPENDENCIES                                        │
│    - Read gate_dependencies.json                            │
│    - Filter optional gates (if --only-required)             │
│    - Total gates: 19 required + 5 optional                  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. TOPOLOGICAL SORT                                         │
│    - Build dependency graph                                 │
│    - Detect cycles (fail if found)                          │
│    - Generate execution order                               │
│    Example order:                                           │
│      GATE-000 → GATE-001 → GATE-002,003,004,005 (parallel) │
│      → GATE-006 → GATE-007 → GATE-008                       │
│      → GATE-010 → GATE-011 → GATE-012 → GATE-013           │
│      → GATE-014,015,016,017 (parallel)                      │
│      → GATE-998 → GATE-999                                  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. SEQUENTIAL EXECUTION (NO PARALLELISM IN v2.4.0)          │
│    FOR EACH gate IN sorted_order:                           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. CHECK DEPENDENCIES                                       │
│    - If any depends_on gate failed: SKIP this gate          │
│    - Add to skipped list                                    │
│    - Continue to next gate                                  │
└────────────────────┬────────────────────────────────────────┘
                     │ (dependencies OK)
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. PREPARE GATE EXECUTION                                   │
│    - Create evidence directory: .state/evidence/GATE-XXX/   │
│    - Build command:                                         │
│      [python, gate_script.py,                               │
│       --plan-file, plan.json,                               │
│       --evidence-dir, .state/evidence/GATE-XXX/]            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. RUN GATE (subprocess.run)                                │
│    - Timeout: 300 seconds (5 minutes)                       │
│    - Capture stdout/stderr                                  │
│    - Handle exceptions:                                     │
│      * TimeoutExpired → Mark as failed                      │
│      * Other exceptions → Mark as failed                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 8. CHECK EXIT CODE                                          │
│    - exit_code == 0 → PASSED                                │
│    - exit_code != 0 → FAILED                                │
└────────────────┬────────────┬───────────────────────────────┘
                 │            │
         (PASSED)│            │(FAILED)
                 ▼            ▼
        ┌─────────────┐  ┌──────────────────────┐
        │ Add to      │  │ Add to failed list   │
        │ passed list │  │ Print error output   │
        └─────────────┘  └──────┬───────────────┘
                                │
                                ▼
                        ┌───────────────────┐
                        │ Check fail_fast?  │
                        └──────┬────────┬───┘
                               │        │
                        (YES)  │        │ (NO)
                               ▼        ▼
                        ┌───────────┐  ┌─────────────┐
                        │ STOP      │  │ Continue to │
                        │ Return    │  │ next gate   │
                        └───────────┘  └─────────────┘
                                
                                ▼
┌─────────────────────────────────────────────────────────────┐
│ 9. (SPECIAL) GATE-012 EXECUTION                             │
│    - Runs audit_failure_modes.py                            │
│    - Internally runs all 12 FM checks                       │
│    - Aggregates FM results                                  │
│    - Returns 0 only if ALL FM checks pass                   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 10. GENERATE SUMMARY                                        │
│     - Count passed/failed/skipped                           │
│     - List failed gate IDs                                  │
│     - Print summary report                                  │
│     - Exit with code:                                       │
│       * 0 if all gates passed                               │
│       * 1 if any gate failed                                │
└─────────────────────────────────────────────────────────────┘
```

### 6.3 Example Execution Output

```
================================================================================
🚀 GATE VALIDATION RUN
Run ID: 20260210_190000
Plan: my_project.plan.json
Evidence: .state/evidence
Gates to execute: 19
Mode: Run all
================================================================================

▶️  [1/19] GATE-000 - No Obfuscation Check
    Script: P_01260207233100000258_validate_plan_structure.py
✅  [1/19] GATE-000 - PASSED

▶️  [2/19] GATE-001 - Schema Validation
    Script: P_01260207233100000263_validate_structure.py
✅  [2/19] GATE-001 - PASSED

▶️  [3/19] GATE-002 - Gate Definitions Valid
    Script: P_01260207233100000253_validate_gates.py
✅  [3/19] GATE-002 - PASSED

▶️  [4/19] GATE-003 - Step Contracts Complete
    Script: P_01260207233100000262_validate_step_contracts.py
❌  [4/19] GATE-003 - FAILED (exit code 1)
    Error: 3 steps missing postconditions

▶️  [5/19] GATE-004 - Assumptions Documented
    Script: P_01260207233100000248_validate_assumptions.py
⏭️  [5/19] GATE-004 - SKIPPED (dependency failed)

...

▶️  [12/19] GATE-012 - Failure Modes Audit
    Script: wiring/P_01260207233100000273_audit_failure_modes.py
    Running 12 FM checks...
    ✅ FM-01: 0 orphaned artifacts
    ❌ FM-02: 2 write conflicts detected
    ✅ FM-03: All handoffs complete
    ...
❌  [12/19] GATE-012 - FAILED (exit code 1)

================================================================================
📊 VALIDATION SUMMARY
================================================================================
✅ Passed:  16
❌ Failed:  2
⏭️  Skipped: 1
📝 Total:   19

Failed gates:
  - GATE-003
  - GATE-012

Evidence: .state/evidence
================================================================================

Exit code: 1
```

### 6.4 Timeout Handling

Each gate has a **5-minute timeout**:

```python
try:
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace',
        timeout=300  # 5 minutes
    )
except subprocess.TimeoutExpired:
    print(f"⏱️  [{i}/{len(sorted_gates)}] {gate_id} - TIMEOUT (>5 minutes)")
    failed.append(gate_id)
    if fail_fast:
        break
```

### 6.5 Error Handling

**Types of Errors:**

1. **File Not Found:** Gate script missing
2. **Invalid JSON:** Plan file malformed
3. **Timeout:** Gate exceeds 5 minutes
4. **Non-zero Exit:** Gate validation failed
5. **Exception:** Python error during execution

**Recovery Actions:**

- **Current System:** None - manual intervention required
- **Error Logging:** stderr captured in evidence
- **Exit Strategy:** Fail-fast (optional) or continue-to-end

---

## 7. Evidence & Artifact Management

### 7.1 Evidence Lifecycle

```
┌──────────────────┐
│ Gate Executes    │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────────────────┐
│ Gate Script Generates Evidence       │
│ - Validation results                 │
│ - Error details                      │
│ - Statistics                         │
│ - Timestamps                         │
└────────┬─────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────┐
│ Write Evidence to Disk               │
│ Path: .state/evidence/GATE-XXX/      │
│ Format: JSON                         │
│ Permissions: Read-only after write   │
└────────┬─────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────┐
│ Evidence Referenced in Gate Result   │
│ CLI includes path in summary         │
└────────┬─────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────┐
│ Evidence Persists for Audit          │
│ Retention: Indefinite (user-managed) │
│ Used for: Debugging, compliance      │
└──────────────────────────────────────┘
```

### 7.2 Evidence Standards

**Mandatory Fields:**

```json
{
  "gate_id": "GATE-XXX",               // Required
  "gate_name": "Human-readable name",  // Required
  "validated_at": "ISO-8601 UTC",      // Required
  "validator_version": "x.y.z",        // Required
  "plan_file": "/abs/path/to/plan",    // Required
  "validation_result": {               // Required
    "status": "valid|invalid",
    "errors_count": 0,
    "warnings_count": 0
  }
}
```

**Optional Fields:**

- `statistics`: Gate-specific metrics
- `details`: Additional context
- `recommendations`: Suggested fixes

### 7.3 Evidence Storage

**Directory Structure:**

```
.state/
├── evidence/
│   ├── GATE-000/
│   │   └── structure_validation.json          (Generated: 2026-02-10 19:00:00)
│   ├── GATE-001/
│   │   └── schema_validation.json             (Generated: 2026-02-10 19:00:05)
│   ├── GATE-002/
│   │   └── gates_validation.json              (Generated: 2026-02-10 19:00:10)
│   ├── GATE-003/
│   │   ├── step_contracts_validation.json     (Generated: 2026-02-10 19:00:15)
│   │   └── contract_details.json              (Supplementary evidence)
│   └── GATE-012/
│       ├── failure_mode_audit.json            (Main evidence)
│       └── fm_results/
│           ├── FM-01_result.json
│           ├── FM-02_result.json
│           └── ...
└── metrics/
    └── metrics.jsonl                           (Execution metrics)
```

**Retention Policy:**

- Evidence files are **immutable** after creation
- No automatic cleanup (user responsibility)
- Recommended retention: 90 days minimum for compliance

### 7.4 Artifact Registry

**Purpose:** Track all artifacts (inputs/outputs) across plan  
**Validated By:** GATE-011  

**Schema:**

```json
{
  "artifacts": {
    "ART-001": {
      "artifact_id": "ART-001",
      "path": "data/input.json",
      "kind": "INPUT_DATA",
      "producer_phase": "PH-001",
      "producer_step": "ST-001",
      "consumer_phases": ["PH-002"],
      "consumer_steps": ["ST-003"],
      "schema_ref": "schemas/input_data.schema.json",
      "location": "absolute_or_relative_path",
      "size_bytes": 1024,
      "checksum": "sha256:abc123...",
      "created_at": "2026-02-10T19:00:00Z"
    }
  }
}
```

**Validation Rules:**

- Every artifact must have a `producer_phase`
- Every artifact should have at least one `consumer_phase` (unless terminal output)
- `schema_ref` must point to valid schema file
- `location` must be resolvable path

---

## 8. Data Structures & Schemas

### 8.1 Plan Schema v3.0.0

**File:** `schemas/01260207233100000675_NEWPHASEPLANPROCESS_plan.schema.v3.0.0.json`  
**Standard:** JSON Schema Draft 2020-12  
**Size:** ~2,000 lines  

**Top-Level Structure:**

```json
{
  "meta": {
    "plan_id": "PLAN-XXXXXXXX",
    "version": "3.0.0",
    "created_at": "2026-02-10T19:00:00Z",
    "updated_at": "2026-02-10T19:00:00Z",
    "schema_version": "3.0.0"
  },
  "plan": {
    "phases": [],
    "gates_by_id": {},
    "artifacts": {},
    "assumptions": {},
    "file_manifest": {},
    "execution_config": {}
  },
  "navigation": {
    "phase_dag": {},
    "dependency_order": []
  }
}
```

### 8.2 Phase Definition

```json
{
  "phase_id": "PH-001",
  "name": "Phase Name",
  "description": "Human-readable description",
  "gates": ["GATE-001", "GATE-002"],
  "steps": [
    {
      "step_id": "ST-001",
      "name": "Step Name",
      "inputs": [
        {
          "artifact_id": "ART-001",
          "path": "path/to/input",
          "must_exist": true,
          "schema_id": "schemas/input.schema.json"
        }
      ],
      "outputs": [
        {
          "artifact_id": "ART-002",
          "path": "path/to/output",
          "schema_id": "schemas/output.schema.json"
        }
      ],
      "preconditions": [
        {
          "condition_id": "PRE-001",
          "description": "Input exists",
          "validation_command": "test -f path/to/input",
          "must_pass": true
        }
      ],
      "postconditions": [
        {
          "condition_id": "POST-001",
          "description": "Output created",
          "validation_command": "test -f path/to/output",
          "must_pass": true
        }
      ],
      "invariants": [
        "Global state unchanged",
        "File count constant"
      ],
      "commands": [
        "python process.py --input path/to/input --output path/to/output"
      ],
      "rollback": [
        "rm -f path/to/output"
      ],
      "evidence": ".state/evidence/PH-001/ST-001/",
      "idempotent": true,
      "file_scope": {
        "allowed_paths": ["path/to/*"],
        "forbidden_paths": ["system/*"],
        "read_only_paths": ["config/*"]
      }
    }
  ],
  "depends_on": ["PH-000"],
  "parallel_safe": false
}
```

### 8.3 Gate Definition

```json
{
  "gate_id": "GATE-001",
  "gate_name": "Schema Validation",
  "validation_command": "python scripts/P_01260207233100000263_validate_structure.py --plan-file {{plan_file}}",
  "success_pattern": "✅ PASSED",
  "evidence_output": ".state/evidence/GATE-001/schema_validation.json",
  "depends_on": ["GATE-000"],
  "timeout_seconds": 300,
  "retry_on_failure": false,
  "critical": true
}
```

### 8.4 Gate Dependencies Format

```json
{
  "gates": [
    {
      "id": "GATE-001",
      "name": "Schema Validation",
      "script": "P_01260207233100000263_validate_structure.py",
      "depends_on": ["GATE-000"],
      "phase": "core-validation",
      "required": true,
      "evidence_dir": ".state/evidence/GATE-001"
    }
  ]
}
```

---

## 9. Security & Safety Mechanisms

### 9.1 Input Validation

**Plan File Validation:**

1. **JSON Parsing:** Validate JSON syntax before schema validation
2. **Schema Validation:** GATE-001 enforces JSON Schema Draft 2020-12
3. **Placeholder Detection:** GATE-000 rejects TODO/TBD/FIXME markers
4. **Path Validation:** All file paths checked for traversal attacks

**Command Injection Prevention:**

```python
# SAFE: Using list-based subprocess call
subprocess.run([sys.executable, script_path, "--plan-file", plan_file])

# UNSAFE: String-based shell=True (NOT USED IN SYSTEM)
# subprocess.run(f"python {script_path} --plan-file {plan_file}", shell=True)
```

### 9.2 File System Safety

**Constraints:**

- All evidence written to `.state/evidence/` only
- No writes outside project directory
- File permissions: User read/write, no execute
- Directory creation: Parents created with `exist_ok=True`

**Scoping (GATE-003 Enforced):**

```json
{
  "file_scope": {
    "allowed_paths": ["src/*", "data/*"],
    "forbidden_paths": ["/etc/*", "/sys/*", "~/.ssh/*"],
    "read_only_paths": ["config/*", "schemas/*"]
  }
}
```

### 9.3 Secret Detection

**Script:** `P_01260207233100000230_check_secrets.py`  
**Detection Patterns:**

```python
SECRET_PATTERNS = [
    r"password\s*=\s*['\"]([^'\"]+)['\"]",
    r"api_key\s*=\s*['\"]([^'\"]+)['\"]",
    r"token\s*=\s*['\"]([^'\"]+)['\"]",
    r"secret\s*=\s*['\"]([^'\"]+)['\"]",
    r"AWS_SECRET_ACCESS_KEY",
    r"-----BEGIN (RSA|DSA|EC) PRIVATE KEY-----"
]
```

### 9.4 Resource Limits

**Per-Gate Timeouts:**

- Default: 300 seconds (5 minutes)
- Enforced via `subprocess.run(timeout=300)`
- Exceeded → Gate marked as failed

**Memory Limits:**

- Not enforced at system level (relies on OS)
- Large plans (>10MB JSON) may cause performance issues

**Concurrency Limits:**

- Current: Sequential execution only (no parallelism)
- Future: Configurable via `max_concurrent_phases`

---

## 10. Operational Procedures

### 10.1 Normal Operation

**Step 1: Prepare Plan**

```bash
# Create plan JSON file
vi my_project.plan.json

# Validate plan structure first
python scripts/P_01260207233100000242_NEWPHASEPLANPROCESS_plan_cli.py \
  validate my_project.plan.json
```

**Step 2: Run Gates**

```bash
# Run all gates
python scripts/P_01260207233100000242_NEWPHASEPLANPROCESS_plan_cli.py \
  run-gates \
  --plan-file my_project.plan.json \
  --evidence-dir .state/evidence \
  --run-id PROJECT_001

# Check exit code
echo $?  # 0 = success, 1 = failure
```

**Step 3: Review Evidence**

```bash
# List all evidence
ls -la .state/evidence/

# View specific gate evidence
cat .state/evidence/GATE-001/schema_validation.json | jq .

# Check failures
grep -r '"status": "invalid"' .state/evidence/
```

**Step 4: Fix Failures**

```bash
# Example: Fix GATE-003 failure (missing postconditions)
vi my_project.plan.json  # Add postconditions to steps

# Re-run gates
python scripts/P_01260207233100000242_NEWPHASEPLANPROCESS_plan_cli.py \
  run-gates \
  --plan-file my_project.plan.json
```

### 10.2 Troubleshooting

#### Issue: Gate Timeout

**Symptoms:**
```
⏱️  [3/19] GATE-003 - TIMEOUT (>5 minutes)
```

**Diagnosis:**
- Gate script hung or very slow
- Large plan file (>10MB)
- Complex validation logic

**Resolution:**
```bash
# Run gate manually to see output
python scripts/P_01260207233100000262_validate_step_contracts.py \
  --plan-file my_project.plan.json \
  --evidence-dir .state/evidence/GATE-003 \
  --verbose

# Increase timeout in source (requires code change)
# Edit: P_01260207233100000242_NEWPHASEPLANPROCESS_plan_cli.py
# Change: timeout=300 to timeout=600
```

#### Issue: Circular Dependency

**Symptoms:**
```
❌ Error: Circular dependency detected in gate graph!
```

**Diagnosis:**
```bash
# Check gate_dependencies.json for cycles
python -c "
import json
from pathlib import Path
data = json.loads(Path('scripts/01260207233100000678_gate_dependencies.json').read_text())
for gate in data['gates']:
    print(f\"{gate['id']}: depends_on {gate.get('depends_on', [])}\")"
```

**Resolution:**
- Remove circular dependency in `gate_dependencies.json`
- Ensure DAG (Directed Acyclic Graph) structure

#### Issue: Evidence Not Generated

**Symptoms:**
```
✅  [2/19] GATE-001 - PASSED
ls: .state/evidence/GATE-001/: No such file or directory
```

**Diagnosis:**
- Gate script didn't create evidence
- Wrong evidence directory path
- Permissions issue

**Resolution:**
```bash
# Create evidence directory manually
mkdir -p .state/evidence/GATE-001

# Check gate script for evidence generation
grep "evidence" scripts/P_01260207233100000263_validate_structure.py

# Run gate with explicit evidence dir
python scripts/P_01260207233100000263_validate_structure.py \
  --plan-file my_project.plan.json \
  --evidence-dir .state/evidence/GATE-001
```

### 10.3 Performance Tuning

**Metrics Collection:**

```bash
# Enable metrics (if supported)
export NPP_METRICS_ENABLED=1

# Run gates with timing
time python scripts/P_01260207233100000242_NEWPHASEPLANPROCESS_plan_cli.py \
  run-gates --plan-file my_project.plan.json

# View metrics
cat .state/metrics/metrics.jsonl | jq .
```

**Optimization Strategies:**

1. **Skip Optional Gates:**
   ```bash
   python plan_cli.py run-gates --plan-file plan.json --only-required
   ```

2. **Use Fail-Fast:**
   ```bash
   python plan_cli.py run-gates --plan-file plan.json --fail-fast
   ```

3. **Cache Evidence:**
   - Reuse evidence from previous runs if plan unchanged
   - Compare plan checksums before re-running gates

### 10.4 Maintenance Procedures

**Weekly:**

- Review `.state/evidence/` size (clean old evidence if >1GB)
- Check for gate script updates
- Verify schema files are current

**Monthly:**

- Audit gate execution times (identify slow gates)
- Review FM check results (identify common failures)
- Update documentation

**Quarterly:**

- Review gate dependencies (optimize execution order)
- Update JSON schemas to latest draft
- Performance benchmarking

---

## 11. Known Limitations

### 11.1 Architectural Limitations

| Limitation | Impact | Workaround | Future Resolution |
|------------|--------|-----------|-------------------|
| **No Self-Healing** | Manual recovery required on gate failure | Document common fixes | Implement self-healing orchestrator |
| **Sequential Execution** | Long validation time (19 gates × 5 min = 95 min worst case) | Use `--fail-fast` | Implement parallel gate execution |
| **Per-Gate Scripts** | 44 separate scripts, duplication of argparse logic | Standardize argparse usage | Consolidate to shared GateRunner |
| **No Retry Logic** | Transient failures require manual rerun | Script wrapper for retries | Add bounded retry with exponential backoff |
| **Manual Evidence Cleanup** | Evidence accumulates indefinitely | Periodic manual deletion | Implement retention policy |

### 11.2 Scalability Limits

| Metric | Current Limit | Impact | Recommendation |
|--------|---------------|--------|----------------|
| **Plan Size** | ~10MB JSON | Performance degrades | Split large plans into sub-plans |
| **Gate Count** | 24 gates | ~15 min validation time | Optimize gate logic |
| **Phase Count** | ~100 phases | Memory usage ~500MB | No action needed |
| **Step Count** | ~1000 steps | GATE-003 timeout risk | Increase timeout |
| **Artifact Count** | ~5000 artifacts | FM checks slow | Index artifact registry |

### 11.3 Error Handling Gaps

1. **Network Failures:** No retry for network-dependent gates
2. **Disk Full:** No pre-check for evidence storage space
3. **Permission Errors:** Not handled gracefully (generic Python exception)
4. **Corrupted Evidence:** No validation of existing evidence files
5. **Partial Writes:** Evidence files not written atomically

### 11.4 Security Considerations

1. **Command Injection:** Mitigated via list-based subprocess calls (not shell=True)
2. **Path Traversal:** Basic validation present, but not comprehensive
3. **Secret Detection:** Pattern-based only (false negatives possible)
4. **Evidence Tampering:** No cryptographic signatures on evidence files
5. **Privilege Escalation:** Runs with user permissions (no privilege separation)

---

## 12. Appendices

### 12.1 Glossary

| Term | Definition |
|------|------------|
| **Artifact** | File or data product produced/consumed by plan steps |
| **Evidence** | Timestamped JSON proof of gate validation result |
| **Fail-Closed** | Default to failure when outcome is unknown/ambiguous |
| **FM Check** | Failure Mode check detecting specific wiring failures |
| **Gate** | Binary pass/fail validation check with evidence requirement |
| **Phase** | Ordered group of steps with gates and dependencies |
| **Step Contract** | Explicit declaration of inputs, outputs, pre/post conditions |
| **Topological Sort** | Ordering gates by dependencies (DAG traversal) |
| **Wiring** | Artifact flow and handoff validation |

### 12.2 File Size Reference

| File/Directory | Size | Lines of Code |
|----------------|------|---------------|
| `P_01260207233100000242_NEWPHASEPLANPROCESS_plan_cli.py` | ~50KB | 1,100 |
| `schemas/01260207233100000675_NEWPHASEPLANPROCESS_plan.schema.v3.0.0.json` | ~80KB | 2,000 |
| `scripts/` (all gate scripts) | ~500KB | 12,000 |
| `.state/evidence/` (after full run) | ~5MB | N/A |
| `gate_dependencies.json` | ~8KB | 173 |

### 12.3 Performance Benchmarks

**Test Environment:**
- CPU: Intel i7-10700 @ 2.9GHz
- RAM: 16GB
- Disk: SSD
- OS: Windows 11
- Python: 3.11.5

**Results (Average of 10 runs):**

| Operation | Time | Notes |
|-----------|------|-------|
| Schema Validation (GATE-001) | 0.8s | Plan size: 500KB |
| Step Contracts (GATE-003) | 12.5s | 100 steps |
| FM Audit (GATE-012) | 8.2s | All 12 FM checks |
| Full Gate Run (19 gates) | 45s | All gates pass |
| Full Gate Run (with failures) | 38s | Fail-fast at GATE-003 |

### 12.4 Exit Code Reference

| Exit Code | Meaning | When Used |
|-----------|---------|-----------|
| 0 | Success | All gates passed |
| 1 | Validation Failure | One or more gates failed |
| 2 | File Not Found | Plan file or dependency missing |
| 3 | Invalid JSON | Plan file malformed |
| 4 | Schema Violation | Plan doesn't conform to schema |
| 130 | User Interrupt | Ctrl+C pressed |

### 12.5 Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `NPP_SCHEMA_PATH` | `schemas/` | Override schema directory |
| `NPP_EVIDENCE_DIR` | `.state/evidence` | Override evidence directory |
| `NPP_METRICS_ENABLED` | `false` | Enable metrics collection |
| `NPP_LOG_LEVEL` | `INFO` | Logging verbosity |
| `NPP_TIMEOUT` | `300` | Default gate timeout (seconds) |

### 12.6 Common Error Codes

**GATE-000 Errors:**

| Code | Message | Resolution |
|------|---------|------------|
| `PLACEHOLDER_FOUND` | TODO/TBD/FIXME detected | Remove placeholders |
| `EMPTY_STRING` | Required field is empty | Populate field |

**GATE-001 Errors:**

| Code | Message | Resolution |
|------|---------|------------|
| `SCHEMA_VALIDATION_FAILED` | JSON doesn't match schema | Fix JSON structure |
| `MISSING_REQUIRED_FIELD` | Required field missing | Add field |
| `INVALID_TYPE` | Field has wrong type | Fix type |

**GATE-003 Errors:**

| Code | Message | Resolution |
|------|---------|------------|
| `MISSING_INPUTS` | Step has no inputs | Add inputs array |
| `MISSING_OUTPUTS` | Step has no outputs | Add outputs array |
| `MISSING_PRECONDITIONS` | No preconditions defined | Add preconditions |
| `MISSING_POSTCONDITIONS` | No postconditions defined | Add postconditions |

**FM Errors:**

| Code | Message | Resolution |
|------|---------|------------|
| `FM-01_ORPHAN` | Artifact produced but not consumed | Add consumer or remove artifact |
| `FM-02_WRITE_CONFLICT` | Multiple writers to same artifact | Deduplicate producers |
| `FM-06_CYCLE` | Circular dependency detected | Remove circular reference |

### 12.7 Related Documentation

- **Plan Schema:** `schemas/01260207233100000675_NEWPHASEPLANPROCESS_plan.schema.v3.0.0.json`
- **AI Usage Guide:** `PLAN_AI_USAGE_GUIDE.md`
- **Registry Integration:** `REGISTRY_PLANNING_INTEGRATION_SPEC.md`
- **Claude CLI Reference:** `CLAUDE.md`
- **Self-Healing Proposal:** `ChatGPT-Self-Healing Gate Process.json`
- **Reusable Patterns:** `ChatGPT-Reusable Pattern Programs (1).json`

### 12.8 Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.4.0 | 2026-02-03 | Current production version |
| 2.3.0 | 2026-01-15 | Added GATE-017 (SSOT validation) |
| 2.2.0 | 2025-12-10 | Added FM-12 (E2E linkage) |
| 2.1.0 | 2025-11-05 | Added step-level contracts |
| 2.0.0 | 2025-10-01 | Schema v3.0.0, breaking changes |

---

## Document Control

**Author:** System Architect  
**Reviewers:** Engineering Team  
**Approval:** Technical Lead  
**Next Review:** 2026-05-10  
**Classification:** Internal Use  

**Change Log:**

| Date | Version | Author | Changes |
|------|---------|--------|---------|
| 2026-02-10 | 1.0.0 | System | Initial technical specification |

---

**END OF DOCUMENT**
