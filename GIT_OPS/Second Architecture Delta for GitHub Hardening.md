# Second Architecture Delta for GitHub Hardening

## Context and scope of the patch

This delta patches the previously merged architecture delta by hardening the “GitHub projection + automation” layer to the same determinism standard as the core phase-plan system (contracts, gates, evidence, worktree isolation, fail-closed). fileciteturn4file6 fileciteturn4file0

The assessment you provided is correct about the gap: the template→GitHub mapping is conceptually strong (phase→field, step→issue, gate→CI check, execution→PR), but the last-mile enforcement is still too descriptive, token-fragile, and environment-coupled. fileciteturn4file2 fileciteturn4file6

This delta explicitly adds five missing constructs:

- GitHub App authentication model
- Field bootstrap registry model
- Phase advancement evaluator
- Runner platform policy
- Sync governance rules

It also aligns these constructs with your “SSOT-to-execution-surface projection” framing: **projection is easy; reconciliation is where systems break**, so the governing primitive must be a reconciliation controller (observe → diff → act → report). fileciteturn4file1

## Delta identity and intent

**Delta ID**: `ARCH-DELTA-NPP-GITHUB-HARDENING-002`  
**Patches**: `ARCH-DELTA-NPP-GITWORKTREE-PROGRAMSPEC-001` (the prior merged delta) fileciteturn4file12  
**Primary outcome**: GitHub automation becomes **portable, repeatable, org-safe, project-recreation-safe**, and **level-triggered** (self-healing) rather than edge-triggered (webhook-miss fragile). fileciteturn4file1

**Non-negotiable invariants carried forward**:
- single-writer authority for global state
- delta-only workers
- explicit scope declarations
- no implied behavior
- evidence-based completion criteria fileciteturn4file12 fileciteturn4file11

This delta adds GitHub-specific versions of those invariants.

## GitHub App authentication model

### Why this is mandatory

GitHub’s own documentation states plainly that `GITHUB_TOKEN` is repository-scoped and **cannot access Projects**; to access projects you must use either a GitHub App (recommended for organization projects) or a personal access token (recommended for user projects). citeturn2view0

Your assessment flags PAT reliance as a production liability at the scale you’re targeting (autonomous phase transitions, CI-triggered field updates, multi-repo workflows), and recommends GitHub App auth as the correct replacement. fileciteturn4file6

### Formal rule

**LAW-GH-001 — APP-FIRST AUTHENTICATION**  
All automation that reads/writes Projects must authenticate via a GitHub App installation token. PATs may exist only as an explicitly declared exception path.

This aligns with GitHub’s own recommended approach for organization projects. citeturn2view0

### App privilege requirements

GitHub’s Projects automation guide includes a critical note: you must grant the App **read/write permission to organization projects**; repository projects permission is not sufficient. citeturn2view2

Minimum permissions should be selected (“least privilege”) per GitHub’s guidance on GitHub App permissions. citeturn6view2

### Token issuance pattern

Use an installation token per workflow run (ephemeral credential):

- Use `actions/create-github-app-token` to generate the installation token inside GitHub Actions. citeturn2view2turn0search0
- The action generates a token via the `/app/installations/{installation_id}/access_tokens` endpoint. citeturn5search1turn5search5
- Installation tokens expire about one hour after creation by design, so the system must generate new tokens rather than attempting token reuse. citeturn6view1

### Rate-limit implications you must codify

- GitHub documents that GraphQL rate limiting is points-based and depends on auth type; `GITHUB_TOKEN` has its own lower GraphQL limit (1,000 points/hour per repository) while GitHub App installations have higher limits depending on context. citeturn6view0  
- GitHub also enforces secondary rate limits (concurrency caps, points per minute, and content-creation limits), and recommends using headers when possible. citeturn6view3turn6view0

**Enforcement addition**: the orchestration layer must include `RATE_LIMIT_BUDGET` and `BACKOFF_POLICY` as first-class configuration, not ad hoc retry logic. This is required to keep autonomous reconciliation stable under load. citeturn6view3turn6view0

### Required artifacts and programs

Implement auth as a **ProgramSpec** (declarative) program, not a bespoke script:

- `programs/GH_AUTH_ISSUE_INSTALLATION_TOKEN.spec.json`
  - category: Transport
  - inputs: app_id var key, private key secret key, installation scope selector
  - outputs: token envelope with expiry timestamp
  - fingerprint: app_id + installation id + spec version
  - locks: none (read-only)
  - evidence: token issuance log (redacted) fileciteturn4file10

## Field bootstrap registry model

### Why this is mandatory

Your current workflows use environment-bound IDs like `PROJECT_NODE_ID`, `STATUS_FIELD_ID`, `PHASE_FIELD_ID`, and option IDs. The assessment is right that **field-ID bootstrap is missing**, and without it the system becomes fragile when projects are recreated, copied, migrated, or fields are renamed. fileciteturn4file6

GitHub’s own Projects API docs explicitly state that to update a field you must know:
- the project node ID,
- the field node ID,
- and for single-select and iteration fields, the option/iteration IDs. citeturn3view1turn3view3

GitHub also provides an official GraphQL query pattern to retrieve the first N fields for a project, including options and iteration configuration. citeturn3view1turn3view3

### Formal rule

**LAW-GH-002 — NO INLINE FIELD IDS**  
No automation step may hardcode project field IDs or option IDs. All IDs must come from a generated, versioned `github_field_registry.json`.

### Registry contents

Create a generated registry file that is the single source of truth for IDs:

`config/github_field_registry.json` should include at minimum:

- `project_node_id` (and owner org/user)
- `field_name → field_id` map
- for each single-select field: `option_name → option_id` map
- for each iteration field: `iteration_start_date/name → iteration_id` map
- `generated_at`
- `generator_version`
- `api_version`
- `registry_fingerprint`

This is directly supported by the GitHub query examples in “Using the API to manage Projects.” citeturn3view1turn3view3turn1view3

### Bootstrap lifecycle

Bootstrap must be **repeatable and self-healing**:

- Run on demand (manual trigger) and automatically on:
  - project recreation
  - projection failure that indicates unknown field IDs
  - scheduled reconciliation (e.g., daily)
- If registry is missing or stale, **fail closed** on any field-update operation and require bootstrap to run first. (This mirrors your plan-lint and gate discipline.) fileciteturn4file20turn4file11

### Required programs and gates

Define these as ProgramSpecs:

- `programs/GH_FIELDS_DISCOVER.spec.json`  
  - category: Gate (binary outcome)
  - inputs: project_node_id
  - steps: GraphQL fields query
  - outputs: `github_field_registry.json`
  - pass criteria: required fields present, required options present citeturn3view1turn3view3 fileciteturn4file10

- `programs/GH_FIELDS_VALIDATE.spec.json`  
  - category: Gate
  - inputs: registry file
  - pass criteria: schema-valid + contains required names fileciteturn4file10

Add gates:

- `GATE_GH_FIELD_REGISTRY_PRESENT`
- `GATE_GH_FIELD_REGISTRY_SCHEMA_VALIDATE`
- `GATE_GH_FIELD_REGISTRY_COVERAGE_VALIDATE`

These act like your required-files/gates/evidence map pattern, but scoped to GitHub governance. fileciteturn4file11

## Phase advancement evaluator

### Why this must exist as a separate authority

The evaluation correctly identifies a key difference:

- syncing a phase field based on an event is not the same as
- deterministically proving phase exit criteria are satisfied and then advancing phase. fileciteturn4file6

Your phase-plan system already assumes composite lifecycle logic (gates, postconditions, reconciliation states). The GitHub layer must not reduce phase advancement to incidental side effects. fileciteturn4file6turn4file2

### Formal rule

**LAW-GH-003 — PHASE ADVANCEMENT IS COMPOSITE**  
Phase transitions may occur only through the Phase Advancement Evaluator and must be backed by a stored decision artifact.

### Evaluator inputs and decision model

Inputs:
- plan package: phase definitions, step-to-phase bindings, exit criteria
- GitHub observed state: issues closed/open, required checks, PR merge states, evidence markers
- optional: project milestone state (only if a phase explicitly requires a delivery checkpoint)

Observed-state acquisition must use the official Projects primitives:
- `addProjectV2ItemById` and `updateProjectV2ItemFieldValue` for item/field mutations (not bundled in one call). citeturn1view3turn6view3
- idempotency guarantee: adding an existing item returns the existing item ID (enables convergent “ensure-in-project” behavior). citeturn1view3

### Level-triggered rather than edge-triggered

Your “SSOT-to-execution-surface projection” analysis stresses that robust systems are level-triggered (converge to correct current state), not edge-triggered (dependent on missed events). fileciteturn4file1

So the evaluator must run:
- on key events (PR merged, check suite completed, issue closed)
- and on schedule (reconciliation loop), so missed events do not create permanent divergence. fileciteturn4file1

### Outputs

- `phase_advancement_report.json` (machine-consumable)
- `phase_transition_decision.json` (the exact rule outcomes)
- optional: GitHub comment on the phase root issue with a short decision summary and link to evidence artifacts

### Required programs and gates

Define:
- `programs/GH_PHASE_ADVANCEMENT_EVALUATOR.spec.json` (Phase category or Gate category, depending on your taxonomy)
  - locks: project write lock + phase field lock
  - pass criteria: decision artifact emitted and (if advancing) the project field update succeeded fileciteturn4file10

Add gates:
- `GATE_GH_PHASE_EVALUATION_COMPLETE`
- `GATE_GH_PHASE_ADVANCE_APPLIED_OR_EXPLICITLY_BLOCKED`

## Runner platform policy

### Why this must be explicit

The evaluation is right that you currently have a mismatch: lots of automation assumes GitHub-hosted Linux runners, while parts of your broader architecture and local sync concepts are Windows-centric. The policy must explicitly separate “platform-agnostic control plane work” from “platform-dependent execution work.” fileciteturn4file6

GitHub’s runner reference explicitly lists supported GitHub-hosted runner labels (`ubuntu-latest`, specific Ubuntu versions, `windows-latest`, and others) and warns that `-latest` images are the latest stable images GitHub provides, not necessarily the OS vendor’s latest release. citeturn4view0

GitHub’s self-hosted runner documentation notes practical operational constraints:
- if no matching runner is available, jobs can remain queued until a 24-hour timeout expires,
- self-hosted runners have auto-update behavior (or must be updated within 30 days if auto-update is disabled). citeturn4view1

### Formal rule

**LAW-RUN-001 — PLATFORM-SPLIT IS REQUIRED**  
Every ProgramSpec must declare its allowed runner class:
- `linux_hosted`
- `windows_hosted`
- `self_hosted_windows`
- `self_hosted_linux`
- `self_hosted_ephemeral`

### Policy mapping

- Use GitHub-hosted runners (`ubuntu-latest`) for:
  - GraphQL/REST operations
  - plan validation gates
  - registry rebuild and schema validation
  - GitHub projection and reconciliation workflows  
  This keeps automation consistent and reduces environmental drift. citeturn4view0turn2view2

- Use self-hosted Windows runners for:
  - Windows-only automation (PowerShell workflows, local filesystem sync, Windows toolchain requirements)  
  and route via labels. GitHub supports applying custom labels to self-hosted runners. citeturn1view4

Operational rule:
- Any workflow that targets a self-hosted runner must include an explicit fallback strategy, because a missing runner can leave jobs queued for up to 24 hours. citeturn4view1

### Required artifacts

- `policies/runner_policy.yaml`
  - defines allowed runner classes per program category
  - defines labels for self-hosted groups (e.g., `self-hosted`, `windows`, `npp-sync`, `npp-exec`) citeturn1view4turn4view1

## Sync governance rules

### Why this must be formal

Your mapping doc explicitly calls out “no formal mapping spec” and “sync direction not clearly enforced.” fileciteturn4file2

Your cross-system architecture analysis is even clearer: what typically breaks is reconciliation (drift, bidirectional conflicts, impedance mismatch, lack of escape hatches). fileciteturn4file1

### Governance model

Define the following ownership sets:

- **Plan-owned**
  - decomposition, step contracts, phase structure, gate requirements, evidence requirements  
  (GitHub is not allowed to author these.) fileciteturn4file2turn4file1
- **GitHub-owned**
  - assignees, review conversations, comment threads
- **Automation-only fields**
  - Phase, Status, EvidenceState, DeterminismState, PlanHash, ProjectionVersion  
  Manual edits here are treated as drift. fileciteturn4file6turn4file2

### Reconciliation loop specification

Adopt the explicit reconciliation pattern described in your SSOT projection analysis: observe → diff → act → report. fileciteturn4file1

**Rule**: Recovery must be self-healing. If a webhook is missed, the scheduled reconciliation pass must correct drift (level-triggered behavior). fileciteturn4file1

### Drift classes

Use a deterministic drift taxonomy so the system never has to “guess” intent:

- **Allowed drift**
  - GitHub-owned edits (assignee changes, comments)
- **Violation drift**
  - changes to automation-only fields
  - unlinked “free-floating” issues that look like execution work but lack step IDs
- **Orphan drift**
  - GitHub items without a corresponding plan node
- **Missing drift**
  - plan nodes without a corresponding GitHub artifact
- **Override drift**
  - explicitly approved deviations

This is directly aligned with the “projection breaks in reconciliation” failure analysis: you need an escape hatch policy and non-ambiguous classification. fileciteturn4file1

### Convergent mutation rules

Govern all mutations by convergence principles supported by GitHub’s API semantics:

- **Upsert behavior**
  - “ensure item exists” uses `addProjectV2ItemById`; if it already exists, GitHub returns the existing item ID (idempotent). citeturn1view3
- **Two-step mutation**
  - GitHub requires separate calls to add an item vs update field values; do not attempt to combine. citeturn1view3
- **Field constraints**
  - `updateProjectV2ItemFieldValue` can’t change assignees/labels/milestone/repository because those belong to issues/PRs, so governance must treat those as separate mutation channels. citeturn1view3
- **Backoff and budgets**
  - must obey GraphQL and REST rate limits (primary and secondary) with backoff and concurrency ceilings. citeturn6view0turn6view3

### Checksum and version comparison rules

Add two deterministic fields to GitHub Project items (project custom fields, not issue labels):

- `PlanHash` (sha256 of canonical plan package / projection manifest)
- `ProjectionVersion` (monotonic integer or semantic version)

Reconciliation compares:
- desired `PlanHash` and `ProjectionVersion` (from plan package)
against
- observed values in GitHub fields

If mismatch:
- classify drift
- apply convergent correction or require explicit override based on drift class

This is precisely the “diff desired vs observed” model described in your projection analysis. fileciteturn4file1

## Implementation artifacts and gates

### New required files

- `config/github_field_registry.json`  
- `config/github_projection_registry.json`  
- `config/github_override_registry.json`  
- `policies/github_sync_governance.yaml`  
- `policies/runner_policy.yaml`  
- `schemas/github_field_registry.schema.json`  
- `schemas/github_projection_manifest.schema.json`  
- `schemas/reconciliation_report.schema.json`  
- `schemas/phase_advancement_report.schema.json`  

These mirror your existing “required files / gates / evidence map” approach from the worktree parallel execution system. fileciteturn4file11turn4file12

### New workflows

- `bootstrap-github-fields.yml`  
  - runs discovery query and writes registry output  
  - fails closed if required fields/options missing  
  - uses GitHub App token citeturn2view2turn3view1

- `phase-advancement-evaluator.yml`  
  - runs composite evaluator  
  - writes decision artifacts  
  - updates Phase field when allowed fileciteturn4file6

- `ssot-drift-reconciliation.yml`  
  - scheduled + event-triggered  
  - classifies drift and reconciles  
  - emits reconciliation report  
  (level-triggered self-healing loop) fileciteturn4file1

### New ProgramSpecs

All of these should be declarative ProgramSpecs to keep behavior configuration-driven and replayable. fileciteturn4file10

- `GH_AUTH_ISSUE_INSTALLATION_TOKEN`
- `GH_FIELDS_DISCOVER`
- `GH_FIELDS_VALIDATE`
- `GH_PROJECTION_GENERATE`
- `GH_PROJECTION_APPLY`
- `GH_RECONCILE_DRIFT`
- `GH_PHASE_ADVANCE_EVALUATE`

### New gates

- `GATE_GH_APP_AUTH_AVAILABLE`
- `GATE_GH_FIELD_REGISTRY_VALID`
- `GATE_GH_PROJECTION_MANIFEST_VALID`
- `GATE_GH_RECONCILIATION_COMPLETE`
- `GATE_GH_PHASE_ADVANCEMENT_DECIDED`

These are the GitHub-level equivalents of your existing strict gates and evidence requirements. fileciteturn4file11turn4file20

## The patched architectural result

After applying `ARCH-DELTA-NPP-GITHUB-HARDENING-002`, your GitHub layer stops being a set of “helpful scripts” and becomes a governed subsystem with:

- App-first authentication and short-lived credentials (no PAT dependency by default) citeturn2view0turn6view1
- deterministic bootstrap of project/field/option IDs so project recreation is survivable citeturn3view1turn3view3
- a composite phase advancement authority, not incidental event-based updates fileciteturn4file6
- explicit runner platform policy and label-based routing for self-hosted execution where required citeturn4view0turn1view4turn4view1
- a level-triggered reconciliation controller with drift classes, overrides, convergent mutations, and hash/version comparison fileciteturn4file1 citeturn1view3

This directly patches the “last-mile determinism” gaps called out by the evaluation, without changing the core phase-plan contract architecture. fileciteturn4file6turn4file0