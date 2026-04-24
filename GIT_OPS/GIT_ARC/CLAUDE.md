# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this directory is

`GIT_OPS/` is the design and architecture working folder for the **GitHub automation subsystem** of the Gov_Reg project. It contains research, architecture deltas, and planning documents — no executable code lives here.

The subsystem's job is to project the SSOT plan files (YAML/JSON phase plans in `Gov_Reg/`) onto GitHub as the execution surface: phases become Project fields, steps become Issues, gates become required CI checks, and PRs become execution attempts.

## Document inventory

| File | What it is |
|------|-----------|
| `compass_artifact_wf-..._text_markdown.md` | Research synthesis: "SSOT-to-Execution-Surface Projection" — cross-system analysis of reconciliation patterns across Temporal, ArgoCD/Flux, PlanetScale, Atlas, Linear, Oxide, and Red Hat's `qontract-reconcile`. The authoritative reference for architectural decisions. |
| `ChatGPT-Template to GitHub Mapping (1).md` | Gap analysis and target mapping: Phase→Project field, Step→Issue, Gate→CI check, Execution→PR, Completion→Issue closure. Identifies 6 gaps in the current system. |
| `Second Architecture Delta for GitHub Hardening.md` | Formal delta `ARCH-DELTA-NPP-GITHUB-HARDENING-002`. Adds 5 constructs missing from the prior delta. |
| `ChatGPT-Branch · GitHub Automation Files.json` / `ChatGPT-GitHub Automation Files.json` | Inventories of existing GitHub Actions workflow template files (`TEMP_*.yml`) with array classification metadata. |
| `github_project_management_process_inventory.json` | SHA256-stamped inventory of workflow template files. Used for drift detection against known-good copies. |
| `Git automation subsystem.txt` | MVP component model and architecture rationale for the git automation subsystem. |

## Core architecture model

```
TEMPLATE/PLAN (SSOT — YAML/JSON in Gov_Reg/)
    │
    ▼  projection (unidirectional, SSOT owns decomposition)
PHASE ──────────► GitHub Project field "Phase"
STEP CONTRACT ──► GitHub Issue  (1 step = 1 issue, linked by step_id)
GATE ────────────► Required CI check / GitHub Actions workflow
EXECUTION ──────► Pull Request  (PR = implementation of ≥1 step contracts)
MERGE ──────────► Step complete → Issue closed → Milestone progress
```

**GitHub is the execution surface, not the control plane.** Plan YAML/JSON is the authority for decomposition, step contracts, phase structure, gate requirements, and evidence requirements. GitHub owns assignees, review conversations, and comment threads only.

## Architecture delta status

The hardening delta (`ARCH-DELTA-NPP-GITHUB-HARDENING-002`) adds five constructs that must be implemented:

### 1. GitHub App Authentication (`LAW-GH-001`)
- All automation accessing Projects must use GitHub App installation tokens, not `GITHUB_TOKEN` (which cannot access Projects) and not PATs (fragile at scale).
- Token issued per workflow run via `actions/create-github-app-token@v2`; 1-hour max lifetime.
- Required ProgramSpec: `programs/GH_AUTH_ISSUE_INSTALLATION_TOKEN.spec.json`

### 2. Field Bootstrap Registry (`LAW-GH-002`)
- No automation may hardcode `PROJECT_NODE_ID`, `STATUS_FIELD_ID`, `PHASE_FIELD_ID`, or option IDs.
- All IDs come from a generated `config/github_field_registry.json` (query-then-extract at workflow start via GraphQL).
- Bootstrap must be repeatable and self-healing; fail closed if registry is missing or stale.
- Required ProgramSpecs: `GH_FIELDS_DISCOVER`, `GH_FIELDS_VALIDATE`

### 3. Phase Advancement Evaluator (`LAW-GH-003`)
- Phase transitions only through the evaluator backed by a stored decision artifact.
- Evaluator inputs: plan package + GitHub observed state (issues, check states, PR merges, evidence markers).
- Must be level-triggered (also runs on schedule), not edge-triggered (webhook-only).
- Outputs: `phase_advancement_report.json` + `phase_transition_decision.json`

### 4. Runner Platform Policy (`LAW-RUN-001`)
- Every ProgramSpec declares its runner class: `linux_hosted`, `windows_hosted`, `self_hosted_windows`, `self_hosted_linux`, `self_hosted_ephemeral`.
- GraphQL/REST ops and plan validation gates → `ubuntu-latest` (GitHub-hosted).
- Windows-only automation (PowerShell, local filesystem sync) → self-hosted Windows runner.
- Required: `policies/runner_policy.yaml`

### 5. Sync Governance Rules
- Ownership model:
  - **Plan-owned**: decomposition, step contracts, phase structure, gate/evidence requirements
  - **GitHub-owned**: assignees, review conversations, comments
  - **Automation-only** (manual edits = drift): `Phase`, `Status`, `EvidenceState`, `DeterminismState`, `PlanHash`, `ProjectionVersion`
- Drift taxonomy: Allowed / Violation / Orphan / Missing / Override
- Reconciliation loop: observe → diff → act → report (level-triggered, scheduled + event)
- `PlanHash` and `ProjectionVersion` as custom Project fields for checksum-based drift detection.

## Required artifacts to produce

From the delta, these files must be created in the parent repo structure:

```
config/
  github_field_registry.json
  github_projection_registry.json
  github_override_registry.json
policies/
  github_sync_governance.yaml
  runner_policy.yaml
schemas/
  github_field_registry.schema.json
  github_projection_manifest.schema.json
  reconciliation_report.schema.json
  phase_advancement_report.schema.json
.github/workflows/
  bootstrap-github-fields.yml
  phase-advancement-evaluator.yml
  ssot-drift-reconciliation.yml        ← level-triggered self-healing loop
programs/
  GH_AUTH_ISSUE_INSTALLATION_TOKEN.spec.json
  GH_FIELDS_DISCOVER.spec.json
  GH_FIELDS_VALIDATE.spec.json
  GH_PROJECTION_GENERATE.spec.json
  GH_PROJECTION_APPLY.spec.json
  GH_RECONCILE_DRIFT.spec.json
  GH_PHASE_ADVANCE_EVALUATE.spec.json
```

## Key design principles (from research synthesis)

- **Level-triggered, not edge-triggered**: reconciliation must converge to correct state on a schedule; missed webhooks must not cause permanent drift.
- **Unidirectional projection**: SSOT → GitHub only. Bidirectional sync reliably causes data loss (documented across Linear, custom integrations).
- **Idempotent mutations**: use `addProjectV2ItemById` (returns existing ID if item already present) and `updateProjectV2ItemFieldValue` as two separate calls — GitHub does not support combining them.
- **Checksum-based change detection**: hash the plan spec, hash observed GitHub state, skip reconciliation if they match (reduces API consumption).
- **Escape hatches are required**: Override drift class exists for intentional divergence; pure enforcement with no escape hatch fails during incidents.
- **No inline field IDs**: field IDs change when a project is recreated or fields are renamed/deleted; always resolve from the bootstrap registry.

## Existing gaps (from `ChatGPT-Template to GitHub Mapping`)

Six gaps identified in current system, not yet closed:
1. No formal mapping spec contract (JSON/YAML)
2. Step→Issue creation not deterministic; no stable `step_id ↔ issue_number` linkage table
3. Milestones ambiguous (phases vs. delivery checkpoints — should be delivery groupings only)
4. No explicit "one step = one issue" granularity rule enforced
5. No enforcement that all work originates from template (free-floating issues can bypass plan)
6. Evidence artifacts not linked to GitHub Issues/PRs
