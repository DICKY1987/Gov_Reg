# LangGraph Integration Architecture

## Multi-Agent Communication & Deterministic Collaboration Layer

This document describes how **LangGraph** can integrate into your deterministic, worktree-isolated, gate-enforced execution system to facilitate structured multi-agent communication, orchestration, and controlled iterative refinement — without compromising your existing invariants.

This is not a replacement architecture.
LangGraph becomes the **control-plane state machine and loop engine** layered above your existing deterministic runtime.

---

# 1. Architectural Positioning

## 1.1 Current System Characteristics (From Conversation)

Your system already includes:

* Git worktree isolation
* Single-writer merge discipline
* Declared write enforcement
* Preflight gates
* Runtime guardrails
* Post-run invariant validation
* Evidence-first artifact persistence
* Canonical hashing and deterministic IDs
* CLI-based tool execution
* Structured JSON/NDJSON artifacts
* Circuit breakers
* Planner–critic feedback loops
* Run directories under `.acms_runs/{run_id}/`

These are enforcement primitives.

LangGraph does not replace them.

LangGraph integrates at the orchestration layer.

---

# 2. What LangGraph Actually Contributes

LangGraph provides:

1. Explicit state graph execution
2. Cycles and conditional routing
3. Built-in retry policies
4. Checkpointing and persistence
5. Structured state mutation model
6. Tool abstraction layer
7. Deterministic edge-based transitions
8. Convergence loops
9. Agent-to-agent routing without implicit coupling
10. Replayable execution traces

In your system:

LangGraph becomes the deterministic **control engine** that decides:

* which CLI to call
* when to loop
* when to escalate
* when to stop
* when to retry
* when to fail

It does not enforce git invariants.
It orchestrates calls to tools that enforce them.

---

# 3. Control Plane vs Execution Plane

| Layer            | Responsibility                          |
| ---------------- | --------------------------------------- |
| LangGraph        | Control plane (state machine + routing) |
| CLI Tools        | Execution plane (actual work)           |
| Git Worktrees    | Isolation boundary                      |
| Gate Runner      | Deterministic validation                |
| Merge Integrator | Single-writer enforcement               |
| Evidence Sealer  | Post-run verification                   |

LangGraph coordinates these.

---

# 4. Integration Model

## 4.1 CLI Tools Become LangGraph Nodes

Each CLI becomes a Tool node:

* Input: structured JSON
* Output: structured JSON
* Side effects: artifacts in run directory
* No hidden stdout semantics
* No implicit state

LangGraph handles:

* input preparation
* routing decisions
* retry logic
* loop control
* termination

---

# 5. Message Passing Model

Your system already implies the correct approach:

Messages are artifacts.

Not free-text.

## Two Valid Message Transport Models

### A) Artifact-Based Handoff (Preferred)

Node A writes:

```
.acms_runs/{run_id}/stage_X/output.json
```

Node B consumes that file.

LangGraph stores only references in state:

```
{
  "artifact_path": "...",
  "hash": "...",
  "schema_version": "..."
}
```

Advantages:

* Replayable
* Hashable
* Audit-friendly
* Deterministic

### B) NDJSON Streaming (Optional for live events)

Used only for:

* progress streaming
* real-time monitoring

Final decision artifacts still persisted to disk.

---

# 6. LangGraph State Design

The state object should include:

```
{
  run_id,
  phase,
  hop_counter,
  workstream_id,
  artifact_index[],
  error_history[],
  retry_count,
  termination_flag,
  convergence_score,
  declared_write_manifest,
  invariant_status,
  merge_status
}
```

State changes only via node returns.

No mutation outside graph execution.

---

# 7. Integration Patterns

## 7.1 Planner–Critic–Refiner Loop

Nodes:

* Planner
* CLI executor
* Gate validator
* Critic
* Refiner

Flow:
Planner → Executor → Validator
If fail → Refiner → Executor
If pass → Continue

Loop ends when gates satisfied.

LangGraph manages:

* routing
* max iterations
* convergence threshold
* retry exhaustion behavior

---

## 7.2 Deterministic Workstream Execution Graph

Phases mapped to nodes:

1. Validate plan
2. Canonicalize + hash
3. Preflight repo safety
4. Build conflict graph
5. Provision worktrees
6. Dispatch workers
7. Collect outputs
8. Single-writer merge
9. Post-run invariant validation
10. Evidence sealing

Each phase is a node.

Conditional edges enforce:

* fail → repair
* repair fail → escalate
* invariant failure → rollback

---

## 7.3 Multi-Agent Collaborative Graph

Agents:

* Planner Agent
* Execution Agent
* Critic Agent
* Merge Agent
* Audit Agent

All agents operate through:

* deterministic tool nodes
* schema-bound messages
* no free-form memory mutation

LangGraph mediates communication through state.

---

# 8. Deterministic Routing

Routing logic should be:

* explicit
* rule-based
* state-driven
* not LLM-implicit

Example:

```
if gate_result.status == FAIL and retry_count < MAX:
    goto refiner
elif gate_result.status == FAIL:
    goto escalate
else:
    goto next_phase
```

LangGraph supports conditional edges natively.

---

# 9. Retry and Circuit Breakers

LangGraph retry policies can wrap:

* transient CLI failures
* network issues
* LLM timeouts

System-level retry logic still belongs in your deterministic guardrails:

* fingerprint repetition detection
* repeated invariant failure detection
* merge conflict recurrence
* declared write violation recurrence

LangGraph triggers circuit breaker transitions.

---

# 10. Persistence and Replay

LangGraph checkpointing enables:

* resume after crash
* replay of prior runs
* forensic audit
* deterministic simulation

Checkpoint storage must include:

* state snapshot
* artifact hashes
* node transition history
* routing decisions

Checkpoint data must reference artifact hashes, not raw file content.

---

# 11. Single-Writer Discipline

LangGraph must never:

* apply patches directly
* write to main
* bypass merge enforcement

Instead:

Node → call `merge_integrator_cli`
Return structured result:

```
{
  merge_status,
  conflicts[],
  applied_patches[],
  rollback_performed
}
```

LangGraph then routes accordingly.

---

# 12. Worktree Isolation Enforcement

LangGraph must:

* call worktree provisioning tool
* verify isolation
* ensure declared write manifest passed
* ensure no cross-worktree writes

Isolation validation remains external tool responsibility.

---

# 13. Gate Invocation Model

Gate runner is a tool node.

Return shape:

```
{
  gate_id,
  status,
  evidence_path,
  fingerprint,
  error_classification
}
```

LangGraph uses status to route.

---

# 14. Convergence Management

For multi-pass refinement:

State tracks:

* convergence score
* delta magnitude
* patch diff size
* gate failure count

Termination rules:

* score >= threshold
* max iterations
* no delta change across N loops

LangGraph handles cycle.

---

# 15. Artifact Registry Synchronization

LangGraph should not modify registries directly.

Instead:

Node → call registry tool
Registry tool returns structured diff
LangGraph routes based on validation

---

# 16. Conflict Graph Scheduling

LangGraph can orchestrate:

* topological sort
* parallel workstream eligibility
* barrier synchronization

Parallelism controlled by:

* conflict graph tool
* resource locking tool
* worktree map

LangGraph manages scheduling state.

---

# 17. Evidence Sealing

Final node:

* verify invariant set
* hash artifact tree
* generate run summary
* seal evidence bundle

LangGraph only routes to this node once all required prior gates pass.

---

# 18. What LangGraph Should Never Do

* Direct filesystem mutation
* Git merge logic
* Schema enforcement
* Declared write validation
* Hash canonicalization
* Invariant verification

It calls tools for these.

---

# 19. Safe Integration Model

LangGraph becomes:

Deterministic Orchestrator
not Autonomous Executor

It coordinates but does not enforce.

---

# 20. Multi-Agent Communication Model

Agents communicate through:

* shared state
* artifact references
* structured JSON

Not:

* memory buffers
* implicit chat histories
* untracked reasoning

---

# 21. Benefits to Your System

LangGraph adds:

* Structured multi-agent loops
* Explicit routing control
* Deterministic state transitions
* Built-in retry handling
* Replayable execution
* Clear separation of planning vs execution
* Scalable multi-agent orchestration

Without removing:

* worktree isolation
* single-writer merge discipline
* invariant enforcement
* evidence-first architecture

---

# 22. Recommended Deployment Pattern

1. Keep existing CLI system intact.
2. Wrap each CLI as LangChain Tool.
3. Implement LangGraph control graph.
4. Integrate checkpoint persistence.
5. Gradually migrate loop logic into graph nodes.
6. Leave enforcement logic in deterministic tools.

---

# 23. Final Assessment

LangGraph is highly compatible with your architecture if:

* It is used strictly as orchestration.
* All enforcement remains tool-based.
* All messages are artifact-backed.
* All routing is explicit.
* All state is persisted.

It strengthens:

* Multi-agent collaboration
* Controlled feedback loops
* Retry logic
* Convergence management
* Deterministic orchestration visibility

It does not replace:

* Your invariant framework
* Your git worktree model
* Your single-writer enforcement
* Your evidence-first discipline

---

