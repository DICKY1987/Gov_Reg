---
doc_id: DOC-GUIDE-PATH-ABSTRACTION-INDIRECTION-LAYER-473
---

# PATH ABSTRACTION & INDIRECTION LAYER

**Agentic CLI Task Specification**

> **Audience:** Agentic AI CLI apps (Codex CLI, Claude Code CLI, Aider, etc.) acting as autonomous refactoring/infra agents in a Git repo.
> **Goal:** Replace hard-coded file paths in scripts/configs with a **stable key → path indirection layer**, so that future directory changes only require updating a central registry.

---

## 1. Purpose & High-Level Objectives

You (the AI CLI app) are responsible for:

1. **Designing and implementing an indirection layer** for all “important” paths in the repository.
2. **Refactoring scripts and tools** to use *semantic keys* (e.g. `phase_docs.ph02_state_layer_spec`) instead of literal paths.
3. **Integrating with the existing Hardcoded Path Indexer** so that:

   * Hard-coded paths are systematically removed over time.
   * Future refactors are driven by updating a single registry.

The outcome: scripts, tools, and other automation **no longer depend directly** on physical directory structure. They depend on logical keys resolved by a **Path Registry**.

---

## Current Implementation Anchors

- Registry source: `config/path_index.yaml`
- Resolver library: `src/path_registry.py`
- CLI wrapper: `scripts/dev/paths_resolve_cli.py` (`paths-resolve`)

---

## 2. Scope & Non-Goals

### In Scope

* Creation of:

  * A **human-readable spec** for the indirection system.
  * A **machine-readable registry** defining keys → paths.
  * A **resolver library + CLI** for looking up paths by key.
* Refactoring:

  * Python scripts, PowerShell scripts, and other automation to use **keys** instead of hard-coded paths.
* Integration:

  * Use of the **Hardcoded Path Index DB** (if present) to:

    * Discover existing hard-coded paths.
    * Track progress replacing them with key-based access.

### Out of Scope

* Changing business logic or external APIs beyond what’s needed for path abstraction.
* Moving files or redesigning the entire directory structure (that’s handled by the **Section Refactor** spec).
* Replacing *all* hard-coded paths in one shot; focus first on **high-value** and **high-risk** paths.

---

## 3. Key Concepts & Definitions

### 3.1. Path Key

A **Path Key** is a stable, semantic identifier for a resource, independent of its physical path.

Examples:

* `phase_docs.ph02_state_layer_spec`
* `phase_docs.ph03_tool_profiles_spec`
* `aider.git_import_prompt_example`
* `error.operating_contract`
* `spec.multi_doc_main_spec`
* `pm.ccpm_setup_guide`

Path keys:

* Are **stable** across directory changes.
* Are **namespaced** (e.g., `phase_docs.*`, `aider.*`, `error.*`).
* Are used by scripts instead of literal filesystem paths.

### 3.2. Path Registry

The **Path Registry** is the central mapping of **keys → paths + metadata**.

* Stored in a machine-readable file (e.g. `config/path_index.yaml`) or a dedicated table in SQLite.
* Human-facing spec is in `docs/PATH_INDEX_SPEC.md` (or equivalent).
* Scripts and tools do **not** hard-code paths; they call a resolver that reads the registry.

Example `config/path_index.yaml`:

```yaml
paths:
  phase_docs:
    ph00_baseline_spec:
      path: "PHASE_DEV_DOCS/PH-00_Baseline & Project Skeleton.md"
      section: "core"
    ph01_spec_alignment:
      path: "PHASE_DEV_DOCS/PH-01_Spec Alignment & Index Mapping.md"
      section: "core"
    ph02_state_layer_spec:
      path: "PHASE_DEV_DOCS/PH-02_Data Model, SQLite State Layer & State Machine.md"
      section: "core"

  aider_help:
    git_import_prompt_example:
      path: "AIDER_PROMNT_HELP/AIDER_GIT_IMP_PROMNT_EXAMPLE.md"
      section: "aider"

  error_docs:
    operating_contract:
      path: "MOD_ERROR_PIPELINE/ERROR_Operating Contract.txt"
      section: "error"
```

### 3.3. Path Resolver

The **Path Resolver** is a small library/CLI that:

* Loads the Path Registry.
* Resolves a key like `phase_docs.ph02_state_layer_spec` to the **current repo-relative path**.
* Provides a consistent API to all scripts.

Conceptual Python API:

```python
from path_registry import resolve_path

path = resolve_path("phase_docs.ph02_state_layer_spec")
# -> "spec/phase_docs/PH-02_State_Layer.md" after refactor
```

Conceptual CLI:

```bash
paths-resolve phase_docs.ph02_state_layer_spec
# prints resolved path to stdout
```

### 3.4. Integration with Hardcoded Path Indexer

If a **Hardcoded Path Indexer** exists (e.g., `refactor_paths.db`):

* It tracks where legacy hard-coded paths still appear.
* It can help identify:

  * Which occurrences must be replaced with `resolve_path(...)`.
  * Which patterns are now **forbidden** (old paths that should be abstracted).

---

## 4. Objectives for the Agent

You must:

1. **Design the key naming scheme** and Path Registry schema.
2. **Implement the Path Registry** (YAML or DB-backed).
3. **Implement the Path Resolver** as:

   * A small Python module (library).
   * A CLI wrapper for other languages and shell scripts.
4. **Refactor selected scripts** to use keys instead of hard-coded paths.
5. **Hook into the Hardcoded Path Indexer** to:

   * Prioritize replacing high-risk hardcoded paths.
   * Mark occurrences as “updated” once converted to key-based access.
6. **Document the abstraction** clearly for future human and AI use.

---

## 5. Detailed Deliverables

### 5.1. Documents

1. **`docs/PATH_ABSTRACTION_SPEC.md`** (this document or refined version)

   * Describes:

     * What Path Keys are.
     * How the path registry is structured.
     * How resolvers must be used by tools and AIs.
2. **Updated `docs/PATH_INDEX_SPEC.md`**

   * Cross-references the abstraction:

     * Explains that `PATH_INDEX_SPEC` is the human-facing view of the same key → path mapping.

### 5.2. Registry Artifacts

3. **`config/path_index.yaml`** (or equivalent)

   * Authoritative mapping of keys → paths.
   * May also include:

     * `section`
     * `description`
     * Flags like `deprecated`, `read_only`, etc.

   Example extended entry:

   ```yaml
   paths:
     error_docs:
       operating_contract:
         path: "error/ERROR_Operating Contract.txt"
         section: "error"
         description: "Primary operating contract for the error pipeline."
         deprecated: false
   ```

4. **(Optional) DB Mapping Table**

   * Path index integrated into `refactor_paths.db`:

     * Table `path_registry` with columns `key`, `path`, `section`, `description`, etc.
   * YAML remains the human-editable source; DB is for fast queries.

### 5.3. Resolver Code

5. **Python Resolver Module** (e.g. `src/path_registry.py`)

   Minimum API:

   ```python
   def resolve_path(key: str) -> str:
       """
       Resolve a key to a repo-relative path, or raise a clear error.
       """

   def list_paths(section: str | None = None) -> dict[str, str]:
       """
       Return a mapping {key: path} optionally filtered by `section`.
       """
   ```

   Requirements:

   * Load `config/path_index.yaml` once and cache it.
   * Provide clear, deterministic error messages for:

     * Unknown key.
     * Missing path in config.
   * Include unit tests:

     * Resolving valid keys.
     * Handling invalid keys.
     * Behavior when config is missing or malformed.

6. **CLI Wrapper** (e.g. `scripts/paths_index_cli.py`)

   Suggested commands:

   ```bash
   paths-resolve <key>
   paths-list [--section <section>]
   paths-debug <key>     # show full entry (path, section, description)
   ```

   Usage:

   * Allows PowerShell, shell scripts, and other tools to resolve keys without embedding Python logic.

### 5.4. Refactored Scripts

7. **Updated scripts** that previously used hard-coded paths:

   * Replace constructs like:

     ```python
     path = "PHASE_DEV_DOCS/PH-02_Data Model, SQLite State Layer & State Machine.md"
     ```

     with:

     ```python
     from path_registry import resolve_path

     path = resolve_path("phase_docs.ph02_state_layer_spec")
     ```

   * For PowerShell:

     ```powershell
     # Old
     $SpecPath = "PHASE_DEV_DOCS\PH-02_Data Model, SQLite State Layer & State Machine.md"

     # New
     $SpecPath = paths-resolve phase_docs.ph02_state_layer_spec
     ```

8. **Refactor report** (Markdown or JSON):

   * List of files updated.
   * Keys introduced.
   * Any deprecated paths that still exist and why.

### 5.5. Integration with Hardcoded Path Indexer

9. **Integration logic** (can be part of tools or scripts):

   * For each occurrence of a hard-coded path found in `refactor_paths.db`:

     * Determine if it should be abstracted.
     * If yes:

       * Create a path key (if one doesn’t exist).
       * Update the code to use `resolve_path(key)`.
       * Mark the occurrence as `updated` or `auto_fixed`.

10. **Optional CI check**:

* A GitHub Actions job that:

  * Runs the Hardcoded Path Indexer.
  * Fails if new `pending` occurrences appear for **deprecated** patterns that have a registered key in `config/path_index.yaml`.

---

## 6. Recommended Approach (Algorithm for the Agent)

### Phase 1 – Analyze & Design the Key Space

1. **Inventory “special” paths**:

   * Using:

     * Existing knowledge of important docs/scripts.
     * Hardcoded Path Index DB (if present).
   * Identify paths that:

     * Are used by multiple scripts.
     * Are referred to in docs and prompts.
     * Are likely to move again (e.g., spec docs, phase plans).

2. **Define key naming conventions**:

   * Namespace by domain or section:

     * `phase_docs.*`, `aider.*`, `error_docs.*`, `spec.*`, `pm.*`, etc.
   * Ensure keys are:

     * Stable.
     * Readable.
     * Unique.

3. **Generate initial `config/path_index.yaml`**:

   * Populate keys for the highest-value paths.
   * Document them in comments where helpful.

### Phase 2 – Implement Registry & Resolver

1. Implement the **resolver library**:

   * YAML loading.
   * Key parsing (e.g., split on `.`).
   * Error handling.

2. Implement the **CLI wrapper**:

   * `paths-resolve`, `paths-list`, `paths-debug`.

3. Add **unit tests** for both.

4. Optionally integrate with `refactor_paths.db` so the registry can be mirrored into the DB if needed.

### Phase 3 – Gradual Refactor of Scripts

1. **Identify target scripts**:

   * Use the Hardcoded Path Indexer to find files containing:

     * `PHASE_DEV_DOCS`
     * `AIDER_PROMNT_HELP`
     * `MOD_ERROR_PIPELINE`
     * Other known-volatile paths.
   * Prioritize:

     * Scripts run frequently.
     * Scripts executed by CI.
     * Scripts used by multiple tools (Codex, Aider, Claude, etc.).

2. **Refactor a small batch**:

   * For 1–3 scripts:

     * Introduce path keys and update `config/path_index.yaml`.
     * Replace hard-coded paths with `resolve_path(key)` calls.
     * Run tests / script in dry-run mode.
   * Verify behavior matches pre-refactor.

3. **Iterate in batches**:

   * After successful small batch, expand to more scripts.
   * Keep each batch small enough to be reviewable and testable.

4. **Update Hardcoded Path Index**:

   * Re-run the scanner on modified files.
   * Update occurrence statuses:

     * Old literal path removed → `status = 'updated'` or `auto_fixed`.

### Phase 4 – Documentation & Enforcement

1. Update `PATH_ABSTRACTION_SPEC` and `PATH_INDEX_SPEC` to reflect the new abstraction:

   * Add examples of:

     * How new scripts should be written.
     * How future AIs should add new keys.

2. Add a **“How to add a new path key”** section:

   * Steps for humans/AIs to:

     * Choose a key.
     * Update `config/path_index.yaml`.
     * Use `resolve_path(key)` in new code.

3. Optionally add a **CI rule**:

   * After a cutover date:

     * For certain patterns (e.g., `PHASE_DEV_DOCS`), **only** allow references via the registry.
     * Fail the build if new hard-coded references appear.

---

## 7. Design Principles & Constraints

You must follow these:

* **Single Source of Truth**:
  The Path Registry is the **only** place that encodes the real path to a “special” file. Scripts must rely on keys.

* **Minimal Complexity**:
  The resolver should be as simple and deterministic as possible:

  * Avoid clever logic that guesses keys.
  * No network calls.
  * Prefer simple YAML + small Python module.

* **Backward-Compatible Migration**:
  During the refactor, there may be a period where both:

  * Old hard-coded paths exist.
  * New key-based calls exist.

  You must keep the system runnable and tests passing throughout the transition.

* **Traceability**:
  When you replace a hard-coded path:

  * Leave a clear commit message.
  * Optionally add a comment linking the key to its old path for historical understanding (until docs are updated).

---

## 8. Quick Summary for Future Agents

When you (future AI agent) see this spec:

1. **Never introduce new hard-coded paths** for “important” files.

   * Always add a Path Key and use `resolve_path(key)` or `paths-resolve`.

2. **When a file moves**:

   * Update `config/path_index.yaml`, *not* every script.
   * Run tests and `paths-index` / Hardcoded Path Indexer to confirm there are no stale references.

3. **When creating new automation**:

   * Use Path Keys for any doc/config/script path that:

     * Might be referenced by multiple tools.
     * Might move in future refactors.

This indirection layer is your **abstraction boundary** between “what the code wants” and “where the file actually lives.”
