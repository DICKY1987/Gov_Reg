# Registry Automation Script Index

Current inventory for `REGISTRY_AUTOMATION\scripts\`.

## Validation and Gating

- `P_01999000042260305000_enum_drift_gate.py`
  - Build canonical enum definitions, detect drift, and optionally normalize registry values.
- `P_01999000042260305019_preflight_checker.py`
  - Fail-closed validation for required `.state\` inputs, file-id uniqueness, and sha256 shape before mutations.
- `P_01999000042260305020_registry_path_cleaner.py`
  - Remove `FILE WATCHER` pollution from registry paths and verify cleanup.

## Mapping, Transformation, and Patch Application

- `P_01999000042260305001_file_id_reconciler.py`
  - Build `sha256 -> file_id` and `file_id -> sha256` mappings for downstream consumers.
- `P_01999000042260305002_phase_a_transformer.py`
  - Transform Phase A analyzer output into registry-shaped records.
- `P_01999000042260305003_run_metadata_collector.py`
  - Record run metadata, script execution, timing, and status for audit trails.
- `P_01999000042260305004_patch_generator.py`
  - Generate, validate, and apply RFC-6902 patches to the registry.

## Column Runtime Helpers

- `P_01999000042260305005_column_loader.py`
  - Load and cache column definitions from the registry column dictionary.
- `P_01999000042260305006_column_validator.py`
  - Validate record values against the loaded column definitions.
- `P_01999000042260305007_default_injector.py`
  - Inject defaults for missing columns.
- `P_01999000042260305008_null_coalescer.py`
  - Replace nullable values with configured defaults where applicable.
- `P_01999000042260305009_phase_selector.py`
  - Extract phase-specific slices from a registry record.
- `P_01999000042260305010_missing_reporter.py`
  - Report columns defined in the dictionary but absent from records.
- `P_01999000042260305011_column_introspector.py`
  - Inspect real column usage across the registry.

## Entity Resolution and Pipeline Orchestration

- `P_01999000042260305012_doc_id_resolver.py`
  - Resolve `doc_id` collisions and build canonical mappings.
- `P_01999000042260305013_module_dedup.py`
  - Deduplicate module names and flag cross-repo ambiguities.
- `P_01999000042260305014_intake_orchestrator.py`
  - Run the single-file intake pipeline across the analyzer stages.
- `P_01999000042260305015_timestamp_clusterer.py`
  - Group files by timestamp proximity for watcher-driven batches.
- `P_01999000042260305016_e2e_validator.py`
  - Validate registry structure and record content end to end.
- `P_01999000042260305017_pipeline_runner.py`
  - Run the batch pipeline and consolidate registry updates.
- `P_01999000042260305018_sha256_backfill.py`
  - Compute and backfill missing sha256 values with backup support.

## Common Commands

```powershell
python .\REGISTRY_AUTOMATION\scripts\P_01999000042260305019_preflight_checker.py
python .\REGISTRY_AUTOMATION\scripts\P_01999000042260305000_enum_drift_gate.py --fix
python .\REGISTRY_AUTOMATION\scripts\P_01999000042260305018_sha256_backfill.py --registry .\01260207201000001250_REGISTRY\01999000042260124503_REGISTRY_file.json --dry-run
python .\REGISTRY_AUTOMATION\scripts\P_01999000042260305017_pipeline_runner.py --input-dir .\01260207201000001313_capability_mapping_system\01260207220000001318_mapp_py --output-dir .\tmp\pipeline
```

## Test Inventory

- `tests\conftest.py`
- `tests\integration\test_entity_resolution.py`
- `tests\integration\test_sha256_promotion.py`
- `tests\unit\test_default_injector.py`
- `tests\unit\test_enum_drift_gate_smoke.py`
- `tests\unit\test_phase_a_transformer_smoke.py`
- `tests\unit\test_pipeline_runner_smoke.py`
