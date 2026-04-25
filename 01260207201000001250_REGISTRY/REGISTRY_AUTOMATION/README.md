# Registry Automation

Automation utilities for validating and mutating `01999000042260124503_REGISTRY_file.json` and its supporting `.state\` artifacts.

## Current Layout

- `scripts\` contains 21 Python utilities numbered `05000` through `05020`.
- `tests\` contains 7 pytest files covering smoke, entity-resolution, and sha256-promotion flows.
- `docs\EVIDENCE_ARTIFACT_SCHEMA_V1.json` remains as a reference schema for evidence artifacts.
- `README.md` and `SCRIPT_INDEX.md` are the live package entrypoints.
- Historical remediation notes now live under `..\archive\analysis_reports\2026-04-24_root_cleanup\REGISTRY_AUTOMATION\`.

## Primary Entry Points

- `scripts\P_01999000042260305019_preflight_checker.py`
  - Fail-closed validation before mutations.
- `scripts\P_01999000042260305000_enum_drift_gate.py`
  - Detect and optionally normalize enum drift in registry data.
- `scripts\P_01999000042260305017_pipeline_runner.py`
  - Batch orchestration for the intake and validation pipeline.
- `scripts\P_01999000042260305018_sha256_backfill.py`
  - Compute and backfill missing sha256 values.
- `scripts\P_01999000042260305020_registry_path_cleaner.py`
  - Remove `FILE WATCHER` path pollution and re-run dedup cleanup.

## Script Groups

- Validation and gating
  - `05000`, `05019`, `05020`
- Mapping, transformation, and patch application
  - `05001` through `05004`
- Column runtime helpers
  - `05005` through `05011`
- Entity resolution and pipeline orchestration
  - `05012` through `05018`

See `SCRIPT_INDEX.md` for the full inventory.

## Tests

- Unit tests
  - `tests\unit\test_default_injector.py`
  - `tests\unit\test_enum_drift_gate_smoke.py`
  - `tests\unit\test_phase_a_transformer_smoke.py`
  - `tests\unit\test_pipeline_runner_smoke.py`
- Integration tests
  - `tests\integration\test_entity_resolution.py`
  - `tests\integration\test_sha256_promotion.py`
- Shared test setup
  - `tests\conftest.py`

Run from the repo root:

```powershell
python -m pytest 01260207201000001250_REGISTRY\REGISTRY_AUTOMATION\tests
```

## Notes

- Most scripts use the Python standard library only.
- Tests require `pytest`.
- Generated operational state is written under `.state\`.
