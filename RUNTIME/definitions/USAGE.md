# DOC_ID: DOC-SCRIPT-1138
# Definition Site Identifier Usage Guide

**Type ID:** `definition_id`
**Classification:** derived

---

## Quick Start

### Deriving IDs

IDs are automatically derived from source data.

**Derivation Rule:** Derived from symbol_id + location hash

```python
from scripts.automation.definition_id_assigner import derive_id

source_data = {"key": "value"}
derived_id = derive_id(source_data)
```

---

## Validation

Validate the registry:

```bash
python scripts/validators/validate_definition_id.py
```

---

## Registry Lookup

View all assigned IDs:

```bash
cat RUNTIME/definitions/DEF_REGISTRY.yaml
```

---

## Integration

### Pre-commit Hook

Automatically validates on commit (if enabled in automation).

### CI/CD Pipeline

Add to `.github/workflows/`:

```yaml
- name: Validate Definition Site Identifier
  run: python scripts/validators/validate_definition_id.py
```

---

**Last Updated:** 2026-01-04
