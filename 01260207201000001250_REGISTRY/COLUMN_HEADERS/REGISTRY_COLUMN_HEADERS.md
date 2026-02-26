# Governance Registry Column Headers
**Schema Version:** 1.0.0  
**Dictionary Version:** 4.2.0  
**Generated:** 02/25/2026 19:22:17 UTC  
**Total Columns:** 185

---

## Complete Column Reference

| Column Name | Derivation Mode | Presence | Type | Scope |
|-------------|-----------------|----------|------|-------|
| absolute_path | EXTRACTED | OPTIONAL | string|null | entity:file |
| allocated_at | SYSTEM | REQUIRED | string | entity:file |
| anchor_file_id | LOOKUP | OPTIONAL | string|null | All |
| artifact_kind | INPUT | OPTIONAL | string|null | All |
| asset_family | INPUT | CONDITIONAL | string|null | entity:asset |
| asset_id | LOOKUP | CONDITIONAL | string|null | entity:asset |
| asset_version | INPUT | OPTIONAL | string|null | entity:asset |
| build_report_entity_id | LOOKUP | OPTIONAL | string|null | generator |
| bundle_id | SYSTEM | OPTIONAL | string|null | entity:file |
| bundle_key | INPUT | OPTIONAL | string|null | entity:file |
| bundle_role | INPUT | CONDITIONAL | string|null | entity:file |
| bundle_version | INPUT | OPTIONAL | string|null | entity:file |
| canonical_path | EXTRACTED | OPTIONAL | string|null | entity:asset,file |
| canonicality | INPUT | OPTIONAL | string|null | All |
| collected_by | INPUT | OPTIONAL | string|null | All |
| column_headers | INPUT | OPTIONAL | array|null | All |
| confidence | INPUT | CONDITIONAL | number|null | edge |
| content_type | INPUT | OPTIONAL | string|null | entity:file |
| contracts_consumed | INPUT | OPTIONAL | array|null | entity:file |
| contracts_produced | INPUT | OPTIONAL | array|null | entity:file |
| coverage_status | INPUT | OPTIONAL | string|null | entity:file |
| created_by | INPUT | REQUIRED | string | core,entity,edge,generator |
| created_utc | INPUT | REQUIRED | string | core,entity,edge,generator |
| data_transformation | DERIVED | OPTIONAL | boolean|string|null | entity:file |
| declared_dependencies | INPUT | OPTIONAL | array|null | generator |
| deliverables | INPUT | OPTIONAL | array|null | All |
| depends_on_file_ids | LOOKUP | OPTIONAL | array|null | All |
| description | INPUT | OPTIONAL | string|null | All |
| dir_id | EXTRACTED | OPTIONAL | string|null | entity:file |
| directionality | INPUT | CONDITIONAL | string|null | edge |
| directory_path | INPUT | OPTIONAL | string|null | entity:file |
| edge_flags | INPUT | OPTIONAL | array|null | edge |
| edge_id | SYSTEM | CONDITIONAL | string|null | edge |
| edge_type | INPUT | OPTIONAL | string|null | All |
| edges | INPUT | OPTIONAL | array|null | All |
| enforced_by | INPUT | OPTIONAL | string|null | All |
| enforced_by_file_ids | LOOKUP | OPTIONAL | array|null | All |
| enforces | INPUT | OPTIONAL | string|null | All |
| enforces_rule_ids | LOOKUP | OPTIONAL | array|null | All |
| entity_id | SYSTEM | CONDITIONAL | string|null | entity |
| entity_kind | INPUT | CONDITIONAL | string|null | entity |
| entries | INPUT | OPTIONAL | array|null | All |
| entrypoint_flag | DERIVED | OPTIONAL | boolean|null | entity:file |
| evidence | INPUT | OPTIONAL | string|null | All |
| evidence_locator | INPUT | OPTIONAL | string|null | edge |
| evidence_method | INPUT | OPTIONAL | string|null | edge |
| evidence_only | DERIVED | OPTIONAL | boolean|null | entity:file |
| evidence_outputs | INPUT | OPTIONAL | array|null | All |
| evidence_snippet | INPUT | OPTIONAL | string|null | edge |
| evidence_type | INPUT | OPTIONAL | string|null | All |
| expires_utc | INPUT | OPTIONAL | string|null | entity:transient |
| extension | EXTRACTED | OPTIONAL | string|null | entity:file |
| external_ref | INPUT | CONDITIONAL | string|null | entity:external |
| external_system | INPUT | OPTIONAL | string|null | entity:external |
| extract | INPUT | OPTIONAL | string|null | All |
| file_id | SYSTEM | REQUIRED | string|null | entity,edge,generator:file,asset |
| filename | INPUT | CONDITIONAL | string|null | entity:file |
| files | INPUT | OPTIONAL | array|null | All |
| first_seen_utc | INPUT | OPTIONAL | string|null | entity |
| function_code_1 | INPUT | OPTIONAL | string|null | entity:file |
| function_code_2 | INPUT | OPTIONAL | string|null | entity:file |
| function_code_3 | INPUT | OPTIONAL | string|null | entity:file |
| generated | DERIVED | OPTIONAL | boolean|null | All |
| generated_at | INPUT | OPTIONAL | string|null | All |
| generated_by_file_id | LOOKUP | OPTIONAL | string|null | All |
| generator_id | LOOKUP | CONDITIONAL | string|null | generator |
| generator_name | INPUT | CONDITIONAL | string|null | generator |
| generator_version | INPUT | CONDITIONAL | string|null | generator |
| geu_ids | LOOKUP | OPTIONAL | array|null | entity:file |
| geu_role | LOOKUP | CONDITIONAL | string|null | entity:file |
| geu_role_definitions | LOOKUP | OPTIONAL | object|null | entity:file |
| geu_type_slot_matrix | LOOKUP | OPTIONAL | object|null | entity:file |
| governance_domain | LOOKUP | OPTIONAL | string|null | entity:file |
| has_tests | DERIVED | OPTIONAL | boolean|null | entity:file |
| input_filters | INPUT | OPTIONAL | object|null | generator |
| inputs | INPUT | OPTIONAL | array|null | All |
| is_directory | DERIVED | OPTIONAL | boolean|null | All |
| is_generated | DERIVED | OPTIONAL | boolean|null | All |
| is_shared | DERIVED | OPTIONAL | boolean|null | All |
| last_build_utc | INPUT | OPTIONAL | string|null | generator |
| last_seen_utc | INPUT | OPTIONAL | string|null | entity |
| layer | INPUT | OPTIONAL | string|null | All |
| metadata | INPUT | OPTIONAL | object|null | entity:file |
| module_id | LOOKUP | OPTIONAL | string|null | entity:file |
| module_id_override | LOOKUP | OPTIONAL | string|null | entity:file |
| module_id_source | LOOKUP | OPTIONAL | string|null | entity:file |
| mtime_utc | INPUT | OPTIONAL | string|null | entity:file |
| notes | INPUT | OPTIONAL | string|null | core,entity,edge,generator |
| ns_code | INPUT | OPTIONAL | string|null | entity:file |
| observed_utc | INPUT | OPTIONAL | string|null | edge |
| one_line_purpose | INPUT | OPTIONAL | string|null | All |
| optional_roles | INPUT | OPTIONAL | array|null | entity:file |
| output_hash | INPUT | OPTIONAL | string|null | generator |
| output_kind | INPUT | OPTIONAL | string|null | generator |
| output_path | INPUT | OPTIONAL | string|null | generator |
| output_path_pattern | INPUT | OPTIONAL | string|null | generator |
| outputs | INPUT | OPTIONAL | array|null | All |
| owner_geu_id | LOOKUP | CONDITIONAL | string|null | entity:file |
| path_aliases | INPUT | OPTIONAL | array|null | All |
| primary_geu_id | LOOKUP | CONDITIONAL | string|null | entity:file |
| process_id | LOOKUP | OPTIONAL | string|null | entity:file |
| process_step_id | LOOKUP | OPTIONAL | string|null | entity:file |
| process_step_role | INPUT | OPTIONAL | string|null | entity:file |
| py_analysis_run_id | N/A | OPTIONAL | string|null | entity:file |
| py_analysis_success | N/A | OPTIONAL | boolean|null | entity:file |
| py_analyzed_at_utc | N/A | OPTIONAL | string|null | entity:file |
| py_ast_dump_hash | N/A | OPTIONAL | string|null | entity:file |
| py_ast_parse_ok | N/A | OPTIONAL | boolean|null | entity:file |
| py_canonical_candidate_score | N/A | OPTIONAL | number|null | entity:file |
| py_canonical_text_hash | N/A | OPTIONAL | string|null | entity:file |
| py_capability_facts_hash | N/A | OPTIONAL | string|null | entity:file |
| py_capability_tags | N/A | OPTIONAL | array|null | entity:file |
| py_complexity_cyclomatic | N/A | OPTIONAL | number|null | entity:file |
| py_component_artifact_path | N/A | OPTIONAL | string|null | entity:file |
| py_component_count | N/A | OPTIONAL | integer|null | entity:file |
| py_component_ids | N/A | OPTIONAL | array|null | entity:file |
| py_coverage_percent | N/A | OPTIONAL | number|null | entity:file |
| py_defs_classes_count | N/A | OPTIONAL | integer|null | entity:file |
| py_defs_functions_count | N/A | OPTIONAL | integer|null | entity:file |
| py_defs_public_api_hash | N/A | OPTIONAL | string|null | entity:file |
| py_deliverable_inputs | N/A | OPTIONAL | array|null | entity:file |
| py_deliverable_interfaces | N/A | OPTIONAL | array|null | entity:file |
| py_deliverable_kinds | N/A | OPTIONAL | array|null | entity:file |
| py_deliverable_outputs | N/A | OPTIONAL | array|null | entity:file |
| py_deliverable_signature_hash | N/A | OPTIONAL | string|null | entity:file |
| py_imports_hash | N/A | OPTIONAL | string|null | entity:file |
| py_imports_local | N/A | OPTIONAL | array|null | entity:file |
| py_imports_stdlib | N/A | OPTIONAL | array|null | entity:file |
| py_imports_third_party | N/A | OPTIONAL | array|null | entity:file |
| py_io_surface_flags | N/A | OPTIONAL | array|null | entity:file |
| py_overlap_best_match_file_id | N/A | OPTIONAL | string|null | entity:file |
| py_overlap_group_id | N/A | OPTIONAL | string|null | entity:file |
| py_overlap_similarity_max | N/A | OPTIONAL | number|null | entity:file |
| py_pytest_exit_code | N/A | OPTIONAL | integer|null | entity:file |
| py_quality_score | N/A | OPTIONAL | number|null | entity:file |
| py_security_risk_flags | N/A | OPTIONAL | array|null | entity:file |
| py_static_issues_count | N/A | OPTIONAL | integer|null | entity:file |
| py_tests_executed | N/A | OPTIONAL | integer|null | entity:file |
| py_tool_versions | N/A | OPTIONAL | object|null | entity:file |
| py_toolchain_id | N/A | OPTIONAL | string|null | entity:file |
| record_id | SYSTEM | REQUIRED | string | core,entity,edge,generator |
| record_kind | INPUT | REQUIRED | string | core,entity,edge,generator |
| rel_type | INPUT | CONDITIONAL | string|null | edge |
| relative_path | EXTRACTED | CONDITIONAL | string|null | entity:file |
| repo_root_id | LOOKUP | OPTIONAL | string|null | All |
| report_outputs | INPUT | OPTIONAL | array|null | All |
| required_roles | INPUT | OPTIONAL | array|null | entity:file |
| required_suite_key | LOOKUP | OPTIONAL | string|null | entity:file |
| resolver_hint | INPUT | OPTIONAL | string|null | entity:external |
| role | INPUT | OPTIONAL | string|null | entity:file |
| role_code | INPUT | OPTIONAL | string|null | entity:file |
| rule_based | DERIVED | OPTIONAL | boolean|null | entity:file |
| runner_based | DERIVED | OPTIONAL | boolean|null | entity:file |
| scan_id | LOOKUP | OPTIONAL | string|null | entity |
| schema_based | DERIVED | OPTIONAL | boolean|null | entity:file |
| schema_version | INPUT | OPTIONAL | string|null | All |
| scope | INPUT | OPTIONAL | string|null | All |
| sha256 | EXTRACTED | CONDITIONAL | string|null | entity:file,asset |
| short_description | INPUT | OPTIONAL | string|null | entity |
| size_bytes | EXTRACTED | OPTIONAL | integer|null | entity:file |
| sort_keys | INPUT | OPTIONAL | array|null | generator |
| sort_rule_id | LOOKUP | OPTIONAL | string|null | generator |
| source_entity_id | LOOKUP | CONDITIONAL | string|null | entity,edge |
| source_file_id | LOOKUP | OPTIONAL | string|null | All |
| source_registry_hash | INPUT | OPTIONAL | string|null | generator |
| source_registry_scan_id | LOOKUP | OPTIONAL | string|null | generator |
| status | INPUT | REQUIRED | string | core,entity,edge,generator |
| step_refs | INPUT | OPTIONAL | array|null | entity:file |
| superseded_by | INPUT | OPTIONAL | string|null | All |
| supersedes_entity_id | LOOKUP | OPTIONAL | string|null | entity |
| tags | INPUT | OPTIONAL | array|null | core,entity,edge,generator |
| target_entity_id | LOOKUP | CONDITIONAL | string|null | edge |
| target_file_id | LOOKUP | OPTIONAL | string|null | All |
| target_schema_id | LOOKUP | OPTIONAL | string|null | All |
| template_ref_entity_id | LOOKUP | OPTIONAL | string|null | generator |
| test_file_ids | LOOKUP | OPTIONAL | array|null | All |
| tool_version | INPUT | OPTIONAL | string|null | edge |
| transient_id | LOOKUP | CONDITIONAL | string|null | entity:transient |
| transient_type | INPUT | OPTIONAL | string|null | entity:transient |
| ttl_seconds | INPUT | OPTIONAL | integer|null | entity:transient |
| type_code | INPUT | OPTIONAL | string|null | entity:file |
| updated_by | INPUT | REQUIRED | string | core,entity,edge,generator |
| updated_utc | INPUT | REQUIRED | string | core,entity,edge,generator |
| validation_rules | INPUT | OPTIONAL | object|null | generator |
| validator_id | LOOKUP | OPTIONAL | string|null | generator |

---

## Derivation Modes

- **EXTRACTED**: Directly extracted from filesystem or scan event
- **SYSTEM**: System-generated (timestamps, IDs, allocators)
- **LOOKUP**: Retrieved from registry or external source
- **DERIVED**: Computed using DSL formulas from other fields
- **INPUT**: User/manual input required
- **HYBRID**: Combination of multiple derivation strategies

---

## Presence Policies

- **REQUIRED**: Field must be populated for all records
- **OPTIONAL**: Field may be null
- **CONDITIONAL**: Required based on record_kind or entity_kind

---

**Generated:** 2026-02-25 19:22:17 UTC
**Source:** 01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json
