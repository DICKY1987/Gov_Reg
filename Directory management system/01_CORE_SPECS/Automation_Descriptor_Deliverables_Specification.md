# Automation Descriptor Subsystem - Deliverables Specification

**Document Version**: 1.1  
**Date**: 2026-01-23  
**Status**: Final Specification  
**Related**: Automation_Descriptor_Phase_Plan.md (v1.3)

**Authority**: This document is the SSOT for requirements and contracts per the spec hierarchy defined in `Automation_Descriptor_Phase_Plan.md <spec_authority_hierarchy>`. All frozen contracts from the Phase Plan are binding on this specification.

---

## Executive Summary

Upon completion of the Automation Descriptor Subsystem implementation, the system will provide a production-ready, deterministic, and auditable pipeline for managing Python file metadata in a unified SSOT registry. The system enforces strict governance through a single-writer architecture, automatic normalization, and comprehensive validation with automatic rollback.

---

## 1. System Architecture Deliverables

### 1.1 Core Services

#### Registry Writer Service
**Purpose**: Single mutation point for all registry writes  
**Location**: `repo_autoops/automation_descriptor/registry_writer_service.py`  
**Key Features**:
- Only component permitted to write to UNIFIED_SSOT_REGISTRY.json
- Enforces promotion patch interface (no ad-hoc edits)
- Integrates: write policy validator + normalizer + backup manager
- Atomic pipeline: validate → normalize → backup → apply → verify
- Automatic rollback on any pipeline failure
- Supports fast mode (every write) and strict mode (CI/release)

**Contract Enforcement**:
- Tool-only fields rejected from user patches
- Immutable fields cannot be changed after creation
- Derived fields recomputed automatically
- CAS precondition (registry_hash) prevents lost updates

#### Watcher Daemon
**Purpose**: Filesystem event monitoring and work orchestration  
**Location**: `repo_autoops/automation_descriptor/watcher_daemon.py`  
**Key Features**:
- Monitors governed directories via watchdog library
- Stability-gate algorithm (min-age + mtime/size sampling)
- UPSERT-by-path event coalescing in SQLite queue
- Self-induced event suppression (loop prevention)
- Dry-run default mode (--live flag required for writes)
- Max actions per cycle safety cap

**Event Pipeline**:
1. Detect filesystem event (CREATE/MODIFY/MOVE/DELETE)
2. Enqueue with debounce/coalescing
3. Stability check (pushback if file still changing)
4. Classification (governed/unmanaged, file kind)
5. Acquire locks (path + doc_id + registry)
6. Execute pipeline (ID allocation → parse → promote)
7. Release locks, log completion

#### Work Queue Manager
**Purpose**: Persistent, transactional work item management  
**Location**: `repo_autoops/automation_descriptor/work_queue.py`  
**Key Features**:
- SQLite-backed queue (survives restarts)
- UPSERT-by-path prevents duplicate processing
- State machine: queued → stable_pending → stable_ready → running → done/retry/dead_letter
- Exponential backoff retry (5s, 15s, 45s, 2min, 5min, 15min, 30min, 1hr)
- Dead-letter queue for non-retryable failures

**Schema**:
```sql
CREATE TABLE work_items (
    work_item_id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    path TEXT NOT NULL UNIQUE,  -- UNIQUE on path alone for proper coalescing
    old_path TEXT,  -- for MOVE events
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    attempts INTEGER DEFAULT 0,
    status TEXT NOT NULL,
    error_code TEXT
);
```

**Dedupe Invariant**: One row per path. Status changes update the row in-place (do NOT create new rows). This ensures proper coalescing and prevents duplicate processing when status transitions occur.

### 1.2 Supporting Components

#### ID Allocator
**Location**: `repo_autoops/automation_descriptor/id_allocator.py`  
**Function**: Allocates 16-digit doc_ids from ID_REGISTRY.json (separate from SSOT registry)

#### File Renamer
**Location**: `repo_autoops/automation_descriptor/file_renamer.py`  
**Function**: Atomically renames files to include doc_id prefix, registers with suppression manager

#### Descriptor Extractor
**Location**: `repo_autoops/automation_descriptor/descriptor_extractor.py`  
**Function**: Wraps python_ast_parser.py, produces descriptor JSON + promotion payload

#### Normalizer
**Location**: `repo_autoops/automation_descriptor/normalizer.py`  
**Function**: Automatic normalization on write (uppercase rel_type, forward-slash paths)

#### Backup Manager
**Location**: `repo_autoops/automation_descriptor/backup_manager.py`  
**Function**: Creates timestamped backups before mutations, provides rollback

#### Reconciler
**Location**: `repo_autoops/automation_descriptor/reconciler.py`  
**Function**: Periodic scan for drift detection, repair via work queue

---

## 2. Data Structure Deliverables

### 2.1 UNIFIED_SSOT_REGISTRY.json

**Location**: `registry/UNIFIED_SSOT_REGISTRY.json`  
**Purpose**: Single source of truth for all file entities  
**Schema Version**: 2.2+ (unified timestamps + Python promotion columns)

**Core Identity Fields** (immutable):
- `doc_id` (16-digit)
- `record_kind` ("entity")
- `entity_kind` ("file")
- `first_seen_utc` (ISO 8601)

**Lifecycle Fields** (tool-owned):
- `status` (active/deleted/quarantine)
- `updated_utc` (ISO 8601)
- `updated_by` (tool identifier)

**Python Promotion Columns** (81-100):
- `py_parse_status` (ok/syntax_error/encoding_error/missing_file/timeout)
- `py_parsed_utc`
- `py_parser_id`
- `py_parser_version`
- `py_parse_error_count`
- `py_parse_error_first`
- `py_module_qualname`
- `py_is_package_init`
- `py_has_main_guard`
- `py_entrypoint_symbol`
- `py_cli_framework` (none/argparse/click/typer/fire/docopt/unknown)
- `py_imports_local` (array[string])
- `py_imports_external` (array[string])
- `py_imports_local_count`
- `py_imports_external_count`
- `py_function_count`
- `py_class_count`
- `py_docstring_1l`
- `py_descriptor_path`
- `py_descriptor_sha256`

### 2.2 Python Descriptor Artifacts

**Location**: `.dms/artifacts/python_descriptor/{doc_id}.v1.json`  
**Schema**: `config/PYTHON_FILE_DESCRIPTOR.yml`  
**Purpose**: Full parse results (imports, functions, classes, I/O patterns, env vars)

**Structure**:
```yaml
identity:
  doc_id: "1234567890123456"
  relative_path: "repo_autoops/example.py"
  
parse_provenance:
  parser_id: "python_ast_parser_astroid"
  parser_version: "1.0.0"
  parsed_utc: "2026-01-23T14:00:00Z"
  source_sha256: "abc123..."
  
structure:
  imports:
    local: ["repo_autoops.utils", "repo_autoops.config"]
    external: ["click", "pydantic"]
  functions: [...]
  classes: [...]
  
behavior:
  cli_framework: "click"
  entrypoints: ["main", "cli"]
  file_operations: [...]
  env_vars: [...]
```

### 2.3 Registry Promotion Patch Schema

**Purpose**: All registry updates MUST use this patch interface (no ad-hoc edits)  
**Schema ID**: `REGISTRY_PATCH_V2`  
**Contract**: Frozen in `Automation_Descriptor_Phase_Plan.md` (see `<patch_contract>`)

**Required Fields**:
```yaml
registry_hash: "sha256:abc123..."  # CAS precondition (SHA-256 of current registry bytes)
doc_id: "1234567890123456"         # Target entity
ops:                               # Array of patch operations
  - op: "set"
    path: "/py_parse_status"
    value: "ok"
  - op: "set"
    path: "/py_imports_local"
    value: ["repo_autoops.utils"]
actor:
  tool: "automation_descriptor"
  tool_version: "1.0.0"
utc_ts: "2026-01-23T14:00:00Z"     # Patch creation timestamp
work_item_id: "uuid-1234"          # Correlation ID for traceability
```

**CAS Enforcement**: Registry Writer Service MUST reject patch if `hash(current_registry_bytes) != patch.registry_hash`. This prevents lost updates in concurrent scenarios.

**Hash Scope**: SHA-256 of entire canonical registry file bytes (raw file content, not JSON-parsed). All tools MUST compute hash identically.

### 2.4 Registry Backups

**Location**: `.dms/backups/registry/UNIFIED_SSOT_REGISTRY_{timestamp}.json`  
**Naming**: ISO 8601 timestamp (e.g., `UNIFIED_SSOT_REGISTRY_20260123T140000Z.json`)  
**Retention**: Configurable (default: 30 days)  
**Purpose**: Automatic rollback on validation failure, manual recovery

---

## 3. Functional Capabilities

### 3.1 Automatic File Discovery & ID Assignment

**Trigger**: New Python file appears in governed directory  
**Process**:
1. Watcher detects CREATE event
2. File queued with stability check (750ms default)
3. Classification: governed, file_kind=python
4. Acquire path lock
5. Allocate doc_id from ID_REGISTRY.json
6. Atomic rename: `example.py` → `1234567890123456_example.py`
7. Create registry row (status=registered)
8. Register rename with suppression manager (prevents self-trigger)

**Output**:
- File renamed with doc_id
- Registry row created
- Audit log entry

### 3.2 Automatic Parsing & Descriptor Generation

**Trigger**: File with doc_id is stable  
**Process**:
1. Compute source_sha256
2. Compare with `py_source_sha256` in registry (skip if unchanged)
3. Parse via python_ast_parser.py (no execution)
4. Extract imports, functions, classes, CLI detection
5. Merge with declared metadata (if present)
6. Generate descriptor JSON
7. Generate promotion payload (20 columns)

**Output**:
- Descriptor artifact: `.dms/artifacts/python_descriptor/{doc_id}.v1.json`
- Promotion payload ready for registry

### 3.3 Automatic Registry Update

**Trigger**: Promotion payload ready  
**Process** (Registry Writer Service):
1. **Validate**: Check write policy (tool_only/immutable/derived)
2. **Normalize**: Uppercase rel_type, forward-slash paths
3. **Backup**: Create timestamped backup of current registry
4. **Apply**: Atomic patch (temp-file-then-replace + fsync)
5. **Verify**: Fast validation (schema + referential + policy)
6. **Commit**: Release locks, log success

**On Failure**:
- Automatic rollback from backup
- Error logged to errors.jsonl
- Work item moved to retry or dead-letter

**Output**:
- Registry updated atomically
- Backup created
- Patch logged to `.dms/patches/registry/`

### 3.4 Move/Delete Handling

**MOVE Event**:
1. Detect old_path → new_path
2. Update registry row: `relative_path = new_path`
3. Detect doc_id rename (self-induced vs external)
4. Update descriptor if needed

**DELETE Event**:
1. Set `status = deleted` (tombstone)
2. Clean up descriptor artifact (optional)
3. Log deletion

### 3.5 Reconciliation & Drift Repair

**Trigger**: Scheduled (e.g., hourly, nightly)  
**Process**:
1. Scan governed directories
2. Detect: missing registry rows, moved files, stale hashes
3. Enqueue repair work items via work queue (deduplicates)
4. Run full pipeline for each repair

**Output**:
- Registry consistent with filesystem
- Drift repaired without duplicate processing

### 3.6 Validation Modes

**Fast Mode** (every write):
- Schema validation (field types, required fields)
- Referential integrity (doc_id exists, paths valid)
- Write policy compliance (tool_only/immutable/derived)

**Strict Mode** (CI/release):
- All fast mode checks
- Cross-record consistency
- Derived field correctness
- Normalization completeness

**Trigger**: Automatic (fast) or `cli.py validate-registry --strict`

---

## 4. Event Types & Handlers

### 4.1 Filesystem Events

**Canonical Event Enum** (frozen in Phase Plan `<event_contract>`):

**FILE_ADDED**: New file created → ID allocation + parse  
**FILE_MODIFIED**: Existing file changed → re-parse if hash changed  
**FILE_MOVED**: File renamed/moved → update registry path  
**FILE_DELETED**: File removed → tombstone + cleanup

**Legacy Compatibility**: `FILE_CREATED` from older documents is automatically mapped to `FILE_ADDED` on intake. All new code MUST emit canonical enum values only.

### 4.2 Policy Events

**WRITE_POLICY_VIOLATION**: Patch rejected, error logged  
**NORMALIZATION_REQUIRED**: Auto-normalize triggered  
**DERIVATION_DRIFT**: Recompute derived fields  
**VALIDATION_FAILED**: Auto-rollback to backup

---

## 5. Operational Interfaces

### 5.1 CLI Commands

**Start Watcher** (dry-run default):
```bash
python cli.py start-watcher
python cli.py start-watcher --live  # enables writes
```

**Stop Watcher**:
```bash
python cli.py stop-watcher
```

**Run Reconciliation**:
```bash
python cli.py reconcile
python cli.py reconcile --scope=repo_autoops  # specific directory
```

**Describe File**:
```bash
python cli.py describe-file --path=repo_autoops/example.py
python cli.py describe-file --doc-id=1234567890123456
```

**Migrate Registry** (Deprecated aliases → canonical UNIFIED_SSOT_REGISTRY.json):
```bash
python cli.py migrate-registry
python cli.py migrate-registry --backup-first
```

**Notes**: 
- Migrates from `FILE_REGISTRY.json`, `FILE_REGISTRY_v2.json`, or any deprecated alias
- Target is always `registry/UNIFIED_SSOT_REGISTRY.json` (canonical path, frozen in Phase Plan)
- Converts `allocated_at` → `first_seen_utc` during migration
- All deprecated aliases become read-only after migration

**Validate Registry**:
```bash
python cli.py validate-registry           # fast mode
python cli.py validate-registry --strict  # comprehensive
```

### 5.2 Configuration Files

**WATCHER_CONFIG.yml**:
```yaml
watch_roots:
  - repo_autoops/
  - scripts/

ignore_patterns:
  - "**/.git/**"
  - "**/__pycache__/**"
  - "**/*.pyc"
  - "**/.dms/**"

stability_window_ms: 750
debounce_window_ms: 500
max_actions_per_cycle: 100

dry_run_default: true

retry_backoff_seconds: [5, 15, 45, 120, 300, 900, 1800, 3600]
max_retry_attempts: 8
```

**PYTHON_FILE_DESCRIPTOR.yml**:
- Schema definition for descriptor artifacts
- Required sections: identity, parse_provenance, structure, behavior

### 5.3 Audit Logs

**actions.jsonl**:
```json
{"work_item_id": "...", "event_id": "...", "stage_id": "S5_ID_AND_ROW_UPSERT", "doc_id": "...", "path": "...", "result": "ok", "duration_ms": 123}
```

**errors.jsonl**:
```json
{"work_item_id": "...", "event_id": "...", "stage_id": "S6_ANALYZE_PYTHON", "doc_id": "...", "path": "...", "error_code": "SYNTAX_ERROR", "message": "...", "utc": "..."}
```

---

## 6. Quality Gates & Verification

### 6.1 Unit Test Coverage

**Target**: >80% line coverage  
**Test Files** (15):
- test_work_queue.py
- test_stability_checker.py
- test_lock_manager.py
- test_suppression_manager.py
- test_id_allocator.py
- test_event_handlers.py
- test_descriptor_extractor.py
- test_normalizer.py
- test_backup_manager.py
- test_write_policy_validator.py
- test_registry_writer_service.py
- test_cas_precondition.py
- test_reconciler.py
- test_loop_prevention.py
- test_integration.py

### 6.2 Validation Gates (30 Total)

**Critical Gates**:
1. Single-writer enforcement (only Registry Writer Service writes)
2. Promotion patch interface (all updates via patches)
3. Automatic backup before mutation
4. Automatic rollback on validation failure
5. CAS precondition (prevents lost updates)
6. Loop prevention (no self-triggering)
7. Write policy enforcement (tool_only/immutable/derived)

**Full List**: See Phase Plan validation_gates section

### 6.3 Integration Test Scenarios

**Scenario 1**: Add 10 Python files
- Verify all assigned doc_ids
- Verify all registry rows created
- Verify all descriptors generated
- Verify no duplicate processing

**Scenario 2**: Modify file
- Verify re-parse triggered
- Verify registry updated
- Verify descriptor updated
- Verify idempotency (no change if hash same)

**Scenario 3**: Move file
- Verify registry path updated
- Verify descriptor path updated
- Verify doc_id preserved

**Scenario 4**: Delete file
- Verify tombstone created
- Verify descriptor cleaned up

**Scenario 5**: Introduce drift
- Manually edit registry
- Run reconcile
- Verify drift repaired
- Verify no duplicate queue entries

---

## 7. System Guarantees

### 7.1 Correctness Guarantees

1. **Single Source of Truth**: UNIFIED_SSOT_REGISTRY.json is authoritative
2. **Single Writer**: Registry Writer Service is only mutation point
3. **Atomic Operations**: All registry writes are atomic (temp-file-replace + fsync)
4. **No Lost Updates**: CAS precondition (registry_hash) enforced
5. **No Partial Writes**: Validation failure triggers automatic rollback
6. **Idempotency**: Re-processing same file produces same result
7. **Loop Prevention**: Watcher doesn't retrigger on own writes

### 7.2 Consistency Guarantees

1. **Write Policy Enforcement**: tool_only/immutable/derived rules enforced
2. **Normalization**: Automatic on every write (not manual)
3. **Referential Integrity**: Fast validation on every write
4. **Derived Fields**: Automatically recomputed on reconcile
5. **Audit Trail**: Every action logged with structured metadata

### 7.3 Availability Guarantees

1. **Persistent Queue**: Work survives daemon restarts
2. **Retry Logic**: Transient errors auto-retry with backoff
3. **Dead-Letter Queue**: Non-retryable errors isolated
4. **Quarantine**: Problematic files isolated, don't block pipeline
5. **Graceful Degradation**: Dry-run mode allows safe testing

---

## 8. Operational Characteristics

### 8.1 Performance

**Throughput**: 50+ files per batch without errors  
**Latency**: 
- Stability window: 750ms (configurable)
- Parse time: <1s for typical Python file
- Registry update: <100ms (atomic write)

**Scalability**:
- Single daemon per project (no distributed coordination)
- Queue-based design supports backlog handling
- Reconciliation scans scale with directory size

### 8.2 Observability

**Metrics Available**:
- Work items queued/processed/failed
- Parse success/failure rate
- Validation pass/fail rate
- Lock contention events
- Retry/dead-letter counts

**Logs**:
- Structured JSONL (actions.jsonl, errors.jsonl)
- Stage-correlated (work_item_id, event_id, stage_id)
- Parseable for analytics

### 8.3 Safety Rails

**Dry-Run Default**: Watcher requires `--live` flag for writes  
**Max Actions Cap**: Prevents runaway processing (default: 100/cycle)  
**Quarantine Over Delete**: Problematic files moved, not destroyed  
**Backup Retention**: 30 days default, configurable

---

## 9. Documentation Deliverables

### 9.1 User Documentation

**README.md**: Overview, quickstart, CLI reference  
**RUNBOOK.md**: Setup, operation, troubleshooting, rollback procedures  
**REGISTRY_MIGRATION.md**: Migration guide from deprecated aliases (FILE_REGISTRY*.json) to canonical UNIFIED_SSOT_REGISTRY.json  
**REGISTRY_WRITE_POLICY.md**: Write policy rules and examples

### 9.2 Developer Documentation

**Inline Code Comments**: Critical sections documented  
**Architecture Diagrams**: Component relationships, data flows  
**Schema Documentation**: PYTHON_FILE_DESCRIPTOR.yml, registry columns  
**Test Documentation**: Test strategy, coverage requirements

---

## 10. Known Limitations (Documented)

### 10.1 Phase 1 Scope Boundaries

**Not Included**:
- Multi-process/distributed coordination
- Edge records (entity relationships)
- Generator records (derived artifact definitions)
- Generator staleness tracking
- Automatic module/process validation
- SQLite registry backend (registry remains JSON; SQLite is used for work queue only)
- Real-time UI/dashboard

### 10.2 Platform Limitations

**Tested On**: Windows 10+  
**Expected to Work**: Unix-like systems (not validated)  
**Single Daemon**: One instance per project

### 10.3 File Type Limitations

**Phase 1**: Python files only  
**Future**: Markdown, YAML, JSON (separate plugins)

---

## 11. Success Criteria (Final Acceptance)

### 11.1 Functional Acceptance

- [ ] All 30 validation gates pass
- [ ] Integration tests pass (5 scenarios)
- [ ] Manual smoke test passes (add/modify/move/delete 5 files)
- [ ] Code coverage >80%
- [ ] No placeholder/skeleton code

### 11.2 Operational Acceptance

- [ ] Watcher runs continuously for 24 hours without errors
- [ ] Reconciliation scan completes without errors
- [ ] Backup/rollback tested successfully
- [ ] Dry-run mode prevents writes
- [ ] CLI commands work as documented

### 11.3 Quality Acceptance

- [ ] Pylint clean (no errors)
- [ ] Mypy clean (no type errors)
- [ ] Documentation complete (README, RUNBOOK, migration guide)
- [ ] Audit logs parseable and complete
- [ ] Registry passes strict validation

---

## 12. Phase 2 Roadmap (Future Enhancements)

### 12.1 Near-Term (3-6 months)

- Edge records (entity relationships)
- Generator records (derived artifacts)
- Generator staleness tracking + rebuild automation
- Automatic module/process validation

### 12.2 Mid-Term (6-12 months)

- SQLite backend migration
- Telemetry/metrics (Prometheus/OpenTelemetry)
- Web UI for monitoring
- Performance benchmarking

### 12.3 Long-Term (12+ months)

- Multi-language support (JavaScript, Java, etc.)
- Distributed coordination (multi-daemon)
- Cloud deployment
- Advanced analytics/visualizations

---

## 13. Maintenance & Support

### 13.1 Routine Maintenance

**Daily**: Review error logs, check queue backlog  
**Weekly**: Run strict validation, review quarantine  
**Monthly**: Backup cleanup, reconciliation audit  
**Quarterly**: Dependency updates, security patches

### 13.2 Troubleshooting

**Common Issues**:
- Watcher not detecting files → check ignore patterns
- Parse failures → check syntax errors, encoding
- Validation failures → check write policy violations
- Lock contention → check for stuck processes

**Resolution**:
- Review errors.jsonl for details
- Use describe-file CLI for diagnostics
- Run reconcile to repair drift
- Restore from backup if needed

### 13.3 Support Resources

**Runbook**: Operational procedures  
**Logs**: Structured audit trail  
**Tests**: Reproduce issues in test environment  
**Backups**: Rollback capability

---

## Appendix A: File Inventory

### A.1 Source Code (15 files)

```
repo_autoops/automation_descriptor/
├── __init__.py
├── watcher_daemon.py
├── work_queue.py
├── stability_checker.py
├── lock_manager.py
├── suppression_manager.py
├── classifier.py
├── id_allocator.py
├── file_renamer.py
├── event_handlers.py
├── descriptor_extractor.py
├── normalizer.py
├── backup_manager.py
├── write_policy_validator.py
├── registry_writer_service.py
├── reconciler.py
├── reconcile_scheduler.py
├── audit_logger.py
└── cli.py
```

### A.2 Configuration (3 files)

```
config/
├── WATCHER_CONFIG.yml
└── PYTHON_FILE_DESCRIPTOR.yml

registry/
└── UNIFIED_SSOT_REGISTRY.json
```

### A.3 Tests (15 files)

```
tests/automation_descriptor/
├── test_work_queue.py
├── test_stability_checker.py
├── test_lock_manager.py
├── test_suppression_manager.py
├── test_id_allocator.py
├── test_event_handlers.py
├── test_descriptor_extractor.py
├── test_normalizer.py
├── test_backup_manager.py
├── test_write_policy_validator.py
├── test_registry_writer_service.py
├── test_cas_precondition.py
├── test_reconciler.py
├── test_loop_prevention.py
└── test_integration.py
```

### A.4 Documentation (5 files)

```
docs/automation_descriptor/
├── README.md
├── RUNBOOK.md
├── REGISTRY_MIGRATION.md
└── REGISTRY_WRITE_POLICY.md

docs/
└── 2026012015460001_COLUMN_DICTIONARY.md (updated)
```

### A.5 Runtime Directories

```
.dms/
├── artifacts/
│   ├── python_descriptor/    # {doc_id}.v1.json
│   └── index/                # derived indexes
├── backups/
│   └── registry/             # timestamped backups
├── patches/
│   └── registry/             # patch logs
├── runtime/
│   ├── work_queue.sqlite
│   └── locks/
│       ├── path/
│       ├── doc/
│       └── registry.lock
├── logs/
│   ├── actions.jsonl
│   └── errors.jsonl
└── quarantine/               # problematic files
```

---

## Appendix B: Glossary

**SSOT**: Single Source of Truth - UNIFIED_SSOT_REGISTRY.json  
**CAS**: Compare-and-Swap - precondition preventing lost updates  
**Doc ID**: 16-digit unique identifier for files  
**Promotion**: Process of updating registry columns from descriptor  
**Patch**: Structured update intent, enforced by Registry Writer Service  
**Fast Validation**: Schema + referential + policy (every write)  
**Strict Validation**: Comprehensive checks (CI/release)  
**Quarantine**: Isolated storage for files that fail processing  
**Dead-Letter**: Queue for non-retryable failures  
**Tombstone**: Registry row with status=deleted

---

## Appendix C: Frozen Contracts Compliance

This specification complies with all frozen contracts defined in `Automation_Descriptor_Phase_Plan.md v1.3 <frozen_contracts>`. The following contracts are binding:

### C.1 Registry Contract ✅
- **Canonical Path**: `registry/UNIFIED_SSOT_REGISTRY.json` (enforced throughout)
- **Write-Canonical-Only**: All writes target canonical path only (see Section 3.3, 5.1)
- **Deprecated Aliases**: `FILE_REGISTRY*.json` are read-only migration inputs (see Section 5.1 migrate-registry)

### C.2 Patch Contract ✅
- **Schema ID**: `REGISTRY_PATCH_V2` (defined in Section 2.3)
- **CAS Required**: `registry_hash` is required field, enforced by Registry Writer Service (see Section 2.3, 7.1)
- **Hash Scope**: SHA-256 of entire canonical registry file bytes (see Section 2.3)

### C.3 Timestamp Contract ✅
- **Canonical Fields**: `first_seen_utc`, `updated_utc`, `updated_by` (defined in Section 2.1)
- **Removed Fields**: `allocated_at`, `created_utc`, `id_assigned_utc` (migrated during registry migration, see Section 5.1)

### C.4 Queue Contract ✅
- **Dedupe Invariant**: `UNIQUE(path)` only, NOT `UNIQUE(path, status)` (fixed in Section 1.1)
- **In-Place Updates**: Status changes update row in-place (documented in Section 1.1)

### C.5 Lock Contract ✅
- **Total Order**: `path_lock → doc_lock → registry_lock` (enforced in pipeline, see Section 3.1-3.3)
- **Lock Files**: `.dms/runtime/locks/{path|doc|registry}/` (see Appendix A.5)

### C.6 Event Contract ✅
- **Canonical Enum**: `FILE_ADDED`, `FILE_MODIFIED`, `FILE_MOVED`, `FILE_DELETED` + policy events (see Section 4.1)
- **Legacy Mapping**: `FILE_CREATED → FILE_ADDED` on intake (documented in Section 4.1)

### C.7 Path Contract ✅
- **Canonical Field**: `relative_path` (POSIX forward-slash, repo-relative) (used throughout, e.g., Section 2.2)
- **Runtime-Only Fields**: `current_path`, `abs_path` not stored in registry

**Compliance Verified**: 2026-01-23  
**Phase Plan Version**: 1.3  
**Deliverables Spec Version**: 1.1

---

**End of Deliverables Specification**
