# DOC_ID: DOC-SCRIPT-1175
# Trace Identifier Registry

**Type ID:** `trace_id`
**Classification:** runtime
**Owner:** Observability
**Status:** Active

---

## Overview

Distributed trace identifier for correlation

**Format:** `TRACE-{ULID}`

## Categories

*No categories defined*

---

## Registry Structure

```yaml
trace_ids:
  - id: TRACE-<ULID>
    name: <human_readable_name>
    status: active
    created_utc: <ISO8601_timestamp>
    categories: [<category_list>]
```

---

## Usage

### Minting a New Trace Identifier

IDs are generated at runtime using ULID.

**Format:** TRACE-{ULID}

---

## Validation

This registry is validated by:
- Format validator (regex: `^TRACE-[0-9A-HJKMNP-TV-Z]{26}$`)
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
