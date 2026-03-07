# Registry Backup Hierarchy

**Created:** 2026-02-26T09:25:00Z  
**Purpose:** Document backup strategy and restore priority

---

## Active Backups

### 1. Pre-Cleanup Archive (2026-02-25)
**Location:** `archive/pre_cleanup_20260225_173348/`  
**Contents:**
- `01260207233100000466_geu_sets.regenerated.json`
- `01999000042260124503_REGISTRY_file.json`
- `registry_decontamination_report_20260225_173348.json`

**Purpose:** Snapshot before directory reorganization  
**Created By:** Directory cleanup process  
**Restore Command:**
```powershell
Copy-Item archive/pre_cleanup_20260225_173348/* . -Force
```

**Note:** This is a **partial backup** - contains only data files, not specification files.

---

### 2. Pre-Remediation Backup (Upcoming)
**Location:** `C:\Users\richg\Gov_Reg\01260207201000001133_backups\REGISTRY_pre_spec_remediation_*`  
**Purpose:** Full directory backup before specification remediation  
**Created By:** REGISTRY_SPEC_REMEDIATION_EXECUTION_PLAN.md Pre-Flight step  
**Status:** Not yet created - will be created before remediation execution

**Restore Command:**
```powershell
# Replace $timestamp with actual backup timestamp
Remove-Item "C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY" -Recurse -Force
Copy-Item -Path "C:\Users\richg\Gov_Reg\01260207201000001133_backups\REGISTRY_pre_spec_remediation_$timestamp" `
          -Destination "C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY" `
          -Recurse
```

**Note:** This will be a **complete backup** - includes all files and directory structure.

---

## Git History Backups

Git maintains a complete history of all committed changes. To restore from git:

```powershell
cd C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY

# View recent commits
git log --oneline -20

# Restore to specific commit
git checkout <commit-hash>

# Or revert a specific commit
git revert <commit-hash>

# Or reset to before remediation (DESTRUCTIVE)
git reset --hard <commit-before-remediation>
```

**Current Branch:** master  
**Recent Commits:**
- e656e83: docs: Add cross-reference to COLUMN_DICTIONARY
- 72c2fda: docs: Enhance py_capability_* fields in COLUMN_DICTIONARY
- ac63f85: refactor: Reorganize REGISTRY directory structure

---

## Backup Priority / Restore Strategy

If problems occur, use this order:

### Level 1: Git Operations (Preferred)
**Use When:** Need to undo specific changes or revert to a known good state  
**Advantages:** Granular control, maintains history, clean rollback  
**Commands:**
```powershell
# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes)
git reset --hard HEAD~1

# Revert specific commit (creates new commit)
git revert <commit-hash>
```

### Level 2: Pre-Remediation Backup (If Created)
**Use When:** Need complete directory restore after failed remediation  
**Advantages:** Complete snapshot, all files included  
**Disadvantages:** Overwrites everything, loses any good changes  

### Level 3: Pre-Cleanup Archive (Last Resort)
**Use When:** Critical data corruption and other methods fail  
**Advantages:** Known-good data files  
**Disadvantages:** 
- Only includes 3 files (data only, no specs)
- Doesn't include COLUMN_HEADERS/ or other directories
- May be stale if significant changes made since 2026-02-25

---

## Historical Backup Records

| Date | Original | Backup | Size | SHA256 |
|------|----------|--------|------|--------|
| 2026-02-03 17:14:30 | `01999000042260124503_REGISTRY_file.json` | `01999000042260124503_REGISTRY_file.json.20260203_171422.backup` | 0.61 MB | `D646FBFA...C94CD0EF` |

---

## Backup Retention Policy

**Git History:** Keep all commits (prune periodically after major milestones)  
**Pre-Cleanup Archive:** Keep indefinitely (reference point before reorganization)  
**Pre-Remediation Backup:** Keep for 30 days after successful remediation, then archive  
**Future Backups:** Create before major changes, retain per policy

---

## Emergency Restore Procedure

If the registry becomes corrupted or unusable:

1. **Stop all processes** accessing the registry
2. **Assess damage:**
   ```powershell
   cd C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY
   git status
   git diff
   ```
3. **Try git restore first:**
   ```powershell
   git restore .
   # Or if needed:
   git reset --hard HEAD
   ```
4. **If git doesn't fix it, use backup:**
   ```powershell
   # Identify most recent good backup
   Get-ChildItem C:\Users\richg\Gov_Reg\01260207201000001133_backups\ | 
       Where-Object Name -like "REGISTRY_pre_*" | 
       Sort-Object LastWriteTime -Descending |
       Select-Object -First 1
   
   # Restore from backup
   # (see commands above)
   ```
5. **Document what happened** in an incident report
6. **Test restored registry:**
   ```powershell
   python -m jsonschema --instance 01999000042260124503_REGISTRY_file.json `
                        01999000042260124012_governance_registry_schema.v3.json
   ```

---

## Next Backup Due

**Before:** REGISTRY_SPEC_REMEDIATION_EXECUTION_PLAN.md Phase 1  
**When:** Before any changes to WRITE_POLICY, DERIVATIONS, or schema files  
**Command:**
```powershell
cd C:\Users\richg\Gov_Reg
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
Copy-Item -Path "01260207201000001250_REGISTRY" `
          -Destination "01260207201000001133_backups\REGISTRY_pre_spec_remediation_$timestamp" `
          -Recurse
```

---

**Status:** DOCUMENTED  
**Last Updated:** 2026-02-26T09:25:00Z
