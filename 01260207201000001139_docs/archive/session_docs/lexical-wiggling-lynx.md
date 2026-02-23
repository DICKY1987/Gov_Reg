# Plan: Apply NEWPHASE_TEMPLATE_PROCESS Classification Rules (Phase A)

## Context
The AI Refactor Instructions JSON (`Downloads\ChatGPT-AI Refactor Instructions.json`) was just updated to
replace the over-broad `TEMPLATE_OPERATIONS` category with `NEWPHASE_TEMPLATE_PROCESS`, which targets
ONLY files associated with `NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3`. The goal is to now
execute Phase A of that instruction set for this category: scan, classify, produce MOVE_MAP +
HUMAN_MOVE_REVIEW, and patch the registry — without moving any files.

---

## Key Facts (from exploration)

| Fact | Detail |
|------|--------|
| Destination root exists | `C:\Users\richg\Gov_Reg\newPhasePlanProcess\` with `.dir_id` → `01260207201000001177` |
| Template file | `newPhasePlanProcess\01260207201000000510_NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3.json` |
| LP_LONG_PLAN\newPhasePlanProcess | Does NOT exist — seed path B is N/A |
| Expand-set scan result | Zero matches outside `newPhasePlanProcess\` for all 7 reference literals |
| All 4 destination roots | Confirmed present and ID-prefixed |
| Unified registry | `Gov_Reg\01260207201000001250_REGISTRY\01999000042260124503_REGISTRY_file.json` |
| Registry field for module | `module_id` exists in `column_headers`; do NOT add `module_dir_id` |
| Registry path issue | Registry records likely still point to stale `LP_LONG_PLAN\newPhasePlanProcess\` paths → triggers `MISMATCH_REGISTRY_VS_FS` |
| Prior run | Feb 15 TEMPLATE_OPERATIONS run exists at `Gov_Reg\MOVE_MAP.json` + `Gov_Reg\EVIDENCE_BUNDLE\` |
| False positive | `01260207201000001288_sections\01260207233100000434_UNIFIED_MASTER_TEMPLATE_V1_PART2.yml` — had "TEMPLATE" in name, correctly excluded by new rules |

---

## Implementation Plan

### Step 1 — Git branch
```bash
cd C:\Users\richg\Gov_Reg
git checkout -b refactor/newphase-template-process-phase-a
```

### Step 2 — Write the Phase A script

**File to create:**
`C:\Users\richg\Gov_Reg\SSOT_REFACTOR\phase_a_newphase_template_process.py`

**Script must do (in order):**

1. **Init**: Generate `run_id` (timestamp + uuid6), create output dir
   `C:\Users\richg\Gov_Reg\SSOT_REFACTOR\run_NEWPHASE_<YYYYMMDD_HHMMSS_hex6>\`
   Write `EVIDENCE_BUNDLE\run_manifest.json`.

2. **Load registry** (`01999000042260124503_REGISTRY_file.json`): build `file_id → record` dict.

3. **Scan seed set** (Group B path signal):
   - Recurse `Gov_Reg\newPhasePlanProcess\` — all files, including subdirs.
   - Skip `.state\`, `__pycache__`, `.git`, `*.pyc`, `*.bak`, `*.log`.
   - Check LP_LONG_PLAN\newPhasePlanProcess path — skip if non-existent (it doesn't exist).

4. **Expand set scan**: recurse all of `Gov_Reg\` outside `newPhasePlanProcess\`, search for
   any of the 7 strings. Expect zero results; include in report to formally prove empty.

5. **False-positive detection**: find all files outside `newPhasePlanProcess\` whose filenames
   contain `TEMPLATE` (case-insensitive). For each, verify no NPP references → mark `CORRECTLY_EXCLUDED`.

6. **Classify each candidate** using Groups A–D + explicit exclusions. Every file under
   `newPhasePlanProcess\` passes Group B → `NEWPHASE_TEMPLATE_PROCESS`. Record `match_signals[]`.

7. **Eligibility check** per file:
   - Extract `file_id` from 20-digit filename prefix (`\d{20}_` or `P_\d{20}_`).
   - If no prefix → search registry by `artifact_path`/`absolute_path` match.
   - If still not found → `SKIPPED_NO_ID`.
   - Validate `file_id` is exactly 20 digits; else `INVALID_ID_FORMAT`.
   - Registry lookup: compare `relative_path` vs actual path → if mismatch → `MISMATCH_REGISTRY_VS_FS`.
   - Read current `module_id` from registry record.
   - `move_enabled = False` always in Phase A.

8. **Hash all candidates** (SHA-256) → `EVIDENCE_BUNDLE\before_snapshot\file_hashes.json`.

9. **Write MOVE_MAP.json** (see schema below). All `dest_relpath == source_relpath` (files already
   at destination).

10. **Write REFERENCE_INDEX.json** — empty (`references: []`) since no paths change.

11. **Write REWRITE_PATCHSET\manifest.json** — `plan_count: 0`, empty `plans\` dir.

12. **Registry patch** (ELIGIBLE records only — skip MISMATCH):
    - Back up registry: `01999000042260124503_REGISTRY_file.json.backup.<run_id>`.
    - Build RFC-6902 patch ops for `module_id` → `"01260207201000001177"` on each ELIGIBLE record.
    - Apply in memory, write updated registry, write `EVIDENCE_BUNDLE\diffs\registry.patch.rfc6902.json`.
    - Report MISMATCH records separately as `REGISTRY_PATH_CORRECTION_NEEDED`.

13. **Validate registry** (post-patch): file_id uniqueness, relative_path uniqueness, module_id
    populated for ELIGIBLE cohort → `EVIDENCE_BUNDLE\reports\validation_report.md`.

14. **Write all reports** (see output list below).

15. **Write HUMAN_MOVE_REVIEW.md** → **STOP** (no moves executed).

---

## MOVE_MAP.json Schema (key fields)

```json
{
  "schema_version": "1.1.0",
  "generated_utc": "...",
  "run_id": "...",
  "repo_root": "C:\\Users\\richg\\Gov_Reg",
  "category_scope": "NEWPHASE_TEMPLATE_PROCESS",
  "dir_id_resolution": {
    "NEWPHASE_TEMPLATE_PROCESS": {
      "abs_path": "C:\\Users\\richg\\Gov_Reg\\newPhasePlanProcess",
      "dir_id": "01260207201000001177",
      "dir_id_source": ".dir_id metadata file"
    }
  },
  "counts_by_category": { "NEWPHASE_TEMPLATE_PROCESS": N },
  "counts_by_eligibility": { "ELIGIBLE": N, "MISMATCH_REGISTRY_VS_FS": N, "SKIPPED_NO_ID": N },
  "moves": [
    {
      "entity_type": "file",
      "file_id": "<20digits>",
      "source_relpath": "newPhasePlanProcess/...",
      "dest_dir_id": "01260207201000001177",
      "dest_dir_relpath": "newPhasePlanProcess",
      "dest_relpath": "newPhasePlanProcess/...",
      "category": "NEWPHASE_TEMPLATE_PROCESS",
      "confidence": "HIGH",
      "matched_group": "B",
      "match_signals": ["path_under:Gov_Reg\\newPhasePlanProcess"],
      "move_enabled": false,
      "eligibility_status": "ELIGIBLE|MISMATCH_REGISTRY_VS_FS|SKIPPED_NO_ID",
      "module_id_current": "...",
      "module_id_target": "01260207201000001177"
    }
  ]
}
```

---

## Output Directory Structure

```
Gov_Reg\SSOT_REFACTOR\run_NEWPHASE_<id>\
  MOVE_MAP.json
  REFERENCE_INDEX.json                     ← references: []
  REWRITE_PATCHSET\
    manifest.json                          ← plan_count: 0
    plans\                                 ← empty
  EVIDENCE_BUNDLE\
    run_manifest.json
    before_snapshot\
      file_hashes.json
    reports\
      inventory_consistency_report.md
      classification_report.md             ← includes false-positive analysis
      move_plan_report.md
      HUMAN_MOVE_REVIEW.md                 ← final stop artifact
      rewrite_plan_report.md               ← explains zero rewrites
      registry_patch_report.md             ← includes MISMATCH list
      validation_report.md
    diffs\
      registry.patch.rfc6902.json
    logs\
      errors.jsonl
```

---

## Critical Files

| File | Role |
|------|------|
| `Gov_Reg\01260207201000001250_REGISTRY\01999000042260124503_REGISTRY_file.json` | Registry to query + patch |
| `Gov_Reg\newPhasePlanProcess\.dir_id` | Authoritative source for `dir_id = "01260207201000001177"` |
| `Gov_Reg\MOVE_MAP.json` | Prior Feb 15 run — cross-reference to avoid overwriting |
| `Downloads\ChatGPT-AI Refactor Instructions.json` | Governs all field names, schema contracts, eligibility rules |

---

## Key Architectural Decisions

| Decision | Reason |
|----------|--------|
| Use `module_id` field (not `module_dir_id`) | Registry `column_headers` already has `module_id`; only add new column if absent |
| Output to isolated `SSOT_REFACTOR\run_<id>\` | Prevents overwriting the Feb 15 `Gov_Reg\MOVE_MAP.json` and `Gov_Reg\EVIDENCE_BUNDLE\` |
| `source_relpath == dest_relpath` for all records | Files already at destination; MOVE_MAP is still required to prove classification and provide registry patch basis |
| MISMATCH_REGISTRY_VS_FS blocks `module_id` patch | Patching `module_id` on a stale `relative_path` creates half-corrected state; report these but skip them in the patch |
| Invoke with `py` launcher | `python` and `python3` are not on PATH; use `py phase_a_newphase_template_process.py` |

---

## Verification Checklist

1. **All Phase A output files exist** (13 files/dirs listed in output structure above)
2. **MOVE_MAP.json**: zero records with `move_enabled: true`; all `category = "NEWPHASE_TEMPLATE_PROCESS"` (not `"TEMPLATE_OPERATIONS"`)
3. **REFERENCE_INDEX.json**: `references: []`
4. **Registry backup** exists: `...REGISTRY_file.json.backup.<run_id>`
5. **registry.patch.rfc6902.json**: all ops target `/files/N/module_id` only
6. **Validation report**: `PASS` for uniqueness gates; MISMATCH files listed under separate section
7. **No file moves**: `git status` shows no changes to `newPhasePlanProcess\` contents
8. **Before-snapshot hashes match** current disk state for all candidates
9. **False positive check**: `UNIFIED_MASTER_TEMPLATE_V1_PART2.yml` listed as `CORRECTLY_EXCLUDED`
10. **Expand-set result**: zero files outside `newPhasePlanProcess\` classified as `NEWPHASE_TEMPLATE_PROCESS`
