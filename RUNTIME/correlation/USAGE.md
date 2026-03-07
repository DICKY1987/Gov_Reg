# DOC_ID: DOC-SCRIPT-1135
# Correlation Identifier Usage Guide

**Type ID:** `correlation_id`
**Classification:** runtime

---

## Quick Start

### Generating Runtime IDs

```python
from scripts.automation.correlation_id_assigner import generate_correlation_id

new_id = generate_correlation_id()
print(new_id)  # CORR-ULID
```

---

## Validation

Validate the registry:

```bash
python scripts/validators/validate_correlation_id.py
```

---

## Registry Lookup

View all assigned IDs:

```bash
cat RUNTIME/correlation/CORR_REGISTRY.yaml
```

---

## Integration

### Pre-commit Hook

Automatically validates on commit (if enabled in automation).

### CI/CD Pipeline

Add to `.github/workflows/`:

```yaml
- name: Validate Correlation Identifier
  run: python scripts/validators/validate_correlation_id.py
```

---

**Last Updated:** 2026-01-04
