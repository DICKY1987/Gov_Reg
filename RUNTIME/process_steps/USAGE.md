# DOC_ID: DOC-SCRIPT-1165
# Process Step Identifier Usage Guide

**Type ID:** `step_id`
**Classification:** derived

---

## Quick Start

### Deriving IDs

IDs are automatically derived from source data.

**Derivation Rule:** Derived from phase_id + step sequence number

```python
from scripts.automation.step_id_assigner import derive_id

source_data = {"key": "value"}
derived_id = derive_id(source_data)
```

---

## Validation

Validate the registry:

```bash
python scripts/validators/validate_step_id.py
```

---

## Registry Lookup

View all assigned IDs:

```bash
cat RUNTIME/process_steps/STEP_REGISTRY.yaml
```

---

## Integration

### Pre-commit Hook

Automatically validates on commit (if enabled in automation).

### CI/CD Pipeline

Add to `.github/workflows/`:

```yaml
- name: Validate Process Step Identifier
  run: python scripts/validators/validate_step_id.py
```

---

**Last Updated:** 2026-01-04
