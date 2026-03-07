# DOC_ID: DOC-ERROR-0293
# Error Code Identifier Usage Guide

**Type ID:** `error_code`
**Classification:** minted

---

## Quick Start

### Assigning a New Error Code Identifier

```bash
python scripts/automation/error_code_assigner.py <entity_name> --category <category>
```

**Example:**
```bash
python scripts/automation/error_code_assigner.py my_template --category DOC
```

### Scanning for Unassigned Entities

```bash
python scripts/automation/error_code_scanner.py
```

---

## Validation

Validate the registry:

```bash
python scripts/validators/validate_error_code.py
```

---

## Registry Lookup

View all assigned IDs:

```bash
cat RUNTIME/errors/ERROR_REGISTRY.yaml
```

---

## Integration

### Pre-commit Hook

Automatically validates on commit (if enabled in automation).

### CI/CD Pipeline

Add to `.github/workflows/`:

```yaml
- name: Validate Error Code Identifier
  run: python scripts/validators/validate_error_code.py
```

---

**Last Updated:** 2026-01-04
