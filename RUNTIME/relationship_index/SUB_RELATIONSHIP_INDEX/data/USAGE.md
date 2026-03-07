# DOC_ID: DOC-SCRIPT-1194
# Relationship Edge Identifier Usage Guide

**Type ID:** `relationship_id`
**Classification:** derived

---

## Quick Start

### Deriving IDs

IDs are automatically derived from source data.

**Derivation Rule:** Derived from source ID hash + target ID hash + relationship type

```python
from scripts.automation.relationship_id_assigner import derive_id

source_data = {"key": "value"}
derived_id = derive_id(source_data)
```

---

## Validation

Validate the registry:

```bash
python scripts/validators/validate_relationship_id.py
```

---

## Registry Lookup

View all assigned IDs:

```bash
cat RUNTIME/relationship_index/SUB_RELATIONSHIP_INDEX/data/RELATIONSHIP_INDEX.json
```

---

## Integration

### Pre-commit Hook

Automatically validates on commit (if enabled in automation).

### CI/CD Pipeline

Add to `.github/workflows/`:

```yaml
- name: Validate Relationship Edge Identifier
  run: python scripts/validators/validate_relationship_id.py
```

---

**Last Updated:** 2026-01-04
