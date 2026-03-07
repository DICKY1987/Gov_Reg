# DOC_ID: DOC-SCRIPT-1149
# Graph Edge Identifier Troubleshooting Runbook

**Type ID:** `graph_edge_id`

---

## Common Issues

### Issue 1: Format Validation Failures

**Symptom:** Validator reports format violations

**Diagnosis:**
```bash
python scripts/validators/validate_graph_edge_id.py
```

**Resolution:**
1. Check ID format against regex: `^EDGE-[0-9a-f]{16}$`
2. Update malformed IDs in registry
3. Re-run validator

---

### Issue 2: Duplicate IDs

**Symptom:** Registry contains duplicate IDs

**Diagnosis:**
```bash
python scripts/validators/validate_graph_edge_id.py
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
python scripts/automation/graph_edge_id_scanner.py
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
   cp RUNTIME/graph/EDGE_REGISTRY.yaml.backup RUNTIME/graph/EDGE_REGISTRY.yaml
   ```

2. **Rebuild from source:**
   ```bash
   python scripts/automation/graph_edge_id_scanner.py --rebuild
   ```

---

## Monitoring

### Health Check

```bash
# Check registry health
python scripts/validators/validate_graph_edge_id.py

# Check coverage
python scripts/automation/graph_edge_id_scanner.py --report
```

---

## Escalation

If issues persist:
1. Check `ID_TYPE_REGISTRY.yaml` for spec errors
2. Review recent commits affecting graph_edge_id
3. Contact: Graph System

---

**Last Updated:** 2026-01-04
