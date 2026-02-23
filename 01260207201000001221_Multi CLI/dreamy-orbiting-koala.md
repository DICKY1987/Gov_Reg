# LangGraph Multi-Agent Orchestration System - Complete Implementation Plan

## Context

The user has two key architecture documents:
1. **LangGraph Integration Architecture** - Describes LangGraph as a control-plane orchestration layer above existing deterministic CLI tools
2. **Deep Research Report** - Describes a Contract-First Self-Healing Planner-Critic Loop using Codex CLI and Copilot CLI

The goal is to implement a **100% COMPLETE SYSTEM** that integrates these two architectures to create a production-grade multi-agent planning and execution workflow.

### Why This Implementation

**Problem:** The existing system has excellent planning infrastructure (MCP server, NPP CLI, 18+ validation gates, registry enforcement) but no AI agent coordination. Planning and execution are manual, single-pass processes without iterative refinement.

**Solution:** Add LangGraph as an orchestration control plane that coordinates multiple AI agents (Planner, Critic, Refiner) in a self-healing feedback loop, then executes validated plans through existing deterministic infrastructure.

**Outcome:** Automated, iterative plan generation with quality gates, deterministic validation, and full audit trails - all while preserving existing governance primitives (registry CAS, write policies, evidence sealing, worktree isolation).

---

## System Architecture

### High-Level Flow

```
Planning Request → LangGraph Orchestrator
  ↓
  Planner (Codex CLI) → Draft Plan
  ↓
  Quality Gate (Deterministic) → Pass/Fail
  ↓ (if pass)
  Critic (Copilot CLI) → Critique Report
  ↓
  Convergence Check → Converged/Needs Revision
  ↓ (if needs revision)
  Refiner (Codex CLI) → Revised Plan → back to Quality Gate
  ↓ (if converged)
  Executor (NPP CLI) → Execute Plan
  ↓
  Gates Runner → Run GATE-000 through GATE-017
  ↓
  Evidence Sealer → Hash artifacts, seal bundle
  ↓
  Complete (checkpointed)
```

### Key Design Decisions

1. **LangGraph = Control Plane ONLY**
   - LangGraph manages state, routing, retries, convergence
   - LangGraph NEVER touches git, registry, or filesystem directly
   - All mutations done via existing CLI tools

2. **Artifact-Based Message Passing**
   - Nodes communicate via JSON files (not free-text)
   - State stores artifact references (path + SHA-256), not content
   - Full audit trail via evidence files

3. **AI Service Selection**
   - **Codex CLI** for Planner/Refiner (has `--output-schema` for guaranteed JSON validity)
   - **Copilot CLI** for Critic (cross-model validation, different LLM provider)
   - Deterministic Python gate (no AI) for quality validation

4. **Convergence Strategy**
   - Max 3 iterations (configurable)
   - Convergence threshold: 0.85 (weighted scorecard)
   - Loop terminates on: convergence met, max attempts, or no delta change

5. **Zero Changes to Existing Code**
   - MCP server unchanged
   - NPP CLI unchanged
   - Gate scripts unchanged
   - Registry writer unchanged
   - All integration via new wrapper layer

---

## Directory Structure

All new code goes in: `LP_LONG_PLAN/newPhasePlanProcess/01260207201000001221_Multi_CLI/`

### New Directories (67 files total)

```
01260207201000001221_Multi_CLI/
├── langgraph_integration/          # LangGraph orchestration (30 files)
│   ├── graph_builder.py            # Graph definition
│   ├── state_schema.py             # State TypedDict
│   ├── nodes/                      # Node implementations (7 nodes)
│   ├── routers/                    # Conditional routing (3 routers)
│   ├── tools/                      # Tool wrappers (6 wrappers)
│   ├── checkpointing/              # SQLite checkpoint (2 files)
│   ├── config/                     # YAML configs (4 files)
│   └── cli/                        # Entry points (2 CLIs)
│
├── ai_service_wrappers/            # AI service integration (10 files)
│   ├── planner.py                  # Codex Planner
│   ├── critic.py                   # Copilot Critic
│   ├── refiner.py                  # Codex Refiner
│   ├── plan_quality_gate.py        # Deterministic gate
│   ├── run_loop.sh                 # Standalone bash orchestrator
│   └── utils/                      # Utilities (4 files)
│
├── schemas_langgraph/              # LangGraph schemas (7 files)
│   ├── planning_request.schema.json
│   ├── draft_plan.schema.json
│   ├── envelope.schema.json
│   ├── gate_report.schema.json
│   ├── critique_report.schema.json
│   ├── langgraph_state.schema.json
│   └── convergence_metrics.schema.json
│
├── tests/                          # Test suite (15 files)
│   ├── unit/                       # Unit tests (5 files)
│   ├── integration/                # Integration tests (5 files)
│   └── e2e/                        # End-to-end tests (4 files)
│
└── docs/                           # Documentation (5 files)
    ├── ARCHITECTURE.md
    ├── API_REFERENCE.md
    ├── TROUBLESHOOTING.md
    ├── DEPLOYMENT.md
    └── RUNBOOK.md
```

### Evidence Storage

```
.state/
├── langgraph_checkpoints/          # NEW
│   └── checkpoints.db              # SQLite checkpoint store
└── evidence/
    └── langgraph_runs/              # NEW
        └── <run_id>/
            ├── <iteration>/
            │   ├── planner_envelope.json
            │   ├── draft_plan.json
            │   ├── gate_report.json
            │   ├── critique_report.json
            │   └── logs/
            ├── run_meta.json
            └── convergence_trace.jsonl
```

---

## Critical Files (Implement These First)

### 1. State Schema
**Path:** `langgraph_integration/state_schema.py`

Defines the LangGraph state that flows through all nodes:

```python
class PlanningState(TypedDict):
    # Core identifiers
    run_id: str
    plan_id: Optional[str]

    # Iteration tracking
    iteration: int
    hop_counter: int
    phase: str  # planner, gate, critic, refiner, executor, etc.

    # Artifacts (by reference, not content)
    planning_request: ArtifactReference
    current_plan: Optional[ArtifactReference]
    gate_report: Optional[ArtifactReference]
    critique_report: Optional[ArtifactReference]

    # Convergence tracking
    convergence_score: float  # 0.0 to 1.0
    gate_passed: bool
    critic_verdict: str  # pass, needs_revision, fail

    # Error handling
    error_history: List[Dict[str, Any]]
    retry_count: int
    termination_flag: bool
    termination_reason: Optional[str]

    # Metadata
    created_at: str
    updated_at: str
    actor: str
```

### 2. Graph Builder
**Path:** `langgraph_integration/graph_builder.py`

Defines the LangGraph state machine:

```python
def create_planning_graph() -> StateGraph:
    workflow = StateGraph(PlanningState)

    # Add nodes
    workflow.add_node("planner", planner_node.execute)
    workflow.add_node("gate", gate_node.execute)
    workflow.add_node("critic", critic_node.execute)
    workflow.add_node("refiner", refiner_node.execute)
    workflow.add_node("executor", executor_node.execute)
    workflow.add_node("gates_runner", gates_runner_node.execute)
    workflow.add_node("evidence_sealer", evidence_sealer_node.execute)

    # Add edges with conditional routing
    workflow.set_entry_point("planner")
    workflow.add_edge("planner", "gate")

    workflow.add_conditional_edges("gate", route_from_gate, {
        "critic": "critic",
        "refiner": "refiner",
        "fail": "fail",
    })

    workflow.add_conditional_edges("critic", route_from_critic, {
        "executor": "executor",
        "refiner": "refiner",
        "fail": "fail",
    })

    workflow.add_edge("refiner", "gate")  # Loop back
    workflow.add_edge("executor", "gates_runner")
    workflow.add_edge("gates_runner", "evidence_sealer")
    workflow.add_edge("evidence_sealer", END)

    return workflow
```

### 3. Codex CLI Wrapper
**Path:** `langgraph_integration/tools/codex_wrapper.py`

Wraps Codex CLI for schema-enforced plan generation:

```python
class CodexWrapper:
    def execute(
        self,
        prompt: str,
        output_schema_path: Path,
        output_path: Path,
        log_stdout: Path,
        log_stderr: Path,
    ) -> Tuple[int, str]:
        cmd = [
            "codex", "exec",
            "--sandbox", "read-only",
            "--model", self.model,
            "--output-schema", str(output_schema_path),
            "-o", str(output_path),
            "--ephemeral",
            "--skip-git-repo-check",
            prompt
        ]
        # Execute with timeout, auth via CODEX_API_KEY env var
```

**Key Features:**
- Uses `--output-schema` to guarantee JSON Schema compliance
- Uses `-o` to write output to file
- Ephemeral mode (no session history)
- Timeout: 300s (5 minutes)
- Auth: `CODEX_API_KEY` environment variable

### 4. Copilot CLI Wrapper
**Path:** `langgraph_integration/tools/copilot_wrapper.py`

Wraps Copilot CLI for plan critique with JSON extraction:

```python
class CopilotWrapper:
    def execute(
        self,
        plan_path: Path,
        plan_id: str,
        output_path: Path,
        log_stdout: Path,
        log_stderr: Path,
    ) -> Tuple[int, Optional[Dict[str, Any]]]:
        cmd = [
            "copilot",
            "-s",  # Silent mode (output only response)
            "-p", prompt,
            "--no-color",
            "--stream", "off",
            "--deny-tool", "write",
            "--deny-tool", "shell",
        ]
        # Execute with retry logic for JSON parsing
```

**Key Features:**
- Silent mode (`-s`) for programmatic output
- Denies tools (`--deny-tool write`, `--deny-tool shell`) for headless safety
- Retry logic (max 2 attempts) for JSON extraction
- Fallback critique on failure
- Auth: `GH_TOKEN` or `GITHUB_TOKEN` environment variable

### 5. Plan Quality Gate
**Path:** `ai_service_wrappers/plan_quality_gate.py`

Deterministic validation without AI:

```python
def gate_checks(plan: dict):
    defects = []

    # Check: Deliverables have acceptance criteria
    for d in plan.get("deliverables", []):
        if not d.get("acceptance_criteria"):
            defects.append({
                "code": "PLAN_MISSING_ACCEPTANCE",
                "severity": "blocker",
                "message": f"Deliverable {d['id']} missing acceptance_criteria",
                "remediation_template": "add_acceptance_criteria"
            })

    # Check: Quality gates have evidence artifacts
    for g in plan.get("quality_gates", []):
        if not g.get("evidence_artifacts"):
            defects.append({
                "code": "PLAN_WEAK_GATES",
                "severity": "major",
                "message": f"Gate {g['id']} missing evidence_artifacts",
                "remediation_template": "strengthen_gates"
            })

    # Check: Risk register exists
    if not plan.get("risks"):
        defects.append({
            "code": "PLAN_NO_RISKS",
            "severity": "major",
            "message": "Missing risk register",
            "remediation_template": "add_risks"
        })

    return defects
```

**Key Features:**
- Schema validation via jsonschema
- Deterministic defect codes
- Remediation templates for each defect
- Exit code 0 (pass) or 10 (fail)

### 6. SQLite Checkpointer
**Path:** `langgraph_integration/checkpointing/sqlite_checkpointer.py`

Enables replay and audit:

```python
from langgraph.checkpoint.sqlite import SqliteSaver

def create_checkpointer(checkpoint_dir: Path) -> SqliteSaver:
    checkpoint_db = checkpoint_dir / "checkpoints.db"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    return SqliteSaver.from_conn_string(str(checkpoint_db))
```

**Key Features:**
- SQLite-based checkpoint storage
- Stores state snapshots after each node
- Enables resume after crash
- Enables replay for audit
- Enables time-travel debugging

---

## Integration Points

### LangGraph → MCP Server

**File:** `langgraph_integration/tools/mcp_client.py`

Communicates with MCP server via JSON-RPC stdio:

```python
class MCPClient:
    def call_tool(self, tool_name: str, arguments: Dict) -> Dict:
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments}
        }
        # Send to stdin, read from stdout
```

**MCP Tools Used:**
- `plan.validate_structure` - Plan schema validation
- `plan.validate_step_contracts` - Step contract validation
- `plan.validate_ssot` - Single source of truth validation
- `registry.snapshot_query` - Registry state queries

### LangGraph → NPP CLI

**File:** `langgraph_integration/tools/npp_cli_wrapper.py`

Wraps existing NPP CLI commands:

```python
class NPPCLIWrapper:
    def execute(self, plan_path: Path, evidence_dir: Path) -> Tuple[int, str]:
        cmd = ["python3", str(self.cli_path), "execute",
               str(plan_path), "--evidence-dir", str(evidence_dir)]
        # Execute via subprocess

    def run_gates(self, plan_path: Path, evidence_dir: Path) -> Tuple[int, str]:
        cmd = ["python3", str(self.cli_path), "run-gates",
               str(plan_path), "--evidence-dir", str(evidence_dir)]
        # Execute GATE-000 through GATE-017 in dependency order
```

**NPP CLI Path:**
`LP_LONG_PLAN/newPhasePlanProcess/01260207201000001225_scripts/P_01260207233100000242_NEWPHASEPLANPROCESS_plan_cli.py`

**Commands Used:**
- `validate` - Schema validation
- `compile` - Normalize + regenerate navigation
- `execute` - Execute plan
- `run-gates` - Run all validation gates

### LangGraph → Registry Writer

**File:** `langgraph_integration/tools/registry_writer_client.py`

Records plan execution in governance registry:

```python
class RegistryWriterClient:
    def record_plan_execution(
        self,
        run_id: str,
        plan_id: str,
        registry_hash: str,  # CAS precondition
        actor: str = "langgraph_orchestrator"
    ) -> bool:
        patch = {
            "planning_executions": {
                run_id: {
                    "plan_id": plan_id,
                    "executed_at": datetime.now(timezone.utc).isoformat(),
                    "status": "completed"
                }
            }
        }
        return self.service.apply_patch(patch, registry_hash, actor, run_id)
```

**Registry Writer Path:**
`01260207201000001289_src/01260207201000001297_registry_writer/P_01260207233100000335_registry_writer_service_v2.py`

---

## Implementation Phases

### Phase 1: Core Infrastructure (Week 1)

**Tasks:**
1. Install LangGraph: `pip install langgraph`
2. Create directory structure
3. Implement `state_schema.py` with `PlanningState`
4. Implement `graph_builder.py` with basic graph
5. Implement `sqlite_checkpointer.py`
6. Create configuration files (YAML)
7. Unit tests for state transitions

**Verification:**
- Graph compiles without errors
- Checkpoint saves and loads
- State mutations tracked correctly

### Phase 2: AI Wrappers (Week 2)

**Tasks:**
1. Install AI CLIs:
   ```bash
   npm install -g @github/copilot
   npm install -g @openai/codex
   ```
2. Implement `codex_wrapper.py`
3. Implement `copilot_wrapper.py`
4. Implement `retry_policy.py`
5. Create JSON schemas in `schemas_langgraph/`
6. Implement `plan_quality_gate.py`
7. Implement envelope builder
8. Unit tests for wrappers

**Verification:**
- Codex produces schema-valid JSON
- Copilot JSON extraction works
- Retry policy handles rate limits
- Envelopes have SHA-256 hashes

### Phase 3: Planner-Critic Loop (Week 3)

**Tasks:**
1. Implement planner node
2. Implement gate node
3. Implement critic node
4. Implement refiner node
5. Implement routers (gate, convergence, retry)
6. Implement convergence metrics
7. Implement defect taxonomy
8. Add loop termination conditions
9. Integration tests

**Verification:**
- Loop converges on valid plan
- Loop terminates on max attempts
- Defects tracked properly
- Each iteration checkpointed

### Phase 4: Executor Integration (Week 4)

**Tasks:**
1. Implement MCP client
2. Implement NPP CLI wrapper
3. Implement executor node
4. Implement gates runner node
5. Implement registry writer client
6. Integration tests with existing NPP

**Verification:**
- MCP tools called via JSON-RPC
- NPP CLI commands execute
- GATE-000 through GATE-017 run
- Registry updates atomic

### Phase 5: Evidence and Audit (Week 5)

**Tasks:**
1. Implement evidence sealer node
2. Implement artifact hash store
3. Enhance checkpoint with artifact hashes
4. Implement checkpoint replay
5. Implement checkpoint viewer CLI
6. Add evidence bundle creation
7. Add audit trail generation

**Verification:**
- All artifacts have SHA-256 hashes
- Checkpoints include full provenance
- Replay produces identical results
- Evidence bundles tamper-evident

### Phase 6: Testing and Validation (Week 6)

**Tasks:**
1. Unit tests (state, routers, convergence)
2. Integration tests (loop, checkpoints, MCP, NPP, registry)
3. End-to-end tests (full workflow, gates, evidence)
4. Performance tests (convergence time, checkpoint overhead)
5. Documentation (architecture, API, troubleshooting, deployment)
6. Monitoring setup (metrics, alerts, dashboards)

**Verification:**
- Test coverage > 80%
- All integration tests pass
- E2E workflow completes
- Performance meets targets

---

## Configuration Files

### langgraph_config.yaml

```yaml
graph:
  name: "planning_workflow"
  version: "1.0.0"
  checkpointer: "sqlite"
  checkpoint_dir: ".state/langgraph_checkpoints"

convergence:
  max_iterations: 3
  threshold: 0.85
  delta_tolerance: 0.01

artifacts:
  base_dir: ".state/evidence/langgraph_runs"
  preserve_all_iterations: true
  hash_algorithm: "sha256"
```

### retry_policies.yaml

```yaml
retry:
  max_attempts: 3
  base_delay: 1.0
  max_delay: 60.0
  exponential_base: 2.0

  retryable_errors:
    - "rate limit"
    - "timeout"
    - "429"

  fail_fast_errors:
    - "unauthorized"
    - "401"
    - "api key"
```

### convergence_thresholds.yaml

```yaml
convergence:
  scorecard_weights:
    completeness: 0.25
    testability: 0.20
    risk_coverage: 0.20
    sequencing: 0.15
    gate_quality: 0.20

  minimum_scores:
    completeness: 4
    testability: 3
    risk_coverage: 3

  defect_blocking_severities:
    - "blocker"
```

---

## Authentication Setup

### Required Environment Variables

```bash
# Codex CLI (for Planner and Refiner)
export CODEX_API_KEY="sk-...your-openai-api-key..."

# Copilot CLI (for Critic)
export GH_TOKEN="ghp_...your-github-token..."
# OR
export GITHUB_TOKEN="ghp_...your-github-token..."
```

### GitHub Token Permissions

For Copilot CLI, create a fine-grained personal access token with:
- **Permission:** "Copilot Requests"
- **Repository access:** All repositories (or specific repos)

---

## Verification Strategy

### Unit Tests

```python
# tests/unit/test_state_transitions.py
def test_state_mutation():
    state = {"iteration": 0, "hop_counter": 0}
    new_state = planner_node.execute(state)
    assert new_state["iteration"] == 0
    assert new_state["hop_counter"] == 1
```

### Integration Tests

```python
# tests/integration/test_planner_critic_loop.py
def test_loop_convergence():
    state = initial_state
    for i in range(3):
        state = planner_node.execute(state)
        state = gate_node.execute(state)
        if state["gate_passed"]:
            state = critic_node.execute(state)
            if state["critic_verdict"] == "pass":
                break
        state = refiner_node.execute(state)

    assert state["critic_verdict"] == "pass"
    assert state["convergence_score"] >= 0.85
```

### End-to-End Test

```python
# tests/e2e/test_full_workflow.py
def test_full_planning_workflow():
    result = run_planning_workflow(
        request_path="tests/fixtures/planning_request.json",
        max_iterations=3
    )

    assert result["success"] is True
    assert result["converged"] is True
    assert Path(f".state/evidence/langgraph_runs/{result['run_id']}").exists()
```

### Manual Verification

```bash
# 1. Test Planner-Critic loop standalone
cd LP_LONG_PLAN/newPhasePlanProcess/01260207201000001221_Multi_CLI/ai_service_wrappers
./run_loop.sh inputs/planning_request.json

# 2. Test LangGraph orchestration
cd LP_LONG_PLAN/newPhasePlanProcess/01260207201000001221_Multi_CLI
python -m langgraph_integration.cli.langgraph_orchestrator \
  --request inputs/planning_request.json \
  --max-iterations 3

# 3. Verify checkpoint replay
python -m langgraph_integration.cli.checkpoint_viewer \
  --checkpoint-id <checkpoint_id> \
  --replay
```

---

## Success Criteria

The implementation is **100% COMPLETE** when:

1. ✅ **LangGraph graph compiles** without errors
2. ✅ **Planner-Critic loop converges** on valid plan within 3 iterations
3. ✅ **All 7 nodes execute** successfully (planner, gate, critic, refiner, executor, gates_runner, evidence_sealer)
4. ✅ **Checkpoints persist** to SQLite and can be replayed
5. ✅ **MCP server integration** works (5 tools callable)
6. ✅ **NPP CLI integration** works (execute, run-gates commands)
7. ✅ **GATE-000 through GATE-017** execute in dependency order
8. ✅ **Evidence artifacts** have SHA-256 hashes and sealed bundles
9. ✅ **Registry writer** records plan execution with CAS precondition
10. ✅ **Test suite passes** (unit, integration, e2e)
11. ✅ **Documentation complete** (architecture, API, troubleshooting, deployment)
12. ✅ **End-to-end workflow** runs from planning request → converged plan → execution → evidence sealing

---

## Key Constraints

**CRITICAL: Zero Changes to Existing Code**
- Do NOT modify MCP server
- Do NOT modify NPP CLI
- Do NOT modify gate scripts
- Do NOT modify registry writer
- All integration via NEW wrapper layer

**CRITICAL: LangGraph Never Touches**
- Git operations (worktree, merge, commit)
- Filesystem writes (except via CLI tools)
- Registry updates (except via registry writer client)
- Schema enforcement (use existing validators)

**CRITICAL: Artifact-Based Only**
- State stores paths + hashes, NOT content
- All communication via JSON files
- No free-text messages
- SHA-256 hash every artifact

---

## Troubleshooting Guide

### Issue: Codex CLI not found
```bash
npm install -g @openai/codex
# or
brew install --cask codex
```

### Issue: Copilot CLI authentication failed
```bash
# Check token
echo $GH_TOKEN

# Verify token has "Copilot Requests" permission
gh auth status
```

### Issue: MCP server not responding
```bash
# Test MCP server directly
echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | \
  python LP_LONG_PLAN/newPhasePlanProcess/01260207201000001217_mcp/P_01260207201000000493_server.py
```

### Issue: Convergence not happening
- Check convergence threshold (default 0.85)
- Verify scorecard weights sum to 1.0
- Review defect remediation templates
- Increase max_iterations if needed

---

This plan provides everything needed to implement the complete LangGraph Multi-Agent Orchestration System while preserving all existing governance primitives and enforcement infrastructure.
