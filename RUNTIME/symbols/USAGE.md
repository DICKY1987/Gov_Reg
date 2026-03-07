# DOC_ID: DOC-SCRIPT-1174
# Code Symbol Identifier Usage Guide

**Type ID:** `symbol_id`
**Classification:** derived

---

## Quick Start

### Deriving IDs

IDs are automatically derived from source data.

**Derivation Rule:** Derived from file doc_id + qualified name + signature hashes

```python
from scripts.automation.symbol_id_assigner import derive_id

source_data = {"key": "value"}
derived_id = derive_id(source_data)
```

---

## Validation

Validate the registry:

```bash
python scripts/validators/validate_symbol_id.py
```

---

## Registry Lookup

View all assigned IDs:

```bash
cat RUNTIME/symbols/SYMBOL_REGISTRY.yaml
```

---

## Integration

### Pre-commit Hook

Automatically validates on commit (if enabled in automation).

### CI/CD Pipeline

Add to `.github/workflows/`:

```yaml
- name: Validate Code Symbol Identifier
  run: python scripts/validators/validate_symbol_id.py
```

---

**Last Updated:** 2026-01-04
