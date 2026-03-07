# DOC_ID: DOC-SCRIPT-1192
# Relationship Edge Identifier Registry

**Type ID:** `relationship_id`
**Classification:** derived
**Owner:** Relationship Index
**Status:** Active

---

## Overview

Identifier for typed relationships between entities

**Format:** `REL-{SOURCE_HASH}-{TARGET_HASH}-{TYPE}`

## Categories

*No categories defined*

---

## Registry Structure

```yaml
relationship_ids:
  - id: REL-<SOURCE_HASH>-<TARGET_HASH>-<TYPE>
    name: <human_readable_name>
    status: active
    created_utc: <ISO8601_timestamp>
    categories: [<category_list>]
```

---

## Usage

### Minting a New Relationship Edge Identifier

IDs are automatically derived from source data.

**Derivation Rule:** Derived from source ID hash + target ID hash + relationship type

---

## Validation

This registry is validated by:
- Format validator (regex: `^REL-[0-9a-f]{8}-[0-9a-f]{8}-[A-Z_]+$`)
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
