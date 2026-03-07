<!-- DOC_LINK: DOC-ID-GOVERNANCE-REQ-001 -->
---
doc_id: DOC-ID-GOVERNANCE-REQ-001
title: ID System Governance Requirements
status: active
version: 1.0.0
owner: id_system
created: 2025-12-25
derived_from: ChatGPT-ID system review.md
authority: constitutional
---

# ID System Governance Requirements

## Document Purpose

This document extracts and formalizes the **key design decisions, requirements, and invariants** for the ID system based on the comprehensive design conversation documented in `ChatGPT-ID system review.md`.

This is a **constitutional document** under the governance model - it defines non-negotiable rules that all other system components must honor.

---

## Implementation Status

**Document Status:** Constitutional (Authoritative)
**System Maturity:** Partial Implementation
**Last Updated:** 2025-12-31

### ID Type Implementation Matrix

| ID Type | Status | Registry Location | Tooling | Notes |
|---------|--------|-------------------|---------|-------|
| **doc_id** | ✅ **Operational** | `5_REGISTRY_DATA/DOC_ID_REGISTRY.yaml` | `doc_id_scanner.py`, `doc_id_assigner.py`, validators | **Fully implemented** - 100% coverage (2,624/2,625 files) |
| **pattern_id** | 🚧 **Planned** | `patterns/PATTERN_REGISTRY.yaml` | TBD | Governance defined, implementation pending |
| **module_id** | 🚧 **Planned** | `SUBSYSTEM_CATALOG.yaml` | TBD | Governance defined, implementation pending |
| **run_id** | ✅ **Operational** | Generated at runtime | UUID v4 / ULID | Used for execution tracing and determinism |
| **event_id** | 🚧 **Planned** | Runtime only | TBD | Governance defined, implementation pending |

### Current Capabilities

**✅ Fully Operational:**
- `doc_id` scanning and assignment
- Registry management (YAML-based)
- Format validation and uniqueness checking
- Coverage reporting (100% as of 2025-12-31)
- Git hooks and file watchers
- Multi-tier architecture (Tier 0-2)

**🚧 Governance-Defined (Implementation Pending):**
- `pattern_id` tracking
- `module_id` system
- `event_id` observability
- Tier 3 semantic analysis
- Advanced conflict resolution

### Compliance Status

| Requirement | Status | Evidence |
|-------------|--------|----------|
| R-ID-001: Primary identity type | ✅ Compliant | `doc_id` fully implemented |
| R-ID-002: Identity type taxonomy | ⚠️ Partial | Only `doc_id` and `run_id` operational |
| R-ID-003: ULID usage constraints | ✅ Compliant | `run_id` uses UUID v4 (compatible) |
| Immutability invariants | ✅ Compliant | No doc_id reassignment logic |
| SSOT integration | ✅ Compliant | Registry managed via patches |
| Coverage enforcement | ✅ Compliant | 100% coverage achieved |

### Artifact ID Examples

The following artifact IDs are used for project management within the doc_id system itself:

- **WORK-REGV3-001**: Work package for Registry V3 implementation
- **A-REGV3-001**: Artifact ID for V3 schema definition
- **A-REGV3-002**: Artifact ID for V3 migration tools

**Format Pattern:**
- **WORK-\<system>-\<seq>**: Work package IDs (project management)
- **A-\<system>-\<seq>**: Artifact IDs (deliverable tracking)
- **DOC-\<category>-\<name>-\<seq>**: Document IDs (file tracking)

---

## 1. Core Identity Types

### R-ID-001: Primary Identity Type
**Requirement:** `doc_id` is the **single, primary identity type** for cross-artifact linkage.
- **Applies to:** Documents, code files, specs, binaries
- **Format:** `DOC-<SYSTEM>-<DOMAIN>-<KIND>-<SEQ>`
- **Rationale:** Unified identity model prevents fragmentation and enables deterministic mapping

### R-ID-002: Identity Type Taxonomy
**Requirement:** The system SHALL support the following ID types:
```yaml
doc_id:      # Document/artifact-level identity
  format: "DOC-<SYSTEM>-<DOMAIN>-<KIND>-<SEQ>"
  scope: individual files
  cardinality: one per file

pattern_id:  # Pattern suite identity
  format: "PATTERN-<CATEGORY>-<NAME>-<SEQ>"
  scope: pattern concept (shared across spec/executor/tests)
  cardinality: one per pattern, many files per pattern

module_id:   # Architectural module identity
  format: "MOD-<SYSTEM>-<LAYER>-<NAME>"
  scope: semantic module/submodule
  cardinality: one per module concept

run_id:      # Execution run identity
  format: "RUN-<ULID>" or "RUN-<SYSTEM>-<DATE>-<SEQ>"
  scope: single autonomous pipeline run
  cardinality: one per orchestration run

event_id:    # Event/step identity
  format: ULID
  scope: atomic events in ledgers
  cardinality: one per event
```

### R-ID-003: ULID Usage Constraints
**Requirement:** ULIDs SHALL be used **only** for:
- Pipeline run identifiers (`run_id`)
- Event identifiers (`event_id`) in JSONL ledgers
- State snapshots where time-ordering is critical

**Prohibition:** ULIDs MUST NOT be used as primary document identity when structured `doc_id` is appropriate.

**Rationale:** Overuse of non-semantic IDs muddies the system and reduces agent/human comprehension.

---

## 2. Immutability and Stability Invariants

### R-ID-010: ID Immutability
**Requirement:** Once assigned, an ID (doc_id, pattern_id, module_id) MUST:
- Never be reused for a different artifact/concept
- Never have its semantic meaning changed
- Remain stable across path moves, renames, and refactors

**Exception:** None. This is an absolute invariant.

### R-ID-011: IDs Represent Concepts, Not Paths
**Requirement:** IDs MUST represent **conceptual identity**, not implementation details.

**Prohibitions:**
- ❌ Encoding exact filesystem paths in ID strings
- ❌ Encoding version numbers in ID strings
- ❌ Encoding technology choices in ID strings (e.g., `_PY`, `_TS`)

**Metadata Storage:** Volatile details (paths, versions, tech stack) MUST be stored as:
```yaml
doc_id: DOC-AIM-ENV-HEALTH-001
current_path: "modules/aim_environment/health_01001B.py"
previous_paths:
  - "modules/aim_scheduler/health.py"
version: "2.1.0"
language: "python"
```

### R-ID-012: ID Grammar Stability
**Requirement:** The ID grammar MUST be:
- Simple and regular (easy to parse/validate)
- Consistent across ID types
- Documented in `ID_TAXONOMY.yaml`

**Format Constraints:**
- Uppercase letters, digits, and hyphens only
- Fixed slot structure (type-system-domain-kind-sequence)
- No sprawling sentence-length slugs

---

## 3. Canonical Placement Rules

### R-ID-020: Placement by File Type
**Requirement:** Every refactor-participating file MUST have exactly one `doc_id` in the canonical location for its type:

```yaml
Markdown:
  location: YAML frontmatter
  format: |
    ---
    doc_id: DOC-...
    pattern_id: PATTERN-...  # if applicable
    module_id: mod....   # if applicable
    ---

Python/PowerShell:
  location: top-of-file comment
  format: |
    # DOC_ID: DOC-...
    # PATTERN_ID: PATTERN-...
    # MODULE_ID: mod....

Binaries:
  location: sidecar .meta.json
  format: |
    {
      "doc_id": "DOC-...",
      "module_id": "mod....",
      "kind": "diagram"
    }
```

### R-ID-021: Python Module Naming Safety
**Requirement:** Python module filenames MUST follow PEP-8:
- Start with letter or underscore (NOT digit)
- Use lowercase with underscores
- Snapshot/ULID codes MAY appear as **suffixes only**

**Valid:**
- ✅ `health_01001B.py`
- ✅ `scheduler_00001A.py`

**Invalid:**
- ❌ `01001B_health.py` (import breaks)
- ❌ `00001A_scheduler.py` (import breaks)

**Rationale:** This prevents the `01001B_health.py` import failure incident.

### R-ID-022: ID Storage Location
**Requirement:** IDs MUST live in:
1. Canonical in-file locations (frontmatter/headers)
2. Central registries (DOC_ID_REGISTRY.yaml, MODULE_REGISTRY.yaml)
3. Mapping files (doc_id_mapping.json)

IDs MUST NOT be used as:
- Raw Python import names
- Bare directory names (use in metadata, not paths)

---

## 4. Single Source of Truth

### R-ID-030: Central Registry Authority
**Requirement:** All `doc_id` minting MUST flow through:
- The central doc_id registry + CLI (`doc_id_registry_cli.py`)
- During orchestration: through `IDCoordinator` (which delegates to registry)

**Prohibition:** Worktrees, agents, and ad-hoc scripts MUST NOT mint IDs independently.

### R-ID-031: Registry Structure
**Requirement:** The registry MUST maintain:
```yaml
doc_id: DOC-AIM-ENV-HEALTH-001
name: "AIM Environment Health Module"
system: AIM
domain: ENV
kind: module
current_path: "modules/aim_environment/health_01001B.py"
previous_paths: []
status: active  # active | retired | superseded
created_at: "2025-11-29T10:00:00Z"
last_modified_at: "2025-12-25T15:30:00Z"
module_id: mod.aim.environment
derived_from: null
superseded_by: null
```

### R-ID-032: Inventory Sync
**Requirement:** `docs_inventory.jsonl` MUST be kept in sync with:
- Registry state
- On-disk file metadata
- Via incremental updates after each merge

**Format:**
```jsonl
{"path": "core/state/db.py", "doc_id": "DOC-CORE-STATE-DB-001", "module_id": "mod.core.state", "last_assigned_at": "2025-12-25T15:30:00Z"}
```

---

## 5. Worktree Orchestration Rules

### R-ID-040: Worktree ID Isolation
**Requirement:** Worktrees MUST NOT mint `doc_id`s directly.

**Orchestration Flow:**
1. **Pre-orchestration:** IDCoordinator assigns doc_ids on MAIN
2. **Worktree creation:** Copies files with IDs already present
3. **ID injection:** WorktreeManager syncs IDs into worktree copies
4. **AI tool execution:** Operates on files with stable IDs
5. **Merge back:** No ID conflicts because IDs were pre-assigned centrally

### R-ID-041: Scanner Exclusions
**Requirement:** The Doc ID scanner MUST exclude:
```yaml
exclusions:
  - .git/
  - .venv/
  - __pycache__/
  - .worktrees/
  - .state/
  - node_modules/
  - .pytest_cache/
  - "*.db-shm"
  - "*.db-wal"
```

**Rationale:** Prevents scanner from seeing duplicate/transient copies during orchestration.

### R-ID-042: Workstream File Specifications
**Requirement:** Workstream specs MUST include:
```json
{
  "id": "ws-22",
  "name": "Pipeline Plus Phase 0 - Schema",
  "files_to_edit": [
    "core/state/db.py",
    "core/config/router.py"
  ],
  "files_to_create": [
    "schemas/pipeline_plus.yaml"
  ]
}
```

**Purpose:** Enables IDCoordinator to pre-assign IDs before worktree divergence.

---

## 6. Lifecycle and State Transitions

### R-ID-050: File Split
**Policy:**
- Primary file (retaining main behavior) SHOULD keep original `doc_id`
- New files MUST get new `doc_id`s with metadata:
  ```yaml
  derived_from: DOC-ORIGINAL-001
  ```

### R-ID-051: File Merge
**Policy:**
- Merged file MUST receive a new `doc_id`
- Original doc_ids are marked:
  ```yaml
  status: superseded
  superseded_by: DOC-MERGED-NEW-003
  ```

### R-ID-052: File Move/Rename
**Policy:**
- `doc_id` MUST NOT change
- Registry/inventory updated:
  ```yaml
  previous_paths:
    - "old/path/file.py"
  current_path: "new/path/file.py"
  ```

### R-ID-053: File Deletion
**Policy:**
- `doc_id` MUST be marked:
  ```yaml
  status: retired
  deleted_in_commit: "abc123def"
  deleted_at: "2025-12-25T20:00:00Z"
  ```
- ID MUST NOT be reused

---

## 7. Conflict Resolution Rules

### R-ID-060: Same File, Different doc_id
**Scenario:** Two branches independently assign different `doc_id`s to the same file.

**Policy:**
- First merged wins (becomes canonical)
- Second doc_id is rejected and logged
- Merge driver MUST keep first `doc_id`

### R-ID-061: Different Files, Same doc_id
**Scenario:** Two distinct files claim the same `doc_id`.

**Policy:**
- **Hard error** - system MUST reject this state
- Validation/scanner MUST detect and fail
- Operator MUST resolve by assigning new `doc_id` to one file

### R-ID-062: Conflict Detection
**Requirement:** CI/validation MUST include checks for:
- Duplicate `doc_id` values across distinct files
- `doc_id` format violations
- Missing `doc_id`s in Tier 1 files (configurable)

---

## 8. Coverage and Enforcement

### R-ID-070: Coverage Tiers
**Requirement:** The system SHALL support tiered coverage policies:

```yaml
tier_1_immediate:  # Must have IDs before orchestration
  - "modules/**/*.py"
  - "patterns/**"
  - "docs/**/*.md"

tier_2_on_demand:  # Get IDs when first touched
  - "tests/**"
  - "examples/**"

tier_3_never:      # Never need IDs
  - "__pycache__/**"
  - ".git/**"
  - ".worktrees/**"
```

### R-ID-071: Preflight Gates
**Requirement:** Before any module refactor, a preflight gate MUST:
1. Load `docs_inventory.jsonl`
2. Validate coverage for target modules
3. Check for ID format violations
4. **Fail** if coverage < threshold

**Gate Identifier:** `REFACTOR_GATE_001`

**Default Threshold:** 100% for Tier 1 modules

### R-ID-072: CI Integration
**Requirement:** CI pipelines MUST:
- Run scanner on every PR
- Validate ID grammar against `ID_TAXONOMY.yaml`
- Check for duplicate IDs
- Enforce coverage thresholds
- Fail builds on violations

---

## 9. Agent and Automation Protocols

### R-ID-080: Task ID References
**Requirement:** All task objects MUST include ID references:
```json
{
  "task_id": "TASK-001",
  "run_id": "RUN-01JH8T1QZQ...",
  "doc_ids": ["DOC-...", "DOC-..."],
  "pattern_ids": ["PATTERN-EXEC-..."],
  "module_id": "mod.core.state"
}
```

### R-ID-081: Event Logging
**Requirement:** Events in `.state/*.jsonl` MUST include:
```jsonl
{"event_id": "01JH8T...", "run_id": "RUN-...", "doc_id": "DOC-...", "action": "edit", "timestamp": "..."}
```

### R-ID-082: Agent Routing
**Requirement:** Agents SHOULD route operations based on ID prefixes/slots:
```python
if doc_id.startswith("DOC-AIM-"):
    route_to_aim_system()
elif doc_id.startswith("DOC-ERR-"):
    route_to_error_handler()
```

---

## 10. Implementation Requirements

### R-ID-090: IDCoordinator Implementation
**Requirement:** The orchestrator MUST implement `IDCoordinator` with:
- Thread-safe ID assignment (use `RLock`)
- Process-wide cache of assigned IDs
- Delegation to central registry for minting
- Incremental updates to `docs_inventory.jsonl`

### R-ID-091: Scanner Implementation
**Requirement:** The scanner (`doc_id_scanner.py`) MUST:
- Exclude `.worktrees/` and `.state/`
- Extract IDs from canonical locations
- Produce `docs_inventory.jsonl` and `DOC_ID_COVERAGE_REPORT.md`
- Support incremental updates (not just full scans)

### R-ID-092: Auto-Assigner Implementation
**Requirement:** The auto-assigner (`doc_id_assigner.py`) MUST:
- Read `docs_inventory.jsonl`
- Find files missing `doc_id`
- Call registry CLI to mint IDs
- Inject IDs into canonical locations
- Update inventory and registry

### R-ID-093: ID Taxonomy Definition
**Requirement:** The system MUST maintain `ID_TAXONOMY.yaml`:
```yaml
types:
  DOC:
    pattern: "DOC-<SYSTEM>-<DOMAIN>-<KIND>-<SEQ>"
    slots:
      SYSTEM: [AIM, CORE, ERR, PM, EXEC, TOOLING]
      DOMAIN: [description]
      KIND: [SPEC, GUIDE, TEST, EXEC, SCHEMA, PLAN]
      SEQ: "[0-9]{3}"

keys:
  SYSTEM:
    AIM: "AI Manager / Orchestrator"
    CORE: "Core engine / shared domain"
    ERR: "Error handling / resilience"
  KIND:
    SPEC: "Specification"
    TEST: "Test suite"
```

---

## 11. Validation and Testing

### R-ID-100: Format Validation
**Requirement:** All IDs MUST pass regex validation:
```python
DOC_ID_PATTERN = r"^DOC-[A-Z0-9]+-[A-Z0-9]+(-[A-Z0-9]+)*-[0-9]{3}$"
PAT_ID_PATTERN = r"^PATTERN-[A-Z0-9]+-[A-Z0-9]+-[0-9]{3}$"
MOD_ID_PATTERN = r"^MOD-[A-Z0-9]+-[A-Z0-9]+-[A-Z0-9]+$"
```

### R-ID-101: Uniqueness Validation
**Requirement:** The system MUST maintain uniqueness constraints:
- No two files may share the same `doc_id`
- Pattern files sharing `pattern_id` is allowed (by design)
- Module IDs must be unique across modules

### R-ID-102: Test Coverage
**Requirement:** The test suite MUST include:
- `test_doc_id_compliance.py` - validates format and uniqueness
- `test_id_coordinator.py` - validates thread-safety
- `test_scanner_exclusions.py` - validates `.worktrees/` excluded
- `test_lifecycle_rules.py` - validates split/merge/retire

---

## 12. Authority and Precedence

### R-ID-110: Document Authority
**Authority Chain** (highest to lowest):
1. **This document** (ID_SYSTEM_GOVERNANCE_REQUIREMENTS.md)
2. ID_WORKTREES_INTEGRATION_SPEC_V1.md
3. ID_TAXONOMY.yaml
4. TECHNICAL_SPECIFICATION_V2.1.md
5. Implementation code
6. Chat logs (reference only)

**Conflict Resolution:** In case of conflict, higher authority wins.

### R-ID-111: Amendment Process
**Requirement:** Changes to this document MUST:
1. Be proposed via documented RFC
2. Pass governance review
3. Update version number
4. Update all dependent documents
5. Be committed with clear rationale

---

## 13. Known Issues and Mitigations

### Issue 1: Python Import Safety
**Incident:** `01001B_health.py` broke imports (leading digits)

**Mitigation Applied:** R-ID-021 (Python module naming safety)

**Status:** Resolved - all numeric-prefixed modules renamed

### Issue 2: Scanner Including Worktrees
**Risk:** Scanner could see duplicate files across worktrees

**Mitigation Applied:** R-ID-041 (scanner exclusions)

**Status:** Resolved - exclusions already implemented

### Issue 3: Parallel ID Minting
**Risk:** Multiple worktrees minting IDs independently

**Mitigation Applied:** R-ID-040 (worktree ID isolation) + R-ID-090 (IDCoordinator)

**Status:** Design complete, implementation pending

---

## 14. Implementation Checklist

- [ ] **Phase 0: Formalize**
  - [ ] Create `ID_TAXONOMY.yaml`
  - [ ] Document ID grammar
  - [ ] Define ULID usage boundaries

- [ ] **Phase 1: Instrument**
  - [ ] Verify scanner exclusions
  - [ ] Generate initial inventory
  - [ ] Measure baseline coverage

- [ ] **Phase 2: Assign**
  - [ ] Implement `doc_id_assigner.py`
  - [ ] Reach 100% Tier 1 coverage
  - [ ] Commit baseline to main

- [ ] **Phase 3: Enforce**
  - [ ] Implement `REFACTOR_GATE_001`
  - [ ] Add CI checks
  - [ ] Wire into PR workflow

- [ ] **Phase 4: Registries**
  - [ ] Create `MODULE_REGISTRY.yaml`
  - [ ] Define split/merge metadata
  - [ ] Implement lifecycle tracking

- [ ] **Phase 5: Orchestration**
  - [ ] Implement `IDCoordinator` (thread-safe)
  - [ ] Update `WorktreeManager` integration
  - [ ] Add `files_to_edit` to workstream specs
  - [ ] Test parallel execution

---

## 15. References

**Authoritative Documents:**
- ChatGPT-ID system review.md (design rationale)
- ID_WORKTREES_INTEGRATION_SPEC_V1.md (integration spec)
- TECHNICAL_SPECIFICATION_V2.1.md (technical details)

**Related Systems:**
- SUB_DOC_ID/ (implementation directory)
- doc_id_registry_cli.py (minting authority)
- doc_id_scanner.py (inventory tool)

**Governance:**
- .github/copilot-instructions.md (5-Layer Governance Model)
- SYSTEM_DETERMINISM_CONTRACT.json (determinism rules)

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-12-25 | System | Initial extraction from design conversation |

---

**END OF DOCUMENT**
