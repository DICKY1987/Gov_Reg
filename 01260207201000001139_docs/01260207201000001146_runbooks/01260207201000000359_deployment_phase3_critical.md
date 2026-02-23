# Deployment Runbook: Phase 3 (CRITICAL)

**Phase:** Phase 3 Deployment + 2-Week Soak (PH-OP-004)  
**Duration:** 14 days (Week 5-6)  
**Critical Level:** MAXIMUM - Last reversible point

---

## ⚠️ CRITICAL WARNINGS

🚨 **THIS IS THE LAST REVERSIBLE POINT BEFORE PHASE 4**  
🚨 **REQUIRES FULL PRODUCTION BACKUP**  
🚨 **2-WEEK SOAK PERIOD MANDATORY**  
🚨 **WEEKLY STAKEHOLDER REPORTS REQUIRED**  
🚨 **ZERO CRITICAL ERRORS REQUIRED TO PROCEED**

---

## Pre-Deployment Requirements

### Mandatory Prerequisites:
- [x] Phase 0 stable for 24+ hours
- [x] Phase 1 stable for 48+ hours
- [x] Phase 2 stable for 72+ hours
- [ ] Full production backup completed
- [ ] Backup restore tested successfully
- [ ] Schema migration tested on copy
- [ ] Stakeholder approval obtained
- [ ] Emergency rollback plan approved
- [ ] 24/7 on-call schedule confirmed

---

## Step 1: Full Production Backup

### Commands:
```powershell
# Create comprehensive backup
python scripts/deployment/full_backup.py --output backups/pre_phase3_full_backup.tar.gz --verify

# Verify backup integrity
python scripts/deployment/verify_backup.py --backup backups/pre_phase3_full_backup.tar.gz

# Test restore on staging
python scripts/deployment/test_restore.py --backup backups/pre_phase3_full_backup.tar.gz --target staging
```

### Success Criteria:
- ✓ Backup created successfully
- ✓ Checksum verified
- ✓ Restore test passed on staging
- ✓ Backup size reasonable (< 10GB typical)
- ✓ Backup stored in multiple locations

### Artifacts:
- `backups/pre_phase3_full_backup.tar.gz`
- `backups/pre_phase3_backup_manifest.json`
- `.state/evidence/PH-008/backup_verification.log`

---

## Step 2: Test Schema Migration on Copy

### Commands:
```powershell
# Create production copy
python scripts/deployment/clone_production.py --output staging/registry_copy.json

# Test migration on copy
python scripts/deployment/test_schema_migration.py --backup backups/pre_phase3_full_backup.tar.gz --output .state/evidence/PH-008/migration_test_results.json

# Validate migrated data
python scripts/deployment/validate_migrated_data.py --input staging/registry_copy_v3.json
```

### Success Criteria:
- ✓ Migration completes without errors
- ✓ All records migrated successfully
- ✓ Schema v3 validation passes
- ✓ Data integrity maintained
- ✓ No data loss detected

### Abort Conditions:
- ❌ Any migration errors → ABORT, do not proceed
- ❌ Data validation fails → ABORT
- ❌ Schema inconsistencies → ABORT

---

## Step 3: Execute Production Schema Migration (v2 → v3)

### Pre-Flight Checklist:
- [ ] Backup verified
- [ ] Test migration successful
- [ ] Stakeholder approval obtained
- [ ] On-call team notified
- [ ] Rollback plan ready
- [ ] Monitoring dashboards open

### Commands:
```powershell
# Announce maintenance window
python scripts/deployment/announce_maintenance.py --duration 2-hours --phase PHASE_3

# Execute migration
python govreg_core/registry_schema_v3.py migrate --target production/registry.json --backup --log .state/evidence/PH-008/production_migration_log.json

# Verify migration
python scripts/deployment/verify_migration.py --registry production/registry.json
```

### Success Criteria:
- ✓ Migration completes within time window
- ✓ All records migrated to v3
- ✓ Schema validation passes
- ✓ Application starts successfully
- ✓ Smoke tests pass

### Immediate Rollback If:
- ❌ Migration fails or hangs
- ❌ Critical errors in logs
- ❌ Application fails to start
- ❌ Data corruption detected

### Rollback Commands:
```powershell
# Emergency rollback
python scripts/deployment/emergency_rollback.py --backup backups/pre_phase3_full_backup.tar.gz

# Restore from backup
python scripts/deployment/restore_from_backup.py --backup backups/pre_phase3_full_backup.tar.gz --verify

# Restart services
python scripts/deployment/restart_services.py --phase PHASE_2
```

---

## Step 4: 2-Week Soak Period

### Week 1 Monitoring

#### Daily Checks:
```powershell
# Daily health check
python scripts/deployment/daily_health_check.py --phase PHASE_3 --output .state/evidence/PH-008/daily/day_$(Get-Date -Format 'yyyyMMdd').json

# Check for critical errors
python scripts/deployment/check_critical_errors.py --since "24 hours ago"

# Performance metrics
python scripts/deployment/performance_report.py --output .state/evidence/PH-008/daily/perf_$(Get-Date -Format 'yyyyMMdd').json
```

#### Week 1 Report (Due: End of Day 7):
```powershell
# Generate Week 1 status report
python scripts/deployment/generate_soak_report.py --week 1 --output REPORTS/phase3_week1_status.md

# Submit to stakeholders
python scripts/deployment/submit_report.py --report REPORTS/phase3_week1_status.md --recipients stakeholders@company.com
```

**Week 1 Success Criteria:**
- ✓ Zero critical errors
- ✓ Performance within targets
- ✓ No data corruption
- ✓ No user-reported critical issues
- ✓ All daily checks passed

### Week 2 Monitoring

#### Daily Checks:
Same as Week 1 (continued monitoring)

#### Week 2 Report (Due: End of Day 14):
```powershell
# Generate Week 2 status report
python scripts/deployment/generate_soak_report.py --week 2 --output REPORTS/phase3_week2_status.md

# Generate final soak period summary
python scripts/deployment/generate_soak_summary.py --output .state/evidence/PH-008/soak_period_results.json

# Submit final report
python scripts/deployment/submit_report.py --report REPORTS/phase3_week2_status.md --recipients stakeholders@company.com
```

**Week 2 Success Criteria:**
- ✓ Zero critical errors for 14 consecutive days
- ✓ Performance stable and within targets
- ✓ No data integrity issues
- ✓ No user escalations
- ✓ All weekly reports submitted and approved

---

## Soak Period Failure Handling

### If Critical Error Occurs:

**Immediate Actions:**
1. Log incident details
2. Notify on-call team
3. Assess severity
4. Determine rollback necessity

**Rollback Decision Matrix:**

| Severity | Impact | Action |
|----------|--------|--------|
| Data corruption | Any | IMMEDIATE ROLLBACK |
| Critical error with data loss | Any | IMMEDIATE ROLLBACK |
| Performance degradation | >50% | ROLLBACK |
| Non-critical errors | Multiple | EVALUATE & ROLLBACK |
| Single non-critical error | Isolated | MONITOR & DOCUMENT |

**Rollback Commands:**
```powershell
# Rollback to Phase 2
python scripts/deployment/rollback_deployment.py --phase PHASE_3 --target PHASE_2

# Restore from backup if needed
python scripts/deployment/restore_from_backup.py --backup backups/pre_phase3_full_backup.tar.gz

# Restart from Phase 2 stable state
python scripts/deployment/restart_phase.py --phase PHASE_2
```

### Restart Soak Period:
If rolled back, must:
1. Fix root cause
2. Re-test migration
3. Obtain new stakeholder approval
4. Start fresh 2-week soak period

---

## Post-Soak Validation

### Final Validation Gate:
```powershell
# Validate 2-week soak success
python scripts/validation/validate_soak_period.py --phase PHASE_3 --duration 14 --output .state/evidence/PH-008/soak_validation.json

# Generate stability report
python scripts/execution/generate_stability_report.py --input .state/evidence/PH-008/ --output REPORTS/phase3_stability_report.md
```

### Success Criteria (ALL MUST PASS):
- [x] Zero critical errors for 14 days
- [x] All performance targets met
- [x] No data integrity issues
- [x] No user-reported critical issues
- [x] Weekly reports submitted and approved
- [x] Stakeholder approval obtained

### If All Criteria Met:
✅ **Phase 3 soak successful**  
✅ **Ready to proceed to Phase 4 approval process**  
✅ **Document lessons learned**

### If Any Criteria Failed:
❌ **Rollback to Phase 2**  
❌ **Investigate and fix issues**  
❌ **Restart soak period after fixes**

---

## Monitoring Dashboards

### Key Metrics to Watch:
- Registry write latency
- Conflict detection rate
- Error rates (all severities)
- Data integrity checks
- System resource utilization
- User transaction success rate

### Alert Thresholds:
- **Critical:** Any data corruption, schema validation failures
- **High:** Error rate > 1%, latency > 200ms
- **Medium:** Warning rate > 5%, resource use > 80%

---

## Communication Plan

### Daily Updates:
- Morning: Post overnight summary to #ops-channel
- Evening: Post daily metrics summary

### Weekly Reports:
- Week 1: Detailed status report to stakeholders
- Week 2: Final status + recommendation

### Escalation Path:
1. On-call engineer
2. Technical Lead (richg@local)
3. Operations Manager
4. CTO (for rollback decisions)

---

## Evidence Archive

All evidence must be preserved:
- `.state/evidence/PH-008/` - All deployment and monitoring logs
- `REPORTS/phase3_week1_status.md` - Week 1 report
- `REPORTS/phase3_week2_status.md` - Week 2 report
- `REPORTS/phase3_stability_report.md` - Final stability report
- `backups/pre_phase3_full_backup.tar.gz` - Backup (retain 1 year)

---

## Final Approval

After successful 2-week soak:
- [ ] Technical Lead sign-off
- [ ] Operations Lead sign-off
- [ ] Stakeholder approval
- [ ] Evidence reviewed
- [ ] Ready for Phase 4 approval process (PH-OP-006)

---

*Runbook Version: 1.0*  
*Critical Phase - Review Before Each Execution*  
*Last Updated: 2026-02-08*
