# DOC-INTEGRATION-MAPP-PY-REGISTRY-001
# mapp_py ↔ Gov_Reg REGISTRY Integration Specification

**Work ID**: WORK-MAPP-PY-001
**Created**: 2026-02-02
**Status**: PLANNED

---

## Purpose

Define how **mapp_py Python introspection outputs** integrate with the **Gov_Reg Unified SSOT Registry** (148-column system) to enrich Python file records with deterministic analysis evidence.

---

## System Overview

### Gov_Reg Registry System

**Location**: `C:\Users\richg\Gov_Reg\REGISTRY`

**Core Components**:
- **Unified SSOT**: `01999000042260124503_governance_registry_unified.json` (148 columns)
- **Column Dictionary**: `2026012816000001_COLUMN_DICTIONARY.json` (147 headers with 6-field definitions)
- **Schema**: `01999000042260124012_governance_registry_schema.v3.json` (428 properties)
- **Derivation Formulas**: `UNIFIED_SSOT_REGISTRY_DERIVATIONS.yaml` (30+ safe DSL functions)
- **Write Policy**: `UNIFIED_SSOT_REGISTRY_WRITE_POLICY.yaml`

**Current Python File Support**:
- `artifact_kind: PYTHON_MODULE` classification exists
- Basic file identity (file_id, relative_path, sha256, size_bytes)
- Governance metadata (layer, governance_domain, bundle_id, geu_role)
- Relationship tracking (depends_on_file_ids, test_file_ids, enforced_by_file_ids)

**Gap**: No Python-specific introspection data (AST, components, capabilities, similarity).

---

## Integration Architecture

### Flow: mapp_py → Registry

```
Python File (on disk)
  ↓
[mapp_py Pipeline - Stages S0-S6]
  ↓
Analysis Evidence JSON (per-file + per-comparison)
  ↓
[Registry Ingest Process]
  ↓
Unified SSOT Registry (enriched Python columns)
  ↓
[Rule Evaluation via DOC-CONFIG-PY-IDENTIFY-SOLUTION-001]
  ↓
Decisions: ACTIVE | OBSOLETE_CANDIDATE | DUPLICATE_SET_CANDIDATE
```

---

## New Registry Columns for Python Files

### Required Column Extensions (37 new headers)

These extend the existing 148-column registry to support Python introspection:

#### **Category 1: Python Identity & Analysis Metadata** (6 columns)

```yaml
py_analysis_run_id:
  type: string
  description: "Unique ID for mapp_py analysis execution"
  derivation_mode: EXTRACTED
  presence: CONDITIONAL  # Required for artifact_kind=PYTHON_MODULE

py_analyzed_at_utc:
  type: string
  format: date-time
  description: "When mapp_py last analyzed this file"
  derivation_mode: SYSTEM

py_toolchain_id:
  type: string
  description: "Stable identifier for analyzer toolset version"
  derivation_mode: EXTRACTED

py_tool_versions:
  type: object
  description: "Python version, parser version, analyzer versions"
  derivation_mode: EXTRACTED

py_canonical_text_hash:
  type: string
  pattern: "^[0-9a-fA-F]{64}$"
  description: "SHA256 after normalization (encoding/newlines/formatting)"
  derivation_mode: DERIVED

py_analysis_success:
  type: boolean
  description: "Whether mapp_py analysis completed successfully"
  derivation_mode: EXTRACTED
```

#### **Category 2: AST & Component Fingerprints** (8 columns)

```yaml
py_ast_dump_hash:
  type: string
  pattern: "^[0-9a-fA-F]{64}$"
  description: "Deterministic hash of normalized AST structure"
  derivation_mode: DERIVED

py_ast_parse_ok:
  type: boolean
  description: "Whether Python AST parsing succeeded"
  derivation_mode: EXTRACTED

py_defs_functions_count:
  type: integer
  minimum: 0
  description: "Number of function definitions"
  derivation_mode: EXTRACTED

py_defs_classes_count:
  type: integer
  minimum: 0
  description: "Number of class definitions"
  derivation_mode: EXTRACTED

py_defs_public_api_hash:
  type: string
  pattern: "^[0-9a-fA-F]{64}$"
  description: "Hash of exported public API surface"
  derivation_mode: DERIVED

py_component_count:
  type: integer
  minimum: 0
  description: "Total extracted components (functions + classes + methods)"
  derivation_mode: EXTRACTED

py_component_ids:
  type: array
  items:
    type: string
    pattern: "^COMP-[0-9a-f]{12}$"
  description: "List of stable component IDs"
  derivation_mode: EXTRACTED

py_component_artifact_path:
  type: string
  description: "Path to detailed component extraction JSON"
  derivation_mode: SYSTEM
```

#### **Category 3: Deliverables & Capabilities** (9 columns)

```yaml
py_deliverable_kinds:
  type: array
  items:
    type: string
    enum: ["cli_tool", "library_module", "daemon", "migration_script",
           "validator", "test_suite", "data_transformer", "api_server"]
  description: "What this script delivers"
  derivation_mode: EXTRACTED

py_deliverable_signature_hash:
  type: string
  pattern: "^[0-9a-fA-F]{64}$"
  description: "Deterministic hash of deliverable fingerprint (enables duplicate clustering)"
  derivation_mode: DERIVED

py_deliverable_inputs:
  type: array
  items: string
  description: "CLI args, env vars, config keys, input file patterns"
  derivation_mode: EXTRACTED

py_deliverable_outputs:
  type: array
  items: string
  description: "Files produced, registries updated, reports emitted"
  derivation_mode: EXTRACTED

py_deliverable_interfaces:
  type: array
  items: string
  description: "CLI commands, public functions/classes, exported API symbols"
  derivation_mode: EXTRACTED

py_capability_tags:
  type: array
  items: string
  description: "Controlled vocabulary capability tags (registry_update, path_resolve, schema_validate, etc.)"
  derivation_mode: EXTRACTED

py_capability_facts_hash:
  type: string
  pattern: "^[0-9a-fA-F]{64}$"
  description: "Hash of structured capability facts (imports/calls/IO/exceptions)"
  derivation_mode: DERIVED

py_io_surface_flags:
  type: object
  properties:
    file_read: {type: boolean}
    file_write: {type: boolean}
    network: {type: boolean}
    subprocess: {type: boolean}
    env_read: {type: boolean}
    db_access: {type: boolean}
  description: "Boolean flags for I/O surface detection"
  derivation_mode: EXTRACTED

py_security_risk_flags:
  type: array
  items:
    type: string
    enum: ["uses_eval", "shell_injection_risk", "network_access",
           "subprocess_calls", "env_manipulation", "file_system_write"]
  description: "Security-relevant patterns detected"
  derivation_mode: EXTRACTED
```

#### **Category 4: Dependencies & Imports** (4 columns)

```yaml
py_imports_stdlib:
  type: array
  items: string
  description: "Standard library imports"
  derivation_mode: EXTRACTED

py_imports_third_party:
  type: array
  items: string
  description: "Third-party package imports"
  derivation_mode: EXTRACTED

py_imports_local:
  type: array
  items: string
  description: "Local/relative module imports"
  derivation_mode: EXTRACTED

py_imports_hash:
  type: string
  pattern: "^[0-9a-fA-F]{64}$"
  description: "Deterministic hash of import set"
  derivation_mode: DERIVED
```

#### **Category 5: Quality & Test Metrics** (6 columns)

```yaml
py_quality_score:
  type: integer
  minimum: 0
  maximum: 100
  description: "Composite quality score (tests + lint + complexity + docs)"
  derivation_mode: DERIVED

py_tests_executed:
  type: boolean
  description: "Whether pytest was executed for this file"
  derivation_mode: EXTRACTED

py_pytest_exit_code:
  type: integer
  description: "Pytest exit code (0=pass)"
  derivation_mode: EXTRACTED

py_coverage_percent:
  type: number
  minimum: 0.0
  maximum: 100.0
  description: "Test coverage percentage"
  derivation_mode: EXTRACTED

py_static_issues_count:
  type: integer
  minimum: 0
  description: "Count of linter/type-checker issues (ruff/mypy)"
  derivation_mode: EXTRACTED

py_complexity_cyclomatic:
  type: integer
  minimum: 1
  description: "Cyclomatic complexity metric"
  derivation_mode: EXTRACTED
```

#### **Category 6: Overlap & Canonicality** (4 columns)

```yaml
py_overlap_group_id:
  type: string
  description: "Cluster ID for duplicate/similar files (derived from deliverable_signature_hash)"
  derivation_mode: DERIVED

py_overlap_similarity_max:
  type: number
  minimum: 0.0
  maximum: 1.0
  description: "Maximum similarity score to any other Python file in registry"
  derivation_mode: DERIVED

py_overlap_best_match_file_id:
  type: string
  pattern: "^[0-9]{20}$"
  description: "file_id of most similar Python file"
  derivation_mode: DERIVED

py_canonical_candidate_score:
  type: number
  minimum: 0.0
  maximum: 100.0
  description: "Canonical preference ranking score within overlap group"
  derivation_mode: DERIVED
```

---

## Column Dictionary Integration

Each new column MUST be added to `2026012816000001_COLUMN_DICTIONARY.json` with:

1. **value_schema** - Type + constraints
2. **scope** - `record_kinds_in: ["entity"]`, `entity_kinds_in: ["file"]`
3. **presence** - Policy (REQUIRED for PYTHON_MODULE, OPTIONAL for others)
4. **normalization** - Transforms (if any)
5. **provenance** - Source doc_id references
6. **derivation** - How the value is populated:

Example for `py_deliverable_signature_hash`:

```json
{
  "py_deliverable_signature_hash": {
    "value_schema": {
      "type": "string",
      "pattern": "^[0-9a-fA-F]{64}$"
    },
    "scope": {
      "record_kinds_in": ["entity"],
      "entity_kinds_in": ["file"]
    },
    "presence": {
      "policy": "CONDITIONAL",
      "rules": [{
        "rule_id": "PY_001",
        "when": "artifact_kind == 'PYTHON_MODULE' AND py_analysis_success == true",
        "must": "value != null"
      }]
    },
    "normalization": {
      "transforms": []
    },
    "provenance": {
      "sources": [{
        "doc_id": "DOC-DESIGN-MAPP-PY-SYSTEM-001",
        "path": "mapp_py/DOC-DESIGN-MAPP-PY-SYSTEM-001__Technical_Design.json",
        "anchor": "deliverable_signature_hash"
      }]
    },
    "derivation": {
      "mode": "DERIVED",
      "sources": [
        {"kind": "COLUMN", "ref": "py_deliverable_kinds"},
        {"kind": "COLUMN", "ref": "py_deliverable_inputs"},
        {"kind": "COLUMN", "ref": "py_deliverable_outputs"},
        {"kind": "COLUMN", "ref": "py_io_surface_flags"}
      ],
      "process": {
        "engine": "FORMULA_AST",
        "spec": {
          "op": "HASH_STABLE",
          "args": [
            {"op": "col", "name": "py_deliverable_kinds"},
            {"op": "col", "name": "py_deliverable_inputs"},
            {"op": "col", "name": "py_deliverable_outputs"},
            {"op": "col", "name": "py_io_surface_flags"}
          ]
        }
      },
      "null_policy": "ALLOW_NULL",
      "error_policy": "WARN",
      "evidence": {
        "evidence_keys": ["py_analysis_run_id"],
        "artifacts": ["py_component_artifact_path"]
      }
    }
  }
}
```

---

## Ingest Process

### Phase 1: Analysis Execution

```bash
cd C:\Users\richg\ALL_AI\mapp_py

# Analyze single file
python -m mapp_py.cli analyze \
  --file-id 00199900004226012484 \
  --file-path "src/P_01999000042260124484_geu_governance/validation.py" \
  --output .runs/{run_id}/analysis_00199900004226012484.json

# Analyze all PYTHON_MODULE files in registry
python -m mapp_py.cli analyze-registry \
  --registry C:\Users\richg\Gov_Reg\REGISTRY\01999000042260124503_governance_registry_unified.json \
  --filter "artifact_kind=PYTHON_MODULE" \
  --output .runs/{run_id}/
```

### Phase 2: Registry Update

```bash
cd C:\Users\richg\Gov_Reg\REGISTRY

# Ingest mapp_py analysis outputs into registry
python scripts/ingest_mapp_py_analysis.py \
  --analysis-dir C:\Users\richg\ALL_AI\mapp_py\.runs\{run_id}\ \
  --registry 01999000042260124503_governance_registry_unified.json \
  --dry-run  # Validate before commit

# Actual ingest (atomic write with backup)
python scripts/ingest_mapp_py_analysis.py \
  --analysis-dir C:\Users\richg\ALL_AI\mapp_py\.runs\{run_id}\ \
  --registry 01999000042260124503_governance_registry_unified.json \
  --commit
```

### Phase 3: Derivation Computation

Registry derivation engine automatically computes:

- `py_deliverable_signature_hash` from deliverable facts
- `py_overlap_group_id` by clustering similar signatures
- `py_canonical_candidate_score` within overlap groups

Via formulas in `UNIFIED_SSOT_REGISTRY_DERIVATIONS.yaml`:

```yaml
py_overlap_group_id:
  depends_on:
    - py_deliverable_signature_hash
    - py_capability_facts_hash
  formula: >
    CLUSTER_BY_SIMILARITY(
      py_deliverable_signature_hash,
      py_capability_facts_hash,
      threshold=0.85
    )
  trigger: recompute_on_analysis_update
```

---

## Rule Integration

### Redundancy Detection Rules

From `DOC-CONFIG-PY-IDENTIFY-SOLUTION-001__MAPP_py_identify_soultion.yml`:

```yaml
- rule_id: R_RED_001
  decision: DUPLICATE_SET_CANDIDATE
  requires_all:
    - py_overlap_similarity_max >= 0.92
    - py_ast_dump_hash != null
    - py_deliverable_signature_hash: matches_another_file

- rule_id: R_RED_002
  decision: CANONICAL_PREFERENCE
  type: ranking
  formula: weighted_sum
  weights:
    py_quality_score: 0.30
    py_coverage_percent: 0.20
    has_tests: 0.15
    py_static_issues_count: -0.10  # Negative weight
    py_security_risk_flags: -0.05  # Fewer risks = better
    last_modified_at: 0.10
  disqualifiers:
    - py_ast_parse_ok == false
    - py_static_issues_count > 50
```

### Active Determination Rules

```yaml
- rule_id: R_ACTIVE_007
  decision: ACTIVE
  type: hard_stop
  requires_any:
    - py_deliverable_kinds contains "entrypoint"
    - py_capability_tags contains "cli_tool"
    - entrypoint_flag: true  # Existing registry field

- rule_id: R_ACTIVE_008
  decision: ACTIVE_LIBRARY
  type: classification
  requires_all:
    - py_deliverable_kinds contains "library_module"
    - py_defs_public_api_hash != null
    - depends_on_by_count > 0  # Other files import this
```

---

## Evidence Schema Alignment

mapp_py outputs MUST conform to `EVIDENCE_SCHEMA_EXTENSIONS.yaml`:

```yaml
evidence:
  python_similarity:
    structural:
      score: 0.94
      confidence: 0.92
      method: "ast_diff"
    semantic:
      score: 0.88
      confidence: 0.85
      method: "tfidf"

  python_components:
    function_count: 12
    class_count: 3
    stable_component_ids: ["COMP-a3f2b1c4d5e6", "COMP-7f8e9a0b1c2d"]

  python_io_surface:
    cli_args:
      uses_argparse: true
      argument_names: ["--registry", "--dry-run", "--commit"]
    env_vars:
      detected: ["PATH", "PYTHONPATH", "GOV_REG_ROOT"]
    surface_overlap:
      jaccard_index: 0.75
```

These evidence paths map directly to registry columns via the ingest script.

---

## Schema Updates Required

### 1. Extend `01999000042260124012_governance_registry_schema.v3.json`

Add 37 new property definitions under `definitions.FileRecord.properties`:

```json
{
  "py_deliverable_signature_hash": {
    "type": ["string", "null"],
    "pattern": "^[0-9a-fA-F]{64}$",
    "description": "Deterministic hash of Python deliverable fingerprint"
  },
  // ... (36 more)
}
```

### 2. Update `2026012816000001_COLUMN_DICTIONARY.json`

- Increment `header_count_expected` from 147 to 184
- Add 37 header definitions with 6-field structure
- Update `header_order` array

### 3. Update `UNIFIED_SSOT_REGISTRY_DERIVATIONS.yaml`

Add derivation formulas for computed fields:

```yaml
py_canonical_candidate_score:
  depends_on:
    - py_quality_score
    - py_coverage_percent
    - has_tests
    - py_static_issues_count
  formula: >
    (py_quality_score * 0.30) +
    (py_coverage_percent * 0.20) +
    (IF(has_tests, 15, 0)) -
    (py_static_issues_count * 0.10)
  trigger: recompute_on_analysis_update
```

---

## Validation Gates

### Gate: PY_ANALYSIS_COMPLETENESS

```python
# validators/validate_py_analysis_completeness.py

def validate_py_columns(registry):
    """Ensure all PYTHON_MODULE files have required py_* columns populated."""
    errors = []

    for file in registry["files"]:
        if file["artifact_kind"] != "PYTHON_MODULE":
            continue

        required = [
            "py_analysis_run_id",
            "py_canonical_text_hash",
            "py_ast_parse_ok",
            "py_deliverable_kinds",
        ]

        for col in required:
            if file.get(col) is None:
                errors.append(f"{file['file_id']}: Missing {col}")

    return {"passed": len(errors) == 0, "errors": errors}
```

### Gate: PY_OVERLAP_CONSISTENCY

```python
def validate_overlap_consistency(registry):
    """Ensure overlap_group_id clustering is consistent."""

    groups = {}
    for file in registry["files"]:
        if not file.get("py_overlap_group_id"):
            continue

        gid = file["py_overlap_group_id"]
        sig = file["py_deliverable_signature_hash"]

        if gid not in groups:
            groups[gid] = []
        groups[gid].append(sig)

    # All files in same group should have similar signatures
    errors = []
    for gid, sigs in groups.items():
        if len(set(sigs)) > 1:  # Simplified check
            errors.append(f"Group {gid} has inconsistent signatures")

    return {"passed": len(errors) == 0, "errors": errors}
```

---

## Implementation Phases

### Phase 0: Column Definition (Week 1)
- [ ] Add 37 column definitions to Column Dictionary
- [ ] Update schema with new properties
- [ ] Add derivation formulas to DERIVATIONS.yaml
- [ ] Create validation gates

### Phase 1: Single-File Analysis (Week 2)
- [ ] Implement `mapp_py.cli analyze` command
- [ ] Generate analysis JSON matching evidence schema
- [ ] Test with 5 sample Python files from Gov_Reg

### Phase 2: Registry Ingest (Week 3)
- [ ] Implement `scripts/ingest_mapp_py_analysis.py`
- [ ] Atomic write protocol with backups
- [ ] Test ingest with dry-run mode

### Phase 3: Batch Analysis (Week 4)
- [ ] Implement `mapp_py.cli analyze-registry` command
- [ ] Parallel processing for 100+ Python files
- [ ] Progress tracking and error recovery

### Phase 4: Derivation & Rules (Week 5)
- [ ] Deploy derivation formulas to registry
- [ ] Test overlap clustering
- [ ] Integrate with rule evaluation system

### Phase 5: Validation & Gates (Week 6)
- [ ] Implement PY_ANALYSIS_COMPLETENESS gate
- [ ] Implement PY_OVERLAP_CONSISTENCY gate
- [ ] Add gates to CI pipeline

---

## Success Criteria

1. **All PYTHON_MODULE files enriched**: 100% of Python files in registry have py_* columns populated
2. **Duplicate detection working**: Files with `py_overlap_similarity_max > 0.90` correctly clustered
3. **Canonical selection deterministic**: Same inputs → same canonical_candidate_score
4. **Gates passing**: PY_ANALYSIS_COMPLETENESS and PY_OVERLAP_CONSISTENCY return exit code 0
5. **Rule evaluation enabled**: R_RED_001 and R_RED_002 execute successfully on enriched registry

---

## References

- **mapp_py Technical Design**: `DOC-DESIGN-MAPP-PY-SYSTEM-001__Technical_Design.json`
- **Gov_Reg CLAUDE.md**: `C:\Users\richg\Gov_Reg\REGISTRY\CLAUDE.md`
- **Column Dictionary**: `C:\Users\richg\Gov_Reg\REGISTRY\2026012816000001_COLUMN_DICTIONARY.json`
- **ChatGPT Header Discussion**: `ChatGPT-Header Definition Structure.json`
- **Evidence Schema**: `EVIDENCE_SCHEMA_EXTENSIONS.yaml`
- **Rule Config**: `DOC-CONFIG-PY-IDENTIFY-SOLUTION-001__MAPP_py_identify_soultion.yml`

---

**Next Step**: Review and approve this integration spec, then proceed with Phase 0 (Column Definition).
