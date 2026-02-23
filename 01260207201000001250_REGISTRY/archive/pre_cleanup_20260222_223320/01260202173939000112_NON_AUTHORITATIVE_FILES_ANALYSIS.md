# Non-Authoritative Documentation Files - Analysis Report

**Generated:** 2026-02-03
**Purpose:** Identify non-authoritative .md and .txt files in REGISTRY directory
**Scope:** All markdown and text files in REGISTRY and subdirectories

---

## Executive Summary

Out of **27 .md and .txt files** analyzed, **15 files are non-authoritative** (historical, status reports, feedback, or superseded documentation). **12 files are authoritative** and should be retained as active system documentation.

---

## Classification Criteria

### Authoritative Files
- Active system specifications
- Current operational documentation
- Reference implementations
- Required for system operation

### Non-Authoritative Files
- Historical status reports
- Completion/checkpoint logs
- Feedback/review documents
- Superseded specifications
- Planning artifacts (completed phases)

---

## NON-AUTHORITATIVE FILES (15 total)

### Category A: Status Reports & Completion Logs (7 files)

1. **`FILE_ID_MANAGEMENT_SYSTEM.md`**
   - Type: Completion report
   - Date: 2026-02-03
   - Status: ✅ Complete and operational
   - **Reason:** Historical documentation of completed file ID system implementation
   - **Action:** Archive or move to docs/history/

2. **`mapp_py/BATCH_1_COMPLETE.md`**
   - Type: Batch completion report
   - **Reason:** Historical milestone marker
   - **Action:** Archive

3. **`mapp_py/IMPLEMENTATION_COMPLETE_REPORT.md`**
   - Type: Implementation status report
   - **Reason:** Snapshot of completed implementation phase
   - **Action:** Archive

4. **`mapp_py/RECONCILIATION_COMPLETE.md`**
   - Type: Reconciliation completion log
   - **Reason:** Historical reconciliation process record
   - **Action:** Archive

5. **`mapp_py/SCRIPT_VALIDATION_REPORT.md`**
   - Type: Validation report
   - **Reason:** Point-in-time validation results
   - **Action:** Archive

6. **`BACKUP_FILES/backups/legacy_docs_20260202_175922/FILE_ID_CORRECTION_COMPLETE_REPORT.md`**
   - Type: Completion report (in backup)
   - **Reason:** Already backed up, historical artifact
   - **Action:** Keep in backups, no action needed

7. **`BACKUP_FILES/backups/file_id_correction_20260202_134242/AUDIT_REPORT.md`**
   - Type: Audit report (in backup)
   - **Reason:** Historical audit log, already backed up
   - **Action:** Keep in backups, no action needed

### Category B: Feedback & Review Documents (2 files)

8. **`FEEDBACK_ON_INGEST_BLOCKER.md`**
   - Type: Feedback/review document
   - Date: 2026-02-02
   - Status: ✅ Document is ACCURATE but should be updated
   - **Reason:** Feedback commentary on another document, not operational spec
   - **Action:** Archive after addressing recommendations

9. **`DOC-ISSUE-MAPP-PY-INGEST-BLOCKER.md`**
   - Type: Issue documentation
   - **Reason:** Issue tracker-style document for a specific blocker
   - **Action:** Archive when blocker resolved (may keep for reference)

### Category C: Patch & Correction Logs (3 files)

10. **`CRITICAL_ISSUES_PATCH.md`**
    - Type: Patch documentation
    - Date: 2026-02-02
    - Status: INCOMPLETE - Critical issues remain
    - **Reason:** Temporary patch tracking document, not permanent spec
    - **Action:** Archive once all fixes (TASK-016 through TASK-020) are applied

11. **`mapp_py/CORRECTIONS_APPLIED_V2.md`**
    - Type: Correction log
    - **Reason:** Historical record of applied corrections
    - **Action:** Archive

12. **`mapp_py/RECONCILIATION_PATCH.md`**
    - Type: Patch documentation
    - **Reason:** Historical patch application record
    - **Action:** Archive

### Category D: Planning & Working Docs (2 files)

13. **`plan_001`** (no extension)
    - Type: Planning document (JSON format)
    - **Reason:** Planning artifact for py_* column implementation
    - **Action:** Archive after completion of all phases

14. **`37 New Python-Specific Registry Col.txt`**
    - Type: Column list/specification
    - **Reason:** Superseded by formal schema and dictionary definitions
    - **Action:** Archive (information now in authoritative schema files)

### Category E: Informational Lists (1 file)

15. **`mapp_py/18 mapp_py Analyzer Scripts.txt`**
    - Type: Script inventory
    - **Reason:** Static list, information available via directory listing
    - **Action:** Archive or delete

---

## AUTHORITATIVE FILES (12 total)

### Category 1: System Specifications (3 files)

1. **`CLAUDE.md`** ✅
   - Type: AI assistant guidance documentation
   - Purpose: Repository overview and operational guidance
   - Status: Active, should be kept up-to-date

2. **`INGEST_SPEC_UNIFIED_REGISTRY.txt`** ✅
   - Type: Formal specification (JSON format)
   - spec_id: INGEST_SPEC_UNIFIED_REGISTRY
   - spec_version: 1.0.0
   - Status: Active specification
   - Purpose: Deterministic ingestion protocol

3. **`mapp_py/COLUMN_TO_SCRIPT_MAPPING.md`** ✅
   - Type: Authoritative mapping documentation
   - Purpose: Column-to-script mappings for mapp_py system
   - Status: Active reference (v2.0)

### Category 2: Technical Specifications (4 files)

4. **`mapp_py/TECHNICAL_COMPATIBILITY_SPEC.md`** ✅
   - Type: Compatibility specification
   - Purpose: Technical constraints and compatibility rules
   - Status: Active technical reference

5. **`mapp_py/IMPLEMENTATION_GUIDE_18_SCRIPTS.md`** ✅
   - Type: Implementation guide
   - Purpose: Guide for implementing 18 analyzer scripts
   - Status: Active development guide

6. **`REVIEW_PACKAGE_20260130_160006/README.md`** ✅
   - Type: Package documentation
   - Purpose: Review package overview
   - Status: Active for this review package

7. **`REVIEW_PACKAGE_20260130_160006/REVIEW_CHECKLIST.md`** ✅
   - Type: Procedural checklist
   - Purpose: Review process checklist
   - Status: Active for this review package

### Category 3: Integration Documentation (1 file)

8. **`BACKUP_FILES/backups/file_id_correction_20260202_134242/mapp_py/DOC-INTEGRATION-MAPP-PY-REGISTRY-001__Registry_Integration.md`** ✅
   - Type: Integration specification
   - Purpose: mapp_py to registry integration spec
   - Status: Active (in backup, may need to restore to main location)
   - **Note:** Should verify if current version exists outside backups

### Category 4: System Inventory (2 files)

9. **`repo_tree.txt`** ✅
   - Type: Repository structure snapshot
   - Purpose: Directory tree documentation
   - Status: Informational reference

10. **`mapp_py/requirements.txt`** ✅
    - Type: Python dependencies
    - Purpose: Package requirements for mapp_py
    - Status: Active operational file

### Category 5: Backup Specifications (2 files)

11. **`BACKUP_FILES/backups/file_id_correction_20260202_134132/INGEST_SPEC_UNIFIED_REGISTRY.txt`** ✅
    - Type: Backup of active specification
    - Purpose: Historical version of ingest spec
    - Status: Backup (retain for rollback capability)

12. **`BACKUP_FILES/backups/py_columns_20260202_142006/INGEST_SPEC_UNIFIED_REGISTRY.txt`** ✅
    - Type: Backup of active specification
    - Purpose: Historical version of ingest spec
    - Status: Backup (retain for rollback capability)

---

## Additional Files (No Extension)

- **`mapp_py/● ✅ All 18 Scripts are Already in t.txt`**
  - Type: Status indicator file (likely incomplete filename)
  - **Action:** Review and rename or delete

---

## Recommended Actions

### Immediate (High Priority)

1. **Create archive directory structure:**
   ```
   REGISTRY/
     archive/
       completed_milestones/
       feedback_reviews/
       patches_applied/
       planning_artifacts/
   ```

2. **Move non-authoritative files to appropriate archive folders**

3. **Update documentation index** to reflect current authoritative files only

### Short-Term (Medium Priority)

4. **Review backup locations:**
   - Verify `DOC-INTEGRATION-MAPP-PY-REGISTRY-001` exists outside backups
   - Consider restoring to main location if it's the only copy

5. **Clean up anomalies:**
   - Rename or remove `mapp_py/● ✅ All 18 Scripts are Already in t.txt`
   - Verify `plan_001` completion status

6. **Update CLAUDE.md:**
   - Remove references to archived documents
   - Update file paths if documents are moved

### Long-Term (Low Priority)

7. **Establish archival policy:**
   - Define retention periods for different document types
   - Create automated archival process for completion reports

8. **Documentation lifecycle management:**
   - Add status markers to active specifications (status: active/deprecated/superseded)
   - Implement version control for specifications

---

## Summary Statistics

| Category | Count | Percentage |
|----------|-------|------------|
| **Non-Authoritative Files** | 15 | 55.6% |
| **Authoritative Files** | 12 | 44.4% |
| **Total Files Analyzed** | 27 | 100% |

### Non-Authoritative Breakdown

| Type | Count |
|------|-------|
| Status Reports & Completion Logs | 7 |
| Feedback & Review Documents | 2 |
| Patch & Correction Logs | 3 |
| Planning & Working Docs | 2 |
| Informational Lists | 1 |

---

## File Disposition Matrix

| File | Category | Keep/Archive | Priority | Notes |
|------|----------|--------------|----------|-------|
| FILE_ID_MANAGEMENT_SYSTEM.md | Status | Archive | Low | System operational |
| CRITICAL_ISSUES_PATCH.md | Patch | Archive after fixes | High | 4 tasks remaining |
| FEEDBACK_ON_INGEST_BLOCKER.md | Feedback | Archive | Medium | Review complete |
| DOC-ISSUE-MAPP-PY-INGEST-BLOCKER.md | Issue | Archive/Keep ref | Medium | Blocker documented |
| plan_001 | Planning | Archive after completion | Medium | Check phase status |
| 37 New Python-Specific Registry Col.txt | Spec | Archive | Low | Info in schemas |
| repo_tree.txt | Info | Keep | Low | Useful reference |
| CLAUDE.md | Spec | **Keep** | High | Active guidance |
| INGEST_SPEC_UNIFIED_REGISTRY.txt | Spec | **Keep** | High | Active spec |
| mapp_py/COLUMN_TO_SCRIPT_MAPPING.md | Spec | **Keep** | High | Active mapping |
| mapp_py/requirements.txt | Config | **Keep** | High | Active deps |
| mapp_py/TECHNICAL_COMPATIBILITY_SPEC.md | Spec | **Keep** | High | Active tech spec |
| mapp_py/IMPLEMENTATION_GUIDE_18_SCRIPTS.md | Guide | **Keep** | High | Active dev guide |

---

## Validation Checklist

- [ ] Verify all 15 non-authoritative files are truly non-critical
- [ ] Check if any archived files are referenced by active code
- [ ] Ensure backups exist before archiving original files
- [ ] Update documentation indexes and references
- [ ] Test that system operation continues after archival
- [ ] Update CLAUDE.md with current file structure

---

## Conclusion

**55.6% of .md and .txt files are non-authoritative** and can be safely archived. This cleanup will:
- Reduce documentation clutter
- Clarify which files are operational vs historical
- Improve maintainability of the documentation set
- Preserve historical records in organized archive structure

The remaining **44.4% of files are authoritative** and must be maintained as active system documentation.

---

**Report Status:** ✅ Complete
**Next Action:** Review and approve archival plan, then execute file moves
