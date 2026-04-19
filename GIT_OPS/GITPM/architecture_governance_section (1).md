# Architecture and Governance Section

This file contains only the portions of the uploaded terminal transcript related to broader architecture and governance work: exploration of `ALL_AI\GOVERNANCE`, `SSOT_System`, scaffold registries, gates, lifecycle, and comparison against the live `Gov_Reg\...\ID` system.

## SSOT_System Overview

This is a Single Source of Truth (SSOT) governance system — a documentation-as-infrastructure framework for AI-assisted codebases.

### Purpose
It enforces deterministic validation and quality gates so that documentation, component identities, and architectural decisions remain stable and machine-verifiable across refactoring. Core idea: treat docs like code, with schemas, validators, CI gates, and lifecycle tracking.

### Top-Level Structure
- `SSOT_SYS_tools/` — Python validators and enforcement tools
- `SSOT_SYS_ci/` — CI gate orchestration and pre-commit hooks
- `SSOT_SYS_schemas/` — JSON/YAML schemas
- `SSOT_SYS_tests/` — unit, integration, automation, and end-to-end tests
- `SSOT_SYS_docs/` — documentation and guides
- `SSOT_SYS_enforcement/` — compliance and validation gates
- `SSOT_SYS_patches/` — RFC 6902 patch files
- `SSOT_SYS_baselines/` — baseline snapshots
- `SSOT_SYS_repo_scaffolding/` — templates and manifests
- `automation/` — automation chain specs and diagrams
- `policies/` — policy definitions and registry

### Key Files
- `DOC-CONFIG-SSOT-CURRENT-APPROACH-505__SSOT_CURRENT_APPROACH.json`
- `DOC-AUTOMATION-SSOT-001__AUTOMATION.SSOT.yaml`
- `DOC-CONFIG-SYSTEM-MANIFEST-506__SYSTEM_MANIFEST.json`
- `DOC-CONFIG-VALIDATOR-CATALOG-507__VALIDATOR_CATALOG.json`

## File-Level Audit Results

### Confirmed
- 33 Python files in `SSOT_SYS_tools/`, including explicit validators
- Real RFC 6902 patch files in `SSOT_SYS_patches/`
- Canonical SSOT document with artifact records keyed by ID
- CI gate blocks commits when SSOT changes lack a corresponding patch
- Active automation pipeline documentation
- Policy files with enforcement via pre-commit and CI
- 23 pytest test files across multiple suites

### Correction
The earlier Flask claim was wrong. No Flask service exists in this folder. ID resolution is handled by standalone Python tools such as:
- `id_registry.py`
- `relationship_index_generator.py`
- `path_registry.py`

## GOVERNANCE Folder Summaries

### `registries/`
Status: Placeholder / scaffold. Mostly empty and used as a template source.

### `rules/`
Purpose: Rule identifier registry using format `RULE-{DOMAIN}-{NAME}-{SEQ}`. Documentation exists, but no populated rule data yet.

### `contracts/`
Purpose: System identity model contract.
- `dir_id` tier: physical inventory IDs stored as `.dir_id` JSON files
- semantic key tier: stable coupling IDs used by code and automation through a mandatory PathRegistry

Rule: code must never reference directories by physical path or `dir_id`; it must use semantic keys.

### `gates/`
Purpose: Quality gate enforcement engine.
- `gate_runner.py` executes YAML-defined gates
- `enforcement_bridge.py` hooks gates into orchestrators
- `definition_of_done.yaml` defines the gate layers

Non-zero exit codes stop pipeline progression. Evidence is written under `evidence/<run_id>/gates/`.

### `lifecycle/`
Purpose: Artifact lifecycle and state transition management.
Key capabilities include:
- remediation map for multiple error categories
- schema files for gate aggregate output, manifest index, and validator catalog
- tools such as `atomic_assigner.py`, `reconciliation_engine.py`, `filesystem_watcher.py`, and `repo_audit.py`

Invariant: the lifecycle graph must be an acyclic DAG and all references must resolve.

### `policies/`
Purpose: Policy identifier registry plus definition of done.
Tracks policy IDs and contains the most substantive `definition_of_done.yaml`, which defines six quality gate layers:
1. Process Compliance
2. BDD/TDD linkage
3. Observability schemas
4. Docs-as-Code
5. Determinism Contracts
6. Integrated Gates

### `precedents/`
Purpose: Authority precedent identifier registry scaffold. Documentation exists, but the actual precedent registry is not yet populated.

## Overall Pattern

These folders form a layered governance stack:

- `contracts/` → identity rules
- `registries/` → ID templates / format standard
- `rules/` → validation rule IDs
- `policies/` → policy IDs and definition-of-done enforcement
- `gates/` → blocking checks at pipeline transitions
- `lifecycle/` → artifact state transitions and remediation
- `precedents/` → authority decision records

Most are scaffolds. The two with real operational content are `gates/` and `lifecycle/`.

## Gov_Reg ID System Comparison

### What `Gov_Reg\01260207201000001250_REGISTRY\ID` is
A live production ID system with:
- real populated numeric registry
- atomic counter with cross-platform file locking
- duplicate prevention via allocator, reservation ledger, pre-commit hook, and reconciliation loop

### ID format
- file ID: `01999000042260124031`
- Python file naming example: `P_01999000042260124031_module.py`
- directory ID: `.dir_id` JSON anchor file

### Internal structure
- `1_runtime/` — allocators, validators, watchers
- `2_cli_tools/` — CLI tools, Git hooks, health checks
- `3_schemas/` — schemas
- `4_config/` — active allocator config
- `5_tests/` — tests
- `6_docs/` — architecture and contracts
- `7_automation/` — daemons and repair agents

## Verdict: GOVERNANCE vs Gov_Reg ID

They are **not duplicates**. They are different generations of the same idea.

### ALL_AI/GOVERNANCE
- older
- mostly design-time scaffolds and contracts
- human-readable ID formats
- not fully populated

### Gov_Reg ID
- newer
- live runtime allocator
- pure 20-digit numeric IDs
- populated registry and active enforcement

### Compatibility
They are **not compatible** as-is.
- `GOVERNANCE` uses human-readable formats such as `DIR-governance-rules-912af35f`
- `Gov_Reg` uses pure numeric IDs such as `01999000042260124031`

There is no bridge, converter, or shared schema between them.

### Are both required to add IDs to files?
No.
- For files in `ALL_AI/`, use the GOVERNANCE-side tooling
- For files in `Gov_Reg/`, use the Gov_Reg numeric allocator

They operate on separate trees and do not know about each other.
