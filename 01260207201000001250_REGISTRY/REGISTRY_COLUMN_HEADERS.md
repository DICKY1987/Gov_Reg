# Governance Registry Column Headers
**Schema Version:** 4.0  
**Generated:** 02/13/2026 17:32:39  
**Total Columns:** 27

---

## Complete Column Reference

| Column Name | Description |
|-------------|-------------|
| `anchor_file_id` | file_id of the bundle anchor (schema/SSOT) |
| `artifact_kind` | Type of artifact (YAML, MARKDOWN, PYTHON_MODULE, JSON, SCHEMA, TEST, etc.) |
| `bundle_id` | 16-digit ID for bundle grouping (separate namespace from file_id) |
| `bundle_key` | Human-readable stable bundle name (e.g., GATE_AGGREGATE, ID_REGISTRY) |
| `bundle_role` | Role within bundle (SCHEMA, VALIDATOR, EXECUTOR, RUNNER, BRIDGE, TEST, DOC, REPORT, TOOL, FAILURE_MODE, EVIDENCE_SCHEMA, RULE, SHARED_LIB) |
| `bundle_version` | Optional bundle version string (e.g., v2.5.3) |
| `canonicality` | Canonical status (CANONICAL, DERIVED, REFERENCE, etc.) |
| `coverage_status` | Bundle completeness status (PRESENT, MISSING, DUPLICATE, CONFLICT) |
| `depends_on_file_ids` | Explicit dependency list |
| `enforced_by_file_ids` | List of file_ids that enforce this file |
| `enforces_rule_ids` | List of rule IDs this file enforces |
| `evidence_outputs` | List of evidence outputs |
| `file_id` | Unique identifier for the file |
| `geu_ids` | List of Governance Enforcement Unit IDs associated with this file |
| `geu_role` | Role this file plays in its GEU (SCHEMA, RULE, VALIDATOR, RUNNER, FAILURE_MODE, EVIDENCE, TEST, REPORT, SHARED_LIB, or null) |
| `governance_domain` | Governance domain category (CONFIGS, REPORTS, SCHEMAS, etc.) |
| `has_tests` | Boolean indicating if file has associated tests |
| `is_shared` | Boolean indicating if file is shared across multiple GEUs |
| `layer` | Architectural layer (CI_CD, DOCUMENTATION, CORE, TESTING, VALIDATION, GOVERNANCE, etc.) |
| `module_id` | Dir ID of module root folder (section assignment) |
| `owner_geu_id` | GEU ID of the owner if file is shared, otherwise null |
| `primary_geu_id` | Primary GEU ID responsible for this file, or null if not assigned |
| `relative_path` | Path to the file relative to repository root |
| `repo_root_id` | Repository root identifier (e.g., AI_PROD_PIPELINE) |
| `report_outputs` | List of report outputs |
| `superseded_by` | file_id of replacement (for duplicates) |
| `test_file_ids` | List of test file_ids for this file |


---

## Column Categories

### Identity & Location
- `file_id` - Unique identifier for the file
- `relative_path` - Path to the file relative to repository root
- `module_id` - Dir ID of module root folder (section assignment)
- `repo_root_id` - Repository root identifier

### Architecture & Classification
- `layer` - Architectural layer
- `artifact_kind` - Type of artifact
- `governance_domain` - Governance domain category
- `canonicality` - Canonical status

### GEU (Governance Enforcement Unit) Fields
- `geu_ids` - List of Governance Enforcement Unit IDs
- `is_shared` - Boolean indicating if file is shared across multiple GEUs
- `owner_geu_id` - GEU ID of the owner if file is shared
- `primary_geu_id` - Primary GEU ID responsible for this file
- `geu_role` - Role this file plays in its GEU

### Bundle Fields
- `bundle_id` - 16-digit ID for bundle grouping
- `bundle_key` - Human-readable stable bundle name
- `bundle_role` - Role within bundle
- `bundle_version` - Optional bundle version string
- `anchor_file_id` - file_id of the bundle anchor

### Dependencies & Relationships
- `depends_on_file_ids` - Explicit dependency list
- `enforced_by_file_ids` - List of file_ids that enforce this file
- `enforces_rule_ids` - List of rule IDs this file enforces
- `superseded_by` - file_id of replacement (for duplicates)

### Testing & Evidence
- `has_tests` - Boolean indicating if file has associated tests
- `test_file_ids` - List of test file_ids for this file
- `evidence_outputs` - List of evidence outputs
- `report_outputs` - List of report outputs

### Status Fields
- `coverage_status` - Bundle completeness status

---

**Generated:** 2026-02-16 07:18:11
