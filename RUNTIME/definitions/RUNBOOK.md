# DOC_ID: DOC-SCRIPT-1137
# Definition Site Identifier Troubleshooting Runbook

**Type ID:** `definition_id`

---

## Common Issues

### Issue 1: Format Validation Failures

**Symptom:** Validator reports format violations

**Diagnosis:**
```bash
python scripts/validators/validate_definition_id.py
```

**Resolution:**
1. Check ID format against regex: `^DEF-SYM-[0-9a-f]{8}-[0-9a-f]{8}-[0-9a-f]{8}-[0-9a-f]{8}$`
2. Update malformed IDs in registry
3. Re-run validator

---

### Issue 2: Duplicate IDs

**Symptom:** Registry contains duplicate IDs

**Diagnosis:**
```bash
python scripts/validators/validate_definition_id.py
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
python scripts/automation/definition_id_scanner.py
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
   cp RUNTIME/definitions/DEF_REGISTRY.yaml.backup RUNTIME/definitions/DEF_REGISTRY.yaml
   ```

2. **Rebuild from source:**
   ```bash
   python scripts/automation/definition_id_scanner.py --rebuild
   ```

---

## Monitoring

### Health Check

```bash
# Check registry health
python scripts/validators/validate_definition_id.py

# Check coverage
python scripts/automation/definition_id_scanner.py --report
```

---

## Escalation

If issues persist:
1. Check `ID_TYPE_REGISTRY.yaml` for spec errors
2. Review recent commits affecting definition_id
3. Contact: Code Analysis

---

**Last Updated:** 2026-01-04
