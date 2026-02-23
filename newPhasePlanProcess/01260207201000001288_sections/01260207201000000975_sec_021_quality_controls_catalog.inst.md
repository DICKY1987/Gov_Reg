# SEC-021: Quality Controls Catalog

## Purpose

This section defines the **Single Source of Truth (SSOT)** for proactive quality controls derived from DBG debugging topics. Instead of debugging issues after they occur, controls are enforced at planning time via the G-CTRL-001 gate.

## Key Concepts

### Control Classes

Controls are classified into categories that map to DBG topic areas:

| Class | Description | Example Controls |
|-------|-------------|------------------|
| `security` | Input validation, secrets management, access control | CTRL-SEC-001, CTRL-SEC-002 |
| `testing` | Coverage thresholds, test quality, regression prevention | CTRL-TST-001 |
| `validation` | Schema compliance, data integrity, format validation | CTRL-VAL-001 |
| `architecture` | Dependency management, module boundaries, design patterns | CTRL-ARC-001 |
| `observability` | Logging, metrics, tracing requirements | (future) |
| `deployment` | CI/CD gates, environment parity, rollback capability | (future) |
| `documentation` | API docs, changelog, decision records | (future) |

### Control Structure

Each control MUST define:

1. **control_id**: Unique identifier (format: `CTRL-{CLASS}-{SEQ}`)
2. **class**: One of the defined control classes
3. **enforcement**: Gate ID + validation command + expected output
4. **evidence_requirements**: Artifact paths using deterministic formulas
5. **severity**: `critical`, `high`, `medium`, `low`

### Enforcement Policy

The **G-CTRL-001** gate enforces control coverage:

1. For each phase in the plan, identify required controls from `control_mappings.by_phase`
2. For each required control, verify a satisfying gate exists in the plan's gates
3. Fail with specific error code if any control is unsatisfied

## Error Codes

| Code | Meaning | Remediation |
|------|---------|-------------|
| `CTRL001_MISSING_SATISFYING_GATE` | Control requires a gate but none found | Add the required gate to the plan |
| `CTRL001_MISSING_EVIDENCE_MAPPING` | Control requires evidence but path not defined | Define evidence path in gate output |
| `CTRL001_UNSATISFIED_CONTROL` | Control gate did not pass | Fix the underlying issue and re-run |
| `CTRL001_INVALID_CONTROL_ID` | Referenced control_id not in catalog | Use valid control_id from catalog |

## Adding New Controls

To add a new control:

1. Choose appropriate `control_id` following naming convention
2. Define enforcement with structured command (exe + args, not free-form string)
3. Define evidence path using formula variables: `{{PHASE}}`, `{{CONTROL_ID}}`, `{{ARTIFACT_NAME}}`
4. Add to `control_mappings.by_phase` for relevant phases
5. Add to `control_mappings.by_gate` linking to enforcement gate
6. Run `python validators/validate_sec_021.py sections/sec_021_quality_controls_catalog.json` to validate

## Validation

```bash
# Validate SEC-021 structure
python validators/validate_sec_021.py sections/sec_021_quality_controls_catalog.json

# Expected output:
# control_id_uniqueness: true
# all_required_fields_present: true
# evidence_paths_deterministic: true
# status: pass
```

## Integration Points

- **SEC-012**: G-CTRL-001 gate added to validation_gates
- **SEC-009**: Tool entries for control-required tools (bandit, semgrep, etc.)
- **SEC-010**: Task schema includes `controls` field
- **SEC-011**: Artifact schema includes `required_by_controls` field
- **SEC-016**: `control_test_mapping` links controls to test suites
