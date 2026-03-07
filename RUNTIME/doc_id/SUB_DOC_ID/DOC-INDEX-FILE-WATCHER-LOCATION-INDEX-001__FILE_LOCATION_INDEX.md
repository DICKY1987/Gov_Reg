<!-- DOC_LINK: DOC-INDEX-FILE-WATCHER-LOCATION-INDEX-001 -->
---
doc_id: DOC-INDEX-FILE-WATCHER-LOCATION-INDEX-001
date: 2026-01-08
version: 1.0
---

# File Watcher System - Complete File Location Index

**Quick navigation index for all file watcher related files across the repository.**

---

## Core System Files (Production)

### Active Implementation

| File | Path | Size | Purpose |
|------|------|------|---------|
| **file_watcher_v2_hardened.py** | `3_AUTOMATION_HOOKS/` | 657 lines | Main watcher (v2 hardened) - PRODUCTION |
| **test_file_watcher_v2_integration.py** | `3_AUTOMATION_HOOKS/` | 204 lines | Real end-to-end tests (26 tests) |
| **DOC_ID_REGISTRY.yaml** | `5_REGISTRY_DATA/` | ~3761 docs | Master registry (27 categories) |
| **doc_id_scanner.py** | `1_CORE_OPERATIONS/` | ~600 lines | Repository scanner |
| **doc_id_assigner.py** | `1_CORE_OPERATIONS/` | ~500 lines | ID assignment engine |

### Legacy/Alternate Versions

| File | Path | Size | Status |
|------|------|------|--------|
| **file_watcher.py** | `3_AUTOMATION_HOOKS/` | 498 lines | v1.5 (superseded by v2 hardened) |
| **v3_file_watcher.py** | `3_AUTOMATION_HOOKS/` | ~300 lines | v3 architecture (experimental) |
| **detect_changes.py** | `3_AUTOMATION_HOOKS/` | ~100 lines | Change detection utility |

---

## Documentation Files

### Primary Documentation (Read These First)

| Document | Path | Size | Purpose |
|----------|------|------|---------|
| **FILE_WATCHER_COMPREHENSIVE_DOCS.md** | `SUB_DOC_ID/` | 45KB | THIS FILE - Complete reference |
| **FILE_WATCHER_V2_HARDENED_REPORT.md** | `SUB_DOC_ID/` | 11KB | Assessment response & delivery report |
| **ENHANCEMENT_RUNBOOK.md** | `SUB_DOC_ID/` | 8KB | Operations guide & troubleshooting |
| **FILE_WATCHER_ENHANCEMENT_SUMMARY.md** | `SUB_DOC_ID/` | 9KB | Enhancement delivery summary |
| **FILE_WATCHER_ANALYSIS.md** | `SUB_DOC_ID/` | 9KB | Technical analysis & architecture |

### Supporting Documentation

| Document | Path | Purpose |
|----------|------|---------|
| **FILE_WATCHER_USER_GUIDE.md** | `SUB_DOC_ID/` | User guide (v1.0 era) |
| **CROSS_FOLDER_WATCHER_README.md** | `3_AUTOMATION_HOOKS/` | Cross-folder watching docs |
| **README_3_AUTOMATION_HOOKS.md** | `3_AUTOMATION_HOOKS/` | Automation hooks README |

---

## Directory Structure

```
C:\Users\richg\ALL_AI\RUNTIME\doc_id\SUB_DOC_ID\
│
├── FILE_WATCHER_COMPREHENSIVE_DOCS.md       ← YOU ARE HERE
├── FILE_WATCHER_V2_HARDENED_REPORT.md       ← Assessment response
├── FILE_WATCHER_ENHANCEMENT_SUMMARY.md      ← Delivery summary
├── FILE_WATCHER_ANALYSIS.md                 ← Technical analysis
├── ENHANCEMENT_RUNBOOK.md                   ← Operations runbook
├── FILE_WATCHER_USER_GUIDE.md               ← User guide
│
├── 3_AUTOMATION_HOOKS/                      ← AUTOMATION LAYER
│   ├── file_watcher_v2_hardened.py          ← PRODUCTION WATCHER
│   ├── file_watcher.py                      ← Legacy (v1.5)
│   ├── test_file_watcher_v2_integration.py  ← Tests (26 tests)
│   ├── v3_file_watcher.py                   ← Experimental (v3)
│   ├── detect_changes.py                    ← Change detector
│   ├── pre_commit_hook.py                   ← Git integration
│   ├── setup_scheduled_tasks.py             ← Windows scheduler
│   └── README_3_AUTOMATION_HOOKS.md
│
├── 1_CORE_OPERATIONS/                       ← CORE ENGINE
│   ├── doc_id_scanner.py                    ← Repository scanner
│   ├── doc_id_assigner.py                   ← ID assigner
│   ├── batch_assign_docids.py               ← Batch operations
│   ├── fix_docid_format.py                  ← Format fixer
│   ├── deprecate_doc_id.py                  ← Deprecation
│   ├── classify_scope.py                    ← Scope classifier
│   ├── tree_sitter_extractor.py             ← AST parser
│   ├── registry_lock.py                     ← Locking mechanism
│   └── README_1_CORE_OPERATIONS.md
│
├── 2_VALIDATION_FIXING/                     ← VALIDATION LAYER
│   ├── validate_doc_id_coverage.py          ← Coverage checks
│   ├── validate_doc_id_uniqueness.py        ← Uniqueness validation
│   ├── validate_doc_id_sync.py              ← Sync validation
│   ├── validate_doc_id_references.py        ← Reference checks
│   ├── validate_automation_health.py        ← Health checks
│   ├── fix_duplicate_doc_ids.py             ← Duplicate fixer
│   ├── fix_invalid_doc_ids.py               ← Invalid ID fixer
│   ├── detect_doc_drift.py                  ← Drift detector
│   ├── auto_resolve_drift.py                ← Auto drift fixer
│   └── README_2_VALIDATION_FIXING.md
│
├── 4_REPORTING_MONITORING/                  ← REPORTING LAYER
│   ├── generate_dashboard.py                ← Dashboard generator
│   ├── doc_id_coverage_trend.py             ← Coverage trends
│   ├── scheduled_report_generator.py        ← Scheduled reports
│   ├── alert_monitor.py                     ← Alert system
│   └── README_4_REPORTING_MONITORING.md
│
├── 5_REGISTRY_DATA/                         ← DATA LAYER
│   ├── DOC_ID_REGISTRY.yaml                 ← MASTER REGISTRY
│   ├── sync_doc_id_registry.py              ← Registry sync
│   ├── backups_v2_v3/
│   │   ├── DOC_ID_REGISTRY_v2_final_*.yaml  ← v2 backup
│   │   └── CUTOVER_LOG_*.md                 ← Cutover logs
│   └── README_5_REGISTRY_DATA.md
│
├── 6_TESTS/                                 ← TEST LAYER
│   ├── test_core_operations.py              ← Core tests
│   ├── test_doc_id_system.py                ← System tests
│   ├── test_integration_unified.py          ← Integration tests
│   ├── test_suite_master.py                 ← Master suite
│   ├── run_tests.py                         ← Test runner
│   ├── conftest.py                          ← Pytest config
│   └── README_6_TESTS.md
│
├── 7_CLI_INTERFACE/                         ← CLI LAYER
│   ├── doc_id_cli.py                        ← CLI interface
│   ├── cli_wrapper.py                       ← CLI wrapper
│   └── README_7_CLI_INTERFACE.md
│
└── common/                                  ← SHARED UTILITIES
    ├── config.py                            ← Configuration
    ├── utils.py                             ← Utilities
    ├── validators.py                        ← Validators
    ├── rules.py                             ← Business rules
    ├── registry.py                          ← Registry interface
    ├── errors.py                            ← Error definitions
    ├── logging_setup.py                     ← Logging
    ├── event_emitter.py                     ← Event system
    └── README_common.md
```

---

## Quick Access Paths

### For Users

```powershell
# Start production watcher
cd C:\Users\richg\ALL_AI\RUNTIME\doc_id\SUB_DOC_ID\3_AUTOMATION_HOOKS
python file_watcher_v2_hardened.py

# Run tests
pytest test_file_watcher_v2_integration.py -v

# Check registry
cd ..\5_REGISTRY_DATA
Get-Content DOC_ID_REGISTRY.yaml
```

### For Developers

```powershell
# Edit watcher
code C:\Users\richg\ALL_AI\RUNTIME\doc_id\SUB_DOC_ID\3_AUTOMATION_HOOKS\file_watcher_v2_hardened.py

# Edit tests
code C:\Users\richg\ALL_AI\RUNTIME\doc_id\SUB_DOC_ID\3_AUTOMATION_HOOKS\test_file_watcher_v2_integration.py

# Edit registry
code C:\Users\richg\ALL_AI\RUNTIME\doc_id\SUB_DOC_ID\5_REGISTRY_DATA\DOC_ID_REGISTRY.yaml
```

### For Administrators

```powershell
# Documentation root
cd C:\Users\richg\ALL_AI\RUNTIME\doc_id\SUB_DOC_ID

# View all docs
Get-ChildItem -Filter "*FILE_WATCHER*.md"

# View logs (if running as service)
Get-Content C:\logs\file_watcher.log -Tail 50
```

---

## File Categories

### Production Code (DO NOT DELETE)

```
✅ CRITICAL - Active production files:
   - file_watcher_v2_hardened.py
   - doc_id_scanner.py
   - doc_id_assigner.py
   - DOC_ID_REGISTRY.yaml
   - common/*.py
```

### Test Files (DO NOT DELETE)

```
✅ CRITICAL - Test coverage:
   - test_file_watcher_v2_integration.py (26 tests)
   - test_core_operations.py
   - test_doc_id_system.py
   - conftest.py
```

### Documentation (REFERENCE)

```
📚 PRIMARY DOCS:
   - FILE_WATCHER_COMPREHENSIVE_DOCS.md (this file)
   - FILE_WATCHER_V2_HARDENED_REPORT.md
   - ENHANCEMENT_RUNBOOK.md
   - FILE_WATCHER_ENHANCEMENT_SUMMARY.md
   - FILE_WATCHER_ANALYSIS.md

📝 SUPPORTING DOCS:
   - FILE_WATCHER_USER_GUIDE.md
   - README_*.md (per directory)
```

### Legacy Code (CAN ARCHIVE)

```
⚠️  SUPERSEDED - Keep for reference:
   - file_watcher.py (v1.5 - superseded by v2)
   - detect_changes.py (utility, rarely used)

🧪 EXPERIMENTAL - Keep for future:
   - v3_file_watcher.py (v3 architecture)
   - v3_pre_commit.py
   - v3_automation_runner.py
```

---

## Related Systems

### Trigger ID System

```
RUNTIME/doc_id/SUB_DOC_ID/trigger_id/
├── 1_CORE_OPERATIONS/
│   ├── trigger_id_scanner.py
│   └── trigger_id_assigner.py
├── 5_REGISTRY_DATA/
│   └── TRIGGER_ID_REGISTRY.yaml
└── README.md
```

### Pattern ID System

```
RUNTIME/doc_id/SUB_DOC_ID/pattern_id/
├── 1_CORE_OPERATIONS/
│   ├── pattern_id_scanner.py
│   └── pattern_id_manager.py
├── 5_REGISTRY_DATA/
│   └── PATTERN_ID_REGISTRY.yaml
└── README.md
```

---

## Backup & Archive Locations

### Registry Backups

```
5_REGISTRY_DATA/backups_v2_v3/
├── DOC_ID_REGISTRY_v2_final_20251227_173447.yaml
├── CUTOVER_LOG_20251227_173447.md
└── [automated backups with timestamps]
```

### Documentation Archives

```
docs/ARCHIVE/
├── phase_plans/
│   ├── BATCH_ASSIGNMENT_COMPLETION_REPORT.md
│   ├── MULTI_DIR_DOC_ID_PHASE_PLAN.md
│   └── OPTIMIZATION_PHASE_PLAN_V3.0.md
├── analysis/
│   ├── FILE_BREAKDOWN.md
│   └── MISPLACED_FILES_ANALYSIS.md
└── cleanup_2025_12_28/
    └── [cleanup reports]
```

---

## Search Patterns

### Find All Watcher Files

```powershell
cd C:\Users\richg\ALL_AI\RUNTIME\doc_id\SUB_DOC_ID
Get-ChildItem -Recurse -Filter "*file_watcher*"
```

### Find All Documentation

```powershell
Get-ChildItem -Recurse -Filter "FILE_WATCHER*.md"
```

### Find All Tests

```powershell
cd 6_TESTS
Get-ChildItem -Filter "*watcher*.py"
```

### Find Registry Files

```powershell
Get-ChildItem -Recurse -Filter "*REGISTRY.yaml"
```

---

## External Dependencies

### Python Packages

```
watchdog>=3.0.0     # File system monitoring
pyyaml>=6.0         # YAML parsing
pytest>=7.0         # Testing framework
```

**Install:**
```bash
pip install watchdog pyyaml pytest
```

### System Requirements

- **OS:** Windows 10/11, Linux, macOS
- **Python:** 3.8+
- **Git:** 2.x (for pre-commit hooks)
- **Disk:** 100MB (registry + logs)
- **RAM:** 50-100MB (watcher process)

---

## Integration Points

### Git Integration

```
.git/hooks/
└── pre-commit → SUB_DOC_ID/3_AUTOMATION_HOOKS/pre_commit_hook.py
```

**Setup:**
```powershell
cd C:\Users\richg\ALL_AI\RUNTIME\doc_id\SUB_DOC_ID\3_AUTOMATION_HOOKS
python install_pre_commit_hook.py
```

### Windows Task Scheduler

```
Task Name: DOC_ID File Watcher
Script: C:\Users\richg\ALL_AI\RUNTIME\doc_id\SUB_DOC_ID\3_AUTOMATION_HOOKS\file_watcher_v2_hardened.py
Trigger: System startup
Run as: Current user
```

**Setup:**
```powershell
python setup_scheduled_tasks.py
```

---

## Navigation Shortcuts

### By Task

| Task | Go To |
|------|-------|
| Start watcher | `3_AUTOMATION_HOOKS/file_watcher_v2_hardened.py` |
| Run tests | `3_AUTOMATION_HOOKS/test_file_watcher_v2_integration.py` |
| Check registry | `5_REGISTRY_DATA/DOC_ID_REGISTRY.yaml` |
| Troubleshoot | `ENHANCEMENT_RUNBOOK.md` |
| Learn architecture | `FILE_WATCHER_ANALYSIS.md` |
| Read full docs | `FILE_WATCHER_COMPREHENSIVE_DOCS.md` |

### By Role

| Role | Primary Files |
|------|---------------|
| **User** | FILE_WATCHER_USER_GUIDE.md, ENHANCEMENT_RUNBOOK.md |
| **Developer** | file_watcher_v2_hardened.py, test_file_watcher_v2_integration.py |
| **Admin** | FILE_WATCHER_COMPREHENSIVE_DOCS.md, setup_scheduled_tasks.py |
| **Tester** | test_file_watcher_v2_integration.py, conftest.py |
| **Architect** | FILE_WATCHER_ANALYSIS.md, FILE_WATCHER_V2_HARDENED_REPORT.md |

---

## Change History

### v2.0 Hardened (2026-01-08)

**Added:**
- file_watcher_v2_hardened.py
- test_file_watcher_v2_integration.py
- FILE_WATCHER_V2_HARDENED_REPORT.md
- FILE_WATCHER_COMPREHENSIVE_DOCS.md (this file)
- FILE_LOCATION_INDEX.md (this file)

**Modified:**
- DOC_ID_REGISTRY.yaml (+11 categories)
- ENHANCEMENT_RUNBOOK.md (updated)
- FILE_WATCHER_ENHANCEMENT_SUMMARY.md (updated)

**Status:**
- file_watcher.py → Superseded by v2 hardened
- Original tests → Replaced by real integration tests

### v1.5 Enhancement (2026-01-07)

**Added:**
- file_watcher.py (enhanced)
- ENHANCEMENT_RUNBOOK.md
- FILE_WATCHER_ENHANCEMENT_SUMMARY.md
- FILE_WATCHER_ANALYSIS.md

**Modified:**
- DOC_ID_REGISTRY.yaml (+11 categories)
- MONITORED_FOLDERS (+12 directories)

### v1.0 Original (2025-12)

**Initial:**
- file_watcher.py (basic)
- FILE_WATCHER_USER_GUIDE.md
- DOC_ID_REGISTRY.yaml (16 categories)

---

## Maintenance

### Regular Tasks

| Task | Frequency | File |
|------|-----------|------|
| Check watcher running | Daily | Task Manager / ps |
| Review coverage stats | Weekly | Scanner output |
| Backup registry | Monthly | DOC_ID_REGISTRY.yaml |
| Update docs | On changes | *.md files |
| Run tests | On changes | pytest |

### Backup Procedures

**Manual Backup:**
```powershell
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
Copy-Item "5_REGISTRY_DATA\DOC_ID_REGISTRY.yaml" `
          "5_REGISTRY_DATA\backups_v2_v3\DOC_ID_REGISTRY_backup_$timestamp.yaml"
```

**Automated:** Registry backups created by watcher on each scan.

---

## Support Resources

### Documentation Hierarchy

1. **FILE_WATCHER_COMPREHENSIVE_DOCS.md** (this file) - Complete reference
2. **ENHANCEMENT_RUNBOOK.md** - Operations & troubleshooting
3. **FILE_WATCHER_V2_HARDENED_REPORT.md** - Assessment & delivery
4. **FILE_WATCHER_ANALYSIS.md** - Technical architecture
5. **FILE_WATCHER_USER_GUIDE.md** - User guide (legacy)

### Contact/Support

**Questions:**
1. Check comprehensive docs (this file)
2. Check runbook for troubleshooting
3. Check test suite for examples
4. Review delivery report for details

**Issues:**
1. Check stats output for diagnostics
2. Run tests to verify system health
3. Check registry for conflicts
4. Review recent changes in git history

---

## Document Metadata

**Document ID:** DOC-INDEX-FILE-WATCHER-LOCATION-INDEX-001
**Created:** 2026-01-08
**Version:** 1.0
**Purpose:** Complete file location index for file watcher system
**Scope:** All file watcher related files in repository

**Related Documents:**
- FILE_WATCHER_COMPREHENSIVE_DOCS.md (parent document)
- ENHANCEMENT_RUNBOOK.md
- FILE_WATCHER_V2_HARDENED_REPORT.md

**Last Updated:** 2026-01-08
**Update Frequency:** On file structure changes

---

**END OF FILE LOCATION INDEX**
