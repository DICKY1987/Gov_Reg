#!/usr/bin/env python3
"""Update AI instructions with schema migration guidance."""

import sys
from pathlib import Path
from datetime import datetime


AI_INSTRUCTIONS = """# AI Instructions for Schema Migration

**Updated:** {timestamp}  
**Context:** Track C Infrastructure Automation Complete

---

## Schema v3 Migration Context

The system has migrated to Schema v3 which includes:

### Lifecycle State Tracking
- All artifacts now have `lifecycle_state` field
- Valid states: DRAFT, PROPOSED, APPROVED, DEPLOYED, MONITORING, STABLE, DEPRECATED, ARCHIVED
- State transitions are tracked in `lifecycle_history`
- Use `validators/lifecycle_validator.py` to validate states

### SSOT Protection
- Certain fields are marked as Single Source of Truth (SSOT)
- SSOT fields: `artifact_id`, `cas_hash`, `created_at`, `baseline_id`
- These fields cannot be modified after creation
- Use `validators/ssot_validator.py` to enforce protection

### Enhanced ID Validation
- IDs now follow strict patterns:
  - `artifact_id`: `ART-YYYYMMDDHHmmSS-XXXXXXXX`
  - `phase_id`: `PH-XXXXX-NNN`
  - `gate_id`: `GATE-NNN`
  - `baseline_id`: `BASELINE-YYYYMMDDHHmmSS`

### Merge Conflict Policies
- Conflicts resolved via policy-based strategies
- Strategies: NEWEST_WINS, MANUAL, MERGE_ARRAY, SSOT_PROTECTED
- Use `validators/merge_resolver.py` for conflict resolution

### Execution Baselines
- Performance baselines tracked per phase
- Drift detection monitors deviation from baseline
- Use `validators/drift_validator.py` to check drift

---

## When Working With Artifacts

### Creating New Artifacts
```python
artifact = {{
    "artifact_id": f"ART-{{timestamp}}-{{random_id}}",
    "lifecycle_state": "DRAFT",
    "lifecycle_history": [],
    "lifecycle_metadata": {{
        "created_at": datetime.utcnow().isoformat() + 'Z'
    }},
    # ... other fields
}}
```

### Transitioning States
```python
# Valid transitions
transitions = {{
    "DRAFT": ["PROPOSED", "ARCHIVED"],
    "PROPOSED": ["APPROVED", "DRAFT"],
    "APPROVED": ["DEPLOYED", "PROPOSED"],
    "DEPLOYED": ["MONITORING", "APPROVED"],
    "MONITORING": ["STABLE", "DEPLOYED"],
    "STABLE": ["DEPRECATED"],
    "DEPRECATED": ["ARCHIVED"],
    "ARCHIVED": []
}}

# Record transition
artifact['lifecycle_history'].append({{
    "from_state": current_state,
    "to_state": new_state,
    "timestamp": datetime.utcnow().isoformat() + 'Z',
    "reason": "Phase completion",
    "approved_by": "system"
}})
artifact['lifecycle_state'] = new_state
```

### Validating Artifacts
```bash
# Lifecycle validation
python validators/lifecycle_validator.py artifact.json

# SSOT validation (after modification)
python validators/ssot_validator.py original.json modified.json schemas/artifact.schema.v3.json

# Drift validation
python validators/drift_validator.py baseline.json current.json
```

---

## Available Automation Scripts

### Execution Scripts (scripts/execution/)
- `identify_integration_points.py` - Find module integration points
- `generate_integration_tests.py` - Create integration test suites
- `generate_benchmarks.py` - Create performance benchmarks
- `generate_performance_report.py` - Report generation
- `generate_api_docs.py` - API documentation
- `generate_runbooks.py` - Operational runbooks
- `generate_approval_package.py` - Approval documentation
- `record_approval_decision.py` - Record committee decision
- `generate_training_materials.py` - Training content
- `record_training_session.py` - Attendance tracking
- `generate_stability_report.py` - Phase stability report
- `record_approval_meeting.py` - Meeting minutes
- `record_final_approval.py` - Final approval record

### Validation Scripts (scripts/validation/)
- `validate_performance.py` - Performance benchmark validation
- `review_documentation.py` - Documentation completeness review
- `validate_documentation.py` - Documentation validation
- `validate_pre_migration_checklist.py` - Pre-deployment checklist
- `validate_approval_status.py` - Approval status check
- `validate_phase_stability.py` - Phase stability validation
- `validate_soak_period.py` - Soak period completion
- `validate_monitoring_system.py` - Monitoring system check
- `validate_training_completion.py` - Training completion
- `validate_phase4_approval.py` - Phase 4 approval validation

### Deployment Scripts (scripts/deployment/)
- `deploy_module.py` - Deploy module to environment
- `enable_migration_phase.py` - Enable migration phase
- `monitor_production.py` - Production monitoring
- `backup_registry.py` - Registry backup
- `full_backup.py` - Full system backup
- `restore_from_backup.py` - Restore from backup
- `rollback_deployment.py` - Rollback deployment
- `test_schema_migration.py` - Test migration
- `monitor_soak_period.py` - Soak period monitoring
- `generate_prometheus_config.py` - Prometheus config
- `generate_grafana_dashboards.py` - Grafana dashboards
- `generate_alert_rules.py` - Alert rules

### Schema Enhancement Scripts (scripts/)
- `update_schema_lifecycle_states.py` - Add lifecycle tracking
- `generate_lifecycle_validator.py` - Lifecycle validator
- `update_template_lifecycle.py` - Update templates
- `add_execution_baseline_schema.py` - Baseline schema
- `generate_drift_validator.py` - Drift validator
- `annotate_ssot_fields.py` - Mark SSOT fields
- `generate_ssot_validator.py` - SSOT validator
- `strengthen_id_patterns.py` - Enhance ID patterns
- `add_merge_policies_schema.py` - Merge policy schema
- `generate_merge_resolver.py` - Merge resolver
- `generate_metric_validator.py` - Metric validator
- `add_gate_dependency.py` - Gate dependencies
- `generate_migration_guide.py` - Migration guide
- `update_ai_instructions.py` - AI instruction updates

---

## Common Workflows

### Workflow 1: Deploy New Phase
```bash
# 1. Create backup
python scripts/deployment/full_backup.py --output backups/backup.tar.gz --verify

# 2. Validate pre-migration checklist
python scripts/validation/validate_pre_migration_checklist.py --output .state/checklist.json

# 3. Deploy module
python scripts/deployment/deploy_module.py --module <name> --target production

# 4. Enable phase
python scripts/deployment/enable_migration_phase.py --phase <phase>

# 5. Monitor
python scripts/deployment/monitor_production.py --phase <phase> --duration-hours 24 --output monitoring.json
```

### Workflow 2: Generate Phase Reports
```bash
# 1. Generate performance report
python scripts/execution/generate_performance_report.py \\
  --input benchmarks.json --output performance_report.md

# 2. Generate stability report
python scripts/execution/generate_stability_report.py \\
  --input .state/evidence/PH-008/ --output stability_report.md

# 3. Generate approval package
python scripts/execution/generate_approval_package.py \\
  --output approval_package.md
```

### Workflow 3: Validate Migration
```bash
# 1. Validate lifecycle states
python validators/lifecycle_validator.py production/registry.json

# 2. Validate SSOT protection
python validators/ssot_validator.py backup.json current.json schema.json

# 3. Validate performance drift
python validators/drift_validator.py baseline.json current.json

# 4. Validate monitoring
python scripts/validation/validate_monitoring_system.py
```

---

## Best Practices

1. **Always backup before operations**
   - Use `full_backup.py --verify`
   - Store backups with timestamps

2. **Validate before and after**
   - Run validators before deployment
   - Revalidate after changes

3. **Monitor continuously**
   - Use soak period monitoring
   - Watch for drift from baseline

4. **Document everything**
   - Generate reports automatically
   - Record decisions in evidence

5. **Follow lifecycle states**
   - Respect state transition rules
   - Never skip required states

---

*AI instructions generated by update_ai_instructions.py*
*Last updated: {timestamp}*
"""


def update_ai_instructions(output_path):
    """Generate/update AI instructions."""
    print(f"Updating AI Instructions")
    print("=" * 70)
    
    content = AI_INSTRUCTIONS.format(
        timestamp=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    )
    
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✓ AI instructions updated: {output_path}")
    print(f"  Includes:")
    print(f"    - Schema v3 context")
    print(f"    - All 49 automation scripts")
    print(f"    - Common workflows")
    print(f"    - Best practices")
    print("=" * 70)
    return 0


if __name__ == '__main__':
    output = sys.argv[1] if len(sys.argv) > 1 else 'docs/AI_INSTRUCTIONS.md'
    sys.exit(update_ai_instructions(output))
