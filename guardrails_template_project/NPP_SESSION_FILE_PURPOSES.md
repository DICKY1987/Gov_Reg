# NPP Session File Purposes

This document describes the purpose of every file created or modified during the `newPhasePlanProcess` v3.2 baseline, Phase A, Phase B, and A.3 reindexing work completed on branch `npp-v3_2-baseline`.

## Core governance documents

| File | Purpose |
| --- | --- |
| `NEWPHASEPLANPROCESS_TECHNICAL_SPECIFICATION_V3_2.json` | The authoritative technical specification for the framework. It defines architecture, gate registry, step-contract schema, governance sections, and the cross-document rules the template and instruction doc must follow. |
| `NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_2.json` | The executable plan template used to author concrete plans. It carries the required top-level sections, example step contracts, validation-gate examples, and pattern/executor governance examples. |
| `NEWPHASEPLANPROCESS_INSTRUCTION_DOCUMENT_V3_2.json` | The AI-facing instruction document. It explains how an agent should fill the template and now enforces pattern-first, configuration-driven planning rules in narrative form. |

## Migration authority and runbook inputs

| File | Purpose |
| --- | --- |
| `guardrails_template_project/greedy-stirring-tower.md` | The main execution runbook for upgrading the v3.2 documents. It defines the phase order, prerequisites, checks, and expected outputs. |
| `guardrails_template_project/GREEDY_STIRRING_TOWER_EXECUTION_READINESS.md` | A readiness review of the runbook. It documents what originally blocked strict execution, why those issues mattered, and what was fixed. |
| `guardrails_template_project/FINAL_EDIT_PLAN_V3_2_TO_V3_3.md` | The detailed operation list for the governance migration. It is the raw step-by-step source plan for Phase B edits. |
| `guardrails_template_project/MERGED_CORRECTED_FINAL_EDIT_PLAN.md` | The override/correction layer applied to the raw migration plan. It narrows scope and removes conflicting or speculative edits. |
| `guardrails_template_project/cli_blocker_fix_guide.md` | The blocker-remediation guide for Phase A.1. It defines how duplicate gates, enhancement IDs, execution phase classification, and missing component IDs are fixed and verified. |
| `guardrails_template_project/final_indexing_implementation_plan.json` | The Phase A.2/A.3 indexing plan. It defines the inventory, semantic-index build, resolver behavior, and validation gates for the indexing system. |
| `guardrails_template_project/phase_b_override_map.md` | The explicit override authority for Phase B. It decides version policy, registry path, scope restrictions, edit order, and which plan instructions win when sources conflict. |
| `guardrails_template_project/reserved_id_namespaces.json` | The namespace reservation file for post-governance IDs. It declares the required `GATE-CFG-*`, `PAT-*`, `EXEC-*`, and extended `COMP-*` families. |
| `guardrails_template_project/v3_3_patch_plan_machine_style.json` | A deferred machine-patch plan captured for future use. It was tracked as migration context but intentionally not applied in v3.3 scope. |
| `guardrails_template_project/v3_3_patch_plan_machine_layer2.json` | Another deferred machine-patch plan, specifically for out-of-scope Layer 2 work. It was retained as reference but not applied in this migration. |

## Validator and indexing tooling

| File | Purpose |
| --- | --- |
| `newPhasePlanProcess/01260207201000001225_scripts/P_01260207233100000242_NEWPHASEPLANPROCESS_plan_cli.py` | Existing plan CLI script updated to resolve the repo’s current schema layout instead of a stale broken schema path. |
| `index_generator.py` | Generates `inventory.json`, semantic index artifacts, validation reports, namespace checks, and cross-file integrity checks for the three governance documents. |
| `resolver.py` | Resolves semantic IDs such as `GATE-003`, `PAT-EXAMPLE-PLAN-DOC`, or `PH-00/STEP-001` to RFC-6901 JSON Pointers using generated index files. |
| `inventory.json` | The generated inventory of arrays in the three source documents. It records which arrays are structural and which are indexed by semantic identity. |
| `indexes/NEWPHASEPLANPROCESS_TECHNICAL_SPECIFICATION_V3_2.index.json` | Generated semantic index for the technical specification, including component and gate identity maps. |
| `indexes/NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_2.index.json` | Generated semantic index for the template, including gate, enhancement, step, pattern, and executor maps. |
| `indexes/NEWPHASEPLANPROCESS_INSTRUCTION_DOCUMENT_V3_2.index.json` | Generated semantic index artifact for the instruction document. It mainly preserves source hash and empty map structure because the document is markdown-in-JSON, not ID-addressed content. |

## Blocker-remediation evidence

| File | Purpose |
| --- | --- |
| `evidence/blocker_1_gate_registry_fix/pre.json` | Captures the pre-fix state for the duplicate-gate remediation. |
| `evidence/blocker_1_gate_registry_fix/post.json` | Captures the post-fix state after the duplicate `GATE-008` issue was removed. |
| `evidence/blocker_1_gate_registry_fix/validation.json` | Records the validation result proving the gate-registry fix passed. |
| `evidence/blocker_2_enhancement_id_migration/pre.json` | Captures the original numeric enhancement IDs before migration. |
| `evidence/blocker_2_enhancement_id_migration/post.json` | Records the migrated `ENH-001..ENH-010` enhancement IDs. |
| `evidence/blocker_2_enhancement_id_migration/validation.json` | Records the validation result for the enhancement-ID migration. |
| `evidence/blocker_3_execution_phases_classification/pre.json` | Captures the initial state of the `execution_phases` array before inventory-only classification. |
| `evidence/blocker_3_execution_phases_classification/post.json` | Records the accepted post-remediation state showing source JSON left unchanged while classification moved to the inventory. |
| `evidence/blocker_3_execution_phases_classification/validation.json` | Records the validation result for the `execution_phases` structural-classification decision. |
| `evidence/blocker_4_component_id_backfill/pre.json` | Captures the pre-fix architecture state before component IDs were added. |
| `evidence/blocker_4_component_id_backfill/post.json` | Records the post-fix architecture state after all system-layer components gained `component_id` values. |
| `evidence/blocker_4_component_id_backfill/validation.json` | Records the validation result proving the component-ID backfill passed. |
| `evidence/final_blocker_resolution_report.json` | Roll-up report for Phase A.1 showing all four blockers resolved successfully. |

## Indexing and readiness evidence

| File | Purpose |
| --- | --- |
| `evidence/PH-03/inventory_validation.json` | Generated validation artifact showing the array inventory and classification state after indexing. |
| `evidence/PH-05/index_build_report.json` | Generated report confirming index artifacts were built successfully. |
| `evidence/PH-06/resolver_report.json` | Generated resolver report summarizing semantic round-trip coverage and, later, namespace/cross-file integrity checks. |
| `evidence/PH-08/validation_gate_report.json` | Generated validation-gate report for the indexing system. It records `IDX-GATE-01..05`, namespace validation, and cross-file integrity status. |
| `evidence/PH-09/final_readiness_report.json` | Final post-indexing readiness report stating whether the document set is semantically indexed and cross-file consistent. |

## What changed in role terms

- The three root `V3_2` JSONs became the tracked authoritative working set.
- The runbook and override documents became explicit execution authority instead of loose planning notes.
- The evidence bundle now proves both blocker remediation and semantic-index readiness.
- The indexing toolchain now understands post-governance IDs such as `PAT-*`, `EXEC-*`, `GATE-CFG-*`, and `GATE-FILE-MUTATIONS`.
