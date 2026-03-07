# DOC_ID: DOC-SCRIPT-1151
# Hook Identifier Registry

**Type ID:** `hook_id`
**Classification:** minted
**Owner:** Hook Framework
**Status:** Active

---

## Overview

Identifier for extensibility hooks

**Format:** `HOOK-{TYPE}-{NAME}-{SEQ}`

## Categories

- **PRE** - PRE category
- **POST** - POST category
- **AROUND** - AROUND category
- **EVENT** - EVENT category

---

## Registry Structure

```yaml
hook_ids:
  - id: HOOK-<TYPE>-<NAME>-<SEQ>
    name: <human_readable_name>
    status: active
    created_utc: <ISO8601_timestamp>
    categories: [<category_list>]
```

---

## Usage

### Minting a New Hook Identifier

1. Run the ID assigner: `python scripts/assign_hook_id.py`
2. Or manually add to registry following format
3. Validate with: `python scripts/validators/validate_hook_id.py`

---

## Validation

This registry is validated by:
- Format validator (regex: `^HOOK-([A-Z0-9]+)-([A-Z0-9-]+)-([0-9]{3,})$`)
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
