# py_* Registry Column — Pipeline Mapping (Unified Corrected)

**Generated:** 2026-02-27
**Sources reconciled:** Claude Code session + OpenAI Codex session
**Pipeline files:** `consolidated_runner.py`, `analyzer_interface.py`, `inventory_schema_v2.json`
**Registry files:** `REGISTRY_COLUMN_HEADERS.md`, `COLUMN_DICTIONARY_184_COLUMNS.csv`, `UNIFIED_SSOT_REGISTRY_DERIVATIONS.yaml`

---

## Status Definitions

| Status | Meaning |
|--------|---------|
| **DIRECT** | Pipeline produces the value; field name matches or is a trivial rename with identical semantics |
| **RENAME** | Pipeline produces equivalent data but field name, structure, or type differs (e.g., string vs array, nested vs flat) |
| **PARTIAL** | Raw data exists in pipeline output but requires non-trivial transformation, filtering, or derivation |
| **NO** | Pipeline does not produce this data; requires new analyzer, external tool, or batch operation |

---

## Summary

| Status | Count | Columns |
|--------|-------|---------|
| DIRECT | 1 | `py_imports_hash` |
| RENAME | 3 | `py_complexity_cyclomatic`, `py_deliverable_kinds`, `py_deliverable_signature_hash` |
| PARTIAL | 10 | `py_ast_dump_hash`, `py_ast_parse_ok`, `py_component_count`, `py_defs_classes_count`, `py_defs_functions_count`, `py_deliverable_interfaces`, `py_imports_local`, `py_imports_stdlib`, `py_imports_third_party`, `py_io_surface_flags`, `py_security_risk_flags` |
| NO | 23 | All remaining (see detailed table) |
| **Total** | **37** | |

---

## Critical Integration Gap

**`file_id` mismatch:** The pipeline sets `file_id = content_sha256` (64-char hex). The registry expects an allocated 20-digit numeric ID from `ALLOCATE_FILE_ID()`. This is not a py_* column issue but **blocks all promotion** because records cannot be matched to registry entries. A mapping/lookup layer is required before any py_* values can be promoted.

---

## Detailed Mapping Table

| py_* Column | Status | Pipeline Source | Gap Description | Action Needed |
|---|---|---|---|---|
| py_analysis_run_id | NO | — | Run-level metadata not captured | Add to `consolidated_runner.py` or build `registry_integration_pipeline.py` |
| py_analysis_success | NO | — | Per-file success flag absent | Add aggregate success flag after all analyzers run |
| py_analyzed_at_utc | NO | — | Per-file analysis timestamp absent | Capture UTC timestamp per file in runner |
| py_ast_dump_hash | PARTIAL | `FileContext.ast_tree` exists | AST is parsed but dump hash not computed | Add `hashlib.sha256(ast.dump(tree))` to `FileContext` or a new analyzer |
| py_ast_parse_ok | PARTIAL | `FileContext.ast_tree is not None` | Boolean derivable but not exposed as a field | Add boolean field to record: `ast_tree is not None` |
| py_canonical_candidate_score | NO | — | Requires batch ranking across overlap groups | Build `canonical_ranker.py` (LAST_MILE Phase 2) |
| py_canonical_text_hash | NO | — | Requires text normalization before hashing | Wire `text_normalizer.py` as an analyzer adapter |
| py_capability_facts_hash | NO | — | Registry expects hash of *capability-specific* facts from mapping pipeline (Steps 3-4), not the general `facts_sha256` from inventory | Build capability mapping pipeline; compute hash over capability tags + purpose only |
| py_capability_tags | NO | — | Capability tagging is a mapping pipeline output (Step 3) | Build capability discovery + purpose registry builder |
| py_complexity_cyclomatic | RENAME | `facts.complexity.average` | Pipeline produces `average`, `max`, `total`; registry expects single `cyclomatic` value | Decide semantic mapping (average vs max) and rename; currently at `ComplexityAnalyzerAdapter` line 369 |
| py_component_artifact_path | NO | — | Evidence writer not implemented | Build evidence writer; capture artifact output path |
| py_component_count | PARTIAL | `facts.deliverable.interface_signature` | Classes + functions lists exist but not counted | Add `len(classes) + len(functions)` derivation |
| py_component_ids | NO | — | Requires `component_extractor` + `generate_component_signature` | Wire `component_extractor.py` as adapter; generate stable IDs |
| py_coverage_percent | NO | — | Requires pytest + coverage execution | Phase B external tool (LAST_MILE) |
| py_defs_classes_count | PARTIAL | `facts.deliverable.interface_signature.classes` | List exists but not counted as integer | Add `len(classes)` derivation |
| py_defs_functions_count | PARTIAL | `facts.deliverable.interface_signature.functions` | List exists but not counted as integer | Add `len(functions)` derivation |
| py_defs_public_api_hash | NO | — | Public API surface not separately hashed | Extend deliverable analyzer or add dedicated extractor |
| py_deliverable_inputs | NO | — | Deliverable analyzer does not extract input dependencies | Extend `DeliverableAnalyzerAdapter` to capture input patterns |
| py_deliverable_interfaces | PARTIAL | `facts.deliverable.interface_signature` | Data exists as nested object; registry expects flat array | Flatten `{classes: [...], functions: [...]}` into array of interface descriptors |
| py_deliverable_kinds | RENAME | `facts.deliverable.kind` | Pipeline produces single string; registry expects array | Wrap: `[facts.deliverable.kind]` |
| py_deliverable_outputs | NO | — | Deliverable analyzer does not extract output patterns | Extend `DeliverableAnalyzerAdapter` to capture output patterns |
| py_deliverable_signature_hash | RENAME | `facts.deliverable.interface_hash` | Semantically equivalent; name differs | Rename `interface_hash` → `py_deliverable_signature_hash` |
| py_imports_hash | DIRECT | `facts.imports.hash` | Direct match from `DependencyAnalyzerAdapter` | No action needed |
| py_imports_local | PARTIAL | `facts.imports.entries` + `relative_count` | Count exists; registry expects list of module names | Filter `entries` where `type == "relative"`, extract module names |
| py_imports_stdlib | PARTIAL | `facts.imports.entries` + `stdlib_count` | Count exists; registry expects list of module names | Filter `entries` where classification is stdlib, extract module names |
| py_imports_third_party | PARTIAL | `facts.imports.entries` + `external_count` | Count exists; registry expects list of module names | Filter `entries` where classification is external, extract module names |
| py_io_surface_flags | PARTIAL | `facts.io_surface.*` | Raw lists of file_ops, network_calls, security_calls exist | Define flag taxonomy and map: e.g., `HAS_NETWORK`, `HAS_FILE_WRITE`, `HAS_SECURITY_CALL` |
| py_overlap_best_match_file_id | NO | — | Requires pairwise similarity computation | Build `similarity_clusterer.py` (LAST_MILE Phase 2) |
| py_overlap_group_id | NO | — | Requires batch clustering by signature hash | Build `similarity_clusterer.py` (LAST_MILE Phase 2) |
| py_overlap_similarity_max | NO | — | Requires similarity scoring | Build `similarity_clusterer.py` (LAST_MILE Phase 2) |
| py_pytest_exit_code | NO | — | Requires pytest execution | Phase B external tool (LAST_MILE) |
| py_quality_score | NO | — | Composite score from multiple inputs | Build `quality_scorer.py` (LAST_MILE Phase 2) |
| py_security_risk_flags | PARTIAL | `facts.io_surface.security_calls` | Raw security call list exists | Define risk flag taxonomy and map from security_calls + network_calls |
| py_static_issues_count | NO | — | Requires linter execution (ruff/pylint) | Phase B external tool (LAST_MILE) |
| py_tests_executed | NO | — | Requires pytest execution | Phase B external tool (LAST_MILE) |
| py_tool_versions | NO | — | Toolchain versions not captured | Add version collection to runner (Python, pytest, ruff, etc.) |
| py_toolchain_id | NO | — | Toolchain identifier not assigned | Add constant or config-driven toolchain ID |

---

## Base Registry Columns (non-py_*) Produced by Pipeline

These are base columns the pipeline incidentally produces data for, but not in registry format:

| Registry Column | Pipeline Field | Gap |
|---|---|---|
| sha256 | `content_sha256` | Rename only |
| size_bytes | `size_bytes` | Direct match |
| mtime_utc | `mtime_utc` | Direct match |
| relative_path | `path_rel` | Rename only (already POSIX) |
| absolute_path | `path_abs` | Needs slash normalization for registry |
| extension | `ext` | Pipeline includes leading dot; registry expects without dot |
| file_id | `content_sha256` | **WRONG** — registry uses 20-digit allocated IDs |
| entrypoint_flag | `classification == "python_entrypoint"` | Derivable with boolean transform |
| filename | — | Not emitted; derivable from `path_rel` |
| directory_path | — | Not emitted; derivable from `path_rel` |

---

## Discrepancy Resolution Log

| Item | Claude Code (original) | Codex (original) | Corrected | Rationale |
|---|---|---|---|---|
| `py_complexity_cyclomatic` | PARTIAL (summary) / YES (detail) | YES | **RENAME** | Data exists at `facts.complexity.average` but needs field rename + semantic decision (avg vs max) |
| `py_capability_facts_hash` | YES (mapped from `facts_sha256`) | NO | **NO** | `facts_sha256` hashes ALL analyzer facts; registry column is for capability-specific facts only |
| `py_security_risk_flags` | PARTIAL | NO | **PARTIAL** | Raw `security_calls` list exists; needs flag mapping rules |
| `py_io_surface_flags` | PARTIAL | NO | **PARTIAL** | Raw io_surface lists exist; needs flag derivation |
| YES total | 4 | 5 | **1 DIRECT + 3 RENAME = 4 total** | Splitting YES into DIRECT/RENAME resolves ambiguity |
| NO total | 22 | 21 | **23** | `py_capability_facts_hash` moved from YES to NO |
