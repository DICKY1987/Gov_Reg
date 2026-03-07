# Mini Pipeline - Core Components Reference

**Generated**: 2025-12-06  
**Purpose**: Essential components for minimal working pipeline  
**Source**: Extracted from CORE_SCRIPTS_CATALOG.md

This document describes the core components required for a minimal functional pipeline implementation.

---

## Table of Contents

1. [Core Engine Orchestration & Execution](#core-engine-orchestration--execution)
2. [Resilience / Safety Layer](#resilience--safety-layer)
3. [CLI Entrypoint](#cli-entrypoint)
4. [Patch Lifecycle](#patch-lifecycle)
5. [Automation Triggers (Pipeline Wiring)](#automation-triggers-pipeline-wiring)

---

## Core Engine Orchestration & Execution

### `orchestrator.py`
**DOC_ID**: `DOC-CORE-ENGINE-ORCHESTRATOR-151`  
**Workstream**: WS-03-01A  
**Location**: `core/engine/orchestrator.py`

Main orchestration logic for executing workstreams. Manages run lifecycle, state transitions, and event emission. The orchestrator is the central component that coordinates workstream execution.

**Key Features**:
- Run lifecycle management
- State machine transitions
- Event emission and handling
- ULID generation (deterministic mode support)

**Critical For**:
- Coordinating all pipeline phases
- Managing run state transitions
- Event-driven workflow coordination

---

### `scheduler.py`
**DOC_ID**: `DOC-CORE-ENGINE-SCHEDULER-158`  
**Workstream**: WS-03-01C  
**Location**: `core/engine/scheduler.py`

Schedules and executes tasks with dependency resolution. Handles parallel and sequential execution based on task dependencies.

**Key Features**:
- Task dependency resolution
- Parallel execution coordination
- Sequential execution handling
- Task status tracking (pending, ready, running, completed, failed)

**Critical For**:
- Task dependency management
- Parallel task execution
- Wave-based execution planning

---

### `router.py`
**DOC_ID**: `DOC-CORE-ENGINE-ROUTER-157`  
**Workstream**: WS-03-01B  
**Location**: `core/engine/router.py`

Routes tasks to appropriate tools based on `router_config.json`. Supports multiple routing strategies and capability matching.

**Key Features**:
- Task-to-tool routing
- Multiple routing strategies
- Capability matching
- Round-robin and weighted routing
- File-backed state persistence

**Critical For**:
- Tool selection and routing
- Load balancing across tools
- Capability-based task assignment

---

### `executor.py`
**DOC_ID**: `DOC-CORE-ENGINE-EXECUTOR-149`  
**Location**: `core/engine/executor.py`

Parallel execution workers that run scheduled workstream tasks with isolation and telemetry capture. Handles actual task execution with adapter integration.

**Key Features**:
- Parallel task execution
- Tool adapter integration
- Result capture and telemetry
- Subprocess adapter support

**Critical For**:
- Actual task execution
- Tool adapter invocation
- Result collection

---

### `tools.py`
**DOC_ID**: `DOC-CORE-ENGINE-TOOLS-161`  
**Location**: `core/engine/tools.py`

Tool adapter layer for AI Development Pipeline. Provides config-driven external tool execution with subprocess handling, timeouts, error capture, and result tracking.

**Key Features**:
- Template-based command rendering
- Subprocess handling
- Timeout management
- Standardized result reporting

**Critical For**:
- External tool execution
- Command-line tool integration
- Result standardization

---

### `process_spawner.py`
**DOC_ID**: `DOC-CORE-ENGINE-PROCESS-SPAWNER-154`  
**Workstream**: Phase I-1 WS-I2  
**Location**: `core/engine/process_spawner.py`

Worker process spawning for parallel execution. Manages subprocess creation, sandboxing, and lifecycle for tool adapters.

**Key Features**:
- Worker process spawning
- Sandbox environment creation
- Process lifecycle management
- Environment variable handling

**Critical For**:
- Isolated task execution
- Sandbox creation
- Worker process management

---

## Resilience / Safety Layer

### `resilience/circuit_breaker.py`
**DOC_ID**: `DOC-CORE-RESILIENCE-CIRCUIT-BREAKER-186`  
**Workstream**: WS-03-03A  
**Location**: `core/engine/resilience/circuit_breaker.py`

Circuit breaker pattern implementation. Prevents cascading failures by stopping requests to failing services.

**States**:
- `CLOSED`: Normal operation, requests pass through
- `OPEN`: Too many failures, requests blocked
- `HALF_OPEN`: Testing if service recovered

**Critical For**:
- Preventing cascading failures
- Tool failure isolation
- Service health monitoring

---

### `resilience/retry.py`
**DOC_ID**: `DOC-CORE-RESILIENCE-RETRY-189`  
**Workstream**: WS-03-03A  
**Location**: `core/engine/resilience/retry.py`

Retry logic with exponential backoff and jitter. Provides retry strategies for failed operations.

**Key Features**:
- Exponential backoff
- Jitter for collision avoidance
- Configurable max attempts
- Strategy pattern implementation

**Critical For**:
- Transient failure handling
- Network error recovery
- Backoff strategy management

---

### `resilience/resilient_executor.py`
**DOC_ID**: `DOC-CORE-RESILIENCE-RESILIENT-EXECUTOR-188`  
**Workstream**: WS-03-03A  
**Location**: `core/engine/resilience/resilient_executor.py`

Combines circuit breakers and retry logic for robust task execution.

**Key Features**:
- Circuit breaker integration
- Retry strategy management
- Per-tool failure tracking
- Auto-recovery

**Critical For**:
- Robust task execution
- Combined resilience patterns
- Tool-level failure handling

---

### `circuit_breakers.py`
**DOC_ID**: `DOC-CORE-ENGINE-CIRCUIT-BREAKERS-144`  
**Workstream**: Phase 6 (PH-06)  
**Location**: `core/engine/circuit_breakers.py`

Circuit breakers, retries, and oscillation detection. Lightweight utilities to load breaker config, compute error/diff signatures, and decide whether to continue FIX attempts.

**Key Features**:
- Pure Python stdlib implementation
- Deterministic defaults when config missing
- Error signature computation
- Diff hash calculation
- Oscillation detection

**Critical For**:
- Error pattern detection
- Fix attempt management
- Oscillation prevention

---

### `recovery.py`
**DOC_ID**: (Not specified)  
**Workstream**: Phase 6 bridge  
**Location**: `core/engine/recovery.py`

Failure handling and retry orchestration. Coordinates retries after error recovery.

**Key Features**:
- Recovery policy configuration
- Task retry coordination
- Event-driven recovery
- Backoff strategy support

**Critical For**:
- Error recovery orchestration
- Retry coordination
- Recovery policy enforcement

---

## CLI Entrypoint

### `orchestrator_cli.py`
**DOC_ID**: `DOC-CORE-CLI-ORCHESTRATOR-001`  
**Location**: `core/cli/orchestrator_cli.py`

Orchestrator CLI for workstream execution. Click-based command-line interface for running workstreams.

**Key Features**:
- Plan execution
- Phase specification
- Workstream filtering
- Timeout configuration

**Usage**:
```bash
orchestrator-cli --plan plans/example.json --phase phase1 --workstream WS-001
```

**Critical For**:
- User interaction
- Plan-based execution
- Command-line workflow

---

## Patch Lifecycle

### `patch_converter.py`
**DOC_ID**: `DOC-CORE-ENGINE-PATCH-CONVERTER-152`  
**Location**: `core/engine/patch_converter.py`

Converts tool outputs to unified diff format. Standardizes patches from different tools (aider, custom tools).

**Key Features**:
- Tool-specific to unified patch conversion
- Patch format standardization
- Metadata tracking

**Critical For**:
- Patch normalization
- Multi-tool support
- Unified patch format

---

### `patch_ledger.py`
**DOC_ID**: `DOC-CORE-ENGINE-PATCH-LEDGER-153`  
**Workstream**: WS-NEXT-002-002  
**Location**: `core/engine/patch_ledger.py`

Manages patch lifecycle with state machine transitions. Tracks patch validation, application, verification, and quarantine.

**State Machine**:
- `created → validated → queued → applied → verified → committed`
- `any → apply_failed` (retry or quarantine)
- `any → quarantined` (safety)
- `any → dropped` (reject)

**Critical For**:
- Patch lifecycle management
- Quality gate enforcement
- Patch state tracking

---

## Automation Triggers (Pipeline Wiring)

### `monitoring_trigger.py`
**DOC_ID**: `DOC-CORE-AUTOMATION-MONITORING-TRIGGER-001`  
**Workstream**: WS1-005  
**Location**: `core/automation/monitoring_trigger.py`

Auto-start monitoring on `RUN_CREATED` event. Watches `orchestration.db` for new runs and auto-launches monitoring UI.

**Key Features**:
- Database polling
- Run detection
- Monitoring UI auto-launch
- Event-driven activation

**Critical For**:
- Automated monitoring
- Event-driven UI launch
- Run tracking

---

### `request_builder_trigger.py`
**DOC_ID**: `DOC-CORE-AUTOMATION-REQUEST-BUILDER-TRIGGER-001`  
**Workstream**: WS1-003  
**Location**: `core/automation/request_builder_trigger.py`

Auto-trigger request builder on `PLANNING_COMPLETE` event. Watches for `PLANNING_COMPLETE` flag and automatically invokes request builder.

**Key Features**:
- Flag file watching
- Metadata extraction
- Request builder invocation
- Automated phase transition

**Critical For**:
- Phase 1 → Phase 2 transition
- Automated request building
- Pipeline continuity

---

### `router_trigger.py`
**DOC_ID**: `DOC-CORE-AUTOMATION-ROUTER-TRIGGER-001`  
**Workstream**: WS1-004  
**Location**: `core/automation/router_trigger.py`

Auto-trigger router on `task_queue.json` changes. Watches for task queue updates and automatically invokes router.

**Key Features**:
- File modification monitoring
- Queue change detection
- Router auto-invocation
- Continuous watching

**Critical For**:
- Phase 3 → Phase 4 transition
- Automated routing
- Queue-based triggering

---

## Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     MINI PIPELINE FLOW                       │
└─────────────────────────────────────────────────────────────┘

┌──────────────────┐
│  orchestrator    │  ← Entry point (orchestrator_cli.py)
│     _cli.py      │
└────────┬─────────┘
         │
         v
┌──────────────────┐
│  orchestrator.py │  ← Run lifecycle, state machine
└────────┬─────────┘
         │
         v
┌──────────────────┐
│   scheduler.py   │  ← Dependency resolution, task waves
└────────┬─────────┘
         │
         v
┌──────────────────┐
│    router.py     │  ← Tool routing, capability matching
└────────┬─────────┘
         │
         v
┌──────────────────┐
│   executor.py    │  ← Task execution
└────────┬─────────┘
         │
         v
┌──────────────────┐     ┌─────────────────────┐
│     tools.py     │ ──> │ process_spawner.py  │
└──────────────────┘     └─────────────────────┘
         │                        │
         v                        v
   [External Tools]          [Sandboxed Workers]

                 │
                 v
         ┌───────────────┐
         │  RESILIENCE   │
         │    LAYER      │
         ├───────────────┤
         │ circuit_      │
         │   breaker.py  │
         │ retry.py      │
         │ resilient_    │
         │   executor.py │
         │ circuit_      │
         │   breakers.py │
         │ recovery.py   │
         └───────────────┘
                 │
                 v
         ┌───────────────┐
         │ PATCH MGMT    │
         ├───────────────┤
         │ patch_        │
         │   converter.py│
         │ patch_        │
         │   ledger.py   │
         └───────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   AUTOMATION TRIGGERS                        │
├─────────────────────────────────────────────────────────────┤
│  monitoring_trigger.py  (RUN_CREATED → Monitor UI)         │
│  request_builder_trigger.py  (PLANNING_COMPLETE → Phase 2) │
│  router_trigger.py  (task_queue.json → Router)             │
└─────────────────────────────────────────────────────────────┘
```

---

## Minimal Implementation Checklist

### Phase 1: Core Execution
- [ ] `orchestrator.py` - Run management
- [ ] `scheduler.py` - Task scheduling
- [ ] `router.py` - Tool routing
- [ ] `executor.py` - Task execution
- [ ] `tools.py` - Tool adapter layer

### Phase 2: Process Management
- [ ] `process_spawner.py` - Worker spawning

### Phase 3: Resilience
- [ ] `resilience/circuit_breaker.py` - Failure isolation
- [ ] `resilience/retry.py` - Retry logic
- [ ] `resilience/resilient_executor.py` - Combined patterns

### Phase 4: Error Recovery
- [ ] `circuit_breakers.py` - Error detection
- [ ] `recovery.py` - Recovery coordination

### Phase 5: User Interface
- [ ] `orchestrator_cli.py` - CLI entrypoint

### Phase 6: Patch Management
- [ ] `patch_converter.py` - Patch normalization
- [ ] `patch_ledger.py` - Lifecycle tracking

### Phase 7: Automation
- [ ] `monitoring_trigger.py` - Monitor automation
- [ ] `request_builder_trigger.py` - Phase 2 automation
- [ ] `router_trigger.py` - Phase 4 automation

---

## Dependencies Between Components

```
orchestrator_cli.py
    └── orchestrator.py
            ├── scheduler.py
            ├── router.py
            └── executor.py
                    ├── tools.py
                    │   └── process_spawner.py
                    └── resilient_executor.py
                            ├── circuit_breaker.py
                            └── retry.py

recovery.py
    └── resilient_executor.py

patch_ledger.py
    └── patch_converter.py

Automation Triggers (parallel, event-driven)
    ├── monitoring_trigger.py
    ├── request_builder_trigger.py
    └── router_trigger.py
```

---

## Configuration Requirements

### Required Config Files
1. `router_config.json` - Tool routing rules
2. `config/tool_profiles/*.yaml` - Tool capability definitions
3. Circuit breaker config (inline or YAML)
4. Retry policy config (inline or YAML)

### Required State Files
1. `.state/orchestration.db` - Run and task state
2. `.state/task_queue.json` - Scheduled tasks
3. `.state/routing_decisions.json` - Routing results
4. `.state/PLANNING_COMPLETE` - Phase transition flag

---

## Summary

**Total Components**: 16 scripts  
**Critical Path**: orchestrator → scheduler → router → executor → tools  
**Safety Layer**: 5 resilience components  
**Automation**: 3 trigger scripts  

This minimal set provides:
- ✅ Complete orchestration flow
- ✅ Resilient execution with retries and circuit breakers
- ✅ Patch lifecycle management
- ✅ Automated phase transitions
- ✅ CLI interface for user interaction

---

## Document Version

- **Version**: 1.0
- **Last Updated**: 2025-12-06
- **Source**: CORE_SCRIPTS_CATALOG.md
- **Purpose**: Minimal pipeline implementation reference
