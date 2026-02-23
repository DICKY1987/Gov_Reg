# ID File Classification

This document classifies files under the ID folder into current system, supporting, legacy, and reference sets. It is generated from ID_FILE_CLASSIFICATION.json and reflects the current IDPKG runtime and governance tooling.

Generated from: ID_FILE_CLASSIFICATION.json

## Current ID System

Total: 24 files

- ID\.dir_id — ID folder directory identity anchor (category: anchor)
- ID\01260207201000000122_DIR_ID_SYSTEM_DOCUMENTATION.md — DIR_ID system reference documentation (category: contract_doc)
- ID\01260207201000000352_ID_IDENTITY_CONTRACT.md — Canonical ID vocabulary and enforcement rules (v2.1.4) (category: contract_doc)
- ID\01260207201000000877_DIR_ID_ANCHOR.schema.json — .dir_id anchor schema (category: schema)
- ID\IDPKG_CONFIG.schema.json — IDPKG config schema (project-level) (category: schema)
- ID\P_01260207233100000068_zone_classifier.py — Zone classifier for directory governance system. (category: tool)
- ID\P_01260207233100000069_dir_id_handler.py — .dir_id file handler for directory identity anchoring. (category: handler)
- ID\P_01260207233100000070_dir_identity_resolver.py — Directory identity resolution pipeline (S10D-S12D). (category: resolver)
- ID\P_01999000042260124031_unified_id_allocator.py — Unified ID allocator consolidating multiple allocation strategies. (category: allocator)
- ID\P_01999000042260124521_id_format_scanner.py — ID Format Scanner - Identify files with missing or incorrect file ID format. (category: tool)
- ID\P_01999000042260125000_gate_id_canonicality.py — Pre-commit Gate: ID Canonicality Enforcement (category: governance_gate)
- ID\P_01999000042260125002_canonical_id_patterns.py — Canonical ID Pattern Definitions (category: tool)
- ID\P_01999000042260125006_id_allocator_facade.py — ID Allocator Facade (category: allocator)
- ID\P_01999000042260125100_generate_dir_ids_gov_reg.py — Generate .dir_id files for governed directories using IDPKG config. (category: tool)
- ID\P_01999000042260125101_validate_dir_ids.py — Validate .dir_id files for governed directories using IDPKG config. (category: tool)
- ID\P_01999000042260125103_rename_dirs_with_id.py — Rename directories to include dir_id prefix. (category: tool)
- ID\P_01999000042260125104_dir_id_auto_repair.py — Auto-repair invalid .dir_id anchors (GAP-001). (category: tool)
- ID\P_01999000042260125105_dir_id_watcher.py — Continuous enforcement via filesystem watcher (GAP-002). (category: watcher)
- ID\P_01999000042260125106_pre_commit_dir_id_check.py — Pre-commit hook for .dir_id validation (GAP-002). (category: governance_gate)
- ID\P_01999000042260125107_pre_push_governance_check.py — Pre-push hook for governance validation (GAP-002). (category: governance_gate)
- ID\P_01999000042260125111_orphan_purger.py — Orphan and dead-entry cleanup (GAP-006). (category: tool)
- ID\P_01999000042260125113_healthcheck.py — Nightly ID and registry health check (GAP-008). (category: tool)
- ID\P_01999000042260126000__idpkg_runtime.py — IDPKG Runtime - Unified File+Directory ID Package (category: runtime)
- ID\WRITE_POLICY_IDPKG.yaml — IDPKG registry write policy (category: policy)

## Supporting (Tests/Reports/Installers)

Total: 12 files

- ID\01260207201000000371_PRODUCTION_VALIDATION_RESULTS.txt — Production Deployment Complete - Validation Results (category: report)
- ID\01260207201000000376_VALIDATION_RESULTS.txt —  Task 3.3 Complete: Validate Test Results (category: report)
- ID\CONSOLIDATION_COMPLETE.md — Registry Consolidation - Completion Report (category: report)
- ID\CONSOLIDATION_PLAN.md — Registry Files Consolidation Plan (category: report)
- ID\ID_AUTOMATION_COMPLETE.md —  ID System Automation - COMPLETE (category: report)
- ID\install_automation.py — Installation script for automation gaps implementation. (category: support_tool)
- ID\P_01260207201000001009_test_directory_identity.py — Tests for directory identity resolver. (category: test)
- ID\P_01260207233100000050_test_identity_resolver.py — Tests for identity_resolver.py - 4-step matching algorithm (category: test)
- ID\P_01999000042260124029_test_id_allocator.py — Unit tests for ID Allocator module. (category: test)
- ID\P_01999000042260124032_reservation_ledger.py — Reservation ledger manager for tracking file ID reservations. (category: supporting_script)
- ID\P_01999000042260124040_test_reservation_system.py — Phase 4 - Comprehensive Test Suite for Reservation System. (category: test)
- ID\README_CONSOLIDATION.md — Registry Scripts Consolidation - Complete (category: report)

## Legacy (Superseded)

Total: 19 files

- ID\01260207201000000174_ID_IDENTITY_CONTRACT.md — ID Identity Contract - Vocabulary & Rules (category: contract_doc; note: Superseded by 01260207201000000352_ID_IDENTITY_CONTRACT.md)
- ID\IDPKG_CONFIG.schema (1).json — Duplicate IDPKG config schema (legacy copy) (category: schema; note: Duplicate of IDPKG_CONFIG.schema.json)
- ID\P_01260207201000000109_add_file_ids.py — Add 20-digit IDs to files in current directory that need them. (category: legacy_script)
- ID\P_01260207201000000130_Enhanced File Scanner v2.py — Enhanced File Scanner v2.0 (category: legacy_script; note: Legacy scanner (pre-IDPKG))
- ID\P_01260207201000000198_add_ids_recursive.py — Add 20-digit IDs to all files recursively that need them. (category: legacy_script)
- ID\P_01260207201000000936_strengthen_id_patterns.py — Strengthen ID patterns for better validation. (category: legacy_script)
- ID\P_01260207201000000989_identity_resolver.py — Wrapper for P_01260207233100000323_identity_resolver.py (category: legacy_script)
- ID\P_01260207233100000033_fix_file_id_pattern.py — Fix file_id pattern in Column Dictionary to match COMPLETE_SSOT.json specification. (category: legacy_script)
- ID\P_01260207233100000064_migrate_remove_doc_id_from_data.py — Data migration: remove doc_id from registry records. (category: legacy_script)
- ID\P_01260207233100000154_id_normalizer.py — ID Normalizer (category: legacy_script)
- ID\P_01260207233100000287_batch_assign_file_ids.py — Batch File ID Assignment - Add file IDs to existing files and register them (category: legacy_script)
- ID\P_01260207233100000288_allocate_ids.py — Phase 0.7: Allocate 20-digit IDs for migration files (category: legacy_script)
- ID\P_01260207233100000323_identity_resolver.py — Identity Resolver - 4-Step Matching Algorithm (category: legacy_script)
- ID\P_01260207233100000333_id_allocator.py — Canonical ID Allocator for Registry records. (category: legacy_script; note: Superseded by P_01999000042260125006_id_allocator_facade.py)
- ID\P_01260207233100000342_01999000042260125024_identity_pipeline.py — Python module (category: legacy_script)
- ID\P_01999000042260124027_id_allocator.py — ID Allocation Module - Proactive ID Assignment. (category: legacy_script; note: Backend allocator; use facade instead)
- ID\P_01999000042260125067_zone_classifier.py — Zone Classifier Module - Directory ID Package v1.0 (category: legacy_script; note: Superseded by P_01260207233100000068_zone_classifier.py)
- ID\P_01999000042260125068_dir_id_handler.py — Directory ID Handler - Directory ID Package v1.0 (category: legacy_script; note: Superseded by P_01260207233100000069_dir_id_handler.py)
- ID\P_01999000042260126012_validate_no_doc_id.py — Validator: Ensure no doc_id in registry records (category: legacy_script; note: Renumbered from P_01999000042260126012_validate_no_doc_id.py to resolve duplicate file_id)

## Reference (Docs/Artifacts)

Total: 36 files

- ID\01260202173939000110_FLOW_DIAGRAM_EVIDENCE.md — Flow Diagram Evidence Package (category: reference_doc)
- ID\01260207201000000123_DOC-CONFIG-1208__ChatGPT-Stable ID Types.json — Data/config file: 01260207201000000123_DOC-CONFIG-1208__ChatGPT-Stable ID Types.json (category: data_config)
- ID\01260207201000000139_ID_ALLOCATOR_OVERLAP_ANALYSIS.md — ID Allocator Function Overlap Analysis (category: analysis_doc)
- ID\01260207201000000140_ID_ALLOCATOR_QUICKREF.txt — Document: 01260207201000000140_ID_ALLOCATOR_QUICKREF.txt (category: reference_doc)
- ID\01260207201000000144_ID_CANONICALITY_CORRECTIONS_V2.1.1.md — ID Canonicality - Final Corrections (Blockers Fixed) (category: reference_doc)
- ID\01260207201000000147_ID_CANONICALITY_EXECUTION_BLOCKERS.md — ID Canonicality - EXECUTION BLOCKERS (v2.1.3  v2.1.3.1) (category: reference_doc)
- ID\01260207201000000166_ID_CANONICALITY_INDEX.md — ID Canonicality - Documentation Index (category: analysis_doc)
- ID\01260207201000000168_ID_CANONICALITY_MUTATION_SET_V2.1.4.md — ID Canonicality System - Mutation Set v2.1.4-READY (category: reference_doc)
- ID\01260207201000000173_ID_CRAZY.txt — "C:\Users\richg\Gov_Reg\scripts\P_01999000042260124027_id_allocator.py" (category: reference_doc)
- ID\01260207201000000175_IDENTITY_CONFIG (1).yaml — Data/config file: 01260207201000000175_IDENTITY_CONFIG (1).yaml (category: data_config)
- ID\01260207201000000346_DIR_ID_CANONICALITY_LAW.json — Data/config file: 01260207201000000346_DIR_ID_CANONICALITY_LAW.json (category: data_config)
- ID\01260207201000000347_DIR_ID_TRANSITION_VECTORS.yaml — Data/config file: 01260207201000000347_DIR_ID_TRANSITION_VECTORS.yaml (category: data_config)
- ID\01260207201000000349_BUNDLE_ID_DEFINITION.md — Bundle ID Definition (category: reference_doc)
- ID\01260207201000000515_Planning-Time File ID Reservation System.txt — TECHNICAL SPECIFICATION (category: reference_doc)
- ID\01260207201000000516_Planning-Time_File_ID_Reservation_System_UPDATED.md — TECHNICAL SPECIFICATION (UPDATED) (category: reference_doc)
- ID\01260207201000000558_MULTI_AGENT_CONSOLIDATION_QUICKREF.md — Multi-Agent Workstream Coordination - Quick Reference (category: report)
- ID\01260207201000000576_DOC_AIDER_CONTRACT.md — DOC_AIDER_CONTRACT - Aider Tool Integration Contract v1 (category: contract_doc)
- ID\01260207201000000609_AI_GUIDANCE (2).md — --- (category: reference_doc)
- ID\01260207201000000613_DOC_AIDER_CONTRACT (2).md — --- (category: contract_doc)
- ID\01260207201000000640_AI_DEV_HYGIENE_GUIDELINES.md — AI Development Hygiene - Quick Reference Guidelines (category: guide)
- ID\01260207201000000647_DOC_AI_DEV_HYGIENE_GUIDELINES.md — --- (category: guide)
- ID\01260207201000000683_AIDER_CONFIG_ANALYSIS.md — --- (category: analysis_doc)
- ID\01260207201000000684_AIDER_FIXES_APPLIED.md — --- (category: reference_doc)
- ID\01260207201000000685_AIDER_GIT_IMP_PROMNT_EXAMPLE.md — IMP_PLAN_3  Aider-Ready Implementation Plan (category: reference_doc)
- ID\01260207201000000686_AIDER_OLLAMA_DEEP.md — Windows (category: reference_doc)
- ID\01260207201000000687_AIDER_QUICK_REFERENCE.md — Aider Quick Reference Card (category: reference_doc)
- ID\01260207201000000688_AIDER_SETUP_README.md — --- (category: reference_doc)
- ID\01260207201000000750_DOC_ID_AUTOMATION_CHAIN_ANALYSIS.md — DOC_ID System - Complete Automation Chain Analysis (category: analysis_doc)
- ID\01260207201000000753_DOC_ID_REGISTRY_CLI_REVIEW.md — doc_id Registry CLI Implementation Review (category: reference_doc)
- ID\01260207201000000775_EXECUTION_PATTERN_DATA_FLOW_VALIDATION.md — --- (category: report)
- ID\ChatGPT-Dir ID System Model.json — Data/config file: ChatGPT-Dir ID System Model.json (category: data_config)
- ID\HOW_TO_IDENTIFY_DEPRECATED_FILES.md — How to Identify Deprecated Files - Complete Guide (category: guide)
- ID\P_01260202173939000081_generate_component_id.py — Component ID Generator for mapp_py Analysis Pipeline (category: reference_script)
- ID\P_01260207233100000302_locate_id_counter.py — Phase 0.2a: Locate ID Counter (category: reference_script)
- ID\P_01999000042260124489_id_scheme.py — GEU ID generation scheme. (category: reference_script)
- ID\Unified File+Directory ID Package v1.0 — Legacy design spec for unified ID package (category: other)

## Notes

- Current ID system definition: IDPKG runtime + canonical allocator/patterns + dir_id governance tooling
- Inventory file for ID-prefixed scripts: ID_SCRIPT_INVENTORY.jsonl
