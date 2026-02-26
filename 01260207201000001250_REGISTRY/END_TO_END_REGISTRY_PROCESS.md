# End-to-End Registry Process: Adding a File & Populating Column Data

**Document Version:** 1.1.0
**Date:** 2026-02-26
**Scope:** Complete lifecycle of a file entering the Governance Registry and having its column data populated.

---

## Process Diagram

```
 ========================================================================
  TRIGGER: New file observed (filesystem scan, watcher daemon, or CLI)
 ========================================================================
       |
       v
 +---------------------------------------------------------------------------+
 | PHASE 0: CONTRACT LOADING (Steps S00-S02)                                 |
 |                                                                           |
 |  S00 Load Contracts                                                       |
 |  +-----------------------------------------------------------------+      |
 |  | INPUT FILES:                                                    |      |
 |  |   Column Dictionary ......... COLUMN_DICTIONARY.json       [1]  |      |
 |  |   Write Policy .............. UNIFIED_SSOT_REGISTRY_            |      |
 |  |                               WRITE_POLICY.yaml            [2]  |      |
 |  |   Derivations ............... UNIFIED_SSOT_REGISTRY_            |      |
 |  |                               DERIVATIONS.yaml             [3]  |      |
 |  |   Registry Schema ........... governance_registry_              |      |
 |  |                               schema.v3.json               [4]  |      |
 |  +-----------------------------------------------------------------+      |
 |       |                                                                   |
 |       v                                                                   |
 |  S01 Build File Context                                                   |
 |  +-----------------------------------------------------------------+      |
 |  | INPUT FILES:                                                    |      |
 |  |   Observed file ............ (absolute path on filesystem)      |      |
 |  |   Repo roots config ........ (configured repo root mappings)    |      |
 |  |   Event metadata ........... (optional: watcher/CLI event)      |      |
 |  |                                                                 |      |
 |  | COMPUTES:                                                       |      |
 |  |   repo_root_id, relative_path, filename, is_directory,          |      |
 |  |   size_bytes, mtime_utc, file_ext                               |      |
 |  +-----------------------------------------------------------------+      |
 |       |                                                                   |
 |       v                                                                   |
 |  S02 Select Applicable Headers                                            |
 |  +-----------------------------------------------------------------+      |
 |  | USES FILES:                                                     |      |
 |  |   Column Dictionary ......... COLUMN_DICTIONARY.json       [1]  |      |
 |  |   Derivations ............... DERIVATIONS.yaml             [3]  |      |
 |  |                                                                 |      |
 |  | ACTIONS:                                                        |      |
 |  |   Evaluate required_when predicates per header                  |      |
 |  |   Filter active headers where predicate = true                  |      |
 |  |   Build depends_on graph -> topological sort                    |      |
 |  |   Tie-break by header name for stable ordering                  |      |
 |  |                                                                 |      |
 |  | OUTPUT:                                                         |      |
 |  |   H01_applicable_headers (filtered list)                        |      |
 |  |   H02_header_order (topologically sorted)                       |      |
 |  +-----------------------------------------------------------------+      |
 +---------------------------------------------------------------------------+
       |
       v
 +---------------------------------------------------------------------------+
 | PHASE 1: IDENTITY RESOLUTION (Steps S10-S12)                              |
 |                                                                           |
 |  S10 Detect Prefix                                                        |
 |  +-----------------------------------------------------------------+      |
 |  | INPUT:                                                          |      |
 |  |   filename from S01 context                                     |      |
 |  |                                                                 |      |
 |  | ACTION:                                                         |      |
 |  |   Parse filename for leading 20-digit token                     |      |
 |  |   Regex: ^(\d{20})_                                             |      |
 |  |   Example: 01999000042260125189_my_file.py                      |      |
 |  |            ^^^^^^^^^^^^^^^^^^^^                                 |      |
 |  |            extracted_prefix                                     |      |
 |  |                                                                 |      |
 |  | OUTPUT:                                                         |      |
 |  |   has_id_prefix = true/false                                    |      |
 |  |   extracted_prefix = "01999000042260125189" (if found)          |      |
 |  +-----------------------------------------------------------------+      |
 |       |                                                                   |
 |       v                                                                   |
 |  S11 Validate Prefix                                                      |
 |  +-----------------------------------------------------------------+      |
 |  | INPUT FILES:                                                    |      |
 |  |   Registry (snapshot) ....... REGISTRY_file.json           [5]  |      |
 |  |   Schema .................... schema.v3.json               [4]  |      |
 |  |                                                                 |      |
 |  | ACTIONS:                                                        |      |
 |  |   IF has_id_prefix == false:                                    |      |
 |  |     -> id_resolution_mode = "allocate", skip to S12             |      |
 |  |   Validate prefix matches ^[0-9]{20}$ pattern (from schema)    |      |
 |  |   Check registry for duplicate file_id conflict                 |      |
 |  |   IF valid + no conflict:                                       |      |
 |  |     -> file_id = extracted_prefix                               |      |
 |  |     -> id_resolution_mode = "use_prefix"                        |      |
 |  |                                                                 |      |
 |  | FAILURE MODES:                                                  |      |
 |  |   F_PREFIX_INVALID_FORMAT -> quarantine file                    |      |
 |  |   F_FILE_ID_COLLISION    -> abort (fatal)                       |      |
 |  +-----------------------------------------------------------------+      |
 |       |                                                                   |
 |       v                                                                   |
 |  S12 Allocate File ID (only if mode = "allocate")                         |
 |  +-----------------------------------------------------------------+      |
 |  | INPUT FILES:                                                    |      |
 |  |   Counter Store ............. COUNTER_STORE.json           [6]  |      |
 |  |   Lock file ................. COUNTER_STORE.json.lock      [7]  |      |
 |  |   Registry (snapshot) ....... REGISTRY_file.json           [5]  |      |
 |  |                                                                 |      |
 |  | AUTOMATION:                                                     |      |
 |  |   ID Allocator .............. P_...24031_unified_          |      |
 |  |                               id_allocator.py         [A1] |      |
 |  |                                                                 |      |
 |  | ACTIONS:                                                        |      |
 |  |   IF mode == "use_prefix": pass through, no allocation          |      |
 |  |   ELSE:                                                         |      |
 |  |     Acquire exclusive lock on COUNTER_STORE                     |      |
 |  |     Allocate via allocate_single_id()                           |      |
 |  |     current_counter++ (e.g., 1999000042260125189 -> ...190)     |      |
 |  |     Release lock                                                |      |
 |  |   FALLBACK (if allocator unavailable):                          |      |
 |  |     file_id = max_id_in_registry + 1 (must be enabled + logged) |      |
 |  +-----------------------------------------------------------------+      |
 +---------------------------------------------------------------------------+
       |
       v
 +---------------------------------------------------------------------------+
 | PHASE 2: COLUMN POPULATION (Steps S20-S22)                                |
 |                                                                           |
 |  S20 Populate Identity Fields                                             |
 |  +-----------------------------------------------------------------+      |
 |  | GOVERNED BY:                                                    |      |
 |  |   Column Dictionary ......... COLUMN_DICTIONARY.json       [1]  |      |
 |  |   Write Policy .............. WRITE_POLICY.yaml            [2]  |      |
 |  |   Derivations ............... DERIVATIONS.yaml             [3]  |      |
 |  |                                                                 |      |
 |  | FIELDS SET:                                                     |      |
 |  |   file_id ........... resolved ID from Phase 1                  |      |
 |  |   repo_root_id ...... from S01 context                          |      |
 |  |   relative_path ..... computed: relpath(abs_path, repo_root)    |      |
 |  |   filename .......... computed: basename(abs_path)              |      |
 |  |   doc_id ............ formula: DOC-{last4(file_id)}             |      |
 |  |   record_kind ....... literal: "entity"                         |      |
 |  |                                                                 |      |
 |  | DERIVATION ORDER:                                               |      |
 |  |   Follows H02_header_order (topological sort from S02)          |      |
 |  +-----------------------------------------------------------------+      |
 |       |                                                                   |
 |       v                                                                   |
 |  S21 Populate Scan / Infer / Compute Fields                               |
 |  +-----------------------------------------------------------------+      |
 |  | GOVERNED BY:                                                    |      |
 |  |   Column Dictionary ......... COLUMN_DICTIONARY.json       [1]  |      |
 |  |   Write Policy .............. WRITE_POLICY.yaml            [2]  |      |
 |  |   Derivations ............... DERIVATIONS.yaml             [3]  |      |
 |  |                                                                 |      |
 |  | AUTOMATION:                                                     |      |
 |  |   Scanner ................... P_...24023_scanner.py        [A2] |      |
 |  |                                                                 |      |
 |  | DERIVE MODE "scan" (filesystem):                                |      |
 |  |   sha256 ............. SHA256_BYTES(file_content)                |      |
 |  |   size_bytes ......... FILE_SIZE(abs_path)                      |      |
 |  |   mtime_utc .......... FILE_MTIME(abs_path)                     |      |
 |  |   is_directory ....... IS_DIRECTORY(abs_path)                    |      |
 |  |   extension .......... EXTENSION(filename)                      |      |
 |  |   first_seen_utc ..... NOW_UTC() (immutable after creation)     |      |
 |  |   created_utc ........ NOW_UTC() (immutable after creation)     |      |
 |  |                                                                 |      |
 |  | DERIVE MODE "infer" (deterministic rules):                      |      |
 |  |   artifact_kind ...... INFER_ARTIFACT_KIND(ext, name, path)     |      |
 |  |     Mapping: .py -> PYTHON_MODULE, .json+schema -> SCHEMA,      |      |
 |  |     test_* -> TEST, .md -> MARKDOWN_DOC, etc.                   |      |
 |  |   governance_domain .. INFER_GOVERNANCE_DOMAIN(path)            |      |
 |  |     Mapping: schema/ -> SCHEMAS, registry/ -> REGISTRY,         |      |
 |  |     test/ -> TESTS, evidence/ -> EVIDENCE, etc.                 |      |
 |  |   layer .............. INFER_LAYER(path, artifact_kind)         |      |
 |  |     Mapping: SCHEMA -> DEFINITION, TEST -> TESTING,             |      |
 |  |     validate* -> VALIDATION, .md -> DOCUMENTATION, etc.         |      |
 |  |   canonicality ....... default "CANONICAL"                      |      |
 |  |   has_tests .......... default false                            |      |
 |  |                                                                 |      |
 |  | DERIVE MODE "compute" (safe DSL formulas):                      |      |
 |  |   dir_id ............. WALK_UP_FIND_DIR_ID(path)                |      |
 |  |   depth .............. computed from relative_path              |      |
 |  |   zone ............... computed from path (governed/staging)     |      |
 |  |   parent_dir_id ...... WALK_UP_FIND_DIR_ID(parent_path)         |      |
 |  |   owning_dir_id ...... resolved from directory hierarchy        |      |
 |  |                                                                 |      |
 |  | DERIVE MODE "user_input":                                       |      |
 |  |   one_line_purpose ... left null unless user supplies           |      |
 |  |   description ........ left null unless user supplies           |      |
 |  |   notes .............. left null unless user supplies           |      |
 |  |   bundle_key ......... manual assignment                        |      |
 |  |   geu_role ........... manual assignment                        |      |
 |  |                                                                 |      |
 |  | NULL POLICY ENFORCEMENT (from WRITE_POLICY.yaml):               |      |
 |  |   forbid_null -> field MUST have a value or abort               |      |
 |  |   allow_null  -> field can be null                              |      |
 |  |   conditional -> depends on other field values                  |      |
 |  +-----------------------------------------------------------------+      |
 |       |                                                                   |
 |       v                                                                   |
 |  S22 Populate Python Analysis Fields (PYTHON_MODULE only)                 |
 |  +-----------------------------------------------------------------+      |
 |  | CONDITION: artifact_kind == "PYTHON_MODULE" AND                  |      |
 |  |            mapp_py analysis bundle is available                  |      |
 |  |                                                                 |      |
 |  | INPUT FILES:                                                    |      |
 |  |   Capability mapping ....... capability_mapping_system/    [8]  |      |
 |  |   mapp_py analysis bundle .. (per-file evidence JSON)           |      |
 |  |                                                                 |      |
 |  | FIELDS SET:                                                     |      |
 |  |   py_capability_tags .... [list of detected capabilities]       |      |
 |  |   py_capability_facts_hash . SHA256 of extracted facts          |      |
 |  |   py_analysis_run_id .... trace ID of analysis run              |      |
 |  |   py_canonical_text_hash  . normalized content hash             |      |
 |  |   py_overlap_group_id ... deduplication group                   |      |
 |  |   py_analysis_success ... true/false                            |      |
 |  |                                                                 |      |
 |  | IF SKIPPED (not a .py file or no analysis bundle):              |      |
 |  |   All py_* fields remain null/empty                             |      |
 |  +-----------------------------------------------------------------+      |
 +---------------------------------------------------------------------------+
       |
       v
 +---------------------------------------------------------------------------+
 | PHASE 3: ATOMIC WRITE (Steps S30-S32)                                     |
 |                                                                           |
 |  S30 Build Promotion Patch                                                |
 |  +-----------------------------------------------------------------+      |
 |  | INPUT FILES:                                                    |      |
 |  |   Registry (snapshot) ....... REGISTRY_file.json           [5]  |      |
 |  |                                                                 |      |
 |  | ACTIONS:                                                        |      |
 |  |   Determine: add_new vs update_existing                         |      |
 |  |     (based on whether file_id exists in registry)               |      |
 |  |   Construct RFC-6902 JSON Patch operations                      |      |
 |  |   Include metadata: trace_id, tool_version,                     |      |
 |  |     catalog_version, derivation_set_hash                        |      |
 |  |   Validate patch is minimal (no redundant writes)               |      |
 |  |                                                                 |      |
 |  | OUTPUT:                                                         |      |
 |  |   O01_promotion_patch (RFC-6902 compatible)                     |      |
 |  +-----------------------------------------------------------------+      |
 |       |                                                                   |
 |       v                                                                   |
 |  S31 Single-Writer Atomic Commit                                          |
 |  +-----------------------------------------------------------------+      |
 |  | INPUT/OUTPUT FILES:                                              |      |
 |  |   Registry .................. REGISTRY_file.json           [5]  |      |
 |  |   Write Policy .............. WRITE_POLICY.yaml            [2]  |      |
 |  |   Schema .................... schema.v3.json               [4]  |      |
 |  |   Backup .................... archive/ (auto-created)      [9]  |      |
 |  |                                                                 |      |
 |  | SEQUENCE (all-or-nothing):                                      |      |
 |  |   1. Acquire registry write lock (single-writer)                |      |
 |  |   2. Backup current REGISTRY_file.json -> archive/              |      |
 |  |   3. Load current registry from disk                            |      |
 |  |   4. Enforce write policy per column:                           |      |
 |  |      - Check writable_by (tool_only / user_only / both)         |      |
 |  |      - Check update_policy (immutable fields can't change)      |      |
 |  |      - Reject illegal field writes -> abort                     |      |
 |  |   5. Apply RFC-6902 patch                                       |      |
 |  |   6. Normalize canonical formatting (pinned normalizer)         |      |
 |  |   7. Recompute tool-owned derived fields                        |      |
 |  |   8. Validate against schema.v3.json (types, required fields)   |      |
 |  |   9. Validate referential integrity (edges, dependencies)       |      |
 |  |  10. Write to temp file -> atomic replace -> fsync              |      |
 |  |  11. Release lock                                               |      |
 |  |                                                                 |      |
 |  | ROLLBACK TRIGGERS:                                              |      |
 |  |   F_SCHEMA_VALIDATION_FAIL -> restore backup                    |      |
 |  |   F_ATOMIC_WRITE_FAIL     -> restore backup                    |      |
 |  |   F_WRITE_POLICY_VIOLATION -> abort (no write attempted)        |      |
 |  +-----------------------------------------------------------------+      |
 |       |                                                                   |
 |       v                                                                   |
 |  S32 Post-Write Generators                                                |
 |  +-----------------------------------------------------------------+      |
 |  | INPUT FILES:                                                    |      |
 |  |   Registry (updated) ....... REGISTRY_file.json           [5]  |      |
 |  |                                                                 |      |
 |  | OUTPUT FILES:                                                   |      |
 |  |   GEU Sets .................. geu_sets.regenerated.json    [10] |      |
 |  |   Evidence bundle ........... .state/evidence/             [11] |      |
 |  |                                                                 |      |
 |  | ACTIONS:                                                        |      |
 |  |   Compute source registry hash                                  |      |
 |  |   Detect stale derived artifacts                                |      |
 |  |   Rebuild geu_sets.regenerated.json deterministically            |      |
 |  |     - Groups files into Governance Enforcement Units            |      |
 |  |     - Assigns GEU roles (SCHEMA, RULE, VALIDATOR, etc.)         |      |
 |  |   Record build metadata:                                        |      |
 |  |     last_build_utc, source_registry_hash,                       |      |
 |  |     output_hash, build_status                                   |      |
 |  +-----------------------------------------------------------------+      |
 +---------------------------------------------------------------------------+
       |
       v
 +---------------------------------------------------------------------------+
 | PHASE 4: POST-INGESTION (Ongoing Maintenance)                             |
 |                                                                           |
 |  Reconciliation (periodic or on-demand)                                   |
 |  +-----------------------------------------------------------------+      |
 |  | AUTOMATION:                                                     |      |
 |  |   Reconciler .......... P_...25106_registry_filesystem_         |      |
 |  |                         reconciler.py                      [A3] |      |
 |  |                                                                 |      |
 |  | 6 BIDIRECTIONAL CHECKS:                                         |      |
 |  |   1. Registry -> Filesystem (orphan detection)                  |      |
 |  |   2. Filesystem -> Registry (unregistered files)                |      |
 |  |   3. ID mismatches (dir_id / file_id)                           |      |
 |  |   4. Duplicate file_ids                                         |      |
 |  |   5. Duplicate paths                                            |      |
 |  |   6. Missing dir_ids                                            |      |
 |  |                                                                 |      |
 |  | AUTO-FIX: orphans, dir_id mismatches                            |      |
 |  +-----------------------------------------------------------------+      |
 |                                                                           |
 |  Dir ID Population (backfill)                                             |
 |  +-----------------------------------------------------------------+      |
 |  | AUTOMATION:                                                     |      |
 |  |   Dir ID populator .... P_...25102_populate_registry_           |      |
 |  |                         dir_ids.py                         [A4] |      |
 |  |   Dir ID generator .... P_...25100_generate_dir_ids_            |      |
 |  |                         gov_reg.py                         [A5] |      |
 |  |   Dir ID validator .... P_...25101_validate_dir_ids.py     [A6] |      |
 |  +-----------------------------------------------------------------+      |
 +---------------------------------------------------------------------------+
       |
       v
 ========================================================================
  DONE: File is registered with all derivable column data populated.
  User-input fields (one_line_purpose, description, bundle assignments)
  remain null until manually patched.
 ========================================================================
```

---

## File Reference Index

### Contract / Governance Files (read at every ingestion)

| Ref | File | Full Path (relative to REGISTRY/) | Role |
|-----|------|-----------------------------------|------|
| [1] | Column Dictionary | `COLUMN_HEADERS/01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json` | 185 header definitions with derivation specs, scopes, normalization rules |
| [2] | Write Policy | `COLUMN_HEADERS/01260207201000000193_UNIFIED_SSOT_REGISTRY_WRITE_POLICY.yaml` | Per-column: null_policy, update_policy, writable_by, merge_strategy |
| [3] | Derivations | `COLUMN_HEADERS/01260207201000000192_UNIFIED_SSOT_REGISTRY_DERIVATIONS.yaml` | Safe DSL formulas (60+ functions), dependency graphs, triggers |
| [4] | Schema | `01999000042260124012_governance_registry_schema.v3.json` | JSON Schema (draft-07): types, required fields, enums, patterns |

### Data Files (read and/or written during ingestion)

| Ref | File | Full Path (relative to repo root) | Role |
|-----|------|-----------------------------------|------|
| [5] | Registry | `REGISTRY/01999000042260124503_REGISTRY_file.json` | SSOT - the single registry file (2,013 files + 245 entries + 723 entities) |
| [6] | Counter Store | `01260207201000000116_COUNTER_STORE.json` | Persisted ID counter (current: 1999000042260125192) |
| [7] | Counter Lock | `COUNTER_STORE.json.lock` | Exclusive lock file for ID allocation |

### Generated / Derived Files (written after successful commit)

| Ref | File | Full Path (relative to REGISTRY/) | Role |
|-----|------|-----------------------------------|------|
| [8] | Capability Mapping | `01260207201000001313_capability_mapping_system/` | Python analysis toolchain (mapp_py) |
| [9] | Archive | `archive/` | Registry backups before each write |
| [10] | GEU Sets | `01260207233100000466_geu_sets.regenerated.json` | Derived: files grouped into Governance Enforcement Units |
| [11] | Evidence | `.state/evidence/` | Audit trail: input snapshots, contract pins, derivation traces |

### Automation Scripts

| Ref | Script | Full Path (relative to REGISTRY/ID/7_automation/) | Role |
|-----|--------|---------------------------------------------------|------|
| [A1] | ID Allocator | `ID/1_runtime/allocators/P_01999000042260124031_unified_id_allocator.py` | Lock-protected ID allocation from COUNTER_STORE |
| [A2] | Scanner | `P_01999000042260124023_scanner.py` | Filesystem scan, artifact detection, metadata inference |
| [A3] | Reconciler | `P_01999000042260125106_registry_filesystem_reconciler.py` | 6-check bidirectional sync between registry and disk |
| [A4] | Dir ID Populator | `P_01999000042260125102_populate_registry_dir_ids.py` | Backfill dir_id fields via RFC-6902 patches |
| [A5] | Dir ID Generator | `P_01999000042260125100_generate_dir_ids_gov_reg.py` | Generate .dir_id files for all directories |
| [A6] | Dir ID Validator | `P_01999000042260125101_validate_dir_ids.py` | Validate dir_id consistency across filesystem |

### Entry Points (how the process is triggered)

| Trigger | Script | Command |
|---------|--------|---------|
| CLI Scan | `P_01999000042260124015_govreg.py` | `python govreg.py scan --write` |
| CLI Validate | `P_01999000042260124015_govreg.py` | `python govreg.py validate` |
| File Watcher | `P_01260207233100000008_watcher_daemon.py` | Daemon: auto-detects filesystem changes |
| Scanner Service | `P_01260207233100000071_scanner_service.py` | Background service: continuous scan |
| Manual File Create | `P_01999000042260124028_file_creator.py` | Creates file with ID prefix pre-assigned |

---

## Column Population Summary by Derive Mode

| Derive Mode | When | Fields (examples) | Source |
|-------------|------|--------------------|--------|
| **literal** | S20 | `file_id`, `repo_root_id`, `record_kind` | Directly set from resolved values |
| **scan** | S21 | `sha256`, `size_bytes`, `mtime_utc`, `is_directory`, `extension`, `created_utc` | Filesystem I/O |
| **infer** | S21 | `artifact_kind`, `governance_domain`, `layer`, `canonicality`, `has_tests` | Deterministic rules in scanner + derivations DSL |
| **compute** | S21 | `dir_id`, `depth`, `zone`, `parent_dir_id`, `owning_dir_id`, `doc_id` | Safe DSL formulas evaluated with dependency ordering |
| **user_input** | S21 | `one_line_purpose`, `description`, `notes`, `bundle_key`, `geu_role` | Left null; populated by manual patch later |
| **py_analysis** | S22 | `py_capability_tags`, `py_capability_facts_hash`, `py_analysis_run_id` | mapp_py analysis bundle (Python files only) |

---

## Write Policy Enforcement (per column at S31)

| Policy | Meaning | Example Columns |
|--------|---------|-----------------|
| `immutable` | Cannot change after first write | `file_id`, `dir_id`, `created_utc` |
| `recompute_on_scan` | Recomputed every scan | `sha256`, `size_bytes`, `mtime_utc`, `depth`, `zone` |
| `recompute_on_build` | Recomputed on post-write rebuild | Derived/computed fields |
| `manual_patch_only` | Only changed by explicit user action | `validation_rules`, `notes` |
| `manual_or_automated` | Changed by user or approved automation | `bundle_key`, `geu_role` |
| `normalize_on_ingest` | Standardized format on entry | Path fields (slash normalization) |

| Writable By | Who Can Write |
|-------------|---------------|
| `tool_only` | Automation scripts only |
| `user_only` | Human operator only |
| `both` | Either tool or human |
| `never` | Read-only / deprecated |

---

## Failure Modes and Recovery

| Code | Phase | Severity | Action | Description |
|------|-------|----------|--------|-------------|
| `F_CONTRACT_MISSING` | S00 | Fatal | Abort | Required contract file not found |
| `F_REPO_ROOT_NOT_FOUND` | S01 | Fatal | Abort | Path doesn't match any configured repo root |
| `F_HEADER_DEP_CYCLE` | S02 | Fatal | Abort | Circular dependency in header graph |
| `F_PREFIX_INVALID_FORMAT` | S11 | Recoverable | Quarantine | ID-like prefix fails pattern validation |
| `F_FILE_ID_COLLISION` | S11 | Fatal | Abort | Duplicate file_id already in registry |
| `F_ALLOCATOR_LOCK_FAIL` | S12 | Recoverable | Retry | Counter store lock contention |
| `F_REQUIRED_FIELD_NULL` | S21 | Fatal | Abort | `forbid_null` field has no value after derivation |
| `F_WRITE_POLICY_VIOLATION` | S31 | Fatal | Abort | Patch writes to field not allowed by policy |
| `F_SCHEMA_VALIDATION_FAIL` | S31 | Fatal | Rollback | Registry fails JSON Schema validation after patch |
| `F_ATOMIC_WRITE_FAIL` | S31 | Fatal | Rollback | File write/replace failed; restore backup |
| `F_GENERATOR_REBUILD_FAIL` | S32 | Recoverable | Retry | GEU sets rebuild failed; registry is valid but stale |

---

## Determinism Guarantees

1. All derivations use **pinned contract versions** and the **safe DSL** (no `eval`, `exec`, `import`, `lambda`)
2. Header applicability decided by **predicates over bounded file context**, not arbitrary code
3. Population order is **dependency-driven via topological sort** with stable tie-break
4. All writes are **atomic and single-writer**; allocator is **lock-protected**
5. Any fallback path (e.g., max_id+1) must be **explicitly enabled and logged as evidence**
6. Evidence bundles record: input snapshots, contract hashes, derivation traces, commit hashes

---

## Reference

- **Ingest Spec:** `REGISTRY/01260202173939000111_INGEST_SPEC_UNIFIED_REGISTRY.txt`
- **Column Headers Doc:** `REGISTRY/COLUMN_HEADERS/REGISTRY_COLUMN_HEADERS.md`
- **Folder Manifest:** `REGISTRY/00_REGISTRY_FOLDER_MANIFEST.md`
