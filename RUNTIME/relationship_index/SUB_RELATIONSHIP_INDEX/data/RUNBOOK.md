# DOC_ID: DOC-SCRIPT-1193
# Relationship Edge Identifier Troubleshooting Runbook

**Type ID:** `relationship_id`

---

## Common Issues

### Issue 1: Format Validation Failures

**Symptom:** Validator reports format violations

**Diagnosis:**
```bash
python scripts/validators/validate_relationship_id.py
```

**Resolution:**
1. Check ID format against regex: `^REL-[0-9a-f]{8}-[0-9a-f]{8}-[A-Z_]+$`
2. Update malformed IDs in registry
3. Re-run validator

---

### Issue 2: Duplicate IDs

**Symptom:** Registry contains duplicate IDs

**Diagnosis:**
```bash
python scripts/validators/validate_relationship_id.py
```

**Resolution:**
1. Identify duplicates in error output
2. Manually resolve conflicts in registry
3. Update references if IDs changed
4. Re-run validator

---

### Issue 3: Registry/Filesystem Sync Issues

**Symptom:** Registry doesn't match filesystem

**Diagnosis:**
```bash
python scripts/automation/relationship_id_scanner.py
```

**Resolution:**
1. Scan for unassigned entities
2. Assign missing IDs
3. Remove stale registry entries
4. Re-run validator

---

## Emergency Procedures

### Registry Corruption

1. **Restore from backup:**
   ```bash
   cp RUNTIME/relationship_index/SUB_RELATIONSHIP_INDEX/data/RELATIONSHIP_INDEX.json.backup RUNTIME/relationship_index/SUB_RELATIONSHIP_INDEX/data/RELATIONSHIP_INDEX.json
   ```

2. **Rebuild from source:**
   ```bash
   python scripts/automation/relationship_id_scanner.py --rebuild
   ```

---

## Monitoring

### Health Check

```bash
# Check registry health
python scripts/validators/validate_relationship_id.py

# Check coverage
python scripts/automation/relationship_id_scanner.py --report
```

---

## Escalation

If issues persist:
1. Check `ID_TYPE_REGISTRY.yaml` for spec errors
2. Review recent commits affecting relationship_id
3. Contact: Relationship Index

---

**Last Updated:** 2026-01-04
