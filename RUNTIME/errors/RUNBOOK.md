# DOC_ID: DOC-ERROR-0292
# Error Code Identifier Troubleshooting Runbook

**Type ID:** `error_code`

---

## Common Issues

### Issue 1: Format Validation Failures

**Symptom:** Validator reports format violations

**Diagnosis:**
```bash
python scripts/validators/validate_error_code.py
```

**Resolution:**
1. Check ID format against regex: `^ERR-([A-Z0-9]+)-([0-9]{3,})$`
2. Update malformed IDs in registry
3. Re-run validator

---

### Issue 2: Duplicate IDs

**Symptom:** Registry contains duplicate IDs

**Diagnosis:**
```bash
python scripts/validators/validate_error_code.py
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
python scripts/automation/error_code_scanner.py
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
   cp RUNTIME/errors/ERROR_REGISTRY.yaml.backup RUNTIME/errors/ERROR_REGISTRY.yaml
   ```

2. **Rebuild from source:**
   ```bash
   python scripts/automation/error_code_scanner.py --rebuild
   ```

---

## Monitoring

### Health Check

```bash
# Check registry health
python scripts/validators/validate_error_code.py

# Check coverage
python scripts/automation/error_code_scanner.py --report
```

---

## Escalation

If issues persist:
1. Check `ID_TYPE_REGISTRY.yaml` for spec errors
2. Review recent commits affecting error_code
3. Contact: Error Taxonomy

---

**Last Updated:** 2026-01-04
