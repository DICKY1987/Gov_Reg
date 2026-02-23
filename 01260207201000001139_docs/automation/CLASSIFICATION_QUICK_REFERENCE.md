# File Classification Quick Reference

A rapid lookup guide for categorizing files into sections.

## Quick Classification Table

| Section | Directory Signals | File Pattern | Extension | Key Indicator |
|---------|------------------|--------------|-----------|---------------|
| **Core Governance** | `govreg_core/`, `src/` (except `src/validators/`), `src/registry_*/`, `REGISTRY/` | `*governance_registry*.json`, `*SSOT*` | `.py`, `.json` | Registry operations, GEU logic |
| **ID Management** | - | `*ID_CANONICALITY*`, `*COUNTER_STORE*`, `*id_allocator*` | `.json`, `.py`, `.md` | ID allocation, file_id patterns |
| **Schemas** | `schemas/`, `contracts/` | `*.schema.json`, `*_contract.json` | `.json`, `.yaml` | Has `"$schema"` field |
| **Scripts** | `scripts/` | `P_*`, `run_*`, `migrate_*`, `fix_*` | `.py` | Has `if __name__ == "__main__"` |
| **Tests** | `tests/`, `test/` | `test_*.py`, `*_test.py` | `.py` | Imports `pytest`, has `test_*()` functions |
| **Validators** | `validators/`, `src/validators/` | `validate_*.py` | `.py` | Has `validate_*()` functions, validation logic |
| **Documentation** | `docs/`, `OLD_MD_*` | `README*`, `*_GUIDE*`, `*_PLAN*` | `.md`, `.txt` | Prose, no executable code |
| **Configs** | `config/`, `policies/` | `*_policy*.json`, `*_config*`, `*_map.json` | `.json`, `.yaml` | Config params, policy rules |
| **Evidence** | `evidence/`, `gates/` | `*_audit*`, `*_report.json`, `*_20260*` | `.json` | Execution results, timestamps |
| **GEU** | `GEU/` | `*geu_sets*`, `*GEU*` | `.json` | GEU definitions and mappings |
| **Path/Watcher** | `FILE WATCHER/`, `PATH_FILES/` | `*watcher*`, `*path_*` | `.py`, `.md` | File system monitoring, path resolution |
| **Planning** | `LP_LONG_PLAN/`, `sections/` | `PHASE_*`, `sec_*.json`, `*phase_*` | `.json`, `.md` | Phase definitions, execution plans |
| **State** | `.state/`, `.state_temp/` | `*decision_ledger*`, `*phase_tracking*` | `.json` | System state, flags, ledgers |
| **CI/CD** | `.github/` | `pre-commit`, `*.workflow.yml` | `.yml`, `.yaml` | GitHub Actions, hooks |
| **Backups** | `backups/`, `Archive_*/` | `*.backup`, `*_BEFORE_*` | Any | Dated copies, archived versions |
| **Templates** | `templates/` | `*_template.*`, `*.template.*` | Any | Placeholders like `{{VAR}}` |
| **Monitoring** | `monitoring/`, `training/` | `*alert*`, `*monitor*`, `*event_*` | `.py`, `.md` | Metrics, alerts, training |
| **Patches** | `PATCHES/`, `.migration/` | `*.patch.json`, `transition_*` | `.json`, `.yaml` | Data transformations, migrations |
| **Deployment** | Root | `DEPLOYMENT_*`, `CRITICAL_FIXES*`, `FINAL_STATUS*` | `.md` | Operational checklists, summaries |

---

## Fast Decision Tree

```
START
  |
  ├─ In specific directory? (tests/, schemas/, validators/)
  |     YES → Use directory mapping
  |     NO → Continue
  |
  ├─ File extension?
  |     .schema.json → Schemas
  |     .patch.json → Patches
  |     test_*.py → Tests
  |     validate_*.py → Validators
  |     P_*.py with __main__ → Scripts
  |     *.md → Documentation
  |
  ├─ File name pattern?
  |     *ID_CANONICALITY* → ID Management
  |     *governance_registry* → Core Governance
  |     *_audit*, *_report → Evidence
  |     *phase*, sec_* → Planning
  |     *.backup → Backups
  |
  ├─ Check first 20 lines:
  |     Has "$schema" → Schemas
  |     Imports pytest → Tests
  |     Has validate_* functions → Validators
  |     Has if __name__ == "__main__" → Scripts
  |     All prose text → Documentation
  |
  └─ Check registry metadata (layer, artifact_kind, geu_role)
```

---

## Registry Metadata Quick Lookup

### Layer → Section Mapping
```
CI_CD → CI/CD & Integration
DOCUMENTATION → Documentation
CORE → Core Governance
TESTING → Tests
VALIDATION → Validators
GOVERNANCE → Configs & Policies
MONITORING → Monitoring
PLANNING → Planning & Execution
EVIDENCE → Evidence & Gates
```

### artifact_kind → Section Mapping
```
SCHEMA → Schemas
TEST → Tests
VALIDATOR → Validators
PYTHON_MODULE → (Check context: Core/Scripts/Tests)
MARKDOWN → Documentation
JSON → (Check context: Schemas/Configs/Evidence)
YAML → Configs or CI/CD
EVIDENCE → Evidence
REPORT → Evidence
```

### geu_role → Section Mapping
```
SCHEMA → Schemas
RULE → Configs & Policies
VALIDATOR → Validators
RUNNER → Scripts
TEST → Tests
EVIDENCE → Evidence
REPORT → Evidence
SHARED_LIB → Core Governance
```

---

## Common Ambiguities

| File Type | Disambiguation Rule | Example |
|-----------|---------------------|---------|
| `.py` file | Has `test_*` functions? → Test<br>Has `validate_*` functions? → Validator<br>Has `if __name__` and in `scripts/`? → Script<br>In `govreg_core/` or `src/`? → Core | `test_id_allocator.py` → Test<br>`validate_schema.py` → Validator<br>`migrate_geu.py` → Script |
| `.json` file | Has `$schema` at root? → Schema<br>Has `generated_at` + metrics? → Evidence<br>Has `version` + `policies`? → Config<br>Is registry file? → Core | `column_dict.schema.json` → Schema<br>`audit_report.json` → Evidence<br>`null_policy_map.json` → Config |
| `.md` file | Contains code + docs? → Documentation<br>In root with checklist? → Deployment<br>Describes architecture? → Documentation | `DEPLOYMENT_CHECKLIST.md` → Deployment<br>`ARCHITECTURE.md` → Documentation |
| File with `ID_*` | About ID system itself? → ID Management<br>Just has an ID in filename? → (Original section) | `ID_CANONICALITY_PLAN.md` → ID Management<br>`01260207*.json` → (Check other traits) |

---

## Pattern Matching Regex

```python
# Quick classification patterns
PATTERNS = {
    'schemas': r'\.(schema\.json|contract\.json)$',
    'tests': r'(^test_|_test\.py$|conftest\.py$)',
    'validators': r'(^validate_|validator\.py$)',
    'scripts': r'^P_\d{20}_.*\.py$',
    'evidence': r'(_audit\.|_report\.json|_\d{8}_)',
    'backups': r'(\.backup|_BEFORE_|/backups/|/Archive_)',
    'id_management': r'(ID_CANONICALITY|ID_ALLOCATOR|COUNTER_STORE)',
    'planning': r'(PHASE_|sec_\d{3}_|phase_contract)',
    'deployment': r'(DEPLOYMENT_|CRITICAL_FIXES|FINAL_STATUS)',
}
```

---

## Classification Confidence Levels

- **HIGH**: File in specific directory (e.g., `tests/test_*.py`)
- **MEDIUM**: Clear naming pattern (e.g., `*.schema.json`)
- **LOW**: Ambiguous name, requires content inspection
- **REGISTRY**: Use metadata from unified registry (ground truth)

**Always prefer registry metadata when available.**

---

## Verification Checklist

When classifying a file, verify:
- [ ] Checked directory location
- [ ] Matched file name pattern
- [ ] Examined file extension
- [ ] Inspected first 20-30 lines (for code files)
- [ ] Checked JSON root structure (for JSON files)
- [ ] Consulted registry metadata (if available)
- [ ] Resolved ambiguities using decision tree
- [ ] Confirmed with at least 2 trait matches

---

**Document Version**: 1.0
**Last Updated**: 2026-02-13
**Companion to**: FILE_CLASSIFICATION_CRITERIA.md
