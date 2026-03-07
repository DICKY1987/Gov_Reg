# Registry Automation Script Index

**Total Scripts:** 18  
**Last Updated:** 2026-03-06 18:57:20

---

## Phase 0: Pre-Flight Stabilization (1 script)

### P_01999000042260305000_enum_drift_gate.py
**Purpose:** Validates and normalizes enum values in registry  
**Input:** REGISTRY_file.json  
**Output:** REGISTRY_ENUMS_CANON.json, normalized registry  
**Usage:** `python P_01999000042260305000_enum_drift_gate.py [--fix]`  
**Lines:** ~381

---

## Week 1: Tactical Wins (4 scripts)

### P_01999000042260305001_file_id_reconciler.py
**Purpose:** Builds file_id ↔ sha256 bidirectional mappings  
**Input:** REGISTRY_file.json  
**Output:** SHA256_TO_FILE_ID.json  
**Usage:** `python P_01999000042260305001_file_id_reconciler.py`  
**Lines:** ~186

### P_01999000042260305002_phase_a_transformer.py
**Purpose:** Transforms Phase A analyzer output to registry schema  
**Input:** analysis.json  
**Output:** transformed.json  
**Usage:** `python P_01999000042260305002_phase_a_transformer.py --input IN --output OUT`  
**Lines:** ~214

### P_01999000042260305003_run_metadata_collector.py
**Purpose:** Tracks analysis run metadata for audit trail  
**Input:** Run commands (start/script/finish)  
**Output:** ANALYSIS_RUNS.json, RUN_{id}.json  
**Usage:** `python P_01999000042260305003_run_metadata_collector.py --run-id ID --action ACTION`  
**Lines:** ~224

### P_01999000042260305004_patch_generator.py
**Purpose:** Generates and applies RFC-6902 JSON Patches  
**Input:** Analysis results, existing registry  
**Output:** registry_patches.json, patched registry  
**Usage:** `python P_01999000042260305004_patch_generator.py --mode {generate|validate|apply}`  
**Lines:** ~317

---

## Week 2 Track A: Column Runtime Engine (7 scripts)

### P_01999000042260305005_column_loader.py
**Purpose:** Runtime loader for COLUMN_DICTIONARY definitions  
**Input:** COLUMN_DICTIONARY.json  
**Output:** In-memory column metadata  
**Usage:** `python P_01999000042260305005_column_loader.py --list-phases`  
**Lines:** ~266

### P_01999000042260305006_column_validator.py
**Purpose:** Validates column types and constraints  
**Input:** file_record.json  
**Output:** Validation report  
**Usage:** `python P_01999000042260305006_column_validator.py --record-json FILE`  
**Lines:** ~57

### P_01999000042260305007_default_injector.py
**Purpose:** Injects default values for missing columns  
**Input:** record.json  
**Output:** record_with_defaults.json  
**Usage:** `python P_01999000042260305007_default_injector.py --input IN --output OUT`  
**Lines:** ~45

### P_01999000042260305008_null_coalescer.py
**Purpose:** Replaces NULL values with defaults  
**Input:** record.json  
**Output:** coalesced.json  
**Usage:** `python P_01999000042260305008_null_coalescer.py --input IN --output OUT`  
**Lines:** ~46

### P_01999000042260305009_phase_selector.py
**Purpose:** Extracts phase-specific columns  
**Input:** record.json, phase name  
**Output:** phase_subset.json  
**Usage:** `python P_01999000042260305009_phase_selector.py --input IN --phase PHASE_A --output OUT`  
**Lines:** ~53

### P_01999000042260305010_missing_reporter.py
**Purpose:** Generates missing column coverage report  
**Input:** REGISTRY_file.json  
**Output:** missing_columns_report.json  
**Usage:** `python P_01999000042260305010_missing_reporter.py --registry REG --output OUT`  
**Lines:** ~70

### P_01999000042260305011_column_introspector.py
**Purpose:** Analyzes actual column usage patterns  
**Input:** REGISTRY_file.json  
**Output:** introspection_report.json  
**Usage:** `python P_01999000042260305011_column_introspector.py --registry REG --output OUT`  
**Lines:** ~85

---

## Week 2 Track B: Entity Canonicalization (2 scripts)

### P_01999000042260305012_doc_id_resolver.py
**Purpose:** Resolves doc_id collisions and ambiguities  
**Input:** REGISTRY_file.json  
**Output:** DOC_ID_RESOLUTION.json  
**Usage:** `python P_01999000042260305012_doc_id_resolver.py`  
**Lines:** ~162

### P_01999000042260305013_module_dedup.py
**Purpose:** Deduplicates Python module names  
**Input:** REGISTRY_file.json  
**Output:** MODULE_NAME_RESOLUTION.json  
**Usage:** `python P_01999000042260305013_module_dedup.py`  
**Lines:** ~174

---

## Week 3: Pipeline Integration (4 scripts)

### P_01999000042260305014_intake_orchestrator.py
**Purpose:** Orchestrates Phase A/B/C analyzers for single file  
**Input:** Python file  
**Output:** unified_analysis.json  
**Usage:** `python P_01999000042260305014_intake_orchestrator.py --file FILE --output OUT`  
**Lines:** ~199

### P_01999000042260305015_timestamp_clusterer.py
**Purpose:** Groups files by timestamp proximity  
**Input:** REGISTRY_file.json  
**Output:** cluster_report.json  
**Usage:** `python P_01999000042260305015_timestamp_clusterer.py --registry REG --output OUT --window 300`  
**Lines:** ~61

### P_01999000042260305016_e2e_validator.py
**Purpose:** End-to-end registry validation  
**Input:** REGISTRY_file.json  
**Output:** Validation pass/fail report  
**Usage:** `python P_01999000042260305016_e2e_validator.py --registry REG`  
**Lines:** ~70

### P_01999000042260305017_pipeline_runner.py
**Purpose:** Complete pipeline for batch file processing  
**Input:** Directory of files  
**Output:** pipeline_results_{run_id}.json  
**Usage:** `python P_01999000042260305017_pipeline_runner.py --input-dir DIR --output-dir OUT`  
**Lines:** ~128

---

## Summary Statistics

| Category | Scripts | Total Lines | Avg Lines/Script |
|----------|---------|-------------|------------------|
| Phase 0 | 1 | 381 | 381 |
| Week 1 | 4 | 941 | 235 |
| Week 2A | 7 | 622 | 89 |
| Week 2B | 2 | 336 | 168 |
| Week 3 | 4 | 458 | 115 |
| **Total** | **18** | **~2,738** | **~152** |

---

## Quick Reference: Common Tasks

### Task 1: Fix Enum Drift
```bash
python P_01999000042260305000_enum_drift_gate.py --fix
```

### Task 2: Validate Registry
```bash
python P_01999000042260305016_e2e_validator.py --registry ../../01999000042260124503_REGISTRY_file.json
```

### Task 3: Analyze Directory
```bash
python P_01999000042260305017_pipeline_runner.py --input-dir src/ --output-dir results/
```

### Task 4: Check Missing Columns
```bash
python P_01999000042260305010_missing_reporter.py --registry ../../01999000042260124503_REGISTRY_file.json --output missing.json
```

---

**Generated:** 2026-03-06 18:57:20
