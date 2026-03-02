# Automation Descriptor Subsystem - Phase Plan Execution

<prompt_template name="Autonomous Project Delivery — Automation Descriptor Subsystem" version="1.3">
  <context>
    <mission>
      Deliver a complete, working Automation Descriptor Subsystem end-to-end (plan → build → test → runnable scripts → runbook),
      with objective validation gates and test-first development. This system will automatically generate descriptors for Python files,
      assign doc_ids, update the UNIFIED_SSOT_REGISTRY.json, and maintain derived artifacts.
    </mission>

    <usage_notes>
      - This implements the full pipeline from filesystem watcher to registry updates
      - Integrates with UNIFIED_SSOT_REGISTRY.json (canonical) and doc_id allocation system
      - Follows deterministic artifact generation patterns
    </usage_notes>

    <spec_authority_hierarchy>
      IMPORTANT: This hierarchy prevents implementation drift from conflicting documents.

      1. **Automation_Descriptor_Deliverables_Specification.md** = SSOT for requirements + contracts
      2. **Automation_Descriptor_Phase_Plan.md (THIS FILE)** = Build order + frozen contracts (may not redefine filenames/contracts)
      3. **ChatGPT-Automation Descriptor Subsystem.md + .docx** = DEPRECATED legacy/reference; conflicts are resolved in favor of #1 and #2

      Where any document conflicts with this hierarchy, the higher-ranked document wins.
    </spec_authority_hierarchy>
  </context>

  <frozen_contracts>
    <!-- These contracts are FROZEN and must not be redefined by any other document or implementation -->

    <registry_contract>
      <canonical_path>registry/UNIFIED_SSOT_REGISTRY.json</canonical_path>
      <deprecated_aliases>
        - FILE_REGISTRY.json (read-only migration input)
        - FILE_REGISTRY_v2.json (read-only migration input)
        - 2026012201113004_FILE_REGISTRY_v2.json (read-only migration input)
      </deprecated_aliases>
      <write_canonical_only>true</write_canonical_only>
      <rule>ALL writes MUST target canonical_path. Deprecated aliases are READ-ONLY migration inputs.</rule>
    </registry_contract>

    <patch_contract>
      <schema_id>REGISTRY_PATCH_V2</schema_id>
      <required_fields>
        - registry_hash (string, SHA-256 of current registry bytes - CAS precondition, REQUIRED)
        - doc_id (string, 16-digit identifier)
        - ops (array of patch operations)
        - actor (object: tool, tool_version)
        - utc_ts (string, ISO 8601 timestamp)
        - work_item_id (string, correlation ID)
      </required_fields>
      <cas_rule>Registry Writer Service MUST reject patch if hash(current_registry_bytes) != patch.registry_hash</cas_rule>
      <hash_scope>SHA-256 of entire canonical registry file bytes (not JSON-parsed content)</hash_scope>
    </patch_contract>

    <timestamp_contract>
      <canonical_fields>
        - first_seen_utc (immutable, set on creation)
        - updated_utc (updated on every mutation)
        - updated_by (tool identifier)
      </canonical_fields>
      <removed_fields>
        - allocated_at (REMOVED - migrated to first_seen_utc)
        - created_utc (REMOVED - use first_seen_utc)
        - id_assigned_utc (REMOVED - use first_seen_utc)
      </removed_fields>
      <migration_rule>On migration, allocated_at/created_utc → first_seen_utc; patches must NOT enforce "allocated_at must exist"</migration_rule>
    </timestamp_contract>

    <queue_contract>
      <dedupe_invariant>One row per path (UNIQUE(path), NOT UNIQUE(path, status))</dedupe_invariant>
      <schema>
        CREATE TABLE work_items (
            work_item_id TEXT PRIMARY KEY,
            event_type TEXT NOT NULL,
            path TEXT NOT NULL UNIQUE,  -- UNIQUE on path alone for proper coalescing
            old_path TEXT,              -- for MOVE events
            first_seen TEXT NOT NULL,
            last_seen TEXT NOT NULL,
            attempts INTEGER DEFAULT 0,
            status TEXT NOT NULL,
            error_code TEXT
        );
      </schema>
      <rule>Status changes update the row in-place; they do NOT create new rows.</rule>
    </queue_contract>

    <lock_contract>
      <total_order>path_lock → doc_lock → registry_lock</total_order>
      <rule>Locks MUST be acquired in this order. Never acquire path_lock while holding registry_lock.</rule>
      <lock_files>
        - .dms/runtime/locks/path/{path_hash}.lock
        - .dms/runtime/locks/doc/{doc_id}.lock
        - .dms/runtime/locks/registry.lock
      </lock_files>
      <timeout>30 seconds default; configurable in WATCHER_CONFIG.yml</timeout>
      <stale_recovery>Locks older than 5 minutes are considered stale and may be forcibly released</stale_recovery>
    </lock_contract>

    <event_contract>
      <canonical_enum>
        - FILE_ADDED
        - FILE_MODIFIED
        - FILE_MOVED
        - FILE_DELETED
        - WRITE_POLICY_VIOLATION
        - NORMALIZATION_REQUIRED
        - DERIVATION_DRIFT
        - VALIDATION_FAILED
        - RECONCILE_TICK
      </canonical_enum>
      <legacy_mapping>
        FILE_CREATED → FILE_ADDED (for compatibility with legacy docs)
      </legacy_mapping>
      <rule>All producers MUST emit canonical enum values. Legacy values are mapped on intake.</rule>
    </event_contract>

    <path_contract>
      <canonical_field>relative_path</canonical_field>
      <format>POSIX forward-slash, repo-relative (e.g., "repo_autoops/tools/example.py")</format>
      <derived_fields>
        - current_path (runtime-only, not stored in registry)
        - abs_path (runtime-only, not stored in registry)
      </derived_fields>
      <rule>Only relative_path is used as SSOT key. Lock keys and dedupe keys MUST use normalized relative_path.</rule>
    </path_contract>
  </frozen_contracts>

  <inputs>
    <project_brief>
      Build an Automation Descriptor Subsystem that:
      1. Watches filesystem for Python file changes (create/modify/move/delete)
      2. Assigns stable 16-digit doc_ids to governed files
      3. Parses Python files via AST (no execution) to extract structure
      4. Generates descriptor JSON artifacts in .dms/artifacts/python_descriptor/
      5. Promotes key fields (parse status, imports, CLI detection, etc.) to File Registry columns
      6. Maintains idempotent, atomic updates with proper locking
      7. Provides reconciliation scan for drift detection
      8. Implements retry logic and error handling with quarantine
      
      Integration points:
      - UNIFIED_SSOT_REGISTRY.json (canonical; replaces FILE_REGISTRY.json, FILE_REGISTRY_v2.json)
      - Existing AST parser (DOC-SCRIPT-0996__python_ast_parser.py)
      - ID allocation system (ID_REGISTRY.json - separate from SSOT registry, SEQ_ALLOCATOR_SPEC.md)
      - Column dictionary (2026012015460001_COLUMN_DICTIONARY.md)
      - Write policy enforcement (tool_only, immutable, derived rules)
      - CAS protection (registry_hash precondition)
    </project_brief>
    
    <target_environment>local Windows development, Python 3.10+</target_environment>
    
    <tech_preferences>
      - Python 3.10+ (existing codebase standard)
      - SQLite for work queue
      - watchdog library for filesystem events
      - atomic file operations for registry updates
      - jsonlines for audit logs
    </tech_preferences>
    
    <constraints>
      <time_budget>Complete, production-ready implementation</time_budget>
      <security_or_compliance>
        - No execution of watched Python files (AST only)
        - Atomic registry updates (no partial state)
        - Proper lock files to prevent race conditions
        - Audit trail for all actions
      </security_or_compliance>
      <performance_targets>
        - Debounce filesystem events (500-750ms default)
        - Handle batch operations efficiently
        - Minimal registry writes (hash-based change detection)
      </performance_targets>
    </constraints>
    
    <delivery_mode>
      <autopilot>true</autopilot>
      <enterprise_mode>true</enterprise_mode>
    </delivery_mode>
  </inputs>

  <task_analysis>
    <original_request>
      Implement production-ready Automation Descriptor Subsystem with full integration to UNIFIED_SSOT_REGISTRY.json.

      NOTE: "ChatGPT-Automation Descriptor Subsystem.md" is a DEPRECATED reference document.
      Where it conflicts with this plan or Automation_Descriptor_Deliverables_Specification.md,
      those conflicts are resolved in favor of this plan (see spec_authority_hierarchy above).
      Key conflicts resolved:
      - Registry target: UNIFIED_SSOT_REGISTRY.json (NOT FILE_REGISTRY.json)
      - Event enum: FILE_ADDED (NOT FILE_CREATED)
      - Path field: relative_path (NOT current_path)
      - Timestamp fields: first_seen_utc, updated_utc (NOT allocated_at)
      - Queue dedupe: UNIQUE(path) (NOT UNIQUE(path, status))
    </original_request>
    
    <specificity_transformation>
      <objective>
        Create a working watcher daemon that:
        1. Detects Python file changes in governed directories
        2. Allocates doc_ids and renames files atomically
        3. Parses files and generates descriptor artifacts
        4. Updates registry with promoted columns (py_parse_status, py_imports_*, etc.)
        5. Maintains consistency via locks, queues, and reconciliation
        6. Enforces single-writer pattern via Registry Writer Service (only component that mutates registry)
        7. Normalizes on ingest (not as separate step)
        8. Provides automatic backup/rollback on validation failures
      </objective>
      
      <methodology>
        Phase 0: Lock down scope and validate existing dependencies
        Phase 1: Design architecture and file structure
        Phase 2: Implement work queue and locking infrastructure
        Phase 3: Build ID allocation and file renaming
        Phase 4: Implement AST parsing and descriptor generation
        Phase 5: Build registry update and promotion logic
        Phase 6: Add reconciliation scanner
        Phase 7: Validation gates (unit tests, integration tests, end-to-end)
        Phase 8: Packaging and runbook
      </methodology>
      
      <success_criteria>
        1. All tests pass (unit + integration)
        2. Watcher can process 50+ files in batch without errors
        3. Registry updates are atomic and idempotent
        4. Registry Writer Service is the only component that mutates registry
        5. All promotion patches go through single-writer (no ad-hoc edits)
        6. Descriptors match schema and contain all required fields
        7. Normalization happens automatically on every write
        8. Validation failures trigger automatic rollback to backup
        9. Fast validation runs on every write; strict validation available for CI
        10. Reconciliation scan detects and repairs drift
        11. Error handling covers all failure modes with proper quarantine
        12. Runbook allows operator to start/stop/monitor the system
        13. No placeholder/skeleton code in final delivery
      </success_criteria>
    </specificity_transformation>
    
    <classification>
      <complexity>complex</complexity>
      <domain>technical</domain>
      <quality>production</quality>
    </classification>
  </task_analysis>

  <assumptions_scope>
    <assumptions>
      - Python 3.10+ is available
      - watchdog library will be installed via pip
      - Unified SSOT Registry schema is stable (one canonical file: UNIFIED_SSOT_REGISTRY.json)
      - ID_REGISTRY.json (separate file) contains valid counter state for doc_id allocation
      - .dms/ directory structure can be created in project root
      - Windows filesystem semantics (backslashes, file locking behavior)
      - Single-writer assumption enforced via Registry Writer Service (not just convention)
      - Governed directories are defined in WATCHER_CONFIG.yml
      - AST parser (DOC-SCRIPT-0996__python_ast_parser.py) is functional
      - Watcher runs in dry-run mode by default (explicit flag required for writes)
      - Self-induced events are suppressed via timestamp-based suppression window
      - Write policy enforcement is mandatory (not optional)
      - CAS precondition (registry_hash) prevents lost updates
      - Unified timestamp fields used (first_seen_utc, updated_utc, not allocated_at)
      - Normalization happens on write (not as separate cleanup step)
      - Backups created automatically before registry mutations
    </assumptions>
    
    <in_scope>
      - Filesystem watcher with stability algorithm (not just time-based debounce)
      - Work queue (SQLite-based) with UPSERT-by-path coalescing and retry/dead-letter handling
      - Path, doc_id, and registry locking with defined lock ordering
      - Self-induced event suppression (loop prevention)
      - ID allocation and atomic file rename
      - Move and delete event handling (path updates, tombstones, artifact cleanup)
      - Python AST parsing (imports, functions, classes, CLI detection)
      - Descriptor JSON generation
      - Registry promotion of 20 Python columns (py_parse_status → py_descriptor_sha256)
      - Registry Writer Service (single component that mutates registry, enforces all policies)
      - Promotion patches (all updates go through single-writer, no ad-hoc edits)
      - Atomic registry updates with automatic backup before mutation
      - Automatic rollback on validation failures
      - Normalization on write (uppercase rel_type, path separators, etc.)
      - Fast validation mode (every write: schema + referential + policy)
      - Strict validation mode (CI/release: comprehensive checks)
      - Reconciliation scanner with scheduled ticks and queue deduplication
      - Retry logic with exponential backoff
      - Error logging and quarantine with structured observability
      - Safety rails: dry-run default, max actions per cycle, quarantine over deletes
      - Event types: FILE_ADDED/MODIFIED/MOVED/DELETED, WRITE_POLICY_VIOLATION, NORMALIZATION_REQUIRED, DERIVATION_DRIFT, VALIDATION_FAILED
      - Unit and integration tests including loop prevention and move/delete
      - CLI commands: start-watcher, reconcile, describe-file, with dry-run flags
      - Runbook with setup/run/troubleshoot
    </in_scope>
    
    <out_of_scope>
      - Multi-process/distributed coordination (single daemon only)
      - Real-time UI or web dashboard
      - Cloud deployment (local only)
      - Non-Python file descriptors (markdown, YAML, etc.)
      - Execution of Python files (AST analysis only)
      - Git integration (commit/push automation)
      - Performance optimization beyond basic caching
      - Edge records (relationships between entities) - deferred to Phase 2
      - Generator records (derived artifact definitions) - deferred to Phase 2
      - Generator staleness tracking and rebuild triggers - deferred to Phase 2
      - Automatic module/process validator enforcement - deferred to Phase 2
      - SQLite **registry** backend (registry remains JSON; SQLite is used for work queue only)
    </out_of_scope>
    
    <definition_of_done>
      - [ ] All Python source files created and tested
      - [ ] Canonical registry filename chosen: UNIFIED_SSOT_REGISTRY.json (all tools updated)
      - [ ] FILE_REGISTRY.json and FILE_REGISTRY_v2.json marked as deprecated aliases
      - [ ] ID_REGISTRY.json confirmed as separate file (doc_id counter only)
      - [ ] Registry Writer Service implemented as single mutation point
      - [ ] All registry updates go through promotion patch interface (no ad-hoc edits)
      - [ ] WATCHER_CONFIG.yml exists with sensible defaults including safety rails
      - [ ] PYTHON_FILE_DESCRIPTOR.yml schema documented
      - [ ] Column dictionary updated with Python promotion columns (81-100)
      - [ ] Unified timestamp fields implemented (first_seen_utc, updated_utc; allocated_at removed)
      - [ ] Work queue database schema defined with UPSERT-by-path, retry, and dead-letter handling
      - [ ] Stability algorithm implemented (min-age, mtime/size sampling, pushback)
      - [ ] Self-induced event suppression implemented and tested
      - [ ] Lock ordering documented and enforced (path_lock → doc_lock → registry_lock, never reverse)
      - [ ] Registry lock file added to runtime directory
      - [ ] Move event handler updates registry path and handles doc_id renames
      - [ ] Delete event handler creates tombstones and cleans up artifacts
      - [ ] ID allocation integrated with existing ID_REGISTRY.json (separate from SSOT registry)
      - [ ] Descriptor extractor produces valid JSON matching schema
      - [ ] Write policy enforcement baked into Registry Writer Service (tool_only, immutable, derived rules)
      - [ ] Normalization runs automatically on every write (uppercase rel_type, path separators, etc.)
      - [ ] Automatic backup created before every registry mutation
      - [ ] Automatic rollback on validation failure
      - [ ] CAS precondition enforced: patches require registry_hash, reject on mismatch
      - [ ] Fast validation mode implemented (schema + referential + policy on every write)
      - [ ] Strict validation mode implemented (comprehensive checks for CI/release)
      - [ ] Validation failures are fail-fast (strict mode, no partial writes)
      - [ ] Event types implemented: FILE_ADDED/MODIFIED/MOVED/DELETED, WRITE_POLICY_VIOLATION, NORMALIZATION_REQUIRED, DERIVATION_DRIFT, VALIDATION_FAILED
      - [ ] Reconciliation scheduler integrated with work queue (deduplication)
      - [ ] Structured logging includes: work_item_id, event_id, stage_id, doc_id, path, result, error_code, duration_ms
      - [ ] Unit tests cover: parser, extractor, queue coalescing, locks, ID allocation, stability algorithm
      - [ ] Write policy enforcement test: verify tool_only/immutable/derived violations rejected
      - [ ] CAS precondition test: verify stale registry_hash rejected (lost update prevented)
      - [ ] Normalization test: verify automatic normalization on write
      - [ ] Backup/rollback test: verify automatic backup and rollback on validation failure
      - [ ] Single-writer test: verify only Registry Writer Service can mutate registry
      - [ ] Loop prevention test: verify watcher doesn't retrigger on own renames/writes
      - [ ] Integration test: add 10 Python files, verify registry + descriptors
      - [ ] End-to-end test: modify file, verify re-parse and update
      - [ ] Move/Delete test: move file, verify path update; delete file, verify tombstone
      - [ ] Reconciliation test: manual drift introduced, scan repairs it without duplicate queue entries
      - [ ] Error handling test: syntax error in Python file, verify quarantine
      - [ ] Safety rails test: dry-run mode, max actions cap
      - [ ] Fast/strict validation test: verify fast mode on write, strict mode on demand
      - [ ] CLI commands work: start-watcher (with --live flag), stop-watcher, reconcile, describe-file
      - [ ] Runbook includes: prerequisites, setup, run, logs, troubleshoot, rollback
      - [ ] Documentation: README for subsystem, inline code comments where needed
      - [ ] Phase 2 scope documented: edge/generator records, generator staleness tracking, automatic module validators
    </definition_of_done>
  </assumptions_scope>

  <phase_plan>
    | Phase | Goals | Deliverables | Validation Gates | Exit Criteria |
    |-------|-------|--------------|------------------|---------------|
    | **0. Scope Lock** | Validate dependencies, confirm existing files, registry filename decision | Dependency checklist, scope document, registry migration plan | Verify all referenced files exist, canonical registry chosen | All files found, UNIFIED_SSOT_REGISTRY.json confirmed |
    | **1. Architecture** | Design components, directory structure, data flows, lock ordering, write policy enforcement, CAS protection, schema migration | Architecture doc, file tree, sequence diagrams, lock order spec, write policy validator spec, CAS protocol, unified timestamp schema | Peer review, validate against requirements, write policy completeness | Design approved, no open questions, registry hardening complete |
    | **2. Infrastructure** | Work queue DB with UPSERT coalescing, locking (path/doc/registry), structured logging, stability algorithm | work_queue.py, lock_manager.py, audit_logger.py, stability_checker.py, tests | Unit tests: queue coalescing, stability sampling, lock ordering | All infrastructure tests green |
    | **3. ID & Rename** | ID allocation (separate ID_REGISTRY.json), atomic rename, registry row creation with unified timestamps, self-induced suppression | id_allocator.py, file_renamer.py, suppression_manager.py, tests | Unit tests + integration test (allocate+rename), loop prevention test, timestamp validation | Files renamed with doc_id, no self-triggering, timestamps correct |
    | **4. Parser & Descriptor** | AST parsing, descriptor generation | descriptor_extractor.py, PYTHON_FILE_DESCRIPTOR.yml, tests | Unit tests, validate descriptor schema | Valid descriptors produced for sample files |
    | **5. Registry Update** | Promotion logic, Registry Writer Service (single mutation point), atomic patching with registry lock, write policy enforcement, normalization on write, automatic backup/rollback, CAS precondition, fail-fast validation (fast/strict modes) | registry_writer_service.py (consolidates write_policy_validator, normalizer, backup manager), patch schema (with registry_hash), tests | Unit tests, idempotency test, lock order test, write policy violation test, normalization test, backup/rollback test, CAS mismatch test, single-writer enforcement test, fast/strict mode test | Registry Writer Service is only mutation point, all policies enforced, backups automatic, rollback on failure |
    | **6. Watcher** | Event loop, stability gate, classification, move/delete handlers, orchestration, safety rails | watcher_daemon.py, WATCHER_CONFIG.yml (with dry-run, max_actions), event_handlers.py, tests | Integration test (watch dir, add/modify/move/delete), safety rails test | Full pipeline works end-to-end with all event types |
    | **7. Reconciliation** | Drift detection, repair, scheduled ticks, queue deduplication | reconciler.py, reconcile_scheduler.py, tests | Reconciliation test (introduce drift, verify repair without duplicates) | Scan detects and fixes issues without queue pollution |
    | **8. CLI & Runbook** | Commands with dry-run support, documentation, runbook | cli.py, README.md, RUNBOOK.md, REGISTRY_MIGRATION.md | Manual smoke test, runbook walkthrough, dry-run verification | Operator can start/stop/monitor system safely |
    | **9. Validation** | Full test suite, quality gates, production readiness checklist, registry integrity checks | Final test run, coverage report, readiness doc, registry consistency validator | All tests pass (including loop/move/delete/reconcile/write-policy/CAS), coverage >80% | System ready for production, SSOT integrity guaranteed |
  </phase_plan>

  <architecture>
    <high_level_design>
      Components:
      1. **Watcher Daemon** (watcher_daemon.py)
         - Uses watchdog to monitor filesystem
         - Stability-gates events (not just time debounce)
         - Enqueues work items via UPSERT (coalescing)
         - Orchestrates the pipeline for each file
         - Enforces safety rails (dry-run default, max actions per cycle)
      
      2. **Work Queue** (work_queue.py)
         - SQLite-backed persistent queue
         - UPSERT-by-path to coalesce duplicate events
         - Rich schema: work_item_id, event_type, path, old_path (for moves), first_seen, last_seen, attempts, status
         - States: queued → stable_pending → stable_ready → running → done/retry/dead_letter
         - Retry logic with exponential backoff
         - Dead-letter queue for non-retryable failures
      
      3. **Stability Checker** (stability_checker.py)
         - Min-age check (file must be N ms old)
         - Mtime/size sampled twice across stability window
         - Pushback to stable_pending if changed (no new work item)
      
      4. **Lock Manager** (lock_manager.py)
         - Acquires/releases path locks, doc_id locks, and registry lock
         - Prevents concurrent processing
         - Enforces lock ordering: path_lock → doc_lock → registry_lock (total order, never reverse)
         - Lock files: .dms/runtime/locks/{path|doc|registry}/
         - Timeout: 30 seconds default, stale locks (>5 min) forcibly released
      
      5. **Suppression Manager** (suppression_manager.py)
         - Tracks self-induced events (renames, writes) with timestamp
         - Suppresses follow-up events for N seconds
         - Prevents infinite loop from watcher triggering itself
      
      6. **Classifier** (classifier.py)
         - Determines if file is governed
         - Detects file kind (.py)
         - Checks for existing doc_id in filename
      
      7. **ID Allocator** (id_allocator.py)
         - Reads ID_REGISTRY.json
         - Allocates next 16-digit doc_id
         - Updates ID registry atomically
      
      8. **File Renamer** (file_renamer.py)
         - Atomically renames file to include doc_id
         - Handles collisions and retry
         - Registers rename with suppression manager
      
      9. **Event Handlers** (event_handlers.py)
         - **FILE_ADDED/MODIFIED**: triggers parse and descriptor generation
         - **FILE_MOVED**: updates registry path, detects doc_id renames (self-induced vs external)
         - **FILE_DELETED**: sets status=deleted tombstone, cleans up descriptor artifacts
         - **WRITE_POLICY_VIOLATION**: rejects patch, logs error
         - **NORMALIZATION_REQUIRED**: triggers automatic normalization
         - **DERIVATION_DRIFT**: triggers recomputation
         - **VALIDATION_FAILED**: triggers automatic rollback
      
      10. **Descriptor Extractor** (descriptor_extractor.py)
          - Wraps existing python_ast_parser.py
          - Merges AST output with declared metadata
          - Produces descriptor JSON + promotion payload
      
      11. **Normalizer** (normalizer.py)
          - Uppercase rel_type values
          - Normalize path separators to forward slash
          - Apply other schema-level normalization rules
          - Runs automatically on every write (integrated into Registry Writer Service)
      
      12. **Backup Manager** (backup_manager.py)
          - Creates timestamped backup before every registry mutation
          - Stores backups in .dms/backups/registry/
          - Provides rollback functionality
          - Cleanup old backups (retention policy)
      
      13. **Registry Writer Service** (registry_writer_service.py)
          - **Single component allowed to mutate UNIFIED_SSOT_REGISTRY.json**
          - Enforces promotion patch interface (no ad-hoc edits)
          - Integrates: write_policy_validator, normalizer, backup_manager
          - Pipeline: validate → normalize → backup → apply → verify
          - Automatic rollback on any failure
          - Supports fast validation (every write) and strict validation (CI/release)
          - Acquires registry lock during entire pipeline
          - Uses unified timestamp fields (first_seen_utc, updated_utc)
          - Logs all mutations with structured audit trail
      
      13. **Reconciler** (reconciler.py)
          - Scans project tree
          - Detects missing registry rows, stale hashes, moved files
          - Re-enqueues files for repair via work queue (deduplicates)
          - Validates registry integrity (CAS preconditions, write policy)
          - Uses Registry Writer Service for all updates (no direct edits)
      
      14. **Reconcile Scheduler** (reconcile_scheduler.py)
          - Triggers RECONCILE_TICK at configured intervals
          - Coordinates with work queue to avoid duplicate processing
      
      15. **CLI** (cli.py)
          - start-watcher (--live flag required for writes, default dry-run)
          - stop-watcher, reconcile, describe-file
          - migrate-registry (converts old FILE_REGISTRY.json to UNIFIED_SSOT_REGISTRY.json)
          - validate-registry (runs fast or strict validation on demand)
      
      16. **Audit Logger** (audit_logger.py)
          - Appends to actions.jsonl and errors.jsonl
          - Structured fields: work_item_id, event_id, stage_id, doc_id, path, result, error_code, duration_ms
    </high_level_design>
    
    <project_structure>
      eafix-modular/
      ├── .dms/
      │   ├── artifacts/
      │   │   ├── python_descriptor/     # {doc_id}.v1.json
      │   │   └── index/                 # derived indexes
      │   ├── patches/
      │   │   └── registry/              # registry patch logs
      │   ├── runtime/
      │   │   ├── work_queue.sqlite
      │   │   └── locks/
      │   │       ├── path/
      │   │       └── doc/
      │   ├── logs/
      │   │   ├── actions.jsonl
      │   │   └── errors.jsonl
      │   └── quarantine/
      │
      ├── repo_autoops/
      │   └── automation_descriptor/
      │       ├── __init__.py
      │       ├── watcher_daemon.py
      │       ├── work_queue.py
      │       ├── stability_checker.py
      │       ├── lock_manager.py
      │       ├── suppression_manager.py
      │       ├── classifier.py
      │       ├── id_allocator.py
      │       ├── file_renamer.py
      │       ├── event_handlers.py
      │       ├── descriptor_extractor.py
      │       ├── normalizer.py
      │       ├── backup_manager.py
      │       ├── write_policy_validator.py
      │       ├── registry_writer_service.py
      │       ├── reconciler.py
      │       ├── reconcile_scheduler.py
      │       ├── audit_logger.py
      │       └── cli.py
      │
      ├── .dms/
      │   ├── backups/
      │   │   └── registry/              # timestamped registry backups
      │
      ├── registry/
      │   ├── UNIFIED_SSOT_REGISTRY.json    # canonical
      │   ├── FILE_REGISTRY.json            # deprecated alias
      │   └── FILE_REGISTRY_v2.json         # deprecated alias
      │
      ├── config/
      │   ├── WATCHER_CONFIG.yml
      │   └── PYTHON_FILE_DESCRIPTOR.yml
      │
      ├── tests/
      │   └── automation_descriptor/
      │       ├── test_work_queue.py
      │       ├── test_stability_checker.py
      │       ├── test_lock_manager.py
      │       ├── test_suppression_manager.py
      │       ├── test_id_allocator.py
      │       ├── test_event_handlers.py
      │       ├── test_descriptor_extractor.py
      │       ├── test_normalizer.py
      │       ├── test_backup_manager.py
      │       ├── test_write_policy_validator.py
      │       ├── test_registry_writer_service.py
      │       ├── test_cas_precondition.py
      │       ├── test_reconciler.py
      │       ├── test_loop_prevention.py
      │       └── test_integration.py
      │
      └── docs/
          ├── automation_descriptor/
          │   ├── README.md
          │   ├── RUNBOOK.md
          │   └── REGISTRY_MIGRATION.md
          ├── 2026012015460001_COLUMN_DICTIONARY.md  (updated)
          └── REGISTRY_WRITE_POLICY.md
    </project_structure>
    
    <key_decisions>
      1. **UNIFIED_SSOT_REGISTRY.json as canonical**: Single source of truth, FILE_REGISTRY.json deprecated
      2. **ID_REGISTRY.json separate**: Counter state only, not mixed with entity registry
      3. **Registry Writer Service as single mutation point**: Only component allowed to write registry, enforces all policies
      4. **Promotion patch interface**: All updates go through patches, no ad-hoc edits
      5. **Normalization on write**: Automatic (uppercase rel_type, path separators), not separate cleanup step
      6. **Automatic backup before mutation**: Every registry write creates timestamped backup
      7. **Automatic rollback on validation failure**: Pipeline fails fast, restores backup
      8. **Fast and strict validation modes**: Fast on every write, strict for CI/release
      9. **Unified timestamp fields**: first_seen_utc, updated_utc (allocated_at removed)
      10. **Write policy enforcement mandatory**: tool_only, immutable, derived rules validated before write
      11. **CAS precondition required**: registry_hash in every patch, prevents lost updates
      12. **Event-driven architecture**: FILE_*, WRITE_POLICY_VIOLATION, NORMALIZATION_REQUIRED, DERIVATION_DRIFT, VALIDATION_FAILED
      13. **File entities only (Phase 1)**: Edge/generator records deferred to Phase 2
      14. **Generator staleness deferred**: Tracking and rebuild triggers in Phase 2
      15. **SQLite for work queue with UPSERT-by-path**: Coalesces events, retry/dead-letter handling
      16. **Stability algorithm beyond time debounce**: Min-age + mtime/size sampling handles atomic writes
      17. **Self-induced event suppression**: Timestamp-based suppression prevents infinite loops
      18. **Watchdog library**: Industry-standard, cross-platform filesystem watcher
      19. **File-based locks with total ordering**: path_lock → doc_lock → registry_lock (prevents deadlocks)
      20. **Registry lock file**: Explicit .dms/runtime/locks/registry.lock for atomic patching
      31. **Queue dedupe invariant**: UNIQUE(path) only, NOT UNIQUE(path, status) - prevents duplicate rows on status change
      32. **Canonical path field**: relative_path (POSIX forward-slash, repo-relative) - NOT current_path or abs_path
      33. **Event enum normalization**: Legacy FILE_CREATED mapped to FILE_ADDED on intake
      21. **Temp-file-then-replace for registry**: Atomic updates, prevents corruption
      22. **Separate descriptor artifacts from registry**: Keeps registry lean, allows versioned schemas
      23. **20 promoted columns**: Balance between registry queryability and size
      24. **Hash-based change detection**: Avoids redundant parsing
      25. **Exponential backoff retry**: Standard pattern for transient errors
      26. **Quarantine for non-retryable errors**: Prevents infinite loops
      27. **Dry-run default with --live flag**: Safety rail, requires explicit opt-in for writes
      28. **Max actions per cycle cap**: Prevents runaway processing
      29. **Structured JSONL logs**: Append-only, parseable, stage-correlated for observability
      30. **Reconcile via work queue**: Deduplicates with normal watcher flow
    </key_decisions>
    
    <tradeoffs>
      - Single daemon vs distributed: Simpler, no coordination overhead, sufficient for single-developer use
      - SQLite vs in-memory queue: Persistence across restarts, slight performance cost acceptable
      - File locks vs distributed locks: Simple, no dependencies, limited to single machine
      - Promoted columns vs all-in-descriptor: Registry stays lean, queries remain fast
      - Synchronous processing vs async: Simpler reasoning, easier debugging, performance acceptable for local use
    </tradeoffs>
  </architecture>

  <implementation>
    See attached files in next sections
  </implementation>

  <validation_gates>
    1. **Linting**: `python -m pylint repo_autoops/automation_descriptor/` → no errors
    2. **Type checking**: `python -m mypy repo_autoops/automation_descriptor/` → no errors
    3. **Unit tests**: `python -m pytest tests/automation_descriptor/ -v` → all pass
    4. **Registry filename test**: Verify all tools write to UNIFIED_SSOT_REGISTRY.json only
    5. **Single-writer enforcement test**: Verify only Registry Writer Service can mutate registry
    6. **Promotion patch interface test**: Verify all updates go through patch interface
    7. **Schema migration test**: Verify allocated_at → first_seen_utc/updated_utc conversion
    8. **Write policy enforcement test**: Verify tool_only/immutable/derived violations rejected
    9. **Normalization test**: Verify automatic normalization on write (rel_type uppercase, path separators)
    10. **Backup test**: Verify automatic backup created before every mutation
    11. **Rollback test**: Verify automatic rollback on validation failure
    12. **CAS precondition test**: Verify stale registry_hash rejected (lost update prevented)
    13. **Fast validation test**: Verify fast mode runs on every write
    14. **Strict validation test**: Verify strict mode runs on demand (comprehensive checks)
    15. **Event handler test**: Verify FILE_ADDED/MODIFIED/MOVED/DELETED, WRITE_POLICY_VIOLATION, NORMALIZATION_REQUIRED, DERIVATION_DRIFT, VALIDATION_FAILED
    16. **Queue coalescing test**: Verify UPSERT-by-path merges duplicate events
    17. **Retry/dead-letter test**: Verify retry logic and dead-letter queue handling
    18. **Stability algorithm test**: Verify pushback to stable_pending on mtime/size change
    19. **Lock ordering test**: Verify path_lock → doc_lock → registry_lock order, detect deadlock attempts
    20. **Loop prevention test**: Verify watcher doesn't retrigger on own renames/writes
    21. **Move event test**: Move file, verify registry path update and doc_id rename detection
    22. **Delete event test**: Delete file, verify tombstone and artifact cleanup
    23. **Integration test**: `python -m pytest tests/automation_descriptor/test_integration.py -v` → all pass
    24. **Schema validation**: Descriptor JSON validates against PYTHON_FILE_DESCRIPTOR.yml
    25. **Idempotency test**: Re-parse same file, verify no registry change
    26. **Reconciliation test**: Introduce drift, run reconcile, verify repair without duplicate queue entries
    27. **Error handling test**: Add file with syntax error, verify quarantine
    28. **Safety rails test**: Verify dry-run mode, verify max actions cap
    29. **Registry integrity test**: Run consistency checker, verify no policy violations
    30. **Manual smoke test**: Start watcher with --live, add/modify/move/delete 5 Python files, verify UNIFIED_SSOT_REGISTRY.json + descriptors + backups
    31. **Queue dedupe invariant test**: Verify UNIQUE(path) constraint, status changes update in-place (no duplicate rows)
    32. **Path field normalization test**: Verify all paths use relative_path (POSIX forward-slash, repo-relative)
    33. **Event enum mapping test**: Verify FILE_CREATED from legacy sources is mapped to FILE_ADDED
    34. **Registry canonical path test**: Verify all writes target UNIFIED_SSOT_REGISTRY.json, deprecated aliases rejected
    35. **Timestamp migration test**: Verify allocated_at → first_seen_utc conversion, old field constraints not enforced
    36. **Frozen contracts compliance test**: Verify implementation matches all contracts in frozen_contracts section
  </validation_gates>

  <runbook>
    See RUNBOOK.md in final delivery
  </runbook>

  <final_summary>
    Complete Automation Descriptor Subsystem delivered with:
    - Production-ready watcher daemon
    - Full test coverage (>80%)
    - Integration with UNIFIED_SSOT_REGISTRY.json (hardened, canonical-only writes)
    - Registry Writer Service (single mutation point, enforces all policies)
    - Promotion patch interface (no ad-hoc edits)
    - Write policy enforcement (tool_only, immutable, derived rules)
    - Normalization on write (automatic, not separate step)
    - Automatic backup before every mutation
    - Automatic rollback on validation failure
    - Fast and strict validation modes
    - CAS protection (registry_hash precondition prevents lost updates)
    - Atomic operations and proper error handling
    - Unified timestamp schema (first_seen_utc, updated_utc; allocated_at removed)
    - Event-driven architecture (FILE_ADDED/MODIFIED/MOVED/DELETED + policy events)
    - Retry logic with dead-letter queue
    - Reconciliation for drift repair
    - CLI commands for operation (including migrate-registry, validate-registry)
    - Comprehensive runbook and migration guide

    Frozen Contracts Enforced (see frozen_contracts section):
    - Registry: UNIFIED_SSOT_REGISTRY.json canonical, deprecated aliases read-only
    - Patch: registry_hash (CAS) required, defined schema
    - Timestamps: first_seen_utc, updated_utc only; allocated_at migrated/removed
    - Queue: UNIQUE(path) dedupe invariant, in-place status updates
    - Locks: path_lock → doc_lock → registry_lock total ordering
    - Events: Canonical enum (FILE_ADDED not FILE_CREATED), legacy mapped on intake
    - Paths: relative_path canonical, POSIX format, repo-relative

    Document Authority Established:
    - Deliverables Specification = SSOT for requirements
    - Phase Plan (this file) = Build order + frozen contracts
    - ChatGPT export = Deprecated legacy reference (conflicts resolved)

    Known limitations:
    - Single daemon instance only (no distributed coordination)
    - Windows-focused (tested on Windows, should work on Unix but not validated)
    - File entities only (edges/generators deferred to Phase 2)
    - Python files only (other file types require separate plugins)
    - JSON registry backend only (SQLite registry deferred to Phase 2; SQLite queue is in scope)
    
    Phase 2 scope (explicitly deferred):
    - Edge records (entity relationships)
    - Generator records (derived artifact definitions)
    - Generator staleness tracking and rebuild triggers
    - Automatic module/process validator enforcement
    - SQLite backend migration
    
    Next hardening steps (Phase 2+):
    - Add telemetry/metrics (Prometheus/OpenTelemetry)
    - Implement graceful shutdown with signal handling
    - Add configuration hot-reload
    - Build web UI for monitoring
    - Add performance benchmarking
    - Implement automatic module/process validation
    - Implement generator staleness detection and rebuild automation
  </final_summary>
</prompt_template>
