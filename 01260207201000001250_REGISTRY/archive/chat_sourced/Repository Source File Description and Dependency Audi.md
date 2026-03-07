# Repository Source File Description and Dependency Audit

## Executive summary

This repository snapshot (as provided) contains **twenty** files spanning three main themes: **ID Package governance** (schemas, policies, gate catalog), **registry tooling** (generators/validators/tests), and **spec/evidence artifacts** (traceability matrix, transition vectors, “verified bundle”, path-abstraction spec). The files are internally inconsistent in multiple places, especially around **ID formats and registry schemas**, which will cause validators to fail, gates to block, and automation to diverge unless reconciled.

Top risks (with blunt remediation):

- **ID format fragmentation and contradictions**: file IDs appear as **20-digit numeric**, **22-digit numeric**, **short numeric doc IDs**, and **stringy derived IDs** (e.g., `DIR-<slug>-<hash>`), while gates and scripts hard-code one or the other. Normalize to a single canonical ID spec and enforce it with schemas + tests. (Evidence across `GATE_CATALOG.json`, transition vectors, token-removal script, and the verified bundle.) (Source: `GATE_CATALOG.json` lines 60–69 and 115–135; `01260207201000000191_transition_vectors.yaml` lines 72–84; `P_RENAME_REMOVE_DOC_TOKEN.py` line 45; `01260207201000000195_VERIFIED_ARTIFACT_BUNDLE.md` lines 64–74 and 572–576.)
- **Registry schema drift (“docs” vs “documents”)**: the sync script writes/reads `documents`, while the validator and cross-sync validator expect `docs`. This is a guaranteed break in the DOC_ID pipeline. Pick one schema, version it, and update all tools. (Source: `DOC-SCRIPT-1014__sync_doc_id_registry.py` lines 40–45 and 70–77; `DOC-CORE-UTI-TOOLS-VALIDATE-REGISTRY-823__validate_registry.py` lines 75–83; `DOC-SCRIPT-UTI-VALIDATE-CROSS-SYNC-001__validate_cross_registry_sync.py` lines 106–112.)
- **Gate/policy vs generator conflict for `.dir_id`**: gates demand a `.dir_id` containing a **20-digit dir_id**, but the registry generator and one sample registry use **derived** directory IDs (`DIR-...-<hash>`). Decide whether dir IDs are minted numeric or derived string IDs, and align gates, generators, and registries accordingly. (Source: `GATE_CATALOG.json` lines 60–69; `DOC-SCRIPT-0991__generate_id_registry.py` lines 43–54 and 124–137; `DOC-CONFIG-ID-REGISTRY-435__id_registry.json` lines 295–305.)
- **Portability and determinism risks from hard-coded absolute paths**: the DOC-token removal script is effectively pinned to a specific Windows filesystem layout, directly contradicting the repo’s own “path indirection” spec. Parameterize via config + CLI and/or adopt the key→path resolver. (Source: `P_RENAME_REMOVE_DOC_TOKEN.py` lines 652–660; `01260207201000000181_PATH ABSTRACTION & INDIRECTION LAYER (1).md` lines 29–34.)
- **Tests and implementation do not match**: the ID registry unit tests expect an **entirely different IdRegistry API and registry JSON shape** than the actual `IdRegistry` implementation in this snapshot. Fix either the tests or the implementation, but don’t leave both. (Source: `DOC-TEST-UNIT-TEST-ID-REGISTRY-641__test_id_registry.py` lines 18–25, 32–55, and 60–88; `DOC-CORE-SSOT-SYS-TOOLS-ID-REGISTRY-1105__id_registry.py` lines 47–55 and 85–90.)

## Scope and inventory

The repository root is unspecified; the system only has access to the files mounted in the environment. All observed files are in a single attachment directory (no subdirectories visible), so “grouped by directory” effectively means **one directory** containing all files. Paths below are the observed filenames.

The timestamps and sizes below come from filesystem metadata available in the execution environment.

| Path (observed) | Size (bytes) | Last modified (America/Chicago) | Last modified (UTC) | Language |
|---|---:|---|---|---|
| `01260207201000000181_PATH ABSTRACTION & INDIRECTION LAYER (1).md` | 13971 | 2026-03-01 15:18:04 CST | 2026-03-01 21:18:04 UTC | Markdown |
| `01260207201000000189_traceability_matrix.json` | 13503 | 2026-03-01 15:18:04 CST | 2026-03-01 21:18:04 UTC | JSON |
| `01260207201000000191_transition_vectors.yaml` | 11512 | 2026-03-01 15:18:04 CST | 2026-03-01 21:18:04 UTC | YAML |
| `01260207201000000195_VERIFIED_ARTIFACT_BUNDLE.md` | 23109 | 2026-03-01 15:18:03 CST | 2026-03-01 21:18:03 UTC | Markdown |
| `DOC-CONFIG-ID-REGISTRY-435__id_registry.json` | 13763 | 2026-03-01 15:18:06 CST | 2026-03-01 21:18:06 UTC | JSON |
| `DOC-CONFIG-ID-REGISTRY-847__id_registry.json` | 213 | 2026-03-01 15:18:05 CST | 2026-03-01 21:18:05 UTC | JSON |
| `DOC-CORE-SSOT-SYS-TOOLS-ID-REGISTRY-1105__id_registry.py` | 11574 | 2026-03-01 15:18:04 CST | 2026-03-01 21:18:04 UTC | Python |
| `DOC-CORE-UTI-TOOLS-VALIDATE-REGISTRY-823__validate_registry.py` | 8991 | 2026-03-01 15:18:04 CST | 2026-03-01 21:18:04 UTC | Python |
| `DOC-SCRIPT-0991__generate_id_registry.py` | 12249 | 2026-03-01 15:18:04 CST | 2026-03-01 21:18:04 UTC | Python |
| `DOC-SCRIPT-1014__sync_doc_id_registry.py` | 3615 | 2026-03-01 15:18:03 CST | 2026-03-01 21:18:03 UTC | Python |
| `DOC-SCRIPT-UTI-VALIDATE-CROSS-SYNC-001__validate_cross_registry_sync.py` | 15716 | 2026-03-01 15:18:04 CST | 2026-03-01 21:18:04 UTC | Python |
| `DOC-TEST-UNIT-TEST-ID-REGISTRY-641__test_id_registry.py` | 6280 | 2026-03-01 15:18:04 CST | 2026-03-01 21:18:04 UTC | Python |
| `DOC-VALIDATOR-ID-TYPE-REGISTRY-001__validate_id_type_registry.py` | 5587 | 2026-03-01 15:18:04 CST | 2026-03-01 21:18:04 UTC | Python |
| `DOC-VALIDATOR-REGISTRY-LOCKING-001__validate_registry_locking.py` | 8605 | 2026-03-01 15:18:05 CST | 2026-03-01 21:18:05 UTC | Python |
| `GATE_CATALOG.json` | 4177 | 2026-03-01 15:18:04 CST | 2026-03-01 21:18:04 UTC | JSON |
| `IDPKG_CONFIG.schema.json` | 2778 | 2026-03-01 15:18:04 CST | 2026-03-01 21:18:04 UTC | JSON Schema |
| `PREFIX_POLICY.json` | 572 | 2026-03-01 15:18:04 CST | 2026-03-01 21:18:04 UTC | JSON |
| `P_RENAME_REMOVE_DOC_TOKEN.py` | 30119 | 2026-03-01 15:18:04 CST | 2026-03-01 21:18:04 UTC | Python |
| `UNIFIED_INGEST_ENVELOPE.schema.json` | 2046 | 2026-03-01 15:18:04 CST | 2026-03-01 21:18:04 UTC | JSON Schema |
| `WRITE_POLICY_IDPKG.yaml` | 2300 | 2026-03-01 15:18:04 CST | 2026-03-01 21:18:04 UTC | YAML |

## File-level descriptions

### Unified ingest envelope schema

**File:** `UNIFIED_INGEST_ENVELOPE.schema.json`  
This JSON Schema defines the **ingest event envelope** for a unified file/directory ingestion pipeline, requiring a trigger kind, entity kind, observation timestamp, project root identifiers, a repo-relative path, depth, and a computed governance zone. It optionally allows a `desired_action` enum (e.g., `register`, `ignore`, `promote`) to steer ingest behavior. The envelope is strict: unknown top-level fields are rejected (`additionalProperties: false`), while the nested `context` object allows arbitrary keys. (Source: `UNIFIED_INGEST_ENVELOPE.schema.json` lines 5–14, 62–71, and 72–74.)

### ID package config schema

**File:** `IDPKG_CONFIG.schema.json`  
This JSON Schema defines an **ID Package configuration** object with required sections for governance, naming, registry, and allocator settings. Governance includes depth-based zoning (`staging_depth`, `governed_min_depth`), naming defines filename conventions (`separator`, `python_prefix`), and allocator settings require `allocator_store_path` and `lock_timeout_ms` (implying lock-based concurrency control). The schema is strict throughout (`additionalProperties: false`). (Source: `IDPKG_CONFIG.schema.json` lines 5–12, 24–46, 55–75, 82–95, and 94–98.)

### Prefix policy for governed filenames

**File:** `PREFIX_POLICY.json`  
This policy defines governed-zone filename prefixes by extension: Python files must use the `P_` prefix before the numeric file ID, while all other file types use no letter prefix and rely solely on the numeric file ID. The rules are explicitly scoped to `entity_kind: file` and `zone: governed`. (Source: `PREFIX_POLICY.json` lines 1–19.)

### Write policy for identity governance

**File:** `WRITE_POLICY_IDPKG.yaml`  
This policy document defines immutability and mutation constraints for the identity system: `.dir_id` anchors are create-only (no delete; no modify except migration), and users must not rename governed files to remove prefixes. Registry mutation must be **patch-only** via RFC 6902 patches, with a declared immutable field set (`dir_id`, `file_id`, `project_root_id`, `allocated_at_utc`, `allocator_version`) and a separate mutable field set (paths, parent/owning IDs, timestamps, semantic keys, extra metadata). It also asserts that file IDs and directory IDs must never change and that missing prefixes must be restored from registry state. (Source: `WRITE_POLICY_IDPKG.yaml` lines 3–12, 14–22, 24–44, 45–59.)

### Gate catalog for the ID package

**File:** `GATE_CATALOG.json`  
This gate catalog defines blocking gates for a “Unified File+Directory ID Package (IDPKG)”, including cross-cutting constraints (allocator store outside project root, lockability, patch-only registry mutation, and no auto-registration in staging). Governed directory gates require a `.dir_id`, require it to contain a **20-digit dir_id**, and require a directory record in the registry; governed file gates require a valid ID prefix, require Python files to use `P_` before a **20-digit file_id**, and require registry uniqueness and ownership consistency. These gates hard-code the “20-digit” requirement for both directory and file IDs. (Source: `GATE_CATALOG.json` lines 1–15, 5–48, 60–69, and 115–135.)

### DOC token removal renamer

**File:** `P_RENAME_REMOVE_DOC_TOKEN.py`  
This script implements a staged renaming pipeline that **removes `DOC-*` tokens** from governed Python filenames while preserving the canonical file ID. It scans target roots for files matching a regex of the form `P_<20digits>_DOC-...__<rest>` and plans renames to `P_<20digits>_<rest>`, enforcing invariants like “prefix remains `P_`”, extension unchanged, and extracted `file_id` unchanged. The tool emits planning artifacts (`RENAME_MAP.json`, `PLAN_REPORT.md`, and “before” manifests) and won’t execute renames unless a **`PROCEED.txt` gate file** contains `PROCEED_RENAME=YES`. In the provided main configuration it contains hard-coded Windows paths for both `target_roots` and output, making it non-portable without modification. (Source: `P_RENAME_REMOVE_DOC_TOKEN.py` lines 45–55, 121–152, 300–320, 347–357, 382–409, and 652–660.)

Example of the enforced filename match rule:
```python
MATCH_REGEX = re.compile(r'^(P_\d{20})_DOC-.*?__+(.+)$')
```
(Source: `P_RENAME_REMOVE_DOC_TOKEN.py` line 45.)

### Simple JSON-backed path-to-ID registry tool

**File:** `DOC-CORE-SSOT-SYS-TOOLS-ID-REGISTRY-1105__id_registry.py`  
This module defines an `IdRegistry` class for stable, never-reused IDs bound to paths, backed by a JSON file. It normalizes paths using POSIX separators and lowercasing, allocates IDs with a **monotonic counter** per prefix (e.g., `DIR-00001`), and records `path_history` so path moves/renames keep the same ID. It also provides integrity validation (duplicate paths, index mismatches) and a CLI with commands like allocate, lookup, update, list, and validate. This registry writer performs full JSON rewrites (`json.dump`) without any explicit file locking or patch-only semantics. (Source: `DOC-CORE-SSOT-SYS-TOOLS-ID-REGISTRY-1105__id_registry.py` lines 1–15, 47–55, 75–83, 170–193, 223–263, and 266–294.)

Example of the allocation format:
```python
return f"{prefix}-{next_num:05d}"
```
(Source: `DOC-CORE-SSOT-SYS-TOOLS-ID-REGISTRY-1105__id_registry.py` lines 75–83.)

### Empty registry seed matching the `IdRegistry` format

**File:** `DOC-CONFIG-ID-REGISTRY-847__id_registry.json`  
This is a seed/blank JSON registry file shaped with `entries`, `path_index`, and `meta` timestamps, plus a `doc_id`. Its shape aligns with what `IdRegistry._load_registry()` creates when the file does not exist (meta + entries + path_index). (Source: `DOC-CONFIG-ID-REGISTRY-847__id_registry.json` lines 1–10; `DOC-CORE-SSOT-SYS-TOOLS-ID-REGISTRY-1105__id_registry.py` lines 47–55.)

### Artifact and directory registry with derived directory IDs

**File:** `DOC-CONFIG-ID-REGISTRY-435__id_registry.json`  
Despite its filename, this JSON document is not the same schema as the `IdRegistry` path-index tool; it holds `artifacts`, `directories`, an `index`, and `meta` fields, functioning more like a work/artifact catalog and directory ID mapping. Directory IDs are **derived string IDs** like `DIR-PHASE-0-BOOTSTRAP-9678ee7e`, mapping to logical repo paths like `PHASE_0_BOOTSTRAP`. The file ends with a `doc_id` identifying it as `DOC-CONFIG-ID-REGISTRY-435`. (Source: `DOC-CONFIG-ID-REGISTRY-435__id_registry.json` lines 1–10, 295–305, and 387–392.)

### DOC ID registry validator

**File:** `DOC-CORE-UTI-TOOLS-VALIDATE-REGISTRY-823__validate_registry.py`  
This script validates a YAML-based `DOC_ID_REGISTRY.yaml` located under a `doc_id/specs` folder rooted at `REPO_ROOT = Path(__file__).parent.parent`. It enforces that the registry contains top-level keys `metadata`, `categories`, and `docs`, validates required fields per doc entry, and enforces a `doc_id` format that must start with `"DOC-"`. It can generate a JSON validation report containing timestamps, registry path, errors, and warnings. (Source: `DOC-CORE-UTI-TOOLS-VALIDATE-REGISTRY-823__validate_registry.py` lines 3–16, 23–33, 75–83, 113–119, and 180–187.)

### DOC ID registry sync script

**File:** `DOC-SCRIPT-1014__sync_doc_id_registry.py`  
This script syncs a YAML registry file named `DOC_ID_REGISTRY.yaml` with an inventory file `docs_inventory.jsonl` in the same directory as the script. It parses JSONL into a dict keyed by `doc_id`, compares against registry entries, then appends missing inventory entries into the registry and updates registry metadata (`total_docs`, `last_updated`). Critically, it treats the registry list as `registry['documents']`, which conflicts with the validator’s `docs` expectation. (Source: `DOC-SCRIPT-1014__sync_doc_id_registry.py` lines 1–5, 17–27, 40–45, 60–71, and 75–84.)

### Cross-registry synchronization validator

**File:** `DOC-SCRIPT-UTI-VALIDATE-CROSS-SYNC-001__validate_cross_registry_sync.py`  
This validator is designed to check consistency across three registries: a glossary metadata YAML, a doc_id registry YAML under `SUB_DOC_ID/5_REGISTRY_DATA`, and a process index JSON under `PROCESS_STEP_LIB/indices`. It computes coverage metrics (doc ID coverage, term coverage, implementation coverage) and emits a report that includes percentages and counts, plus warnings and errors. The overall status is determined strictly from “errors present” and doc ID coverage thresholds (FAIL if <70, WARN if <85, PASS otherwise), even though other metrics are computed. (Source: `DOC-SCRIPT-UTI-VALIDATE-CROSS-SYNC-001__validate_cross_registry_sync.py` lines 4–16, 74–83, 106–112, 296–306, and 308–317.)

### ID type registry validator

**File:** `DOC-VALIDATOR-ID-TYPE-REGISTRY-001__validate_id_type_registry.py`  
This script validates an `ID_TYPE_REGISTRY.yaml` assumed to be co-located with the script (`Path(__file__).parent / "ID_TYPE_REGISTRY.yaml"`). It enforces meta fields, checks `meta.total_types` matches the actual number of `id_types`, validates required fields per type, validates allowed classifications, and requires `derivation_rule` for any type with `classification: derived`. It also validates summary counts (if present) against computed status counts. (Source: `DOC-VALIDATOR-ID-TYPE-REGISTRY-001__validate_id_type_registry.py` lines 13–16, 40–41, 46–54, and 68–70.)

### ID type registry bootstrap generator

**File:** `DOC-SCRIPT-0991__generate_id_registry.py`  
This script bootstraps registry infrastructure for a given ID type by reading a spec from `RUNTIME/doc_id/SUB_DOC_ID/ID_TYPE_REGISTRY.yaml`. It generates a registry YAML, a directory manifest, a `.dir_id` anchor file (JSON), and a README, then updates the ID type’s status in `ID_TYPE_REGISTRY.yaml` (e.g., planned → active). Directory IDs are generated as `DIR-<slugified_path>-<8_char_hash>`, but the `.dir_id` metadata claims the derivation is “slugified_path + blake2b_8char” even though the function uses SHA-256 and truncates to 8 hex chars. (Source: `DOC-SCRIPT-0991__generate_id_registry.py` lines 25–31, 43–54, 124–137, 278–301, and 303–353.)

### Registry locking validator

**File:** `DOC-VALIDATOR-REGISTRY-LOCKING-001__validate_registry_locking.py`  
This validator performs lightweight static analysis to find `registry.save()` calls and heuristically checks whether surrounding lines contain something like `with registry_lock` to infer locking discipline. It only searches Python files under `RUNTIME`, `scripts`, and `tests`, so any registry writes outside those directories are ignored. The “lock detection” is string-based and context-window-based, so it can both miss real locking and incorrectly approve false positives. (Source: `DOC-VALIDATOR-REGISTRY-LOCKING-001__validate_registry_locking.py` lines 3–10, 39–49, and 93–99.)

### Unit test suite for an ID registry

**File:** `DOC-TEST-UNIT-TEST-ID-REGISTRY-641__test_id_registry.py`  
This pytest module attempts to load the registry tool file by name via `_ssot_tool_loader.load_tool()` and then expects the loaded module to provide `IdRegistry` and `IdType`. The tests assume an API where `allocate_id` takes `(type_code, category, artifact_path)` and emits IDs like `A-SSOT-<digits>`, along with methods like `lookup_by_artifact()`, `list_by_category()`, `validate_id()`, and `exists()`. The fixture’s initial JSON registry shape (`allocations`, `indexes`) does not match the `IdRegistry` module’s default shape (`entries`, `path_index`), so this test suite is not compatible with the `IdRegistry` implementation present in this snapshot. (Source: `DOC-TEST-UNIT-TEST-ID-REGISTRY-641__test_id_registry.py` lines 18–25, 32–55, 60–66, 106–118, and 132–134; `DOC-CORE-SSOT-SYS-TOOLS-ID-REGISTRY-1105__id_registry.py` lines 47–55 and 85–90.)

### Path abstraction and indirection specification

**File:** `01260207201000000181_PATH ABSTRACTION & INDIRECTION LAYER (1).md`  
This Markdown document is an “agentic CLI task specification” to eliminate hard-coded paths in scripts/configs by introducing a stable **key → path registry** and a resolver library/CLI. It names current anchors explicitly: a registry at `config/path_index.yaml`, a resolver at `src/path_registry.py`, and a CLI wrapper at `scripts/dev/paths_resolve_cli.py`. It includes example YAML registry structures and conceptual resolver APIs. (Source: `01260207201000000181_PATH ABSTRACTION & INDIRECTION LAYER (1).md` lines 1–3 and 29–34.)

### Verified artifact bundle

**File:** `01260207201000000195_VERIFIED_ARTIFACT_BUNDLE.md`  
This is an evidence-style bundle claiming a set of “critical fixes” are present at a specific commit, listing allocator/ledger/shared-utils/monitor/test files and what fixes were applied. It includes embedded code showing an allocator that claims to generate **22-digit IDs** using a 17-digit prefix plus a five-digit counter, and includes a test snippet asserting `len(id1) == 22` and `id1.endswith("00001")`. The manifest filenames themselves use a `P_<20digit>_...` format, which clashes with the document’s “22-digit IDs” narrative unless the repo distinguishes between “file_id in filenames” and “allocator output IDs.” (Source: `01260207201000000195_VERIFIED_ARTIFACT_BUNDLE.md` lines 10–16, 29–31, 64–72, and 572–576.)

### Process traceability matrix

**File:** `01260207201000000189_traceability_matrix.json`  
This JSON document is a list of process steps with fields like `step_number`, `module_id`, input/output contracts, and entrypoints. Each entrypoint records a file path, a `doc_id`, and a role; for example, it references service entrypoints under `services/.../src/..._main.py` with numeric doc IDs. Many steps are explicitly marked `has_implementation: false`, making this more of a “what should exist” map than a guarantee of what is present. (Source: `01260207201000000189_traceability_matrix.json` lines 3–12 and 68–80.)

### Transition vector suite

**File:** `01260207201000000191_transition_vectors.yaml`  
This YAML file defines a suite of “test vectors” describing lifecycle transitions and expected outcomes for record identity resolution, including happy path, blocked transitions, and conflict scenarios. It includes a “strong identity” example where a planned record with a 20-digit `file_id` matches an observed path whose filename includes `P_<20digit>_...`, encoding a strong dependency on that filename convention. The vectors read like acceptance tests for an identity resolver/state machine, but the corresponding implementation is not part of this snapshot. (Source: `01260207201000000191_transition_vectors.yaml` lines 68–84.)

## Inter-file dependencies and data flows

### Dependency map table

The table below focuses on explicit references present in this snapshot: file reads/writes, expected registry locations, and direct string references.

| Source file | Depends on / interacts with | Relationship | Practical impact |
|---|---|---|---|
| `WRITE_POLICY_IDPKG.yaml` | `PREFIX_POLICY.json` | Policy references prefix rules for governed filenames | Prefix enforcement must be implemented by a resolver/ingest engine; otherwise policy is aspirational. (Source: `WRITE_POLICY_IDPKG.yaml` lines 14–18.) |
| `GATE_CATALOG.json` | `.dir_id` anchors + governance registry (not provided) | Gates assume existence of anchor schema + registry records | Any implementation must satisfy “20-digit ID” conventions to pass. (Source: `GATE_CATALOG.json` lines 60–69 and 115–135.) |
| `P_RENAME_REMOVE_DOC_TOKEN.py` | `PROCEED.txt`, emits `RENAME_MAP.json`, `PLAN_REPORT.md`, manifests/logs | Generates artifacts and conditionally renames files | Tool is safe by default (plan-only) but is non-portable as shipped due to hard-coded paths. (Source: `P_RENAME_REMOVE_DOC_TOKEN.py` lines 316–320, 347–357, and 652–660.) |
| `DOC-CORE-UTI-TOOLS-VALIDATE-REGISTRY-823__validate_registry.py` | `doc_id/specs/DOC_ID_REGISTRY.yaml`, `doc_id/specs/module_taxonomy.yaml` | Reads and validates registry + taxonomy | Any registry not shaped as `metadata/categories/docs` will fail validation. (Source: `DOC-CORE-UTI-TOOLS-VALIDATE-REGISTRY-823__validate_registry.py` lines 23–33 and 75–83.) |
| `DOC-SCRIPT-1014__sync_doc_id_registry.py` | `DOC_ID_REGISTRY.yaml`, `docs_inventory.jsonl`, `common.REPO_ROOT` | Reads/writes registry and reads inventory | Produces/depends on `documents` list, which is incompatible with the validator expecting `docs`. (Source: `DOC-SCRIPT-1014__sync_doc_id_registry.py` lines 13–16 and 40–45.) |
| `DOC-SCRIPT-UTI-VALIDATE-CROSS-SYNC-001__validate_cross_registry_sync.py` | `SUB_GLOSSARY/.glossary-metadata.yaml`, `SUB_DOC_ID/5_REGISTRY_DATA/DOC_ID_REGISTRY.yaml`, `PROCESS_STEP_LIB/indices/master_index.json` | Reads three systems and computes sync report | Assumes doc registry uses `docs` array; defines PASS/WARN/FAIL thresholds mainly on doc ID coverage. (Source: `DOC-SCRIPT-UTI-VALIDATE-CROSS-SYNC-001__validate_cross_registry_sync.py` lines 6–9, 106–112, and 308–317.) |
| `DOC-SCRIPT-0991__generate_id_registry.py` | `RUNTIME/doc_id/SUB_DOC_ID/ID_TYPE_REGISTRY.yaml` | Reads ID type specs; writes registry/manifest/anchor/README and updates status | Produces derived `DIR-...-hash` IDs, contradicting gates that require 20-digit IDs. (Source: `DOC-SCRIPT-0991__generate_id_registry.py` lines 25–31, 43–54, 124–137, and 278–301.) |
| `DOC-VALIDATOR-ID-TYPE-REGISTRY-001__validate_id_type_registry.py` | `ID_TYPE_REGISTRY.yaml` (co-located) | Validates required fields + derived rule | Its file location assumption may not match the generator’s hard-coded registry path. (Source: `DOC-VALIDATOR-ID-TYPE-REGISTRY-001__validate_id_type_registry.py` line 13; `DOC-SCRIPT-0991__generate_id_registry.py` line 280.) |
| `DOC-TEST-UNIT-TEST-ID-REGISTRY-641__test_id_registry.py` | `DOC-CORE-SSOT-SYS-TOOLS-ID-REGISTRY-1105__id_registry.py` (via loader) | Expects different API/JSON schema | Test suite won’t meaningfully validate the included `IdRegistry` tool. (Source: `DOC-TEST-UNIT-TEST-ID-REGISTRY-641__test_id_registry.py` lines 18–25 and 32–55; `DOC-CORE-SSOT-SYS-TOOLS-ID-REGISTRY-1105__id_registry.py` lines 47–55.) |
| `01260207201000000181_PATH ABSTRACTION & INDIRECTION LAYER (1).md` | `config/path_index.yaml`, `src/path_registry.py`, `scripts/dev/paths_resolve_cli.py` | Specifies an indirection system | Contradicts scripts with embedded absolute paths until adopted. (Source: `01260207201000000181_PATH ABSTRACTION & INDIRECTION LAYER (1).md` lines 29–34; `P_RENAME_REMOVE_DOC_TOKEN.py` lines 652–660.) |

### Mermaid data-flow sketch

The following diagram reflects **intended** flows implied by schemas/policies + tooling (not a guarantee of current runtime behavior, because full ingest/resolver implementations are not present in this snapshot).

```mermaid
flowchart TD
  subgraph Identity_Governance
    Cfg[IDPKG_CONFIG.schema.json] --> Env[UNIFIED_INGEST_ENVELOPE.schema.json]
    Prefix[PREFIX_POLICY.json] --> Gates[GATE_CATALOG.json]
    Policy[WRITE_POLICY_IDPKG.yaml] --> Gates
    Cfg --> Gates
    Env --> Gates
    Gates --> Reg[Governance Registry\nnot included here]
    Reg -->|restore prefixes| RenameOps[P_RENAME_REMOVE_DOC_TOKEN.py\n(optional maintenance)]
  end

  subgraph Doc_ID_Registry_Tooling
    Inventory[docs_inventory.jsonl\nnot included here] --> Sync[DOC-SCRIPT-1014__sync_doc_id_registry.py]
    Sync --> DocReg[DOC_ID_REGISTRY.yaml\nnot included here]
    DocReg --> Validate[DOC-CORE-UTI-TOOLS-VALIDATE-REGISTRY-823__validate_registry.py]
    Gloss[SUB_GLOSSARY/.glossary-metadata.yaml\nnot included here] --> Cross[DOC-SCRIPT-UTI-VALIDATE-CROSS-SYNC-001__validate_cross_registry_sync.py]
    DocReg --> Cross
    Proc[PROCESS_STEP_LIB/indices/master_index.json\nnot included here] --> Cross
  end

  subgraph ID_Type_Registry
    TypeReg[RUNTIME/doc_id/SUB_DOC_ID/ID_TYPE_REGISTRY.yaml\nnot included here] --> Gen[DOC-SCRIPT-0991__generate_id_registry.py]
    TypeReg --> TypeVal[DOC-VALIDATOR-ID-TYPE-REGISTRY-001__validate_id_type_registry.py]
    Gen --> DirAnchor[.dir_id + DIR_MANIFEST.yaml + README\ngenerated outputs]
  end

  subgraph Legacy_Path_ID_Registry
    Seed[DOC-CONFIG-ID-REGISTRY-847__id_registry.json] --> IdRegTool[DOC-CORE-SSOT-SYS-TOOLS-ID-REGISTRY-1105__id_registry.py]
    Tests[DOC-TEST-UNIT-TEST-ID-REGISTRY-641__test_id_registry.py] -.API mismatch.- IdRegTool
  end
```

(Source basis for this sketch: `UNIFIED_INGEST_ENVELOPE.schema.json` lines 5–14; `IDPKG_CONFIG.schema.json` lines 5–12 and 82–92; `WRITE_POLICY_IDPKG.yaml` lines 24–44; `GATE_CATALOG.json` lines 5–48; `DOC-SCRIPT-1014__sync_doc_id_registry.py` lines 17–27 and 40–45; `DOC-CORE-UTI-TOOLS-VALIDATE-REGISTRY-823__validate_registry.py` lines 23–33 and 75–83; `DOC-SCRIPT-UTI-VALIDATE-CROSS-SYNC-001__validate_cross_registry_sync.py` lines 6–9 and 106–112; `DOC-SCRIPT-0991__generate_id_registry.py` lines 25–31 and 278–301; `DOC-CONFIG-ID-REGISTRY-847__id_registry.json` lines 1–10; `DOC-TEST-UNIT-TEST-ID-REGISTRY-641__test_id_registry.py` lines 18–25.)

## Schema mismatches, incompatible ID formats, and gate/policy contradictions

### Mismatch and contradiction table

| Category | What conflicts | Evidence in files | Why it matters |
|---|---|---|---|
| ID length | **20-digit** ID expectations vs **22-digit** allocator claims | Gates require “20-digit dir_id” and “20-digit file_id”. (Source: `GATE_CATALOG.json` lines 60–69 and 115–124.) Transition vectors use 20-digit `file_id` and `P_<20digit>` filenames. (Source: `01260207201000000191_transition_vectors.yaml` lines 72–84.) Rename script hard-codes `P_\d{20}`. (Source: `P_RENAME_REMOVE_DOC_TOKEN.py` line 45.) Verified bundle asserts 22-digit IDs and tests `len(id1) == 22`. (Source: `01260207201000000195_VERIFIED_ARTIFACT_BUNDLE.md` lines 64–72 and 572–576.) | Ingestion, validation, and maintenance tooling will disagree about what is valid; identity matching can fail silently or block deployments. |
| Directory ID format | Gate wants numeric 20-digit dir_id; generator emits `DIR-<slug>-<hash>` | Gate DIR-G2 requires “20-digit dir_id”. (Source: `GATE_CATALOG.json` lines 60–66.) Generator returns `DIR-{path_slug}-{hash_str}`. (Source: `DOC-SCRIPT-0991__generate_id_registry.py` lines 43–54.) Sample registry uses IDs like `DIR-PHASE-0-BOOTSTRAP-9678ee7e`. (Source: `DOC-CONFIG-ID-REGISTRY-435__id_registry.json` lines 295–305.) | Either the gate definition is wrong/outdated or the generator/registry strategy is wrong; you can’t satisfy both at once. |
| DOC_ID registry schema | `docs` vs `documents` key mismatch | Validator requires top-level `docs`. (Source: `DOC-CORE-UTI-TOOLS-VALIDATE-REGISTRY-823__validate_registry.py` lines 75–83.) Cross-sync validator reads `get('docs', [])`. (Source: `DOC-SCRIPT-UTI-VALIDATE-CROSS-SYNC-001__validate_cross_registry_sync.py` lines 106–112.) Sync script reads/writes `registry['documents']`. (Source: `DOC-SCRIPT-1014__sync_doc_id_registry.py` lines 40–45 and 70–77.) | Sync output won’t validate; cross-sync checks may undercount or fail; registry maintenance becomes unreliable. |
| Registry write semantics | Patch-only registry policy vs full-file rewrite tools | Policy mandates patch-only RFC 6902 for registry mutations and immutable fields. (Source: `WRITE_POLICY_IDPKG.yaml` lines 24–44.) `IdRegistry` saves by rewriting JSON via `json.dump(...)`. (Source: `DOC-CORE-SSOT-SYS-TOOLS-ID-REGISTRY-1105__id_registry.py` lines 57–63.) | Breaks immutability/provenance guarantees; makes concurrent writes and audits harder; undermines the stated governance model. |
| ID registry implementation vs tests | Tests assume a different ID registry API and storage schema | Tests expect `allocate_id("A","SSOT","/path")` and IDs like `A-SSOT-...` plus methods `validate_id`, `exists`, `lookup_by_artifact`, `list_by_category`. (Source: `DOC-TEST-UNIT-TEST-ID-REGISTRY-641__test_id_registry.py` lines 60–66 and 106–118.) Included `IdRegistry.allocate_id` signature is `(path, prefix="DIR", metadata=None)` returning `DIR-00001`-style IDs and uses `entries/path_index`. (Source: `DOC-CORE-SSOT-SYS-TOOLS-ID-REGISTRY-1105__id_registry.py` lines 47–55 and 85–90.) | The test suite can’t validate the actual implementation; failures will be hidden by skips or meaningless passes. |
| Hash algorithm self-contradiction | “derivation” claims blake2b while code uses sha256 | ID generator uses SHA-256 truncated to 8 hex chars. (Source: `DOC-SCRIPT-0991__generate_id_registry.py` lines 49–53.) `.dir_id` metadata says “slugified_path + blake2b_8char”. (Source: `DOC-SCRIPT-0991__generate_id_registry.py` lines 130–137.) | Documentation/evidence becomes untrustworthy; reproducibility and auditability suffer. |
| Path strategy contradiction | Path-indirection spec vs hard-coded paths in scripts | Spec explicitly targets replacement of hard-coded paths and names the path registry and resolver modules. (Source: `01260207201000000181_PATH ABSTRACTION & INDIRECTION LAYER (1).md` lines 29–34.) Token removal script hard-codes absolute Windows paths. (Source: `P_RENAME_REMOVE_DOC_TOKEN.py` lines 652–660.) | Prevents portability, complicates CI, and increases the cost of moving directories. |

### Clarifying snippets

Schema vs implementation drift (DOC_ID registry):

```python
print(f"📊 Registry: {len(registry.get('documents', []))} docs")
registry_docs = {doc['doc_id']: doc for doc in registry.get('documents', []) if 'doc_id' in doc}
```
(Source: `DOC-SCRIPT-1014__sync_doc_id_registry.py` lines 40–45.)

```python
required_keys = ["metadata", "categories", "docs"]
```
(Source: `DOC-CORE-UTI-TOOLS-VALIDATE-REGISTRY-823__validate_registry.py` lines 75–79.)

## Remediation roadmap

A practical fix path that reduces breakage fast:

First, **freeze and define canonical schemas**. Create authoritative schemas for:
- The governance registry file(s) (including fields marked immutable in `WRITE_POLICY_IDPKG.yaml`). (Source: `WRITE_POLICY_IDPKG.yaml` lines 24–44.)
- The DOC_ID registry YAML shape (decide `docs` vs `documents` and version it). (Source: `DOC-CORE-UTI-TOOLS-VALIDATE-REGISTRY-823__validate_registry.py` lines 75–83; `DOC-SCRIPT-1014__sync_doc_id_registry.py` lines 40–45.)

Second, **standardize ID formats**. Decide:
- Whether “file_id” is 20-digit or 22-digit (and whether filenames should embed the same value the allocator outputs). Gates and test vectors currently encode 20-digit assumptions. (Source: `GATE_CATALOG.json` lines 115–124; `01260207201000000191_transition_vectors.yaml` lines 72–84.)
- Whether “dir_id” is minted numeric or derived string; current gate vs generator conflicts show both are in use. (Source: `GATE_CATALOG.json` lines 60–66; `DOC-SCRIPT-0991__generate_id_registry.py` lines 43–54.)

Third, **make tooling consistent and enforceable**:
- Update `sync_doc_id_registry.py` to operate on the same list key the validator uses (recommended: `docs`, because both validator and cross-sync already assume it). (Source: `DOC-CORE-UTI-TOOLS-VALIDATE-REGISTRY-823__validate_registry.py` lines 75–83; `DOC-SCRIPT-UTI-VALIDATE-CROSS-SYNC-001__validate_cross_registry_sync.py` lines 106–112.)
- Fix the ID registry unit tests to match the actual `IdRegistry` behavior or replace the `IdRegistry` implementation with the API expected by tests—don’t keep both. (Source: `DOC-TEST-UNIT-TEST-ID-REGISTRY-641__test_id_registry.py` lines 60–66; `DOC-CORE-SSOT-SYS-TOOLS-ID-REGISTRY-1105__id_registry.py` lines 85–90.)

Fourth, **align governance semantics with code**. If patch-only mutation is a hard requirement, then any registry writer must emit patches and apply them atomically with locking; a plain `json.dump` rewrite violates the governance contract. (Source: `WRITE_POLICY_IDPKG.yaml` lines 24–44; `DOC-CORE-SSOT-SYS-TOOLS-ID-REGISTRY-1105__id_registry.py` lines 57–63.)

Fifth, **kill hard-coded paths** in production-facing scripts. Start with `P_RENAME_REMOVE_DOC_TOKEN.py`: move root paths and output dirs into CLI args and/or the path registry approach specified in the path indirection doc. (Source: `P_RENAME_REMOVE_DOC_TOKEN.py` lines 652–660; `01260207201000000181_PATH ABSTRACTION & INDIRECTION LAYER (1).md` lines 29–34.)