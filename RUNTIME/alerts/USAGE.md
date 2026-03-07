# DOC_ID: DOC-SCRIPT-1129
# Alert Rule Identifier Usage Guide

**Type ID:** `alert_id`
**Classification:** minted

---

## Quick Start

### Assigning a New Alert Rule Identifier

```bash
python scripts/automation/alert_id_assigner.py <entity_name> --category <category>
```

**Example:**
```bash
python scripts/automation/alert_id_assigner.py my_template --category DOC
```

### Scanning for Unassigned Entities

```bash
python scripts/automation/alert_id_scanner.py
```

---

## Validation

Validate the registry:

```bash
python scripts/validators/validate_alert_id.py
```

---

## Registry Lookup

View all assigned IDs:

```bash
cat RUNTIME/alerts/ALERT_REGISTRY.yaml
```

---

## Integration

### Pre-commit Hook

Automatically validates on commit (if enabled in automation).

### CI/CD Pipeline

Add to `.github/workflows/`:

```yaml
- name: Validate Alert Rule Identifier
  run: python scripts/validators/validate_alert_id.py
```

---

**Last Updated:** 2026-01-04
