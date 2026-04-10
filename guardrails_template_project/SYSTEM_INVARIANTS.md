# SYSTEM_INVARIANTS.md
# Critical Invariants for ACMS + MINI_PIPE

These invariants MUST always be true for any run. They are the non-negotiable safety boundaries.

## Version
- **Document Version**: 1.0.0
- **Last Updated**: 2025-12-07
- **Enforcement**: Automated via guardrails system

---

## 1. ISOLATION INVARIANTS

### I-1: Branch Isolation
**Invariant**: All ACMS changes MUST happen in a dedicated worktree/branch, NEVER directly on `main`.

**Enforcement**:
- Pre-run: Verify current branch is not `main` OR create worktree
- Runtime: Block any operation that would modify `main` directly
- Post-run: Verify `main` has not changed

**Violation Response**: 
- HALT execution immediately
- Trigger `rollback` pattern
- Log as CRITICAL anti-pattern

### I-2: Clean State Entry
**Invariant**: Every run MUST start with a clean git state (no uncommitted changes in main branch).

**Enforcement**:
- Pre-run: `git status --porcelain` must be empty on main
- If dirty: offer to stash or fail

**Violation Response**:
- HALT execution
- Prompt for manual cleanup
- Do not auto-commit unknown changes

### I-3: Run Directory Containment
**Invariant**: All run artifacts MUST be contained in `.acms_runs/{run_id}/`.

**Enforcement**:
- Pre-run: Create run directory
- Runtime: Validate all artifact writes go to run directory
- Post-run: Verify no artifacts leaked outside

**Violation Response**:
- Log WARNING
- Move leaked artifacts to run directory
- Continue execution

---

## 2. GROUND TRUTH INVARIANTS

### GT-1: Test-Backed Changes
**Invariant**: Every AI-generated code change MUST be backed by ground truth verification.

**Ground Truth Hierarchy** (in order of preference):
1. Tests pass (`pytest_green`)
2. Static checks pass (`lint_check`, `schema_validate`)
3. Explicit file-level verification (manual review flag)

**Enforcement**:
- Post-change: MUST run at least one ground truth check
- Pattern specs define which checks are required
- No change can be marked "success" without verification

**Violation Response**:
- Mark task as FAILED
- Do not apply patch/commit
- Require manual intervention

### GT-2: Schema Compliance
**Invariant**: All structured data MUST conform to its JSON schema.

**Applies To**:
- Gap records
- Execution plans
- Run status
- Workstream definitions
- Pattern specs

**Enforcement**:
- Pre-execution: Validate plan against schema
- Runtime: Validate data before writing
- Post-execution: Validate run artifacts

**Violation Response**:
- HALT execution if plan is invalid
- FAIL task if runtime data is invalid
- Report schema errors with context

### GT-3: Observable Success
**Invariant**: A task cannot claim success without observable evidence.

**Required Evidence** (pattern-dependent):
- Exit code 0
- Expected files created/modified
- Tests passed
- Validation checks passed
- Ledger updated

**Enforcement**:
- Post-task: Executor verifies evidence exists
- No "I think it worked" claims accepted

**Violation Response**:
- Mark task FAILED even if AI claims success
- Log as anti-pattern (hallucinated success)
- Trigger verification pattern

---

## 3. PATTERN GOVERNANCE INVARIANTS

### PG-1: Patternless Work Forbidden
**Invariant**: Every task MUST have a `pattern_id` that exists in `PATTERN_INDEX.yaml`.

**Enforcement**:
- Pre-planning: Planner only creates tasks with valid patterns
- Runtime: Executor rejects tasks without pattern_id
- Validation: Schema requires pattern_id field

**Violation Response**:
- REJECT plan at compile time
- Do not execute task
- Log as configuration error

### PG-2: Pattern Spec Completeness
**Invariant**: Every pattern MUST have all required components.

**Required Components**:
- Spec file (`.spec.yaml`)
- Schema file (`.schema.json`)
- Executor function
- Entry in `PATTERN_INDEX.yaml`
- Guardrails block

**Enforcement**:
- Pattern registration: Validate all components exist
- Pre-run: Run `PAT-CHECK` validation
- CI/CD: Block merges if patterns incomplete

**Violation Response**:
- Disable pattern in index
- Block execution using that pattern
- Require pattern to be fixed

### PG-3: Guardrails Non-Bypassable
**Invariant**: Pattern guardrails CANNOT be bypassed or overridden at runtime.

**Enforcement**:
- Guardrails encoded in pattern spec (read-only at runtime)
- Executor enforces before/during/after task execution
- No "skip guardrails" flag allowed

**Violation Response**:
- HALT execution
- Log as CRITICAL security violation
- Require code review

---

## 4. CONSISTENCY INVARIANTS

### C-1: Gap-Task Consistency
**Invariant**: All tasks in a plan MUST trace to gaps; all gaps MUST have resolution tasks.

**Enforcement**:
- Post-planning: Validate gap_id references
- Runtime: Track gap → task → result mapping
- Post-run: Verify all gaps addressed or explicitly deferred

**Violation Response**:
- WARN if orphaned tasks
- FAIL if gaps missing resolutions
- Log inconsistency report

### C-2: Run Status Coherence
**Invariant**: `run_status.json` MUST be consistent with actual execution state.

**Consistency Checks**:
- Task counts match actual tasks
- Phase progression is valid (no skips)
- Timestamps are monotonic
- Status fields match reality

**Enforcement**:
- Post-phase: Validate status update
- Pre-phase: Verify status allows transition
- Post-run: Final coherence check

**Violation Response**:
- HALT if critical inconsistency
- Auto-correct minor issues
- Log discrepancies

### C-3: Ledger Integrity
**Invariant**: Patch ledger MUST maintain valid state machine transitions.

**Valid Transitions**:
```
created → validated → queued → applied → verified → committed
created → rejected
queued → failed
applied → rolled_back
```

**Enforcement**:
- Pre-transition: Validate state allows transition
- Post-transition: Update ledger atomically
- Runtime: Lock ledger during updates

**Violation Response**:
- REJECT invalid transition
- Log as data corruption
- Trigger recovery

---

## 5. RESOURCE LIMITS INVARIANTS

### RL-1: Bounded Execution
**Invariant**: No pattern can run indefinitely; all have timeouts.

**Limits**:
- Max execution time: 30 minutes per task
- Max file size: 10 MB
- Max files per task: 50 (configurable per pattern)
- Max LOC per change: 500 (configurable per pattern)

**Enforcement**:
- Runtime: Executor monitors execution time
- Pre-execution: Validate limits in pattern spec
- Timeout: Kill task and mark FAILED

**Violation Response**:
- Kill runaway task
- Mark as TIMEOUT
- Trigger cleanup pattern

### RL-2: Scope Boundaries
**Invariant**: Tasks can only touch files within their `path_scope`.

**Enforcement**:
- Pre-execution: Load path_scope from pattern
- Runtime: Validate all file operations against scope
- Post-execution: Verify no out-of-scope changes

**Violation Response**:
- BLOCK out-of-scope operation
- Mark task FAILED
- Log as security violation

### RL-3: Protected Paths Inviolate
**Invariant**: Certain paths MUST NEVER be modified by automation.

**Protected Paths**:
- `.git/objects/**`
- `.git/refs/heads/main`
- `PATTERN_INDEX.yaml`
- `schemas/*.schema.json`
- `SYSTEM_INVARIANTS.md`

**Enforcement**:
- Global guardrail applies to ALL patterns
- Runtime: Block any write to protected paths
- Post-run: Verify protected paths unchanged

**Violation Response**:
- HALT execution immediately
- ROLLBACK entire run
- Log as CRITICAL violation
- Alert operator

---

## 6. ANTI-PATTERN DETECTION INVARIANTS

### AP-1: Known Failures Detected
**Invariant**: System MUST detect and respond to known anti-patterns automatically.

**Detection Triggers**:
- Hallucinated success (claim success but tests fail)
- Planning loops (>3 planning attempts without progress)
- Incomplete implementation (files created but empty)
- Over-engineering (complexity metrics exceeded)
- Worktree contamination (main branch modified)

**Enforcement**:
- Post-task: Run anti-pattern detectors
- Post-phase: Check for systemic anti-patterns
- Pre-commit: Final anti-pattern scan

**Violation Response**:
- Auto-trigger appropriate runbook
- HALT if critical anti-pattern
- Self-heal if recoverable

### AP-2: Failure Transparency
**Invariant**: All failures MUST be logged with full context; no silent failures.

**Required Logging**:
- Error message
- Stack trace
- Task context (pattern_id, gap_id, files)
- Timestamps
- Retry history

**Enforcement**:
- Exception handlers must log
- No bare `except: pass`
- Failures update run_status.json

**Violation Response**:
- Code review required
- Log as monitoring gap
- Add explicit logging

### AP-3: Recovery Paths Exist
**Invariant**: For every failure mode, a recovery pattern MUST exist.

**Required Recovery Patterns**:
- Test failure → `self_heal` or `rollback`
- Patch failure → `rollback`
- Timeout → `cleanup` + `resume`
- Schema violation → `fix_schema` or `fail_fast`

**Enforcement**:
- Pattern specs declare failure modes
- Executor has recovery mapping
- Runbooks provide recovery steps

**Violation Response**:
- HALT if no recovery path
- Create runbook for new failure mode
- Resume after recovery defined

---

## 7. VERIFICATION & AUDIT INVARIANTS

### V-1: Audit Trail Complete
**Invariant**: Every pattern execution MUST be logged to audit trail.

**Logged Fields**:
- Pattern ID
- Timestamp (start, end)
- Inputs
- Outputs
- Guardrail check results
- Success/failure status

**Enforcement**:
- Executor writes to `pattern_audit.jsonl`
- One line per task execution
- Atomic append (no partial writes)

**Violation Response**:
- WARN if logging fails
- Continue execution
- Report audit gap

### V-2: Validation Gates Enforced
**Invariant**: Pre-execution and post-execution validation gates MUST pass.

**Pre-Execution Gates**:
- Pattern exists in index
- Pattern enabled
- Guardrails valid
- Prechecks passed

**Post-Execution Gates**:
- Postchecks passed
- No protected paths touched
- Anti-patterns clear

**Enforcement**:
- Executor runs gates automatically
- Gate failure blocks progression
- All results logged

**Violation Response**:
- FAIL task if any gate fails
- Log which gate failed
- Do not proceed

### V-3: Manual Review Hooks
**Invariant**: High-risk operations MUST have manual review hooks.

**High-Risk Operations**:
- Bulk renames (>50 files)
- Protected path requests
- Schema changes
- Pattern additions

**Enforcement**:
- Pattern spec flags `requires_manual_review: true`
- Executor pauses and prompts
- Continue only after approval

**Violation Response**:
- PAUSE execution
- Await manual approval
- Timeout after 24h → FAIL

---

## ENFORCEMENT SUMMARY

### Automated Enforcement
✅ **Pre-run validation** (`validate_everything.py`)  
✅ **Runtime guardrails** (executor + pattern specs)  
✅ **Post-run verification** (anti-pattern detection + schema validation)  

### Manual Enforcement
🔍 **Code review** (pattern specs, guardrail additions)  
🔍 **Incident review** (when invariants violated)  
🔍 **Periodic audits** (quarterly invariant compliance check)  

### Escalation Path
1. **Automated detection** → Log + auto-recover if possible
2. **Auto-recovery fails** → HALT + alert operator
3. **Operator intervention** → Manual fix + runbook update
4. **Persistent violations** → Disable pattern + code review

---

## INVARIANT TESTING

Each invariant MUST have:
- ✅ Unit test (verify enforcement code works)
- ✅ Integration test (verify enforcement in real run)
- ✅ Violation test (verify response to violation is correct)

Test suite: `tests/test_invariants.py`

---

## DOCUMENT GOVERNANCE

- **Owner**: ACMS Core Team
- **Review Frequency**: Monthly or after any critical incident
- **Change Process**: 
  1. Propose invariant addition/change
  2. Implement enforcement
  3. Write tests
  4. Update this document
  5. Code review + merge
- **Version Control**: This file is protected (cannot be modified by automation)

---

**Remember**: Invariants are not suggestions. They are the bedrock of system safety. Violating them is a bug, not a feature request.
