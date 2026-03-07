# DOC_ID: DOC-SCRIPT-1159
# Outcome Identifier Usage Guide

**Type ID:** `outcome_id`
**Classification:** derived

---

## Quick Start

### Deriving IDs

IDs are automatically derived from source data.

**Derivation Rule:** Derived from step_id + outcome type hash

```python
from scripts.automation.outcome_id_assigner import derive_id

source_data = {"key": "value"}
derived_id = derive_id(source_data)
```

---

## Validation

Validate the registry:

```bash
python scripts/validators/validate_outcome_id.py
```

---

## Registry Lookup

View all assigned IDs:

```bash
cat RUNTIME/outcomes/OUTCOME_REGISTRY.yaml
```

---

## Integration

### Pre-commit Hook

Automatically validates on commit (if enabled in automation).

### CI/CD Pipeline

Add to `.github/workflows/`:

```yaml
- name: Validate Outcome Identifier
  run: python scripts/validators/validate_outcome_id.py
```

---

**Last Updated:** 2026-01-04
