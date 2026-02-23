#!/usr/bin/env python3
"""Generate migration guide documentation."""

import sys
from pathlib import Path
from datetime import datetime


MIGRATION_GUIDE = """# Schema Migration Guide

**Generated:** {timestamp}  
**Version:** 3.0

---

## Overview

This guide covers migrating from schema v2 to schema v3, which includes:
- Lifecycle state tracking
- SSOT field protection
- Enhanced ID validation patterns
- Merge conflict policies
- Execution baselines

---

## Migration Steps

### Step 1: Backup Current Data
```bash
python scripts/deployment/full_backup.py --output backups/pre_migration_backup.tar.gz --verify
```

### Step 2: Test Migration on Copy
```bash
python scripts/deployment/test_schema_migration.py \\
  --backup backups/pre_migration_backup.tar.gz \\
  --output .state/migration_test_results.json
```

### Step 3: Update Schema Files
```bash
python scripts/update_schema_lifecycle_states.py \\
  --schema schemas/artifact.schema.json \\
  --output schemas/artifact.schema.v3.json

python scripts/strengthen_id_patterns.py \\
  --schema schemas/artifact.schema.v3.json \\
  --output schemas/artifact.schema.v3.json

python scripts/annotate_ssot_fields.py \\
  --schema schemas/artifact.schema.v3.json \\
  --fields artifact_id,cas_hash,created_at \\
  --output schemas/artifact.schema.v3.json
```

### Step 4: Generate Validators
```bash
python scripts/generate_lifecycle_validator.py --output validators/lifecycle_validator.py
python scripts/generate_ssot_validator.py --output validators/ssot_validator.py
python scripts/generate_drift_validator.py --output validators/drift_validator.py
```

### Step 5: Migrate Production Data

⚠️ **WARNING: This step is irreversible after commit**

```bash
# Enable Phase 3 migration
python scripts/deployment/enable_migration_phase.py --phase PHASE_3_REGISTRY

# Monitor migration
python scripts/deployment/monitor_production.py \\
  --phase PHASE_3_REGISTRY \\
  --duration-hours 1 \\
  --output .state/migration_monitoring.json
```

### Step 6: Validate Migration
```bash
# Validate lifecycle states
python validators/lifecycle_validator.py production/registry.json

# Validate SSOT protection
python validators/ssot_validator.py \\
  backups/pre_migration_backup.json \\
  production/registry.json \\
  schemas/artifact.schema.v3.json

# Validate no drift
python validators/drift_validator.py \\
  .state/baseline.json \\
  .state/current_metrics.json
```

### Step 7: Begin Soak Period
```bash
python scripts/deployment/monitor_soak_period.py \\
  --phase PHASE_3_REGISTRY \\
  --duration-days 14 \\
  --output .state/evidence/PH-008/soak_period_results.json \\
  --weekly-reports REPORTS/
```

---

## Rollback Procedure

⚠️ **Only available during soak period (14 days)**

```bash
# Rollback to Phase 2
python scripts/deployment/rollback_deployment.py \\
  --phase PHASE_3_REGISTRY \\
  --backup-id latest \\
  --target PHASE_2_CORE

# Verify rollback
python scripts/validation/validate_phase_stability.py \\
  --phase PHASE_2_CORE \\
  --duration 24
```

---

## Schema Changes Summary

### New Fields

| Field | Type | Description |
|-------|------|-------------|
| `lifecycle_state` | string (enum) | Current lifecycle state |
| `lifecycle_history` | array | State transition history |
| `lifecycle_metadata` | object | Lifecycle tracking metadata |

### Enhanced Validations

| Field | Old Pattern | New Pattern |
|-------|-------------|-------------|
| `artifact_id` | None | `^ART-[0-9]{{14}}-[A-Z0-9]{{8}}$` |
| `phase_id` | None | `^PH-[A-Z]+-[0-9]{{3}}$` |
| `gate_id` | None | `^GATE-[0-9]{{3}}$` |

### SSOT Protected Fields

These fields cannot be modified after creation:
- `artifact_id`
- `cas_hash`
- `created_at`
- `baseline_id`

---

## Validation Gates

All migration phases must pass these gates:

### GATE-001: Schema Compliance
- All artifacts conform to v3 schema
- No validation errors

### GATE-002: Data Integrity
- Record count unchanged
- No data loss
- Checksums match

### GATE-003: Backward Compatibility
- Legacy operations still function
- No breaking changes for clients

### GATE-004: Performance
- No performance degradation
- All benchmarks within targets

---

## Troubleshooting

### Issue: Validation Failures

**Symptoms:** Validator returns errors

**Solution:**
```bash
# Check specific validation
python validators/lifecycle_validator.py <file> --verbose

# Review error details
cat .state/validation_errors.log
```

### Issue: Migration Stuck

**Symptoms:** Migration hangs or times out

**Solution:**
1. Check logs: `monitoring/logs/migration.log`
2. Verify no lock conflicts
3. Consider rollback if unrecoverable

### Issue: Performance Degradation

**Symptoms:** Slow operations after migration

**Solution:**
```bash
# Profile operations
python -m cProfile -o migration.stats <operation>

# Compare with baseline
python validators/drift_validator.py baseline.json current.json
```

---

## Post-Migration Tasks

### Week 1
- [ ] Daily monitoring reviews
- [ ] Weekly stakeholder report
- [ ] Document any issues

### Week 2
- [ ] Daily monitoring reviews
- [ ] Weekly stakeholder report
- [ ] Prepare Phase 4 approval package

### Week 3+
- [ ] Generate stability report
- [ ] Request Phase 4 approval
- [ ] Plan Phase 4 deployment

---

## Support

For migration support:
- **Technical Issues:** Check `docs/runbooks/troubleshooting_guide.md`
- **Emergency:** Run rollback procedure
- **Questions:** Review `docs/api_reference.md`

---

*Migration guide generated by generate_migration_guide.py*
"""


def generate_migration_guide(output_path):
    """Generate comprehensive migration guide."""
    print(f"Generating Migration Guide")
    print("=" * 70)
    
    content = MIGRATION_GUIDE.format(
        timestamp=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    )
    
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✓ Migration guide generated: {output_path}")
    print(f"  Includes:")
    print(f"    - 7-step migration process")
    print(f"    - Rollback procedures")
    print(f"    - Schema change summary")
    print(f"    - Troubleshooting guide")
    print("=" * 70)
    return 0


if __name__ == '__main__':
    output = sys.argv[1] if len(sys.argv) > 1 else 'docs/SCHEMA_MIGRATION_GUIDE.md'
    sys.exit(generate_migration_guide(output))
