# Deep Research Report vs. Repo Reality — Gap Analysis

## Context

The deep research report ("One Process Pipeline Integration Report") proposes consolidating Governance, RUNTIME, MINI_PIPE, and LangGraph into a single Stage0–Stage7 pipeline with `evidence/<run_id>/` as the canonical run root. This document maps each recommendation against what actually exists in the repo today.

---

## 1. Canonical Run Root & Evidence Store

| Report Recommends | Repo Reality | Gap |
|---|---|---|
| Single `evidence/<run_id>/` run root for all components | **6+ competing run roots**: `.planning_loop_state\\runs\\{id}\\`, `.acms_runs\\{id}\\`, `01260207201000001221_Multi CLI\\.state\\evidence\\plan_loop_runs\\RUN_{id}\\`, `.state\\01260207201000001027_evidence\\`, `01260207201000001148_evidence\\`, `EVIDENCE_BUNDLE\\` | **LARGE** - split-brain is real and active |
| Unified run manifest (`run_manifest.json`) | Manifests exist in multiple formats: planning_run manifests, ACMS execution manifests, EVIDENCE_BUNDLE/run_manifest.json — all different schemas | **MEDIUM** — manifests exist but are not unified |
| Stage-scoped artifact folders (`stages/stage0_ssot/`, etc.) | No stage-scoped layout anywhere; artifacts are scattered by component origin | **LARGE** — no stage directory convention exists |
| `compat/acms/` and `compat/planning_runs/` mounts | No compatibility mounts exist | **SMALL** — can be added once canonical root is chosen |

**Verdict**: The report correctly identifies split-brain as the #1 structural risk. The repo confirms it - at least 6 distinct run/evidence roots exist with incompatible schemas.

---

## 2. Execution Substrate (RUNTIME vs MINI_PIPE)

| Report Recommends | Repo Reality | Gap |
|---|---|---|
| RUNTIME as single canonical orchestrator | **Multiple orchestrators at different tiers**: repo_autoops `Orchestrator` (file events), `FlowOrchestrator` (service flows with circuit breaker), `ControlPlane` (LangGraph planning), `TransactionCoordinator` (atomic ops) | **MEDIUM** — orchestrators exist but serve different scopes; no unified lifecycle owner |
| MINI_PIPE as optional remediation profile | **MINI_PIPE not observed in tree**; `repo_autoops` appears primary; `.acms_runs\\` contains at least one run; no ACMS controller module found | **LOW** - MINI_PIPE is already de-facto demoted |
| Router/Scheduler/Executor pattern | Router: `Orchestrator` routes file events ✅. Scheduler: `ReconcileScheduler` is a stub (`NotImplementedError("Phase 7")`) ❌. Executor: `FlowOrchestrator` has async execution ✅ | **MEDIUM** — 2 of 3 exist; scheduler is a stub |
| RFC 6902 patch ledger | `PromotionPatch` supports patch operations with CAS precondition ✅. Actual RFC 6902 patches exist in `PATCHES/` folder ✅. **No persistent ledger** tracking which patches were applied when ❌ | **MEDIUM** — patch generation exists, ledger tracking missing |

**Verdict**: The report's recommendation to pick RUNTIME is already partially realized — MINI_PIPE has been superseded by `repo_autoops`. The gap is consolidating the 4 orchestrator tiers into one lifecycle owner.

---

## 3. Governance Gating & Enforcement

| Report Recommends | Repo Reality | Gap |
|---|---|---|
| `enforce_pre_execution_gates()` / `enforce_post_execution_gates()` bridge | **No enforcement bridge exists**. `validation_gates.py` has `SchemaValidationGate`, `PolicyComplianceGate`, and `DependencyValidationGate` implemented | **LARGE** — no mechanism to halt pipeline on gate failure |
| Gate runner CLI (`--policy`, `--evidence-dir`, `--layer`, `--gate`) | No gate runner CLI found | **LARGE** — completely missing |
| Gate evidence schema (run_id, layer_id, gate_id, exit_code, etc.) | Gate catalog exists in `.idpkg/contracts/GATE_CATALOG.json` with 14 gates defined (DIR-G1–G5, FILE-G1–G5, X-G1–G4), but **no evidence emission** | **MEDIUM** — gates defined, evidence schema not implemented |
| Evidence path policy | `evidence_path_policy.json` exists under `01260207201000001249_policies\` (not `policies\`) ✅ | **LOW** — policy defined, not yet consumed |
| Structured event schema (`events.jsonl`) | Multiple incompatible JSONL formats: `metrics.jsonl`, `access_audit.jsonl`, `approvals.jsonl`, `tool_call_manifest.jsonl` — **no unified event schema** | **LARGE** — telemetry exists but is fragmented |
| Event handlers | `EventHandlers` class exists with 4 methods, all `raise NotImplementedError("Phase 6")` | **LARGE** — defined but completely unimplemented |

**Verdict**: Governance is the **widest gap**. Gate definitions and policies are authored, but no enforcement runtime exists. The pipeline currently has no ability to block on gate failure.

---

## 4. Scanner / Facts Extraction (Stages 2–3)

| Report Recommends | Repo Reality | Gap |
|---|---|---|
| Unified repo inventory scanner | `scanner_service.py` (49KB, comprehensive) ✅, `id_format_scanner.py` ✅, `file_inventory_builder.py` ✅ — but **scattered across 3+ locations** | **SMALL** — capability exists, needs consolidation |
| AST-only facts extraction per file | `component_extractor.py`, `extract_semantic_features.py`, `argparse_extractor.py`, `descriptor_extractor.py` — **4 separate extractors** with no unified facts schema | **MEDIUM** — AST extraction exists but not unified into per-file facts.json |
| Canonicalized facts hashing (JCS/RFC 8785) | `hash_utils.py` in plan_refine_cli has deterministic JSON hashing ✅. `canonical_hash.py` in govreg_core ✅. **Not wired to facts extraction** | **SMALL** — hashing utilities exist, need integration |
| `<file_id>.facts.json` artifact per file | No per-file facts artifacts found | **LARGE** — facts extraction doesn't produce the report's artifact format |

**Verdict**: Individual extraction capabilities exist but are scattered. The main gap is the unified per-file `facts.json` artifact with canonical hashing.

---

## 5. Deterministic Capability Mapping (Stage 4)

| Report Recommends | Repo Reality | Gap |
|---|---|---|
| Closed-world `vocab_capabilities.json` | **Does not exist** — no SSOT capability tag enumeration | **LARGE** — completely missing |
| Closed-world `vocab_components.json` | **Does not exist** — no SSOT component ID enumeration | **LARGE** — completely missing |
| Deterministic mapping rules engine | `capability_discoverer.py` has precedence rules (code > schemas > template_specs > docs) ✅. `capability_mapper.py` and `capability_detector.py` exist ✅ | **MEDIUM** — mapping logic exists but not constrained to closed-world vocabs |
| Mapping output: `capability_tags`, `component_ids`, `facts_hash` | Capability discovery produces catalogs, but not in the report's per-file `mapping.json` format | **MEDIUM** — output format differs |

**Verdict**: Mapping logic exists, but the report's key insight — **closed-world vocabularies as SSOT inputs** — is entirely missing. Without them, tag drift and CAP-UNMAPPED are inevitable.

---

## 6. Registry Promotion (Stage 5)

| Report Recommends | Repo Reality | Gap |
|---|---|---|
| RFC 6902 patch generation | `PromotionPatch` with typed operations (ADD, UPDATE, DELETE, UPSERT) ✅. Actual RFC 6902 patches in `PATCHES/` and `SSOT_REFACTOR/` ✅ | **LOW** — exists and works |
| CAS precondition (registry_hash) | `PromotionPatch` includes `registry_hash` for CAS ✅ | **NONE** — implemented |
| Dry-run + explicit apply separation | `write_policy_validator.py` exists ✅. **No dry-run/apply separation found** | **MEDIUM** — validation exists, but no dry-run mode |
| Atomic `os.replace()` writes | `AtomicTransaction` (14KB) with prepare→execute→rollback/commit protocol ✅. `TransactionCoordinator` with ACID semantics ✅ | **LOW** — atomic infrastructure exists |
| Before/after registry snapshots in run bundle | Backup files exist (`BACKUP_FILES/`, `.pre_apply_backup_*`) but **not scoped to run bundles** | **MEDIUM** — snapshots exist but not under `evidence/<run_id>/` |
| Patch touches forbidden field → block | No field-level write allowlist/denylist enforcement found | **MEDIUM** — WRITE_POLICY_IDPKG.yaml exists as spec but not enforced at patch level |

**Verdict**: Registry promotion has the strongest existing infrastructure. The gaps are operational: dry-run mode, field-level enforcement, and scoping artifacts to run bundles.

---

## 7. SSOT Registry (Stage 0 input)

| Report Recommends | Repo Reality | Gap |
|---|---|---|
| Registry as queryable canonical store | `REGISTRY_file.json`: schema v4.0, 2,074 entries, 184 columns ✅ | **NONE** — exists |
| Registry schema validation | `governance_registry_schema.v3.json` (Draft-07) ✅. Column dictionary (184 headers) ✅ | **NONE** — comprehensive |
| Dir_ID integrity | 200+ `.dir_id` files, auto-repair, zone classifier, pre-commit hooks, reconciliation ✅ | **NONE** — fully implemented |
| Registry baseline snapshot per run | Backups exist but **not per-run snapshots** | **SMALL** — mechanism exists, needs run-scoping |

**Verdict**: The SSOT registry is the most mature subsystem. The report's Stage 0 requirements are largely satisfied.

---

## 8. LangGraph Planning Loop

| Report Recommends | Repo Reality | Gap |
|---|---|---|
| Bounded Plan–Execute–Replan loop | `ControlPlane` with GraphState, staleness/critic/termination nodes ✅. CLI with init/context/skeleton/lint/loop/finalize commands ✅ | **MEDIUM** — framework present but LangGraph not actually imported; skeleton only |
| Planning runs under `evidence/<run_id>/compat/planning_runs/` | Planning runs live under `.planning_loop_state\runs\` and `01260207201000001221_Multi CLI\.state\evidence\plan_loop_runs\` — separate from evidence root | **MEDIUM** — needs relocation |
| Structured state with hashes | `GraphState` tracks plan_hash, context_bundle_hash, policy_hash ✅. `planning_run_manifest.schema.json` requires SHA256 hashes ✅ | **LOW** — hash discipline exists |

**Verdict**: The planning loop skeleton is solid but doesn't yet use LangGraph as a library (no imports found). Integration to the unified evidence root is needed.

---

## Summary Heatmap

| Report Area | Exists | Partial | Missing | Overall Gap |
|---|---|---|---|---|
| **Canonical run root** | | | ■ | 🔴 LARGE |
| **Execution substrate** | ■ | ■ | | 🟡 MEDIUM |
| **Governance enforcement** | | ■ | ■ | 🔴 LARGE |
| **Scanner/facts** | ■ | ■ | | 🟡 MEDIUM |
| **Capability vocab** | | | ■ | 🔴 LARGE |
| **Deterministic mapping** | | ■ | | 🟡 MEDIUM |
| **Registry promotion** | ■ | ■ | | 🟢 LOW |
| **SSOT registry** | ■ | | | 🟢 NONE |
| **Dir_ID system** | ■ | | | 🟢 NONE |
| **Schema validation** | ■ | | | 🟢 NONE |
| **Event/telemetry** | | ■ | ■ | 🔴 LARGE |
| **LangGraph loop** | | ■ | | 🟡 MEDIUM |

---

## Top 5 Gaps (Prioritized)

1. **No unified run root** — 6+ competing evidence/run directories with incompatible schemas. This is the foundation everything else depends on.

2. **No governance enforcement bridge** — 14 gates defined, policies authored, but zero runtime enforcement. The pipeline cannot block on failure.

3. **No closed-world vocabulary artifacts** — Capability tags and component IDs are not constrained, making deterministic mapping impossible.

4. **No unified event/telemetry schema** — 6+ JSONL formats exist with no shared contract. Cannot correlate events across subsystems.

5. **No per-file facts artifact** — AST extractors exist but don't produce the canonical `facts.json` + hash that the mapping and promotion stages need.

---

## What the Report Gets Right

- **Split-brain diagnosis is accurate** — the repo genuinely has 6+ run roots
- **RUNTIME over MINI_PIPE** — MINI_PIPE is already de-facto replaced by repo_autoops
- **Registry promotion is closest to done** — PromotionPatch + AtomicTransaction + CAS is real
- **Dir_ID and registry are mature** — the SSOT foundation is solid
- **Governance gates are spec'd but not enforced** — confirmed

## Where the Report Has Stale/Incorrect Assumptions

- **MINI_PIPE still active** — the report treats MINI_PIPE as a live system to demote; it's already been superseded
- **RUNTIME as named entity** — there is no single "RUNTIME" module; the functionality is split across `repo_autoops`, `FlowOrchestrator`, `TransactionCoordinator`, and `registry_writer`
- **LangGraph integration** — the report assumes LangGraph is being used; the code has the structure but doesn't import LangGraph
- **`evidence/<run_id>/` already exists for gates** — the policy exists under `01260207201000001249_policies\` (tests default to `policies\`), but no gate runner populates the folder
