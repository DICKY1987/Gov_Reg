# DOC_ID: DOC-SCRIPT-1158
# Outcome Identifier Troubleshooting Runbook

**Type ID:** `outcome_id`

---

## Common Issues

### Issue 1: Format Validation Failures

**Symptom:** Validator reports format violations

**Diagnosis:**
```bash
python scripts/validators/validate_outcome_id.py
```

**Resolution:**
1. Check ID format against regex: `^OUT-STEP-[A-Z0-9-]+-[0-9]{8}$`
2. Update malformed IDs in registry
3. Re-run validator

---

### Issue 2: Duplicate IDs

**Symptom:** Registry contains duplicate IDs

**Diagnosis:**
```bash
python scripts/validators/validate_outcome_id.py
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
python scripts/automation/outcome_id_scanner.py
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
   cp RUNTIME/outcomes/OUTCOME_REGISTRY.yaml.backup RUNTIME/outcomes/OUTCOME_REGISTRY.yaml
   ```

2. **Rebuild from source:**
   ```bash
   python scripts/automation/outcome_id_scanner.py --rebuild
   ```

---

## Monitoring

### Health Check

```bash
# Check registry health
python scripts/validators/validate_outcome_id.py

# Check coverage
python scripts/automation/outcome_id_scanner.py --report
```

---

## Escalation

If issues persist:
1. Check `ID_TYPE_REGISTRY.yaml` for spec errors
2. Review recent commits affecting outcome_id
3. Contact: Process Library

---

**Last Updated:** 2026-01-04
