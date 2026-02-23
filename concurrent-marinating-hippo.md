# Plan: Improve Script Capability Mapping Quality

## Context
The capability mapping system (4-step pipeline) exists and runs, but Step 4 (SSOT write-back) has
never been applied, and Step 3's rule engine is too blunt — most non-entrypoint files land in
`CAP-UNMAPPED-REVIEW` or a generic `CAP-LIB-SHARED_SUPPORT` bucket because the only signals
used are classification type, argparse presence, gate markers, and schema JSON. The ChatGPT
design conversation identifies the fix: add **system-boundary signal rules** (what files
read/write), a **bounded vocab** to prevent tag sprawl, and a **human override table** to pin
ambiguous cases. No per-script `__script_meta__` declarations; inference only.

---

## Phase 1 - Restore Steps 3 & 4 to the Active Source Tree

Steps 3 & 4 must exist in the active package. If missing, copy them from the archive. After
they exist, align imports so the orchestrator and package `__init__` reference the actual
filenames (the current `P_01260207233100000YYY_*` imports do not exist in this repo).

**Source (archive):**
- `C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY\archive\from_directories_consolidated\from_gov_reg_subdirs\scripts\capability_mapping\P_01260207201000000984_P_01260207233100000YYY_purpose_registry_builder.py`
- `C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY\archive\from_directories_consolidated\from_gov_reg_subdirs\scripts\capability_mapping\P_01260207201000000985_P_01260207233100000YYY_registry_promoter.py`

**Destination (active source):**
- `C:\Users\richg\Gov_Reg\01260207201000001289_src\01260207201000001290_capability_mapping\P_01260207201000000984_P_01260207233100000YYY_purpose_registry_builder.py`
- `C:\Users\richg\Gov_Reg\01260207201000001289_src\01260207201000001290_capability_mapping\P_01260207201000000985_P_01260207233100000YYY_registry_promoter.py`

Update `__init__.py` at the same package to export `PurposeRegistryBuilder` and `RegistryPromoter`.
Update the orchestrator imports (or add wrapper modules) so it imports the
`P_0126020720100000098x_*` modules that actually exist.

---

## Phase 2 - Create `COMPONENT_CAPABILITY_VOCAB.json`

Create a bounded label set (not a full contract — just valid labels to prevent tag sprawl).

**Location:** `C:\Users\richg\Gov_Reg\newPhasePlanProcess\01260207201000001223_schemas\COMPONENT_CAPABILITY_VOCAB.json`

```json
{
  "schema_version": "1.0",
  "components": ["REGISTRY", "IDS", "GOVERNANCE", "PLANNING", "TEMPLATE_OPS", "EVIDENCE", "ARCHIVE", "ORCHESTRATION", "QA"],
  "capabilities": {
    "REGISTRY":      ["VALIDATE", "SCAN", "PROMOTE", "PATCH_APPLY", "BUILD_INDEX"],
    "IDS":           ["ALLOCATE", "SCAN", "RECONCILE", "MIGRATE", "VALIDATE"],
    "GOVERNANCE":    ["VALIDATE", "EXTRACT_FACTS", "SCAN"],
    "PLANNING":      ["BUILD_INDEX", "VALIDATE"],
    "TEMPLATE_OPS":  ["EXTRACT_FACTS", "MIGRATE"],
    "EVIDENCE":      ["EMIT", "VALIDATE", "BUILD_INDEX"],
    "ARCHIVE":       ["ARCHIVE_MOVE", "MIGRATE", "SCAN"],
    "ORCHESTRATION": ["RUN", "VALIDATE"],
    "QA":            ["VALIDATE", "SCAN"]
  }
}
```

Wire this vocab into Step 3 by passing `vocab_path` to `PurposeRegistryBuilder`
(or by adding a default path resolution in the builder).

---

## Phase 3 - Create `SCRIPT_CLASSIFIER_OVERRIDES.json`

Human decision cache — empty initially, applied last to pin ambiguous scripts.

**Location:** `C:\Users\richg\Gov_Reg\newPhasePlanProcess\SCRIPT_CLASSIFIER_OVERRIDES.json`

```json
{
  "schema_version": "1.0",
  "note": "Keyed by file_id or stable relative path. Applied last, overrides inferred mapping.",
  "overrides": {}
}
```

Wire this overrides file into Step 3 by passing `overrides_path` to `PurposeRegistryBuilder`.
Because the inventory does not currently include `file_id`, use stable relative path keys
unless you add a file_id join step.

---

## Phase 4 — Improve Rule Engine in `purpose_registry_builder.py`

Extend `_map_files_to_capabilities` with new signal-based rules inserted **before** the
generic `python_module` fallback. All new rules should be based on system-boundary evidence
(what the file reads/writes/calls), not function names.

**File to edit:**
`C:\Users\richg\Gov_Reg\01260207201000001289_src\01260207201000001290_capability_mapping\P_01260207201000000984_P_01260207233100000YYY_purpose_registry_builder.py`

### New rules to add (in priority order after CLI check):

| Priority | Signal | Capability ID | Confidence |
|----------|--------|---------------|------------|
| 4a | `path_literals` contains `COUNTER_STORE` or `_ID_LEDGER` | `CAP-IDS-ALLOCATE` | high |
| 4b | `imports` contains `jsonschema` or `fastjsonschema` | `CAP-REGISTRY-VALIDATE` | high |
| 4c | `produces` (.state/evidence/ paths in path_literals) | `CAP-EVIDENCE-EMIT` | medium |
| 4d | `subprocess_calls` present AND `imports` contains orchestration modules | `CAP-ORCHESTRATION-RUN` | medium |
| 4e | `path_literals` contains archive keywords (`.archive`, `_backups`, `_ARCHIVE`) | `CAP-ARCHIVE-ARCHIVE_MOVE` | medium |
| 4f | `path_literals` contains registry SSOT file name | `CAP-REGISTRY-PATCH_APPLY` | medium |
| 4g | `defines` contains known GEU/REGISTRY vocabulary keywords | component-specific | medium |

### Also add:
- **Override application**: After all rules, check `SCRIPT_CLASSIFIER_OVERRIDES.json` and
  override `primary_capability_id` + `mapping_confidence="pinned"` if file_id/path is listed.
- **Vocab validation**: After mapping, warn (don't fail) if an assigned `capability_id` is not
  in `COMPONENT_CAPABILITY_VOCAB.json`.
- **Confidence breakdown**: Add a new field `signal_sources: List[str]` to each mapping record
  to explain which signals fired, supporting the "review queue with hints" model.
- **Import matching**: Treat dotted imports as matches (e.g., `jsonschema.validators`,
  `concurrent.futures`) by checking prefixes/contains, not only exact matches.
- **Vocab parsing**: Parse `CAP-<COMPONENT>-<CAPABILITY...>` where capability can include
  multiple tokens (e.g., `PATCH_APPLY`, `ARCHIVE_MOVE`, `EXTRACT_FACTS`) to avoid false warnings.
- **Warnings capture**: Record vocab warnings into the output `warnings` list, not only stdout.

---

## Phase 5 - Apply the SSOT Patch (Step 4)

After validating Step 3 output quality (check that `review_queue` count has decreased vs the
prior run), run Step 4 in apply mode:

```bash
python 01260207201000001276_scripts/P_01260207201000000934_P_01260207233100000XXX_capability_mapper.py \
  --step 3 --step 4 --registry-mode apply \
  --registry-root C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY
```

This promotes `py_capability_tags`, `py_capability_facts_hash`, and `one_line_purpose` into:
`C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY\01999000042260124503_REGISTRY_file.json`

Ensure `RegistryPromoter` imports the correct `apply_patch` implementation
(e.g., `01260207201000001250_REGISTRY\01260207201000001270_scripts\P_01260207201000000834_apply_patch.py`)
or adds the right `sys.path` entries.

---

## Critical Files

| File | Role |
|------|------|
| `01260207201000001289_src/01260207201000001290_capability_mapping/P_01260207201000000984_*_purpose_registry_builder.py` | **PRIMARY EDIT** — rule engine improvement |
| `01260207201000001289_src/01260207201000001290_capability_mapping/P_01260207201000000985_*_registry_promoter.py` | Restore from archive; no edits needed |
| `01260207201000001289_src/01260207201000001290_capability_mapping/P_01260207201000000979_*___init__.py` | Add exports for Steps 3 & 4 |
| `01260207201000001276_scripts/P_01260207201000000934_*_capability_mapper.py` | Orchestrator - verify it imports from correct paths |
| `newPhasePlanProcess/01260207201000001223_schemas/COMPONENT_CAPABILITY_VOCAB.json` | **CREATE** - bounded label set |
| `newPhasePlanProcess/SCRIPT_CLASSIFIER_OVERRIDES.json` | **CREATE** - human override cache |
| `01260207201000001250_REGISTRY/01999000042260124503_REGISTRY_file.json` | **WRITE TARGET** - SSOT registry (Step 4 apply) |
| `01260207201000001250_REGISTRY/01260207201000001270_scripts/P_01260207201000000834_apply_patch.py` | Patch applicator used by Step 4 |

---

## Verification

1. **Prereq**: Run Steps 1-2 or confirm `.state/purpose_mapping/CAPABILITIES.json` and
   `.state/purpose_mapping/FILE_INVENTORY.jsonl` exist.
2. **Dry-run Step 3**: Run `--step 3` only; compare `FILE_PURPOSE_REGISTRY.json` confidence
   distribution to prior run at `.state/purpose_mapping/`. Count of `CAP-UNMAPPED-REVIEW`
   should decrease.

3. **Check review_queue**: Open `FILE_PURPOSE_REGISTRY.json`, inspect the `review_queue` array.
   For each remaining low-confidence file, add a record to `SCRIPT_CLASSIFIER_OVERRIDES.json`
   to pin it.

4. **Dry-run Step 4**: Run `--step 4 --registry-mode dry-run`; inspect the generated RFC-6902
   patch at `.state/evidence/registry_integration/purpose_mapping/patch_ssot_purpose_mapping.rfc6902.json`.

5. **Apply**: Run `--registry-mode apply`; verify `01999000042260124503_REGISTRY_file.json`
   entries now have `py_capability_tags` set (not null/empty) and `py_capability_facts_hash`
   populated.

6. **Determinism check**: Run Steps 3-4 twice back-to-back; compare stable hashes (exclude
   `generated_at` timestamps or hash only the `mappings` + `review_queue` arrays).
