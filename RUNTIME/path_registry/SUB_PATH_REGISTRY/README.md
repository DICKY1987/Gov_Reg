# DOC_ID: DOC-SCRIPT-1187
# Path Key Identifier Registry

**Type ID:** `path_key`
**Classification:** derived
**Owner:** Path Registry
**Status:** Active

---

## Overview

Stable identifier for canonical paths

**Format:** `PATH-{HASH}`

## Categories

*No categories defined*

---

## Registry Structure

```yaml
path_keys:
  - id: PATH-<HASH>
    name: <human_readable_name>
    status: active
    created_utc: <ISO8601_timestamp>
    categories: [<category_list>]
```

---

## Usage

### Minting a New Path Key Identifier

IDs are automatically derived from source data.

**Derivation Rule:** Derived from file path: hash first 8 chars of canonical path

---

## Validation

This registry is validated by:
- Format validator (regex: `^PATH-[0-9a-f]{8}$`)
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
