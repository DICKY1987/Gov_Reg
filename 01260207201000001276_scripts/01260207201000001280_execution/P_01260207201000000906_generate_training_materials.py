#!/usr/bin/env python3
"""Generate training materials for team education."""

import sys
from pathlib import Path
from datetime import datetime


TRAINING_MATERIALS = {
    'system_overview': {
        'title': 'Gov_Reg System Overview',
        'filename': 'system_overview.md',
        'content': '''# Gov_Reg System Overview

## Training Module 1: System Architecture

### Duration: 2 hours

### Learning Objectives
- Understand the Gov_Reg system architecture
- Learn about key components and their interactions
- Identify deployment phases and migration strategy

### System Architecture

#### Core Components

1. **Planning Engine**
   - Creates and validates execution plans
   - Manages phase dependencies
   - Coordinates step execution

2. **Registry System**
   - Maintains system state
   - Tracks artifacts and dependencies
   - Provides CAS-based versioning

3. **Validation Framework**
   - Runs validation gates
   - Checks preconditions/postconditions
   - Ensures data integrity

4. **Deployment Manager**
   - Orchestrates deployments
   - Manages rollback procedures
   - Monitors system health

### Migration Phases

| Phase | Description | Reversible |
|-------|-------------|------------|
| Phase 0 | Canonical Hash Module | Yes |
| Phase 1 | Registry Writer | Yes |
| Phase 2 | Conflict Validators | Yes |
| Phase 3 | Schema v3 Migration | Yes (during soak) |
| Phase 4+ | Production Optimization | No |

### Hands-On Exercise

**Exercise 1:** Explore the Registry
```bash
python -c "from govreg_core import registry; print(registry.get_all_artifacts())"
```

**Exercise 2:** Run a Validation Gate
```bash
python scripts/validation/validate_structure.py --plan-file sample_plan.json
```

### Quiz
1. What are the four core components?
2. Which phase is the last reversible point?
3. What does CAS stand for?

---
*Training Module 1 - Page 1 of 3*
'''
    },
    'operational_procedures': {
        'title': 'Operational Procedures',
        'filename': 'operational_procedures.md',
        'content': '''# Operational Procedures

## Training Module 2: Day-to-Day Operations

### Duration: 3 hours

### Learning Objectives
- Master common operational tasks
- Learn monitoring and alerting procedures
- Practice incident response

### Daily Operations

#### Morning Checklist
- [ ] Check system health dashboard
- [ ] Review overnight logs
- [ ] Verify backup completion
- [ ] Check pending alerts

#### Deployment Procedures

**Standard Deployment:**
```bash
# 1. Create backup
python scripts/deployment/backup_registry.py --verify

# 2. Deploy module
python scripts/deployment/deploy_module.py --module <name> --target production

# 3. Enable phase
python scripts/deployment/enable_migration_phase.py --phase <phase_name>

# 4. Monitor
python scripts/deployment/monitor_production.py --phase <phase_name> --duration-hours 24
```

#### Monitoring

**Key Metrics to Watch:**
- Error rate (<1% normal)
- Response time (<200ms avg)
- CPU usage (<70%)
- Memory usage (<80%)
- Disk space (>20% free)

**Dashboard Locations:**
- Main: `http://monitoring/dashboards/main`
- Performance: `http://monitoring/dashboards/performance`
- Registry: `http://monitoring/dashboards/registry`

### Incident Response

#### Severity Levels

**P1 - Critical:** System down, data loss risk
- Response time: Immediate
- Escalation: All hands

**P2 - High:** Degraded performance, errors increasing
- Response time: 15 minutes
- Escalation: On-call engineer

**P3 - Medium:** Minor issues, workarounds available
- Response time: 1 hour
- Escalation: During business hours

**P4 - Low:** Cosmetic issues, no impact
- Response time: Next business day
- Escalation: Regular ticket

#### Response Workflow

1. **Acknowledge:** Alert acknowledged within SLA
2. **Assess:** Determine scope and impact
3. **Mitigate:** Apply temporary fix if possible
4. **Resolve:** Implement permanent solution
5. **Document:** Record incident details
6. **Review:** Post-incident review

### Hands-On Exercise

**Scenario:** High error rate alert triggered

**Steps:**
1. Check error logs
2. Identify error pattern
3. Determine if rollback needed
4. Execute response plan
5. Document actions taken

### Certification

Complete the following to earn "Certified Gov_Reg Operator":
- [ ] Complete all training modules
- [ ] Pass operational quiz (80% minimum)
- [ ] Complete hands-on exercises
- [ ] Shadow experienced operator (4 hours)

---
*Training Module 2 - Page 2 of 3*
'''
    },
    'troubleshooting': {
        'title': 'Troubleshooting Guide',
        'filename': 'troubleshooting_guide.md',
        'content': '''# Troubleshooting Guide

## Training Module 3: Problem Resolution

### Duration: 2 hours

### Learning Objectives
- Diagnose common issues
- Apply troubleshooting methodology
- Use diagnostic tools effectively

### Troubleshooting Methodology

#### The 5-Step Process

1. **Define the Problem**
   - What is failing?
   - When did it start?
   - Who is affected?

2. **Gather Information**
   - Check logs
   - Review monitoring
   - Test reproduction

3. **Analyze Possible Causes**
   - Recent changes?
   - Resource constraints?
   - External factors?

4. **Test Solutions**
   - Try least risky first
   - Document each attempt
   - Roll back if worse

5. **Verify and Document**
   - Confirm resolution
   - Update runbooks
   - Share learnings

### Common Issues

#### Issue: Registry Lock Timeout

**Symptoms:**
- Operations hang
- "Lock timeout" errors

**Diagnosis:**
```bash
# Check lock status
python -c "from govreg_core import registry; print(registry.get_lock_status())"
```

**Resolution:**
```bash
# Clear stale locks
python scripts/maintenance/clear_locks.py --force
```

#### Issue: Validation Gate Failure

**Symptoms:**
- Gate returns non-zero exit code
- Validation errors in log

**Diagnosis:**
```bash
# Run with verbose output
python scripts/validation/run_gate.py --gate-id <id> --verbose
```

**Resolution:**
1. Review gate requirements
2. Check input data
3. Verify preconditions
4. Re-run after corrections

#### Issue: Performance Degradation

**Symptoms:**
- Slow response times
- Timeouts
- High resource usage

**Diagnosis:**
```bash
# Profile operation
python -m cProfile -o profile.stats <script.py>

# Analyze profile
python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative'); p.print_stats(20)"
```

**Resolution:**
1. Identify bottleneck
2. Optimize code path
3. Add caching if appropriate
4. Scale resources if needed

### Diagnostic Tools

**Log Analysis:**
```bash
# Search error logs
grep "ERROR" monitoring/logs/*.log

# Count error types
grep "ERROR" monitoring/logs/*.log | cut -d: -f3 | sort | uniq -c
```

**Resource Monitoring:**
```bash
# Check system resources
python scripts/monitoring/check_resources.py

# View real-time metrics
python scripts/monitoring/realtime_metrics.py --duration 60
```

### Practice Scenarios

**Scenario 1:** User reports "system is slow"
- What information do you gather first?
- Which diagnostic tools do you use?
- What are possible causes?

**Scenario 2:** Deployment fails midway
- How do you assess the situation?
- When do you rollback?
- How do you prevent recurrence?

### Final Assessment

Complete the troubleshooting challenge:
- Diagnose provided scenario
- Document your process
- Propose solution
- Present findings

---
*Training Module 3 - Page 3 of 3*
'''
    }
}


def generate_training_materials(output_dir):
    """Generate training materials."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    generated_files = []
    
    # Generate each training module
    for material_id, material_data in TRAINING_MATERIALS.items():
        file_path = output_path / material_data['filename']
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(material_data['content'])
        
        generated_files.append(str(file_path))
        print(f"Generated: {material_data['filename']}")
    
    # Generate training index
    index_content = f"""# Training Materials Index

**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

## Available Training Modules

"""
    
    for material_id, material_data in TRAINING_MATERIALS.items():
        index_content += f"### {material_data['title']}\n"
        index_content += f"- **File:** [{material_data['filename']}]({material_data['filename']})\n"
        index_content += f"- **Module:** {material_id}\n\n"
    
    index_content += """
## Training Schedule

### Week 1: Engineering Team
- Day 1: System Overview (Module 1)
- Day 2: Operational Procedures (Module 2)
- Day 3: Troubleshooting (Module 3)

### Week 2: Operations Team
- Day 1: System Overview (Module 1)
- Day 2: Operational Procedures (Module 2)
- Day 3: Troubleshooting (Module 3)

## Certification Requirements

To become a Certified Gov_Reg Operator:
1. Complete all three training modules
2. Pass operational quiz (80% minimum)
3. Complete hands-on exercises
4. Shadow experienced operator (4 hours minimum)

---
*Training materials generated by generate_training_materials.py*
"""
    
    index_path = output_path / 'README.md'
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(index_content)
    
    generated_files.append(str(index_path))
    
    print(f"\nGenerated {len(generated_files)} training files in {output_dir}")
    return 0


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python generate_training_materials.py --output <output_dir>")
        sys.exit(1)
    
    output_dir = None
    
    for i, arg in enumerate(sys.argv):
        if arg == '--output' and i + 1 < len(sys.argv):
            output_dir = sys.argv[i + 1]
    
    if not output_dir:
        print("Error: --output is required")
        sys.exit(1)
    
    sys.exit(generate_training_materials(output_dir))
