# DOC_ID: DOC-SCRIPT-1139
# Deployment Identifier Registry

**Type ID:** `deployment_id`
**Classification:** runtime
**Owner:** Deployment System
**Status:** Active

---

## Overview

Runtime identifier for deployments

**Format:** `DEPLOY-{ULID}`

## Categories

*No categories defined*

---

## Registry Structure

```yaml
deployment_ids:
  - id: DEPLOY-<ULID>
    name: <human_readable_name>
    status: active
    created_utc: <ISO8601_timestamp>
    categories: [<category_list>]
```

---

## Usage

### Minting a New Deployment Identifier

IDs are generated at runtime using ULID.

**Format:** DEPLOY-{ULID}

---

## Validation

This registry is validated by:
- Format validator (regex: `^DEPLOY-[0-9A-HJKMNP-TV-Z]{26}$`)
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
