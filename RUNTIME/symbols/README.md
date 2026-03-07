# DOC_ID: DOC-SCRIPT-1172
# Code Symbol Identifier Registry

**Type ID:** `symbol_id`
**Classification:** derived
**Owner:** Code Analysis
**Status:** Active

---

## Overview

Stable identifier for code symbols (functions, classes, methods)

**Format:** `SYM-{DOC_ID_HASH}-{QUALNAME_HASH}-{SIG_HASH}`

## Categories

- **FUNCTION** - FUNCTION category
- **CLASS** - CLASS category
- **METHOD** - METHOD category
- **PROPERTY** - PROPERTY category

---

## Registry Structure

```yaml
symbol_ids:
  - id: SYM-<DOC_ID_HASH>-<QUALNAME_HASH>-<SIG_HASH>
    name: <human_readable_name>
    status: active
    created_utc: <ISO8601_timestamp>
    categories: [<category_list>]
```

---

## Usage

### Minting a New Code Symbol Identifier

IDs are automatically derived from source data.

**Derivation Rule:** Derived from file doc_id + qualified name + signature hashes

---

## Validation

This registry is validated by:
- Format validator (regex: `^SYM-[0-9a-f]{8}-[0-9a-f]{8}-[0-9a-f]{8}$`)
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
