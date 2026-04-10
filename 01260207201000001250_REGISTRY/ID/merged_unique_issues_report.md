# Consolidated Unique Issues Report

## Source Files Merged
- `✳ Analyze and validate file naming scheme issues.txt`
- `scrpysort.txt`

## Purpose
This file merges both source analyses into one de-duplicated report that keeps only the unique issues, folds in corrections, and removes repeated findings.

---

## Consolidated Findings

### 1) True P_ ID collision
A confirmed hard collision exists where two different files share the same 20-digit P_ ID:
- `P_01999000042260125106_pre_commit_dir_id_check.py`
- `P_01999000042260125106_registry_filesystem_reconciler.py`

This is the most serious naming-integrity issue because it directly violates the uniqueness rule the system is supposed to enforce.

### 2) Additional shared-ID collisions caused by same base ID reuse
Beyond the one critical direct collision above, several file pairs reuse the same base ID in suffixed variants:
- `P_01999000042260305001_file_id_reconciler.py`
- `P_01999000042260305001_file_id_reconciler_2efb6c.py`
- `P_01999000042260305004_patch_generator.py`
- `P_01999000042260305004_patch_generator_5460db.py`
- `P_01999000042260305012_doc_id_resolver.py`
- `P_01999000042260305012_doc_id_resolver_21864a.py`
- `P_01999000042260305013_module_dedup.py`
- `P_01999000042260305013_module_dedup_c3f244.py`

These are not all identical duplicates. Some are true duplicates, while others are materially different revisions sharing the same ID.

### 3) DOC-slot collisions are broader than the original assessment claimed
Confirmed DOC collisions include:
- `DOC-SCRIPT-0989__build_file_profiles.py` vs `DOC-SCRIPT-0989__validate_rule_id.py`
- `DOC-SCRIPT-0992__validate_alert_id.py` vs `DOC-SCRIPT-0992__validate_section_id.py`
- `DOC-SCRIPT-0993__consolidate_file_mappings.py` vs `DOC-SCRIPT-0993__validate_artifact_id.py`
- `DOC-SCRIPT-1021__validate_policy_id.py` vs `DOC-SCRIPT-VALIDATE-GOV-1021__validate_governance.py`
- `DOC-CLI-DOC-ID-CLI-001__doc_id_cli.py` vs `DOC-CLI-DOC-ID-CLI-001__doc_id_cli_304439.py`

If numeric slots are treated numerically instead of as isolated literal strings, the collision surface expands further:
- `DOC-SCRIPT-0990__validate_run_id.py` vs `DOC-SCRIPT-ID-GEN-AUTOMATION-990__generate_id_automation.py`
- `DOC-SCRIPT-0991__validate_schema_id.py` vs `DOC-SCRIPT-ID-GEN-DOCS-991__generate_id_docs.py`

### 4) Date-prefixed version layering / stale generations
The 14 numeric-prefixed files are not one uniform group.
- 11 are normal operational numeric-prefixed files
- 3 are sentinel-style `2099...` files

The validator family contains older `202601210023...` versions and later `202601212042...` versions:
- `validate_write_policy`
- `validate_derivations`
- `validate_conditional_enums`
- `validate_edge_evidence`

There is also a later `2026012120460001...` / `2026012120460002...` pair that extends the dated generation set.

Core issue: the directory contains multiple timestamp generations of similar validator tooling with no explicit canonicality declaration.

### 5) 2099 sentinel file drift
The `2099...` files behave like sentinel or placeholder artifacts rather than clean operational IDs. At minimum:
- `2099900001260118_apply_ids_to_filenames.py` has filename/header ID drift
- `2099900078260118_validate_identity_sync.py` and `2099900079260118_validate_uniqueness.py` are part of the sentinel set

These should not remain semantically ambiguous. They need to be either normalized into the active naming system or formally documented as legacy/sentinel exceptions.

### 6) Dual-ID composite filenames
There are **4** dual-ID P_ filenames, not 3:
- `P_01260207201000000865_01999000042260130007_registry_patch_generator.py`
- `P_01260207201000000984_01999000042260130008_purpose_registry_builder.py`
- `P_01260207201000000985_01999000042260130009_registry_promoter.py`
- `P_01260207233100000365_01999000042260125010_file_renamer.py`

These combine two ID families in one filename and likely fall outside normal scanner expectations. They need an explicit rule: either this is supported syntax, or these are migration artifacts that must be renamed.

### 7) Plain-file governance gap
The original “plain 11” grouping was too coarse. That set actually mixes:
- plain Python files
- hash-suffixed Python files
- one shell-script outlier (`rollout_id_type.sh`)

The real issue is not just “plain files exist.” It is that some files sit outside canonical governance while overlapping with governed implementations.

Important correction:
- `validate_identity_sync.py` and `validate_uniqueness.py` are not true duplicates of the `2099...` files; they are compatibility shims that load those implementations.

### 8) Duplicate vs revised-copy confusion
Several pairs originally labeled as duplicates are not all duplicates.

**True content-duplicate groups confirmed:**
- `validate_identity_sync.py` and `validate_identity_sync_278bdc.py`
- `validate_uniqueness.py` and `validate_uniqueness_ce13c4.py`
- `DOC-CLI-DOC-ID-CLI-001__doc_id_cli.py` and `DOC-CLI-DOC-ID-CLI-001__doc_id_cli_304439.py`
- `P_01999000042260305004_patch_generator.py` and `P_01999000042260305004_patch_generator_5460db.py`

**Materially different, not safe to collapse blindly:**
- `P_01999000042260305001_file_id_reconciler.py` vs `_2efb6c`
- `P_01999000042260305012_doc_id_resolver.py` vs `_21864a`
- `P_01999000042260305013_module_dedup.py` vs `_c3f244`

### 9) Template-generated validator concentration risk
The `DOC-SCRIPT-????__validate_*_id.py` validators are template-generated and structurally near-identical. That is not a naming violation by itself, but it creates a maintenance hotspot: one template flaw can propagate across the whole validator set.

### 10) Syntax / parse failures
Additional analysis identified files that do not successfully parse under Python compilation. At least one explicitly cited example is:
- `P_01260207233100000365_01999000042260125010_file_renamer.py`

This means the problem set is not only about naming drift; some artifacts are also execution-invalid.

### 11) Reusable ID assignment pipeline is not actually self-consistent
The files that appear to define the reusable ID-assignment core do not currently compose cleanly as one portable pipeline.
- `P_01999000042260124031_unified_id_allocator.py` depends on `P_01999000042260124030_shared_utils.py`, which sits outside the active `ID/` runtime tree
- `P_01999000042260125006_id_allocator_facade.py` looks for `.idpkg/config.json`, while the visible active config is `ID/4_config/idpkg_active_config.json`
- `P_01999000042260124521_id_format_scanner.py` only recognizes single-underscore 20-digit prefixes and defines a `files_wrong_format` bucket that is never populated
- `P_01260207201000000198_add_ids_recursive.py` is a filename renamer only; it does not update headers or registry state and assumes `govreg_core` path wiring plus a local `COUNTER_STORE.json`
- `P_01999000042260124028_file_creator.py` generates `DOC-FILE-{id}__...` names, which conflict with the scanner and canonical prefix logic, and it imports missing legacy modules
- `P_01999000042260124023_scanner.py` depends on a missing local config file and a missing older allocator module

Core issue: the apparent “assignment pipeline” is split across active files, external dependencies, and migration leftovers, so reuse is presently fragile and convention-drifting rather than canonical.

### 12) Integrity layer is partially stubbed, partially broken, and partially legacy
The post-assignment integrity stack is not one clean current-generation validation layer.
- `file_id_resolver.py` imports successfully, but its authoritative registry lookup is still a TODO; practical resolution falls back to cache, sidecar metadata, or optional generation / placeholders
- `P_01999000042260305001_file_id_reconciler.py` in `REGISTRY_AUTOMATION/scripts` contains a syntax error in `promote_sha256_to_file_id`, while the capability-mapping-system twin imports cleanly
- `2099900078260118_validate_identity_sync.py` and `2099900079260118_validate_uniqueness.py` still operate on 16-digit `doc_id` semantics via the legacy `RegistryStore`, not the active 20-digit `file_id` contract

Core issue: the integrity layer mixes current 20-digit file-ID expectations with older 16-digit doc-ID tooling and at least one execution-invalid reconciler copy.

---

## Corrections Folded In From The Second File

The merged report intentionally corrects these claims from the original assessment:
- Dual-ID files are **4**, not 3.
- “14 date-prefixed files” includes **3 sentinel-style 2099 files**; operational dated files are fewer.
- Not all hash-suffixed P_ variants are identical duplicates.
- The plain `validate_identity_sync.py` and `validate_uniqueness.py` files are compatibility shims, not simple duplicates of the `2099...` versions.
- DOC collisions should be evaluated across the broader DOC namespace, not only within narrow `DOC-SCRIPT-####` literals.

---

## Final De-duplicated Issue List

1. Hard P_ ID collision on `01999000042260125106`
2. Additional shared-base-ID collisions in suffixed P_ variants
3. Broad DOC slot collisions across SCRIPT and non-SCRIPT namespaces
4. Multiple dated generations with unclear canonical versioning
5. Sentinel `2099...` files with naming/header drift
6. Unsupported or undefined dual-ID filename syntax
7. Governance gap for plain, shim, and outlier files
8. Confusion between exact duplicates and materially different revisions
9. Template-generated validator concentration risk
10. Parse-invalid Python files inside the analyzed set
11. Reusable ID-assignment components do not currently form one self-consistent portable pipeline
12. Integrity tooling mixes stubs, broken copies, and legacy 16-digit validator semantics

---

## Recommended Use Of This Merged File
Use this file as the canonical issue inventory for follow-on cleanup work. If you want to turn it into an implementation document, the next step should be to convert each issue into:
- detection rule
- severity
- evidence pattern
- auto-fix strategy
- manual resolution strategy
- canonical replacement rule
