# Implementation Plan: ID System Automation Functions

## Context

The Gov_Reg ID allocation and registry system is **60-70% complete** with strong foundations:
- ✅ Atomic writes with cross-process file locking
- ✅ Directory ID (.dir_id) anchor system with validation
- ✅ File ID allocation via unified counter store (SSOT)
- ✅ Comprehensive unified registry with 32+ metadata columns
- ✅ Scanner service with basic repair capability (`--fix` mode)
- ✅ File watcher infrastructure (watchdog-based)
- ✅ Reconciliation logic framework
- ❌ **Missing operational glue** to keep system automatically correct

**Problem:** The system can detect violations and perform batch repairs, but lacks **continuous enforcement**, **automatic remediation**, **transactional integrity**, and **scheduled health checks**. This creates drift between directory structure, filesystem state, and registry state.

**Goal:** Implement 8 missing automation functions that transform the ID system from a "batch repair" model to a **self-healing, continuously enforced** governance system.

---

## Implementation Strategy

Build all 8 functions using established patterns:
- **Scanner Architecture Pattern** (walk → detect violations → repair → evidence)
- **Atomic Write Pattern** (temp file → fsync → atomic rename with file locking)
- **Registry Integration Pattern** (RFC6902 JSON Patch → atomic commit → evidence bundle)
- **Testing Pattern** (pytest fixtures for temp projects, mock registry data)

---

## 1. Auto-Repair of Invalid `.dir_id` Anchors

### Current State
- Scanner detects missing and invalid .dir_id files
- `--fix` mode **only repairs missing** anchors (allocates new IDs)
- Invalid/corrupt anchors are **reported but not fixed** (raises ValueError)

### Implementation
**Extend** `P_01260207233100000071_scanner_service.py` with corruption repair:

```python
class CorruptDirIdRepairHandler:
    """Repairs malformed, invalid, or corrupt .dir_id files"""

    def repair_corrupt_anchor(self, dir_path: Path, violation_code: str):
        """
        Handles:
        - Malformed JSON (parse errors)
        - Missing required fields (dir_id, created_at, relative_path, etc.)
        - Wrong digit count (not 20 digits)
        - Wrong relative_path (doesn't match actual path)
        - Wrong project_root_id

        Strategy:
        1. Read existing .dir_id (if parseable)
        2. Preserve `dir_id` if valid 20-digit numeric
        3. Regenerate all other fields (created_at, relative_path, etc.)
        4. Atomic write new .dir_id
        5. Log evidence with before/after snapshots
        """
```

**Files to Modify:**
- `govreg_core/P_01260207233100000071_scanner_service.py` - Add `CorruptDirIdRepairHandler`
- `govreg_core/P_01260207233100000070_dir_identity_resolver.py` - Enhance `_validate_dir_id()` to return repair hints
- `govreg_core/P_01260207233100000069_dir_id_handler.py` - Add `repair_corrupt_dir_id()`

**Evidence Output:**
- `.state/evidence/dir_id_repairs/corrupt_repair_{timestamp}_{dir_id}.json`

**Defect Codes:**
- `DIR-IDENTITY-005-REPAIRED`: Malformed JSON fixed
- `DIR-IDENTITY-006-REPAIRED`: Invalid content corrected

---

## 2. Continuous Enforcement (Watcher + Registry Hook)

### Current State
- File watcher exists (`P_01260207233100000007_watcher.py`) with event detection
- Watcher daemon exists (`P_01260207233100000008_watcher_daemon.py`)
- Work queue exists for deduplication
- **NOT wired to registry updates or dir_id enforcement**

### Implementation
**Connect** watcher → registry writer → dir_id enforcement:

```python
class DirIdEnforcementHandler:
    """Watches filesystem for directory creation and enforces .dir_id"""

    def on_directory_created(self, event):
        """
        1. Classify zone (governed/staging/excluded)
        2. If governed → allocate dir_id → write .dir_id
        3. Register in unified registry
        4. Emit evidence
        """

    def on_directory_moved(self, event):
        """
        1. Update .dir_id relative_path
        2. Update registry paths
        3. Rewrite references (see Function 4)
        """
```

**Files to Create:**
- `govreg_core/P_01260207233100000xxx_dir_id_enforcement_handler.py` (allocate new file_id)

**Files to Modify:**
- `repo_autoops/P_01260207233100000007_watcher.py` - Wire DirIdEnforcementHandler to events
- `govreg_core/P_01260207233100000019_registry_writer.py` - Add `register_new_directory()` method

**Pre-commit Hook Option:**
- Create `.git/hooks/pre-commit` script that runs `scanner_service.py --fix --quick` on staged governed directories

**Evidence Output:**
- `.state/evidence/enforcement/dir_created_{timestamp}_{dir_id}.json`

---

## 3. Registry ↔ Filesystem Reconciliation (Bidirectional)

### Current State
- Reconciliation logic exists (`P_01260207233100000017_reconciliation.py`) for PFMS state
- GEU reconciler exists (`P_01260207233100000152_geu_reconciler.py`) for metadata alignment
- **ReconcileScheduler is skeleton only** (`P_01260207233100000369_reconcile_scheduler.py`)

### Implementation
**Implement full bidirectional reconciliation**:

```python
class RegistryFilesystemReconciler:
    """Strict bidirectional reconciliation with repair options"""

    def reconcile(self, zone: str = "all"):
        """
        Checks:
        1. Every registry path exists on disk
        2. Every governed disk file exists in registry
        3. dir_id in registry matches parent .dir_id on disk
        4. file_id in registry matches filename prefix
        5. No duplicate file_ids (same ID → multiple files)
        6. No duplicate paths (same path → multiple registry entries)

        Outputs:
        - Defect log with codes (REGISTRY-ORPHAN, DISK-UNREGISTERED, ID-MISMATCH, etc.)
        - Optional repair actions (--auto-fix flag)
        - Evidence bundle with before/after snapshots
        """
```

**Files to Create:**
- `govreg_core/P_01260207233100000xxx_registry_filesystem_reconciler.py`

**Files to Modify:**
- `govreg_core/P_01260207233100000017_reconciliation.py` - Extend with new reconciliation types
- `repo_autoops/P_01260207233100000369_reconcile_scheduler.py` - Implement scheduler using APScheduler

**Defect Codes:**
- `REGISTRY-ORPHAN-001`: Path in registry doesn't exist on disk
- `DISK-UNREGISTERED-002`: Governed file exists but not in registry
- `ID-MISMATCH-003`: Registry dir_id != parent .dir_id
- `DUPLICATE-FILE-ID-004`: Same file_id used by multiple files
- `DUPLICATE-PATH-005`: Same path mapped to multiple registry entries

**Evidence Output:**
- `.state/evidence/reconciliation/full_reconcile_{timestamp}.json`

**Scheduler Implementation:**
- Use APScheduler with cron trigger (e.g., nightly at 2 AM)
- Configurable via `RECONCILE_SCHEDULE` env var or config file

---

## 4. Reference Rewrites After ID-Based Renames

### Current State
- **No reference tracking or rewrite mechanism detected**
- Registry path update reports exist but don't rewrite consumers

### Implementation
**Create reference rewriter** that updates hard-coded paths:

```python
class ReferenceRewriter:
    """Rewrites references after file/directory renames"""

    PATTERNS = {
        "markdown_links": r'\[([^\]]+)\]\(([^)]+)\)',
        "yaml_paths": r'path:\s*["\']?([^"\']+)["\']?',
        "json_paths": r'"path":\s*"([^"]+)"',
        "python_imports": r'from\s+([.\w]+)\s+import',
    }

    def rewrite_after_rename(self, old_path: str, new_path: str):
        """
        1. Find all files that reference old_path
        2. Update references to new_path
        3. Emit deterministic change report
        4. Update registry derived artifacts
        """
```

**Files to Create:**
- `govreg_core/P_01260207233100000xxx_reference_rewriter.py`

**Integration Points:**
- Wire into `DirIdEnforcementHandler.on_directory_moved()`
- Wire into any script that renames files/directories with IDs

**Evidence Output:**
- `.state/evidence/reference_rewrites/rewrite_{timestamp}_{old_path_hash}.json`
- Includes: changed files, line numbers, before/after snippets

---

## 5. Automated Coverage Completion for `dir_id` Population

### Current State
- Scanner reports coverage metrics (68% dir_id population achieved)
- **No automated completion for remaining 32%**

### Implementation
**Extend scanner with coverage completion**:

```python
class DirIdCoverageCompleter:
    """Analyzes and completes dir_id population gaps"""

    def analyze_gaps(self):
        """
        Categorizes null dir_id entries:
        1. Missing .dir_id anchor (can auto-fix)
        2. Path outside governed zones (should exclude from registry)
        3. Excluded zone (mark with exclusion reason)
        4. Stale entry (path no longer exists)

        Returns remediation plan with actions
        """

    def complete_coverage(self, auto_apply: bool = False):
        """
        Executes remediation plan:
        - Allocate missing anchors
        - Mark excluded entries
        - Purge stale entries
        - Update registry
        """
```

**Files to Modify:**
- `govreg_core/P_01260207233100000071_scanner_service.py` - Add `DirIdCoverageCompleter`
- `govreg_core/P_01999000042260124023_scanner.py` - Enhance gap analysis

**Evidence Output:**
- `.state/evidence/coverage/gap_analysis_{timestamp}.json`
- `.state/evidence/coverage/completion_report_{timestamp}.json`

---

## 6. Orphan + Dead-Entry Cleanup

### Current State
- Registry scanner detects orphaned entries (disk file exists but not in registry)
- **No automated cleanup mechanism**

### Implementation
**Create cleanup automation**:

```python
class OrphanCleanupService:
    """Detects and quarantines/removes orphaned entries"""

    def detect_orphans(self):
        """
        Finds:
        1. .dir_id exists but directory excluded/moved
        2. Registry has files that don't exist on disk
        3. Disk files in governed zones not in registry
        4. Duplicate IDs across files

        Returns quarantine list with reasons
        """

    def cleanup(self, dry_run: bool = True):
        """
        - Move orphaned .dir_id files to .state/quarantine/
        - Remove dead registry entries (with backup)
        - Register unregistered governed files
        - Emit evidence bundle
        """
```

**Files to Create:**
- `govreg_core/P_01260207233100000xxx_orphan_cleanup_service.py`

**Quarantine Location:**
- `.state/quarantine/dir_ids/{timestamp}/`
- `.state/quarantine/registry_entries/{timestamp}.json`

**Evidence Output:**
- `.state/evidence/cleanup/orphan_cleanup_{timestamp}.json`

---

## 7. Transactional Rollback / Atomic Multi-Step Operations

### Current State
- Atomic writes exist for single files (`atomic_json_write()`)
- **No transaction log or multi-step rollback**

### Implementation
**Create transaction coordinator**:

```python
class TransactionCoordinator:
    """Manages atomic multi-step operations with rollback"""

    def __init__(self):
        self.transaction_log_path = Path(".state/transactions/")

    def begin_transaction(self, transaction_id: str):
        """
        Creates transaction log:
        {
            "transaction_id": "...",
            "started_at": "...",
            "operations": [],
            "snapshots": {}  # before states
        }
        """

    def record_operation(self, op_type: str, target: str, before_state: dict):
        """Logs operation with snapshot for rollback"""

    def commit(self):
        """Marks transaction complete, archives log"""

    def rollback(self):
        """
        Restores all before_states:
        - Restore file contents from snapshots
        - Revert registry patches
        - Delete newly created files
        - Re-create deleted files from snapshots
        """
```

**Files to Create:**
- `govreg_core/P_01260207233100000xxx_transaction_coordinator.py`

**Transaction Log Location:**
- `.state/transactions/active/{transaction_id}.json` (during transaction)
- `.state/transactions/committed/{transaction_id}.json` (after commit)
- `.state/transactions/rolled_back/{transaction_id}.json` (after rollback)

**Integration Pattern:**
```python
# Example: Atomic rename + registry update
tx = TransactionCoordinator()
tx.begin_transaction("rename_with_id_12345")
try:
    tx.record_operation("file_rename", old_path, snapshot)
    rename_file_with_id(old_path, new_path)

    tx.record_operation("registry_patch", registry_path, registry_snapshot)
    registry_writer.apply_patch(patch)

    tx.commit()
except Exception as e:
    tx.rollback()
    raise
```

---

## 8. Scheduled Health Checks

### Current State
- **ReconcileScheduler is skeleton only** (Phase 7 TODO marker)

### Implementation
**Implement scheduler with health check suite**:

```python
class HealthCheckScheduler:
    """Runs scheduled health checks on ID system"""

    def __init__(self):
        self.scheduler = APScheduler()
        self.checks = [
            ScannerHealthCheck(),           # Scan governed zones
            RegistryIntegrityCheck(),       # Validate registry schema + IDs
            ReconciliationHealthCheck(),    # Registry ↔ filesystem alignment
            OrphanDetectionCheck(),         # Find dead entries
            DuplicateIdCheck(),             # Detect ID conflicts
            CoverageMetricsCheck(),         # Track dir_id population %
        ]

    def schedule_nightly_checks(self):
        """Runs all checks at 2 AM daily"""
        self.scheduler.add_job(
            self.run_all_checks,
            trigger='cron',
            hour=2,
            minute=0
        )

    def run_all_checks(self):
        """
        Executes all checks, aggregates defects, emits evidence
        Fail-closed on critical violations (exit 1)
        """
```

**Files to Modify:**
- `repo_autoops/P_01260207233100000369_reconcile_scheduler.py` - Implement full scheduler

**Files to Create:**
- `govreg_core/P_01260207233100000xxx_health_check_scheduler.py`
- `govreg_core/health_checks/` directory with check implementations

**Evidence Output:**
- `.state/evidence/health_checks/nightly_{date}.json`

**Configuration:**
- Env var: `HEALTH_CHECK_SCHEDULE` (default: "0 2 * * *" - 2 AM daily)
- Config file: `health_check_config.json` with enabled checks, thresholds

---

## Critical Files to Create/Modify

### New Files (allocate file_ids from unified allocator)
1. `govreg_core/P_{new_id}_dir_id_enforcement_handler.py` - Continuous enforcement
2. `govreg_core/P_{new_id}_registry_filesystem_reconciler.py` - Bidirectional reconciliation
3. `govreg_core/P_{new_id}_reference_rewriter.py` - Path reference rewriting
4. `govreg_core/P_{new_id}_orphan_cleanup_service.py` - Dead entry cleanup
5. `govreg_core/P_{new_id}_transaction_coordinator.py` - Atomic multi-step ops
6. `govreg_core/P_{new_id}_health_check_scheduler.py` - Scheduled checks
7. `govreg_core/health_checks/__init__.py` - Health check modules
8. `.git/hooks/pre-commit` - Optional hook for continuous enforcement

### Modified Files
1. `govreg_core/P_01260207233100000071_scanner_service.py` - Add corrupt repair + coverage completion
2. `govreg_core/P_01260207233100000070_dir_identity_resolver.py` - Enhance validation
3. `govreg_core/P_01260207233100000069_dir_id_handler.py` - Add repair_corrupt_dir_id()
4. `govreg_core/P_01260207233100000019_registry_writer.py` - Add register_new_directory()
5. `govreg_core/P_01260207233100000017_reconciliation.py` - Extend reconciliation types
6. `repo_autoops/P_01260207233100000007_watcher.py` - Wire enforcement handler
7. `repo_autoops/P_01260207233100000369_reconcile_scheduler.py` - Implement scheduler
8. `govreg_core/P_01999000042260124023_scanner.py` - Enhance gap analysis

### Registry & Evidence Updates
- `01999000042260124503_governance_registry_unified.json` - New entries for all created files
- `.state/evidence/` - New subdirectories for each function's evidence output

---

## Implementation Order & Dependencies

### Phase 1: Foundation (Days 1-2)
1. **Function 7 - Transaction Coordinator** - Required by all other functions
2. **Function 1 - Corrupt Dir ID Repair** - Extends existing scanner

### Phase 2: Detection & Reconciliation (Days 3-4)
3. **Function 3 - Registry ↔ Filesystem Reconciliation** - Full bidirectional
4. **Function 6 - Orphan Cleanup** - Depends on reconciliation

### Phase 3: Coverage & References (Days 5-6)
5. **Function 5 - Coverage Completion** - Extends scanner
6. **Function 4 - Reference Rewriter** - Needed before continuous enforcement

### Phase 4: Automation & Monitoring (Days 7-8)
7. **Function 2 - Continuous Enforcement** - Depends on transaction coordinator + reference rewriter
8. **Function 8 - Scheduled Health Checks** - Orchestrates all above functions

---

## Testing Strategy

### Unit Tests
For each new module:
- Test with temp project fixtures (`conftest.py` pattern)
- Mock registry data
- Verify evidence output format
- Test error handling and rollback

### Integration Tests
- End-to-end directory creation → enforcement → registry update
- Multi-step transaction with forced failure → verify rollback
- Scheduled health check execution → defect detection
- Reference rewrite after directory rename → verify updated links

### Test Files to Create
- `tests/test_dir_id_enforcement_handler.py`
- `tests/test_registry_filesystem_reconciler.py`
- `tests/test_reference_rewriter.py`
- `tests/test_orphan_cleanup_service.py`
- `tests/test_transaction_coordinator.py`
- `tests/test_health_check_scheduler.py`
- `tests/integration/test_end_to_end_automation.py`

---

## Verification Plan

### 1. Manual Testing
```bash
# Function 1: Corrupt dir_id repair
python -m govreg_core.scanner_service --zone governed --fix --repair-corrupt

# Function 2: Continuous enforcement (watcher)
python -m govreg_core.dir_id_enforcement_handler --start-daemon

# Function 3: Reconciliation
python -m govreg_core.registry_filesystem_reconciler --auto-fix

# Function 4: Reference rewrite
python -m govreg_core.reference_rewriter --old-path "old/dir" --new-path "new/dir"

# Function 5: Coverage completion
python -m govreg_core.scanner_service --complete-coverage --auto-apply

# Function 6: Orphan cleanup
python -m govreg_core.orphan_cleanup_service --dry-run

# Function 7: Transaction test
python -m govreg_core.transaction_coordinator --test-rollback

# Function 8: Health checks
python -m govreg_core.health_check_scheduler --run-once
```

### 2. Evidence Validation
- Verify evidence files created in `.state/evidence/`
- Check transaction logs in `.state/transactions/`
- Validate quarantine entries in `.state/quarantine/`

### 3. Registry Integrity
```bash
# Verify no duplicate file_ids
python -m govreg_core.geu_reconciler --check-duplicates

# Verify all governed files registered
python -m govreg_core.registry_filesystem_reconciler --report-only

# Verify 100% dir_id coverage in governed zones
python -m govreg_core.scanner_service --metrics
```

### 4. Automated Testing
```bash
# Run full test suite
pytest tests/ -v --cov=govreg_core --cov-report=html

# Run integration tests only
pytest tests/integration/ -v

# Run health check simulation
python -m govreg_core.health_check_scheduler --simulate
```

### 5. Continuous Monitoring
- Set up scheduled health checks (cron or systemd timer)
- Monitor `.state/evidence/health_checks/` for defects
- Alert on critical violations (coverage drop, duplicate IDs, orphans)

---

## Success Criteria

1. ✅ **Auto-repair**: Scanner can repair corrupt .dir_id files with evidence
2. ✅ **Continuous enforcement**: New directories get .dir_id within 5 seconds
3. ✅ **Reconciliation**: Nightly checks detect and optionally fix all misalignments
4. ✅ **Reference rewrite**: Directory renames update all markdown/JSON/YAML references
5. ✅ **100% coverage**: All governed directories have valid .dir_id anchors
6. ✅ **Zero orphans**: No dead registry entries, no unregistered governed files
7. ✅ **Transactional integrity**: Multi-step ops can rollback on failure
8. ✅ **Health monitoring**: Nightly reports with defect trends and alerts

---

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Transaction rollback fails mid-restore | Use nested transactions; log all operations before execution |
| Watcher misses events under heavy load | Implement event queue with persistence; backfill from scanner |
| Reference rewrite breaks code syntax | Dry-run mode; syntax validation after rewrite; rollback on error |
| Scheduler conflicts with manual operations | Use file locking; detect concurrent runs; skip if lock held |
| False positive orphan detection | Quarantine-first approach; manual review before deletion |
| Performance impact of continuous enforcement | Debounce events; batch registry writes; async processing |

---

## Deliverables

1. **8 new automation modules** with tests and documentation
2. **Enhanced scanner** with repair + coverage completion
3. **Operational scheduler** for nightly health checks
4. **Transaction system** for rollback capability
5. **Evidence framework** with defect codes and structured outputs
6. **Integration tests** proving end-to-end automation
7. **Documentation** for each function's usage and configuration
8. **Health check dashboard** data (JSON reports for visualization)

---

## Estimated Effort

- **Development**: 8-10 days (1 day per function + integration)
- **Testing**: 3-4 days (unit + integration + manual verification)
- **Documentation**: 1-2 days
- **Total**: ~12-16 days for complete implementation

All functions leverage existing patterns (atomic writes, scanner architecture, registry integration), minimizing greenfield development and risk.
