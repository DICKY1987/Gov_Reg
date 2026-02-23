# File Watcher MVP - Requirements Reconciliation

**Document ID:** 01999000042260124558  
**Date:** 2026-01-26  
**Version:** 1.0  
**Status:** REQUIREMENTS RECONCILIATION

---

## Purpose

Reconcile conflicts between:
1. **Past implementations** (16-digit prefix watcher)
2. **Current requirements spec** (FR-1 through FR-10)
3. **Capability Registry** (CAP_* classifications)
4. **Unified Registry needs** (20-digit file_id, GEU tracking)

---

## Key Conflicts Identified

### Conflict 1: File ID Format (16-digit vs 20-digit)

**Past Implementation:**
- Used 16-digit numeric prefix
- Pattern: `{16_DIGIT_PREFIX}_{name}`
- Pre-DOC_ID stage architecture

**Current Requirements:**
- Uses 20-digit file_id
- Pattern: `01` + 17-digit timestamp + 3-digit suffix
- Python: `P_{20_DIGIT_ID}_{name}.py`
- Other: `{20_DIGIT_ID}_{name}.ext`

**Capability Registry:**
- Marks 16-digit prefix as `CAP_IDENTITY_PREFIX_ASSIGN` (optional/"could")
- No explicit 20-digit capability defined

**Resolution:**
- ✅ **MVP SHALL use 20-digit file_id format**
- ✅ **Extract from filename using patterns in unified registry**
- ✅ **If missing, allocate via P_01999000042260124027_id_allocator.py**
- ❌ **Do NOT implement 16-digit prefix logic**

---

### Conflict 2: Registry Target (Multiple vs Single)

**Past Implementation:**
- Monitored state directory with multiple JSON files
- Tracked events.jsonl log
- CSV-oriented in some versions

**Current Requirements:**
- Single unified registry: `01999000042260124552_unified_governance_registry.json`
- 16 top-level keys
- 102 files, 10 GEUs
- Atomic updates with locking

**Resolution:**
- ✅ **MVP SHALL update single unified registry only**
- ✅ **Use atomic_json_write with file locking**
- ✅ **Maintain backward compatibility with registry schema**

---

### Conflict 3: Logging Requirements (Optional vs Must)

**Capability Registry:**
- `CAP_JOURNAL_JSONL_APPEND_ONLY` marked as **"must"**
- Append-only event journal is baseline requirement

**Requirements Spec FR-9:**
- Logging categorized as FR-9 (not in Phase 1 MVP)
- Prioritized MEDIUM
- Placed in Phase 4: Production Hardening

**Resolution:**
- ✅ **MVP SHALL include basic JSONL event logging**
- ✅ **Log file: `01999000042260124559_file_watcher_events.jsonl`**
- ✅ **Minimum fields: timestamp, event_type, file_path, file_id, action, result**
- ⚠️ **Full audit trail (FR-9.2) deferred to Phase 4**

---

### Conflict 4: Directory Events

**Requirements Spec FR-1.2:**
- Explicitly lists directory create/delete/rename events
- Implies directory tracking in registry

**Capability Registry:**
- Lists file events only (create/modify/delete/move)
- No explicit directory event capability

**Unified Registry:**
- Only tracks files (102 entries)
- No directory entries

**Resolution:**
- ✅ **MVP SHALL detect directory events**
- ✅ **BUT ignore them (no action taken)**
- ✅ **Log directory events for audit purposes**
- ⚠️ **Directory tracking deferred to future phase**
- **Rationale:** Registry tracks files only; directories are implied by paths

---

### Conflict 5: Stability Gating

**Past Implementation:**
- File stability checker (polls size/mtime until stable)
- Checks exclusive lock availability
- Timeout: 15 seconds

**Capability Registry:**
- `CAP_STABILITY_GATE` marked as **"must"**
- Core behavioral guarantee

**Requirements Spec:**
- Not explicitly in Phase 1 MVP
- Implied by FR-1.4 (debouncing)

**Resolution:**
- ✅ **MVP SHALL include stability gating**
- ✅ **Wait for file size/mtime to stabilize (2 consecutive checks)**
- ✅ **Check interval: 500ms**
- ✅ **Timeout: 10 seconds**
- ✅ **Failure: log error and skip file**

---

### Conflict 6: Loop Prevention

**Capability Registry:**
- Loop prevention marked as **"must"**
- Don't trigger on own edits

**Requirements Spec:**
- Not explicitly in Phase 1 MVP
- Implied in FR-2.5 (atomic updates)

**Past Implementation:**
- Tracked last registry write timestamp
- Suppressed events within 5 seconds of write

**Resolution:**
- ✅ **MVP SHALL implement loop prevention**
- ✅ **Track last write timestamp of registry file**
- ✅ **Ignore registry modification events within 5 seconds of own writes**
- ✅ **Prevent infinite update loops**

---

## Unified MVP Scope (Phase 1 - REVISED)

### Must Have (Capability Registry "must" + Phase 1 FR)

#### Core Monitoring
- [x] **CAP_DETECT_EVENTS** - Detect file create/modify/delete/rename
- [x] **CAP_FILTER_IGNORE** - Ignore temp files, .git, __pycache__
- [x] **CAP_DEBOUNCE_COALESCE** - Debounce events (2s default)
- [x] **CAP_STABILITY_GATE** - Wait for file stability before processing
- [x] **CAP_LOOP_PREVENTION** - Don't trigger on own registry writes

#### Registry Operations
- [x] **FR-2.1** - File creation handling (detect ID, classify, add entry)
- [x] **FR-2.5** - Atomic registry updates (temp file + rename)
- [x] **FR-3.1** - Extract 20-digit file_id from filename
- [x] **FR-3.2** - Detect layer (EXECUTION, DOCUMENTATION, DATA, etc.)
- [x] **FR-3.3** - Detect artifact_kind (PYTHON_MODULE, JSON, MARKDOWN, etc.)

#### Logging
- [x] **CAP_JOURNAL_JSONL_APPEND_ONLY** - Append-only event log
- [x] Log events: timestamp, event_type, path, file_id, action, result

#### Locking
- [x] **CAP_LOCKING_SHARED_REGISTRIES** - File locking for concurrent access

#### Operations
- [x] **FR-10.1** - Start/stop/status commands
- [x] **FR-10.2** - Dry-run mode (--dry-run flag)

### Explicitly Deferred (Post-MVP)

#### Phase 2: Full Event Handling
- [ ] FR-2.2 - File modification handling (update timestamps)
- [ ] FR-2.3 - File deletion handling (remove entries)
- [ ] FR-2.4 - File rename handling (update paths)

#### Phase 3: GEU Integration
- [ ] FR-4.1 - GEU membership detection
- [ ] FR-4.2 - GEU completeness checking
- [ ] FR-4.3 - GEU anchor validation
- [ ] FR-5.1 - Duplicate file_id detection
- [ ] FR-5.3 - Advanced concurrent modification handling

#### Phase 4: Production Hardening
- [ ] FR-6 - Performance optimization
- [ ] FR-7.1 - Crash recovery
- [ ] FR-7.3 - Registry backups
- [ ] FR-7.4 - Health monitoring
- [ ] FR-9.2 - Full audit trail
- [ ] FR-9.3 - Log rotation

---

## MVP Feature Matrix

| Feature | Capability Registry | Requirements FR | Past Implementation | MVP Status |
|---------|-------------------|-----------------|-------------------|-----------|
| **File Event Detection** | Must (CAP_DETECT_EVENTS) | FR-1.2 | ✅ Implemented | ✅ INCLUDE |
| **20-digit file_id** | Not defined | FR-3.1 | ❌ Used 16-digit | ✅ INCLUDE |
| **Ignore Filtering** | Must (CAP_FILTER_IGNORE) | FR-1.3 | ✅ Implemented | ✅ INCLUDE |
| **Debouncing** | Must (CAP_DEBOUNCE_COALESCE) | FR-1.4 | ✅ Implemented | ✅ INCLUDE |
| **Stability Gate** | Must (CAP_STABILITY_GATE) | Implied | ✅ Implemented | ✅ INCLUDE |
| **Loop Prevention** | Must | Implied | ✅ Implemented | ✅ INCLUDE |
| **JSONL Event Log** | Must (CAP_JOURNAL_JSONL) | FR-9.1 (Phase 4) | ✅ Implemented | ✅ INCLUDE |
| **File Locking** | Must (CAP_LOCKING) | FR-2.5 | ✅ Implemented | ✅ INCLUDE |
| **File Creation** | - | FR-2.1 | Partial (rename only) | ✅ INCLUDE |
| **Layer Detection** | - | FR-3.2 | ❌ Not implemented | ✅ INCLUDE |
| **Artifact Kind Detection** | - | FR-3.3 | ❌ Not implemented | ✅ INCLUDE |
| **Start/Stop Control** | - | FR-10.1 | ✅ Implemented | ✅ INCLUDE |
| **Dry-run Mode** | - | FR-10.2 | ✅ Implemented | ✅ INCLUDE |
| **File Modification** | - | FR-2.2 | ❌ Not needed | ⏸️ DEFER Phase 2 |
| **File Deletion** | - | FR-2.3 | ❌ Not needed | ⏸️ DEFER Phase 2 |
| **File Rename** | - | FR-2.4 | ✅ Implemented | ⏸️ DEFER Phase 2 |
| **GEU Integration** | - | FR-4.* | ❌ Not implemented | ⏸️ DEFER Phase 3 |
| **Duplicate Detection** | - | FR-5.1 | ❌ Not implemented | ⏸️ DEFER Phase 3 |
| **Crash Recovery** | - | FR-7.1 | ❌ Not implemented | ⏸️ DEFER Phase 4 |
| **Registry Backups** | - | FR-7.3 | ❌ Not implemented | ⏸️ DEFER Phase 4 |

---

## Revised MVP Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 File System Events (watchdog)                │
│              Create/Modify/Delete/Rename/MovedTo             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Event Filter (CAP_FILTER_IGNORE)            │
│  - Match: P_*.py, *.json, *.md, 01999*.* patterns          │
│  - Ignore: *.tmp, .git/*, __pycache__/*, registry itself   │
│  - Directory events: Detect but ignore                      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│           Event Queue (CAP_DEBOUNCE_COALESCE)                │
│  - Dict keyed by path: {path: {event, timestamp}}          │
│  - Debounce: 2 seconds after last event                    │
│  - UPSERT semantics (coalesce rapid events)                │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│            Stability Gate (CAP_STABILITY_GATE)               │
│  - Poll file size/mtime every 500ms                         │
│  - Require 2 consecutive stable samples                     │
│  - Timeout: 10 seconds                                      │
│  - Skip file on timeout (log error)                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                Loop Prevention Check                         │
│  - Check if event is on registry file                       │
│  - Check if < 5 seconds since last write                    │
│  - If yes: Skip and log (prevent infinite loop)             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              File ID Extraction (20-digit)                   │
│  - Python: Extract from P_{ID}_{name}.py                   │
│  - Other: Extract from {ID}_{name}.ext                     │
│  - Validate: Exactly 20 digits, starts with 01             │
│  - If missing: Allocate via id_allocator.py                │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Metadata Detection                              │
│  - Layer: By extension and directory path                   │
│  - Artifact Kind: By extension                              │
│  - Relative Path: From repo root                            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│         Registry Update (CAP_LOCKING_SHARED_REGISTRIES)      │
│  CREATED event only (MVP scope):                            │
│    1. Check if file_id already exists in registry          │
│    2. If exists: Skip (already tracked)                    │
│    3. If new: Build entry dict                             │
│    4. Load registry with file lock                         │
│    5. Append entry to files[] array                        │
│    6. Sort files[] by file_id                              │
│    7. Write atomically (temp + rename)                     │
│    8. Update last_write_timestamp                          │
│                                                             │
│  Other events (modify/delete/rename): Log only, no action  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│      Event Log (CAP_JOURNAL_JSONL_APPEND_ONLY)               │
│  - File: 01999000042260124559_file_watcher_events.jsonl    │
│  - Format: One JSON object per line                         │
│  - Fields: timestamp, event_type, path, file_id,           │
│            action, result, error (if failed)                │
└─────────────────────────────────────────────────────────────┘
```

---

## MVP Implementation Plan

### Files to Create

1. **P_01999000042260124560_file_watcher_mvp.py**
   - Main watcher implementation
   - Uses watchdog library
   - Implements all "must" capabilities

2. **P_01999000042260124561_file_watcher_config.json**
   - Configuration file
   - Repository roots, patterns, timeouts

3. **01999000042260124559_file_watcher_events.jsonl**
   - Event log (created automatically)
   - Append-only format

### Dependencies

```python
# Required
import json
import time
import threading
from pathlib import Path
from datetime import datetime, timezone
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# From existing modules
from P_01999000042260124030_shared_utils import (
    atomic_json_read,
    atomic_json_write,
    utc_timestamp
)
from P_01999000042260124027_id_allocator import allocate_single_id
```

### Configuration Schema

```json
{
  "watch_roots": [
    "C:\\Users\\richg\\Gov_Reg"
  ],
  "registry_path": "01999000042260124552_unified_governance_registry.json",
  "event_log_path": "01999000042260124559_file_watcher_events.jsonl",
  "debounce_seconds": 2.0,
  "stability_check_interval_ms": 500,
  "stability_timeout_seconds": 10,
  "loop_prevention_window_seconds": 5,
  "include_patterns": [
    "P_*.py",
    "*.json",
    "*.md",
    "01999*.*"
  ],
  "exclude_patterns": [
    "*.tmp",
    "*.swp",
    "*~",
    ".git/*",
    "__pycache__/*",
    "htmlcov/*",
    "*.pyc",
    ".DS_Store",
    "nul"
  ],
  "layer_mappings": {
    "tests/": "TESTING",
    "evidence/": "EVIDENCE",
    "governance/": "GOVERNANCE",
    "scripts/": "EXECUTION"
  },
  "artifact_kind_mappings": {
    ".py": "PYTHON_MODULE",
    ".json": "JSON",
    ".md": "MARKDOWN",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".txt": "TEXT"
  }
}
```

---

## Success Criteria (MVP Only)

### Must Pass
- [x] Detects file creation events within 2 seconds (after debounce)
- [x] Extracts 20-digit file_id correctly from filename
- [x] Allocates new file_id if missing
- [x] Detects layer and artifact_kind correctly
- [x] Adds entry to unified registry atomically
- [x] Logs events to JSONL file
- [x] Prevents loops (ignores own registry writes)
- [x] Implements stability gate (waits for file to stabilize)
- [x] Uses file locking to prevent concurrent writes
- [x] Supports dry-run mode (no registry changes)
- [x] Supports start/stop/status commands

### Explicitly Out of Scope (MVP)
- [ ] File modification handling
- [ ] File deletion handling
- [ ] File rename handling
- [ ] GEU integration
- [ ] Duplicate detection
- [ ] Crash recovery
- [ ] Registry backups
- [ ] Health monitoring
- [ ] Full audit trail

---

## Testing Plan (MVP)

### Unit Tests
```python
# P_01999000042260124562_test_file_watcher_mvp.py

def test_extract_file_id():
    """Test 20-digit file_id extraction."""
    assert extract_file_id("P_01999000042260124560_file_watcher_mvp.py") == "01999000042260124560"
    assert extract_file_id("01999000042260124552_unified_governance_registry.json") == "01999000042260124552"
    assert extract_file_id("invalid.py") is None

def test_detect_layer():
    """Test layer detection rules."""
    assert detect_layer(Path("P_01999000042260124560_file_watcher_mvp.py")) == "EXECUTION"
    assert detect_layer(Path("README.md")) == "DOCUMENTATION"
    assert detect_layer(Path("tests/test_watcher.py")) == "TESTING"

def test_detect_artifact_kind():
    """Test artifact kind detection."""
    assert detect_artifact_kind(Path("test.py")) == "PYTHON_MODULE"
    assert detect_artifact_kind(Path("test.json")) == "JSON"
    assert detect_artifact_kind(Path("test.md")) == "MARKDOWN"

def test_should_ignore():
    """Test ignore patterns."""
    assert should_ignore(Path(".git/config")) is True
    assert should_ignore(Path("test.tmp")) is True
    assert should_ignore(Path("P_01999000042260124560_file_watcher_mvp.py")) is False
```

### Integration Tests
1. **Test: File creation triggers registry update**
   - Start watcher in apply mode
   - Create new file with valid file_id
   - Verify entry added to registry within 5 seconds
   - Check event logged

2. **Test: Dry-run mode doesn't modify registry**
   - Start watcher in dry-run mode
   - Create new file
   - Verify registry unchanged
   - Check event logged

3. **Test: Stability gate works**
   - Create file and continuously modify it
   - Verify watcher waits until stable
   - Verify entry added after stabilization

4. **Test: Loop prevention works**
   - Start watcher
   - Create file (triggers registry update)
   - Verify watcher doesn't trigger on registry modification
   - Check loop prevention logged

5. **Test: File locking prevents corruption**
   - Start two watcher instances
   - Create files simultaneously
   - Verify registry not corrupted
   - Verify all entries added

---

## Reusable Code from Past Implementations

### From 16-digit Prefix Watcher
✅ **Stability checking logic** (poll size/mtime)  
✅ **File locking pattern** (exclusive lock check)  
✅ **Event queue with debounce** (UPSERT semantics)  
✅ **Loop prevention** (timestamp-based suppression)  
❌ **Prefix assignment** (16-digit; replace with 20-digit)

### From State Watcher Service
✅ **Start/stop/status control**  
✅ **Service-level event handling**  
✅ **JSONL event log pattern**  
⚠️ **Multi-file monitoring** (adapt for single registry)

### From Async Watcher
✅ **Ignore filtering patterns**  
✅ **Processing delay for write completion**  
⚠️ **watchfiles library** (use watchdog instead per requirements)

---

## Key Decisions

### Decision 1: MVP Scope = Create Events Only
**Rationale:** Past implementations focused on file assignment/stability, not full lifecycle. Start minimal.  
**Impact:** Modify/delete/rename deferred to Phase 2.  
**Risk:** Registry grows but doesn't prune deleted files until Phase 2.

### Decision 2: 20-digit File ID (Not 16-digit)
**Rationale:** Unified registry uses 20-digit format. Past 16-digit is incompatible.  
**Impact:** Cannot reuse prefix assignment code directly.  
**Mitigation:** Use existing P_01999000042260124027_id_allocator.py.

### Decision 3: JSONL Event Log in MVP (Not Phase 4)
**Rationale:** Capability Registry marks as "must". Past implementations all had it.  
**Impact:** Adds complexity but provides audit trail from day 1.  
**Benefit:** Debugging and monitoring from MVP launch.

### Decision 4: Stability Gate in MVP (Not Deferred)
**Rationale:** Capability Registry marks as "must". Critical for avoiding incomplete file reads.  
**Impact:** Adds 10s worst-case latency per file.  
**Benefit:** Prevents registry corruption from partial writes.

---

## Open Questions Resolved

| Question | Resolution |
|----------|-----------|
| Checksum calculation? | ❌ Not in MVP. Deferred to Phase 4. |
| GEU membership? | ❌ Not in MVP. Deferred to Phase 3. |
| File deletion handling? | ❌ Not in MVP. Deferred to Phase 2. |
| Cross-repository files? | ⏸️ Out of scope (registry tracks single repo). |
| Large files (>100MB)? | ✅ No special handling. Process all files. |
| Binary files? | ✅ Include in registry (track existence). |
| Directory events? | ✅ Detect and log, but no action (files only). |

---

## Conclusion

**MVP Scope is now clearly defined:**

1. ✅ Monitor file creation events
2. ✅ Extract/allocate 20-digit file_id
3. ✅ Detect metadata (layer, artifact_kind)
4. ✅ Add entry to unified registry atomically
5. ✅ Log events to JSONL
6. ✅ Implement all "must" capabilities (debounce, stability, loop prevention, locking)
7. ✅ Support dry-run mode
8. ✅ Support start/stop/status

**Explicitly deferred to later phases:**
- Modify/delete/rename handling
- GEU integration
- Advanced features (backups, crash recovery, health monitoring)

**Next step:** Implement `P_01999000042260124560_file_watcher_mvp.py` with revised scope.

---

## References

- **Unified Registry:** 01999000042260124552_unified_governance_registry.json
- **Requirements Spec:** 01999000042260124557_FILE_WATCHER_REQUIREMENTS.md
- **Past Plan:** 01999000042260124550_file_watcher_plan_undone.md
- **ID Allocator:** P_01999000042260124027_id_allocator.py
- **Shared Utils:** P_01999000042260124030_shared_utils.py
