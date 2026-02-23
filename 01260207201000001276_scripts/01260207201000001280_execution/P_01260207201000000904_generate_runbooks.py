#!/usr/bin/env python3
"""Generate operational runbooks for system maintenance and troubleshooting."""

import sys
from pathlib import Path
from datetime import datetime


RUNBOOKS = {
    'deployment': {
        'title': 'Deployment Runbook',
        'content': '''# Deployment Runbook

## Overview
This runbook covers standard deployment procedures for the Gov_Reg system.

## Prerequisites
- [ ] All tests passing
- [ ] Code reviewed and approved
- [ ] Backup completed
- [ ] Maintenance window scheduled

## Pre-Deployment Steps

### 1. Verify Environment
```bash
python --version  # Should be 3.11+
git status
pytest tests/ -v
```

### 2. Create Backup
```bash
python scripts/deployment/full_backup.py --output backups/pre_deploy_backup.tar.gz --verify
```

### 3. Run Pre-flight Checks
```bash
python scripts/validation/validate_pre_migration_checklist.py
```

## Deployment Steps

### 1. Deploy to Staging
```bash
python scripts/deployment/deploy_module.py --module <module_name> --target staging
```

### 2. Monitor Staging
- Monitor for 2 hours
- Check error logs
- Verify functionality

### 3. Deploy to Production
```bash
python scripts/deployment/deploy_module.py --module <module_name> --target production
python scripts/deployment/enable_migration_phase.py --phase <phase_name>
```

### 4. Post-Deployment Monitoring
```bash
python scripts/deployment/monitor_production.py --phase <phase_name> --duration-hours 24
```

## Rollback Procedure

### If Issues Detected
```bash
python scripts/deployment/rollback_deployment.py --phase <phase_name> --backup-id latest
```

### Verify Rollback
```bash
python scripts/validation/validate_phase_stability.py --phase <previous_phase>
```

## Communication

### Stakeholders to Notify
- Engineering Team Lead
- Operations Manager
- Product Owner

### Notification Template
```
Subject: [DEPLOYMENT] <Phase Name> Deployment Status

Status: [SUCCESS/FAILURE]
Time: <timestamp>
Duration: <duration>
Issues: <none/list issues>
Next Steps: <actions>
```

## Troubleshooting

### Common Issues

**Issue:** Module fails to deploy
- Check permissions
- Verify dependencies
- Review error logs

**Issue:** Performance degradation
- Check monitoring dashboards
- Review resource usage
- Consider rollback

---
*Last Updated: 2026-02-08*
'''
    },
    'monitoring': {
        'title': 'Monitoring and Alerting Runbook',
        'content': '''# Monitoring and Alerting Runbook

## Overview
Procedures for monitoring system health and responding to alerts.

## Monitoring Dashboards

### Grafana Dashboards
- **Main Dashboard**: `monitoring/dashboards/main.json`
- **Performance Dashboard**: `monitoring/dashboards/performance.json`
- **Registry Dashboard**: `monitoring/dashboards/registry.json`

## Alert Response

### Critical Alerts

#### High Error Rate
**Severity:** Critical  
**Threshold:** >5% error rate

**Response Steps:**
1. Check error logs: `monitoring/logs/errors.log`
2. Identify error pattern
3. If widespread: initiate rollback
4. If isolated: investigate and patch

#### Performance Degradation
**Severity:** High  
**Threshold:** >500ms avg response time

**Response Steps:**
1. Check resource usage
2. Review recent changes
3. Scale resources if needed
4. Investigate bottlenecks

### Warning Alerts

#### Disk Space Low
**Severity:** Warning  
**Threshold:** <20% free space

**Response Steps:**
1. Identify large files/logs
2. Archive old backups
3. Clean temporary files
4. Plan capacity expansion

## Health Checks

### Daily Checks
```bash
# System health
python scripts/validation/validate_monitoring_system.py

# Performance metrics
python scripts/validation/validate_performance.py
```

### Weekly Checks
- Review dashboard trends
- Check backup integrity
- Review security logs
- Update documentation

---
*Last Updated: 2026-02-08*
'''
    },
    'troubleshooting': {
        'title': 'Troubleshooting Guide',
        'content': '''# Troubleshooting Guide

## Common Issues and Resolutions

### Registry Issues

#### Registry Lock Timeout
**Symptoms:** Registry operations timeout
**Diagnosis:**
```bash
# Check registry status
python -c "from govreg_core import registry; print(registry.get_status())"
```

**Resolution:**
1. Check for hung processes
2. Clear stale locks: `python scripts/maintenance/clear_locks.py`
3. Restart registry service if needed

### Validation Failures

#### Gate Check Failures
**Symptoms:** Gate validation returns non-zero exit code
**Diagnosis:**
```bash
# Run gate with verbose output
python scripts/validation/run_gate.py --gate-id <gate_id> --verbose
```

**Resolution:**
1. Review gate requirements
2. Check preconditions
3. Verify input data
4. Re-run after corrections

### Performance Issues

#### Slow Query Performance
**Symptoms:** Operations taking >1s
**Diagnosis:**
```bash
# Profile operation
python -m cProfile -o profile.stats scripts/operation.py
python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative'); p.print_stats(20)"
```

**Resolution:**
1. Identify bottleneck
2. Optimize query/operation
3. Add caching if appropriate
4. Consider indexing

## Emergency Procedures

### Complete System Failure
1. **Assess Scope**: Determine affected systems
2. **Communicate**: Notify stakeholders
3. **Investigate**: Check logs and monitoring
4. **Restore**: From most recent backup
5. **Verify**: Run validation suite
6. **Document**: Record incident details

### Data Corruption
1. **Stop Operations**: Prevent further corruption
2. **Assess Damage**: Identify corrupted data
3. **Restore Backup**: From last known good backup
4. **Verify Integrity**: Run validation checks
5. **Root Cause**: Investigate and fix cause

---
*Last Updated: 2026-02-08*
'''
    }
}


def generate_runbooks(output_dir):
    """Generate operational runbooks."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    generated_files = []
    
    for runbook_id, runbook_data in RUNBOOKS.items():
        filename = f"{runbook_id}_runbook.md"
        file_path = output_path / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(runbook_data['content'])
        
        generated_files.append(str(file_path))
        print(f"Generated: {filename}")
    
    # Generate index
    index_content = f"""# Operational Runbooks Index

**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

## Available Runbooks

"""
    
    for runbook_id, runbook_data in RUNBOOKS.items():
        filename = f"{runbook_id}_runbook.md"
        index_content += f"- [{runbook_data['title']}]({filename})\n"
    
    index_content += "\n---\n*Runbooks generated by generate_runbooks.py*\n"
    
    index_path = output_path / 'README.md'
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(index_content)
    
    generated_files.append(str(index_path))
    
    print(f"\nGenerated {len(generated_files)} runbook files in {output_dir}")
    return 0


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python generate_runbooks.py --output <output_dir>")
        sys.exit(1)
    
    output_dir = None
    
    for i, arg in enumerate(sys.argv):
        if arg == '--output' and i + 1 < len(sys.argv):
            output_dir = sys.argv[i + 1]
    
    if not output_dir:
        print("Error: --output is required")
        sys.exit(1)
    
    sys.exit(generate_runbooks(output_dir))
