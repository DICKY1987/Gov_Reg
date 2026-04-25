# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

**newPhasePlanProcess v3.3.1** is a governance framework for authoring and validating deterministic, AI-executable project plans. The three root JSON files are the authoritative source of truth — all tooling exists to index, validate, and navigate them.

## Active governance documents (source of truth)

| File | Role |
|------|------|
| `NEWPHASEPLANPROCESS_TECHNICAL_SPECIFICATION_V3_3.json` | Architecture, gate registry, step-contract schema, cross-document rules |
| `NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_3.json` | Executable plan template with step contracts, gates, and executor examples |
| `NEWPHASEPLANPROCESS_INSTRUCTION_DOCUMENT_V3_3.json` | AI-facing narrative: how to fill the template and apply governance rules |

Do **not** edit `V3_2` or legacy `V3_0` filenames — those are archived.

## Generated artifacts (do not hand-edit)

- `inventory.json` — array inventory of the three source documents
- `indexes/*_V3_3.index.json` — semantic identity maps (gates, steps, patterns, executors, components)
- `evidence/PH-*/` — validation gate evidence

Rebuild all generated artifacts with:

```powershell
python .\tools\index_generator.py
```

## Tooling

```powershell
# Resolve a semantic ID (e.g. GATE-003, PAT-EXAMPLE-PLAN-DOC, PH-00/STEP-001)
# to its RFC-6901 JSON Pointer
python .\tools\resolver.py <SEMANTIC_ID>
```

Scripts under `scripts/` are individual validators and runners:

```powershell
# Example — run a single validator
python .\scripts\validate_gate_ids_unique.py

# Gate runner (runs all validation gates)
python .\scripts\gate_runner.py

# Pattern / phase / mutation / handoff runners
python .\scripts\execute_pattern.py
python .\scripts\phase_runner.py
python .\scripts\mutation_runner.py
python .\scripts\handoff_runner.py
```

The legacy CLI at `01260207201000001225_scripts/P_01260207233100000242_NEWPHASEPLANPROCESS_plan_cli.py` targets a different plan shape (`meta`/`plan`/`navigation`) and is **not** a validator for the v3.3 documents.

## Architecture

### Design invariants

- **No implied behavior** — every rule must be explicit, executable, and traceable to evidence.
- **Pattern-first execution** — match tasks to the executor registry before writing new machinery.
- **Configuration-driven** — behavior at governed boundaries comes from approved external specs, not bespoke logic.
- **Semantic path keys** — governed paths are referenced via stable keys resolved through `src/path_registry.py`; no hardcoded absolute paths.
- **Artifact intent before execution** — file mutations are declared in a manifest before any write.

### Four layers

1. **Planning** — requirements → validated executable plan (step contracts with inputs/outputs/pre/postconditions)
2. **Validation** — 20+ template gates, mechanical pass/fail, L0–L5 ground-truth levels
3. **Execution** — worktree isolation, pattern-to-executor binding, deterministic execution
4. **Observability** — evidence chains, metrics, audit trails linking each step to its outputs

### Key identity namespaces (used in index maps)

| Prefix | Governs |
|--------|---------|
| `GATE-` | Validation gates |
| `GATE-CFG-` | Config-layer gate extensions (v3.3+) |
| `GATE-FILE-MUTATIONS` | File-mutation gate |
| `PAT-` | Execution patterns |
| `EXEC-` | Executor bindings |
| `COMP-L<n>-<nn>` | Architecture components by layer |
| `PH-<nn>/STEP-<nnn>` | Phase/step addresses |

Duplicate IDs within any namespace are a critical violation.

### Evidence directory convention

Gates write evidence to `evidence/PH-<nn>/<artifact>.json`. The final readiness gate writes to `evidence/PH-09/final_readiness_report.json`.

## Path resolution

Use `src/path_registry.py` (singleton resolver) for all governed paths. The hardcoded-path allowlist is at `config/`. Running `validate_no_new_hardcoded_governed_paths.py` enforces this.

## Archive

Retired v3.0/v3.2 files, migration notes, and completion reports live at:

```
C:\Users\richg\CENTRAL_ARCHIVE\Gov_Reg\newPhasePlanProcess\2026-04-19_v3_3_cleanup
```

The move manifest is `archive_manifest_2026-04-19_v3_3_cleanup.json` at repo root.
