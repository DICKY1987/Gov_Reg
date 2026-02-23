# Monitoring & Training Runbook

**Phase:** Monitoring Setup & Team Training (PH-OP-005)  
**Duration:** 14 days (Week 7-9)  
**Priority:** HIGH

---

## Overview

Configure production monitoring systems and conduct comprehensive team training on the new Gov_Reg system.

---

## Part 1: Monitoring Setup (Week 7)

### Step 1: Configure Prometheus Metrics

#### Setup Commands:
```powershell
# Generate Prometheus configuration
python scripts/deployment/generate_prometheus_config.py --output monitoring/prometheus_config.yml

# Validate configuration
python scripts/deployment/validate_prometheus_config.py --config monitoring/prometheus_config.yml

# Deploy to monitoring server
python scripts/deployment/deploy_monitoring.py --component prometheus --config monitoring/prometheus_config.yml
```

#### Metrics to Collect:
- **Registry Operations:**
  - registry_write_duration_seconds
  - registry_read_duration_seconds
  - registry_validation_errors_total
  
- **PFMS Operations:**
  - pfms_generation_duration_seconds
  - pfms_ingestion_duration_seconds
  - pfms_conflicts_detected_total
  
- **Phase Tracking:**
  - migration_phase_current (gauge)
  - phase_transition_total (counter)
  
- **System Health:**
  - govreg_errors_total (by severity)
  - govreg_api_requests_total
  - govreg_cache_hit_ratio

#### Success Criteria:
- ✓ Prometheus scraping metrics successfully
- ✓ All metric endpoints responding
- ✓ Historical data collection working

---

### Step 2: Create Grafana Dashboards

#### Setup Commands:
```powershell
# Generate Grafana dashboard definitions
python scripts/deployment/generate_grafana_dashboards.py --output monitoring/dashboards/

# Import dashboards
python scripts/deployment/import_grafana_dashboards.py --source monitoring/dashboards/ --grafana-url http://grafana.local
```

#### Dashboards to Create:

**1. Overview Dashboard**
- Current migration phase
- Error rate (24h)
- Request volume
- System health status

**2. Registry Operations Dashboard**
- Write/read latency (p50, p95, p99)
- Validation error rate
- Conflict detection rate
- Registry size metrics

**3. PFMS Dashboard**
- PFMS generation rate
- Ingestion success rate
- Mutation statistics
- Content hash verification

**4. Performance Dashboard**
- API response times
- Database query performance
- Cache hit ratios
- Resource utilization

**5. Alerts Dashboard**
- Active alerts
- Alert history
- Silenced alerts
- Escalation status

#### Success Criteria:
- ✓ All dashboards rendering correctly
- ✓ Real-time data displaying
- ✓ Historical data accessible

---

### Step 3: Configure Critical Alerts

#### Alert Rules:
```powershell
# Generate alert rules
python scripts/deployment/generate_alert_rules.py --severity critical --output monitoring/alerts/critical.yml

# Deploy alerts
python scripts/deployment/deploy_alert_rules.py --rules monitoring/alerts/critical.yml
```

#### Critical Alerts:

**1. Data Integrity Alerts:**
- Registry validation failure (CRITICAL)
- Content hash mismatch (CRITICAL)
- Data corruption detected (CRITICAL)

**2. Performance Alerts:**
- API latency > 1s for 5 minutes (HIGH)
- Error rate > 5% (HIGH)
- Database connection failures (CRITICAL)

**3. System Alerts:**
- Service down (CRITICAL)
- Disk space < 10% (HIGH)
- Memory usage > 90% (HIGH)

**4. Phase Transition Alerts:**
- Unauthorized phase transition attempt (CRITICAL)
- Phase gate failure (HIGH)

#### Alert Routing:
```yaml
critical:
  pagerduty: on-call-team
  email: ops-team@company.com
  slack: #ops-alerts

high:
  email: ops-team@company.com
  slack: #ops-alerts

medium:
  slack: #ops-monitoring
```

#### Success Criteria:
- ✓ Alerts triggering correctly
- ✓ Notifications routing properly
- ✓ Test alerts received

---

## Part 2: Team Training (Week 8-9)

### Training Materials Preparation

```powershell
# Generate training materials
python scripts/execution/generate_training_materials.py --output training/materials/

# Create training environment
python scripts/training/setup_training_env.py --isolated
```

#### Materials Created:
- `training/materials/01_overview.pptx`
- `training/materials/02_architecture.pdf`
- `training/materials/03_operations.pdf`
- `training/materials/04_troubleshooting.pdf`
- `training/materials/05_hands_on_labs.pdf`
- `training/materials/exercises/` - Practical exercises

---

### Engineering Team Training (3 days)

#### Day 1: Architecture & Core Concepts

**Morning (9 AM - 12 PM):**
- System architecture overview
- Migration phases explained
- Core modules deep dive
- Q&A session

**Afternoon (1 PM - 4 PM):**
- Hands-on: Setting up dev environment
- Walkthrough: govreg_core modules
- Lab: Running integration tests
- Lab: Using canonical hash functions

#### Day 2: Development & Integration

**Morning (9 AM - 12 PM):**
- PFMS generation and ingestion
- Registry operations
- Conflict detection and resolution
- Feature flags and phase control

**Afternoon (1 PM - 4 PM):**
- Hands-on: Creating PFMS files
- Lab: Registry read/write operations
- Lab: Handling conflicts
- Code review best practices

#### Day 3: Testing & Deployment

**Morning (9 AM - 12 PM):**
- Integration testing strategies
- Performance benchmarking
- Deployment procedures
- Rollback procedures

**Afternoon (1 PM - 4 PM):**
- Hands-on: Writing integration tests
- Lab: Deployment simulation
- Lab: Rollback execution
- Final assessment

**Attendance Tracking:**
```powershell
# Record training session
python scripts/execution/record_training_session.py --team engineering --output training/attendance/engineering.json
```

---

### Operations Team Training (3 days)

#### Day 1: Operations Overview

**Morning (9 AM - 12 PM):**
- System deployment overview
- Migration phase management
- Monitoring and alerting
- Incident response procedures

**Afternoon (1 PM - 4 PM):**
- Hands-on: Navigating Grafana dashboards
- Lab: Alert response procedures
- Lab: Log analysis
- Incident escalation practice

#### Day 2: Deployment Operations

**Morning (9 AM - 12 PM):**
- Phase 0-2 deployment procedures
- Phase 3 critical deployment
- Backup and restore operations
- Health checks and validation

**Afternoon (1 PM - 4 PM):**
- Hands-on: Executing deployments (staging)
- Lab: Creating backups
- Lab: Restore procedures
- Lab: Validation scripts

#### Day 3: Troubleshooting & Maintenance

**Morning (9 AM - 12 PM):**
- Common issues and solutions
- Performance troubleshooting
- Data integrity checks
- Emergency procedures

**Afternoon (1 PM - 4 PM):**
- Hands-on: Troubleshooting scenarios
- Lab: Performance investigation
- Lab: Emergency rollback
- Final assessment

**Attendance Tracking:**
```powershell
# Record training session
python scripts/execution/record_training_session.py --team operations --output training/attendance/operations.json
```

---

## Training Assessment

### Knowledge Check:
- Pre-training assessment (baseline)
- Mid-training check (Day 2)
- Final assessment (Day 3)

### Passing Criteria:
- Attendance: 100% required
- Final assessment: >80% score
- Hands-on labs: All completed

### Certification:
Upon successful completion:
- Certificate of completion
- Access to production systems
- On-call rotation eligibility

---

## Post-Training Support

### Resources:
- Documentation: docs/
- Runbooks: docs/runbooks/
- API Reference: docs/api_reference.md
- Slack channel: #govreg-support

### Office Hours:
- Week 1 post-training: Daily 2-4 PM
- Week 2-4 post-training: Mon/Wed/Fri 2-4 PM

---

## Validation

### Monitoring Validation:
```powershell
# Validate monitoring system
python scripts/validation/validate_monitoring_system.py --output .state/evidence/PH-009/monitoring_validation.json
```

**Success Criteria:**
- [x] Prometheus collecting metrics
- [x] Grafana dashboards operational
- [x] Alerts configured and tested
- [x] On-call rotation configured

### Training Validation:
```powershell
# Validate training completion
python scripts/validation/validate_training_completion.py --output .state/evidence/PH-010/training_validation.json
```

**Success Criteria:**
- [x] Engineering team: >80% attendance & passing
- [x] Operations team: >80% attendance & passing
- [x] All labs completed
- [x] Assessments passed

---

## Evidence Archive

- `monitoring/prometheus_config.yml` - Prometheus config
- `monitoring/dashboards/` - Grafana dashboards
- `monitoring/alerts/critical.yml` - Alert rules
- `training/materials/` - Training content
- `training/attendance/engineering.json` - Engineering attendance
- `training/attendance/operations.json` - Operations attendance
- `.state/evidence/PH-009/` - Monitoring setup evidence
- `.state/evidence/PH-010/` - Training completion evidence

---

## Sign-Off

### Monitoring Setup:
- [ ] Monitoring systems operational
- [ ] All dashboards created
- [ ] Alerts configured and tested
- [ ] Documentation complete

### Training Completion:
- [ ] Engineering team trained (>80%)
- [ ] Operations team trained (>80%)
- [ ] Assessments completed
- [ ] Certifications issued

---

*Runbook Version: 1.0*  
*Last Updated: 2026-02-08*
