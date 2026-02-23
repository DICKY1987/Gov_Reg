## Instructions for AI: Modify the “Purpose Mapping / Capability Mapping” plan to update the existing SSOT registry (NOT create a parallel registry)

### Objective

Change the plan so `CAPABILITIES.json`, `FILE_INVENTORY.jsonl`, and `FILE_PURPOSE_REGISTRY.json` become **derived/evidence artifacts**, and the **authoritative state is written into the existing registry files located at**:

`C:\Users\richg\Gov_Reg\REGISTRY`

This must follow your patch/ingest philosophy: **no “new registry” living in `.state/…` as SSOT**.

---

## 0) Hard rules (must follow)

1. **Do NOT create a new “registry of record”** under `.state/purpose_mapping/`.
   `.state/...` outputs may exist only as **evidence/derivation artifacts**.
2. **All durable truth must be written into the existing registry files** under `C:\Users\richg\Gov_Reg\REGISTRY`.
3. **Patch-only mutation** (RFC-6902). No in-place hand edits to registry JSON.
4. **Descriptive metadata goes to the file registry**, not the governance registry (governance is rules/policy).

---

## 1) Locate the authoritative registry files (in the given folder)

In `C:\Users\richg\Gov_Reg\REGISTRY`, detect these files (use existence checks; do not assume names beyond patterns):

**Primary file registry (choose 1):**

* Prefer: `01999000042260124503*_REGISTRY*.json` (the unified file registry)
* Fallback: `master_registry.json`

**Column dictionary (needed for adding/using headers):**

* `*_COLUMN_DICTIONARY.json`

**Governance registry (do not write descriptive mappings here):**

* `*governance_registry*.json` and/or `*COMPLETE_SSOT*.json`

Record the resolved paths in the updated plan as explicit variables:

* `REGISTRY_ROOT`
* `FILE_REGISTRY_PATH`
* `COLUMN_DICTIONARY_PATH`
* `GOVERNANCE_REGISTRY_PATH` (read-only for this plan)

---

## 2) Modify the plan: rename the role of the three mapping outputs

Update the plan text so it explicitly states:

### These are **derived artifacts (evidence), not SSOT**

* `.state/purpose_mapping/CAPABILITIES.json`
* `.state/purpose_mapping/FILE_INVENTORY.jsonl`
* `.state/purpose_mapping/FILE_PURPOSE_REGISTRY.json`

### New authoritative deliverables (SSOT updates)

* **RFC-6902 patch set(s)** that update `FILE_REGISTRY_PATH`
* (If needed) a **RFC-6902 patch** that updates `COLUMN_DICTIONARY_PATH` to add required headers
* Evidence bundle proving registry changed deterministically:

  * `before_snapshot.json`
  * `after_snapshot.json`
  * `patch.json`
  * `apply_result.json`
  * `diff_summary.json`

Add a new section in the plan called: **“Registry Integration (SSOT Write-Back)”**.

---

## 3) Add one new step to the plan: “Generate and Apply Registry Patches”

Insert a new step after the current Step 3:

### Step 4 — Registry Integration (SSOT Write-Back)

This step must do all of the following:

#### 4.1 Build a “registry update intent” from derived outputs

Input:

* `FILE_PURPOSE_REGISTRY.json`
* `FILE_INVENTORY.jsonl`
* Existing registry snapshot from `FILE_REGISTRY_PATH`

Action:

* For each file mapping in `FILE_PURPOSE_REGISTRY.json`, resolve the target registry record by:

  1. `file_id` if present in the mapping
  2. else `relative_path` (exact match)
* If a mapped file cannot be found in the registry:

  * mark it as a **blocking error** unless the plan also includes an ingest path to add missing files.

#### 4.2 Column strategy (use existing headers if possible; otherwise patch column dictionary)

Minimum required fields to store in SSOT (choose the closest existing headers first):

* `one_line_purpose` (short purpose string)
* `py_capability_tags` (array of tags, python-specific)
* `py_capability_facts_hash` (deterministic hash of extracted capability facts)

If the plan needs new fields (example: `capability_ids`, `capability_primary`, `purpose_evidence_ref`):

* Add them by generating a **RFC-6902 patch** to `COLUMN_DICTIONARY_PATH`
* Mirror those headers into the registry’s `column_headers` section if your registry stores headers internally

Rules:

* **append-only** (never renumber / never reorder existing header identifiers)
* default presence: OPTIONAL unless you have a gate that demands it

#### 4.3 Generate RFC-6902 patch operations against the file registry

Output:

* `O01_promotion_patch.json` (or equivalent patch filename)

Patch rules:

* Minimal patches only (no rewrite of unrelated sections)
* Stable ordering (sort target file records by `file_id`, tie-break by `relative_path`)
* Store new fields directly on the record kind you’re updating (likely the `entity` record for `entity_kind=file`, or your canonical file record—use whatever is already used consistently in your registry)

#### 4.4 Apply patches using the registry ingest/apply mechanism

The updated plan must specify exact commands, using the resolved paths. Use this pattern:

```bash
# 1) snapshot before
python registry_tools/snapshot.py --in "%FILE_REGISTRY_PATH%" --out ".state/evidence/purpose_mapping/before_snapshot.json"

# 2) apply column dictionary patch (if any)
python registry_tools/apply_patch.py --target "%COLUMN_DICTIONARY_PATH%" --patch ".state/purpose_mapping/patch_column_dictionary.json" --evidence ".state/evidence/purpose_mapping/"

# 3) apply registry patch
python registry_tools/apply_patch.py --target "%FILE_REGISTRY_PATH%" --patch ".state/purpose_mapping/patch_file_registry.json" --evidence ".state/evidence/purpose_mapping/"

# 4) snapshot after
python registry_tools/snapshot.py --in "%FILE_REGISTRY_PATH%" --out ".state/evidence/purpose_mapping/after_snapshot.json"

# 5) diff summary
python registry_tools/diff_snapshots.py --before ".state/evidence/purpose_mapping/before_snapshot.json" --after ".state/evidence/purpose_mapping/after_snapshot.json" --out ".state/evidence/purpose_mapping/diff_summary.json"
```

If your repo already uses a different ingestion entrypoint (example: `registry/ingest_mutations.py`), the plan must:

* call that existing entrypoint instead of inventing new ones
* still produce the same evidence artifacts listed above

#### 4.5 Write evidence outputs

Must write:

* patch files actually applied
* snapshots before/after
* deterministic counts:

  * number of records updated
  * number of files mapped
  * number of unmapped files (must be zero or explicitly allowed by policy)

---

## 4) Update plan “Success Criteria” so it proves SSOT integration occurred

Replace/extend success criteria so it is impossible to “pass” while still being a parallel registry:

Minimum success criteria:

1. `FILE_REGISTRY_PATH` changes are present and validated (hash changed, diff summary non-empty).
2. Every mapped file in `FILE_PURPOSE_REGISTRY.json` is reflected in the SSOT registry fields:

   * `one_line_purpose` populated when provided
   * capability tag fields populated when applicable
3. Determinism check:

   * re-run Step 4 without changing inputs must produce **identical patch** (or empty patch) and identical diff summary (excluding timestamps in evidence files, if any).
4. Evidence bundle exists and is complete.

---

## 5) Update plan “Outputs” section (final form)

In the plan, rewrite the outputs list to this exact intent:

### Derived/Evidence Outputs (non-authoritative)

* `.state/purpose_mapping/CAPABILITIES.json`
* `.state/purpose_mapping/FILE_INVENTORY.jsonl`
* `.state/purpose_mapping/FILE_PURPOSE_REGISTRY.json`

### SSOT Updates (authoritative)

* Patched `C:\Users\richg\Gov_Reg\REGISTRY\<file_registry>.json`
* (Optional) Patched `C:\Users\richg\Gov_Reg\REGISTRY\<column_dictionary>.json`

### Evidence Bundle

* `.state/evidence/purpose_mapping/before_snapshot.json`
* `.state/evidence/purpose_mapping/after_snapshot.json`
* `.state/evidence/purpose_mapping/patch_file_registry.json`
* `.state/evidence/purpose_mapping/patch_column_dictionary.json` (if used)
* `.state/evidence/purpose_mapping/apply_result.json`
* `.state/evidence/purpose_mapping/diff_summary.json`

---

## 6) Final required edit: explicitly state “no separate registry”

Add a short, explicit paragraph in the plan:

* “`FILE_PURPOSE_REGISTRY.json` is not SSOT. It is a derived report used to generate patches applied to the SSOT registry under `C:\Users\richg\Gov_Reg\REGISTRY`.”

---

 a concrete rewritten version of the affected plan sections (Step outputs + new Step 4 + success criteria)     