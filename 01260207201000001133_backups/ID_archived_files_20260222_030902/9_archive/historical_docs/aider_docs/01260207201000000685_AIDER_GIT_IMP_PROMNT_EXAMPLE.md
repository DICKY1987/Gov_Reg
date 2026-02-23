# IMP_PLAN_3 — Aider-Ready Implementation Plan

This plan restructures your original phases into an Aider-optimized, GitHub-native format:
- Actionable for Aider (clear, atomic tasks with acceptance criteria and suggested prompts).
- Clean mapping to GitHub (milestones, epics, issues, labels, project board).
- Strong traceability: Vision → Goals → Milestones → Epics → Issues → CI gates.

Use this document as PROJECT_PLAN.md (or keep the filename) and create issues from the “Issue Seeds” blocks.

---

## 0) Snapshot (Executive Overview)

- Vision: Safely migrate legacy docs to a new canonical docs-v2 structure with ULID anchors, MFID-based content verification, sidecars, automated redirects, and CI guards; enable one‑click copy‑verify‑prune flow and safe cutover.
- Outcomes:
  - Deterministic IDs (ULID) for paragraphs/sections; MFID cache for content identity.
  - Validated mapping and redirects; dual CI during migration; automated prune with safeguards.
  - Contributor experience: “Where did my file go?” mapping, sidecars, guardrails.
- Release Mode: Milestones M0–M6 (aligning to Phase 0–6).
- Aider Usage: Target S/M sized issues; explicit file paths; tests first; acceptance criteria per task.

---

## 1) Strategic Goals

- G1 Reliability: Zero data loss in migration; verifiable parity (render + links) before prune.
- G2 Deterministic Identity: ULIDs for sections/paragraphs; MFIDs for files; collision‑free registry.
- G3 One‑Click Migration: CLI implements dry‑run → apply (copy) → verify → prune.
- G4 Traceable Redirects: Complete redirect map across hosting targets (Netlify, Nginx, GH Pages).
- G5 CI Governance: Guards for drift, MFID checks, sidecar regeneration; block unsafe edits.
- G6 Contributor Experience: Clear docs and PR workflow with sidecars; “where did my file go?” table.

Each Goal maps to at least one Milestone and multiple Epics.

---

## 2) Milestones (Release Groupings)

| Milestone | Phase | Target | Exit Criteria |
|---|---|---|---|
| M0 Foundation & Safety | 0 | YYYY‑MM‑DD | .migration/ scaffolded; snapshot complete; identity & rollback policies defined |
| M1 Tooling (One‑Click) | 1 | YYYY‑MM‑DD | CLI minimally functional; registry + MFID cache; validation suite green on sample |
| M2 Dry‑Run | 2 | YYYY‑MM‑DD | mapping.yaml draft; redirects preview; suite-index bootstrap; validation report with no criticals |
| M3 Apply & Parallel Validation | 3 | YYYY‑MM‑DD | docs-v2 created; copied with sidecars; dual CI enabled; automated gates pass |
| M4 Automated Prune | 4 | YYYY‑MM‑DD | prune-plan.yaml generated and executed with all safety checks satisfied |
| M5 Cutover & Redirects | 5 | YYYY‑MM‑DD | docs-v2 canonical; redirects emitted; contributor docs published; branch protections live |
| M6 Cleanup | 6 | YYYY‑MM‑DD | dual CI removed; periodic validation scheduled; suite versions tagged |

Note: Replace dates as planning proceeds.

---

## 3) Epics

### Epic: FND — Foundation & Safety (M0, G1, G2)
- Narrative: Establish migration scaffolding, identity & rollback policies, and repository snapshot.
- Deliverables:
  - .migration/ with mapping.yaml (initial), transaction.log, validation-report.md
  - Snapshot scripts: scripts/get_doc_versions.py output, file list, checksums
  - Identity policies: ULID registry and anchor policy (ULID canonical; slug optional; p‑n positional only)
  - Rollback policy (triggers: guard failures, unresolved links, parity breach, redirect gaps)
- Risks: Hidden identity collisions; incomplete rollback data

Issue Seeds:
1) [FND] Create .migration/ scaffolding (mapping.yaml, transaction.log, validation-report.md)
- Files: .migration/
- Acceptance:
  - .migration/mapping.yaml (valid YAML, empty mapping scaffold)
  - .migration/transaction.log (created, append‑only format doc)
  - .migration/validation-report.md (header + section stubs)
- Suggested Aider Prompt:
  - Create .migration/ with mapping.yaml, transaction.log, validation-report.md and document file formats in header comments. No functional logic required.

2) [FND] Repository snapshot utility
- Files: scripts/snapshot_repo.py; scripts/get_doc_versions.py (if exists)
- Acceptance:
  - snapshot_repo.py outputs: file inventory, checksums, git commit, versions from get_doc_versions.py
  - Saves to .migration/snapshots/<timestamp>/{files.json, checksums.json, versions.json}
  - Tests cover at least listing and checksum generation
- Suggested Aider Prompt:
  - Implement scripts/snapshot_repo.py to produce inventory, checksums, and versions into .migration/snapshots/<ts>. Add basic tests.

3) [FND] Identity & rollback policy docs
- Files: docs-v2/.index/IDENTITY_POLICY.md, docs-v2/.index/ROLLBACK_POLICY.md
- Acceptance:
  - ULID canonical rule, slug optional, p‑n positional only
  - Rollback triggers enumerated with example playbook
- Suggested Aider Prompt:
  - Author policy markdown files with specified content; cross‑link from README.

---

### Epic: MIG — Tooling (One‑Click Migration) (M1, G3, G2)
- Narrative: Implement CLI and core services: registry, MFID cache, validation suite, optional sync.
- Deliverables:
  - CLI: python -m tools.spec_migrate.migrate
  - Flags: --source, --mode copy, --volume-map, --dry-run, --backup-dir, --preserve-timestamps, --transaction-log, --generate-redirect-map, --validate-history, --prune-legacy-on-success, --confirm
  - Services: ulid_registry.py, MFID cache (.mfid-cache/), validate_migration.py, sync.py (optional)

Issue Seeds:
1) [MIG] CLI skeleton with argument parsing
- Files: tools/spec_migrate/migrate.py
- Acceptance:
  - Parses flags listed above; prints plan in --dry-run; no side effects
  - Help text documents modes and flags
  - Unit test for arg parsing and dry-run output
- Suggested Aider Prompt:
  - Scaffold tools/spec_migrate/migrate.py with argparse for flags. Implement dry-run planner stub. Add tests.

2) [MIG] ULID registry with deterministic seeding and collision checks
- Files: tools/spec_migrate/ulid_registry.py; registry/
- Acceptance:
  - Deterministic ULID generation based on (path + first‑git‑intro commit)
  - Collision detection with persisted registry (registry/ulids.jsonl)
  - Unit tests for determinism and collisions
- Suggested Aider Prompt:
  - Implement ulid_registry.py with deterministic ULID(seed) and persistent registry. Add tests.

3) [MIG] MFID cache for files (.mfid-cache/)
- Files: tools/spec_migrate/mfid_cache.py; .mfid-cache/
- Acceptance:
  - Incremental and parallel hashing; persistent cache keyed by path + mtime + size
  - Unit tests simulate cache hits/misses
- Suggested Aider Prompt:
  - Implement MFID cache with parallel hashing using concurrent.futures; write tests.

4) [MIG] Validation suite
- Files: tools/spec_migrate/validate_migration.py
- Acceptance:
  - Parity checks (render diff tolerance), cross‑refs, tags, link resolution
  - CLI function importable by CI
  - Tests covering at least link & cross‑ref checks against small fixture set
- Suggested Aider Prompt:
  - Implement validate_migration.py with hooks for parity and link checks; add tests with 5–10 file sample.

5) [MIG] Optional legacy sync utility
- Files: tools/spec_migrate/sync.py
- Acceptance:
  - Mirrors changes from legacy docs to v2 during parallel period
  - Dry‑run supported
- Suggested Aider Prompt:
  - Implement basic one‑way sync with dry‑run and logging.

---

### Epic: DRY — Dry‑Run Plan (M2, G3, G1)
- Narrative: Generate no‑change plan artifacts.
- Deliverables:
  - .migration/mapping.yaml (old → new)
  - Sidecar generation preview and suite-index bootstrap at docs-v2/.index/suite-index.yaml
  - Redirect preview: .migration/redirects.map + Netlify _redirects, nginx.map, redirect_from.yml
  - Tree diff + parity in .migration/validation-report.md
- Gate: Zero collisions, zero broken links, guard-simulate clean, parity within threshold

Issue Seeds:
1) [DRY] mapping.yaml draft generator
- Files: tools/spec_migrate/mapping_draft.py; .migration/mapping.yaml
- Acceptance:
  - Proposes volume based on “Volume Mapping Defaults”
  - Writes mapping.yaml with reason codes
- Suggested Aider Prompt:
  - Implement generator that proposes old→new path mapping using volume heuristics; write to .migration/mapping.yaml.

2) [DRY] suite-index bootstrap
- Files: tools/spec_migrate/suite_index.py; docs-v2/.index/suite-index.yaml
- Acceptance:
  - Index lists all new doc entries, volumes, expected sidecars
  - Valid YAML schema; tests for schema validation
- Suggested Aider Prompt:
  - Implement suite-index bootstrap and validator; generate docs-v2/.index/suite-index.yaml.

3) [DRY] Redirect previews
- Files: tools/spec_migrate/redirects.py; .migration/redirects.map; _redirects; nginx.map; redirect_from.yml
- Acceptance:
  - All preview artifacts generated without writing to web config paths unless confirmed
  - Tests for path normalization and collision handling
- Suggested Aider Prompt:
  - Generate redirect preview artifacts from mapping.yaml; include collision detection.

---

### Epic: APP — Apply (Copy Mode) & Parallel Validation (M3, G3, G1, G5)
- Narrative: Execute copy, generate sidecars, ULIDs, and enable dual CI.
- Deliverables:
  - Create structure: docs-v2/.index/, docs-v2/source/<volumes>/, ids/, .ledger/, registry/
  - Copy files per mapping; unknowns → docs-v2/source/99-imported/
  - Generate sidecars; finalize suite-index; assign ULIDs; backfill into sidecars and index
  - Dual CI: validate both legacy and v2; pre-commit sidecar regen

Issue Seeds:
1) [APP] Execute copy mode with unknowns fallback
- Files: tools/spec_migrate/migrate.py
- Acceptance:
  - --mode copy copies per mapping; unknowns go to 99-imported; preserves timestamps if flag set
  - Transaction log entries appended
- Suggested Aider Prompt:
  - Implement copy‑mode execution with fallback logic and transaction logging.

2) [APP] Sidecar generator + ULID assignment
- Files: tools/spec_migrate/sidecar.py; ids/
- Acceptance:
  - Paragraph and section ULIDs assigned; sidecars updated; suite-index updated
  - Idempotent over re-runs
- Suggested Aider Prompt:
  - Implement sidecar generation and ULID backfill into index; ensure idempotency.

3) [APP] Dual CI enablement
- Files: .github/workflows/docs-guard.yml, .github/workflows/mfid-check.yml
- Acceptance:
  - Validates both legacy and v2 structures
  - Pre-commit hook regenerates sidecars on staged .md
- Suggested Aider Prompt:
  - Add CI workflows and pre-commit config to validate legacy and v2; regenerate sidecars on commit.

---

### Epic: PRN — Automated Prune (M4, G1, G3)
- Narrative: Safely delete legacy duplicates post‑verification.
- Safety Checks: For each mapping pair, MFIDs match, paragraph counts match, cross‑refs pass, redirects present
- Deliverables:
  - .migration/prune-plan.yaml; prune execution via --confirm
  - transaction.log entries; re‑run full validation post‑prune

Issue Seeds:
1) [PRN] Prune plan generator and executor
- Files: tools/spec_migrate/prune.py; .migration/prune-plan.yaml
- Acceptance:
  - Generates deletions only when all verification checks pass
  - Executes git rm and logs to transaction.log
- Suggested Aider Prompt:
  - Implement prune plan creation and confirmation‑gated execution with safety checks.

---

### Epic: CTO — Cutover & Redirects (M5, G4, G6)
- Narrative: Make docs‑v2 canonical, freeze legacy; emit redirects and contributor docs; enforce protections.
- Deliverables:
  - Emitted redirects: Netlify _redirects, Nginx map, GH Pages redirect_from YAML, JSON bundle
  - Contributor docs: mapping table, addressing scheme, PR workflow with sidecars
  - Branch protection: guard + MFID checks required; block direct suite‑index edits

Issue Seeds:
1) [CTO] Emit production redirects
- Files: tools/spec_migrate/redirects.py (prod mode); output files at repo root or deploy dir
- Acceptance:
  - All target formats emitted from mapping.yaml
  - Validation script confirms resolvable redirects
- Suggested Aider Prompt:
  - Extend redirects tool to output production artifacts and add validation.

2) [CTO] Contributor documentation
- Files: docs-v2/.index/CONTRIBUTING_DOCS_MIGRATION.md
- Acceptance:
  - “Where did my file go?” table from mapping.yaml
  - Addressing scheme tutorial; PR workflow with sidecars
- Suggested Aider Prompt:
  - Author contributor doc sourced from mapping.yaml; include table and workflows.

3) [CTO] Branch protections and CODEOWNERS
- Files: .github/CODEOWNERS; repo settings (manual)
- Acceptance:
  - CODEOWNERS restrict suite-index.yaml edits; CI required checks configured
- Suggested Aider Prompt:
  - Add CODEOWNERS entries to require review for suite-index.yaml and workflows.

---

### Epic: CLN — Cleanup (M6, G1)
- Narrative: Turn off dual CI, keep redirects live; schedule periodic suite validation; tag suite versions.
- Deliverables: CI removal PR, scheduled validation job, release tagging with suite versions

Issue Seeds:
1) [CLN] Remove dual CI and add schedule
- Files: .github/workflows/docs-guard.yml, etc.
- Acceptance:
  - Legacy checks removed; scheduled validation of v2 weekly
- Suggested Aider Prompt:
  - Modify CI to remove legacy jobs and add scheduled validator.

2) [CLN] Suite version tagging
- Files: tools/spec_migrate/versioning.py
- Acceptance:
  - Tag suites on release; write release notes entry to HISTORY/CHANGELOG
- Suggested Aider Prompt:
  - Implement simple version tagging for suite-index and changelog update.

---

### Epic: MAP — Volume Mapping Defaults (Cross‑cutting, M2–M3, G3)
- Heuristics:
  - 01-architecture: “ARCHITECTURE”, “overview”, micro‑kernel
  - 02-operating-contract: “VERSIONING_OPERATING_CONTRACT”
  - 03-plugin-contract: “plugin”, “manifest”, “contract”
  - 04-data-contracts: “schema”, “card”, “ledger”, “registry”
  - 05-process: “workflow”, “process”, BPMN/DMN
  - 06-policy-as-code: docs-guard.yml, policy/rules
  - 07-conformance-kit: “conformance”, “fixtures”, “tests” overview
  - 08-ci-cd-gates: CI workflows and gates
  - 09-observability-slos: “observability”, “SLO”
  - 10-plan-traceability: “plan/”, PBS, RTM
  - 11-developer-experience: “guide”, “quickstart”, “devx”
  - 12-security-supply-chain: “security”, “sbom”
  - 13-implementation-checklists: “checklist”, acceptance
  - 14-taxonomy-autoindex: doc-tags.yml, taxonomy, indexers
  - 15-scripts-integration: scripts, SDK examples
  - Fallback: 99-imported + TODOs in report

Issue Seeds:
1) [MAP] Implement volume classifier
- Files: tools/spec_migrate/volume_map.py
- Acceptance:
  - Deterministic classification with override rules; unit tests with fixtures
- Suggested Aider Prompt:
  - Implement classifier per heuristics and tests.

---

### Epic: IDS — Anchors & IDs (Cross‑cutting, M3, G2)
- Paragraph: id=ULID (canonical, specid://); slug optional; anchor p‑n positional only
- Section: id=ULID; key numeric “1.1”; title from first H1 or filename

Issue Seeds:
1) [IDS] ULID assignment for sections and paragraphs
- Files: tools/spec_migrate/sidecar.py; docs-v2/.index/suite-index.yaml
- Acceptance:
  - Deterministic IDs; persisted to sidecars and suite-index; tests ensure stability
- Suggested Aider Prompt:
  - Extend sidecar generator to assign section/paragraph ULIDs and update index.

---

### Epic: CI — CI/CD Updates (Cross‑cutting, M3–M5, G5)
- docs-guard: run tools.spec_indexer.indexer --verify --strict and tools.spec_guard.guard on v2
- mfid-check: PRs touching docs-v2/source/** fail on drift; bot comment with ULIDs/slugs
- render: publish rendered single-file artifact for reviewers
- pre-commit: regenerate sidecars for staged .md

Issue Seeds:
1) [CI] docs-guard workflow
- Files: .github/workflows/docs-guard.yml
- Acceptance:
  - Runs indexer and guard; fails on violations
- Suggested Aider Prompt:
  - Create docs-guard workflow to run strict verification tools.

2) [CI] mfid-check workflow + bot comment
- Files: .github/workflows/mfid-check.yml
- Acceptance:
  - Detects MFID drift; posts comment listing affected ULIDs/slugs
- Suggested Aider Prompt:
  - Implement workflow that runs MFID check and posts PR comment.

3) [CI] render artifact for review
- Files: .github/workflows/render-preview.yml
- Acceptance:
  - Produces single-file preview; uploads as PR artifact
- Suggested Aider Prompt:
  - Add render workflow to build and upload a combined preview.

---

## 4) Automated Flow (CLI)

- Dry‑run:
  - spec_migrate --source docs --mode copy --volume-map mapping.yml --dry-run
- Apply:
  - spec_migrate --source docs --mode copy --backup-dir .backup --transaction-log .migration/transaction.log --generate-redirect-map --validate-history --confirm
- Prune:
  - spec_migrate --prune-legacy-on-success --confirm

Verification checks (must pass before prune):
- File MFIDs equal; sidecar paragraph counts equal; ULID sets equal
- Resolver maps spec:// and specid://
- External links valid
- Rendered parity within tolerance

---

## 5) GitHub Mapping

- Milestones:
  - M0 Foundation & Safety, M1 Tooling, M2 Dry‑Run, M3 Apply & Parallel, M4 Prune, M5 Cutover, M6 Cleanup
- Labels:
  - area/migrate, area/registry, area/ids, area/validation, area/ci, area/docs
  - type/feature, type/refactor, type/test, type/docs, type/tooling
  - size/s, size/m, size/l
  - priority/p0, p1, p2
  - status/blocked
- Project Board Columns:
  - Backlog → Ready → In Progress → AI Proposed → Review → Merged → Verify → Done
- Commit Convention (AI):
  - Aider: <area>: <action>

---

## 6) Acceptance Criteria Pattern (for Issues)

- Files (explicit paths)
- Behavior with flags (happy path + dry‑run path)
- Idempotency for generators
- Test files/fixtures added with clear scenarios
- Validation integration (CI job names)
- Transaction logging for mutating operations

---

## 7) Risk & Rollback

- Rollback triggers:
  - Guard failures, unresolved links, content parity breach, redirect gaps
- Playbook:
  - Halt prune; revert last migration commit; restore from .backup; compare snapshots
- Logs:
  - Append all mutating steps to .migration/transaction.log with timestamps

---

## 8) Contributor Experience

- Docs:
  - “Where did my file go?” table from mapping.yaml
  - Addressing scheme tutorial (spec://, specid://)
  - PR workflow with sidecars; how to interpret CI failures
- Protections:
  - Require docs-guard + mfid-check
  - Block direct edits to suite-index.yaml (CODEOWNERS)

---

## 9) Glossary

- ULID: Canonical paragraph/section identifier; deterministic; used in specid:// links
- MFID: Content identity for files (hash, with cache); used for parity and drift checks
- Sidecar: Metadata file per doc holding IDs, counts, anchors, tags
- Suite Index: docs-v2/.index/suite-index.yaml listing documents, volumes, and metadata

---

## 10) Initial Aider-Ready Backlog (Top 10)

1) [FND] .migration scaffolding (S) — M0 — area/migrate type/tooling
2) [FND] Snapshot utility (S) — M0 — area/migrate type/tooling
3) [MIG] CLI skeleton + dry‑run (S) — M1 — area/migrate type/tooling
4) [MIG] ULID registry (S) — M1 — area/ids type/feature
5) [MIG] MFID cache (M) — M1 — area/validation type/feature
6) [MIG] Validation suite (M) — M1 — area/validation type/feature
7) [DRY] mapping.yaml generator (S) — M2 — area/migrate type/feature
8) [DRY] suite-index bootstrap (S) — M2 — area/migrate type/feature
9) [APP] Copy mode execution (M) — M3 — area/migrate type/feature
10) [CI] docs-guard workflow (S) — M3 — area/ci type/tooling

Each of these can be created as GitHub issues using the Issue Seeds above.

---

## 11) Notes from Original Plan (Verbatim Requirements Preserved)

- Phase 0: Foundation & Safety
  - Snapshot and controls:
    - Create .migration/ with mapping.yaml, transaction.log, validation-report.md.
    - Snapshot current state: scripts/get_doc_versions.py output, file list, checksums.
  - Identity policies:
    - ULID registry with deterministic seeding (path + first-git-intro commit) and collision checks.
    - Anchor policy: use ULID as canonical anchor for references; optional slug for readability; keep p-n only as positional metadata.
  - Rollback policy:
    - Rollback triggers: guard failures, unresolved links, content parity breach, redirect gaps.

- Phase 1: Tooling (One‑Click Migration)
  - Migrator CLI: python -m tools.spec_migrate.migrate
    - Flags: --source, --mode copy, --volume-map <yaml>, --dry-run, --backup-dir, --preserve-timestamps, --transaction-log, --generate-redirect-map, --validate-history, --prune-legacy-on-success, --confirm.
  - Services/utilities:
    - ulid_registry.py (central registry + collision detection).
    - MFID cache (.mfid-cache/), incremental + parallel hashing.
    - Validation suite: validate_migration.py (parity, cross‑refs, tags, render).
    - Optional sync: sync.py (keep legacy updated during parallel period).
  - Tests:
    - Unit: mapping, ULID registry, sidecar gen, suite‑index bootstrap, MFID cache.
    - Dry‑run on a 5–10 file subset.

- Phase 2: Dry‑Run Plan
  - Generate plan (no changes):
    - Proposed file moves (old → new) to .migration/mapping.yaml.
    - Sidecar generation preview and initial docs/.index/suite-index.yaml bootstrap.
    - Redirects preview: .migration/redirects.map plus _redirects, nginx.map, redirect_from.yml.
    - Tree diff + parity report in .migration/validation-report.md.
  - Gate to proceed:
    - Zero collisions, zero broken links, guard-simulate clean, parity within threshold.

- Phase 3: Apply (Copy Mode) + Parallel Validation
  - Execute migration in copy mode:
    - Create docs-v2/.index/, docs-v2/source/<volumes>/, ids/, .ledger/, registry/.
    - Copy files per mapping; unknowns → docs-v2/source/99-imported/.
    - Generate sidecars; bootstrap and finalize docs-v2/.index/suite-index.yaml.
    - Assign ULIDs for sections and paragraphs; backfill into sidecars and index.
  - Dual CI:
    - Validate both legacy and v2 structures.
    - Pre‑commit hook to regen sidecars on staged .md.
  - Automated gates:
    - spec_guard passes, MFID verify clean, redirects resolvable, rendered parity OK.

- Phase 4: Automated Prune (Remove Duplicates)
  - Safety checks before prune:
    - For each mapping pair (old, new): content MFID match, paragraph counts match, cross‑refs/links pass, redirects present.
  - Prune plan:
    - Generate .migration/prune-plan.yaml listing deletions, then run with --confirm.
    - Delete legacy files and folders safely (use git rm), write to transaction.log.
  - Post‑prune validation:
    - Re-run guard, MFID verify, link check, render parity.

- Phase 5: Cutover & Redirects
  - Make docs-v2 canonical; freeze legacy paths.
  - Redirects:
    - Emit: Netlify _redirects, Nginx map, GitHub Pages redirect_from YAML, and a JSON redirects bundle for other hosts.
  - Contributor docs:
    - “Where did my file go?” table (from mapping), addressing scheme tutorial, PR workflow with sidecars.
  - Branch protection:
    - Require guard + MFID checks; block direct edits to suite-index.yaml.

- Phase 6: Cleanup
  - Remove dual CI; keep redirects live.
  - Periodic suite validation; tag suite versions on release.

- Copy‑Verify‑Prune Automation
  - CLI flow:
    - Dry‑run: spec_migrate --source docs --mode copy --volume-map mapping.yml --dry-run
    - Apply: spec_migrate --source docs --mode copy --backup-dir .backup --transaction-log .migration/transaction.log --generate-redirect-map --validate-history --confirm
    - Prune: spec_migrate --prune-legacy-on-success --confirm
  - Verification checks (must all pass before prune):
    - File MFIDs equal, sidecar paragraph counts equal, ULID sets equal, resolver can map both spec:// and specid://, external links valid, rendered parity within tolerance.

- Volume Mapping Defaults
  - See Epic MAP section above (unchanged from original).

- Anchors & IDs
  - See Epic IDS section above (unchanged from original).

- CI/CD Updates
  - See Epic CI section above (unchanged from original).

---

## 12) How to Use This Plan with Aider

- Create GitHub milestones M0–M6 from Section 2.
- Create labels from Section 5.
- For each Epic, create issues from “Issue Seeds” with:
  - Title: [AREA] Concise action with file path(s)
  - Body: Use Acceptance + Suggested Aider Prompt
  - Labels: area/*, type/*, size/s|m|l, priority/*
  - Milestone: Mx as listed
- Run Aider per issue with the Suggested Aider Prompt.
