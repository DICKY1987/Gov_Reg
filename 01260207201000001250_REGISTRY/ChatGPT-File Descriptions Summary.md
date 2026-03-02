# File Descriptions Summary

**User:** bill reed (richgwilks@gmail.com)  
**Created:** 3/1/2026 13:45:28  
**Updated:** 3/1/2026 15:38:27  
**Exported:** 3/1/2026 15:40:35  
**Link:** [https://chatgpt.com/g/g-p-690ce579540c8191a83eb108945f7da9-id-sub-module/c/69a49736-0bdc-8330-99d6-2c5fa216abb3?tab=files](https://chatgpt.com/g/g-p-690ce579540c8191a83eb108945f7da9-id-sub-module/c/69a49736-0bdc-8330-99d6-2c5fa216abb3?tab=files)  

## Response:
Thought for 2m 31s

What the attached files are (and what each one does)
----------------------------------------------------

### 1) `DOC-CORE-SSOT-SYS-TOOLS-ID-REGISTRY-1105__id_registry.py`

A **JSON-backed path↔ID registry library + CLI** for allocating stable IDs to paths and then keeping those IDs stable across renames/moves (via `update_path` + `path_history`).

DOC-CORE-SSOT-SYS-TOOLS-ID-REGI…

Key behaviors:

*   ID allocation is **prefix + monotonic counter** (example pattern: `DIR-00001`).
    DOC-CORE-SSOT-SYS-TOOLS-ID-REGI…
*   Maintains both `entries` (id→entry) and `path_index` (normalized\_path→id).
    DOC-CORE-SSOT-SYS-TOOLS-ID-REGI…
*   Provides `validate_integrity()` to detect duplicate paths and index/entry mismatches.
    DOC-CORE-SSOT-SYS-TOOLS-ID-REGI…
*   Includes a small CLI (`allocate`, `lookup`, `update`, `list`, `validate`).
    DOC-CORE-SSOT-SYS-TOOLS-ID-REGI…

### 2) `DOC-CONFIG-ID-REGISTRY-847__id_registry.json`

An **empty starter registry file** matching the structure used by `IdRegistry` (meta + `entries` + `path_index`).

DOC-CONFIG-ID-REGISTRY-847\_\_id\_…

### 3) `DOC-CONFIG-ID-REGISTRY-435__id_registry.json`

A **different** “directory registry” style JSON that maps **derived directory IDs** (e.g., `DIR-SSOT-<hash>`) to directory paths and provides indexes `by_id` and `by_path`.

DOC-CONFIG-ID-REGISTRY-435\_\_id\_…

This does **not** match the `entries/path_index` shape used by `IdRegistry` in `id_registry.py`.

DOC-CORE-SSOT-SYS-TOOLS-ID-REGI…

### 4) `DOC-TEST-UNIT-TEST-ID-REGISTRY-641__test_id_registry.py`

A **pytest test module** intended to test an ID registry tool, but it targets a **different API** than the `IdRegistry` in `DOC-CORE-SSOT-SYS-TOOLS-ID-REGISTRY-1105__id_registry.py`:

*   The tests call `allocate_id("A", "SSOT", "/path/to/artifact.py")` and assert IDs like `A-SSOT-###`.
    DOC-TEST-UNIT-TEST-ID-REGISTRY-…
*   The loaded module is expected to provide `IdType`, but the current `id_registry.py` only defines `IdRegistry`.
    DOC-CORE-SSOT-SYS-TOOLS-ID-REGI…

### 5) `DOC-CORE-UTI-TOOLS-VALIDATE-REGISTRY-823__validate_registry.py`

A **validator for `DOC_ID_REGISTRY.yaml`** (documentation ID registry), checking:

*   YAML syntax
*   required fields
*   duplicate `doc_id`s
*   optional `module_id` consistency against a taxonomy file
    DOC-CORE-UTI-TOOLS-VALIDATE-REG…
    It expects top-level keys `metadata`, `categories`, and `docs`.
    DOC-CORE-UTI-TOOLS-VALIDATE-REG…

### 6) `DOC-SCRIPT-1014__sync_doc_id_registry.py`

A **sync tool** that updates `DOC_ID_REGISTRY.yaml` based on `docs_inventory.jsonl`:

*   Builds an inventory dict keyed by `doc_id`, then adds entries that exist only in inventory into the registry.
    DOC-SCRIPT-1014\_\_sync\_doc\_id\_re…
    DOC-SCRIPT-1014\_\_sync\_doc\_id\_re…
*   Updates metadata fields like `total_docs` and `last_updated`.
    DOC-SCRIPT-1014\_\_sync\_doc\_id\_re…
    Important mismatch: it reads/writes a `documents` array (`registry.get('documents', [])`, `registry['documents']`)
    DOC-SCRIPT-1014\_\_sync\_doc\_id\_re…
    while `validate_registry.py` expects `docs`.
    DOC-CORE-UTI-TOOLS-VALIDATE-REG…

### 7) `DOC-SCRIPT-UTI-VALIDATE-CROSS-SYNC-001__validate_cross_registry_sync.py`

A **cross-registry synchronization validator** that checks alignment across:

1.  glossary term registry (`SUB_GLOSSARY/.glossary-metadata.yaml`)
2.  doc\_id registry (`SUB_DOC_ID/5_REGISTRY_DATA/DOC_ID_REGISTRY.yaml`)
3.  process index (`PROCESS_STEP_LIB/indices/master_index.json`)
    DOC-SCRIPT-UTI-VALIDATE-CROSS-S…

It generates a report with coverage metrics (doc\_id coverage, term coverage, implementation coverage) and derives an overall status (`PASS/WARN/FAIL/ERROR`) based on thresholds.

DOC-SCRIPT-UTI-VALIDATE-CROSS-S…

### 8) `DOC-VALIDATOR-ID-TYPE-REGISTRY-001__validate_id_type_registry.py`

A **validator for `ID_TYPE_REGISTRY.yaml`** enforcing:

*   required `meta` fields and `meta.total_types` matches actual count
    DOC-VALIDATOR-ID-TYPE-REGISTRY-…
*   uniqueness of `type_id`, valid enums for classification/tier/status/priority, plus special rule: derived types must include `derivation_rule`
    DOC-VALIDATOR-ID-TYPE-REGISTRY-…
*   warnings for `production` types missing `validators` or `coverage`
    DOC-VALIDATOR-ID-TYPE-REGISTRY-…

### 9) `DOC-VALIDATOR-REGISTRY-LOCKING-001__validate_registry_locking.py`

A **static enforcement tool** that tries to ensure registry writes are lock-protected by:

*   scanning python files for `.save()` calls on variables containing “registry”
*   heuristically checking for `with registry_lock` / `registry_lock(` near the call site
    DOC-VALIDATOR-REGISTRY-LOCKING-…
    It produces a JSON report with PASS/FAIL based on whether unlocked save calls were found.
    DOC-VALIDATOR-REGISTRY-LOCKING-…

### 10) `DOC-SCRIPT-0991__generate_id_registry.py`

A **bootstrap generator** for a new ID-type registry based on a spec found in `ID_TYPE_REGISTRY.yaml`:

*   Loads the ID type spec by `type_id`.
    DOC-SCRIPT-0991\_\_generate\_id\_re…
*   Creates: the registry YAML, `DIR_MANIFEST.yaml`, `.dir_id`, and a README; then updates the ID type status to `active`.
    DOC-SCRIPT-0991\_\_generate\_id\_re…
*   Its `generate_dir_id()` produces a **derived** dir id like `DIR-{SLUG}-{8hex}`.
    DOC-SCRIPT-0991\_\_generate\_id\_re…

How they fit together (high level)
----------------------------------

*   **DOC\_ID governance toolchain:** `validate_registry.py` + `sync_doc_id_registry.py` + `validate_cross_registry_sync.py` + `validate_id_type_registry.py` + `validate_registry_locking.py` form a “registry hygiene” bundle: validate structure, sync inventories, verify cross-system coverage, enforce ID-type definitions, and check locking.
    DOC-CORE-UTI-TOOLS-VALIDATE-REG…
    DOC-SCRIPT-UTI-VALIDATE-CROSS-S…
    DOC-VALIDATOR-REGISTRY-LOCKING-…
*   **Separate ID registry experiments/configs:** `id_registry.py` + `id_registry.json` files (`847`, `435`) represent two different approaches to “ID registry” (one is `entries/path_index`, the other is `dirs/index`).
    DOC-CORE-SSOT-SYS-TOOLS-ID-REGI…
    DOC-CONFIG-ID-REGISTRY-435\_\_id\_…

The biggest immediate red flags are **schema drift** (`docs` vs `documents`)

DOC-CORE-UTI-TOOLS-VALIDATE-REG…

DOC-SCRIPT-1014\_\_sync\_doc\_id\_re…

and **multiple incompatible ID formats** (`DIR-00001`, `DIR-{slug}-{hash}`, etc.).

DOC-CORE-SSOT-SYS-TOOLS-ID-REGI…

DOC-SCRIPT-0991\_\_generate\_id\_re…

## Response:
Thought for 53s

Schemas / Policies (define the ID Package contract)
---------------------------------------------------

*   **`UNIFIED_INGEST_ENVELOPE.schema.json`**  
    JSON Schema for the _event envelope_ that triggers ingestion. Requires fields like `trigger_event_kind`, `entity_kind`, `observed_at_utc`, `project_root_id`, `project_root_path`, `relative_path`, `depth`, `zone`, and forbids unknown fields (`additionalProperties: false`).
    UNIFIED\_INGEST\_ENVELOPE.schema
*   **`IDPKG_CONFIG.schema.json`**  
    JSON Schema for the _ID Package config_. It standardizes: governance thresholds (`staging_depth`, `governed_min_depth`), exclusions patterns, naming (`separator`, `python_prefix`), registry locations (`registry_path`, `patch_output_dir`), and allocator store/lock settings (`allocator_store_path`, `lock_timeout_ms`).
    IDPKG\_CONFIG.schema
*   **`PREFIX_POLICY.json`**  
    Naming policy for governed files: Python must use `P_` before the numeric file id; everything else has no letter prefix (only the numeric id).
    PREFIX\_POLICY
*   **`WRITE_POLICY_IDPKG.yaml`**  
    Write/immutability policy for the system:
    *   `.dir_id` anchor files: create-only (no delete; no modify except explicit migration tooling).
    *   file prefix enforcement: allowed to rename to _apply_ prefixes; forbidden to rename to _remove_ them.
    *   registry: **patch-only** mutations (RFC-6902), with an explicit immutable field list (`dir_id`, `file_id`, `project_root_id`, `allocated_at_utc`, `allocator_version`, etc.).
    *   explicit “restore prefix if missing” rule and “anchor must move with directory” rule.
        WRITE\_POLICY\_IDPKG

Gates / Validation (define what must be true to pass)
-----------------------------------------------------

*   **`GATE_CATALOG.json`**  
    Gate definitions for the unified file+directory identity system. Includes cross-cutting gates (allocator store location/lockability, patch-only provenance, staging not auto-registered) plus governed-only gates for directories and files (must have `.dir_id`, IDs unique, registry record must exist, python files must have `P_` prefix, `owning_dir_id` must match containing dir, etc.).
    GATE\_CATALOG
*   **`01260207201000000191_transition_vectors.yaml`**  
    A test-vector suite (23 vectors) that exercises lifecycle transitions and identity resolution outcomes (happy-path transitions like `PLANNED→PRESENT`, conflict kinds like `MULTI_MATCH`, quarantine states like `ORPHANED`, field precedence/immutability conflicts, and gate pass/fail scenarios including waivers).
    01260207201000000191\_transition…

Operational script (implements a deterministic rename/migration)
----------------------------------------------------------------

*   **`P_RENAME_REMOVE_DOC_TOKEN.py`**  
    A deterministic, staged renamer that removes legacy `DOC-*` tokens from filenames while preserving canonical IDs. It runs as: config → inventory → plan → collision detection (deterministic ordering + hash suffix) → emit artifacts (rename map + report + manifests) → optional execute behind a `PROCEED.txt` gate → rollback on failure → post-verify → run manifest.
    P\_RENAME\_REMOVE\_DOC\_TOKEN

Evidence / “verified state” documentation
-----------------------------------------

*   **`01260207201000000195_VERIFIED_ARTIFACT_BUNDLE.md`**  
    A commit-stamped evidence bundle claiming specific fixes are present and verified (allocator digit format, reservation lifecycle methods, atomic I/O + locking, monitor diagnostics, tests passing). This is “proof packaging” rather than a spec.
    01260207201000000195\_VERIFIED\_A…

Architectural spec (path indirection, not IDs)
----------------------------------------------

*   **`01260207201000000181_PATH ABSTRACTION & INDIRECTION LAYER (1).md`**  
    An agentic-CLI task spec to replace hard-coded paths with a stable _key → path_ registry (e.g., YAML `config/path_index.yaml`), a resolver library, and a CLI wrapper; includes integration ideas for a “Hardcoded Path Indexer” and gradual refactor strategy.
    01260207201000000181\_PATH ABSTR…

Mapping / Traceability artifact
-------------------------------

*   **`01260207201000000189_traceability_matrix.json`**  
    A stepwise traceability/mapping list: each step has `step_number`, `module_id`, input/output contracts, entrypoints (file paths + doc\_id), and whether an implementation exists. It reads like a system pipeline map with concrete entrypoint files.
    01260207201000000189\_traceabili…

What these files deliver together
---------------------------------

A near-complete “ID Package” governance kit:

*   **Contracts**: ingest envelope + config schema
*   **Rules**: prefix policy + write/immutability policy
*   **Enforcement**: gate catalog + transition test vectors
*   **Migration utility**: one deterministic renamer (DOC-token removal)
*   **Supporting docs**: path indirection spec + evidence/verification bundle + traceability mapping

One high-risk mismatch to flag
------------------------------

These governance files enforce **20-digit** identity assumptions in gates (e.g., `.dir_id must contain 20-digit dir_id`, python `P_` + 20-digit file id).

GATE\_CATALOG

But the verified bundle describes an allocator producing **22-digit IDs** (17-digit prefix + 5-digit counter) as the “critical fix.”

01260207201000000195\_VERIFIED\_A…

If both are meant to govern the same ID namespace, that’s a hard contradiction that needs reconciliation (either separate ID families, or the gate/policy language is outdated relative to the allocator).

## Response:




---
Powered by [ChatGPT Exporter](https://www.chatgptexporter.com)