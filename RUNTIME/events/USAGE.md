# DOC_ID: DOC-SCRIPT-1147
# Event Identifier Usage Guide

**Type ID:** `event_id`
**Classification:** runtime

---

## Quick Start

### Generating Runtime IDs

```python
from scripts.automation.event_id_assigner import generate_event_id

new_id = generate_event_id()
print(new_id)  # EVENT-ULID
```

---

## Validation

Validate the registry:

```bash
python scripts/validators/validate_event_id.py
```

---

## Registry Lookup

View all assigned IDs:

```bash
cat RUNTIME/events/EVENT_REGISTRY.yaml
```

---

## Integration

### Pre-commit Hook

Automatically validates on commit (if enabled in automation).

### CI/CD Pipeline

Add to `.github/workflows/`:

```yaml
- name: Validate Event Identifier
  run: python scripts/validators/validate_event_id.py
```

---

**Last Updated:** 2026-01-04
