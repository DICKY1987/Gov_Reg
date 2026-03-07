# DOC_ID: DOC-SCRIPT-1162
# Pipeline Instance Identifier Usage Guide

**Type ID:** `pipeline_id`
**Classification:** runtime

---

## Quick Start

### Generating Runtime IDs

```python
from scripts.automation.pipeline_id_assigner import generate_pipeline_id

new_id = generate_pipeline_id()
print(new_id)  # PIPELINE-ULID
```

---

## Validation

Validate the registry:

```bash
python scripts/validators/validate_pipeline_id.py
```

---

## Registry Lookup

View all assigned IDs:

```bash
cat RUNTIME/pipelines/PIPELINE_REGISTRY.yaml
```

---

## Integration

### Pre-commit Hook

Automatically validates on commit (if enabled in automation).

### CI/CD Pipeline

Add to `.github/workflows/`:

```yaml
- name: Validate Pipeline Instance Identifier
  run: python scripts/validators/validate_pipeline_id.py
```

---

**Last Updated:** 2026-01-04
