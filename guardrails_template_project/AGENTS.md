# Repository Guidelines

## Project Structure & Module Organization
This repository is intentionally flat. The canonical source files are the three top-level governance JSON documents:
`NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_2.json`, `NEWPHASEPLANPROCESS_TECHNICAL_SPECIFICATION_V3_2.json`, and `NEWPHASEPLANPROCESS_INSTRUCTION_DOCUMENT_V3_2.json`.
`index_generator.py` is the only executable utility in this snapshot; it reads those sources and regenerates `inventory.json` plus derived artifacts under `indexes\` and `evidence\`.
Supporting context lives in top-level Markdown and text files such as `SYSTEM_INVARIANTS.md` and `GUARDRAILS_README.md`.

## Build, Test, and Development Commands
Use PowerShell from the repository root.

```powershell
python index_generator.py
```
Rebuilds `inventory.json`, writes `indexes\*.index.json`, and emits validation evidence.

```powershell
python index_generator.py --inventory-only
```
Refreshes only `inventory.json` when reviewing array classification changes.

```powershell
python -m json.tool .\NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_2.json > $null
```
Performs a quick syntax check for an edited JSON file; repeat for any touched JSON artifact.

## Coding Style & Naming Conventions
Python follows the existing style in `index_generator.py`: 4-space indentation, type hints, `pathlib`, and standard-library-only dependencies.
Use `snake_case` for functions and variables, `UPPER_CASE` for module constants, and keep file writes deterministic.
For governance data, preserve existing identifier namespaces exactly, including `PAT-*`, `EXEC-*`, `GATE-*`, `COMP-*`, and `ENH-*`.

## Testing Guidelines
There is no committed `tests\` package in the current snapshot, so the minimum regression check is running `python index_generator.py` and confirming it exits cleanly.
For JSON-only edits, validate syntax with `json.tool` and rerun the generator to confirm derived artifacts remain consistent.
If you add Python behavior, add focused `pytest` coverage in `tests\test_<module>.py`; no formal coverage threshold is enforced yet.

## Commit & Pull Request Guidelines
Recent history uses Conventional Commit style with a scoped subject, for example `feat(npp): complete phase-a3 semantic reindexing`.
Keep commit messages in the form `type(scope): imperative summary`.
Pull requests should identify the canonical source files changed, note whether generated outputs were regenerated, and call out any schema, namespace, or validation impact.
