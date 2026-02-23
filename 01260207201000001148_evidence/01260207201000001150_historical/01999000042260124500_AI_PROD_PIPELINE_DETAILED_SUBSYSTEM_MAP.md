# AI-PROD-PIPELINE Detailed Subsystem File Map
## Generated: 2026-01-24 05:14 UTC
## Post-Cleanup Status

**Deprecated files deleted**: ✅ 475+ files removed
**Remaining solution files**: 500+ active implementation files

---

## DELETION SUMMARY

### Successfully Removed:
1. ✅ Backup files: 2 files
2. ✅ OLD_EXTRACTED_20251212 archive: 17 files
3. ✅ htmlcov directories: 433 files (320 + 57 + 56)
4. ✅ Deprecation analysis files: 14 files
5. ✅ Legacy automation files: 4 files
6. ✅ workspace_ARCHIVE: 11 files

**Total Deleted**: ~481 files and 6 directories

---

## DETAILED SUBSYSTEM FILE LOCATIONS

### 1. WORK UNIT CONTRACT SYSTEM

**Location**: `C:\Users\richg\ALL_AI\GOVERNANCE\lifecycle\v2.5.3\`

**Key Schemas**:
- `DOC-CONFIG-GATE-AGGREGATE-SCHEMA-492__gate_aggregate.schema.json`
- `DOC-CONFIG-UNIVERSAL-REGISTRY-ENTRY-SCHEMA-495__universal_registry_entry.schema.json`
- `DOC-CONFIG-VALIDATOR-CATALOG-SCHEMA-496__validator_catalog.schema.json`
- `DOC-CONFIG-SYSTEM-MANIFEST-SCHEMA-494__system_manifest.schema.json`

**Location**: `C:\Users\richg\ALL_AI\GOVERNANCE\ssot\SSOT_System\SSOT_SYS_schemas\`
- `DOC-CONFIG-SSOT-CURRENT-APPROACH-SCHEMA-845__ssot_current_approach.schema.json`

**Models**:
- `C:\Users\richg\ALL_AI\GOVERNANCE\ssot\SSOT_System\modules\types.py`
- `C:\Users\richg\ALL_AI\modules\DOC-CORE-MODULES-TYPES-410__types.py`

---

### 2. RUNNER + EVIDENCE GATE SYSTEM

**Core Runners**:
- `C:\Users\richg\ALL_AI\GOVERNANCE\gates\gate_runner.py` ⚠️ **CRITICAL**
- `C:\Users\richg\ALL_AI\GOVERNANCE\gates\enforcement_bridge.py` ⚠️ **CRITICAL**
- `C:\Users\richg\ALL_AI\automation\test_runner\DOC-TEST-TEST-RUNNER-RUNNER-524__runner.py`

**Evidence Collection**:
- `C:\Users\richg\ALL_AI\AI_CLI_PROVENANCE_SOLUTION\DOC-SCRIPT-0993__PROV-SOL_validate_evidence_schema.py`
- `C:\Users\richg\ALL_AI\GOVERNANCE\ssot\SSOT_System\SSOT_SYS_tools\DOC-CORE-SSOT-SYS-TOOLS-DEEP-EVIDENCE-VALIDATOR-1100__deep_evidence_validator.py`
- `C:\Users\richg\ALL_AI\RUNTIME\file_id\SUB_DOC_ID\4_REPORTING_MONITORING\DOC-CORE-4-REPORTING-MONITORING-GENERATE-1167__generate_evidence_bundle.py`

**Event Infrastructure** ⚠️ **CRITICAL SYSTEM**:
- `C:\Users\richg\ALL_AI\DOC-SCRIPT-1217__event_emitter.py`
- `C:\Users\richg\ALL_AI\DOC-SCRIPT-1218__event_router.py`
- `C:\Users\richg\ALL_AI\DOC-SCRIPT-1219__event_sinks.py`
- `C:\Users\richg\ALL_AI\LP_LONG_PLAN\event_emitter.py`
- `C:\Users\richg\ALL_AI\LP_LONG_PLAN\event_router.py`
- `C:\Users\richg\ALL_AI\LP_LONG_PLAN\event_sinks.py`
- `C:\Users\richg\ALL_AI\GOVERNANCE\ssot\SSOT_System\SSOT_SYS_tools\DOC-CORE-SSOT-SYS-TOOLS-EVENT-EMITTER-1109__event_emitter.py`
- `C:\Users\richg\ALL_AI\GOVERNANCE\ssot\SSOT_System\SSOT_SYS_tools\DOC-CORE-SSOT-SYS-TOOLS-EVENT-ROUTER-1110__event_router.py`
- `C:\Users\richg\ALL_AI\GOVERNANCE\ssot\SSOT_System\SSOT_SYS_tools\DOC-CORE-SSOT-SYS-TOOLS-EVENT-SINKS-1111__event_sinks.py`

**Event Tests**:
- `C:\Users\richg\ALL_AI\GOVERNANCE\ssot\SSOT_System\SSOT_SYS_tests\DOC-TEST-EVENT-INFRASTRUCTURE-E2E-001__test_e2e_event_infrastructure.py`
- `C:\Users\richg\ALL_AI\GOVERNANCE\ssot\SSOT_System\SSOT_SYS_tests\unit\DOC-CORE-SSOT-SYS-TESTS-UNIT-TEST-EVENT-EMITTER-1113__test_event_emitter.py`

---

### 3. DETERMINISTIC TRACE + REPLAY SYSTEM

**Trace Storage**:
- `C:\Users\richg\ALL_AI\RUNTIME\cli\SUB_CLP\deterministic_debug_audit\src\core\DOC-CORE-CORE-TRACE-STORAGE-1151__trace_storage.py`
- `C:\Users\richg\ALL_AI\LP_LONG_PLAN\PHASE_1_PLANNING\pipeline\src\core\DOC-CORE-CORE-TRACE-STORAGE-1009__trace_storage.py`

**Trace Context** (Multiple implementations):
- `C:\Users\richg\ALL_AI\GOVERNANCE\ssot\SSOT_System\SSOT_SYS_tools\DOC-CORE-SSOT-SYS-TOOLS-TRACE-CONTEXT-1108__trace_context.py`
- `C:\Users\richg\ALL_AI\GOVERNANCE\ssot\SSOT_System\SSOT_SYS_tools\DOC-CORE-1265__trace_context.py`
- `C:\Users\richg\ALL_AI\RUNTIME\file_id\SUB_DOC_ID\common\trace_context.py`
- `C:\Users\richg\ALL_AI\RUNTIME\file_id\SUB_DOC_ID\common\DOC-CORE-SSOT-SYS-TOOLS-TRACE-CONTEXT-1108__trace_context.py`

**Determinism Checkers**:
- `C:\Users\richg\ALL_AI\LP_LONG_PLAN\PHASE_1_PLANNING\pipeline\src\core\DOC-CORE-CORE-DETERMINISM-1005__determinism.py`
- `C:\Users\richg\ALL_AI\GOVERNANCE\lifecycle\v2.5.3\DOC-CORE-LIFECYCLE-V2-5-3-CONSOLIDATED-CROSS-402__cross_reference_validator.py`

**Tests**:
- `C:\Users\richg\ALL_AI\GOVERNANCE\ssot\SSOT_System\SSOT_SYS_tests\unit\DOC-TEST-UNIT-TEST-TRACE-CONTEXT-001__test_trace_context.py`
- `C:\Users\richg\ALL_AI\GOVERNANCE\ssot\SSOT_System\SSOT_SYS_tests\unit\DOC-TEST-UNIT-TEST-DETERMINISM-VALIDATION-640__test_determinism_validation.py`

---

### 4. REGISTRY SSOT + DRIFT PREVENTION SYSTEM

**Central Registry Files** ⚠️ **CRITICAL**:
- `C:\Users\richg\ALL_AI\data\DOC-CONFIG-ID-REGISTRY-435__id_registry.json`
- `C:\Users\richg\ALL_AI\GOVERNANCE\ssot\SSOT_System\SSOT_SYS_tools\DOC-CONFIG-ID-REGISTRY-847__id_registry.json`
- `C:\Users\richg\ALL_AI\REGISTRY_A_FILE_ID.json`
- `C:\Users\richg\ALL_AI\REGISTRY_B_ASSET_ID.json`
- `C:\Users\richg\ALL_AI\REGISTRY_C_TRANSIENT_ID.json`
- `C:\Users\richg\ALL_AI\REGISTRY_D_EDGE_RELATION.json`

**Registry Management**:
- `C:\Users\richg\ALL_AI\DOC-SCRIPT-1233__update_registry_dir_ids.py`
- `C:\Users\richg\ALL_AI\GOVERNANCE\ssot\SSOT_System\SSOT_SYS_tools\DOC-CORE-SSOT-SYS-TOOLS-ID-REGISTRY-1105__id_registry.py`
- `C:\Users\richg\ALL_AI\modules\path_abstraction\DOC-SCRIPT-1320__path_registry.py`
- `C:\Users\richg\ALL_AI\modules\path_abstraction\DOC-CORE-PATH-ABSTRACTION-PATH-REGISTRY-192__path_registry.py`

**SSOT Core**:
- `C:\Users\richg\ALL_AI\GOVERNANCE\ssot\SSOT_System\DOC-CONFIG-SSOT-CURRENT-APPROACH-505__SSOT_CURRENT_APPROACH.json`
- `C:\Users\richg\ALL_AI\GOVERNANCE\ssot\SSOT_System\DOC-CONFIG-SYSTEM-MANIFEST-506__SYSTEM_MANIFEST.json`

**Validators**:
- `C:\Users\richg\ALL_AI\GOVERNANCE\ssot\SSOT_System\SSOT_SYS_tools\DOC-CORE-SSOT-SYS-TOOLS-VALIDATE-SSOT-1112__validate_ssot.py`
- `C:\Users\richg\ALL_AI\UTI_TOOLS\DOC-CORE-UTI-TOOLS-VALIDATE-REGISTRY-823__validate_registry.py`
- `C:\Users\richg\ALL_AI\scripts\validators\DOC-VALIDATOR-REGISTRY-LOCKING-001__validate_registry_locking.py`

**Tests**:
- `C:\Users\richg\ALL_AI\GOVERNANCE\ssot\SSOT_System\SSOT_SYS_tests\unit\DOC-TEST-UNIT-TEST-ID-REGISTRY-641__test_id_registry.py`
- `C:\Users\richg\ALL_AI\RUNTIME\file_id\SUB_DOC_ID\6_TESTS\DOC-TEST-REGISTRY-INTEGRITY-001__test_registry_integrity.py`
- `C:\Users\richg\ALL_AI\RUNTIME\file_id\SUB_DOC_ID\6_TESTS\DOC-TEST-REGISTRY-CONCURRENCY-001__test_registry_concurrency.py`

---

### 5. VALIDATORS (PRE/POST GATES)

**Validation Core** (`C:\Users\richg\ALL_AI\GOVERNANCE\ssot\SSOT_System\SSOT_SYS_tools\`):
- `DOC-CORE-SSOT-SYS-TOOLS-VALIDATE-SSOT-1112__validate_ssot.py`
- `DOC-CORE-SSOT-SYS-TOOLS-VALIDATE-SOLUTIONS-1111__validate_solutions.py`
- `DOC-CORE-SSOT-SYS-TOOLS-VALIDATE-MANIFEST-1110__validate_manifest_coverage.py`
- `DOC-CORE-SSOT-SYS-TOOLS-VALIDATE-MANIFEST-1109__validate_manifest.py`
- `DOC-CORE-SSOT-SYS-TOOLS-VALIDATE-AUTOMATION-SPEC-518__validate_automation_spec.py`
- `DOC-CORE-SSOT-SYS-TOOLS-DEEP-EVIDENCE-VALIDATOR-1100__deep_evidence_validator.py`
- `DOC-CORE-SSOT-SYS-TOOLS-AUTHORITY-CHAIN-ENFORCER-1097__authority_chain_enforcer.py`

**Validation Script Library** (`C:\Users\richg\ALL_AI\scripts\validators\`):
**100+ validator scripts** following pattern: `DOC-SCRIPT-####__validate_*.py`

Sample validators:
- `DOC-SCRIPT-0989__validate_rule_id.py`
- `DOC-SCRIPT-0990__validate_run_id.py`
- `DOC-SCRIPT-0991__validate_schema_id.py`
- `DOC-SCRIPT-0992__validate_alert_id.py`
- ... through ...
- `DOC-SCRIPT-1026__validate_requirement_id.py`

**Specialized Validators**:
- `DOC-VALIDATOR-ARTIFACT-FRESHNESS-001__validate_artifact_freshness.py`
- `DOC-VALIDATOR-DOC-ID-ASSIGNMENTS-001__validate_file_id_assignments.py`
- `DOC-VALIDATOR-MUTATION-COVERAGE-001__validate_mutation_coverage.py`
- `DOC-VALIDATOR-PERFORMANCE-REGRESSION-001__validate_performance.py`
- `DOC-VALIDATOR-PROTECTED-PATHS-001__validate_protected_paths.py`

**Tests** (`C:\Users\richg\ALL_AI\tests\validators\`):
- 40+ validator test files matching pattern: `DOC-TEST-0###__test_validate_*_id.py`

---

### 6. DAG SCHEDULER SYSTEM

**DAG Core**:
- `C:\Users\richg\ALL_AI\modules\core_state\DOC-SCRIPT-1318__m010003_dag_utils.py`
- `C:\Users\richg\ALL_AI\core\state\DOC-SCRIPT-1249__dag_utils.py`
- `C:\Users\richg\ALL_AI\RUNTIME\process_steps\PROCESS_STEP_LIB\tools\dag\DOC-CORE-STATE-DAG-UTILS-170__dag_utils.py`
- `C:\Users\richg\ALL_AI\RUNTIME\process_steps\PROCESS_STEP_LIB\tools\dag\DOC-CORE-ENGINE-DAG-BUILDER-147__dag_builder.py`
- `C:\Users\richg\ALL_AI\WORKFLOWS\planning\PHASE_2_REQUEST_BUILDING\contracts\SUB_IO_CONTRACT_PIPELINE\core\DOC-CORE-CORE-PHASE-DAG-MANAGER-397__phase_dag_manager.py`

**Scheduler** ⚠️ **CRITICAL**:
- `C:\Users\richg\ALL_AI\RUNTIME\engine\PHASE_5_EXECUTION\engine\DOC-CORE-ENGINE-SCHEDULER-158__scheduler.py`

**Pipeline Configs**:
- Found in: `C:\Users\richg\ALL_AI\configs\` (if exists)
- Found in: `C:\Users\richg\ALL_AI\RUNTIME\process_steps\PROCESS_STEP_LIB\config\`

**Tests**:
- `C:\Users\richg\ALL_AI\RUNTIME\process_steps\PROCESS_STEP_LIB\tools\dag\DOC-TEST-ENGINE-TEST-DAG-BUILDER-116__test_dag_builder.py`
- `C:\Users\richg\ALL_AI\RUNTIME\process_steps\PROCESS_STEP_LIB\tools\dag\DOC-CORE-STATE-TEST-DAG-UTILS-126__test_dag_utils.py`

---

### 7. ERROR CLASSIFIER + REMEDY LIBRARY

**Error Engine** ⚠️ **CRITICAL** (`C:\Users\richg\ALL_AI\RUNTIME\recovery\PHASE_6_ERROR_RECOVERY\modules\error_engine\`):
- `src\engine\DOC-ERROR-ENGINE-ERROR-ENGINE-115__error_engine.py`
- `src\engine\DOC-ERROR-ENGINE-PLUGIN-MANAGER-119__plugin_manager.py`
- `src\engine\DOC-ERROR-ENGINE-PIPELINE-ENGINE-118__pipeline_engine.py`
- `src\engine\DOC-ERROR-ENGINE-ERROR-STATE-MACHINE-116__error_state_machine.py`
- `src\engine\DOC-ERROR-ENGINE-ERROR-CONTEXT-114__error_context.py`
- `src\engine\DOC-ERROR-ENGINE-AGENT-ADAPTERS-113__agent_adapters.py`

**Error Plugins** (`C:\Users\richg\ALL_AI\RUNTIME\recovery\PHASE_6_ERROR_RECOVERY\modules\plugins\`):
Plugin directories found:
- `echo\`
- `gitleaks\`
- `md_mdformat_fix\`

**Remediation Tools**:
- `C:\Users\richg\ALL_AI\GOVERNANCE\ssot\SSOT_System\SSOT_SYS_tools\DOC-CORE-SSOT-SYS-TOOLS-EXECUTE-REMEDIATION-1102__execute_remediation.py`
- `C:\Users\richg\ALL_AI\GOVERNANCE\ssot\SSOT_System\SSOT_SYS_tools\DOC-CORE-SSOT-SYS-TOOLS-GENERATE-SOLUTIONS-1104__generate_solutions.py`
- `C:\Users\richg\ALL_AI\RUNTIME\recovery\PHASE_6_ERROR_RECOVERY\error\automation\DOC-ERROR-AUTOMATION-PATCH-APPLIER-338__patch_applier.py`
- `C:\Users\richg\ALL_AI\RUNTIME\recovery\PHASE_6_ERROR_RECOVERY\error\engine\DOC-ERROR-ENGINE-RECOVERY-VALIDATOR-340__recovery_validator.py`

**Error Taxonomy**:
- `C:\Users\richg\ALL_AI\GOVERNANCE\lifecycle\v2.5.3\DOC-CONFIG-ERROR-TAXONOMY-491__ERROR_TAXONOMY.json`

---

### 8. REPORTING SYSTEM

**Report Generators** (SSOT System):
- `DOC-CORE-SSOT-SYS-TOOLS-RENDER-PIPELINE-1301__render_pipeline.py`
- `DOC-CORE-SSOT-SYS-TOOLS-RENDER-FILE-TREE-1304__render_file_tree.py`
- `DOC-CORE-SSOT-SYS-TOOLS-MERGE-SCAN-OVERLAY-1303__merge_scan_overlay.py`
- `DOC-CORE-SSOT-SYS-TOOLS-SCAN-REPO-1302__scan_repo.py`

**Top-Level Renderers**:
- `C:\Users\richg\ALL_AI\render_file_tree.py`
- `C:\Users\richg\ALL_AI\merge_scan_overlay.py`

**Report Directories**:
- `C:\Users\richg\ALL_AI\reports\` (main reports)
- `C:\Users\richg\ALL_AI\RUNTIME\*/reports\` (subsystem reports)
- `C:\Users\richg\ALL_AI\MIGRATIONS\*/reports\` (migration reports)

**Key Report Files**:
- `DOC-REPORT-1359__IMPLEMENTATION_REPORT.md`
- `DOC-REPORT-1225__SECTION_F_IMPLEMENTATION_REPORT.md`
- `DOC-REPORT-1213__DOC_ID_ASSIGNMENT_COMPLETION_REPORT.md`
- `DOC-REPORT-1209__COMPLETE_MIGRATION_EXECUTION_REPORT.md`

---

### 9. SSOT CLI SYSTEM ⚠️ **NEWLY DISCOVERED**

**CLI Entry Point**:
- `C:\Users\richg\ALL_AI\ssot\__main__.py` ⚠️ **ENTRY POINT**
- `C:\Users\richg\ALL_AI\ssot\__init__.py`

**CLI Commands**:
- `C:\Users\richg\ALL_AI\ssot\cli\commands.py`
- `C:\Users\richg\ALL_AI\ssot\cli\orchestrator.py`
- `C:\Users\richg\ALL_AI\ssot\cli\config_loader.py`
- `C:\Users\richg\ALL_AI\ssot\cli\__init__.py`

**SSOT Phases** (7-phase execution pipeline):
1. `C:\Users\richg\ALL_AI\ssot\phases\phase_1_inventory.py` - Inventory collection
2. `C:\Users\richg\ALL_AI\ssot\phases\phase_2_yaml_index.py` - YAML indexing
3. `C:\Users\richg\ALL_AI\ssot\phases\phase_3_validate.py` - Validation
4. `C:\Users\richg\ALL_AI\ssot\phases\phase_4_bundle.py` - Bundling
5. `C:\Users\richg\ALL_AI\ssot\phases\phase_5_rebuild_derived.py` - Rebuild derived artifacts
6. `C:\Users\richg\ALL_AI\ssot\phases\phase_6_integrity_gates.py` - Integrity gates
7. `C:\Users\richg\ALL_AI\ssot\phases\phase_7_reports.py` - Report generation

**Documentation**:
- `C:\Users\richg\ALL_AI\ssot\DOC-GUIDE-1360__README.md`
- `C:\Users\richg\ALL_AI\ssot\DOC-REPORT-1359__IMPLEMENTATION_REPORT.md`

---

### 10. INTEGRATION & AUTOMATION

**Automation Core**:
- `C:\Users\richg\ALL_AI\GOVERNANCE\ssot\SSOT_System\DOC-CONFIG-AUTOMATION-INDEX-967__AUTOMATION.INDEX.json`
- `C:\Users\richg\ALL_AI\GOVERNANCE\ssot\SSOT_System\SSOT_SYS_tools\DOC-CORE-SSOT-SYS-TOOLS-BUILD-AUTOMATION-INDEX-514__build_automation_index.py`
- `C:\Users\richg\ALL_AI\GOVERNANCE\ssot\SSOT_System\SSOT_SYS_tools\DOC-CORE-SSOT-SYS-TOOLS-AUTOMATION-GATE-513__automation_gate.py`

**CI/CD Integration**:
- `C:\Users\richg\ALL_AI\GOVERNANCE\ssot\SSOT_System\SSOT_SYS_ci\DOC-CORE-SSOT-SYS-CI-CI-GATE-1095__ci_gate.py`
- `C:\Users\richg\ALL_AI\scripts\DOC-SCRIPT-RUN-ALL-GATES-001__run_all_gates.py`
- `C:\Users\richg\ALL_AI\scripts\DOC-SCRIPT-SCRIPTS-CI-GATE-STABLE-IDS-973__ci_gate_stable_ids.py`

**Cross-Folder Automation**:
- `C:\Users\richg\ALL_AI\GOVERNANCE\ssot\SSOT_System\SSOT_SYS_tests\DOC-TEST-CROSS-FOLDER-AUTOMATION-001__test_cross_folder_automation.py`

---

## EXECUTION ENTRY POINTS

### Primary CLI:
```powershell
python C:\Users\richg\ALL_AI\ssot\__main__.py
```

### Gate Runner:
```python
# From: C:\Users\richg\ALL_AI\GOVERNANCE\gates\gate_runner.py
```

### Validation Suite:
```powershell
# Run all validators
python C:\Users\richg\ALL_AI\scripts\DOC-SCRIPT-RUN-ALL-GATES-001__run_all_gates.py
```

### CI Gate:
```python
# From: C:\Users\richg\ALL_AI\GOVERNANCE\ssot\SSOT_System\SSOT_SYS_ci\DOC-CORE-SSOT-SYS-CI-CI-GATE-1095__ci_gate.py
```

---

## FILE COUNT BY SUBSYSTEM

1. **Work Unit Contract**: ~15 files
2. **Runner + Evidence**: ~25 files
3. **Trace + Replay**: ~20 files
4. **Registry SSOT**: ~50 files
5. **Validators**: ~150 files
6. **DAG Scheduler**: ~15 files
7. **Error Recovery**: ~40 files
8. **Reporting**: ~30 files
9. **SSOT CLI**: ~15 files
10. **Integration**: ~20 files

**Total Active Files**: ~500 files

---

## CRITICAL FILES (DO NOT DELETE)

⚠️ **NEVER DELETE THESE**:
- `gate_runner.py`
- `enforcement_bridge.py`
- `event_emitter.py`, `event_router.py`, `event_sinks.py`
- All `validate_*.py` files
- `id_registry.json` files
- `SSOT_CURRENT_APPROACH.json`
- `scheduler.py`
- `error_engine.py`
- `ssot\__main__.py`

---

## NEXT STEPS

1. ✅ **CLEANUP COMPLETE** - 481 deprecated files removed
2. ✅ **INVENTORY COMPLETE** - All subsystems mapped
3. 🔄 **READY FOR**: Solution testing and validation
4. 🔄 **READY FOR**: Pipeline execution

---

**STATUS**: ✅ **DETAILED SUBSYSTEM MAP COMPLETE**  
**CLEANUP**: ✅ **DEPRECATED FILES REMOVED**  
**SOLUTION**: ✅ **FULLY INVENTORIED AND MAPPED**
