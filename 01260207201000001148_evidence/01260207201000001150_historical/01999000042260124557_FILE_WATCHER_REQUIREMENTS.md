# File Watcher System - Functional Requirements

**Document ID:** 01999000042260124557  
**Date:** 2026-01-26  
**Version:** 1.0  
**Status:** REQUIREMENTS SPECIFICATION

---

## Purpose

Define functional requirements for a file watcher system that automatically maintains the unified governance registry by monitoring directories for file changes.

---

## System Overview

The File Watcher System monitors specified directories for file system events (create, modify, delete, rename) and automatically updates the unified governance registry to maintain synchronization between the file system and the registry.

---

## Core Functional Requirements

### FR-1: File System Monitoring

#### FR-1.1: Directory Watching
- **Requirement:** System SHALL monitor all directories defined in `repository_configuration.repo_roots`
- **Details:**
  - Monitor recursively (all subdirectories)
  - Support multiple repository roots simultaneously
  - Handle symbolic links appropriately (follow or ignore based on config)
- **Priority:** CRITICAL

#### FR-1.2: Event Detection
- **Requirement:** System SHALL detect the following file system events:
  - File created
  - File modified (content changed)
  - File deleted
  - File renamed/moved
  - Directory created
  - Directory deleted
  - Directory renamed/moved
- **Priority:** CRITICAL

#### FR-1.3: Event Filtering
- **Requirement:** System SHALL filter events to only process relevant files
- **Details:**
  - Include files matching governance patterns (P_*.py, *.json, *.md, etc.)
  - Exclude temporary files (*.tmp, *.swp, *~, .git/*, __pycache__/*, etc.)
  - Exclude hidden directories (except .github/)
  - Support configurable include/exclude patterns
- **Priority:** HIGH

#### FR-1.4: Debouncing
- **Requirement:** System SHALL debounce rapid sequential events on the same file
- **Details:**
  - Wait N seconds (configurable, default 2s) after last event before processing
  - Coalesce multiple modify events into single update
  - Handle save patterns from different editors
- **Rationale:** Prevents duplicate processing during file saves
- **Priority:** HIGH

### FR-2: Registry Updates

#### FR-2.1: File Creation Handling
- **Requirement:** When a new file is created, system SHALL:
  1. Check if file has a valid 20-digit file_id in filename
  2. If no file_id, allocate new ID using id_allocator
  3. Detect file type (layer, artifact_kind)
  4. Create registry entry with metadata
  5. Write registry update atomically
- **Priority:** CRITICAL

#### FR-2.2: File Modification Handling
- **Requirement:** When a file is modified, system SHALL:
  1. Locate existing registry entry by file_id
  2. Update `last_modified` timestamp
  3. Optionally update metadata (size, checksum)
  4. Preserve GEU assignments
  5. Write registry update atomically
- **Priority:** HIGH

#### FR-2.3: File Deletion Handling
- **Requirement:** When a file is deleted, system SHALL:
  1. Locate existing registry entry by file_id
  2. Mark entry as deleted (soft delete) OR remove entry (hard delete)
  3. Check if file is member of any GEU
  4. If GEU member, flag GEU as incomplete
  5. Write registry update atomically
- **Configuration:** Soft delete vs hard delete (configurable)
- **Priority:** CRITICAL

#### FR-2.4: File Rename/Move Handling
- **Requirement:** When a file is renamed or moved, system SHALL:
  1. Detect old file_id from old path
  2. Detect new file_id from new path (if changed)
  3. If file_id unchanged, update `relative_path` only
  4. If file_id changed, create new entry and mark old as renamed
  5. Update GEU member references if applicable
  6. Write registry update atomically
- **Priority:** HIGH

#### FR-2.5: Atomic Registry Updates
- **Requirement:** All registry updates SHALL be atomic
- **Details:**
  - Write to temporary file first
  - Validate JSON structure
  - Rename to actual file (atomic operation)
  - Use file locking to prevent concurrent writes
  - Maintain backup of previous version
- **Priority:** CRITICAL

### FR-3: File Metadata Detection

#### FR-3.1: File ID Extraction
- **Requirement:** System SHALL extract file_id from filename
- **Pattern:** 
  - Python files: `P_{FILE_ID}_{name}.py`
  - Other files: `{FILE_ID}_{name}.ext`
- **Validation:** Must be exactly 20 digits starting with `01`
- **Priority:** CRITICAL

#### FR-3.2: Layer Detection
- **Requirement:** System SHALL automatically detect file layer
- **Rules:**
  - Files in `/tests/` → TESTING
  - Files matching `P_*_test_*.py` → TESTING
  - Files matching `P_*.py` (not test) → EXECUTION
  - Files matching `*.md` → DOCUMENTATION
  - Files matching `*.json` (not test) → DATA
  - Files in `/scripts/` → EXECUTION
  - Configurable layer mappings
- **Priority:** HIGH

#### FR-3.3: Artifact Kind Detection
- **Requirement:** System SHALL automatically detect artifact kind
- **Rules:**
  - `.py` files → PYTHON_MODULE
  - `.json` files → JSON
  - `.md` files → MARKDOWN
  - Test files → TEST
  - `.yaml` / `.yml` → YAML
  - `.sh` / `.bat` / `.ps1` → SCRIPT
- **Priority:** HIGH

#### FR-3.4: File Attributes
- **Requirement:** System SHALL capture file attributes:
  - File size (bytes)
  - Last modified timestamp
  - SHA256 checksum (optional, configurable)
  - Git commit hash (if in git repo)
- **Priority:** MEDIUM

### FR-4: GEU Integration

#### FR-4.1: GEU Membership Detection
- **Requirement:** System SHALL attempt to detect GEU membership for new files
- **Methods:**
  - Check file path patterns
  - Analyze imports/dependencies
  - Use naming conventions
  - Manual override via configuration
- **Priority:** MEDIUM

#### FR-4.2: GEU Completeness Checking
- **Requirement:** When a GEU member file is deleted, system SHALL:
  1. Update GEU `coverage_status` to reflect missing file
  2. Mark required files as missing
  3. Optionally send alert/notification
- **Priority:** MEDIUM

#### FR-4.3: GEU Anchor Validation
- **Requirement:** System SHALL validate that GEU anchor files exist
- **Details:**
  - On file deletion, check if deleted file is GEU anchor
  - If anchor deleted, mark GEU as invalid
  - Prevent anchor deletion if GEU is active (optional)
- **Priority:** MEDIUM

### FR-5: Conflict Resolution

#### FR-5.1: Duplicate File ID Detection
- **Requirement:** System SHALL detect duplicate file_ids
- **Action:**
  - Alert operator
  - Log conflict
  - Optionally rename conflicting file
  - Do not corrupt registry
- **Priority:** CRITICAL

#### FR-5.2: Registry Drift Detection
- **Requirement:** System SHALL detect drift between registry and file system
- **Details:**
  - Files in registry but not on disk
  - Files on disk but not in registry
  - File_id mismatches
- **Frequency:** On startup and periodic scan (configurable)
- **Priority:** HIGH

#### FR-5.3: Concurrent Modification Handling
- **Requirement:** System SHALL handle concurrent registry modifications
- **Details:**
  - Use file locking (01999000042260124026_ID_COUNTER.json.lock pattern)
  - Retry on lock conflicts (with exponential backoff)
  - Detect external registry changes (checksum/timestamp)
  - Reload and reapply changes if registry externally modified
- **Priority:** CRITICAL

### FR-6: Performance Requirements

#### FR-6.1: Startup Time
- **Requirement:** System SHALL start watching within 5 seconds
- **Details:**
  - Load registry asynchronously
  - Begin watching before full registry validation
- **Priority:** MEDIUM

#### FR-6.2: Event Processing Latency
- **Requirement:** System SHALL process file events within 5 seconds (after debounce)
- **Priority:** MEDIUM

#### FR-6.3: Resource Usage
- **Requirement:** System SHALL limit resource usage:
  - Memory: < 500 MB for 10,000 files
  - CPU: < 5% average, < 20% peak
  - Disk I/O: Batch writes, avoid thrashing
- **Priority:** MEDIUM

#### FR-6.4: Scalability
- **Requirement:** System SHALL handle:
  - Up to 10,000 files per repository
  - Up to 5 repository roots simultaneously
  - Up to 100 file events per second (burst)
- **Priority:** MEDIUM

### FR-7: Reliability & Error Handling

#### FR-7.1: Crash Recovery
- **Requirement:** System SHALL recover from crashes
- **Details:**
  - On restart, scan for events missed during downtime
  - Compare registry state to file system
  - Apply incremental updates
  - Log recovery actions
- **Priority:** HIGH

#### FR-7.2: Error Handling
- **Requirement:** System SHALL handle errors gracefully
- **Error Types:**
  - File permission denied
  - Disk full
  - Registry corruption
  - Invalid file_id format
  - Missing required metadata
- **Actions:**
  - Log error with context
  - Optionally alert operator
  - Continue watching (don't crash)
  - Queue failed operations for retry
- **Priority:** HIGH

#### FR-7.3: Registry Backup
- **Requirement:** System SHALL maintain registry backups
- **Details:**
  - Backup before each write
  - Keep N previous versions (configurable, default 10)
  - Rotate old backups (delete oldest)
  - Store in `.backup/` subdirectory
- **Priority:** HIGH

#### FR-7.4: Health Monitoring
- **Requirement:** System SHALL report health status
- **Metrics:**
  - Events processed per minute
  - Registry update success rate
  - Error count
  - Last successful update timestamp
  - Watcher status (active/inactive)
- **Priority:** MEDIUM

### FR-8: Configuration

#### FR-8.1: Configuration File
- **Requirement:** System SHALL use configuration file
- **Location:** `file_watcher_config.json`
- **Settings:**
  - Repository roots to watch
  - Include/exclude patterns
  - Debounce delay
  - Soft delete vs hard delete
  - Enable/disable features
  - Log level
  - Backup retention
- **Priority:** HIGH

#### FR-8.2: Runtime Configuration Changes
- **Requirement:** System SHALL support runtime config changes
- **Details:**
  - Reload config on SIGHUP (Unix) or manual trigger
  - Apply new settings without restart
  - Log configuration changes
- **Priority:** LOW

### FR-9: Logging & Auditing

#### FR-9.1: Event Logging
- **Requirement:** System SHALL log all file system events
- **Details:**
  - Timestamp
  - Event type
  - File path
  - File ID
  - Action taken
  - Success/failure
- **Format:** Structured JSON logs
- **Priority:** HIGH

#### FR-9.2: Registry Change Audit
- **Requirement:** System SHALL maintain audit trail of registry changes
- **Details:**
  - Before/after values
  - Timestamp
  - Triggering event
  - User/process
- **Format:** Append-only audit log
- **Priority:** MEDIUM

#### FR-9.3: Log Rotation
- **Requirement:** System SHALL rotate logs
- **Details:**
  - Max log file size (default 100 MB)
  - Keep N log files (default 10)
  - Compress old logs
- **Priority:** MEDIUM

### FR-10: Operations & Maintenance

#### FR-10.1: Start/Stop Control
- **Requirement:** System SHALL support clean start/stop
- **Details:**
  - Start: `python file_watcher.py start`
  - Stop: `python file_watcher.py stop` (graceful shutdown)
  - Status: `python file_watcher.py status`
  - Restart: `python file_watcher.py restart`
- **Priority:** HIGH

#### FR-10.2: Dry Run Mode
- **Requirement:** System SHALL support dry-run mode
- **Details:**
  - Process events without updating registry
  - Log what would be changed
  - Useful for testing and validation
- **Command:** `python file_watcher.py --dry-run`
- **Priority:** MEDIUM

#### FR-10.3: Manual Sync
- **Requirement:** System SHALL support manual full sync
- **Details:**
  - Scan all files in watched directories
  - Compare with registry
  - Report discrepancies
  - Optionally apply corrections
- **Command:** `python file_watcher.py sync [--fix]`
- **Priority:** HIGH

#### FR-10.4: Pause/Resume
- **Requirement:** System SHALL support pause/resume
- **Details:**
  - Pause: Stop processing events (but keep monitoring)
  - Resume: Process queued events
  - Useful during maintenance
- **Priority:** LOW

---

## Non-Functional Requirements

### NFR-1: Platform Support
- **Windows:** Full support (Windows 10+)
- **Linux:** Full support
- **macOS:** Full support
- **Priority:** HIGH

### NFR-2: Dependencies
- **Python:** 3.7+ required
- **Libraries:** watchdog, filelock, jsonschema (optional)
- **No external services:** Self-contained
- **Priority:** HIGH

### NFR-3: Security
- **File Access:** Read/write to watched directories and registry only
- **Permissions:** Run as regular user (no root/admin required)
- **Secrets:** No credentials stored
- **Priority:** MEDIUM

### NFR-4: Testability
- **Unit Tests:** 80%+ coverage
- **Integration Tests:** Key workflows covered
- **Mock File System:** Support testing without real files
- **Priority:** MEDIUM

---

## User Stories

### US-1: Automatic File Registration
**As a** developer  
**I want** new files to be automatically added to the registry  
**So that** I don't have to manually register files

**Acceptance Criteria:**
- Create file with proper ID format
- File appears in registry within 5 seconds
- Correct layer and artifact_kind detected

### US-2: Rename Without Re-registration
**As a** developer  
**I want** to rename files without losing registry information  
**So that** I can refactor without manual updates

**Acceptance Criteria:**
- Rename file keeping same file_id
- Registry updates path automatically
- GEU memberships preserved

### US-3: Orphan File Detection
**As a** governance admin  
**I want** to detect files not in registry  
**So that** I can maintain registry completeness

**Acceptance Criteria:**
- Run manual sync command
- Report lists all orphan files
- Option to auto-register orphans

### US-4: GEU Completeness Monitoring
**As a** governance admin  
**I want** to be alerted when GEU files are deleted  
**So that** I can maintain GEU integrity

**Acceptance Criteria:**
- Delete GEU member file
- Registry marks GEU as incomplete
- Alert logged (or sent if configured)

### US-5: Crash Recovery
**As a** developer  
**I want** file watcher to recover after crashes  
**So that** no changes are lost

**Acceptance Criteria:**
- Create/modify files while watcher is down
- Restart watcher
- Registry updates applied for all missed events

---

## Implementation Phases

### Phase 1: Core Watching (MVP)
- FR-1: File system monitoring
- FR-2.1: File creation handling
- FR-2.5: Atomic updates
- FR-3.1: File ID extraction
- FR-7.2: Basic error handling
- FR-10.1: Start/stop control

**Deliverable:** Basic file watcher that registers new files

### Phase 2: Full Event Handling
- FR-2.2: File modification handling
- FR-2.3: File deletion handling
- FR-2.4: Rename/move handling
- FR-3.2: Layer detection
- FR-3.3: Artifact kind detection
- FR-5.2: Drift detection

**Deliverable:** Complete file event handling

### Phase 3: GEU Integration
- FR-4: All GEU integration features
- FR-5.1: Duplicate detection
- FR-5.3: Concurrent modification handling

**Deliverable:** GEU-aware file watcher

### Phase 4: Production Hardening
- FR-6: Performance optimization
- FR-7: Reliability features
- FR-8: Configuration management
- FR-9: Logging & auditing
- FR-10: Operations features

**Deliverable:** Production-ready system

---

## Open Questions

1. **Checksum calculation:** Always compute or only on demand?
2. **GEU membership:** Automatic detection rules vs manual configuration?
3. **File deletion:** Soft delete (mark as deleted) or hard delete (remove from registry)?
4. **Cross-repository files:** How to handle files that appear in multiple repos?
5. **Large files:** Should watcher skip files over certain size (e.g., 100MB)?
6. **Binary files:** Include in registry or exclude?

---

## Risks & Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Registry corruption | HIGH | LOW | Atomic writes, backups, validation |
| Performance degradation | MEDIUM | MEDIUM | Event batching, async processing |
| False duplicate IDs | HIGH | LOW | Strict validation, conflict detection |
| Missed events during crash | MEDIUM | MEDIUM | Startup sync, audit trail |
| Race conditions | HIGH | MEDIUM | File locking, retry logic |

---

## Success Criteria

- ✅ System monitors all configured directories
- ✅ File creation triggers automatic registration within 5 seconds
- ✅ File deletion updates registry correctly
- ✅ No registry corruption under normal operation
- ✅ System recovers from crashes without data loss
- ✅ < 5% CPU usage under normal load
- ✅ All unit tests pass
- ✅ Manual sync detects drift accurately

---

## References

- **Unified Registry:** 01999000042260124552_unified_governance_registry.json
- **Registry Guide:** 01999000042260124553_UNIFIED_REGISTRY_GUIDE.md
- **ID Allocator:** P_01999000042260124027_id_allocator.py
- **File Creator:** P_01999000042260124028_file_creator.py
- **Previous Plan:** 01999000042260124550_file_watcher_plan_undone.md

---

## Approval

- [ ] Reviewed by: _____________________ Date: _____
- [ ] Approved by: _____________________ Date: _____
- [ ] Implementation started: Yes / No
