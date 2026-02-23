# Plan: Capability Registry System

## Context

The repo has 1,267 Python files, each with a `# DOC_ID:` header but no machine-readable component/capability mapping. There is no way to answer "what implements capability X?" without tribal knowledge. This plan introduces a two-layer enforcement system: a **SSOT taxonomy file** + **mandatory `__script_meta__` blocks** + an **AST-based validator CLI** that produces inventory/coverage reports and fails CI on missing or invalid mappings.

This builds on-and fits inside-the existing governance infrastructure (SSOT_System, ci_gate.py, enforcement_bridge.py). All paths in this plan are repo-relative to `C:\Users\richg\Gov_Reg`; `--root` must point inside the repo to avoid scanning or writing outside it.

---

## New Files to Create

### 1. `01260207201000001172_Governance\capability_registry\DOC-CONFIG-CAPABILITY-REGISTRY-{ID}__CAPABILITY_REGISTRY.json`
The SSOT taxonomy. Authoritative component/capability list. Never edited directly—only via structured updates.

Structure:
```json
{
  "schema_version": "1.0.0",
  "generated_at_utc": "...",
  "components": {
    "ID_SYSTEM": {
      "description": "Document ID allocation, scanning, validation, migration",
      "capabilities": {
        "allocate_id": "Mint new doc_id values into the registry",
        "scan_tree": "Walk the file tree and discover doc_id assignments",
        "validate_ids": "Check doc_id uniqueness and format compliance",
        "migrate_ids": "Rename files or update references during migration",
        "reconcile_counters": "Re-sync registry numeric counters after bulk ops"
      }
    },
    "REGISTRY": {
      "description": "YAML/JSON registry CRUD for artifacts, patterns, templates, etc.",
      "capabilities": {
        "read_registry": "...",
        "write_registry": "...",
        "query_registry": "...",
        "validate_registry": "..."
      }
    },
    "GOVERNANCE": { ... },
    "SSOT": { ... },
    "AUTOMATION": { ... },
    "ORCHESTRATION": { ... },
    "EVIDENCE": { ... },
    "TEMPLATE_OPS": { ... },
    "PROVENANCE": { ... },
    "PATH_REGISTRY": { ... },
    "ENVIRONMENT": { ... },
    "MONITORING": { ... },
    "ERROR_RECOVERY": { ... },
    "TESTING": { ... }
  }
}
```

---

### 2. `01260207201000001172_Governance\capability_registry\DOC-CORE-CAPABILITY-INVENTORY-{ID}__capability_inventory.py`
The enforcement CLI. Uses `ast.parse()` only — never executes scripts.

**Commands:**
```
python capability_inventory.py scan [--root PATH] [--out-dir PATH]
python capability_inventory.py validate [--strict]
python capability_inventory.py report [--format md|json]
```

**Logic:**
1. Glob `**/*.py` under `--root`, skip `__pycache__`, `.git`, `.venv`, `venv`, `site-packages`, `dist`, `build`, `.mypy_cache`, `.pytest_cache`, `.tox`, `node_modules`, `*.pyi`, and explicit test/fixture patterns (e.g., `*/tests/*`, `*/test*/*`, `*/fixtures/*`)
2. AST-parse each file; on parse failure record a warning (error with `--strict`) and continue; otherwise look for a top-level `__script_meta__` assignment
3. Validate:
   - All required fields present (`component`, `capability`, `script_id`)
   - `script_id` matches the `# DOC_ID:` header
   - `component` key exists in `CAPABILITY_REGISTRY.json`
   - `capability` key exists under that component
   - No file declares two primary capabilities (enforced by schema)
4. Emit three artifacts:
   - `SCRIPT_INVENTORY.jsonl` — one line per script
   - `CAPABILITY_COVERAGE_REPORT.md` — matrix: component/capability → file list
   - `DEFECT_REPORT.jsonl` — missing meta, invalid component, bad capability, duplicates

**Exit codes:** 0=clean, 1=defects found (CI hard-fail)

---

### 3. `01260207201000001172_Governance\capability_registry\DOC-CORE-CAPABILITY-META-STUB-{ID}__generate_meta_stubs.py`
One-shot backfill generator. The **existing registries do not contain component/capability data** in the functional sense — they only have doc_id, type-category, and file paths. So this generator uses **directory path heuristics** to make a best-effort component inference, which is far better than blanket UNKNOWN:

| Directory pattern | Inferred component |
|---|---|
| `*/doc_id/*`, `*/id_registry*` | `ID_SYSTEM` |
| `*/GOVERNANCE/*`, `*/01260207201000001172_Governance/*` | `GOVERNANCE` |
| `*/ssot/*`, `*/SSOT*` | `SSOT` |
| `*/AI_CLI_PROVENANCE*` | `PROVENANCE` |
| `*/path_registry/*`, `*/path_abstraction/*` | `PATH_REGISTRY` |
| `*/environment_manager/*` | `ENVIRONMENT` |
| `*/artifacts/*` | `EVIDENCE` |
| `*/automation/*`, `*/codegen/*` | `AUTOMATION` |
| `*/engine/*`, `*/executor*`, `*/scheduler*` | `ORCHESTRATION` |
| `*/monitoring/*`, `*/metrics/*` | `MONITORING` |
| `*/recovery/*`, `*/error_engine/*` | `ERROR_RECOVERY` |
| `*/templates/*` | `TEMPLATE_OPS` |
| `*/test*`, `*/tests/*` | `TESTING` |

The inserted stub includes a `meta_confidence` field: `"inferred"` (auto-mapped from path) or `"confirmed"` (human-set). Placement rules: preserve encoding cookie and module docstring; insert `__script_meta__` after any module docstring and any `from __future__` imports.

```python
__script_meta__ = {
    "script_id": "<DOC_ID from header>",
    "component": "ID_SYSTEM",       # inferred from path — confirm or correct
    "capability": "UNKNOWN",        # requires human review
    "meta_confidence": "inferred",  # change to "confirmed" after review
    "entrypoints": [],
    "inputs": [],
    "outputs": [],
    "evidence_kind": [],
}
```

Validation behavior:
- `component: "UNKNOWN"` or `capability: "UNKNOWN"` → **warning** (not hard failure) in default mode
- `--strict` flag upgrades these to **errors**; flip to strict once coverage >= 90% confirmed
- `meta_confidence: "inferred"` counts as warning in reports but not a defect
- AST parse failures are warnings by default and errors with `--strict`

---

### 4. (Optional) `01260207201000001172_Governance\capability_registry\DOC-CONFIG-CAPABILITY-TOOLS-{ID}__CAPABILITY_TOOLS.json`
Execution-plane mapping: `{component, capability}` → runnable command + expected artifacts + evidence rules. Enables `orchestrator.run("REGISTRY", "validate_registry")` instead of hard-coding script paths.

---

## Modified Files

### `01260207201000001172_Governance\ssot\SSOT_System\SSOT_SYS_ci\DOC-CORE-SSOT-SYS-CI-CI-GATE-1095__ci_gate.py`
Add a new gate step (Layer 6: Capability Coverage) that calls `capability_inventory.py validate`. Follows the existing 5-layer gate pattern.

---

## Implementation Sequence

1. **Define taxonomy** — author `CAPABILITY_REGISTRY.json` with all components and their capability verbs
2. **Build inventory CLI** - `capability_inventory.py` (AST scanner + validator + report emitter)
3. **Add unit tests** - cover docstring/future-import placement, skip list behavior, and `script_id` vs `# DOC_ID:` mismatch
4. **Build stub generator** - `generate_meta_stubs.py` (inserts UNKNOWN stubs into all files missing meta)
5. **Run stub generator** - produces stubs across all 1,267 files
6. **Validate** - run `capability_inventory.py validate`; expect 0 hard failures (stubs satisfy schema), many warnings for UNKNOWN values
7. **Integrate CI gate** - add Layer 6 step to `ci_gate.py`; run without `--strict` until backfill is complete
8. **Incremental backfill** - fill real `component`/`capability` values in high-value scripts; flip to `--strict` once coverage is at least 90%

---

## Key Reuse (Existing Infrastructure)

| Existing file | Reuse |
|---|---|
| `SSOT_SYS_tools/validate_automation_spec.py` | Pattern for validator class structure |
| `SSOT_SYS_ci/ci_gate.py` | Gate integration point |
| `doc_id_registry_cli.py` | DOC_ID minting for new files |
| `governance/enforcement_bridge.py` | Pre/post hook model if needed |
| `artifact_metadata_v1.schema.json` | Schema pattern for `__script_meta__` fields |

---

## Verification

```powershell
# 1. Confirm CAPABILITY_REGISTRY.json is valid JSON
python -c "import json; json.load(open('CAPABILITY_REGISTRY.json'))"

# 2. Run full scan against repo
python capability_inventory.py scan --root C:\Users\richg\Gov_Reg

# 3. Check outputs
Get-Content SCRIPT_INVENTORY.jsonl | ForEach-Object { ($_ | ConvertFrom-Json).component } | Sort-Object | Group-Object | ForEach-Object { "{0} {1}" -f $_.Count, $_.Name }

# 4. View coverage report
Get-Content CAPABILITY_COVERAGE_REPORT.md

# 5. Confirm CI gate passes
python ci_gate.py
```
Note: PowerShell 5+ recommended for `ConvertFrom-Json`.

---

## Notes

- Existing registries (DOC_ID YAML, artifact registry, pattern registry) contain no component/capability data. The stub generator derives component from directory path heuristics (high accuracy) and leaves capability as UNKNOWN for human review.
- `meta_confidence: "inferred"` lets the inventory CLI surface a clean audit list of files needing human confirmation without blocking CI.
- New files must follow the DOC_ID naming convention; actual IDs to be minted during implementation using `doc_id_registry_cli.py mint`.
