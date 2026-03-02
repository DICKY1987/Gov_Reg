# Automation Descriptor Subsystem

> **⚠️ DEPRECATED REFERENCE DOCUMENT**  
> **Status:** Legacy export from ChatGPT conversation (2026-01-22/23)  
> **Last Updated:** 2026-01-23 (marked deprecated)  
> **Superseded by:** 
> - `Automation_Descriptor_Phase_Plan.md` v1.3 (frozen contracts + build order)
> - `Automation_Descriptor_Deliverables_Specification.md` v1.1 (requirements + final spec)
>
> **Authority Hierarchy:** Per Phase Plan `<spec_authority_hierarchy>`, this document is **Tier 3** (deprecated legacy/reference). Where conflicts exist, **Tier 1 and 2 documents win**.
>
> **Known Conflicts Resolved in Frozen Contracts:**
> 1. **Registry File:** This doc uses `FILE_REGISTRY_v2.json` → **Correct:** `registry/UNIFIED_SSOT_REGISTRY.json`
> 2. **Event Enum:** This doc uses `FILE_CREATED` → **Correct:** `FILE_ADDED` (legacy mapped on intake)
> 3. **Timestamp Fields:** This doc uses `allocated_at`, `created_utc` → **Correct:** `first_seen_utc`, `updated_utc`
> 4. **Path Field:** This doc uses `current_path` → **Correct:** `relative_path` (POSIX, repo-relative)
> 5. **Queue Schema:** This doc uses `UNIQUE(path, status)` → **Correct:** `UNIQUE(path)` only
> 6. **Lock Ordering:** This doc incomplete → **Correct:** `path_lock → doc_lock → registry_lock` (total order)
> 7. **Patch Schema:** This doc missing `registry_hash` → **Correct:** `registry_hash` REQUIRED (CAS precondition)
>
> **Preservation Reason:** Historical context, design rationale, and implementation ideas. Use as reference only; do not implement literally.

**User:** bill reed (richgwilks@gmail.com)  
**Created:** 1/22/2026 15:41:08  
**Updated:** 1/23/2026 2:42:32  
**Exported:** 1/23/2026 4:05:42  
**Link:** [https://chatgpt.com/g/g-p-696e341154508191ba4eb1f9eac07bfe-directory-management-system/c/6972993f-cd6c-832d-abd7-f9db863412f9](https://chatgpt.com/g/g-p-696e341154508191ba4eb1f9eac07bfe-directory-management-system/c/6972993f-cd6c-832d-abd7-f9db863412f9)  

## Response:
Thought for 4m 18s

Stopped talking to connector

Thought for 1m 13s

These new files form a single, coherent “**Automation Descriptor subsystem**” that sits next to (and is meant to feed) your **registry-as-SSOT** and **watcher/plugin** architecture.

1) What this subsystem is trying to do (end-to-end)
---------------------------------------------------

**Goal:** make every automation script self-describing in a _standard structure_, and then **auto-extract** as much of that structure as possible so the remaining gaps are explicit (“manual fields needed”).

**Pipeline (intended):**

1.  Each automation script carries a small **declared metadata block** (authoritative, human-provided).
2.  An **AST parser** reads the script without executing it.
3.  An **extractor** infers additional facts (imports/dependencies, env vars, CLI args, file operations, etc.).
4.  A **CLI** walks the repo and emits a per-file descriptor artifact (e.g., `.automation_descriptor.json`).
5.  Your **File Registry v2** can then reference these descriptors and/or ingest their fields into registry columns.

This lines up with the “plugins are different events + centralized user/program communication” watcher direction you’ve been working toward: the watcher can trigger descriptor regeneration on file change; the registry becomes the queryable SSOT.

watcher subsystem

2026012201113004\_FILE\_REGISTRY\_…

* * *

2) How each file fits (and how they connect)
--------------------------------------------

### A) The “parser layer” (shared utility)

*   **`DOC-SCRIPT-0996__python_ast_parser.py`**: core AST parsing utility (returns structured parse results, timing, etc.). This is the foundation the extractor relies on to safely analyze Python files.
    DOC-SCRIPT-0996\_\_python\_ast\_par…
*   **`DOC-SCRIPT-1272__python_ast_parser.py`**: a **shim/re-export** wrapper around the parser (doc-id based). This fits your larger “stable identifiers / doc-id addressing” approach: code can import a stable doc-id wrapper instead of a moving filename/path.
    DOC-SCRIPT-1272\_\_python\_ast\_par…

### B) The “automation descriptor” contract + tooling

These are the pieces that define and generate automation descriptors:

*   **`REQUIRED DECLARATIVE METADATA (authoritative).py`**: establishes what _must_ be declared by humans as authoritative metadata (the part inference can’t reliably replace).
*   **`AUTOMATION_FILE_DESCRIPTOR.yml`**: the **shape/sections** of a full descriptor (identity/purpose/triggers/inputs/outputs/etc.). This is your canonical template/spec for the descriptor artifact.
*   **`automation_descriptor_extractor.py`**: the main implementation that merges:
    *   “declared authoritative metadata” +
    *   “inferred AST facts”  
        into one descriptor object, and produces a “manual fields needed” list for what couldn’t be derived.
*   **`describe_automations_cli.py`**: a wrapper that scans a directory/repo and writes out descriptor artifacts for every automation file (batch mode).

### C) The “older/parallel implementation”

*   **`descriptor_manual_fields_needed.py`**: overlaps conceptually with the extractor+CLI above (it’s the “flag what must be filled manually” idea). In practice, it looks like a predecessor or alternate approach that you should either:
    *   retire, or
    *   fold into the newer extractor as a compatibility path,  
        otherwise you’ll have two competing definitions of “what’s required vs derivable.”

### D) Tests (validation gates)

*   **`DOC-TEST-0639__test_python_ast_parser.py`**: tests the parser layer.
*   **`DOC-TEST-0632__test_copilot_parser.py`**: tests a different parser (copilot/log intent parsing). It’s adjacent: it supports “process traceability / intent extraction,” not the automation descriptor pipeline directly.

* * *

3) Where this plugs into the rest of your project knowledge
-----------------------------------------------------------

### A) File Registry v2 is the natural SSOT anchor

Your **`2026012201113004_FILE_REGISTRY_v2.json`** is already positioned as a SSOT registry for file entities (with record structure and per-file metadata). That makes it the authoritative place to:

*   link each automation file → its generated descriptor artifact
*   store derived facts (or hashes) so watchers can decide if regeneration is needed
    2026012201113004\_FILE\_REGISTRY\_…

### B) Watcher subsystem becomes the execution engine

Your watcher/plugin concept is the runtime “automation bus” that can:

*   detect changed automation files
*   trigger the descriptor extractor/CLI
*   update the registry (or emit a patch) as a deterministic downstream artifact
    watcher subsystem

### C) Doc-ID wrappers match your deterministic ID strategy

The **`DOC-SCRIPT-1272` shim** is a direct bridge to your “doc-id stable reference” model: you can keep internal imports stable even as physical filenames evolve, while still preserving doc-id traceability.

DOC-SCRIPT-1272\_\_python\_ast\_par…

* * *

4) The “tell it like it is” assessment
--------------------------------------

*   This is **not** just “some scripts.” It’s the start of a **descriptor-driven inventory system** for automations: a prerequisite for making “done” checkable and for populating registry columns from real evidence instead of memory.
*   Right now, the missing link (architecturally) is **registry integration**: the CLI can generate artifacts, but you still need a deterministic rule for:
    *   where descriptor artifacts live,
    *   how they’re named,
    *   how File Registry v2 references them,
    *   and what fields are promoted into registry columns vs left in sidecar descriptors.

If you implement that link, this subsystem becomes a first-class part of your “registry-as-SSOT + deterministic derived artifacts” build pipeline.

## Response:
Thought for 1m 46s

Understood: treat **all `.py` scripts** as first-class “describable” entities, and populate **Python-specific registry columns** from parser output.

Below are the real options you need to choose from, plus a recommended default that stays deterministic and scales.

* * *

1) Where descriptor artifacts live
----------------------------------

### Option A — Co-located sidecar next to each `.py`

**Example**

*   `0123456789012345_mytool.py`
*   `0123456789012345_mytool.py.descriptor.json`

**Pros**

*   Moves with the file.
*   Easy for humans to find.

**Cons**

*   Directory clutter + Git noise.
*   Watcher recursion issues (sidecar creation triggers more events unless excluded).
*   Harder to enforce “derived artifacts are tool-owned” when they live beside source.

* * *

### Option B — Central derived-artifacts directory (recommended)

**Example**

*   Source: `src/tools/0123456789012345_mytool.py`
*   Descriptor: `.dms/artifacts/python_descriptor/0123456789012345.json`

**Pros**

*   Clean source tree.
*   Easy ignore rules.
*   Deterministic naming keyed by `doc_id` (path changes don’t break identity).
*   Works best with “registry-as-SSOT + deterministic derived artifacts.”

**Cons**

*   Humans don’t “see it” next to the file (but registry points to it).

* * *

### Option C — Embedded inside File Registry as a nested blob

**Example**

*   `files[n].python_descriptor = {...big object...}`

**Pros**

*   Single file to query.

**Cons**

*   Registry bloat, merge/patch noise, harder diffs, slower operations.
*   Encourages mixing SSOT rows with large derived payloads.

**Pick:** Option B unless you have a hard requirement that descriptors must travel with sources.

* * *

2) How they’re named
--------------------

If you use Option B, naming can be fully formulaic (best) or stored.

### B1 — Pure formula (recommended)

Descriptor path is derived from `doc_id` + descriptor\_kind + schema\_version:

*   `descriptor_kind = python_descriptor`
*   `schema_version = 1` (or semver)
*   `path = .dms/artifacts/python_descriptor/{doc_id}.v{schema_version}.json`

No need to store the path in the registry; it can be computed.

### B2 — Store a pointer in the registry

Registry stores `descriptor_ref = ".dms/artifacts/python_descriptor/....json"`.

This is simpler to implement initially, but you’ve now got a path field that can drift.

**Pick:** B1 if you’re serious about deterministic “Excel formula” style derivations.

* * *

3) How File Registry v2 references them
---------------------------------------

You have three clean reference styles:

### Ref 1 — Computed reference (recommended)

Registry stores only:

*   `py_desc_schema_version`
*   `py_desc_status`
*   `py_desc_source_hash` (hash of `.py` at parse time)

Descriptor location is computed by formula (Section 2 / B1).

### Ref 2 — Explicit pointer field

Registry stores `py_desc_path`.

### Ref 3 — Separate “artifact registry”

File registry points to an `artifact_id`; artifact registry maps artifact\_id → path + metadata.  
This is more enterprise-y and more work; use only if you expect many artifact types per file.

**Pick:** Ref 1.

* * *

4) What gets promoted into registry columns vs stays in sidecar
---------------------------------------------------------------

Rule of thumb: **promote what you need to filter/sort/route**, leave everything else in sidecar.

### Promote into registry (good candidates)

**Identity / routing**

*   `is_python` (bool)
*   `py_module_name` (string, derived from path/package rules you define)
*   `py_has_main_guard` (`if __name__ == "__main__"`)

**Behavior classification**

*   `py_is_cli` (bool)
*   `py_cli_framework` (enum: argparse/click/typer/fire/none/unknown)
*   `py_entrypoints` (small list or count; if list, cap length)

**Dependency summary (keep it small)**

*   `py_imports_stdlib_count`
*   `py_imports_third_party_count`
*   `py_imports_local_count`
*   optional: `py_imports_third_party_top` (top N, capped)

**Parse provenance**

*   `py_parse_status` (ok/failed)
*   `py_parse_error_code` (if failed)
*   `py_parse_tool_version`
*   `py_parse_utc`
*   `py_source_sha256` (or whatever hash you standardize on)

### Keep in sidecar descriptor

*   Full import lists
*   Function/class inventories
*   Call graph hints
*   File I/O patterns
*   Env var usage
*   Subprocess usage
*   AST “findings” list with line numbers
*   Anything large / verbose / unstable

This prevents the registry from turning into a giant semi-structured dump.

* * *

5) Process: when a new file enters the registry, gets an ID, and gets parsed
----------------------------------------------------------------------------

You want two cooperating mechanisms:

*   **Watcher** for immediate correctness (event-driven)
*   **Scanner** for reconciliation (periodic/CI)

### Deterministic lifecycle for a new file

#### Step 0 — File appears

Event: CREATE or “first seen” during a scan.

#### Step 1 — Governance decision

Decide if the file is governed (in-scope path, not excluded patterns).

If not governed:

*   registry row can still exist, but `status=unmanaged` (or equivalent) and no ID enforcement.

#### Step 2 — ID allocation moment (recommended: immediately on first detection)

If governed and filename lacks valid 16-digit prefix:

*   allocate a `doc_id` immediately
*   rename atomically to `{doc_id}_{original_name}.py` (or your filename rules)
*   write/update registry row with:
    *   `doc_id`, `relative_path`, `allocated_at`, `status=active`

This is the cleanest rule: **a governed file gets its ID at first contact** (watcher or scan).

#### Step 3 — Parse moment (recommended: immediately after ID assignment OR on first stable write)

You have two practical timing choices:

**3A (simple): parse immediately after rename**

*   Good for most scripts.

**3B (robust): debounce**

*   Wait until file stops changing for N ms (e.g., 300–1000ms) or until the editor closes.
*   Prevents parsing partial writes.

After parse:

*   write descriptor artifact (`.dms/artifacts/python_descriptor/{doc_id}.v1.json`)
*   promote summary columns into registry
*   store `py_source_sha256` = hash of source used for parse

#### Step 4 — Update handling (MODIFY)

On MODIFY:

*   compute new source hash
*   if hash unchanged: skip
*   else re-parse and refresh:
    *   descriptor artifact (overwrite or version; your call)
    *   registry parse columns
    *   `updated_utc`

#### Step 5 — Reconciliation scan (daily/CI)

Scanner walks the tree and ensures:

*   every governed file has a registry row
*   every `.py` row has parse outputs consistent with current hash
*   drift repairs are applied deterministically (or quarantined)

* * *

6) Recommended default decision set (minimum ambiguity)
-------------------------------------------------------

1.  **Descriptors live centrally**: `.dms/artifacts/python_descriptor/`
2.  **Name is formulaic**: `{doc_id}.v{schema_version}.json`
3.  **Registry reference is computed** (store schema version + source hash; don’t store path)
4.  **Promote only summary/routing/provenance fields**; keep full details in sidecar
5.  **ID allocated at first detection for governed files** (watcher first; scanner as fallback)
6.  **Parser runs after debounce** and updates both descriptor + registry columns

If you want, I can express these as a single “decision contract” (tight bullet rules + derivation formulas) so it becomes enforceable by both watcher and scanner with zero interpretation.

## Response:
Make it real by turning it into a **transactional, queued, idempotent pipeline** with a strict order, explicit states, debounce, and rollback.

Core invariants
---------------

1.  **Registry is the SSOT for identity and current facts** (one row per file entity).
2.  **ID assignment happens exactly once** per governed file and is atomic with rename (or with a stable alias map if rename is delayed).
3.  **Parsers never “write directly.”** They emit a descriptor artifact + a small “promotion” payload; a single registry-writer applies updates.
4.  **Watcher is not the source of truth.** It is a trigger. A periodic scanner reconciles drift.

* * *

The real process (formalized)
-----------------------------

### Stage 0 — Event ingestion (Watcher)

**Watcher responsibility:** detect filesystem events and enqueue work items.

*   On CREATE/MOVE/MODIFY: enqueue `{event_type, path, timestamp}` into a **work queue**.
*   Ignore anything under tool-owned paths (e.g., `.dms/`, `artifacts/`, `.git/`, `__pycache__/`) to prevent recursion.
*   Use **debounce** per path (e.g., “no changes for 750ms”) before the file is considered stable.

**Output:** `WorkItem(path, reason, stable_at)`

* * *

### Stage 1 — Stabilize and classify (Coordinator)

A coordinator pops stable items and runs a cheap classifier:

*   Determine `governed?` (in-scope directory, not excluded patterns).
*   Determine `file_kind` (python, markdown, etc.).
*   Determine if the file already has a valid `doc_id`.

**Output:** a “Plan” for that file: `Plan(governed, needs_id, parse_python, other_plugins…)`

* * *

### Stage 2 — Acquire a per-file lock (Coordinator)

Before any writes:

*   Acquire a **lock keyed by canonical path** (or temp file identity) so you don’t process the same file concurrently.
*   If lock is held, coalesce events and retry later.

**This is what makes “multiple files added” safe.**

* * *

### Stage 3 — ID assignment + registry row creation (Transaction 1)

If governed:

1.  **Allocate ID** (sequence allocator).
2.  **Rename atomically** to include the ID (recommended):  
    `_{doc_id}_{original_name}.py` (or your naming rule).
3.  Create/ensure a registry row exists with:
    *   `doc_id`
    *   `current_path`
    *   `record_kind=file`
    *   `status=registered`
    *   `source_hash` (optional here; can wait until parse)
    *   `created_utc`, `id_assigned_utc`
4.  Write an audit log entry for this transaction.

If rename fails (locked by editor, permissions, collision):

*   Put file into `status=quarantine` or `status=pending_id`
*   Record error + retry policy (backoff).

**Important ordering:** ID + row must exist _before_ parser-derived fields, because all downstream artifacts want a stable key (`doc_id`).

* * *

### Stage 4 — Content analysis (Transaction 2: derived artifacts)

Run plugins based on `file_kind`. For Python files:

1.  Compute `py_source_sha256` of the stable file contents.
2.  Run AST parser/extractor (no execution).
3.  Emit **descriptor artifact** to computed location:
    *   `.dms/artifacts/python_descriptor/{doc_id}.v1.json`
4.  Emit a compact **promotion payload** (the handful of fields you decided belong in registry columns).

If parse fails:

*   Still write a descriptor stub with error info (status, exception type, message truncated).
*   Promote `py_parse_status=failed` and `py_parse_error_code`.

* * *

### Stage 5 — Apply promotions to registry (single writer)

A single “registry writer” applies updates:

*   Update the row by `doc_id` with:
    *   parse status/provenance fields
    *   selected promoted python fields
    *   `py_desc_schema_version`
    *   `py_desc_hash` (hash of descriptor artifact)
    *   `py_source_sha256`

This is done as an atomic patch operation (or atomic rewrite) so the registry never becomes partially updated.

* * *

### Stage 6 — Post-processing + downstream generators (optional)

After registry is updated, run deterministic generators that depend on registry state:

*   rebuild module indexes
*   rebuild directory manifests
*   rebuild cross-reference maps
*   anything else that is “formula-like” from registry columns

**Do not run these before Stage 5**, otherwise they will see stale registry data.

* * *

State machine for each file (what makes it enforceable)
-------------------------------------------------------

A governed file’s registry row moves through states:

1.  `discovered` (optional)
2.  `registered` (row exists, id assigned, path normalized)
3.  `analyzing` (plugins running)
4.  `enriched` (descriptor exists + promoted fields applied)
5.  `error` (with `error_stage`, retry policy)
6.  `quarantine` (manual attention required)

State changes are written to the audit log with timestamps and tool versions.

* * *

Handling “AI or user adds multiple files” correctly
---------------------------------------------------

### Coalesce + batch

*   The watcher enqueues each path.
*   Coordinator groups stable paths into a batch (e.g., up to 50) but still processes each file under a per-file lock.
*   After the batch completes, run downstream generators **once** (not per file).

This prevents N rebuilds for N new files.

* * *

Failure handling that prevents corrupt SSOT
-------------------------------------------

1.  **Two-phase approach**:
    *   Transaction 1: ID + row creation (must succeed to proceed).
    *   Transaction 2: analysis + artifact emission (can fail without breaking identity).
2.  **Never partially promote**:
    *   If plugin fails, only promote failure status + provenance, not partial data.
3.  **Retry rules**:
    *   transient errors (file locked) → retry with backoff
    *   permanent errors (syntax error) → mark `enriched` with `parse_failed` but not “error” unless you require syntactically valid python

* * *

Minimal “real” ordering (corrected vs brainstorm)
-------------------------------------------------

Your brainstorm had the right idea but slightly wrong ordering. The real order is:

1.  file appears
2.  watcher enqueues + debounces
3.  coordinator classifies + locks
4.  **assign ID + create registry row + rename**
5.  parse/analyze and write descriptor
6.  promote fields into registry
7.  run dependent generators once per batch

That’s the dependable version.

* * *

What you need to decide (small set, high leverage)
--------------------------------------------------

1.  **ID timing:** immediate on first stable detection (recommended) vs delayed until file is “final.”
2.  **Rename policy:** always rename to include ID vs keep name and store ID mapping (rename is simpler/deterministic).
3.  **Promotion set:** the exact python columns (keep small).
4.  **Derived artifact location:** central `.dms/artifacts/...` (recommended).
5.  **Error policy:** syntax errors treated as “valid but failed parse” vs “reject file.”

If you want this to be machine-enforceable, the next step is to write the above as a **Process Contract** with:

*   event types
*   required inputs/outputs per stage
*   state transitions
*   retry rules
*   deterministic path formulas for artifacts
*   registry patch schema for updates

## Response:
Thought for 34s

Production-ready end-to-end process breakdown
---------------------------------------------

This assumes three cooperating subsystems:

*   **Watcher Core** (event intake + debounce + queue + locks)
*   **Registry Authority** (single-writer SSOT updates + ID allocation)
*   **Parsers/Extractors** (read-only analysis → descriptor + promotion payload)

It also assumes a periodic **Reconciler Scan** exists to repair missed events and enforce policy.

* * *

A) Required files and directories (canonical vs generated vs runtime)
---------------------------------------------------------------------

### A1) Canonical (human-maintained; versioned)

These must exist for a production-ready system.

1.  **Registry (SSOT)**
    *   `FILE_REGISTRY.json` (your `2026012201113004_FILE_REGISTRY_v2.json` is the current v2 artifact; in production you’ll want a stable canonical path)
2.  **Registry schema / governance**
    *   `COLUMN_DICTIONARY.md` (or a machine-validated schema equivalent)
    *   `SCHEMA_AUTHORITY_POLICY.md`
    *   `SCOPE_AND_COUNTER_KEY_DECISION.md`
    *   `16_DIGIT_ID_BREAKDOWN.md`
    *   `SEQ_ALLOCATOR_SPEC.md`
3.  **Watcher configuration**
    *   `WATCHER_CONFIG.yml` (project-specific: watch roots, ignore rules, pipelines, caps, debounce settings)
    *   `PLUGIN_REGISTRY.yml` (declares enabled plugins and order)
4.  **Parser/extractor code (tooling)**
    *   `python_ast_parser.py` (your `DOC-SCRIPT-0996__python_ast_parser.py`)
    *   `python_ast_parser_shim.py` (your `DOC-SCRIPT-1272__python_ast_parser.py`, optional)
    *   `python_descriptor_extractor.py` (your `automation_descriptor_extractor.py`, but generalized to _all_ `.py`)
    *   `describe_python_cli.py` (your `describe_automations_cli.py`, generalized to `.py`)
5.  **Descriptor schema**
    *   `PYTHON_FILE_DESCRIPTOR.yml` (can be derived from your `AUTOMATION_FILE_DESCRIPTOR.yml` but broadened to “python script descriptor”)

* * *

### A2) Generated (tool-owned; deterministic; never hand-edited)

These are created/updated by automation.

1.  **Python descriptor artifacts**
    *   `.dms/artifacts/python_descriptor/{doc_id}.v{schema_version}.json`
2.  **Registry patches (optional but recommended for auditability)**
    *   `.dms/patches/registry/{utc_ts}__{work_item_id}__{doc_id}.json`
3.  **Derived indexes/manifests that depend on registry**
    *   `.dms/artifacts/index/module_index.json`
    *   `.dms/artifacts/index/process_index.json`
    *   etc.

* * *

### A3) Runtime (ephemeral; tool-owned)

These must exist at runtime; can be recreated.

1.  **Queue**
    *   `.dms/runtime/work_queue.sqlite`
2.  **Locks**
    *   `.dms/runtime/locks/registry.lock`
    *   `.dms/runtime/locks/path/{path_hash}.lock`
    *   `.dms/runtime/locks/doc/{doc_id}.lock`
3.  **Audit logs**
    *   `.dms/logs/actions.jsonl`
    *   `.dms/logs/errors.jsonl`
4.  **Quarantine**
    *   `.dms/quarantine/{reason}/{doc_id_or_temp_id}/...`

* * *

B) Full step list for “new file added” (all files created/modified)
-------------------------------------------------------------------

This is the “real” version of your brainstorm, made safe and deterministic.

### Step 1 — File appears (user or AI writes file)

*   **Modified/Created:** the new file in the watched tree
*   **No registry changes yet**

### Step 2 — Watcher captures event and enqueues work item

*   Event types: `FILE_CREATED` and usually follow-up `FILE_MODIFIED` (editors)
*   **Created/Modified:**
    *   `.dms/runtime/work_queue.sqlite` (new work item row)
    *   `.dms/logs/actions.jsonl` (enqueue record)

### Step 3 — Debounce + stability gate (coalesce events)

*   Wait until stable (`mtime/size unchanged` for configured window)
*   **Modified:**
    *   `.dms/runtime/work_queue.sqlite` (work item status: `STABLE_READY`)

### Step 4 — Classification and policy decision

*   Determine governed/unmanaged, file kind, ignore patterns, etc.
*   **Modified:**
    *   `.dms/runtime/work_queue.sqlite` (attach classification result)

### Step 5 — Acquire per-path lock

*   Prevent duplicate/concurrent processing
*   **Created/Modified:**
    *   `.dms/runtime/locks/path/{path_hash}.lock`

### Step 6 — Ensure registry row + assign doc\_id (if governed and missing)

**This is the critical ordering correction: ID and row exist before parsing.**

If file already has a valid ID: skip allocation; locate/confirm row.

If file has no ID and is governed:

1.  Allocate `doc_id` (sequence allocator)
2.  Atomically rename file to include `doc_id`
3.  Create/Update registry row with core identity fields
    *   **Modified/Created:**
    *   The file itself (rename)
    *   `FILE_REGISTRY.json` (new row or updated row)
    *   `.dms/logs/actions.jsonl` (ID assignment + rename + registry update)
    *   `.dms/runtime/locks/doc/{doc_id}.lock` (optional; recommended)

### Step 7 — Run parsers/extractors (Python only)

If extension is `.py` and governed:

1.  Hash source (`py_source_sha256`)
2.  Parse AST (no execution)
3.  Produce descriptor JSON
4.  Produce promotion payload (small set of registry columns)
    *   **Created/Modified:**
    *   `.dms/artifacts/python_descriptor/{doc_id}.v1.json`
    *   `.dms/logs/actions.jsonl` (parse result)

If parse fails:

*   still write a descriptor containing error/provenance
*   promotion payload includes `py_parse_status=failed` + error codes

### Step 8 — Apply promotions to registry (single writer)

*   Apply patch atomically to the registry row by `doc_id`
*   **Modified/Created:**
    *   `FILE_REGISTRY.json`
    *   (optional) `.dms/patches/registry/{utc_ts}__{work_item_id}__{doc_id}.json`
    *   `.dms/logs/actions.jsonl`

### Step 9 — Run downstream derived generators (batch-aware)

Only after registry is updated; ideally once per batch of files.

*   **Modified/Created:**
    *   `.dms/artifacts/index/*.json`
    *   `.dms/logs/actions.jsonl`

### Step 10 — Mark work item complete and release locks

*   **Modified/Deleted:**
    *   `.dms/runtime/work_queue.sqlite` (status `DONE`)
    *   remove lock files

* * *

C) Modify/update flow (existing governed file)
----------------------------------------------

Same pipeline, but:

*   no new ID allocation
*   parser runs only if `source_hash changed`
*   promotions update existing fields
*   downstream generators run once per batch

* * *

D) Reconciliation scan (production requirement)
-----------------------------------------------

Watcher misses events; editors do atomic saves; system restarts happen. A periodic scan must:

*   discover governed files missing from registry
*   detect renamed/moved paths and fix registry
*   detect stale descriptors vs current source hash and re-run parsers
*   enforce policy (quarantine invalid)

Artifacts modified are the same as the watcher flow (registry, descriptors, indexes, logs).

* * *

Process Contract (formal)
=========================

Below is a contract suitable to drive implementation and validation.

```yaml
process_contract:
  contract_id: PC_FILE_INGEST_ENRICH_V1
  scope: project
  ssot:
    registry_path: FILE_REGISTRY.json
    registry_schema_version: "2.x"
  tool_owned_roots:
    - .dms/
  ignore_patterns:
    - "**/.git/**"
    - "**/__pycache__/**"
    - "**/*.pyc"
    - "**/.dms/**"

  event_types:
    - FILE_CREATED
    - FILE_MODIFIED
    - FILE_MOVED
    - FILE_DELETED
    - RECONCILE_TICK

  state_machine:
    file_row_states:
      - discovered        # optional pre-row state (if you store discoveries)
      - registered        # row exists; doc_id assigned; path normalized
      - analyzing         # parsers/plugins in progress
      - enriched          # descriptor exists + promotions applied
      - parse_failed      # descriptor exists with error; promotions reflect failure
      - quarantine        # policy violation or repeated failure
      - unmanaged         # out of scope or explicitly ignored
      - deleted           # tombstone state (optional)
    work_item_states:
      - queued
      - stable_pending
      - stable_ready
      - running
      - done
      - retry_wait
      - dead_letter

  deterministic_artifact_formulas:
    python_descriptor:
      schema_version: 1
      path: ".dms/artifacts/python_descriptor/{doc_id}.v{schema_version}.json"
    registry_patch:
      path: ".dms/patches/registry/{utc_ts}__{work_item_id}__{doc_id}.json"
    indexes_root:
      path: ".dms/artifacts/index/"

  retry_rules:
    general:
      max_attempts: 8
      backoff_seconds: [5, 15, 45, 120, 300, 900, 1800, 3600]
    retryable_errors:
      - FILE_LOCKED
      - PERMISSION_DENIED_TRANSIENT
      - TEMP_IO_ERROR
      - REGISTRY_LOCK_BUSY
    non_retryable_errors:
      - POLICY_FORBIDDEN_PATH
      - NAME_COLLISION_UNRESOLVED
      - INVALID_ID_FORMAT_AFTER_REPAIR
    parse_errors:
      policy:
        # Syntax errors are not necessarily quarantine; treat as parse_failed unless policy says otherwise.
        syntax_error_state: parse_failed
        repeated_parse_failures_to_quarantine: 10

  stages:
    - stage_id: S1_EVENT_INTAKE
      triggers: [FILE_CREATED, FILE_MODIFIED, FILE_MOVED, FILE_DELETED]
      required_inputs:
        - fs_event(path, event_type, timestamp)
      outputs:
        - queue_work_item(work_item_id, path, event_type)
      files_created_or_modified:
        - ".dms/runtime/work_queue.sqlite"
        - ".dms/logs/actions.jsonl"

    - stage_id: S2_DEBOUNCE_STABILITY
      triggers: [queue_work_item]
      required_inputs:
        - work_item_id
        - policy(debounce_ms, stability_checks)
      outputs:
        - work_item.status=stable_ready
      files_created_or_modified:
        - ".dms/runtime/work_queue.sqlite"

    - stage_id: S3_CLASSIFY_PLAN
      triggers: [work_item.status=stable_ready, RECONCILE_TICK]
      required_inputs:
        - path
        - policy(scope_roots, ignore_patterns)
      outputs:
        - plan(governed?, file_kind, needs_id?, plugins[])
      files_created_or_modified:
        - ".dms/runtime/work_queue.sqlite"

    - stage_id: S4_LOCK_ACQUIRE
      triggers: [plan_ready]
      required_inputs:
        - path
      outputs:
        - lock_acquired(path_hash)
      files_created_or_modified:
        - ".dms/runtime/locks/path/{path_hash}.lock"

    - stage_id: S5_ID_AND_ROW_UPSERT
      triggers: [plan.governed=true]
      required_inputs:
        - path
        - registry_lock
        - id_allocator
      outputs:
        - doc_id assigned (if missing)
        - path renamed (if missing doc_id)
        - registry row upserted (core identity fields)
        - file_row_state=registered
      files_created_or_modified:
        - "{watched_tree}/{doc_id}_*.{ext}"   # rename if needed
        - "FILE_REGISTRY.json"
        - ".dms/logs/actions.jsonl"
        - ".dms/runtime/locks/doc/{doc_id}.lock"

    - stage_id: S6_ANALYZE_PYTHON
      triggers: [file_kind=python, file_row_state=registered]
      required_inputs:
        - "{watched_tree}/{doc_id}_*.py"
        - python_ast_parser
        - python_descriptor_schema(v1)
      outputs:
        - python descriptor artifact
        - promotion_payload (small, typed)
        - file_row_state=analyzing -> enriched|parse_failed
      files_created_or_modified:
        - ".dms/artifacts/python_descriptor/{doc_id}.v1.json"
        - ".dms/logs/actions.jsonl"

    - stage_id: S7_APPLY_PROMOTIONS
      triggers: [promotion_payload_ready]
      required_inputs:
        - registry_lock
        - doc_id
        - promotion_payload
      outputs:
        - registry patched atomically
        - file_row_state=enriched|parse_failed
      files_created_or_modified:
        - "FILE_REGISTRY.json"
        - ".dms/patches/registry/{utc_ts}__{work_item_id}__{doc_id}.json"
        - ".dms/logs/actions.jsonl"

    - stage_id: S8_DERIVED_GENERATORS
      triggers: [registry_changed]
      required_inputs:
        - FILE_REGISTRY.json
      outputs:
        - derived indexes/manifests updated deterministically
      files_created_or_modified:
        - ".dms/artifacts/index/*.json"
        - ".dms/logs/actions.jsonl"

    - stage_id: S9_FINALIZE
      triggers: [stages_complete]
      required_inputs:
        - work_item_id
      outputs:
        - work_item.status=done
        - locks released
      files_created_or_modified:
        - ".dms/runtime/work_queue.sqlite"
      files_deleted:
        - ".dms/runtime/locks/path/{path_hash}.lock"
        - ".dms/runtime/locks/doc/{doc_id}.lock"
```

* * *

Registry patch schema (update contract)
=======================================

This is the “single writer” rule formalized: all subsystem updates occur as validated patches.

```json
{
  "patch_schema_id": "REGISTRY_PATCH_V1",
  "patch_kind": "file_row_update",
  "required": ["registry_version", "doc_id", "ops", "actor", "utc_ts", "work_item_id"],
  "properties": {
    "registry_version": { "type": "string" },
    "doc_id": { "type": "string", "pattern": "^[0-9]{16}$" },
    "work_item_id": { "type": "string" },
    "utc_ts": { "type": "string" },
    "actor": {
      "type": "object",
      "required": ["tool", "tool_version"],
      "properties": {
        "tool": { "type": "string" },
        "tool_version": { "type": "string" }
      }
    },
    "ops": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["op", "path"],
        "properties": {
          "op": { "type": "string", "enum": ["set", "add", "remove"] },
          "path": { "type": "string" },
          "value": {}
        }
      }
    }
  },
  "constraints": [
    "All ops MUST target the file row identified by doc_id (no cross-row edits).",
    "set/add MUST be type-validated against column dictionary for promoted fields.",
    "remove MUST NOT delete core identity fields (doc_id, relative_path, status, allocated_at).",
    "Patch application MUST be atomic: write-temp-then-replace for FILE_REGISTRY.json.",
    "If source hash unchanged, py promotions MUST NOT change (idempotent)."
  ]
}
```

* * *

What this delivers as “production-ready”
----------------------------------------

1.  Deterministic ordering (ID → row → parse → promote → generate).
2.  No race conditions (queue + locks).
3.  No partial writes (atomic patching).
4.  Infinite-loop protection (ignore tool-owned roots; debounce).
5.  Drift resistance (reconcile scan).
6.  Auditable, replayable evidence (JSONL + optional patch artifacts).

If you want the next concretization step without ambiguity: define the exact **Python promotion column set** (names + types). The rest of the contract already supports it.

## Response:
Thought for 1m 23s

According to a document from **2026-01-20**, the Unified SSOT Registry v2.1 Column Dictionary currently defines **80 columns** and already supports `array[string]`\-style columns (e.g., `tags`, `declared_dependencies`) and recognizes Python via `content_type` examples like `"application/python"`.

2026012015460001\_COLUMN\_DICTION…

2026012015460001\_COLUMN\_DICTION…

2026012015460001\_COLUMN\_DICTION…

2026012015460001\_COLUMN\_DICTION…

Below is the **exact “Python promotion column set”** I recommend adding (i.e., promoted into registry columns; everything else stays in a sidecar descriptor). This set is intentionally **small, stable, and high-value** for downstream deterministic generators (indexes, dependency graphs, watcher decisions), while leaving richer/volatile details in descriptors.

These should be added to `2026012015460001_COLUMN_DICTIONARY.md` as a new section (schema bump to v2.2+), numbered starting at **81**.

* * *

Applicability rule (for every column below)
-------------------------------------------

Populate **only when**:

*   `record_kind = "entity"` AND `entity_kind = "file"` AND (`extension = ".py"` OR `content_type = "application/python"`).
    2026012015460001\_COLUMN\_DICTION…
    2026012015460001\_COLUMN\_DICTION…

All other records: `null`.

* * *

Python Promotion Columns (proposed new columns 81–100)
------------------------------------------------------

### Parsing & provenance (tool-owned, deterministic)

**81\. `py_parse_status`**

*   **Type**: `string` (enum) or `null`
*   **Values**: `ok`, `syntax_error`, `encoding_error`, `missing_file`, `timeout`, `parser_error`
*   **Meaning**: last parse outcome for this file

**82\. `py_parsed_utc`**

*   **Type**: `string` (ISO 8601 datetime) or `null`
*   **Meaning**: when the parser last successfully _attempted_ parsing (success or failure)

**83\. `py_parser_id`**

*   **Type**: `string` or `null`
*   **Meaning**: stable identifier for parser implementation (e.g., `python_ast_parser_astroid`)

**84\. `py_parser_version`**

*   **Type**: `string` or `null`
*   **Meaning**: parser version used to produce the promoted values

**85\. `py_parse_error_count`**

*   **Type**: `integer` or `null`
*   **Meaning**: number of parse errors captured (0 when `py_parse_status=ok`)

**86\. `py_parse_error_first`**

*   **Type**: `string` or `null`
*   **Meaning**: first/most important error message (single-line; truncated to a fixed max length in tool)

* * *

### Identity & entry behavior (high leverage for “is this runnable / CLI / entrypoint?”)

**87\. `py_module_qualname`**

*   **Type**: `string` or `null`
*   **Meaning**: dotted module path derived from `relative_path` (package-aware)
    *   Example: `src/tools/build.py` → `src.tools.build` (rule depends on your chosen repo root mapping)

**88\. `py_is_package_init`**

*   **Type**: `boolean` or `null`
*   **Meaning**: `true` if filename is `__init__.py`

**89\. `py_has_main_guard`**

*   **Type**: `boolean` or `null`
*   **Meaning**: `true` if `if __name__ == "__main__":` is present

**90\. `py_entrypoint_symbol`**

*   **Type**: `string` or `null`
*   **Meaning**: the likely entry function name when detected (common: `main`, `cli`, etc.)

**91\. `py_cli_framework`**

*   **Type**: `string` (enum) or `null`
*   **Values**: `none`, `argparse`, `click`, `typer`, `fire`, `docopt`, `unknown`
*   **Meaning**: best-effort detection of CLI style (for automation classification)

* * *

### Dependency surface (needed for deterministic dependency graphs and “blast radius”)

Normalization rule for arrays below:

*   **unique**, **sorted**, **stable order** (lexicographic), **no empties**

**92\. `py_imports_local`**

*   **Type**: `array[string]` or `null`
*   **Meaning**: imports that resolve to _in-repo_ modules/packages (as dotted names)

**93\. `py_imports_external`**

*   **Type**: `array[string]` or `null`
*   **Meaning**: imports that appear to be third-party (top-level module names)

**94\. `py_imports_local_count`**

*   **Type**: `integer` or `null`

**95\. `py_imports_external_count`**

*   **Type**: `integer` or `null`

* * *

### Structure metrics (useful for categorization; cheap/stable to extract)

**96\. `py_function_count`**

*   **Type**: `integer` or `null`
*   **Meaning**: number of `def` at module scope (not methods)

**97\. `py_class_count`**

*   **Type**: `integer` or `null`
*   **Meaning**: number of `class` definitions at module scope

**98\. `py_docstring_1l`**

*   **Type**: `string` or `null`
*   **Meaning**: first line of module docstring (trimmed). This is a strong candidate to auto-fill `short_description`.

* * *

### Sidecar descriptor linkage (this answers “what stays in descriptors vs registry”)

Your extractor pattern explicitly treats declared metadata as authoritative and uses AST inference to fill gaps, producing “manual\_fields\_needed”.

automation\_descriptor\_extractor

**99\. `py_descriptor_path`**

*   **Type**: `string` or `null`
*   **Meaning**: deterministic relative path to the sidecar descriptor artifact for this file

**100\. `py_descriptor_sha256`**

*   **Type**: `string` or `null`
*   **Meaning**: SHA-256 of the descriptor contents (lets generators detect descriptor change without opening it)

* * *

Why this is the “promotion set” (and what stays in sidecar)
-----------------------------------------------------------

Promote only:

*   parse status + parser identity (debuggability / determinism),
*   entry/CLI signals (watcher + automation classification),
*   dependency surface (graphs / rebuild decisions),
*   stable structure metrics,
*   descriptor pointer + descriptor hash.

Keep in sidecar descriptors:

*   detailed inputs/outputs, SSOT reads/writes, derived artifacts, state keys, human purpose fields, etc. (these change more often and are richer than a single row should hold). The existing descriptor skeleton is already shaped for that kind of data.
    automation\_descriptor\_extractor

* * *

If you adopt this set, the next schema/doc work is straightforward: add a new “Python Promotion Columns” section to the column dictionary (and the JSON Schema), and treat these columns as **tool-owned** fields populated by the parser pipeline (not user-edited).

## Response:
Below is a consolidated inventory of the files and directories discussed across our conversation, grouped by their role in the system. For each item I note whether it already exists and will be **modified**, or is a **new file** that must be created. Citations are provided for canonical documents that already exist (e.g., the registry column dictionary), illustrating the source of some design decisions.

### A. Canonical / Human‑maintained files (must be kept in version control)

| File / Directory | Status | Purpose |
| --- | --- | --- |
| **`FILE_REGISTRY.json` (currently `2026012201113004_FILE_REGISTRY_v2.json`)** | _Modify or supersede_ | The unified SSOT for all file‑based entities. Each row stores identity (`doc_id`), status, timestamps, and promoted parser columns. The watcher/parsers update this file atomically. |
| **`2026012015460001_COLUMN_DICTIONARY.md`** | _Modify_ | Column dictionary for the registry (80 columns today). Must be updated (v2.2+) to add the Python promotion columns (e.g. `py_parse_status`, `py_module_qualname`, `py_imports_local`, etc.) and their descriptions. The existing dictionary illustrates how columns are documented—including type definitions like `array[string]`【177:2†2026012015460001\_COLUMN\_DICTIONARY.md†L17-L27】 and examples of content‑type usage (`"application/python"` for Python files)【177:2†2026012015460001\_COLUMN\_DICTIONARY.md†L17-L27】. |
| **`PYTHON_FILE_DESCRIPTOR.yml`** (based off `AUTOMATION_FILE_DESCRIPTOR.yml`) | _New_ | Schema/template describing a Python file’s descriptor: identity, purpose, imports, I/O, environment variables, etc. Used by the extractor to build deterministic descriptors. |
| **`REQUIRED_DECLARATIVE_METADATA.py`** | _Existing_ | Defines which metadata fields must be provided manually by developers (authoritative fields). Used by the extractor to know what cannot be auto‑inferred. |
| **`SCHEMA_AUTHORITY_POLICY.md`, `SCOPE_AND_COUNTER_KEY_DECISION.md`, `16_DIGIT_ID_BREAKDOWN.md`, `SEQ_ALLOCATOR_SPEC.md`** | _New or update_ | Governance documents for ID assignment and registry policies: detail how 16‑digit `doc_id`s are constructed, sequence allocator behaviour, and what is considered in‑scope vs. unmanaged. |
| **`WATCHER_CONFIG.yml`** | _New_ | Configuration for the file watcher: watched directories, ignore patterns (e.g., `.git/`, `__pycache__/`), debounce timing, and path to queue database. |
| **`PLUGIN_REGISTRY.yml`** | _New_ | Declares available parser/extractor plugins and their order. Ensures that the watcher knows which plugins (e.g. Python AST parser) to invoke for each file kind. |

### B. Parser and extractor tooling

| File | Status | Purpose |
| --- | --- | --- |
| **`python_ast_parser.py`** (`DOC‑SCRIPT‑0996__python_ast_parser.py`) | _Existing_ | Core parser that reads a Python file’s AST and returns structured information (imports, functions, classes, etc.). |
| **`python_ast_parser_shim.py`** (`DOC‑SCRIPT‑1272__python_ast_parser.py`) | _Existing_ | Thin wrapper around the AST parser that exposes a stable doc‑ID‑based import path. |
| **`python_descriptor_extractor.py`** (`automation_descriptor_extractor.py`) | _Modify_ | Combines declared metadata with AST‑inferred facts to produce the descriptor and a small “promotion payload” for registry columns. Should be generalised for all `.py` scripts. |
| **`describe_python_cli.py`** (`describe_automations_cli.py`) | _Modify_ | CLI that scans directories and emits descriptors via the extractor; writes descriptor files into `.dms/artifacts/python_descriptor/`. Needs to be broadened from “automations” to all Python scripts. |
| **`descriptor_manual_fields_needed.py`** | _Modify or retire_ | An older implementation for identifying which fields still require manual entry. Should either be retired or folded into the current extractor’s logic. |
| **Tests** (`DOC‑TEST‑0632__test_copilot_parser.py`, `DOC‑TEST‑0639__test_python_ast_parser.py`) | _Existing_ | Provide automated validation of the AST parser and related inference logic. Must be updated to reflect any schema changes (e.g. Python promotion columns). |

### C. Generated artifacts (tool‑owned; never hand‑edited)

| File / Directory | Status | Purpose |
| --- | --- | --- |
| **`.dms/artifacts/python_descriptor/{doc_id}.v1.json`** | _New_ | For each governed Python file, a JSON descriptor generated by the extractor (schema versioned). |
| **`.dms/patches/registry/{utc_ts}__{work_item_id}__{doc_id}.json`** | _New_ | Optional, but recommended: logs of registry updates applied for each work item; useful for audits and rollback. |
| **`.dms/artifacts/index/…`** | _New_ | Derived indexes—such as module or dependency graphs—built deterministically from the registry’s promoted columns. |
| **`.dms/runtime/work_queue.sqlite`** | _New_ | SQLite database used by the watcher to queue filesystem events and track their state. |
| **`.dms/runtime/locks/path/{path_hash}.lock`** & **`.dms/runtime/locks/doc/{doc_id}.lock`** | _New_ | Per‑file locks that ensure only one process manipulates a path or doc‑ID at a time. |
| **`.dms/logs/actions.jsonl`** & **`.dms/logs/errors.jsonl`** | _New_ | Append‑only logs of every action (enqueue, parse, update) and errors; support debugging and auditing. |
| **`.dms/quarantine/`** | _New_ | Directory where problematic files are placed when automatic processing fails repeatedly or violates policy. |

### D. Runtime code / infrastructure

| File / Component | Status | Purpose |
| --- | --- | --- |
| **Watcher daemon/service** (source file) | _New_ | Runs continuously, watches for filesystem events, enqueues work items, performs debouncing, classification, ID assignment and calls the extractor. |
| **Coordinator / scheduler** | _New_ | Picks up work items, manages locks, invokes parsers, writes descriptors and promotion payloads, applies registry patches, and kicks off downstream generators. This component also implements retry logic and back‑off policies. |
| **Reconciler scan script** | _New_ | Periodically scans the directory tree and registry to catch missed events, detect drift, and re‑generate descriptors when hashes differ. |

### E. Column dictionary updates

To support Python promotion columns, the column dictionary must be extended (columns 81–100). These additions capture parser provenance (status, parse time, parser version), identity/entry‑point markers (`py_module_qualname`, `py_has_main_guard`, `py_cli_framework`), dependency summaries (`py_imports_local`, `py_imports_external` and counts), structure metrics (`py_function_count`, `py_class_count`, `py_docstring_1l`), and descriptor linkage (`py_descriptor_path`, `py_descriptor_sha256`). Existing array column examples like `tags`【177:2†2026012015460001\_COLUMN\_DICTIONARY.md†L17-L27】 and content‑type examples such as `application/python`【177:2†2026012015460001\_COLUMN\_DICTIONARY.md†L17-L27】 should be used as templates for documenting these new columns.

* * *

**Summary**

In total, the production‑ready system introduces or modifies: (1) core specifications and governance docs; (2) parser/extractor code; (3) watcher configuration and runtime infrastructure; (4) the SSOT registry and column dictionary; and (5) a set of tool‑generated artifacts in the `.dms` directory. These elements together enable the watcher to detect new Python files, assign IDs, generate descriptors, promote important fields into registry columns, and maintain a deterministic, auditable single source of truth.

## Response:
I've created a comprehensive, machine‑readable set of instructions for your CLI application. The instructions cover initialization, configuration, event handling, ID assignment, parsing, descriptor generation, registry updates, error handling, reconciliation and schema maintenance. They reference all relevant files by name and integrate the Python promotion columns into the process.

You can review the instructions here:

CLI Application Instructions for Directory Management System (DMS)
==================================================================

These instructions define the end‑to‑end behaviour required for the **Directory Management System (DMS)** CLI. The CLI is responsible for watching a project directory, assigning stable identities to governed files, generating descriptor artifacts for Python files, and updating the unified single source of truth (SSOT) registry. All file names in these steps refer to the actual files in your project.

1\. Initialization and Configuration
------------------------------------

1.  **Load core specifications and schemas**:
    *   Read `2026012012410001_SINGLE_UNIFIED_SSOT_REGISTRY_SPEC.md` to understand the high‑level registry specification and record lifecycle.
    *   Read `2026012015460001_COLUMN_DICTIONARY.md` (latest version) to obtain the column definitions; this document explains that arrays of strings are valid types【177:2†2026012015460001\_COLUMN\_DICTIONARY.md†L17-L27】 and shows how content types like `"application/python"` identify Python files【177:2†2026012015460001\_COLUMN\_DICTIONARY.md†L17-L27】.
    *   Load `2026012012110001_UNIFIED_SSOT_REGISTRY_ANALYSIS.md` and `registry-as-SSOT + deterministic derived artifacts.txt` for additional context on SSOT design and derived artifacts.
2.  **Load ID assignment and scope policies**:
    *   Read `16_DIGIT_ID_BREAKDOWN.md` to understand the structure of a 16‑digit `doc_id` and which segments encode scope, sequence counters, and other bits.
    *   Read `SEQ_ALLOCATOR_SPEC.md` to understand how new IDs are allocated (e.g. monotonic counters per scope).
    *   Review `SCOPE_AND_COUNTER_KEY_DECISION.md` and `SCOPE_EXPLANATION_FOR_DECISION.md` to know which directories are governed (in scope) and how scopes map to ID counters.
    *   Review `2026012100230003_SCHEMA_AUTHORITY_POLICY.md` for the authoritative schema policy and any constraints on modifying schema fields.
3.  **Load watcher and plugin configuration**:
    *   Read `watcher subsystem.md` to understand the high‑level behaviour of the watcher (how events are collected and debounced).
    *   Parse `WATCHER_CONFIG.yml` for runtime configuration: watched root directories, ignore patterns (e.g. `.git`, `__pycache__`), debounce intervals, and concurrency limits.
    *   Parse `PLUGIN_REGISTRY.yml` to determine which parser/extractor plugins are enabled. For Python files, ensure that the `python_ast_parser` and `python_descriptor_extractor` plugins are listed.
4.  **Load ID registry and registry files**:
    *   Load `ID_REGISTRY.json` and `1199900028260118_ID_REGISTRY.json` to read existing ID allocations and scopes. These files track reserved ranges of `doc_id` values and must be updated whenever new IDs are allocated.
    *   Load the current SSOT registry file `2026012201113004_FILE_REGISTRY_v2.json` (or the canonical `FILE_REGISTRY.json`). This file stores one row per file entity and is the authoritative store for all promoted columns. The CLI will read and update this file.
5.  **Load descriptor and parser code**:
    *   Import `DOC-SCRIPT-0996__python_ast_parser.py` as `python_ast_parser`. This module performs AST parsing on Python files.
    *   Import `DOC-SCRIPT-1272__python_ast_parser.py` (a thin wrapper) if your code references a stable document‑ID import path.
    *   Load `automation_descriptor_extractor.py` which combines declared metadata and AST‑inferred facts into a descriptor object and a promotion payload.
    *   Load `REQUIRED DECLARATIVE METADATA (authoritative).py`; this script defines which fields must be provided manually and are considered authoritative.
    *   Load `AUTOMATION_FILE_DESCRIPTOR.yml` (and the more general `PYTHON_FILE_DESCRIPTOR.yml` if available) to understand the expected schema for descriptor JSON files.
    *   Load `describe_automations_cli.py` to reuse or extend its CLI structure for describing Python scripts; if creating a new CLI, base it on this file.
    *   Load `descriptor_manual_fields_needed.py` if still in use; otherwise plan to phase it out.
    *   Optionally load test files (`DOC-TEST-0639__test_python_ast_parser.py` and `DOC-TEST-0632__test_copilot_parser.py`) to run automated tests.
6.  **Prepare runtime directories**:
    *   Ensure the directory `.dms/` exists. Within it create these subdirectories (if they do not exist):
        *   `.dms/artifacts/python_descriptor/` — where descriptor JSON files will be written.
        *   `.dms/artifacts/index/` — where derived index files will be written.
        *   `.dms/patches/registry/` — optional directory to store registry patch files.
        *   `.dms/runtime/locks/path/` and `.dms/runtime/locks/doc/` — to hold lock files for paths and doc IDs.
        *   `.dms/runtime/` with `work_queue.sqlite` — persistent queue database for pending work items.
        *   `.dms/logs/` with `actions.jsonl` and `errors.jsonl` — append‑only logs for actions and errors.
        *   `.dms/quarantine/` — where problematic files are moved or copied when policy violations occur.

2\. Event Ingestion and Debounce Loop
-------------------------------------

1.  **Start the watcher service** as defined in `watcher subsystem.md`. The watcher should:
    *   Monitor each root directory specified in `WATCHER_CONFIG.yml` for file system events: create, modify, move, and delete.
    *   Ignore any event whose path matches an ignore pattern (e.g. inside `.git`, `.dms`, `__pycache__`).
    *   For each event, insert a work item into `work_queue.sqlite` with fields: `path`, `event_type`, `timestamp`, and initial `status` = `queued`. Log this action in `actions.jsonl`.
2.  **Debounce events**:
    *   For each unique path, collect modifications within a configured debounce window (e.g. 500 ms). After no changes occur for the path for the specified interval, mark the work item’s status as `stable_ready`. Log the state change in `actions.jsonl`.

3\. Classification and Locking
------------------------------

1.  **Classification**:
    *   Pop a `stable_ready` work item from `work_queue.sqlite` and classify it:
        *   Determine whether the path is **governed** based on `SCOPE_AND_COUNTER_KEY_DECISION.md`; if not governed, mark the work item as `unmanaged`, update the registry row if it exists (`status=unmanaged`), and skip further processing.
        *   Determine the file kind by extension (e.g. `.py` for Python). Only `.py` files will go through the Python parser; other extensions may use other plugins or be skipped.
        *   Check if the file already contains a 16‑digit prefix matching the `doc_id` pattern; if so, extract it. Otherwise, note that an ID must be allocated.
2.  **Acquire locks**:
    *   For each work item to be processed, acquire a **path lock** file under `.dms/runtime/locks/path/` using a hash of the path. If the lock cannot be acquired, leave the work item as `stable_ready` and retry later.
    *   If a `doc_id` is known, also acquire a **doc lock** file under `.dms/runtime/locks/doc/{doc_id}.lock` to prevent concurrent processing of the same entity.

4\. ID Assignment, Rename, and Registry Row Creation
----------------------------------------------------

1.  **ID allocation** (if the file lacks a valid `doc_id`):
    *   Consult `ID_REGISTRY.json` and `1199900028260118_ID_REGISTRY.json` to find the next available ID range for the file’s scope as determined by `SCOPE_AND_COUNTER_KEY_DECISION.md`.
    *   Use the sequence allocator defined in `SEQ_ALLOCATOR_SPEC.md` to obtain the next unused 16‑digit `doc_id`. Reserve this ID by updating the appropriate ID registry file atomically.
2.  **Atomic rename**:
    *   Rename the file in place to include the new `doc_id` as a prefix, preserving the original name. For example, `foo.py` becomes `1234567890123456_foo.py`. Ensure no other process can write to the file during rename (use the path lock).
3.  **Insert or update registry row**:
    *   Open `2026012201113004_FILE_REGISTRY_v2.json` (or the canonical `FILE_REGISTRY.json`) and locate the row for this `doc_id`. If it does not exist, create a new row with core fields: `record_kind=entity`, `entity_kind=file`, `doc_id`, `relative_path`, `status=registered`, `created_utc`, `created_by`, `updated_utc`, `updated_by`. Leave all promotion columns `null`.
    *   If the row exists, update the `relative_path` and `updated_utc` and set `status=registered` if previously unset or unmanaged.
    *   Atomically write the registry file (e.g. write to a temporary file then replace the original). Optionally create a patch file in `.dms/patches/registry/` recording the update.
    *   Log the ID allocation, rename, and registry update actions in `actions.jsonl`.

5\. Parsing and Descriptor Generation
-------------------------------------

1.  **Hash the source**:
    *   Read the contents of the newly renamed `.py` file and compute a SHA‑256 hash. Compare this hash with the `py_source_sha256` stored in the registry row; if unchanged, skip parsing and proceed to step 6 (promotion and update). If changed or missing, continue.
2.  **Run the Python AST parser**:
    *   Call `python_ast_parser.parse(path)` (implemented in `DOC-SCRIPT-0996__python_ast_parser.py`) to produce a structured representation of the file: imports, functions, classes, main guard, CLI detection, etc. Catch and record exceptions (e.g. syntax errors, encoding errors).
3.  **Merge with declarative metadata**:
    *   Load any declarative metadata found in the file itself (e.g. top‑level YAML comments or special variables) and validate it against `REQUIRED DECLARATIVE METADATA (authoritative).py` to ensure required fields are present.
4.  **Extract descriptor and promotion payload**:
    *   Call `automation_descriptor_extractor.extract(parsed_ast, declarative_metadata)` to produce two structures:
        *   A **descriptor** object conforming to `PYTHON_FILE_DESCRIPTOR.yml`. This descriptor contains full lists of imports, environment variables, functions, classes, declared inputs/outputs, and a `manual_fields_needed` list if anything is missing.
        *   A **promotion payload**: a dictionary keyed by the Python promotion column names (e.g. `py_parse_status`, `py_module_qualname`, `py_has_main_guard`, `py_cli_framework`, `py_imports_local`, `py_imports_external`, `py_imports_local_count`, `py_imports_external_count`, `py_function_count`, `py_class_count`, `py_docstring_1l`, `py_descriptor_path`, `py_descriptor_sha256`).
5.  **Write descriptor file**:
    *   Construct the descriptor file path: `.dms/artifacts/python_descriptor/{doc_id}.v1.json`. Write the descriptor JSON to this path. Compute its SHA‑256 and record in the promotion payload as `py_descriptor_sha256`. Log the descriptor creation action.

6\. Applying Promotion to Registry
----------------------------------

1.  **Prepare registry patch**:
    *   Build a patch object including: `registry_version`, `doc_id`, `work_item_id`, `utc_ts`, `actor` (with `tool` and `tool_version`), and a list of operations. Each operation is a `set` on a registry path corresponding to a promotion column (e.g. `/py_parse_status`, `/py_parsed_utc`, `/py_module_qualname`, etc.) with the value from the promotion payload.
    *   The patch must not modify core identity fields (doc\_id, relative\_path, status) and must be idempotent: if the same source hash is parsed again, the promotion values must be identical.
2.  **Apply patch**:
    *   Acquire the registry lock and apply the patch atomically: load the registry JSON, modify only the row matching `doc_id` at the specified paths, update `updated_utc` and `updated_by`, and write back.
    *   Optionally write the patch JSON to `.dms/patches/registry/{utc_ts}__{work_item_id}__{doc_id}.json`.
    *   Log the registry update in `actions.jsonl`.

7\. Derived Indexes and Post‑processing
---------------------------------------

1.  **Run downstream generators** (once per batch):
    *   After all work items in the current batch have been processed, invoke any deterministic generators that depend on the registry (e.g. rebuilding a module dependency graph or aggregated process index) and write their outputs into `.dms/artifacts/index/`.
    *   Generators must read only from the registry and produce outputs deterministically; never modify the registry.
    *   Log generator invocations in `actions.jsonl`.

8\. Finalization and Cleanup
----------------------------

1.  **Update work item state**:
    *   Mark the current work item as `done` in `work_queue.sqlite` and release the path and doc locks.
    *   If errors occurred at any stage, record them in `errors.jsonl` and decide whether to retry based on the retry policy (see section 9).
2.  **Repeat**: return to the event ingestion loop for the next work item.

9\. Retry and Error Handling
----------------------------

1.  **Retry policy**:
    *   Define a maximum number of attempts (e.g. 8) and a back‑off schedule (e.g. 5 s, 15 s, 45 s, 2 min, 5 min, 15 min, 30 min, 1 hr) for retryable errors such as `FILE_LOCKED`, `PERMISSION_DENIED_TRANSIENT`, or `TEMP_IO_ERROR`.
    *   Non‑retryable errors (e.g. policy violations, repeated parse failures beyond threshold) move the registry row into `status=quarantine` and place the file in `.dms/quarantine/`.
2.  **Logging**:
    *   All actions (enqueue, dequeue, ID allocation, rename, parse success/failure, descriptor write, registry update, generator run, retry decision) must be recorded in `actions.jsonl`.
    *   All exceptions must be recorded in `errors.jsonl` with details about the stage and error type. Use these logs for audits and debugging.

10\. Reconciler Scan (Periodic Task)
------------------------------------

1.  **Periodic validation**:
    *   At scheduled intervals (e.g. once per day or on demand), run a reconciler that performs a complete walk of the project tree and registry:
        *   Discover governed files not present in the registry and enqueue them for processing.
        *   Detect moved or renamed files and update the registry accordingly.
        *   Compare the stored `py_source_sha256` with the hash of the current file; if they differ, enqueue the file for re‑parsing.
        *   Verify that every `.dms/artifacts/python_descriptor/{doc_id}.v1.json` exists for its row; re‑generate if missing.
        *   Verify that the descriptor’s hash matches `py_descriptor_sha256`; re‑generate if mismatched.
    *   Log all reconciler actions in `actions.jsonl`.

11\. Column Dictionary Updates (Schema Maintenance)
---------------------------------------------------

1.  **Update the column dictionary**:
    *   When adding the Python promotion columns (e.g. `py_parse_status`, `py_parsed_utc`, `py_parser_id`, `py_parser_version`, `py_module_qualname`, `py_has_main_guard`, `py_cli_framework`, `py_imports_local`, `py_imports_external`, `py_imports_local_count`, `py_imports_external_count`, `py_function_count`, `py_class_count`, `py_docstring_1l`, `py_descriptor_path`, `py_descriptor_sha256`), update `2026012015460001_COLUMN_DICTIONARY.md` accordingly.
    *   For each column define the data type (string, boolean, integer, array\[string\], or null), when the field applies, valid values, and examples. Use existing entries (e.g. the `tags` column showing `array[string]`【177:2†2026012015460001\_COLUMN\_DICTIONARY.md†L17-L27】) as a template for formatting.

12\. Test and Validate
----------------------

1.  **Unit tests**:
    *   Run `DOC-TEST-0639__test_python_ast_parser.py` to validate the behaviour of the AST parser.
    *   Run `DOC-TEST-0632__test_copilot_parser.py` if relevant.
    *   Add new tests to cover ID allocation, renaming, descriptor generation, promotion payload creation, and registry updates.
2.  **Manual validation**:
    *   Perform manual checks of a few sample files to ensure that descriptor JSON files contain expected fields and that the registry rows reflect the promoted values.
    *   Use `describe_automations_cli.py` (or the new CLI) in dry‑run mode to print descriptors without writing them to disk; compare against expected outputs.
3.  **Documentation updates**:
    *   After implementing the CLI, update any relevant user or developer documentation (e.g. README files) to explain how to run the CLI, which files must be present (config and spec files), and how to interpret logs and registry updates.

This document was created with the context of your column dictionary, which indicates array types and MIME types like “application/python”【177:2†2026012015460001\_COLUMN\_DICTIONARY.md†L17-L27】 and draws on the SSOT registry schema.

Let me know if you need any changes or further clarification.



---
Powered by [ChatGPT Exporter](https://www.chatgptexporter.com)