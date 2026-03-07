# ACMS/MINI_PIPE Guardrails System

## Overview

The guardrails system ensures that ACMS and MINI_PIPE can only operate through well-defined patterns with built-in safety boundaries, validation checks, and anti-pattern detection. This prevents dangerous operations, enforces best practices, and enables automatic recovery from known failure modes.

## Core Principle

**The system can only act through patterns + templates that have pre-defined limits, checks, and success criteria.**

No ad-hoc execution. No "creative" AI detours. Only well-tested, validated patterns from the registry.

---

## Architecture

### 1. **PATTERN_INDEX.yaml** - The Authority

**Location**: `PATTERN_INDEX.yaml`

The authoritative registry of ALL execution patterns. Every task MUST reference a `pattern_id` from this index.

**Key Features**:
- Pattern definitions with guardrails
- Global enforcement rules
- Protected paths
- Anti-pattern detection config

**Validation**: 
```bash
python validate_everything.py
```

### 2. **SYSTEM_INVARIANTS.md** - The Rules

**Location**: `SYSTEM_INVARIANTS.md`

Documents all invariants that MUST be true for any run. Organized by category:

- **I-**: Isolation invariants (branch, state, containment)
- **GT-**: Ground truth invariants (tests, schema, evidence)
- **PG-**: Pattern governance invariants (no patternless work, spec completeness)
- **C-**: Consistency invariants (gap-task alignment, status coherence)
- **RL-**: Resource limits invariants (timeouts, scope, protected paths)
- **AP-**: Anti-pattern detection invariants (known failures detected)
- **V-**: Verification & audit invariants (audit trail, validation gates)

**Enforcement**: Automated via `guardrails.py` + manual code review

### 3. **Pattern Specs** - The Blueprints

**Location**: `patterns/*.spec.yaml`

Each pattern has a spec file defining:
- What it does
- What tools it can use
- What paths it can touch
- What limits it has
- What checks must pass before/after
- What it's forbidden from doing

**Example**: `patterns/atomic_create.spec.yaml`

**Schema**: `schemas/pattern_spec.schema.json`

### 4. **Anti-Pattern Runbooks** - The Defense

**Location**: `anti_patterns/AP_*.yaml`

Each known failure mode has a runbook defining:
- Symptoms (log patterns, metrics)
- Detection rules (automated checks)
- Root causes (why this happens)
- Prevention strategies (how to avoid)
- Automatic response (what to do when detected)
- Verification (how to confirm it's resolved)

**Examples**:
- `AP_HALLUCINATED_SUCCESS.yaml` - AI claims success but tests fail
- `AP_PLANNING_LOOP.yaml` - Stuck in planning without progress

### 5. **guardrails.py** - The Enforcer

**Location**: `guardrails.py`

Python module that enforces guardrails at runtime:

**Classes**:
- `PatternGuardrails` - Validates pattern execution against specs
- `AntiPatternDetector` - Detects known anti-patterns
- `GuardrailViolation` - Represents a violation

**Key Functions**:
- `pre_execution_checks()` - Run before task execution
- `post_execution_checks()` - Run after task execution
- `validate_path_scope()` - Check file paths are in scope
- `validate_tool_usage()` - Check tools are allowed
- `check_forbidden_operations()` - Block forbidden ops

### 6. **validate_everything.py** - The Validator

**Location**: `validate_everything.py`

Validates ALL artifacts before/during/after a run:

**Validates**:
- Gap registry
- Execution plans
- Run status
- Workstreams
- Pattern specs
- Pattern index
- Schemas

**Usage**:
```bash
# Validate latest run
python validate_everything.py

# Validate specific run
python validate_everything.py --run-id 20251207001431_2E134BDB6F61

# Verbose output
python validate_everything.py --verbose
```

---

## How Guardrails Work

### Pre-Execution Phase

1. **Plan Compilation**
   - Every task MUST have `pattern_id`
   - Pattern MUST exist in `PATTERN_INDEX.yaml`
   - Pattern MUST be enabled
   - Plan validated against schema

2. **Pre-Flight Checks** (per task)
   - Pattern exists and enabled ✓
   - Guardrails block loaded ✓
   - Required prechecks defined ✓
   - File paths within `path_scope` ✓
   - Tools in `allowed_tools` list ✓
   - No `forbidden_operations` ✓

**If any check fails**: Task is BLOCKED before execution

### Runtime Phase

3. **Execution Monitoring**
   - Timeout enforcement (pattern-specific)
   - File operation validation (path scope)
   - Tool usage tracking
   - Output capture for verification

4. **Post-Execution Checks** (per task)
   - Required postchecks executed ✓
   - Change limits not exceeded ✓
   - Observable evidence exists ✓
   - No hallucinated success ✓
   - Protected paths unchanged ✓

**If any check fails**: Task marked FAILED even if AI claims success

### Post-Run Phase

5. **Anti-Pattern Detection**
   - Check for hallucinated success
   - Check for planning loops
   - Check for incomplete implementations
   - Check for worktree contamination

6. **Artifact Validation**
   - Run status coherent
   - Gap-task consistency
   - Ledger integrity
   - Audit trail complete

7. **Recovery Actions** (if needed)
   - Auto-trigger recovery patterns
   - Generate diagnostic reports
   - Escalate to operator if critical

---

## Pattern Guardrails Reference

### `allowed_tools`
List of tool IDs this pattern can use.

**Example**:
```yaml
allowed_tools:
  - file_create
  - syntax_check
  - pytest
```

**Enforcement**: Runtime check before tool invocation

### `path_scope`
Glob patterns defining what paths this pattern can touch.

**Example**:
```yaml
path_scope:
  include:
    - "**/*.py"
    - "**/*.json"
  exclude:
    - ".git/**"
    - "PATTERN_INDEX.yaml"
```

**Enforcement**: Runtime check before file operation

### `max_changes`
Numeric limits on scope of changes.

**Example**:
```yaml
max_changes:
  files: 5
  lines: 200
  hunks: 10
```

**Enforcement**: Post-execution check against actual changes

### `required_prechecks`
Checks that MUST pass before execution starts.

**Example**:
```yaml
required_prechecks:
  - git_status_clean
  - pytest_installed
  - no_file_exists
```

**Enforcement**: Pre-execution validation gate

### `required_postchecks`
Checks that MUST pass after execution completes.

**Example**:
```yaml
required_postchecks:
  - file_exists
  - syntax_valid
  - tests_pass
```

**Enforcement**: Post-execution validation gate

### `forbidden_operations`
Operations this pattern is NEVER allowed to do.

**Example**:
```yaml
forbidden_operations:
  - git_push
  - delete_tests
  - modify_pattern_index
```

**Enforcement**: Runtime block if operation attempted

---

## Anti-Pattern Detection

### How It Works

1. **Detection Rules** (in runbook YAML)
   - Defined as conditions on task/run state
   - Checked at phase boundaries
   - Triggered by metric thresholds or log patterns

2. **Automatic Response**
   - Log anti-pattern detection with full context
   - Override incorrect status (e.g., hallucinated success)
   - Trigger recovery pattern (e.g., rollback, self_heal)
   - Escalate if critical or repeated

3. **Verification**
   - Confirm anti-pattern resolved
   - Prevent recurrence
   - Update runbook if new variant found

### Currently Implemented

#### AP_HALLUCINATED_SUCCESS
**Symptoms**: AI claims success but tests fail or expected files missing

**Detection**:
- `task.status == "success" AND task.verification.exit_code != 0`
- `task.status == "success" AND expected_outputs missing`

**Response**:
- Override status to FAILED
- Do not apply changes
- Re-queue with stricter verification

#### AP_PLANNING_LOOP
**Symptoms**: 3+ planning attempts without any patches applied

**Detection**:
- `planning_attempts > 3 AND patches_applied == 0`
- `phase == "planning" AND elapsed_time > 30min`

**Response**:
- Force plan commitment with reduced scope
- Defer non-critical gaps
- Proceed to execution with best-effort plan

---

## Global Guardrails

Applied to ALL patterns, cannot be overridden:

### Protected Paths
**NEVER** modified by automation:
- `.git/objects/**`
- `.git/refs/heads/main`
- `PATTERN_INDEX.yaml`
- `schemas/*.schema.json`
- `SYSTEM_INVARIANTS.md`

**Violation**: HALT execution, ROLLBACK entire run

### Absolute Limits
- Max execution time: 30 minutes per task
- Max file size: 10 MB
- Max concurrent tasks: 5
- Max retry attempts: 3

**Violation**: Kill task, mark TIMEOUT/LIMIT_EXCEEDED

### Required Environment
- `git` available
- `python` available
- Repository root accessible

**Violation**: HALT before execution starts

---

## Integration Points

### ACMS Controller
```python
from guardrails import PatternGuardrails

# During planning phase
guardrails = PatternGuardrails(Path("PATTERN_INDEX.yaml"))

for task in plan.tasks:
    is_valid, error = guardrails.validate_pattern_exists(task.pattern_id)
    if not is_valid:
        raise PlanValidationError(error)
```

### MINI_PIPE Executor
```python
from guardrails import PatternGuardrails, AntiPatternDetector

# Before task execution
passed, violations = guardrails.pre_execution_checks(
    pattern_id=task.pattern_id,
    task_data=task.inputs
)
if not passed:
    task.status = "BLOCKED"
    return

# After task execution
passed, violations = guardrails.post_execution_checks(
    pattern_id=task.pattern_id,
    task_result=result
)
if not passed:
    task.status = "FAILED"
    trigger_recovery_pattern(violations)
```

### Anti-Pattern Detection
```python
from guardrails import AntiPatternDetector

detector = AntiPatternDetector(Path("anti_patterns"))

# After task completes
detections = detector.detect_all({
    "task_status": task.status,
    "verification": task.verification,
    "run_stats": run_stats
})

for detection in detections:
    handle_anti_pattern(detection)
```

---

## Minimal Implementation Checklist

To get guardrails operational:

- [x] **PATTERN_INDEX.yaml** created with 3-5 core patterns
- [x] **SYSTEM_INVARIANTS.md** documented
- [x] **Pattern specs** for core patterns (atomic_create, pytest_green, etc.)
- [x] **Anti-pattern runbooks** for top 2-3 failure modes
- [x] **guardrails.py** module with enforcement logic
- [x] **validate_everything.py** enhanced with pattern validation
- [ ] **Pattern spec schema** enforcement in executor
- [ ] **Pre/post execution hooks** in MINI_PIPE_executor.py
- [ ] **Anti-pattern detection** in ACMS controller
- [ ] **Tests** for guardrail enforcement

---

## Testing Guardrails

### Unit Tests
```bash
# Test guardrail enforcement
python -m pytest tests/test_guardrails.py

# Test anti-pattern detection
python -m pytest tests/test_antipattern_hallucinated_success.py
python -m pytest tests/test_antipattern_planning_loop.py
```

### Integration Tests
```bash
# Test full workflow with guardrails
python -m pytest tests/integration/test_guardrails_workflow.py
```

### Validation
```bash
# Validate all artifacts
python validate_everything.py --verbose

# Test guardrails module directly
python guardrails.py
```

---

## Future Enhancements

### Planned Features
1. **Pattern templates** - Generate new patterns from templates
2. **Guardrail profiles** - Strict/relaxed modes for different contexts
3. **Runtime telemetry** - Detailed metrics on guardrail effectiveness
4. **Auto-runbook generation** - Learn new anti-patterns from failures
5. **Visual dashboard** - Real-time guardrail status display

### Research Directions
1. **ML-based anti-pattern detection** - Learn from incident patterns
2. **Adaptive limits** - Adjust max_changes based on historical data
3. **Formal verification** - Prove invariants hold mathematically
4. **Chaos testing** - Deliberately violate guardrails to test responses

---

## FAQ

**Q: What happens if a pattern doesn't have a guardrails block?**  
A: The pattern fails schema validation and is disabled in PATTERN_INDEX.yaml.

**Q: Can guardrails be overridden in an emergency?**  
A: No. If you need to bypass guardrails, you must:
1. Create a new pattern with appropriate guardrails
2. Add it to PATTERN_INDEX.yaml
3. Use that pattern instead

**Q: What if I need to touch a protected path?**  
A: Protected paths are protected for a reason. If you truly need to modify one:
1. Propose the change in a design review
2. Update SYSTEM_INVARIANTS.md with justification
3. Add a new pattern with explicit permission
4. Require manual review for that pattern

**Q: How do I add a new anti-pattern runbook?**  
A: 
1. Copy existing runbook as template
2. Fill in symptoms, detection rules, response
3. Add to `anti_patterns/` directory
4. Update `guardrails.py` detector if custom logic needed
5. Add tests for detection and response

**Q: Do guardrails slow down execution?**  
A: Minimally. Pre/post checks add ~100ms per task. Validation is only done once per run. The safety is worth it.

---

## Support

**Issues**: Open GitHub issue with tag `guardrails`  
**Questions**: Check `SYSTEM_INVARIANTS.md` first, then ask in discussions  
**Contributing**: See `CONTRIBUTING.md` for pattern development guidelines

---

**Remember**: Guardrails are not obstacles—they're the foundation of trust. They let the system operate autonomously with confidence.
