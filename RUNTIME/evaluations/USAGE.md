# DOC_ID: DOC-SCRIPT-1144
# Evaluation Run Identifier Usage Guide

**Type ID:** `evaluation_id`
**Classification:** runtime

---

## Quick Start

### Generating Runtime IDs

```python
from scripts.automation.evaluation_id_assigner import generate_evaluation_id

new_id = generate_evaluation_id()
print(new_id)  # EVAL-ULID
```

---

## Validation

Validate the registry:

```bash
python scripts/validators/validate_evaluation_id.py
```

---

## Registry Lookup

View all assigned IDs:

```bash
cat RUNTIME/evaluations/EVAL_REGISTRY.yaml
```

---

## Integration

### Pre-commit Hook

Automatically validates on commit (if enabled in automation).

### CI/CD Pipeline

Add to `.github/workflows/`:

```yaml
- name: Validate Evaluation Run Identifier
  run: python scripts/validators/validate_evaluation_id.py
```

---

**Last Updated:** 2026-01-04
