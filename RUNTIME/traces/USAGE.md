# DOC_ID: DOC-SCRIPT-1177
# Trace Identifier Usage Guide

**Type ID:** `trace_id`
**Classification:** runtime

---

## Quick Start

### Generating Runtime IDs

```python
from scripts.automation.trace_id_assigner import generate_trace_id

new_id = generate_trace_id()
print(new_id)  # TRACE-ULID
```

---

## Validation

Validate the registry:

```bash
python scripts/validators/validate_trace_id.py
```

---

## Registry Lookup

View all assigned IDs:

```bash
cat RUNTIME/traces/TRACE_REGISTRY.yaml
```

---

## Integration

### Pre-commit Hook

Automatically validates on commit (if enabled in automation).

### CI/CD Pipeline

Add to `.github/workflows/`:

```yaml
- name: Validate Trace Identifier
  run: python scripts/validators/validate_trace_id.py
```

---

**Last Updated:** 2026-01-04
