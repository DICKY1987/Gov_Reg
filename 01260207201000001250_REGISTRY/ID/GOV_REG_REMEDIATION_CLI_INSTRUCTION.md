# Gov_Reg File Identity Remediation CLI — Instruction Document

**Document Purpose:** Specification for a CLI tool (`govreg-remediate`) that resolves six categories of file identity problems across the Gov_Reg codebase.

**Scope:** 163 Python files spanning four naming schemes (P_, DOC-, date-prefixed, ungoverned plain).

**Produced:** 2026-03-30

---

## PART 1 — UNRESOLVED DESIGN QUESTIONS

The following decisions must be made before implementation begins. Each question lists the options considered and a recommended default, but the final answer depends on project-level policy that only the maintainer can set.

### DQ-1: Which ID survives in the dual-ID composite filenames?

Four files carry two 20-digit IDs concatenated in their name. The `get_file_id_from_name()` parser extracts only the first ID and silently drops the second. The analysis JSON reveals that `file_renamer.py` has `ids_match: false` — the body `file_id` is `01999000042260125010` (the second ID), not the first.

| File | First ID (parser sees) | Second ID | Body match? |
|---|---|---|---|
| `P_01260207201000000865_01999000042260130007_registry_patch_generator.py` | 01260207201000000865 | 01999000042260130007 | N/A (no body file_id) |
| `P_01260207201000000984_01999000042260130008_purpose_registry_builder.py` | 01260207201000000984 | 01999000042260130008 | N/A (no body file_id) |
| `P_01260207201000000985_01999000042260130009_registry_promoter.py` | 01260207201000000985 | 01999000042260130009 | N/A (no body file_id) |
| `P_01260207233100000365_01999000042260125010_file_renamer.py` | 01260207233100000365 | 01999000042260125010 | **Mismatch — body says 01999000042260125010** |

**Options:**

- **(A) Keep the first ID (what the parser already extracts).** Simpler — no parser changes needed. But for `file_renamer.py` this contradicts the body `file_id`.
- **(B) Keep the second ID (the `01999000042...` namespace).** Consistent with the body metadata for `file_renamer.py`, but the other three files have no body `file_id` to confirm.
- **(C) Decide per-file based on which ID has a registry entry.** Most correct but requires a registry lookup before renaming.

**Recommended default:** Option C — run the registry lookup as part of the remediation pre-check. If neither ID has a registry entry, keep the first and log a warning.

---

### DQ-2: What happens to the dropped ID from dual-ID files?

Once one ID is chosen as authoritative, the other still exists in the ID space. If it was ever referenced (in imports, registry entries, or cross-references), silently dropping it breaks those references.

**Options:**

- **(A) Create a cross-reference entry:** Add a registry record mapping `dropped_id → surviving_id` with status `ALIAS`.
- **(B) Grep-and-replace:** Find all references to the dropped ID in the codebase and rewrite them to the surviving ID.
- **(C) Both A and B:** Cross-reference for safety, then also do grep-and-replace so the alias is never actually needed at runtime.

**Recommended default:** Option C.

---

### DQ-3: P_ ID collision — which file keeps P_01999000042260125106?

Both `pre_commit_dir_id_check.py` and `registry_filesystem_reconciler.py` carry `file_id: "01999000042260125106"` in their body metadata. One must be reallocated.

**Options:**

- **(A) Reconciler keeps the ID; pre-commit hook gets a new one.** The reconciler is more complex and more deeply integrated.
- **(B) Pre-commit hook keeps the ID; reconciler gets a new one.** The pre-commit hook may be referenced in `.pre-commit-config.yaml` or git hook scripts by its current filename.

**Recommended default:** Option A — reallocate for the pre-commit hook. Verify no git hook configurations reference the old filename before renaming.

---

### DQ-4: DOC-SCRIPT collision resolution — who keeps the number?

Three DOC-SCRIPT numbers are each assigned to two files. The problem description states the manually-written scripts were assigned first and the generator-emitted validators collided afterward. Both files in each pair carry the same `doc_id` in their body metadata, so the metadata alone cannot disambiguate.

**Question:** Is there external evidence (commit history, allocation logs) confirming which file was assigned first? If not, should we default to keeping the number on the manually-written file (since the generator has a known counter bug)?

**Collision pairs:**

| Number | Manually-written file | Generator-emitted file |
|---|---|---|
| DOC-SCRIPT-0989 | `build_file_profiles.py` | `validate_rule_id.py` |
| DOC-SCRIPT-0992 | `validate_section_id.py` | `validate_alert_id.py` |
| DOC-SCRIPT-0993 | `consolidate_file_mappings.py` | `validate_artifact_id.py` |

**Recommended default:** Keep the number on the manually-written files. Reallocate for the generator-emitted validators. Fix the generator's counter logic so it checks existing DOC-SCRIPT assignments before emitting.

---

### DQ-5: Date-prefixed files — onboard to P_ or DOC-?

The date-prefixed files currently have no embedded `file_id` or `doc_id`. When onboarding them into the standard naming scheme, should they receive P_ IDs (20-digit numeric from the unified allocator) or DOC- IDs (from the doc_id registry)?

**Considerations from the analysis JSON:**

- The later-generation validators (`20420006`–`20420009`) import `shared.registry_config.REGISTRY_PATH` and use `argparse` — they behave like DOC-SCRIPT validators.
- The `2099900078...` and `2099900079...` files use `core.registry_store.RegistryStore` — they behave like P_-prefixed core scripts.
- The `20460001` and `20460002` validators use `shared.registry_config` and `argparse` — DOC-SCRIPT pattern.
- The `2026011820600003` identity system validator is a standalone validator using `csv`, `yaml`, and `pathlib`.

**Options:**

- **(A) All get P_ IDs.** Uniform, simple.
- **(B) Match the convention of similar files.** Validators matching DOC-SCRIPT patterns get DOC- IDs; core pipeline files get P_ IDs.
- **(C) All get DOC- IDs.** Consistent with their validator role.

**Recommended default:** Option B — classify by role and assign the matching scheme.

---

### DQ-6: Ungoverned shim files — keep or eliminate?

Three of the eight "plain" ungoverned files are compatibility shims (identified from the analysis JSON by their `importlib.util.spec_from_file_location` imports and empty `structure.functions` lists):

| Shim file | Forwards to | Exports |
|---|---|---|
| `validate_identity_sync.py` | `2099900078260118_validate_identity_sync.py` | `SyncValidator` |
| `validate_uniqueness.py` | `2099900079260118_validate_uniqueness.py` | `UniquenessValidator` |
| `DOC-SCRIPT-1325__id_core.py` | implementation in same directory | `id_core` namespace |

**Options:**

- **(A) Onboard shims with their own IDs, keep them permanently.** Import convenience preserved.
- **(B) Onboard shims now, schedule elimination.** Give them IDs immediately but mark them `status: DEPRECATED` and open a task to update all consumers to import the canonical module directly.
- **(C) Eliminate shims immediately.** Find all importers, rewrite them, delete the shims.

**Recommended default:** Option B — onboard now with DEPRECATED status. Immediate elimination (C) risks breaking things if any consumer is missed.

---

### DQ-7: Rollback granularity

Should rollback be per-category (one rollback artifact per remediation phase) or per-file (one rollback record per individual rename/reallocation)?

**Recommended default:** Per-category. Each phase produces a single `rollback_manifest.json` that can reverse the entire phase atomically. Per-file granularity adds complexity without clear benefit since partial rollbacks within a category would leave the system in an inconsistent state.

---

## PART 2 — CLI STRUCTURE

### Tool Name and Invocation

```
govreg-remediate <phase> [options]
```

Global options available on all phases:

| Option | Description |
|---|---|
| `--dry-run` | Show what would change without modifying anything |
| `--registry <path>` | Path to `REGISTRY_file.json` (auto-detected if omitted) |
| `--evidence-dir <path>` | Where to write rollback manifests and evidence (default: `.state/evidence/remediation/`) |
| `--verbose` | Print detailed operation log |
| `--force` | Skip confirmation prompts |

### Phase Overview

The tool operates in six phases, executed in order. Each phase is idempotent — running it twice produces the same result. Each phase gates on the previous phase's completion (checked via evidence files).

```
govreg-remediate phase1-collisions    # Fix DOC-SCRIPT + P_ ID collisions
govreg-remediate phase2-identical     # Delete byte-identical hash forks
govreg-remediate phase3-merge-forks   # Merge diverged hash forks into canonicals
govreg-remediate phase4-dual-ids      # Resolve dual-ID composite filenames
govreg-remediate phase5-superseded    # Retire date-prefixed superseded versions
govreg-remediate phase6-onboard       # Onboard ungoverned plain files
govreg-remediate status               # Show current remediation state
govreg-remediate rollback <phase>     # Reverse a completed phase
```

---

## PART 3 — PHASE SPECIFICATIONS

### Phase 1: Fix ID Collisions (`phase1-collisions`)

**Risk level:** CRITICAL
**Blocked by:** Nothing
**Resolves:** DQ-3 (P_ collision), DQ-4 (DOC-SCRIPT collisions)

**Targets:**

- DOC-SCRIPT-0989: `build_file_profiles.py` vs `validate_rule_id.py`
- DOC-SCRIPT-0992: `validate_section_id.py` vs `validate_alert_id.py`
- DOC-SCRIPT-0993: `consolidate_file_mappings.py` vs `validate_artifact_id.py`
- P_01999000042260125106: `pre_commit_dir_id_check.py` vs `registry_filesystem_reconciler.py`

**Steps performed:**

1. **Pre-check:** Load registry. Confirm the collisions still exist. Abort with exit 0 if already resolved.
2. **Allocate new IDs:** For each collision pair, allocate a fresh ID for the file being reassigned.
   - DOC-SCRIPT collisions: Call `doc_id_registry_cli.py mint` for the next available number.
   - P_ collision: Call `unified_id_allocator.allocate()` for the next P_ ID.
3. **Update body metadata:** In each reassigned file, find the `doc_id:` or `FILE_ID:` line and replace the old value with the new one.
4. **Rename file:** Change the filename to use the new ID prefix.
5. **Update registry entries:** Atomically: mark old entry `status: REASSIGNED`, create new entry with fresh ID and `status: active`.
6. **Patch generator:** In `DOC-SCRIPT-ID-GEN-VALIDATORS-992__generate_id_validators.py`, add a pre-emit check that queries existing DOC-SCRIPT assignments before handing out a number. This prevents recurrence.
7. **Grep references:** Search all `.py`, `.yaml`, `.json`, `.md` files for the old ID string. Write hits to `phase1_reference_scan.json`.
8. **Emit evidence.**

**Dry-run output format:**

```
[DRY RUN] Phase 1: Fix ID Collisions
  [COLLISION] DOC-SCRIPT-0989 → 2 files
    KEEP:       DOC-SCRIPT-0989__build_file_profiles.py (manual, priority)
    REASSIGN:   DOC-SCRIPT-0989__validate_rule_id.py → DOC-SCRIPT-XXXX__validate_rule_id.py
  [COLLISION] DOC-SCRIPT-0992 → 2 files
    KEEP:       DOC-SCRIPT-0992__validate_section_id.py
    REASSIGN:   DOC-SCRIPT-0992__validate_alert_id.py → DOC-SCRIPT-XXXX__validate_alert_id.py
  [COLLISION] DOC-SCRIPT-0993 → 2 files
    KEEP:       DOC-SCRIPT-0993__consolidate_file_mappings.py
    REASSIGN:   DOC-SCRIPT-0993__validate_artifact_id.py → DOC-SCRIPT-XXXX__validate_artifact_id.py
  [COLLISION] P_01999000042260125106 → 2 files
    KEEP:       P_01999000042260125106_registry_filesystem_reconciler.py
    REASSIGN:   P_01999000042260125106_pre_commit_dir_id_check.py → P_XXXXXXXXXXXXXXXXXXXX_pre_commit_dir_id_check.py
  [PATCH] generate_id_validators.py: add namespace collision check
  Total: 4 collisions, 4 reassignments, 1 generator patch
```

**Evidence outputs:**

```
.state/evidence/remediation/phase1_collisions/
  rollback_manifest.json
  completion_report.json
  reference_scan.json
  registry_pre_phase1.json
```

---

### Phase 2: Delete Identical Hash Forks (`phase2-identical`)

**Risk level:** LOW
**Blocked by:** Nothing (can run in parallel with Phase 1 but sequential execution is recommended)

**Targets:**

| Fork file (DELETE) | Canonical file (KEEP) |
|---|---|
| `P_01999000042260305004_patch_generator_5460db.py` | `P_01999000042260305004_patch_generator.py` |
| `DOC-CLI-DOC-ID-CLI-001__doc_id_cli_304439.py` | `DOC-CLI-DOC-ID-CLI-001__doc_id_cli.py` |
| `validate_identity_sync_278bdc.py` | `validate_identity_sync.py` |
| `validate_uniqueness_ce13c4.py` | `validate_uniqueness.py` |

**Steps performed:**

1. **Pre-check:** For each pair, compute SHA-256 of both files. Confirm they are byte-for-byte identical. If any pair has diverged since the original analysis, skip it and log a warning — it has become a Phase 3 candidate.
2. **Store content:** Write the full content of each fork to the rollback manifest (base64-encoded) so rollback can recreate them.
3. **Delete fork:** Remove the hash-suffixed file.
4. **Grep references:** Search for any imports or references to the deleted filename. Report hits.
5. **Emit evidence.**

**Rollback behavior:** Recreate deleted files from the stored content in the rollback manifest.

---

### Phase 3: Merge Diverged Hash Forks (`phase3-merge-forks`)

**Risk level:** HIGH
**Blocked by:** Phase 2 (to ensure identical forks are already cleared)

**Targets:**

| Canonical (MERGE INTO) | Fork (MERGE FROM, then DELETE) | Unique functionality in fork |
|---|---|---|
| `P_...305001_file_id_reconciler.py` | `..._2efb6c.py` | `promote_sha256_to_file_id()`, coverage metadata augmentation, `fail_closed: true` |
| `P_...305012_doc_id_resolver.py` | `..._21864a.py` | File-watcher exclusion filter, `generate_resolution_patches()`, `apply_resolutions()`, `backup_before_write: true` |
| `P_...305013_module_dedup.py` | `..._c3f244.py` | File-watcher exclusion filter, `generate_dedup_patches()`, `apply_deduplication()`, `backup_before_write: true` |

**Steps performed:**

1. **Pre-check:** Diff each fork against its canonical. Verify the fork adds substantive functionality (not just whitespace). If no substantive diff, redirect to Phase 2.
2. **Snapshot canonical:** Copy the canonical file to `.state/evidence/remediation/phase3_merge_forks/backups/` for rollback.
3. **Generate merge plan:** Produce a unified diff showing what would be added to the canonical. Save as `merge_plan_{base_name}.patch`.
4. **Prompt for review:** Unless `--force` is set, display the merge plan and require interactive confirmation. This is the highest-risk operation in the entire remediation.
5. **Apply merge:** Add the new functions/methods from the fork into the canonical. Specific additions per file:
   - `file_id_reconciler`: Add `promote_sha256_to_file_id()` method to `FileIDReconciler` class. Add coverage metadata augmentation in `run()`.
   - `doc_id_resolver`: Add `generate_resolution_patches()` and `apply_resolutions()` methods. Add file-watcher exclusion filter. Add `shutil` import.
   - `module_dedup`: Add `generate_dedup_patches()` and `apply_deduplication()` methods. Add file-watcher exclusion filter. Add `shutil` import.
6. **Validate:** Run `python -c "import ast; ast.parse(open('<canonical>').read())"` to confirm no syntax errors. Then run `python -c "import <canonical_module>"` if the import path is resolvable.
7. **Delete fork:** Remove the hash-suffixed file.
8. **Emit evidence.**

**Important implementation note:** The merge should NOT attempt automated AST-level splicing. The patch files are the deliverable. The `--force` flag applies patches without interactive confirmation but does NOT skip syntax validation.

---

### Phase 4: Resolve Dual-ID Composite Filenames (`phase4-dual-ids`)

**Risk level:** HIGH
**Blocked by:** Nothing (independent of Phases 1–3)
**Resolves:** DQ-1, DQ-2

**Targets:**

| Current filename | IDs present |
|---|---|
| `P_01260207201000000865_01999000042260130007_registry_patch_generator.py` | Two 20-digit IDs |
| `P_01260207201000000984_01999000042260130008_purpose_registry_builder.py` | Two 20-digit IDs |
| `P_01260207201000000985_01999000042260130009_registry_promoter.py` | Two 20-digit IDs |
| `P_01260207233100000365_01999000042260125010_file_renamer.py` | Two 20-digit IDs, body says second |

**Steps performed:**

1. **Pre-check:** For each dual-ID file:
   - Extract both IDs from the filename using regex `P_(\d{20})_(\d{20})_(.+)`.
   - Look up both IDs in the registry.
   - Read the body `file_id` metadata.
   - Apply decision logic: body metadata > registry match > first ID as fallback.
2. **Display resolution plan:** Show which ID survives and why, per file.
3. **Rename file:** `P_{surviving_id}_{base_name}.py`
4. **Update body metadata:** If the file has no `file_id` header, insert one. If it has one, confirm it matches the surviving ID.
5. **Create cross-reference:** Add an ALIAS registry entry: `dropped_id → surviving_id`, status `ALIAS`.
6. **Grep-and-replace:** Find all references to the old dual-ID filename AND the dropped ID. Update imports and string references. For the dropped ID specifically, replace with the surviving ID wherever it appears as a literal.
7. **Update internal imports:** `purpose_registry_builder.py` imports from `P_01260207201000000981_01999000042260130004_call_graph_builder` — another dual-ID module. If this file exists in the broader repo, add it to this phase's target list dynamically.
8. **Emit evidence.**

---

### Phase 5: Retire Superseded Date-Prefixed Versions (`phase5-superseded`)

**Risk level:** MEDIUM
**Blocked by:** Nothing (independent of Phases 1–4)
**Resolves:** DQ-5

**Targets — superseded pairs (RETIRE earlier, KEEP later):**

| Earlier version (RETIRE) | Later version (KEEP + ONBOARD) |
|---|---|
| `2026012100230004_validate_write_policy.py` | `2026012120420006_validate_write_policy.py` |
| `2026012100230005_validate_derivations.py` | `2026012120420007_validate_derivations.py` |
| `2026012100230006_validate_conditional_enums.py` | `2026012120420008_validate_conditional_enums.py` |
| `2026012100230009_validate_edge_evidence.py` | `2026012120420009_validate_edge_evidence.py` |

**Targets — standalone date-prefixed files (ONBOARD only, no supersession):**

| File | Classification |
|---|---|
| `2026011820600003_validate_identity_system.py` | DOC-SCRIPT validator |
| `2026012120460001_validate_module_assignment.py` | DOC-SCRIPT validator |
| `2026012120460002_validate_process.py` | DOC-SCRIPT validator |
| `2099900001260118_apply_ids_to_filenames.py` | P_ core script |
| `2099900078260118_validate_identity_sync.py` | P_ core script |
| `2099900079260118_validate_uniqueness.py` | P_ core script |

**Steps performed:**

1. **Pre-check:** Confirm both versions in each superseded pair still exist. Diff the pairs to verify the later version is a superset (or at minimum a distinct iteration).
2. **Archive earlier versions:** Move to `.state/archive/superseded/` with a metadata sidecar recording:
   - Original filename
   - Superseded by (later filename)
   - Archive timestamp
   - SHA-256 at time of archival
3. **Classify surviving and standalone files:** Per DQ-5 (Option B), assign each file to P_ or DOC- based on its role classification and import patterns (drawn from the analysis JSON's `dependencies.third_party` and `role_classification` fields).
4. **Allocate IDs:** For DOC-SCRIPT classified files, mint via `doc_id_registry_cli.py`. For P_ classified files, allocate via `unified_id_allocator.py`.
5. **Rename surviving files:** Apply the new ID prefix, dropping the date prefix.
6. **Update body metadata:** Insert `file_id` and/or `doc_id` headers matching the new allocation.
7. **Update registry:** Create entries for all newly onboarded files.
8. **Emit evidence.**

**Note on sentinel range:** The `2099...` prefix appears to be a sentinel/placeholder convention (possibly indicating "future" or "deferred" files). The completion report should document this observation.

---

### Phase 6: Onboard Ungoverned Plain Files (`phase6-onboard`)

**Risk level:** MEDIUM
**Blocked by:** Phase 5 (shim targets are renamed by Phase 5)
**Resolves:** DQ-6

**Targets:**

| File | Role | Shim? | Notes |
|---|---|---|---|
| `file_id_resolver.py` | Resolver | No | Identity-chain critical; `fail_closed: true` |
| `install_automation.py` | Setup helper | No | Has body `file_id: 01999000042260125114` already |
| `registry_pruning.py` | Registry writer | No | |
| `repo_root_resolver.py` | Resolver | No | `fail_closed: true` |
| `validate_repo_tree_overlay.py` | Validator | No | |
| `test_last_mile_integration.py` | Test | No | |
| `validate_identity_sync.py` | Shim | **Yes** | Forwards to `2099900078...` (now renamed by Phase 5) |
| `validate_uniqueness.py` | Shim | **Yes** | Forwards to `2099900079...` (now renamed by Phase 5) |

**Steps performed:**

1. **Pre-check:** Confirm Phase 5 evidence exists. Confirm each target file still exists. For `install_automation.py`, note it already has body `file_id: 01999000042260125114` — verify this ID is not colliding with any existing P_-prefixed filename.
2. **For non-shim files:**
   - If body already contains a `file_id` (like `install_automation.py`), use that ID. Otherwise allocate a new P_ ID.
   - Rename: `P_{file_id}_{base_name}.py`
   - If body lacked `file_id`, insert the header.
   - Create registry entry with `status: active`.
3. **For shim files (per DQ-6, Option B):**
   - Allocate P_ ID.
   - Rename: `P_{file_id}_{base_name}.py`
   - **Update the shim's import target:** The `spec_from_file_location` call inside the shim currently points at the old `2099...` filename. Update it to point at the Phase 5 renamed canonical (e.g., the new P_ or DOC-SCRIPT filename).
   - Create registry entry with `status: DEPRECATED`.
   - Log deprecation notice: "Consumers should import from `P_{canonical_id}_...` directly."
4. **Grep references:** For each renamed file, search for all imports/references to the old plain name. Write hits to `phase6_reference_scan.json`.
5. **Emit evidence.**

**Priority note:** `file_id_resolver.py` should be processed first within this phase. It is a critical identity-chain component (SHA-256 → file_id resolution) that currently has no identity of its own. Its analysis JSON shows `fail_closed: true` and `lock_file_usage: true` — it is production infrastructure operating outside governance.

---

## PART 4 — ROLLBACK PROTOCOL

### Manifest Format

Every phase writes a `rollback_manifest.json` BEFORE making any changes. The manifest is the first file created and the last thing validated.

```json
{
  "phase": "phase1-collisions",
  "executed_at": "2026-03-30T14:22:00Z",
  "tool_version": "1.0.0",
  "operations": [
    {
      "sequence": 1,
      "type": "rename",
      "old_path": "DOC-SCRIPT-0989__validate_rule_id.py",
      "new_path": "DOC-SCRIPT-1400__validate_rule_id.py",
      "old_body_id": "DOC-SCRIPT-0989",
      "new_body_id": "DOC-SCRIPT-1400"
    },
    {
      "sequence": 2,
      "type": "delete",
      "path": "P_01999000042260305004_patch_generator_5460db.py",
      "content_sha256": "abc123def456...",
      "content_backup_path": ".state/evidence/remediation/backups/patch_generator_5460db.py"
    },
    {
      "sequence": 3,
      "type": "body_edit",
      "path": "some_file.py",
      "old_content_sha256": "...",
      "old_content_backup_path": ".state/evidence/remediation/backups/some_file.py.pre_edit"
    }
  ],
  "registry_snapshot_path": ".state/evidence/remediation/registry_pre_phase1.json"
}
```

### Rollback Command

```
govreg-remediate rollback <phase-name>
```

Behavior:

1. Load the phase's `rollback_manifest.json`.
2. Verify the phase was actually completed (check for `completion_report.json`).
3. Reverse every operation in **reverse sequence order** (last change undone first).
4. Restore the registry from `registry_snapshot_path`.
5. Write `phase{N}_rollback_executed.json` as evidence.

Rollback does NOT cascade. Rolling back Phase 3 does not automatically roll back Phases 4–6. If downstream phases depend on Phase 3's results, they must be rolled back first (the tool enforces this ordering).

---

## PART 5 — STATUS COMMAND

```
govreg-remediate status
```

**Output:**

```
Gov_Reg File Identity Remediation Status
=========================================

Phase 1 — ID Collisions (CRITICAL)
  Status:     NOT STARTED
  Targets:    4 collision pairs (3 DOC-SCRIPT + 1 P_)
  Blocked by: None

Phase 2 — Identical Hash Forks (LOW)
  Status:     NOT STARTED
  Targets:    4 byte-identical copies to delete
  Blocked by: None

Phase 3 — Diverged Hash Forks (HIGH)
  Status:     NOT STARTED
  Targets:    3 diverged forks with orphaned code to merge
  Blocked by: Phase 2

Phase 4 — Dual-ID Filenames (HIGH)
  Status:     NOT STARTED
  Targets:    4 composite-name files to resolve
  Blocked by: None

Phase 5 — Superseded Date-Prefixed (MEDIUM)
  Status:     NOT STARTED
  Targets:    4 superseded pairs to archive + 7 files to onboard
  Blocked by: None

Phase 6 — Ungoverned Plain Files (MEDIUM)
  Status:     NOT STARTED
  Targets:    8 files to onboard (6 standalone + 2 shims)
  Blocked by: Phase 5

Overall: 0/6 phases complete, 30 files requiring action
```

Phase status values: `NOT STARTED`, `IN PROGRESS` (manifest written, not yet complete), `COMPLETE`, `FAILED` (gate check failed), `ROLLED BACK`.

---

## PART 6 — VALIDATION GATES

After each phase completes its operations, the tool runs a validation gate before writing the completion report. All gates must pass for the phase to be marked `COMPLETE`.

| Gate ID | Check | Applies to |
|---|---|---|
| GATE-UNIQUE | No duplicate IDs across all filenames and body metadata | All phases |
| GATE-SYNC | Every modified file's filename ID matches its body `file_id`/`doc_id` | Phases 1, 4, 5, 6 |
| GATE-SYNTAX | `ast.parse()` succeeds for every modified `.py` file | All phases |
| GATE-REGISTRY | Every renamed file has a valid registry entry; no orphaned entries for deleted files | All phases |
| GATE-REFS | Grep for old filenames/IDs returns zero error-level hits | All phases |

Gate behavior:

- **Pass:** Phase marked `COMPLETE`.
- **Warn:** Phase marked `COMPLETE` with warnings logged in evidence.
- **Fail:** Phase marked `FAILED`. Operator must resolve failures. Re-run the phase to retry gates.
- **`--force` override:** Gates that fail are marked as `ACKNOWLEDGED_RISK` in evidence. Phase proceeds to `COMPLETE`.

---

## PART 7 — EVIDENCE CHAIN

### Directory Structure

```
.state/evidence/remediation/
  phase1_collisions/
    rollback_manifest.json
    operations_log.jsonl
    completion_report.json
    reference_scan.json
    validation_gate_results.json
    registry_pre_phase1.json
    backups/
      <original files before modification>
  phase2_identical/
    ...
  phase3_merge_forks/
    ...
    merge_plans/
      merge_plan_file_id_reconciler.patch
      merge_plan_doc_id_resolver.patch
      merge_plan_module_dedup.patch
    backups/
      <pre-merge canonical files>
  phase4_dual_ids/
    ...
  phase5_superseded/
    ...
  phase6_onboard/
    ...
```

### Evidence File Requirements

Every evidence file must include:

- `tool_version`: Version of `govreg-remediate` that produced it.
- `executed_at`: ISO 8601 UTC timestamp.
- `phase`: Phase identifier string.
- `operator`: System username or `--operator` flag value.

Each JSON evidence file has a detached `.sha256` sidecar containing the SHA-256 of the JSON content, enabling tamper detection during audit.

### Operations Log Format

The `operations_log.jsonl` file contains one JSON object per line, recording every filesystem and registry mutation:

```jsonl
{"seq":1,"op":"rename","from":"DOC-SCRIPT-0989__validate_rule_id.py","to":"DOC-SCRIPT-1400__validate_rule_id.py","at":"2026-03-30T14:22:01Z"}
{"seq":2,"op":"body_edit","file":"DOC-SCRIPT-1400__validate_rule_id.py","field":"doc_id","old":"DOC-SCRIPT-0989","new":"DOC-SCRIPT-1400","at":"2026-03-30T14:22:01Z"}
{"seq":3,"op":"registry_update","entry_id":"DOC-SCRIPT-0989__validate_rule_id","action":"status_change","old_status":"active","new_status":"REASSIGNED","at":"2026-03-30T14:22:02Z"}
```

---

## PART 8 — EXECUTION CHECKLIST

Recommended execution order with manual checkpoints:

```
1. [ ] Run: govreg-remediate status
       Verify all 30 target files are detected.

2. [ ] Run: govreg-remediate phase1-collisions --dry-run
       Review reassignment plan. Confirm DQ-3 and DQ-4 decisions.

3. [ ] Run: govreg-remediate phase1-collisions
       Check: phase1_reference_scan.json for stale references.

4. [ ] Run: govreg-remediate phase2-identical --dry-run
       Verify all 4 pairs still byte-identical.

5. [ ] Run: govreg-remediate phase2-identical

6. [ ] Run: govreg-remediate phase3-merge-forks --dry-run
       Review the 3 merge plan patches carefully.

7. [ ] Run: govreg-remediate phase3-merge-forks
       MANUAL: Review merged files. Run any existing test suite.

8. [ ] Run: govreg-remediate phase4-dual-ids --dry-run
       Review ID survival decisions. Confirm DQ-1 resolution per file.

9. [ ] Run: govreg-remediate phase4-dual-ids

10.[ ] Run: govreg-remediate phase5-superseded --dry-run
       Review classification assignments (P_ vs DOC-). Confirm DQ-5.

11.[ ] Run: govreg-remediate phase5-superseded

12.[ ] Run: govreg-remediate phase6-onboard --dry-run
       Verify shim import targets updated to Phase 5 names.

13.[ ] Run: govreg-remediate phase6-onboard

14.[ ] Run: govreg-remediate status
       Confirm: "6/6 phases complete, 0 files requiring action"

15.[ ] Run full validator suite against remediated codebase.

16.[ ] Git commit with message:
       "remediate: complete 6-phase file identity cleanup (govreg-remediate v1.0)"
```

---

## PART 9 — EXIT CODES

| Code | Meaning |
|---|---|
| `0` | Phase completed successfully (or dry-run completed) |
| `1` | Phase failed — validation gate did not pass |
| `2` | Pre-check failed — target files missing, phase already complete, or dependency phase not done |
| `3` | Configuration error — registry not found, evidence directory not writable |
| `4` | User abort — operator declined interactive confirmation |
| `5` | Rollback failed — manifest missing or corrupted |
| `10` | Internal error — unhandled exception (stack trace written to evidence dir) |

All phases write their exit code into `completion_report.json` regardless of success or failure, so downstream automation can parse outcomes without relying on process exit codes alone.

---

## PART 10 — PREREQUISITES & SETUP

### Runtime Requirements

- Python 3.10+ (for `match` statement support in merge patch generation)
- Read/write access to the Gov_Reg repository root
- Read/write access to the registry file (`REGISTRY_file.json` or as configured)
- The unified ID allocator's `COUNTER_STORE.json` must be accessible and writable
- `git` available on PATH (used by reference scanning to detect staged files)

### Pre-flight Verification

Before the first run, the tool performs automatic pre-flight checks:

```
govreg-remediate preflight
```

This verifies:

1. **Registry reachable:** Can read and parse the registry JSON.
2. **Allocator functional:** Can read `COUNTER_STORE.json` and verify the lock mechanism works.
3. **Evidence directory writable:** Can create `.state/evidence/remediation/` if it doesn't exist.
4. **File inventory matches:** The 163-file inventory matches what's on disk. Reports any files added, removed, or renamed since the analysis JSON was produced.
5. **No in-progress phases:** Checks for any phase left in `IN PROGRESS` state from a prior interrupted run.

### Configuration File (Optional)

If a file named `.govreg-remediate.json` exists in the repository root, it overrides defaults:

```json
{
  "registry_path": "01999000042260124503_REGISTRY_file.json",
  "counter_store_path": "COUNTER_STORE.json",
  "evidence_dir": ".state/evidence/remediation",
  "archive_dir": ".state/archive/superseded",
  "decisions": {
    "DQ-1": "C",
    "DQ-2": "C",
    "DQ-3": "A",
    "DQ-4": "manual_first",
    "DQ-5": "B",
    "DQ-6": "B",
    "DQ-7": "per_category"
  },
  "phase5_classifications": {
    "2026011820600003_validate_identity_system.py": "DOC-SCRIPT",
    "2026012120460001_validate_module_assignment.py": "DOC-SCRIPT",
    "2026012120460002_validate_process.py": "DOC-SCRIPT",
    "2099900001260118_apply_ids_to_filenames.py": "P_ID",
    "2099900078260118_validate_identity_sync.py": "P_ID",
    "2099900079260118_validate_uniqueness.py": "P_ID"
  }
}
```

The `decisions` block locks in answers to the design questions from Part 1. If a decision is not present in the config, the tool uses the recommended default and logs a notice.

---

## PART 11 — MERGE PATCH FORMAT (PHASE 3)

Phase 3 is the highest-risk operation. The merge patches it generates follow a structured format to enable human review.

### Patch File Structure

Each `merge_plan_{base_name}.patch` is a JSON file (not a unified diff) with explicit insertion points:

```json
{
  "canonical_file": "P_01999000042260305001_file_id_reconciler.py",
  "fork_file": "P_01999000042260305001_file_id_reconciler_2efb6c.py",
  "canonical_sha256": "...",
  "fork_sha256": "...",
  "additions": [
    {
      "type": "method",
      "class": "FileIDReconciler",
      "name": "promote_sha256_to_file_id",
      "insert_after": "def run(self, ...)",
      "source_lines": [120, 185],
      "code": "    def promote_sha256_to_file_id(self, sha256: str, file_id: str) -> bool:\n        ..."
    },
    {
      "type": "import",
      "statement": "from typing import Optional",
      "insert_at": "imports_block"
    },
    {
      "type": "block",
      "description": "Coverage metadata augmentation in run()",
      "insert_after_line_containing": "# Build mappings",
      "code": "        # Coverage metadata\n        if self.coverage_tracking:\n            ..."
    }
  ],
  "behavioral_changes": [
    "Adds fail_closed=True default (fork has it, canonical does not)",
    "Adds coverage metadata dict to reconciliation output"
  ],
  "new_imports": ["shutil"],
  "risk_notes": [
    "promote_sha256_to_file_id() writes to SHA256_TO_FILE_ID.json — verify path is correct post-merge",
    "Coverage metadata augmentation modifies the return value shape of run()"
  ]
}
```

### Review Protocol

When `--force` is NOT set, Phase 3 displays each merge plan and prompts:

```
═══════════════════════════════════════════════════════════
MERGE PLAN: file_id_reconciler (2efb6c fork → canonical)
═══════════════════════════════════════════════════════════

Additions:
  [1] METHOD  FileIDReconciler.promote_sha256_to_file_id()  (65 lines)
  [2] BLOCK   Coverage metadata augmentation in run()        (12 lines)
  [3] IMPORT  shutil                                         (1 line)

Behavioral changes:
  • Adds fail_closed=True default
  • Modifies return value shape of run()

Risk notes:
  ⚠ promote_sha256_to_file_id() writes to SHA256_TO_FILE_ID.json
  ⚠ Coverage metadata augmentation modifies the return value shape

Apply this merge? [y/N/view/skip]
  y     - Apply merge
  N     - Abort entire phase
  view  - Show full code for each addition
  skip  - Skip this file, continue to next
```

### Post-Merge Validation

After each merge is applied:

1. `ast.parse()` on the merged file (syntax gate)
2. Compare the merged file's class/function list against the union of canonical + fork (structural gate)
3. Verify no function from the canonical was removed or overwritten (regression gate)

---

## PART 12 — EDGE CASES & ERROR HANDLING

### Interrupted Execution

If the tool is interrupted mid-phase (kill signal, power loss, crash):

- The `rollback_manifest.json` was written BEFORE any mutations, so it is always available.
- The `operations_log.jsonl` records each completed operation. On restart, the tool reads the log, skips already-completed operations, and resumes from the interruption point.
- Phase status is `IN PROGRESS` until the completion report is written. The `status` command will show this state.

### File Locked by Another Process

If a file cannot be renamed or written because another process holds a lock:

- The tool retries once after a 2-second delay.
- On second failure, it logs the error, skips that file, and continues.
- The skipped file is recorded in `completion_report.json` under `skipped_files`.
- The phase is marked `COMPLETE` with warnings (not `FAILED`) unless the skipped file is a collision target in Phase 1 — collision resolution cannot be partial.

### Registry Concurrent Modification

The tool takes a registry snapshot before each phase (`registry_pre_phase{N}.json`). If it detects the registry has been modified between snapshot and commit:

- It aborts the registry write.
- It logs the conflict.
- It does NOT roll back filesystem changes already made (those are recorded in the operations log).
- The operator must re-run the phase, which will detect the partial state and resume.

### Hash Fork Re-Divergence

If Phase 2 discovers that a pair listed as "identical" has diverged since the analysis JSON was produced:

- It logs: `WARN: {fork} and {canonical} are no longer byte-identical (analysis may be stale)`
- It skips that pair.
- The pair is automatically added to Phase 3's dynamic target list.

### Import Chain Breakage

After any rename, the reference scan may find imports that cannot be automatically updated (dynamic imports, string-based module loading via `importlib.util.spec_from_file_location`). These are reported as:

```json
{
  "file": "some_consumer.py",
  "line": 42,
  "type": "dynamic_import",
  "old_reference": "validate_identity_sync",
  "auto_fixable": false,
  "reason": "spec_from_file_location uses computed path"
}
```

The tool does NOT attempt to auto-fix dynamic imports. They are reported in `reference_scan.json` for manual resolution.

---

## PART 13 — APPENDIX: COMPLETE FILE INVENTORY BY CATEGORY

### Category A: ID Collisions (4 pairs — Phase 1)

**P_ ID collision:**

| ID | File 1 | File 2 |
|---|---|---|
| `01999000042260125106` | `P_01999000042260125106_pre_commit_dir_id_check.py` | `P_01999000042260125106_registry_filesystem_reconciler.py` |

**DOC-SCRIPT number collisions:**

| Number | File 1 (manually-written) | File 2 (generator-emitted) |
|---|---|---|
| 0989 | `DOC-SCRIPT-0989__build_file_profiles.py` | `DOC-SCRIPT-0989__validate_rule_id.py` |
| 0992 | `DOC-SCRIPT-0992__validate_section_id.py` | `DOC-SCRIPT-0992__validate_alert_id.py` |
| 0993 | `DOC-SCRIPT-0993__consolidate_file_mappings.py` | `DOC-SCRIPT-0993__validate_artifact_id.py` |

### Category B: Hash-Suffixed Forks (7 files — Phases 2 & 3)

**Identical (Phase 2 — delete):**

| Fork (delete) | Canonical (keep) |
|---|---|
| `P_01999000042260305004_patch_generator_5460db.py` | `P_01999000042260305004_patch_generator.py` |
| `DOC-CLI-DOC-ID-CLI-001__doc_id_cli_304439.py` | `DOC-CLI-DOC-ID-CLI-001__doc_id_cli.py` |
| `validate_identity_sync_278bdc.py` | `validate_identity_sync.py` |
| `validate_uniqueness_ce13c4.py` | `validate_uniqueness.py` |

**Diverged (Phase 3 — merge then delete):**

| Fork (merge from) | Canonical (merge into) | Unique additions in fork |
|---|---|---|
| `P_...305001_file_id_reconciler_2efb6c.py` | `P_...305001_file_id_reconciler.py` | `promote_sha256_to_file_id()`, coverage metadata, `fail_closed` |
| `P_...305012_doc_id_resolver_21864a.py` | `P_...305012_doc_id_resolver.py` | `generate_resolution_patches()`, `apply_resolutions()`, file-watcher exclusion |
| `P_...305013_module_dedup_c3f244.py` | `P_...305013_module_dedup.py` | `generate_dedup_patches()`, `apply_deduplication()`, file-watcher exclusion |

### Category C: Dual-ID Composite Filenames (4 files — Phase 4)

| Current filename | First ID | Second ID | Body `file_id` |
|---|---|---|---|
| `P_01260207201000000865_01999000042260130007_registry_patch_generator.py` | `01260207201000000865` | `01999000042260130007` | none |
| `P_01260207201000000984_01999000042260130008_purpose_registry_builder.py` | `01260207201000000984` | `01999000042260130008` | none |
| `P_01260207201000000985_01999000042260130009_registry_promoter.py` | `01260207201000000985` | `01999000042260130009` | none |
| `P_01260207233100000365_01999000042260125010_file_renamer.py` | `01260207233100000365` | `01999000042260125010` | `01999000042260125010` |

### Category D: Date-Prefixed Superseded Versions (4 pairs + 7 standalone — Phase 5)

**Superseded pairs (earlier → archive, later → onboard):**

| Earlier (retire) | Later (keep) | Validator type |
|---|---|---|
| `2026012100230004_validate_write_policy.py` | `2026012120420006_validate_write_policy.py` | WritePolicyValidator |
| `2026012100230005_validate_derivations.py` | `2026012120420007_validate_derivations.py` | DerivationValidator → DerivationsValidator + DerivationEngine |
| `2026012100230006_validate_conditional_enums.py` | `2026012120420008_validate_conditional_enums.py` | ConditionalEnumValidator |
| `2026012100230009_validate_edge_evidence.py` | `2026012120420009_validate_edge_evidence.py` | EdgeEvidenceValidator |

**Standalone date-prefixed (onboard only):**

| File | Target scheme | Rationale |
|---|---|---|
| `2026011820600003_validate_identity_system.py` | DOC-SCRIPT | Validator; imports `csv`, `yaml`, `pathlib` |
| `2026012120460001_validate_module_assignment.py` | DOC-SCRIPT | Validator; imports `shared.registry_config`, uses `argparse` |
| `2026012120460002_validate_process.py` | DOC-SCRIPT | Validator; imports `shared.registry_config`, uses `argparse` |
| `2099900001260118_apply_ids_to_filenames.py` | P_ | CLI entrypoint; imports `core.registry_store`, uses allocator |
| `2099900078260118_validate_identity_sync.py` | P_ | Validator; imports `core.registry_store`, `csv`-based scan |
| `2099900079260118_validate_uniqueness.py` | P_ | Validator; imports `core.registry_store`, `Counter`-based |

**Key behavioral differences between earlier and later versions (from analysis JSON):**

The later-generation validators (`2042...`) add: `argparse` CLI support, `traceback` import for error handling, `shared.registry_config` integration, `top_level_side_effects_on_import` via `sys.path.insert`, and evidence emission (`evidence_block` outputs). The earlier versions (`2023...`) are simpler standalone validators without CLI wrappers. The later versions are a strict superset — no functionality was removed.

### Category E: Ungoverned Plain Files (8 files — Phase 6)

| File | Role | Has body `file_id`? | Is shim? | `fail_closed` |
|---|---|---|---|---|
| `file_id_resolver.py` | Resolver (4-step SHA→ID chain) | No | No | **Yes** |
| `install_automation.py` | Setup helper | **Yes** (`01999000042260125114`) | No | No |
| `registry_pruning.py` | Registry writer | No | No | No |
| `repo_root_resolver.py` | Resolver | No | No | **Yes** |
| `validate_repo_tree_overlay.py` | Validator | No | No | No |
| `test_last_mile_integration.py` | Test suite | No | No | No |
| `validate_identity_sync.py` | Shim → `2099900078260118_...` | No | **Yes** | No |
| `validate_uniqueness.py` | Shim → `2099900079260118_...` | No | **Yes** | No |

### Category F: Generator Bug (remediated in Phase 1, Step 6)

| Generator file | Bug description |
|---|---|
| `DOC-SCRIPT-ID-GEN-VALIDATORS-992__generate_id_validators.py` | Counter does not check existing DOC-SCRIPT assignments before emitting a number. Produces collisions when manually-written scripts already occupy a number in the sequence. |

**Patch requirement:** Add a pre-emit check that loads the current DOC-SCRIPT assignment list (from the doc_id registry or by scanning filenames) and skips any number already in use.

### Also noted: `rollout_id_type.sh`

The project contains one bash file (`rollout_id_type.sh`) that is outside the scope of this Python-focused remediation. It should be inventoried separately. If it references any filenames being changed by this remediation, it will appear in the reference scans and must be updated manually.

---

## PART 14 — SUMMARY METRICS

| Metric | Count |
|---|---|
| Total files in scope | 163 |
| Files requiring action | 30 |
| ID collisions to resolve | 4 pairs |
| Hash forks to delete (identical) | 4 |
| Hash forks to merge (diverged) | 3 |
| Dual-ID filenames to resolve | 4 |
| Superseded versions to archive | 4 |
| Date-prefixed files to onboard | 10 (4 surviving + 6 standalone) |
| Ungoverned files to onboard | 8 (6 standalone + 2 shims) |
| Generator bugs to patch | 1 |
| Design questions requiring decision | 7 |
| Phases | 6 (sequential, with rollback) |
| Estimated execution time | 30–60 minutes (with review pauses at Phase 3) |

---

*End of document.*
