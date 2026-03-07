# DOC_ID: DOC-SCRIPT-1189
# Path Key Identifier Usage Guide

**Type ID:** `path_key`
**Classification:** derived

---

## Quick Start

### Deriving IDs

IDs are automatically derived from source data.

**Derivation Rule:** Derived from file path: hash first 8 chars of canonical path

```python
from scripts.automation.path_key_assigner import derive_id

source_data = {"key": "value"}
derived_id = derive_id(source_data)
```

---

## Validation

Validate the registry:

```bash
python scripts/validators/validate_path_key.py
```

---

## Registry Lookup

View all assigned IDs:

```bash
cat RUNTIME/path_registry/SUB_PATH_REGISTRY/path_key_registry.yaml
```

---

## Integration

### Pre-commit Hook

Automatically validates on commit (if enabled in automation).

### CI/CD Pipeline

Add to `.github/workflows/`:

```yaml
- name: Validate Path Key Identifier
  run: python scripts/validators/validate_path_key.py
```

---

**Last Updated:** 2026-01-04
