# DOC_ID: DOC-SCRIPT-1157
# Outcome Identifier Registry

**Type ID:** `outcome_id`
**Classification:** derived
**Owner:** Process Library
**Status:** Active

---

## Overview

Derived identifier for step outcomes

**Format:** `OUT-{STEP_ID}-{HASH}`

## Categories

*No categories defined*

---

## Registry Structure

```yaml
outcome_ids:
  - id: OUT-<STEP_ID>-<HASH>
    name: <human_readable_name>
    status: active
    created_utc: <ISO8601_timestamp>
    categories: [<category_list>]
```

---

## Usage

### Minting a New Outcome Identifier

IDs are automatically derived from source data.

**Derivation Rule:** Derived from step_id + outcome type hash

---

## Validation

This registry is validated by:
- Format validator (regex: `^OUT-STEP-[A-Z0-9-]+-[0-9]{8}$`)
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
