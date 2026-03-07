# DOC_ID: DOC-SCRIPT-1153
# Hook Identifier Usage Guide

**Type ID:** `hook_id`
**Classification:** minted

---

## Quick Start

### Assigning a New Hook Identifier

```bash
python scripts/automation/hook_id_assigner.py <entity_name> --category <category>
```

**Example:**
```bash
python scripts/automation/hook_id_assigner.py my_template --category DOC
```

### Scanning for Unassigned Entities

```bash
python scripts/automation/hook_id_scanner.py
```

---

## Validation

Validate the registry:

```bash
python scripts/validators/validate_hook_id.py
```

---

## Registry Lookup

View all assigned IDs:

```bash
cat RUNTIME/hooks/HOOK_REGISTRY.yaml
```

---

## Integration

### Pre-commit Hook

Automatically validates on commit (if enabled in automation).

### CI/CD Pipeline

Add to `.github/workflows/`:

```yaml
- name: Validate Hook Identifier
  run: python scripts/validators/validate_hook_id.py
```

---

**Last Updated:** 2026-01-04
