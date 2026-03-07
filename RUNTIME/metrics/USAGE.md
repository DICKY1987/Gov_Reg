# DOC_ID: DOC-SCRIPT-1156
# Metric Identifier Usage Guide

**Type ID:** `metric_id`
**Classification:** minted

---

## Quick Start

### Assigning a New Metric Identifier

```bash
python scripts/automation/metric_id_assigner.py <entity_name> --category <category>
```

**Example:**
```bash
python scripts/automation/metric_id_assigner.py my_template --category DOC
```

### Scanning for Unassigned Entities

```bash
python scripts/automation/metric_id_scanner.py
```

---

## Validation

Validate the registry:

```bash
python scripts/validators/validate_metric_id.py
```

---

## Registry Lookup

View all assigned IDs:

```bash
cat RUNTIME/metrics/METRIC_REGISTRY.yaml
```

---

## Integration

### Pre-commit Hook

Automatically validates on commit (if enabled in automation).

### CI/CD Pipeline

Add to `.github/workflows/`:

```yaml
- name: Validate Metric Identifier
  run: python scripts/validators/validate_metric_id.py
```

---

**Last Updated:** 2026-01-04
