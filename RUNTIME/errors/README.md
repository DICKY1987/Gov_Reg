# DOC_ID: DOC-ERROR-0291
# Error Code Identifier Registry

**Type ID:** `error_code`
**Classification:** minted
**Owner:** Error Taxonomy
**Status:** Active

---

## Overview

Standard error taxonomy identifier

**Format:** `ERR-{SUBSYSTEM}-{NUMBER}`

## Categories

- **VALIDATION** - VALIDATION category
- **EXECUTION** - EXECUTION category
- **INTEGRATION** - INTEGRATION category
- **SYSTEM** - SYSTEM category

---

## Registry Structure

```yaml
error_codes:
  - id: ERR-<SUBSYSTEM>-<NUMBER>
    name: <human_readable_name>
    status: active
    created_utc: <ISO8601_timestamp>
    categories: [<category_list>]
```

---

## Usage

### Minting a New Error Code Identifier

1. Run the ID assigner: `python scripts/assign_error_code.py`
2. Or manually add to registry following format
3. Validate with: `python scripts/validators/validate_error_code.py`

---

## Validation

This registry is validated by:
- Format validator (regex: `^ERR-([A-Z0-9]+)-([0-9]{3,})$`)
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
