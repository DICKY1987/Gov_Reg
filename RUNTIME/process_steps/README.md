# DOC_ID: DOC-SCRIPT-1163
# Process Step Identifier Registry

**Type ID:** `step_id`
**Classification:** derived
**Owner:** Process Library
**Status:** Active

---

## Overview

Derived identifier for process steps

**Format:** `STEP-{PHASE_ID}-{STEP_NUMBER}`

## Categories

*No categories defined*

---

## Registry Structure

```yaml
step_ids:
  - id: STEP-<PHASE_ID>-<STEP_NUMBER>
    name: <human_readable_name>
    status: active
    created_utc: <ISO8601_timestamp>
    categories: [<category_list>]
```

---

## Usage

### Minting a New Process Step Identifier

IDs are automatically derived from source data.

**Derivation Rule:** Derived from phase_id + step sequence number

---

## Validation

This registry is validated by:
- Format validator (regex: `^STEP-PH-[A-Z0-9-]+-[0-9]{3,}-[0-9]{2}$`)
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
