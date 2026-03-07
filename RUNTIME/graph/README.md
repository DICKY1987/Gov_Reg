# DOC_ID: DOC-SCRIPT-1148
# Graph Edge Identifier Registry

**Type ID:** `graph_edge_id`
**Classification:** derived
**Owner:** Graph System
**Status:** Active

---

## Overview

Identifier for document graph edges

**Format:** `EDGE-{HASH}`

## Categories

*No categories defined*

---

## Registry Structure

```yaml
graph_edge_ids:
  - id: EDGE-<HASH>
    name: <human_readable_name>
    status: active
    created_utc: <ISO8601_timestamp>
    categories: [<category_list>]
```

---

## Usage

### Minting a New Graph Edge Identifier

IDs are automatically derived from source data.

**Derivation Rule:** Derived from edge endpoints and properties hash

---

## Validation

This registry is validated by:
- Format validator (regex: `^EDGE-[0-9a-f]{16}$`)
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
