# DOC_ID: DOC-SCRIPT-1154
# Metric Identifier Registry

**Type ID:** `metric_id`
**Classification:** minted
**Owner:** Metrics System
**Status:** Active

---

## Overview

Identifier for system metrics

**Format:** `METRIC-{DOMAIN}-{NAME}-{SEQ}`

## Categories

*No categories defined*

---

## Registry Structure

```yaml
metric_ids:
  - id: METRIC-<DOMAIN>-<NAME>-<SEQ>
    name: <human_readable_name>
    status: active
    created_utc: <ISO8601_timestamp>
    categories: [<category_list>]
```

---

## Usage

### Minting a New Metric Identifier

1. Run the ID assigner: `python scripts/assign_metric_id.py`
2. Or manually add to registry following format
3. Validate with: `python scripts/validators/validate_metric_id.py`

---

## Validation

This registry is validated by:
- Format validator (regex: `^METRIC-([A-Z0-9]+)-([A-Z0-9-]+)-([0-9]{3,})$`)
- Uniqueness validator
- Sync validator (registry ↔ filesystem)

---

## Automation

*No automation configured*

---

## References

- **ID Type Registry:** `RUNTIME/doc_id/SUB_DOC_ID/ID_TYPE_REGISTRY.yaml`
- **Governance:** `.ai/governance.md`
- **Universal Registry Schema:** `CONTEXT/docs/reference/UNIVERSAL_REGISTRY_SCHEMA_REFERENCE.md`

---

**Last Updated:** 2026-01-04
