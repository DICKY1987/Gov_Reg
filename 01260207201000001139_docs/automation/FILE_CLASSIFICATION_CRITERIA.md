# File Classification Criteria Guide
## Key Functions, Responsibilities, and File Traits by Section

This document defines the classification rules for organizing files into logical sections/modules within the Gov_Reg system.

---

## 1. Core Governance Engine

### Key Functions & Responsibilities:
- Central registry management and SSOT maintenance
- Governance rule enforcement and coordination
- GEU (Governance Enforcement Unit) lifecycle management
- Registry transition state machine operations
- Core business logic for governance framework

### File Traits (Classification Rules):
- **Directory Location**: `govreg_core/`, `src/` (except `src/validators/`), `src/P_*_geu_governance/`, `src/registry_transition/`, `REGISTRY/`
- **File Names**:
  - `*governance_registry*.json` (main registry files)
  - `*_COMPLETE_SSOT.json`
  - Files in `govreg_core/` with `config`, `scanner`, `reporter`, `validator`, `__init__`
- **Code Patterns**:
  - Imports from `govreg_core` modules
  - Functions managing registry read/write operations
  - State machine logic (`lifecycle_state.py`, `state_machine.py`)
  - GEU CLI commands (`cli.py`, `__main__.py`)
- **Documentation Headers**:
  - `FILE_ID: P_01999000042260124021` through `P_01999000042260124025`
  - Docstrings mentioning "registry loading", "governance", "GEU"
- **Registry Metadata**:
  - `layer: "CORE"`
  - `artifact_kind: "PYTHON_MODULE"`
  - `geu_role: "RULE"` or `"SHARED_LIB"`

---

## 2. ID Management System

### Key Functions & Responsibilities:
- Unique ID allocation and generation (20-digit format)
- ID canonicality enforcement and correction
- Counter management with atomic operations
- ID format validation and migration
- Prevention of ID collisions and race conditions

### File Traits (Classification Rules):
- **File Names**:
  - Contains `ID_CANONICALITY*`, `ID_ALLOCATOR*`, `ID_IDENTITY*`, `ID_CRAZY*`
  - `*_COUNTER_STORE.json*`
  - `ID_SCRIPT_INVENTORY.jsonl`
  - `*id_allocator*`, `*id_format*`, `*file_id*` in name
- **Code Patterns**:
  - Functions: `allocate_single_id()`, `allocate_batch_ids()`, `reserve_id_range()`
  - Imports: `atomic_json_read`, `atomic_json_write`, file locking (`fcntl`, `msvcrt`)
  - Regex patterns: `^[0-9]{20}$`, `^[0-9]{16}$`
  - Thread locks for counter access
- **Documentation Headers**:
  - `FILE_ID: 01999000042260124027` (id_allocator)
  - Mentions "ID Allocation", "proactive ID assignment", "race conditions"
- **Content Indicators**:
  - JSON with `"next_file_id"`, `"next_doc_id"`, `"last_allocation"`
  - Extensive discussion of ID formats (19-digit vs 20-digit migrations)

---

## 3. Schemas & Contracts

### Key Functions & Responsibilities:
- Formal structural definitions for all artifacts
- JSON Schema validation rules
- Contract specifications for interfaces
- Type definitions and constraints
- Version-controlled schema evolution

### File Traits (Classification Rules):
- **Directory Location**: `schemas/`, `contracts/`
- **File Extensions**: `.schema.json`, `*_schema.json`, `.contract.json`
- **File Names**:
  - `*column_dictionary_schema*`
  - `*command_spec.schema*`
  - `*phase_contract*`
  - `*transition_contract*`
- **JSON Structure**:
  - Contains `"$schema": "http://json-schema.org/draft-07/schema#"`
  - Contains `"type": "object"`, `"required": []`, `"properties": {}`
  - Has `"$id"` field with schema URI
  - Contains `"title"` and `"description"` at root level
- **Registry Metadata**:
  - `artifact_kind: "SCHEMA"`
  - `geu_role: "SCHEMA"`
  - `bundle_role: "SCHEMA"`
- **Content Indicators**:
  - Defines validation patterns (regex, enums, ranges)
  - No executable code (pure declarative JSON)

---

## 4. Scripts & Automation

### Key Functions & Responsibilities:
- Executable automation and workflows
- Migration script execution
- Data transformation and processing
- Batch operations and orchestration
- CLI tools and utilities

### File Traits (Classification Rules):
- **Directory Location**: `scripts/`, `scripts/migration/`
- **File Extensions**: `.py` (executable Python scripts)
- **File Name Patterns**:
  - Prefix `P_*` followed by numeric ID
  - Contains: `run_all`, `migrate_*`, `fix_*`, `check_*`, `generate_*`
  - Examples: `P_01999000042260124027_id_allocator.py`, `P_*_migrate_*.py`
- **Code Patterns**:
  - Shebang: `#!/usr/bin/env python3`
  - Has `if __name__ == "__main__":` block
  - Uses `argparse` or CLI argument parsing
  - Contains `main()` function
  - Performs file system operations (read/write/copy/move)
- **Functional Indicators**:
  - Imports from `govreg_core` or other modules
  - Not primarily a test file (no `pytest`, `unittest` imports)
  - Not a validator (doesn't focus on validation logic)
- **Registry Metadata**:
  - `artifact_kind: "PYTHON_MODULE"` or `"SCRIPT"`
  - `layer: "AUTOMATION"` or `"MIGRATION"`
  - `bundle_role: "EXECUTOR"`, `"RUNNER"`, or `"TOOL"`

---

## 5. Validation & Testing

### Key Functions & Responsibilities:
- Unit testing for modules and functions
- Integration testing for workflows
- Validation logic enforcement
- Quality gate checks
- Test fixtures and utilities

### File Traits (Classification Rules):
- **Directory Location**: `tests/`, `test/`, `validators/`, `src/validators/`
- **File Name Patterns**:
  - Tests: `test_*.py`, `*_test.py`, `P_*_test_*.py`
  - Validators: `validate_*.py`, `*_validator.py`
  - Config: `conftest.py`, `pytest.ini`
- **Code Patterns (Tests)**:
  - Imports: `pytest`, `unittest`, `@pytest.fixture`
  - Functions starting with `test_*`
  - Assertions: `assert`, `assertEqual`, `assertTrue`
  - Fixtures and mocks: `@pytest.fixture`, `unittest.mock`, `patch`
- **Code Patterns (Validators)**:
  - Functions: `validate_*()`, `check_*()`, `verify_*()`
  - Returns validation results (pass/fail, error lists)
  - Loads schemas and performs validation against them
  - CLI usage for standalone validation execution
- **Documentation Headers**:
  - "Unit tests for...", "Validator for...", "Validates that..."
- **Registry Metadata**:
  - `artifact_kind: "TEST"` or `"VALIDATOR"`
  - `geu_role: "TEST"` or `"VALIDATOR"`
  - `bundle_role: "TEST"` or `"VALIDATOR"`
  - `layer: "TESTING"` or `"VALIDATION"`

---

## 6. Documentation

### Key Functions & Responsibilities:
- System documentation and guides
- Architecture descriptions
- Implementation plans and strategies
- User guides and tutorials
- Historical documentation archive

### File Traits (Classification Rules):
- **Directory Location**: `docs/`, `OLD_MD_DOCUMENTS_FOR_REVIEW/`
- **File Extensions**: `.md`, `.txt`, `.docx`
- **File Name Patterns**:
  - `README*.md`, `GUIDE*.md`, `*_GUIDE.md`
  - `DEPLOYMENT_CHECKLIST*.md`
  - `*_PLAN*.md`, `*_STRATEGY*.md`, `*_SUMMARY*.md`
  - Contains: `IMPLEMENTATION_*`, `EXECUTION_*`, `ARCHITECTURE_*`
- **Content Indicators**:
  - Markdown headers (`#`, `##`, `###`)
  - Prose descriptions (paragraphs of text)
  - Code examples in fenced blocks (```)
  - Lists, tables, diagrams
  - No executable code (documentation only)
- **Registry Metadata**:
  - `artifact_kind: "MARKDOWN"` or `"DOCUMENTATION"`
  - `layer: "DOCUMENTATION"`
  - `bundle_role: "DOC"`
- **Exclusions**: Not `.md` files that are primarily code/config (e.g., GitHub Actions YAML)

---

## 7. Configuration & Policies

### Key Functions & Responsibilities:
- System configuration parameters
- Policy definitions and rules
- Normalization maps
- Update and null handling policies
- Environment-specific settings

### File Traits (Classification Rules):
- **Directory Location**: `config/`, `policies/`
- **File Extensions**: `.json`, `.yaml`, `.yml`
- **File Name Patterns**:
  - `*_policy.json`, `*_policy_map.json`
  - `*_config.json`, `*_normalization_map.json`
  - `IDENTITY_CONFIG*.yaml`
  - Examples: `evidence_path_policy.json`, `null_policy_map.json`
- **JSON Structure**:
  - Top-level keys: `"version"`, `"description"`, `"policies"`, `"rules"`
  - Contains policy definitions with enforcement levels
  - Has configuration parameters (not data records)
- **Content Indicators**:
  - Formulas and templates (e.g., `"evidence/{plan_id}/{run_id}/"`)
  - Policy enforcement levels: `"MANDATORY"`, `"RECOMMENDED"`, `"OPTIONAL"`
  - Mapping structures (old → new transformations)
- **Registry Metadata**:
  - `artifact_kind: "YAML"` or `"JSON"`
  - `layer: "CONFIGS"` or `"GOVERNANCE"`
  - `geu_role: "RULE"` or `"SCHEMA"`

---

## 8. Evidence & Gates

### Key Functions & Responsibilities:
- Execution evidence collection
- Validation gate results
- Audit reports and compliance logs
- Test execution artifacts
- Quality control outputs

### File Traits (Classification Rules):
- **Directory Location**: `evidence/`, `gates/`
- **File Name Patterns**:
  - `*_audit.report.json`, `*_audit.duplicate_*.json`
  - `*_validation_report.json`, `*_execution_log.json`
  - `*_coverage.json`, `*_results.json`
  - Dated evidence: `*_20260*.json`
- **JSON Structure**:
  - Root keys: `"generated_at"`, `"checks"`, `"report"`, `"results"`
  - Contains metrics: `"valid"`, `"invalid"`, `"total"`, `"passed"`, `"failed"`
  - Has execution metadata: timestamps, paths, run IDs
- **Content Indicators**:
  - Evidence of execution (logs, diffs, manifests)
  - Pass/fail results and statistics
  - Timestamps and run identifiers
  - Links to source artifacts being validated
- **Registry Metadata**:
  - `artifact_kind: "EVIDENCE"` or `"REPORT"`
  - `geu_role: "EVIDENCE"` or `"REPORT"`
  - `layer: "EVIDENCE"` or `"REPORTS"`

---

## 9. GEU (Governance Enforcement Units)

### Key Functions & Responsibilities:
- GEU definitions and configurations
- GEU association mappings
- GEU set management
- GEU-specific business rules

### File Traits (Classification Rules):
- **Directory Location**: `GEU/`
- **File Name Patterns**:
  - `*geu_sets*.json`, `*GEU*.json`
  - Files explicitly about GEU structure
- **JSON Structure**:
  - Contains `"geu_id"` fields
  - Has GEU metadata: `"geu_type"`, `"geu_owner"`, `"geu_status"`
  - Arrays of GEU associations
- **Content Indicators**:
  - Defines GEU boundaries and membership
  - Maps files to GEUs
  - GEU lifecycle state information
- **Registry References**:
  - Files listed in registry with `"geu_ids"` array populated
  - `"is_shared": true` with `"owner_geu_id"`

---

## 10. File Watcher & Path Abstraction

### Key Functions & Responsibilities:
- File system monitoring and change detection
- Path abstraction and indirection
- Path registry management
- Automated reaction to file changes
- Platform-independent path resolution

### File Traits (Classification Rules):
- **Directory Location**: `FILE WATCHER/`, `PATH_FILES/`
- **File Name Patterns**:
  - `*watcher*.py`, `*path_registry*.py`
  - `*path_abstraction*.md`, `*PATH*.md`
  - Files in `FILE WATCHER/scripts/`
- **Code Patterns**:
  - Imports: `watchdog`, file system observers
  - Functions: `watch()`, `on_modified()`, `on_created()`
  - Path resolution functions: `resolve_path()`, `normalize_path()`
  - Registry lookups for path mappings
- **Documentation Keywords**:
  - "path abstraction", "indirection layer", "file watcher", "monitoring"
- **Registry Metadata**:
  - `layer: "MONITORING"` or `"PATH_ABSTRACTION"`

---

## 11. Planning & Execution

### Key Functions & Responsibilities:
- Long-term execution planning
- Phase contract definitions
- Task decomposition and tracking
- Execution status reporting
- Traceability matrix management

### File Traits (Classification Rules):
- **Directory Location**: `LP_LONG_PLAN/`, `sections/`
- **File Name Patterns**:
  - `PHASE_*`, `*_EXECUTION_*.md`
  - `*phase_contract*.json`, `*phase_tracking*.json`
  - `traceability_matrix.json`
  - `sec_*.json` (section definitions)
- **JSON Structure (Sections)**:
  - Root keys: `"section_id"`, `"title"`, `"required"`
  - Contains phase/gate definitions
  - Has execution criteria and commands
- **Content Indicators**:
  - Phase numbers and identifiers
  - Execution checklists and criteria
  - Task dependency graphs (DAGs)
  - Completion status tracking
- **Registry Metadata**:
  - `layer: "PLANNING"` or `"EXECUTION"`
  - Files are part of planning/execution workflow

---

## 12. State Management

### Key Functions & Responsibilities:
- Persistent system state storage
- Decision ledger tracking
- Feature flag management
- Phase tracking and progression
- Integration point coordination

### File Traits (Classification Rules):
- **Directory Location**: `.state/`, `.state_temp/`
- **File Name Patterns**:
  - `*decision_ledger*.json`, `*feature_flags*.json`
  - `*phase_tracking*.json`, `*integration_points*.json`
  - Files in `.state/evidence/`, `.state/plan/`, `.state/reports/`
- **JSON Structure**:
  - State snapshots with timestamps
  - Decision records with rationale
  - Feature toggles with status
- **Content Indicators**:
  - Current state of system components
  - Historical state transitions
  - Temporary execution state
- **Persistence**:
  - Files intended to persist across sessions
  - Not user-facing documentation

---

## 13. CI/CD & Integration

### Key Functions & Responsibilities:
- Continuous integration workflows
- GitHub Actions automation
- Pre-commit hook enforcement
- Deployment automation
- Pipeline orchestration

### File Traits (Classification Rules):
- **Directory Location**: `.github/`, `.github/workflows/`
- **File Name Patterns**:
  - `pre-commit`, `.pre-commit-config.yaml`
  - Workflow YAML files in `.github/workflows/`
  - `*CI_CD*.md`, `*DEPLOYMENT*.md`
- **File Extensions**: `.yml`, `.yaml` (in `.github/workflows/`)
- **YAML Structure** (Workflows):
  - Top-level keys: `"on:"`, `"jobs:"`, `"steps:"`
  - GitHub Actions syntax
- **Code Patterns**:
  - Hook scripts with `#!/bin/bash` or `#!/usr/bin/env python3`
  - Calls to validation commands before commit
- **Registry Metadata**:
  - `layer: "CI_CD"`

---

## 14. Backups & Archives

### Key Functions & Responsibilities:
- Historical data preservation
- Backup storage for recovery
- Migration history tracking
- Legacy artifact retention

### File Traits (Classification Rules):
- **Directory Location**: `backups/`, `Archive_Gov_Reg/`
- **File Name Patterns**:
  - `*.backup`, `*_BEFORE_*`, `*_backup_*.json`
  - Contains date stamps: `*_20260*`
  - Files in subdirectories like `backups/doc_id_migration/`
- **Content Indicators**:
  - Duplicates of current files with older timestamps
  - Pre-migration snapshots
  - Archived versions with version numbers
- **Organizational Rule**:
  - If file exists in both current location and `backups/`, the backup is the archived copy

---

## 15. Templates

### Key Functions & Responsibilities:
- Reusable document templates
- Code generation templates
- Standardized artifact structures

### File Traits (Classification Rules):
- **Directory Location**: `templates/`
- **File Name Patterns**: `*_template.*`, `*.template.*`
- **Content Indicators**:
  - Placeholder variables: `{{VARIABLE_NAME}}`, `{placeholder}`
  - Incomplete sections for user population
  - Reusable structures
- **Registry Metadata**:
  - `artifact_kind: "TEMPLATE"`

---

## 16. Monitoring & Training

### Key Functions & Responsibilities:
- System health monitoring
- Alert definitions and triggers
- Training materials and guides
- Observability configurations

### File Traits (Classification Rules):
- **Directory Location**: `monitoring/`, `training/`
- **File Name Patterns**:
  - `*alert*.py`, `*monitor*.py`, `*event_*.py`
  - Training guides and materials
- **Code Patterns**:
  - Event emitters and sinks
  - Monitoring metric collection
  - Alert thresholds and conditions

---

## 17. Patches & Migrations

### Key Functions & Responsibilities:
- Data transformation patches
- Registry migration tracking
- Transition vector definitions
- Forward/backward compatibility

### File Traits (Classification Rules):
- **Directory Location**: `PATCHES/`, `.migration/`
- **File Extensions**: `.patch.json`
- **File Name Patterns**:
  - `*_patch.json`, `geu_fix.*.patch.json`
  - `transition_*.yaml`, `*migration_report*.json`
- **JSON Structure (Patches)**:
  - Operations: `"add"`, `"remove"`, `"replace"`, `"transform"`
  - Before/after snapshots
  - Patch metadata: version, author, timestamp
- **Content Indicators**:
  - Data transformations (migrations)
  - Compatibility shims
  - Transition tracking

---

## 18. Deployment & Operations

### Key Functions & Responsibilities:
- Deployment checklists and procedures
- Operational runbooks
- System status summaries
- Critical fixes documentation

### File Traits (Classification Rules):
- **File Name Patterns**:
  - `DEPLOYMENT_CHECKLIST*.md`
  - `IMPLEMENTATION_SUMMARY*.md`, `FINAL_STATUS*.md`
  - `CRITICAL_FIXES*.md`
  - `VERIFIED_ARTIFACT_BUNDLE*.md`
- **Content Indicators**:
  - Checklists with `[ ]` or `[x]`
  - Deployment steps and procedures
  - Sign-off and verification sections
  - Operational procedures
- **Placement**: Usually in root directory for visibility

---

## Classification Algorithm

### Priority Order:
1. **Explicit Directory Signals**: If in `tests/`, `validators/`, `schemas/`, etc. → Follow directory mapping
2. **File Name Patterns**: Match against specific naming conventions
3. **File Extension**: `.schema.json`, `.py`, `.md` narrows possibilities
4. **Content Structure**: Parse first 50 lines for imports, JSON schema, docstrings
5. **Registry Metadata**: Check `layer`, `artifact_kind`, `geu_role`, `bundle_role`
6. **Functional Intent**: Analyze what the file does (test vs. execute vs. validate vs. document)

### Disambiguation Rules:
- **Script vs. Test**: If has `test_*` functions or `pytest` imports → Test; else Script
- **Schema vs. Config**: If has JSON Schema syntax (`"$schema"`, `"properties"`) → Schema; else Config
- **Evidence vs. Report**: Evidence is raw execution data; Reports are formatted for humans
- **Core vs. Script**: Core has no `if __name__ == "__main__"`; Scripts are CLI-executable

---

## Metadata-Driven Classification

The unified registry (`01999000042260124503_governance_registry_unified.json`) contains canonical metadata for classification:

```json
{
  "file_id": "...",
  "relative_path": "...",
  "layer": "CI_CD | DOCUMENTATION | CORE | TESTING | VALIDATION | GOVERNANCE | ...",
  "artifact_kind": "YAML | MARKDOWN | PYTHON_MODULE | JSON | SCHEMA | TEST | ...",
  "geu_role": "SCHEMA | RULE | VALIDATOR | RUNNER | FAILURE_MODE | EVIDENCE | TEST | REPORT | SHARED_LIB",
  "bundle_role": "SCHEMA | VALIDATOR | EXECUTOR | RUNNER | BRIDGE | TEST | DOC | REPORT | TOOL | ..."
}
```

**Use these fields as ground truth when available.**

---

## Edge Cases

### Multi-Role Files:
- **Test Script that also Validates**: Categorize as Test (primary purpose)
- **Documentation with Embedded Config**: Categorize as Documentation (artifact_kind determines)
- **Schema used as Config**: If has `$schema` at root → Schema

### Generated Files:
- Check for `"generated_at"` or `"generated"` field → Often Evidence or Reports
- Auto-generated documentation → Still Documentation

### Numbered Prefixes:
- Files with numeric prefixes (e.g., `01260207201000000110_*`) retain original classification
- Prefix is for ID management, not for categorization

---

## Verification Commands

To verify classification correctness:

```bash
# Check if file meets criteria for section
python validators/validate_classification.py --file <path> --expected-section <section>

# Generate classification report
python scripts/P_01260207201000000001_classify_all_files.py --report classification_report.json
```

---

**Document Version**: 1.0
**Last Updated**: 2026-02-13
**Maintained By**: Gov_Reg Core Team
