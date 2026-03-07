# DOC_ID: DOC-SCRIPT-1136
# Definition Site Identifier Registry

**Type ID:** `definition_id`
**Classification:** derived
**Owner:** Code Analysis
**Status:** Active

---

## Overview

Identifier for exact definition sites

**Format:** `DEF-{SYMBOL_ID}-{HASH}`

## Categories

*No categories defined*

---

## Registry Structure

```yaml
definition_ids:
  - id: DEF-<SYMBOL_ID>-<HASH>
    name: <human_readable_name>
    status: active
    created_utc: <ISO8601_timestamp>
    categories: [<category_list>]
```

---

## Usage

### Minting a New Definition Site Identifier

IDs are automatically derived from source data.

**Derivation Rule:** Derived from symbol_id + location hash

---

## Validation

This registry is validated by:
- Format validator (regex: `^DEF-SYM-[0-9a-f]{8}-[0-9a-f]{8}-[0-9a-f]{8}-[0-9a-f]{8}$`)
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
