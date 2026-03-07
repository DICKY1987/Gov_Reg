# DOC_ID: DOC-SCRIPT-1171
# Run Identifier Usage Guide

**Type ID:** `run_id`
**Classification:** runtime

---

## Quick Start

### Generating Runtime IDs

```python
from scripts.automation.run_id_assigner import generate_run_id

new_id = generate_run_id()
print(new_id)  # RUN-ULID
```

---

## Validation

Validate the registry:

```bash
python scripts/validators/validate_run_id.py
```

---

## Registry Lookup

View all assigned IDs:

```bash
cat RUNTIME/runs/RUN_REGISTRY.yaml
```

---

## Integration

### Pre-commit Hook

Automatically validates on commit (if enabled in automation).

### CI/CD Pipeline

Add to `.github/workflows/`:

```yaml
- name: Validate Run Identifier
  run: python scripts/validators/validate_run_id.py
```

---

**Last Updated:** 2026-01-04
