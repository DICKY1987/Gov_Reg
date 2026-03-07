# DOC_ID: DOC-SCRIPT-1130
# Call Site Identifier Registry

**Type ID:** `callsite_id`
**Classification:** derived
**Owner:** Static Analysis
**Status:** Active

---

## Overview

Identifier for function call sites

**Format:** `CALL-{CALLER_ID}-{CALLEE_ID}-{LINE}`

## Categories

*No categories defined*

---

## Registry Structure

```yaml
callsite_ids:
  - id: CALL-<CALLER_ID>-<CALLEE_ID>-<LINE>
    name: <human_readable_name>
    status: active
    created_utc: <ISO8601_timestamp>
    categories: [<category_list>]
```

---

## Usage

### Minting a New Call Site Identifier

IDs are automatically derived from source data.

**Derivation Rule:** Derived from caller symbol_id + callee symbol_id + line number

---

## Validation

This registry is validated by:
- Format validator (regex: `^CALL-[0-9a-f]{16}-[0-9a-f]{16}-[0-9]+$`)
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
