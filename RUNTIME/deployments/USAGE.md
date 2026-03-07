# DOC_ID: DOC-SCRIPT-1141
# Deployment Identifier Usage Guide

**Type ID:** `deployment_id`
**Classification:** runtime

---

## Quick Start

### Generating Runtime IDs

```python
from scripts.automation.deployment_id_assigner import generate_deployment_id

new_id = generate_deployment_id()
print(new_id)  # DEPLOY-ULID
```

---

## Validation

Validate the registry:

```bash
python scripts/validators/validate_deployment_id.py
```

---

## Registry Lookup

View all assigned IDs:

```bash
cat RUNTIME/deployments/DEPLOY_REGISTRY.yaml
```

---

## Integration

### Pre-commit Hook

Automatically validates on commit (if enabled in automation).

### CI/CD Pipeline

Add to `.github/workflows/`:

```yaml
- name: Validate Deployment Identifier
  run: python scripts/validators/validate_deployment_id.py
```

---

**Last Updated:** 2026-01-04
