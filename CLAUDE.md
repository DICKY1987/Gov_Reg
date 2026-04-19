# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Primary Contract

`DEV_RULES_CORE.md` at repo root is the **primary contract** governing all behavior. When in conflict, it wins over this file.

Subsystem-specific CLAUDE.md files exist in:
- `01260207201000001250_REGISTRY/01260202173939000109_CLAUDE.md` — Registry system (detailed, authoritative for registry work)

## Architecture Overview

Gov_Reg is a deterministic governance automation framework. The central artifact is a **Unified SSOT Registry** (185-column JSON) that tracks every file in the repo with governance metadata. All changes flow through a **6-state lifecycle** (PLANNED → PRESENT → DEPRECATED → DELETED → ORPHANED → CONFLICT) enforced by validators, quality gates, and write policies.

### Data Flow

```
Registry SSOT (185-column JSON)
  ↓ governed by
Write Policy (YAML) + Derivations (safe DSL, 30+ functions)
  ↓ enforced by
GEU Layer (SCHEMA/RULE/VALIDATOR/RUNNER/FAILURE_MODE/EVIDENCE/TEST/REPORT)
  ↓ checked at
Gate Layer (Completeness exit 10, Validity exit 11)
  ↓ triggered by
File System Layer (watchers, event emission, identity resolution)
```

### Core Packages

| Package | Location | Purpose |
|---------|----------|---------|
| Registry Transition | `src/registry_transition/` | 6-state lifecycle; most-tested (90% cov, 26 tests) |
| GEU Governance | `src/P_01999000042260124484_geu_governance/` | 9-module Governance Enforcement Units |
| Repo Auto-Ops | `src/repo_autoops/` | File watcher, reconciler, audit logger, work queue, classifier |
| Phase B CLI | `src/phase_b_cli/` | Phase execution CLI |
| Plan Refine CLI | `src/plan_refine_cli/` | Deterministic planner-critic-refiner loop |
| GovrReg Core | `01260207201000001173_govreg_core/` | Ingest engine, reconciliation, feature flags, migration guard |
| Scripts | `01260207201000001276_scripts/` | Pre-commit/pre-push hooks, health check, coverage completer |
| Path Registry | `01260207201000001242_PATH_FILES/path_registry.py` | Singleton semantic path resolver (80+ keys → filesystem paths) |

### Key Data Files

| File | Purpose |
|------|---------|
| `01260207201000001250_REGISTRY/01999000042260124503_REGISTRY_file.json` | Master SSOT (185 columns) |
| `01260207201000001250_REGISTRY/COLUMN_HEADERS/01260207201000000193_UNIFIED_SSOT_REGISTRY_WRITE_POLICY.yaml` | Column write rules |
| `01260207201000001250_REGISTRY/COLUMN_HEADERS/01260207201000000192_UNIFIED_SSOT_REGISTRY_DERIVATIONS.yaml` | Computed field formulas |
| `01260207201000001250_REGISTRY/01999000042260124012_governance_registry_schema.v3.json` | JSON Schema (428 properties) |
| `01260207201000000190_transition_contract.bundle.yaml` | 6-state lifecycle definition (8 transitions) |

### GIT_OPS Directory

`GIT_OPS/` contains planning and architecture documents for the **GitHub automation subsystem** — GitHub Actions workflows, Projects field-sync, and GitHub App authentication design. No executable code lives here; it is design and mapping artifacts only.

## Commands

All commands run from repo root (`Gov_Reg/`). Python 3.11+.

### Testing

```bash
# Run all tests
pytest tests/ -v

# Run a single test module
pytest tests/test_state_machine.py -v

# Registry transition coverage (target: 90%)
pytest tests/ --cov=src/registry_transition --cov-report=term

# Run test vectors (23 vectors)
python scripts/run_batch_vectors.py

# Determinism score from metrics
python scripts/calc_determinism_score.py --metrics .state/metrics/metrics.jsonl
```

### Registry Validation

```bash
# Validate path registry
python 01260207201000001242_PATH_FILES/path_registry.py validate
python 01260207201000001242_PATH_FILES/path_registry.py list

# Schema compliance
python scripts/P_01999000042260124547_validate_schema.py

# Control coverage (SEC-021)
python validators/validate_sec_021.py

# Derivation formulas
python validators/validate_derivation.py

# doc_id violation check
python ID/P_01999000042260126012_validate_no_doc_id.py
```

### Registry TUI & Patching

```bash
# Interactive TUI for registry browsing and health-checks
python 01260207201000001250_REGISTRY/01260207201000001270_scripts/P_01999000042260126011_registry_tui.py \
  --registry-path 01999000042260124503_REGISTRY_file.json

# Apply RFC-6902 JSON patch to registry
python 01260207201000001250_REGISTRY/01260207201000001270_scripts/P_01260207201000000834_apply_patch.py \
  --target [REGISTRY_FILE] --patch [PATCH_FILE] --evidence [EVIDENCE_DIR]
```

### Dependencies

```bash
pip install pyyaml pytest pytest-cov jsonschema jsonpatch click rich
# Full deps: LP_LONG_PLAN/PHASE_1_PLANNING/pyproject.toml
```

## Key Conventions

### File ID Format — Mandatory

Every file must have a **20-digit numeric prefix**:
- Python modules: `P_01999000XXXXXXXXXX_name.py`
- Data files: `01999000XXXXXXXXXX_name.ext`
- **Duplicate IDs = critical violation.** Never reuse an existing ID.

### Registry Write Protocol

Single-writer semantics only: `Operation → Validate → Atomic write (temp → rename) → Backup`

- All writes validate against `COLUMN_HEADERS/...WRITE_POLICY.yaml`
- Computed fields use derivation DSL only — **never `eval()`**
- Back up registry to `REGISTRY/backups/` before any destructive change

### Field Precedence

- **Authoritative** (must overwrite): `size_bytes`, `sha256`, `mtime_utc`, `last_seen_utc`
- **Inferred** (preserve planned value): `artifact_kind`, `layer`, `language`, `framework`
- **Immutable** (never change): `file_id`, `record_id`, `created_utc`, `original_doc_id`

### Path Safety

Use `resolve_path(KEY)` from `path_registry.py`. No hardcoded absolute paths. Key format: `UPPERCASE_WITH_UNDERSCORES` or `namespace:key`.

### GEU Roles

When classifying files for registry, use `geu_role`:
`SCHEMA` | `RULE` | `VALIDATOR` | `RUNNER` | `FAILURE_MODE` | `EVIDENCE` | `TEST` | `REPORT`

### Code Style

- PEP 8, 4-space indent, 100-char line length
- `snake_case` functions/variables, `PascalCase` classes
- Type hints required for public APIs (mypy strict)
- Google-style docstrings

## Hard Constraints

- Never manually edit `*.phase_contract.json` — use RFC-6902 patches
- Never hardcode absolute paths — use `path_registry.py`
- Never use `eval()` in derivations
- Never create duplicate 20-digit file IDs
- Never write to the registry without validating against write policy
- Always validate path registry before operations
- Always run tests after schema or validator changes

## CI/CD

`.github/workflows/evidence_integrity.yml` enforces on push/PR:
1. `coverage.json` must contain pytest-cov metadata (`.meta.version`)
2. `junit.xml` must contain pytest signature
3. `determinism_score.json` must have `metrics_lines_read > 0`
4. All 26 tests must pass; coverage ≥ 90%

Evidence files live in `.state/evidence/final/` — must be tool-generated, never hand-written.

## Git Workflow

Conventional Commits: `type(scope): subject`

Common scopes: `registry`, `validator`, `gates`, `geu`, `watcher`, `scripts`, `control-coverage`
