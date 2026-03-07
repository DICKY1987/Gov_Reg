# DOC_AIDER_CONTRACT - Aider Tool Integration Contract v1

## Overview

This document defines the **mandatory contract** for all Aider tool integrations in ACMS/MINI_PIPE.

Every Aider invocation MUST go through a contract-compliant adapter that:
1. Uses standardized `ToolRunRequestV1` / `ToolRunResultV1` structures
2. Never raises exceptions (all failures encoded in exit codes)
3. Records tool runs as structured events
4. Enforces timeouts and resource limits
5. Operates within defined worktree boundaries

## Contract Version

**Version:** `AIDER_CONTRACT_V1`  
**Status:** Mandatory for all Aider usage  
**Enforced by:** `MINI_PIPE_tools.run_aider()`

---

## 1. Tool Profile

### 1.1 Tool ID
```
tool_id: "aider"
```

### 1.2 Command Template
```bash
aider --no-auto-commits --yes --model {model_name} --message-file {prompt_file}
```

**Required flags:**
- `--no-auto-commits`: Prevent automatic Git commits (we control commits)
- `--yes`: Auto-accept changes (non-interactive mode)
- `--model {model_name}`: Specify LLM model
- `--message-file {prompt_file}`: Read instructions from file

**Optional flags:**
- `--edit-format {format}`: Specify edit format (diff, whole, etc.)
- `--read {file}`: Add file to context (read-only)
- `{files...}`: Files to edit (from `file_scope`)

### 1.3 Environment Variables
```bash
AIDER_NO_AUTO_COMMITS=1    # Hard-coded safety
AIDER_MODEL={model_name}   # Optional override
```

### 1.4 Execution Constraints
- **Default timeout:** 1800 seconds (30 minutes)
- **Working directory:** Worktree root from `GitWorkspaceRefV1.root_path`
- **File scope:** Only files in `ExecutionRequestV1.file_scope` may be edited
- **No network access** during execution (if sandboxed)

---

## 2. Request Contract: `ToolRunRequestV1`

### 2.1 Structure
```python
@dataclass
class ToolRunRequestV1:
    tool_id: str = "aider"
    cmd: List[str]  # Full command with resolved arguments
    cwd: str        # Absolute path to worktree root
    env: Dict[str, str]  # Environment variables
    timeout_seconds: int = 1800
    stdin_data: Optional[str] = None
    context: Dict[str, Any]  # For logging (run_id, ws_id, task_id, etc.)
```

### 2.2 Example
```python
request = ToolRunRequestV1(
    tool_id="aider",
    cmd=[
        "aider",
        "--no-auto-commits",
        "--yes",
        "--model", "gpt-4",
        "--message-file", "/tmp/prompt_abc123.txt",
        "src/module.py",
        "tests/test_module.py"
    ],
    cwd="/path/to/worktree",
    env={
        "AIDER_NO_AUTO_COMMITS": "1",
        "AIDER_MODEL": "gpt-4"
    },
    timeout_seconds=1800,
    context={
        "run_id": "run-001",
        "ws_id": "ws-acms-001",
        "task_id": "task-003",
        "pattern_id": "aider_refactor"
    }
)
```

---

## 3. Result Contract: `ToolRunResultV1`

### 3.1 Structure
```python
@dataclass
class ToolRunResultV1:
    tool_id: str = "aider"
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    timed_out: bool = False
    started_at: str  # ISO 8601 UTC
    completed_at: str  # ISO 8601 UTC
    
    @property
    def success(self) -> bool:
        return self.exit_code == 0
```

### 3.2 Exit Code Semantics

| Exit Code | Meaning | Action |
|-----------|---------|--------|
| `0` | Success | Aider completed normally |
| `1-255` | Tool error | Aider failed (check stderr) |
| `-1` | Timeout | Process killed after timeout |
| `-2` | Binary not found | Aider executable not in PATH |
| `-3` | Execution error | OS-level error (permissions, etc.) |

**CRITICAL:** The adapter MUST NEVER raise exceptions. All errors encoded in exit codes.

### 3.3 Example Success
```python
result = ToolRunResultV1(
    tool_id="aider",
    exit_code=0,
    stdout="Applied changes to src/module.py\nTests passing\n",
    stderr="",
    duration_seconds=45.3,
    timed_out=False,
    started_at="2025-12-07T01:00:00Z",
    completed_at="2025-12-07T01:00:45Z"
)
assert result.success == True
```

### 3.4 Example Timeout
```python
result = ToolRunResultV1(
    tool_id="aider",
    exit_code=-1,
    stdout="Partial output before timeout...\n",
    stderr="Process timed out after 1800 seconds",
    duration_seconds=1800.0,
    timed_out=True,
    started_at="2025-12-07T01:00:00Z",
    completed_at="2025-12-07T01:30:00Z"
)
assert result.success == False
```

---

## 4. Adapter Implementation: `run_aider()`

### 4.1 Signature
```python
def run_aider(request: ToolRunRequestV1, context: Dict[str, Any]) -> ToolRunResultV1:
    """
    Execute Aider according to DOC_AIDER_CONTRACT.
    
    NEVER raises exceptions - all failures encoded in ToolRunResultV1.
    
    Args:
        request: Tool execution request
        context: Execution context (for logging/events)
    
    Returns:
        ToolRunResultV1 with exit_code, stdout, stderr, duration
    """
```

### 4.2 Implementation Requirements

1. **Validate request:**
   - Check `tool_id == "aider"`
   - Verify `cwd` exists
   - Ensure `cmd[0]` is `"aider"`

2. **Prepare environment:**
   - Merge `os.environ` with `request.env`
   - Force `AIDER_NO_AUTO_COMMITS=1`

3. **Execute subprocess:**
   - Use `subprocess.run()` with `timeout`, `capture_output=True`
   - Handle `TimeoutExpired` → exit_code=-1
   - Handle `FileNotFoundError` → exit_code=-2
   - Handle other exceptions → exit_code=-3

4. **Record event:**
   - Create `LogEventV1` for the tool run
   - Create `ToolRunResultV1` for the result
   - Store in run record / event log

5. **Return result:**
   - Always return `ToolRunResultV1` (never raise)

---

## 5. Integration with Execution Patterns

### 5.1 Pattern Routing

Patterns that require Aider MUST declare it in `PATTERN_INDEX.yaml`:

```yaml
aider_refactor:
  enabled: true
  spec_path: "patterns/aider_refactor.spec.yaml"
  executor: "MINI_PIPE_executor.execute_aider_refactor"
  category: "code_modification"
  guardrails:
    allowed_tools:
      - aider
    path_scope:
      include:
        - "**/*.py"
      exclude:
        - "**/__pycache__/**"
        - "**/venv/**"
```

### 5.2 Router Decision

In `MINI_PIPE_router.py`, when a task's `operation_kind` requires Aider:

```python
if task.operation_kind == "EXEC-AIDER-EDIT":
    tool_request = build_aider_tool_request(
        model_name=task.inputs.get("model", "gpt-4"),
        prompt_file=task.inputs["prompt_file"],
        file_scope=task.file_scope,
        workspace=task.workspace,
        context=task.context
    )
    result = run_aider(tool_request, context)
    return map_tool_result_to_execution_result(result)
```

### 5.3 Pattern Executor

Pattern executors MUST NOT call Aider directly:

```python
# ❌ WRONG - Direct subprocess call
subprocess.run(["aider", ...])  # VIOLATES CONTRACT

# ✅ CORRECT - Via contract
tool_request = ToolRunRequestV1(...)
result = run_tool(tool_request)  # Uses run_aider internally
```

---

## 6. Event & Audit Trail

Every Aider execution MUST generate:

1. **LogEventV1:** Tool invocation event
   ```python
   log = LogEventV1(
       level="INFO",
       message=f"Running aider: {' '.join(request.cmd)}",
       context={"request_id": request_id, "tool_id": "aider"}
   )
   ```

2. **ToolRunResultV1:** Execution result (as defined above)

3. **PatchRecordV1:** For each file modified
   ```python
   patch = PatchRecordV1(
       patch_id=f"patch-{uuid4()}",
       file_path="src/module.py",
       operation="edit",
       diff=unified_diff,
       tool_id="aider",
       request_id=request_id
   )
   ```

4. **RunRecordV1:** Complete execution record (optional, for full audit)

---

## 7. Testing Requirements

### 7.1 Unit Tests

- `test_build_aider_tool_request()`: Verify template resolution
- `test_run_aider_success()`: Verify successful execution
- `test_run_aider_timeout()`: Verify timeout handling (exit_code=-1)
- `test_run_aider_not_found()`: Verify missing binary (exit_code=-2)
- `test_run_aider_never_raises()`: Verify no exceptions escape

### 7.2 Integration Tests

- Full ACMS pipeline with Aider pattern
- Workstream with multiple Aider tasks
- Error recovery after Aider failure

---

## 8. Migration Checklist

For existing Aider usage:

- [ ] Replace all direct `subprocess` calls with `run_aider()`
- [ ] Replace ad-hoc command building with `build_aider_tool_request()`
- [ ] Remove all `try/except` around Aider calls (use exit codes instead)
- [ ] Add `tool_id="aider"` to relevant patterns in `PATTERN_INDEX.yaml`
- [ ] Update router to use `ToolRunRequestV1` / `ToolRunResultV1`
- [ ] Add event logging for all Aider executions
- [ ] Write unit tests per §7.1

---

## 9. Non-Compliance Examples

### 9.1 ❌ Direct Subprocess Call
```python
# VIOLATES CONTRACT
result = subprocess.run(["aider", "--yes", "file.py"])
```

### 9.2 ❌ Raising Exceptions
```python
# VIOLATES CONTRACT
if result.exit_code != 0:
    raise RuntimeError("Aider failed")  # NO!
```

### 9.3 ❌ Ad-Hoc Result Structure
```python
# VIOLATES CONTRACT
return {"success": True, "output": stdout}  # Use ToolRunResultV1
```

### 9.4 ❌ Hardcoded Paths
```python
# VIOLATES CONTRACT
cwd = "/home/user/project"  # Use GitWorkspaceRefV1.root_path
```

---

## 10. Compliance Verification

Run contract validator:
```bash
python contracts/validate_aider_contract.py
```

This checks:
- All Aider calls go through `run_aider()`
- No direct subprocess calls to `aider`
- All results use `ToolRunResultV1`
- Event logging is present

---

## References

- `contracts/uet_submodule_io_contracts.py` - Data structures
- `MINI_PIPE_tools.py` - Adapter implementation
- `PATTERN_INDEX.yaml` - Pattern declarations
- `UET_ABSTRACTION_GUIDELINES.md` - Module boundary rules
