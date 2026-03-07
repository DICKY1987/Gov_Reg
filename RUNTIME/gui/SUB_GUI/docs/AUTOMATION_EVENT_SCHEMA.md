# DOC_ID: DOC-SCRIPT-1186
# Automation Event Schema - AUTOMATION_EVENT.v1

**Doc ID**: DOC-SCHEMA-AUTOMATION-EVENT-V1-010
**Version**: 1.0
**Format**: JSONL (JSON Lines)
**Status**: Production

---

## Overview

The AUTOMATION_EVENT.v1 schema defines the standard format for automation events emitted by subsystems. Events are written to `logs/events/events.jsonl` in JSONL format (one JSON object per line).

---

## Schema Definition

### Required Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `event_id` | string | Unique event identifier | `"evt-abc12345"` |
| `timestamp_utc` | string | UTC timestamp (ISO 8601) | `"2026-01-01T12:00:00.000Z"` |
| `subsystem` | string | Subsystem emitting event | `"SUB_DOC_ID"` |
| `severity` | string | Event severity level | `"INFO"` |
| `subject` | string | Event subject (file, task, etc.) | `"src/module.py"` |
| `summary` | string | Brief event description | `"File detected"` |

### Optional Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `step_id` | string | Step identifier | `"FILE_DETECTED"` |
| `correlation_id` | string | ID for related events | `"chain-abc123"` |
| `automation_chain_id` | string | Automation chain name | `"DOC_ID_ASSIGNMENT"` |
| `sequence_id` | integer | Sequence number in chain | `1` |
| `details` | object | Additional event data | `{"file_size": 1024}` |

---

## Severity Levels

| Level | Use Case | Example |
|-------|----------|---------|
| `DEBUG` | Detailed diagnostic info | Variable values, internal state |
| `INFO` | Informational messages | File detected, task started |
| `NOTICE` | Normal but significant | Assignment completed, validation passed |
| `WARN` | Warning conditions | Missing optional field, deprecated API |
| `ERROR` | Error conditions | Task failed, validation error |
| `CRITICAL` | Critical failures | System crash, data corruption |

---

## Complete Example

```json
{
  "event_id": "evt-a1b2c3d4",
  "timestamp_utc": "2026-01-01T14:23:45.678Z",
  "subsystem": "SUB_DOC_ID",
  "severity": "INFO",
  "step_id": "DOC_ID_ASSIGNED",
  "subject": "src/core/module.py",
  "summary": "Doc ID assigned to file",
  "correlation_id": "chain-xyz789",
  "automation_chain_id": "FILE_PROCESSING",
  "sequence_id": 2,
  "details": {
    "doc_id": "DOC-CORE-MODULE-001",
    "category": "core",
    "file_size_bytes": 2048,
    "line_count": 85
  }
}
```

---

## Event Types by Subsystem

### SUB_DOC_ID Events

#### FILE_DETECTED
```json
{
  "step_id": "FILE_DETECTED",
  "severity": "INFO",
  "subject": "path/to/file.py",
  "summary": "New file detected",
  "details": {
    "file_type": ".py",
    "size_bytes": 1024
  }
}
```

#### DOC_ID_ASSIGNED
```json
{
  "step_id": "DOC_ID_ASSIGNED",
  "severity": "NOTICE",
  "subject": "path/to/file.py",
  "summary": "Doc ID assigned",
  "details": {
    "doc_id": "DOC-CORE-FILE-001",
    "category": "core"
  }
}
```

#### VALIDATION_FAILED
```json
{
  "step_id": "VALIDATION_FAILED",
  "severity": "WARN",
  "subject": "path/to/file.py",
  "summary": "Doc ID validation failed",
  "details": {
    "rule": "metadata_complete",
    "missing_fields": ["author", "created"]
  }
}
```

### PHASE_5 Events

#### TASK_START
```json
{
  "step_id": "TASK_START",
  "severity": "INFO",
  "subject": "task-001",
  "summary": "Task started: lint",
  "details": {
    "task_kind": "lint",
    "tool_id": "ruff",
    "run_id": "run-12345"
  }
}
```

#### TASK_COMPLETE
```json
{
  "step_id": "TASK_COMPLETE",
  "severity": "INFO",
  "subject": "task-001",
  "summary": "Task completed: lint",
  "details": {
    "task_kind": "lint",
    "exit_code": 0,
    "duration_ms": 150.5
  }
}
```

#### TASK_FAILED
```json
{
  "step_id": "TASK_FAILED",
  "severity": "ERROR",
  "subject": "task-003",
  "summary": "Task failed: test",
  "details": {
    "task_kind": "test",
    "error": "AssertionError: test_feature failed",
    "exit_code": 1,
    "duration_ms": 2345.6
  }
}
```

### SUB_CLP Events

#### CLP_GENERATED
```json
{
  "step_id": "CLP_GENERATED",
  "severity": "INFO",
  "subject": "PHASE_1_PLANNING",
  "summary": "CLP generated for phase",
  "details": {
    "phase_id": "PHASE_1",
    "line_count": 42,
    "file_path": "PHASE_1_PLANNING/CLP.yaml"
  }
}
```

---

## Event Chains

Related events can be linked via `correlation_id` and `automation_chain_id`.

### Example Chain: Doc ID Assignment

```jsonl
{"event_id":"evt-001","correlation_id":"chain-abc","automation_chain_id":"DOC_ID_ASSIGNMENT","sequence_id":1,"step_id":"FILE_DETECTED","subject":"src/file.py","summary":"File detected"}
{"event_id":"evt-002","correlation_id":"chain-abc","automation_chain_id":"DOC_ID_ASSIGNMENT","sequence_id":2,"step_id":"CATEGORY_DETERMINED","subject":"src/file.py","summary":"Category: core"}
{"event_id":"evt-003","correlation_id":"chain-abc","automation_chain_id":"DOC_ID_ASSIGNMENT","sequence_id":3,"step_id":"DOC_ID_ASSIGNED","subject":"src/file.py","summary":"Assigned DOC-CORE-FILE-001"}
{"event_id":"evt-004","correlation_id":"chain-abc","automation_chain_id":"DOC_ID_ASSIGNMENT","sequence_id":4,"step_id":"REGISTRY_UPDATED","subject":"src/file.py","summary":"Registry updated"}
```

All events share the same `correlation_id` and `automation_chain_id`, with incrementing `sequence_id`.

---

## File Format: JSONL

Events are written in **JSONL** (JSON Lines) format:
- One complete JSON object per line
- No commas between objects
- Newline (`\n`) separates events
- Easy to append
- Simple to parse line-by-line

### Example File
```jsonl
{"event_id":"evt-001","timestamp_utc":"2026-01-01T12:00:00Z","subsystem":"SUB_DOC_ID","severity":"INFO","subject":"file1.py","summary":"File detected","details":{}}
{"event_id":"evt-002","timestamp_utc":"2026-01-01T12:00:05Z","subsystem":"PHASE_5","severity":"INFO","subject":"task-001","summary":"Task started","details":{"tool":"ruff"}}
{"event_id":"evt-003","timestamp_utc":"2026-01-01T12:00:10Z","subsystem":"PHASE_5","severity":"INFO","subject":"task-001","summary":"Task completed","details":{"exit_code":0}}
```

### Parsing Example (Python)
```python
import json

events = []
with open("events.jsonl", "r") as f:
    for line in f:
        if line.strip():
            event = json.loads(line)
            events.append(event)
```

---

## Emitting Events

### Using event_emitter.py

```python
from ui_core.event_emitter import (
    emit_automation_event,
    EventSeverity
)

# Basic event
emit_automation_event(
    subsystem="MY_SUBSYSTEM",
    summary="Something happened",
    subject="target",
    severity=EventSeverity.INFO,
    step_id="MY_STEP",
    details={"key": "value"}
)
```

### Using Convenience Functions

```python
from ui_core.event_emitter import (
    emit_file_detected_event,
    emit_task_started_event,
    emit_task_completed_event,
    emit_task_failed_event
)

# File detected
emit_file_detected_event("SUB_DOC_ID", "src/file.py")

# Task lifecycle
emit_task_started_event("PHASE_5", "task-001", "lint", tool_id="ruff")
emit_task_completed_event("PHASE_5", "task-001", "lint", exit_code=0)
emit_task_failed_event("PHASE_5", "task-002", "test", error="Failed")
```

### Using Event Chains

```python
from ui_core.event_emitter import EventChain

with EventChain("MY_AUTOMATION", "MY_SUBSYSTEM") as chain:
    chain.emit("Step 1", "subject1")
    chain.emit("Step 2", "subject2")
    chain.emit("Completed", "subject3")
```

---

## Validation

### Required Field Validation

All events must include:
- ✅ `event_id` (auto-generated)
- ✅ `timestamp_utc` (auto-generated)
- ✅ `subsystem` (provided)
- ✅ `severity` (provided, defaults to INFO)
- ✅ `subject` (provided)
- ✅ `summary` (provided)

### Severity Validation

Must be one of:
- `DEBUG`, `INFO`, `NOTICE`, `WARN`, `ERROR`, `CRITICAL`

### Timestamp Format

Must be ISO 8601 UTC:
- `YYYY-MM-DDTHH:MM:SS.sssZ`
- Example: `2026-01-01T14:23:45.678Z`

---

## Best Practices

### 1. Use Appropriate Severity

| Severity | When to Use |
|----------|-------------|
| DEBUG | Internal diagnostics only |
| INFO | Normal operational events |
| NOTICE | Significant but normal events (assignments, completions) |
| WARN | Potential issues, non-critical errors |
| ERROR | Failures requiring attention |
| CRITICAL | System-threatening failures |

### 2. Meaningful Summaries

✅ **Good**: `"Task completed: lint with ruff (150ms)"`
❌ **Bad**: `"Task done"`

✅ **Good**: `"Doc ID assigned: DOC-CORE-MODULE-001"`
❌ **Bad**: `"Success"`

### 3. Useful Details

Include context in `details`:
```json
{
  "details": {
    "file_size_bytes": 2048,
    "line_count": 85,
    "doc_id": "DOC-CORE-MODULE-001",
    "category": "core",
    "duration_ms": 150.5
  }
}
```

### 4. Use Event Chains for Related Events

Link related events with `correlation_id`:
```python
with EventChain("FILE_PROCESSING", "SUB_DOC_ID") as chain:
    chain.emit("File detected", file_path)
    chain.emit("Doc ID assigned", file_path, details={"doc_id": doc_id})
    chain.emit("Registry updated", file_path)
```

### 5. Thread Safety

The event emitter is thread-safe. Multiple processes/threads can emit concurrently.

---

## Monitoring Events

### GUI Panel

The **Automation Events** panel displays events with:
- Filtering by subsystem
- Filtering by severity
- Time-ordered display (newest first)
- Details expansion

### Command Line

```powershell
# View all events
Get-Content logs\events\events.jsonl | ConvertFrom-Json | Format-Table

# Filter by subsystem
Get-Content logs\events\events.jsonl | ConvertFrom-Json | Where-Object {$_.subsystem -eq "PHASE_5"}

# Filter by severity
Get-Content logs\events\events.jsonl | ConvertFrom-Json | Where-Object {$_.severity -eq "ERROR"}

# Count by subsystem
Get-Content logs\events\events.jsonl | ConvertFrom-Json | Group-Object subsystem
```

---

## Version History

### v1.0 (2026-01-01)
- Initial production release
- Standard event schema
- JSONL format
- Thread-safe emitter

---

**Schema Version**: 1.0
**Status**: Production
**Last Updated**: 2026-01-01
