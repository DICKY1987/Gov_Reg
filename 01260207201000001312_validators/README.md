# Validators Directory

This directory contains multi-file validators that enforce structural, consistency, and policy rules across multiple root-level directories in the Gov_Reg governance and regulatory compliance system.

## Validators Overview

### 1. validate_command_spec.py (P_01260207233100000065)
**Purpose:** Validates that all gates/tools use structured command specs (no free-form strings).

**Files Validated:**
- `sections/sec_*.json` (all section files)
- `schemas/command_spec.schema.json` (schema reference)

**Validation Rules:**
- All `command` fields must be structured objects with `exe` and `args` fields
- No free-form string commands allowed
- Args must be arrays

**Usage:**
```bash
python validators/validate_command_spec.py --sections-dir sections/
```

---

### 2. validate_control_coverage.py (P_01260207233100000066)
**Purpose:** Validates that all required quality controls have complete mappings (G-CTRL-001 gate).

**Files Validated:**
- `sections/sec_021_quality_controls_catalog.json` - Quality controls catalog
- `sections/sec_012_validation_gates.json` - Validation gates definitions
- `sections/sec_011_artifact_manifest.json` - Required artifacts
- `sections/sec_016_testing_strategy.json` - Test mappings
- `policies/evidence_path_policy.json` - Evidence path policy

**Validation Rules:**
- Every control must have satisfying gates
- Evidence mappings must be deterministic
- Required artifacts must be declared
- Required tests must be mapped

**Usage:**
```bash
python validators/validate_control_coverage.py \
  --sec-021 sections/sec_021_quality_controls_catalog.json \
  --sec-012 sections/sec_012_validation_gates.json \
  --sec-011 sections/sec_011_artifact_manifest.json \
  --sec-016 sections/sec_016_testing_strategy.json \
  --evidence-policy policies/evidence_path_policy.json
```

---

### 3. validate_sec_021.py (P_01260207233100000069)
**Purpose:** Validates SEC-021 Quality Controls Catalog structure and compliance.

**Files Validated:**
- `sections/sec_021_quality_controls_catalog.json` - Main controls catalog
- `schemas/sec_021_quality_controls_catalog.schema.json` - JSON schema (optional)

**Validation Rules:**
- Control ID uniqueness
- Required fields present (id, description, type, framework_refs)
- Evidence paths follow deterministic formula
- Control mappings are valid

**Usage:**
```bash
python validators/validate_sec_021.py sections/sec_021_quality_controls_catalog.json
python validators/validate_sec_021.py sections/sec_021_quality_controls_catalog.json --schema schemas/sec_021_quality_controls_catalog.schema.json
```

---

### 4. validate_derivation.py (P_01260207233100000067)
**Purpose:** Validates data derivation specifications and column definitions.

**Files Validated:**
- `2026012816000001_COLUMN_DICTIONARY.json` (root level) - Column definitions with derivation specs

**Validation Rules:**
- LOOKUP mode requires: registry_ref, key, lookup_path_template
- Registry sources must be in sources array when referenced
- Formula-based derivations must have valid syntax
- All dependencies must be declared

**Usage:**
```bash
python validators/validate_derivation.py
```

---

### 5. validate_population_completeness.py (P_01999000042260124551)
**Purpose:** Validates population completeness and derivation dependencies.

**Files Validated:**
- `DERIVATIONS.yaml` (root level) - Data derivation rules
- `WRITE_POLICY.yaml` (root level) - Data population policies

**Validation Rules:**
- All required fields have derivation rules
- No missing derivations for required populations
- No unknown dependencies
- No circular dependencies

**Usage:**
```bash
python validators/validate_population_completeness.py \
  --derivations DERIVATIONS.yaml \
  --write-policy WRITE_POLICY.yaml
```

---

### 6. validate_classification.py
**Purpose:** Validates file classification against expected governance sections.

**Files Validated:**
- Any file specified via `--file` argument
- `01999000042260124503_governance_registry_unified.json` (root level) - Registry index
- `scripts/classify_all_files.py` - Classification module

**Validation Rules:**
- File is classified into expected section
- Classification logic matches content signals
- Registry index is consistent

**Usage:**
```bash
python validators/validate_classification.py \
  --file path/to/file \
  --expected-section "Section Name" \
  --root . \
  --registry 01999000042260124503_governance_registry_unified.json
```

---

## Wrapper Files

Several files in this directory are wrappers that import from the actual implementation:

- `P_01260207201000001014_validate_command_spec.py` → wraps P_01260207233100000065
- `P_01260207201000001015_validate_control_coverage.py` → wraps P_01260207233100000066
- `P_01260207201000001016_validate_sec_021.py` → wraps P_01260207233100000069

These exist for backward compatibility with older file ID references.

---

## Single-Folder Validators (Moved)

The following validators were moved to their target directories as they only validate files in a single folder:

- **Moved to `REGISTRY/`:**
  - `P_01999000042260124033_validate_plan_reservations.py` - Validates reservation ledger
  - `P_01999000042260124034_validate_ingest_commitments.py` - Validates commitment status

---

## Exit Codes

All validators follow standard exit code conventions:

- `0` - Validation passed
- `1` - Validation failed (errors found)
- `2` - Runtime error (file not found, invalid JSON, etc.)
- `11` - Missing file IDs (plan validators)
- `12` - Ledger errors (plan validators)

---

## Integration

These validators are typically executed as:

1. **Pre-commit hooks** - Prevent invalid commits
2. **CI/CD gates** - Block deployments on validation failure
3. **Manual checks** - During development and debugging
4. **Planning gates** - Validate before plan execution

Refer to `.git/hooks/pre-commit` and gate specifications in `sections/sec_012_validation_gates.json` for integration details.
