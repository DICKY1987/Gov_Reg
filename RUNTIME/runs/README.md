# DOC_ID: DOC-SCRIPT-1169
# Run Identifier Registry

**Type ID:** `run_id`
**Classification:** runtime
**Owner:** Execution Engine
**Status:** Active

---

## Overview

Execution run identifier

**Format:** `RUN-{ULID}`

## Categories

*No categories defined*

---

## Registry Structure

```yaml
run_ids:
  - id: RUN-<ULID>
    name: <human_readable_name>
    status: active
    created_utc: <ISO8601_timestamp>
    categories: [<category_list>]
```

---

## Usage

### Minting a New Run Identifier

IDs are generated at runtime using ULID.

**Format:** RUN-{ULID}

---

## Validation

This registry is validated by:
- Format validator (regex: `^RUN-[0-9A-HJKMNP-TV-Z]{26}$`)
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
