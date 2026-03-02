# Automation Descriptor Subsystem - Completion File Tree

**What "DONE" Looks Like - Full System After All 9 Phases**

**Date:** 2026-01-23  
**Status:** Vision document (implementation roadmap)  
**Based on:** `Automation_Descriptor_Phase_Plan.md` v1.3 + `Deliverables_Specification.md` v1.1

---

## Executive Summary

When all 9 phases are complete (Phases 0-8), the system will have:
- **19 Python modules** (production code)
- **15 test files** (>80% coverage)
- **5 documentation files**
- **3 configuration files**
- **1 CLI** with 8+ commands
- **1 daemon** (watcher service)
- **1 canonical registry** (`UNIFIED_SSOT_REGISTRY.json`)
- **Automated artifact generation** (Python descriptors)
- **Full observability** (structured logs, audit trail)

**Total Deliverable:** ~5,000-8,000 lines of production code + comprehensive tests + runbook

---

## Complete File Tree (Post-Phase 8)

```
eafix-modular/
│
├── repo_autoops/
│   └── automation_descriptor/          ← NEW SUBSYSTEM (19 modules)
│       ├── __init__.py                 [Phase 1] Package initialization
│       ├── cli.py                      [Phase 8] Command-line interface (8+ commands)
│       │
│       ├── watcher_daemon.py           [Phase 6] Main orchestrator (watchdog integration)
│       ├── work_queue.py               [Phase 2] SQLite-backed work queue (UPSERT coalescing)
│       ├── stability_checker.py        [Phase 2] Min-age + mtime/size sampling
│       ├── lock_manager.py             [Phase 2] Path/doc/registry locks (total ordering)
│       ├── suppression_manager.py      [Phase 2] Self-induced event suppression
│       │
│       ├── classifier.py               [Phase 3] File classification (governed/unmanaged)
│       ├── id_allocator.py             [Phase 3] 16-digit doc_id allocation
│       ├── file_renamer.py             [Phase 3] Atomic rename with doc_id prefix
│       │
│       ├── descriptor_extractor.py     [Phase 4] Wraps python_ast_parser.py
│       ├── normalizer.py               [Phase 5] Automatic normalization on write
│       ├── backup_manager.py           [Phase 5] Timestamped backups + rollback
│       ├── write_policy_validator.py   [Phase 5] tool_only/immutable/derived enforcement
│       ├── registry_writer_service.py  [Phase 5] Single mutation point (CAS precondition)
│       │
│       ├── event_handlers.py           [Phase 6] FILE_ADDED/MODIFIED/MOVED/DELETED handlers
│       ├── reconciler.py               [Phase 7] Drift detection + repair
│       ├── reconcile_scheduler.py      [Phase 7] Periodic reconciliation trigger
│       │
│       └── audit_logger.py             [Phase 2] Structured JSONL logging
│
├── tests/
│   └── automation_descriptor/          ← NEW TEST SUITE (15+ files)
│       ├── __init__.py
│       ├── test_work_queue.py          [Phase 2] Queue coalescing, retry, dead-letter
│       ├── test_stability_checker.py   [Phase 2] Min-age, mtime/size sampling
│       ├── test_lock_manager.py        [Phase 2] Lock ordering, deadlock prevention
│       ├── test_suppression_manager.py [Phase 2] Loop prevention
│       ├── test_id_allocator.py        [Phase 3] Doc_id allocation, collision handling
│       ├── test_event_handlers.py      [Phase 6] MOVE/DELETE event handling
│       ├── test_descriptor_extractor.py [Phase 4] AST parsing, promotion payload
│       ├── test_normalizer.py          [Phase 5] Path/enum normalization
│       ├── test_backup_manager.py      [Phase 5] Backup/rollback operations
│       ├── test_write_policy_validator.py [Phase 5] Policy enforcement
│       ├── test_registry_writer_service.py [Phase 5] Single-writer, atomic updates
│       ├── test_cas_precondition.py    [Phase 5] registry_hash validation
│       ├── test_reconciler.py          [Phase 7] Drift detection/repair
│       ├── test_loop_prevention.py     [Phase 6] Self-triggered event suppression
│       └── test_integration.py         [Phase 9] End-to-end scenarios (5 scenarios)
│
├── config/
│   ├── WATCHER_CONFIG.yml              [Phase 6] Watcher daemon configuration
│   │   # governed_directories, ignore_patterns, stability_window,
│   │   # max_actions_per_cycle, lock_timeout, reconcile_schedule
│   │
│   └── PYTHON_FILE_DESCRIPTOR.yml      [Phase 4] Descriptor artifact schema
│       # structure, behavior, provenance sections
│
├── registry/
│   └── UNIFIED_SSOT_REGISTRY.json      [Existing, updated by subsystem]
│       # Single source of truth
│       # Updated via promotion patches (registry_hash CAS precondition)
│       # Python columns 81-100 populated by automation_descriptor
│
├── docs/
│   ├── automation_descriptor/          ← NEW DOCUMENTATION (5 files)
│   │   ├── README.md                   [Phase 8] Overview + quickstart
│   │   ├── RUNBOOK.md                  [Phase 8] Operations manual
│   │   ├── REGISTRY_MIGRATION.md       [Phase 8] Migration from deprecated aliases
│   │   └── REGISTRY_WRITE_POLICY.md    [Phase 8] Policy rules + examples
│   │
│   └── 2026012015460001_COLUMN_DICTIONARY.md  [Existing, updated]
│       # Python promotion columns 81-100 documented
│
├── .dms/                               ← RUNTIME DIRECTORIES (created by watcher)
│   ├── artifacts/
│   │   ├── python_descriptor/          [Phase 4] Descriptor JSON artifacts
│   │   │   ├── 1234567890123456.v1.json
│   │   │   ├── 2345678901234567.v1.json
│   │   │   └── ...                     # One per Python file
│   │   │
│   │   └── index/                      [Phase 2+] Optional derived indexes
│   │
│   ├── backups/
│   │   └── registry/                   [Phase 5] Registry backups (30-day retention)
│   │       ├── UNIFIED_SSOT_REGISTRY_20260123T140000Z.json
│   │       ├── UNIFIED_SSOT_REGISTRY_20260123T150000Z.json
│   │       └── ...                     # Timestamped, automatic before mutations
│   │
│   ├── patches/
│   │   └── registry/                   [Phase 5] Patch log archive
│   │       ├── 20260123_140000_uuid1234.json
│   │       ├── 20260123_150000_uuid5678.json
│   │       └── ...                     # Audit trail of all patches
│   │
│   ├── runtime/
│   │   ├── work_queue.sqlite           [Phase 2] Persistent work queue
│   │   │   # Survives daemon restarts
│   │   │   # UNIQUE(path) dedupe
│   │   │   # Retry/dead-letter states
│   │   │
│   │   └── locks/                      [Phase 2] Lock files
│   │       ├── path/                   # Path locks (by hash)
│   │       │   ├── abc123def456.lock
│   │       │   └── ...
│   │       ├── doc/                    # Doc_id locks
│   │       │   ├── 1234567890123456.lock
│   │       │   └── ...
│   │       └── registry.lock           # Global registry lock
│   │
│   ├── logs/                           [Phase 2] Structured logs (JSONL)
│   │   ├── actions.jsonl               # All operations (success + failure)
│   │   └── errors.jsonl                # Error-only log
│   │
│   └── quarantine/                     [Phase 6] Problematic files isolated
│       ├── problematic_file_1.py
│       └── ...                         # Manual review required
│
└── scripts/                            [Optional utility scripts]
    └── automation_descriptor/
        ├── migrate_registry.py         [Phase 8] One-time migration helper
        └── validate_registry.py        [Phase 8] Standalone validator

```

---

## Phase-by-Phase Deliverables

### ✅ Phase 0: Scope Lock (COMPLETE - 2026-01-23)
**Deliverables:**
- ✅ Frozen contracts defined (`Phase_Plan.md` v1.3)
- ✅ Deliverables spec aligned (v1.1)
- ✅ Legacy docs deprecated
- ✅ Authority hierarchy established

**Files Created:**
- `Automation_Descriptor_Phase_Plan.md` (v1.3)
- `Automation_Descriptor_Deliverables_Specification.md` (v1.1)
- `LEGACY_DOCS_DEPRECATION_SUMMARY.md`
- `DELIVERABLES_SPEC_UPDATE_SUMMARY.md`

---

### Phase 1: Architecture & Component Shells
**Duration:** 1 week  
**Deliverables:**
- 19 Python module shells (empty functions, docstrings)
- Package structure in `repo_autoops/automation_descriptor/`
- Import hierarchy validated
- Placeholder tests (pass trivially)

**Files Created:**
- `repo_autoops/automation_descriptor/__init__.py`
- 18 module shells (.py files)
- `tests/automation_descriptor/__init__.py`
- 15 test shells

**Validation Gates:**
- [ ] All modules importable
- [ ] No circular dependencies
- [ ] Type hints in place
- [ ] Docstrings present

---

### Phase 2: Infrastructure (Queue, Locks, Logging)
**Duration:** 1 week  
**Deliverables:**
- SQLite work queue with UPSERT coalescing
- Lock manager (path/doc/registry locks, total ordering)
- Suppression manager (loop prevention)
- Stability checker (min-age + mtime/size sampling)
- Audit logger (structured JSONL)

**Files Implemented:**
- `work_queue.py` (~300 lines)
- `lock_manager.py` (~250 lines)
- `suppression_manager.py` (~150 lines)
- `stability_checker.py` (~200 lines)
- `audit_logger.py` (~100 lines)

**Runtime Artifacts:**
- `.dms/runtime/work_queue.sqlite`
- `.dms/runtime/locks/` (directories)
- `.dms/logs/actions.jsonl`
- `.dms/logs/errors.jsonl`

**Validation Gates:**
- [ ] Queue coalescing test passes
- [ ] Lock ordering test passes (no deadlock)
- [ ] Stability algorithm test passes
- [ ] Logs parseable as JSONL

---

### Phase 3: ID Allocation & Rename
**Duration:** 3 days  
**Deliverables:**
- ID allocator (16-digit doc_ids from ID_REGISTRY.json)
- File renamer (atomic rename with suppression)
- Classifier (governed/unmanaged detection)

**Files Implemented:**
- `id_allocator.py` (~200 lines)
- `file_renamer.py` (~150 lines)
- `classifier.py` (~100 lines)

**Validation Gates:**
- [ ] ID allocation collision-free
- [ ] Rename atomic (fsync verified)
- [ ] Suppression registered correctly

---

### Phase 4: Parser & Descriptor Generation
**Duration:** 1 week  
**Deliverables:**
- Descriptor extractor (wraps python_ast_parser.py)
- Promotion payload generation (20 columns)
- Descriptor artifact creation

**Files Implemented:**
- `descriptor_extractor.py` (~400 lines)

**Runtime Artifacts:**
- `.dms/artifacts/python_descriptor/{doc_id}.v1.json`

**Configuration:**
- `config/PYTHON_FILE_DESCRIPTOR.yml`

**Validation Gates:**
- [ ] AST parsing handles syntax errors
- [ ] Descriptor schema valid
- [ ] Promotion payload complete (20 columns)
- [ ] Idempotency test passes (same source → same descriptor)

---

### Phase 5: Registry Writer Service
**Duration:** 1 week  
**Deliverables:**
- Registry Writer Service (single mutation point)
- Backup manager (automatic before mutations)
- Normalizer (automatic on write)
- Write policy validator (tool_only/immutable/derived)
- CAS precondition enforcement (registry_hash)

**Files Implemented:**
- `registry_writer_service.py` (~500 lines)
- `backup_manager.py` (~200 lines)
- `normalizer.py` (~150 lines)
- `write_policy_validator.py` (~300 lines)

**Runtime Artifacts:**
- `.dms/backups/registry/UNIFIED_SSOT_REGISTRY_{timestamp}.json`
- `.dms/patches/registry/{timestamp}_uuid.json`

**Validation Gates:**
- [ ] CAS precondition test passes
- [ ] Automatic rollback on validation failure
- [ ] Backup created before every write
- [ ] Policy enforcement blocks invalid patches
- [ ] Single-writer verified (no ad-hoc edits)

---

### Phase 6: Watcher Daemon
**Duration:** 1 week  
**Deliverables:**
- Watcher daemon (watchdog integration)
- Event handlers (FILE_ADDED/MODIFIED/MOVED/DELETED)
- Full pipeline integration
- Dry-run default mode

**Files Implemented:**
- `watcher_daemon.py` (~600 lines)
- `event_handlers.py` (~400 lines)

**Configuration:**
- `config/WATCHER_CONFIG.yml`

**Runtime:**
- Daemon starts with `python cli.py start-watcher`
- Requires `--live` flag for writes

**Validation Gates:**
- [ ] Loop prevention test passes
- [ ] MOVE event updates registry path
- [ ] DELETE event creates tombstone
- [ ] Dry-run mode blocks writes
- [ ] Max actions cap enforced

---

### Phase 7: Reconciliation
**Duration:** 3 days  
**Deliverables:**
- Reconciler (drift detection + repair)
- Reconcile scheduler (periodic trigger)
- Drift repair via work queue

**Files Implemented:**
- `reconciler.py` (~300 lines)
- `reconcile_scheduler.py` (~100 lines)

**Validation Gates:**
- [ ] Drift detection finds missing rows
- [ ] Repair doesn't create duplicate queue entries
- [ ] Reconcile idempotent (no-op if clean)

---

### Phase 8: CLI & Runbook
**Duration:** 1 week  
**Deliverables:**
- CLI with 8+ commands
- Complete documentation (README, RUNBOOK, migration guide)
- Migration helper scripts

**Files Implemented:**
- `cli.py` (~600 lines)

**CLI Commands:**
```bash
python cli.py start-watcher [--live] [--max-actions N]
python cli.py stop-watcher
python cli.py reconcile [--scope DIR]
python cli.py describe-file --path PATH | --doc-id ID
python cli.py migrate-registry [--backup-first]
python cli.py validate-registry [--strict]
python cli.py show-queue
python cli.py clear-dead-letter
```

**Documentation:**
- `docs/automation_descriptor/README.md` (~200 lines)
- `docs/automation_descriptor/RUNBOOK.md` (~400 lines)
- `docs/automation_descriptor/REGISTRY_MIGRATION.md` (~150 lines)
- `docs/automation_descriptor/REGISTRY_WRITE_POLICY.md` (~200 lines)

**Validation Gates:**
- [ ] All CLI commands work as documented
- [ ] Runbook tested (setup, operation, rollback)
- [ ] Migration from deprecated aliases succeeds

---

### Phase 9: End-to-End Validation
**Duration:** 3 days  
**Deliverables:**
- All 36 validation gates pass
- Integration test suite (5 scenarios)
- 24-hour soak test
- Code coverage >80%

**Test Scenarios:**
1. Add 10 Python files → verify registry + descriptors
2. Modify file → verify re-parse + update
3. Move file → verify path update + doc_id preservation
4. Delete file → verify tombstone + cleanup
5. Introduce drift → verify reconciliation repair

**Validation Gates (36 total):**
- [ ] All 30 from Phase Plan pass
- [ ] 6 additional frozen contract compliance tests pass
- [ ] Integration tests pass
- [ ] Soak test (24 hours) completes without errors
- [ ] Coverage >80%

---

## What "DONE" Looks Like (Summary)

### System State
```
✅ Daemon running:         python cli.py start-watcher --live
✅ Queue operational:      .dms/runtime/work_queue.sqlite
✅ Locks available:        .dms/runtime/locks/
✅ Logs streaming:         .dms/logs/actions.jsonl
✅ Registry canonical:     registry/UNIFIED_SSOT_REGISTRY.json
✅ Backups automated:      .dms/backups/registry/ (30-day retention)
✅ Descriptors generated:  .dms/artifacts/python_descriptor/
```

### Operational Capabilities
```
✅ Automatic file discovery (governed directories)
✅ Automatic doc_id assignment (16-digit)
✅ Automatic file rename (atomic with suppression)
✅ Automatic AST parsing (no execution)
✅ Automatic descriptor generation (.dms/artifacts/)
✅ Automatic registry promotion (20 Python columns)
✅ Atomic registry updates (CAS precondition enforced)
✅ Automatic backup/rollback (on validation failure)
✅ MOVE/DELETE handling (path updates, tombstones)
✅ Drift repair (reconciliation)
✅ Loop prevention (self-induced events suppressed)
✅ Retry logic (exponential backoff)
✅ Dead-letter queue (non-retryable failures)
✅ Structured observability (JSONL logs)
```

### Quality Metrics
```
✅ Code coverage: >80%
✅ Test count: 15+ test files
✅ Validation gates: 36/36 passed
✅ Soak test: 24 hours continuous operation
✅ Documentation: Complete (README, RUNBOOK, guides)
✅ Linting: Pylint clean
✅ Type checking: Mypy clean
```

### Guarantees Delivered
```
✅ Single source of truth (UNIFIED_SSOT_REGISTRY.json)
✅ Single writer (Registry Writer Service only)
✅ Atomic operations (temp-file-replace + fsync)
✅ No lost updates (CAS precondition)
✅ No partial writes (automatic rollback)
✅ Idempotency (re-processing = same result)
✅ Loop prevention (no self-triggering)
✅ Write policy enforcement (tool_only/immutable/derived)
✅ Automatic normalization (on every write)
✅ Audit trail (structured logs, patch archive)
```

---

## Timeline Summary

| Phase | Duration | Cumulative |
|-------|----------|------------|
| Phase 0: Scope Lock | ✅ Complete | - |
| Phase 1: Architecture | 1 week | 1 week |
| Phase 2: Infrastructure | 1 week | 2 weeks |
| Phase 3: ID & Rename | 3 days | 2.5 weeks |
| Phase 4: Parser & Descriptor | 1 week | 3.5 weeks |
| Phase 5: Registry Writer | 1 week | 4.5 weeks |
| Phase 6: Watcher | 1 week | 5.5 weeks |
| Phase 7: Reconciliation | 3 days | 6 weeks |
| Phase 8: CLI & Runbook | 1 week | 7 weeks |
| Phase 9: Validation | 3 days | 7.5 weeks |

**Total Duration:** ~8 weeks (with buffer)

---

## File Count Summary

| Category | Count | Lines of Code (Est.) |
|----------|-------|---------------------|
| Production Python | 19 files | ~5,000 LOC |
| Test Python | 15 files | ~3,000 LOC |
| Configuration | 3 files | ~300 lines YAML |
| Documentation | 5 files | ~1,000 lines MD |
| **Total** | **42 files** | **~9,300 lines** |

---

## Success Criteria Checklist (Final Acceptance)

### Functional Acceptance
- [ ] All 36 validation gates pass
- [ ] Integration tests pass (5 scenarios)
- [ ] Manual smoke test passes (add/modify/move/delete 5 files)
- [ ] Code coverage >80%
- [ ] No placeholder/skeleton code

### Operational Acceptance
- [ ] Watcher runs continuously for 24 hours without errors
- [ ] Reconciliation scan completes without errors
- [ ] Backup/rollback tested successfully
- [ ] Dry-run mode prevents writes
- [ ] CLI commands work as documented

### Quality Acceptance
- [ ] Pylint clean (no errors)
- [ ] Mypy clean (no type errors)
- [ ] Documentation complete (README, RUNBOOK, migration guide)
- [ ] Audit logs parseable and complete
- [ ] Registry passes strict validation

---

**Status:** This is what "DONE" looks like after all 9 phases complete.  
**Current State:** Phase 0 complete (2026-01-23)  
**Ready to Start:** Phase 1 (Architecture & Component Shells)
