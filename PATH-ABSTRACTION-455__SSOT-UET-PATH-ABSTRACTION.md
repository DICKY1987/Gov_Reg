
SSOTPATH-ABSTRACTION.md

---

````markdown
---
doc_id: DOC-SSOT-UET-PATH-ABSTRACTION-001
status: active
doc_type: ssot_guide
ssot_scope:
  - uet_abstraction_contracts
  - path_abstraction_indirection_layer
supersedes:
  - DOC-GUIDE-UET-ABSTRACTION-GUIDELINES-MD-001
  - DOC-GUIDE-PATH-ABSTRACTION-INDIRECTION-LAYER-473
version: 1.0.0
last_updated: 2025-12-08
---

# UET & Path Abstraction – Single Source of Truth (SSOT)

**Audience**

- Human maintainers.
- Agentic CLI tools (Codex CLI, Claude Code CLI, Aider, etc.).
- Any automation that touches repo paths or cross-module boundaries.

**Goal**

Define a **single, canonical abstraction story** for the pipeline:

1. **UET abstraction rules** – *where* abstraction is mandatory and what “abstraction” means in this system.
2. **Path Abstraction & Indirection Layer** – how files and directories are referenced via **keys** instead of hard-coded paths.

Everything else (older guides/specs) should be treated as **derived** from this document.

---

## 1. Core Principle

> **The contracts ARE your abstractions.**

In this system, “abstraction” primarily means:

- **Stable data contracts** (DTOs / record types, e.g. `*V1` types in `UET_SUBMODULE_IO_CONTRACTS.md`).
- **Small helper APIs** that enforce those contracts at **module boundaries**.
- An **indirection layer for paths** so tools talk in **semantic keys** instead of raw file system paths.

It does **not** mean:

- Large class hierarchies.
- Over-generic frameworks.
- Over-abstracting simple, single-module code.

---

## 2. Scope & Non-Goals

### 2.1 In Scope

This SSOT governs:

1. **Cross-boundary abstraction rules**

   - Between **orchestrator ↔ workers/tools**.
   - Between **business logic ↔ environment** (Git, OS, DB, filesystem).
   - Between **patterns ↔ raw scripts/LLM calls**.
   - Between **error engine ↔ error producers**.
   - Between **logical resource names ↔ physical repo paths** (Path Indirection Layer).

2. **Path Abstraction & Indirection Layer**

   - Path keys and naming scheme.
   - Path registry format and location.
   - Resolver library + CLI behavior.
   - Integration with Hardcoded Path Index DB.

3. **Operational & review rules**

   - Where abstraction is **mandatory** vs **optional**.
   - How AI agents and humans should use these abstractions.
   - Migration patterns from legacy/hard-coded usage to contract/key-based usage.

### 2.2 Out of Scope

- Arbitrary architectural style debates (OOP vs FP, etc.) inside a single module.
- Complete directory redesign (covered by separate **Section Refactor** specs).
- Business domain design; this doc only governs **boundaries** and **paths**.
- UI specifics; this is backend/automation abstraction only.

---

## 3. Where Abstraction IS Mandatory

Abstraction is **required** at the following boundaries.

### 3.1 Orchestrator ↔ Workers / Tools

**Rule**

- Orchestrator and workstream engine must talk to workers via **typed contracts**, e.g.:

  - `ExecutionRequestV1`
  - `ExecutionResultV1`
  - `TaskStateV1`
  - `ToolProfileV1`

**Implications**

- Orchestrator **never** calls raw `subprocess.run([...])` for specific tools inlined.
- Workers can swap implementation (Aider, Codex, custom script) as long as they respect the same contracts.

---

### 3.2 Domain Logic ↔ Environment (OS, Git, DB, FS)

**Rule**

- Domain/business code must not call Git/OS/DB/filesystem directly.
- All such calls go through an **environment abstraction layer**, using contracts like:

  - `GitWorkspaceRefV1`, `GitStatusV1`
  - `RunRecordV1`, `PatchRecordV1`
  - `RepoPathRefV1`, `ResolvedPathV1`
  - `LogEventV1`

**Effect**

- Changing underlying tools (e.g. from `git` CLI to a Python Git lib) or storage (SQLite → Postgres) does **not** affect domain logic.
- Testing is easier (you can substitute fake environment adapters).

---

### 3.3 Patterns ↔ Raw Scripts / LLM Calls

**Rule**

- Pattern executors call a **pattern execution contract**, not scripts/tool-specific entry points.

**Example (good)**

```python
result = run_pattern(
    PatternRefV1(pattern_id="PAT-EXEC-ATOMIC-CREATE-001"),
    ExecutionRequestV1(...)
)
````

**Anti-pattern**

```python
subprocess.run(["python", "scripts/create_file.py", ...])
```

Pattern internals can change (shell script → AST transform → LLM) without changing callers.

---

### 3.4 Error Engine ↔ Everything Else

**Rule**

* Error detection and classification plugins must only see **normalized error events** such as `ErrorEventV1`.

**Effect**

* Error engine stays decoupled from internals of execution, test frameworks, or tools.
* New tools only need to emit `ErrorEventV1` rather than custom plugin logic everywhere.

---

### 3.5 Logical Resource ↔ Physical Paths (Path Indirection)

**Rule**

* “Important” docs/configs/scripts are referenced by **path keys** like
  `phase_docs.ph02_state_layer_spec`, not `spec/phase_docs/PH-02_State_Layer.md`.

**Effect**

* Moving or renaming files only requires updating the **Path Registry**, not every script and prompt.
* AI agents can reason in terms of semantic keys instead of brittle path strings.

---

## 4. Where NOT to Add Abstraction

Abstraction is **optional and usually discouraged** when:

* Code lives entirely within a **single module** and has **local impact only**.
* You’re writing **one-off scripts**, ad-hoc migrations, or exploratory experiments.
* Utilities are **tiny and stable** (e.g. a two-line helper that will not be shared across modules).

In these cases:

* Prefer **simple, direct code**.
* Avoid creating “just in case” layers that nobody uses.

**Heuristic**

> If there is no cross-module boundary, cross-process boundary, or external coupling, a simple function is often enough.

---

## 5. Public vs Internal API Rules

Every **shared module** (anything imported by more than one subsystem) MUST:

1. Declare **public types** (DTOs) it accepts / returns.
2. Declare **public functions** (stable signatures + behavior).
3. Treat everything else as **internal**.

### 5.1 Naming Conventions

* **Public** functions: normal names (e.g. `resolve_path`, `get_workspace_status`).
* **Internal** functions: prefixed with `_` (e.g. `_internal_resolve`, `_call_git_status`).
* Types are versioned with a **`V1` suffix** to allow evolution (`RepoPathKeyV1`, `ResolvedPathV1`).

### 5.2 Evolution Rule

* Internals can change freely.
* Public contracts must remain **backwards compatible** or be version-bumped (`V1` → `V2`) and migrated.

---

## 6. Path Abstraction & Indirection Layer

This section merges and replaces the older **Path Abstraction & Indirection Layer** agent spec.

### 6.1 Current Implementation Anchors

These are the canonical implementation points (names can be updated, but this doc is authoritative):

* **Registry source**: `config/path_index.yaml`
* **Resolver library**: `src/path_registry.py`
* **CLI wrapper**: `scripts/dev/paths_resolve_cli.py` (entrypoint command: `paths-resolve`)

If these move, **update this SSOT and the Path Registry**, not every consumer.

---

### 6.2 Path Keys

A **Path Key** is a stable, semantic identifier for a resource, independent of its physical path.

**Examples**

* `phase_docs.ph02_state_layer_spec`
* `phase_docs.ph03_tool_profiles_spec`
* `aider.git_import_prompt_example`
* `error_docs.operating_contract`
* `spec.multi_doc_main_spec`
* `pm.ccpm_setup_guide`

#### Properties

* **Stable**: does not change when files are moved/renamed.
* **Readable**: encodes meaning, not implementation details.
* **Unique**: one key → one resource.

Recommended structure:

```text
<namespace>.<subdomain>_<descriptor>
```

Where:

* `namespace` distinguishes domains (`phase_docs`, `aider`, `error_docs`, `spec`, `pm`, ...).
* The rest is free-form but should be concise and descriptive.

---

### 6.3 Path Registry

The **Path Registry** is a machine-readable mapping of keys → repo paths, plus optional metadata.

**Location**

* Default: `config/path_index.yaml`

**Shape (example)**

```yaml
# config/path_index.yaml

version: 1
paths:
  phase_docs.ph02_state_layer_spec:
    path: "spec/phase_docs/PH-02_State_Layer.md"
    kind: "doc"
    notes: "SSOT for Phase 2 state layer spec"

  phase_docs.ph03_tool_profiles_spec:
    path: "spec/phase_docs/PH-03_Tool_Profiles.md"
    kind: "doc"

  aider.git_import_prompt_example:
    path: "AIDER_PROMNT_HELP/AIDER_GIT_IMP_PROMNT_EXAMPLE.md"
    kind: "prompt"

  error_docs.operating_contract:
    path: "MOD_ERROR_PIPELINE/ERROR_Operating Contract.txt"
    kind: "operating_contract"
```

**Rules**

* New stable resources must get a **Path Key**, not a hard-coded path in scripts.
* Keys must not be reused for different resources.
* Changes to `path` entries must go through normal review (it’s an abstraction boundary).

---

### 6.4 Path Resolver (Library + CLI)

The **Path Resolver** is the **only supported way** to go from key → path.

**Conceptual Python API**

```python
from path_registry import resolve_path, PathNotFoundError

path = resolve_path("phase_docs.ph02_state_layer_spec")
# returns a repo-relative string path like "spec/phase_docs/PH-02_State_Layer.md"
```

**Basic behavior**

* Loads `config/path_index.yaml` (or configured path).
* Validates the registry schema.
* Resolves a key to a **repo-relative path**.
* Raises a typed error (e.g. `PathNotFoundError`) if the key is unknown.

**CLI wrapper (concept)**

```bash
# Echo the path for a key
paths-resolve phase_docs.ph02_state_layer_spec
# -> spec/phase_docs/PH-02_State_Layer.md
```

**Usage rules**

* Scripts **MUST NOT** embed `"spec/phase_docs/PH-02_State_Layer.md"` directly.
* They must call the resolver (Python, PowerShell, or CLI wrapper) with the **key**.

---

### 6.5 Hardcoded Path Index Integration

If a **Hardcoded Path Index DB** exists, it is the source of truth for:

* Which hard-coded paths still exist.
* Which have been migrated to key-based usage.

**Agent responsibilities**

* Use the DB to **discover** high-value / high-risk paths to migrate first.
* Mark occurrences as “updated” once they are replaced with Path Keys.
* Keep a running “migration progress” view (e.g. docs or JSON summary).

---

## 7. Agent & Tool Responsibilities

This section replaces the “Agentic CLI Task Specification” parts from the older path spec.

### 7.1 For Agentic CLI Apps (Codex, Claude Code, Aider, etc.)

When running in “infra/refactor” modes, an agent should:

1. **Design / maintain the key scheme**

   * Ensure consistent namespaces (`phase_docs.*`, `aider.*`, `error_docs.*`, `spec.*`, `pm.*`, etc.).
   * Avoid duplication and ambiguous keys.

2. **Maintain the Path Registry**

   * Add/update entries in `config/path_index.yaml`.
   * Keep comments/notes clear for other agents and humans.
   * Validate the registry before committing.

3. **Implement / call the Resolver**

   * Use the Python library where possible.
   * Use CLI wrapper (`paths-resolve`) from PowerShell/shell as needed.
   * Treat resolver failures as **configuration errors**, not random runtime bugs.

4. **Refactor hard-coded paths**

   * Prefer migrating:

     * Paths used by multiple scripts.
     * Paths referenced in prompts/specs.
     * Paths that are likely to move (docs, specs, phase plans).

   * Replace literals with calls to the resolver.

5. **Respect UET contracts**

   * At every boundary, exchange only the **typed contracts** and path **keys**, not tool-specific or path-specific details.
   * Never embed raw `subprocess` + literal paths in orchestrator or pattern boundary code.

---

### 7.2 For Human Maintainers

* Review new code for:

  * Use of **contracts** at boundaries.
  * Use of **Path Keys** instead of raw paths.
* Keep this SSOT updated when:

  * New important resources are introduced.
  * Implementation anchors move (e.g. resolver file relocations).
  * Contract types evolve (`V1` → `V2`).

---

## 8. Migration Strategy (Legacy → Contract + Keys)

### Phase 1 – Inventory & Design

1. Run Hardcoded Path Indexer (if available).
2. Identify **shared**, **fragile**, or **high-churn** paths.
3. Define corresponding **Path Keys**.
4. Seed `config/path_index.yaml` with initial entries.

### Phase 2 – Implement Registry & Resolver

1. Implement or confirm `src/path_registry.py` and `paths-resolve` are working.
2. Add a small test suite:

   * Verify sample key resolution.
   * Verify registry schema validation.
3. Wire the resolver into relevant modules (no direct `open("spec/phase_docs/...")` in shared code).

### Phase 3 – Refactor Callers

1. For each target script/module:

   * Replace literal paths with calls to the resolver.
   * Ensure error handling is via **typed errors**, not `print` + exit.

2. Update tests to use keys as inputs where appropriate.

### Phase 4 – Enforce via Review & Checks

* Code review checklist must include:

  * “Does this cross a boundary? If so, is there a contract type?”
  * “Does this refer to an important resource path? If so, is there a key + registry entry?”
* Optional: add a CI check that:

  * Fails on newly introduced hard-coded paths in known sensitive directories.
  * Validates `config/path_index.yaml` schema.

---

## 9. Enforcement & Review Checklist

For **every PR** touching orchestrator, patterns, error engine, or automation scripts:

1. **Boundary check**

   * [ ] Orchestrator ↔ workers use contract types (`ExecutionRequestV1`, `ExecutionResultV1`, etc.).
   * [ ] Business logic ↔ environment go through environment adapters, not direct `subprocess`/`os` calls.
   * [ ] Error paths emit `ErrorEventV1` into the error engine.

2. **Path usage check**

   * [ ] No new hard-coded paths to important docs/configs/scripts.
   * [ ] New important resources have a Path Key in `config/path_index.yaml`.
   * [ ] Code uses `resolve_path("key")` or `paths-resolve key`.

3. **API stability**

   * [ ] Public functions and DTOs are clearly documented.
   * [ ] Internal helpers are `_`-prefixed.
   * [ ] Any breaking change to public API is versioned (`V2`) rather than silently mutated.

---

## 10. Quick Reference

### 10.1 When to Add Abstraction

* Crossing **module / subsystem boundaries** → **YES**.
* Talking to **Git / FS / DB / OS** → via environment abstraction → **YES**.
* Switching between tools (Aider, Codex, custom) → via contracts → **YES**.
* Handling errors centrally → via `ErrorEventV1` → **YES**.
* Referencing important repo resources → via **Path Keys** → **YES**.

### 10.2 When Not to

* Single, local module with no external callers → **probably NO**.
* One-off, throwaway scripts → **NO**, unless promoting to infra.
* Tiny helpers that will never be shared → **NO**.

### 10.3 Path Abstraction Summary

* **DON’T**

  * Hard-code `"spec/phase_docs/PH-02_State_Layer.md"` in scripts.
  * Scatter doc paths across dozens of prompts and tools.

* **DO**

  * Introduce a key like `phase_docs.ph02_state_layer_spec`.
  * Map it in `config/path_index.yaml`.
  * Use `resolve_path("phase_docs.ph02_state_layer_spec")` or `paths-resolve phase_docs.ph02_state_layer_spec`.

---

## 11. Relationship to Other Docs

This SSOT replaces and governs:

* `DOC-GUIDE-UET-ABSTRACTION-GUIDELINES-MD-001`
* `DOC-GUIDE-PATH-ABSTRACTION-INDIRECTION-LAYER-473`

Those documents may remain in the repo as **historical / supporting** material, but any conflicts must be resolved in favor of **this SSOT**.

When adding new modules, tools, or specs:

1. Decide whether they introduce a **new boundary** or **new important paths**.
2. Update this SSOT and `config/path_index.yaml` accordingly.
3. Make sure UET contracts and Path Keys remain the **only** abstractions crossing those boundaries.

```

