# DOC_ID: DOC-SCRIPT-1160
# Pipeline Instance Identifier Registry

**Type ID:** `pipeline_id`
**Classification:** runtime
**Owner:** Pipeline Execution
**Status:** Active

---

## Overview

Runtime identifier for pipeline instances

**Format:** `PIPELINE-{ULID}`

## Categories

*No categories defined*

---

## Registry Structure

```yaml
pipeline_ids:
  - id: PIPELINE-<ULID>
    name: <human_readable_name>
    status: active
    created_utc: <ISO8601_timestamp>
    categories: [<category_list>]
```

---

## Usage

### Minting a New Pipeline Instance Identifier

IDs are generated at runtime using ULID.

**Format:** PIPELINE-{ULID}

---

## Validation

This registry is validated by:
- Format validator (regex: `^PIPELINE-[0-9A-HJKMNP-TV-Z]{26}$`)
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
