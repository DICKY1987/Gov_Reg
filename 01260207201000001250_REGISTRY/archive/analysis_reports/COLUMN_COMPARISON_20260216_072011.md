# Column Header Comparison Report
**Generated:** 2026-02-16 07:20:11

## Summary

| Source | Count |
|--------|-------|
| **Registry Headers** | 27 |
| **Dictionary Headers** | 185 |
| **Dictionary Expected** | 184 |
| **Common (Match)** | 27 |
| **In Registry Only** | 0 |
| **In Dictionary Only** | 158 |

---

## Match Status
### ⚠️ MISMATCH DETECTED

Columns differ between registry and dictionary.

---
## Column Details

### ✅ Common Columns (27)

<details><summary>Click to expand list</summary>

- `anchor_file_id`
- `artifact_kind`
- `bundle_id`
- `bundle_key`
- `bundle_role`
- `bundle_version`
- `canonicality`
- `coverage_status`
- `depends_on_file_ids`
- `enforced_by_file_ids`
- `enforces_rule_ids`
- `evidence_outputs`
- `file_id`
- `geu_ids`
- `geu_role`
- `governance_domain`
- `has_tests`
- `is_shared`
- `layer`
- `module_id`
- `owner_geu_id`
- `primary_geu_id`
- `relative_path`
- `repo_root_id`
- `report_outputs`
- `superseded_by`
- `test_file_ids`

</details>

### 🔵 In Dictionary Only (158)

**These columns exist in the dictionary but NOT in the registry:**

#### Non-Python Columns (121)

- `absolute_path`
- `allocated_at`
- `asset_family`
- `asset_id`
- `asset_version`
- `build_report_entity_id`
- `canonical_path`
- `collected_by`
- `column_headers`
- `confidence`
- `content_type`
- `contracts_consumed`
- `contracts_produced`
- `created_by`
- `created_utc`
- `data_transformation`
- `declared_dependencies`
- `deliverables`
- `description`
- `dir_id`
- `directionality`
- `directory_path`
- `edge_flags`
- `edge_id`
- `edge_type`
- `edges`
- `enforced_by`
- `enforces`
- `entity_id`
- `entity_kind`
- `entries`
- `entrypoint_flag`
- `evidence`
- `evidence_locator`
- `evidence_method`
- `evidence_only`
- `evidence_snippet`
- `evidence_type`
- `expires_utc`
- `extension`
- `external_ref`
- `external_system`
- `extract`
- `filename`
- `files`
- `first_seen_utc`
- `function_code_1`
- `function_code_2`
- `function_code_3`
- `generated`
- `generated_at`
- `generated_by_file_id`
- `generator_id`
- `generator_name`
- `generator_version`
- `geu_role_definitions`
- `geu_type_slot_matrix`
- `input_filters`
- `inputs`
- `is_directory`
- `is_generated`
- `last_build_utc`
- `last_seen_utc`
- `metadata`
- `module_id_override`
- `module_id_source`
- `mtime_utc`
- `notes`
- `ns_code`
- `observed_utc`
- `one_line_purpose`
- `optional_roles`
- `output_hash`
- `output_kind`
- `output_path`
- `output_path_pattern`
- `outputs`
- `path_aliases`
- `process_id`
- `process_step_id`
- `process_step_role`
- `record_id`
- `record_kind`
- `rel_type`
- `required_roles`
- `required_suite_key`
- `resolver_hint`
- `role`
- `role_code`
- `rule_based`
- `runner_based`
- `scan_id`
- `schema_based`
- `schema_version`
- `scope`
- `sha256`
- `short_description`
- `size_bytes`
- `sort_keys`
- `sort_rule_id`
- `source_entity_id`
- `source_file_id`
- `source_registry_hash`
- `source_registry_scan_id`
- `status`
- `step_refs`
- `supersedes_entity_id`
- `tags`
- `target_entity_id`
- `target_file_id`
- `target_schema_id`
- `template_ref_entity_id`
- `tool_version`
- `transient_id`
- `transient_type`
- `ttl_seconds`
- `type_code`
- `updated_by`
- `updated_utc`
- `validation_rules`
- `validator_id`

#### Python Analysis Columns (37)

<details><summary>Click to expand py_* columns</summary>

- `py_analysis_run_id`
- `py_analysis_success`
- `py_analyzed_at_utc`
- `py_ast_dump_hash`
- `py_ast_parse_ok`
- `py_canonical_candidate_score`
- `py_canonical_text_hash`
- `py_capability_facts_hash`
- `py_capability_tags`
- `py_complexity_cyclomatic`
- `py_component_artifact_path`
- `py_component_count`
- `py_component_ids`
- `py_coverage_percent`
- `py_defs_classes_count`
- `py_defs_functions_count`
- `py_defs_public_api_hash`
- `py_deliverable_inputs`
- `py_deliverable_interfaces`
- `py_deliverable_kinds`
- `py_deliverable_outputs`
- `py_deliverable_signature_hash`
- `py_imports_hash`
- `py_imports_local`
- `py_imports_stdlib`
- `py_imports_third_party`
- `py_io_surface_flags`
- `py_overlap_best_match_file_id`
- `py_overlap_group_id`
- `py_overlap_similarity_max`
- `py_pytest_exit_code`
- `py_quality_score`
- `py_security_risk_flags`
- `py_static_issues_count`
- `py_tests_executed`
- `py_tool_versions`
- `py_toolchain_id`

</details>


---
## Recommendations

2. 🔵 **Review dictionary-only columns** - 158 columns may be planned/future additions
✅ **All registry columns are documented in dictionary**

---
## Expected vs Actual

- Dictionary Expected Count: **184**
- Dictionary Actual Count: **185**
- Difference: **1**

⚠️ **Warning:** Dictionary count (185) does not match expected (184)

