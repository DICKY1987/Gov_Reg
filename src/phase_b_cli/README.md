# Phase B: Execution Compilation CLI

Transforms validated Phase A plans into executable compilation packages.

## Installation

```bash
cd C:\Users\richg\Gov_Reg
pip install -e src/phase_b_cli
```

## Commands

### B1: validate
Pre-flight check that Phase A plan is execution-ready.

```bash
python -m phase_b_cli.cli validate --run-id phaseA_20260217T120102Z_...
```

**Gates:**
- G13: Termination record exists; reason == "NO_HARD_DEFECTS"
- G14: All Phase A artifacts pass LIV
- G15: Final plan schema-valid

### B2: compile
Generate execution compilation package from validated plan.

```bash
python -m phase_b_cli.cli compile --run-id phaseA_20260217T120102Z_...
```

**Flags:**
- `--parallel-detection auto|none` - Detect independent tasks (default: auto)
- `--max-task-duration SECONDS` - Task duration limit (default: 3600)
- `--harness-lang sh|py` - Test harness language (default: sh)

**Gates:**
- G16-G19, G22-G23

### B3: preview
Generate human-readable execution plan preview.

```bash
python -m phase_b_cli.cli preview --run-id phaseA_20260217T120102Z_... --format markdown
```

**Formats:**
- `markdown` - Human-readable markdown
- `mermaid` - Dependency graph
- `json` - Structured JSON

### B4: package
Bundle all Phase B artifacts into deployable archive.

```bash
python -m phase_b_cli.cli package --run-id phaseA_20260217T120102Z_...
```

**Flags:**
- `--archive-format tar.gz|zip` - Archive format (default: tar.gz)
- `--include-lineage` - Include Phase A artifacts (default: true)

## Example Workflow

```bash
# 1. Validate Phase A plan
python -m phase_b_cli.cli validate --run-id phaseA_20260217T120102Z_abc123

# 2. Compile execution package
python -m phase_b_cli.cli compile --run-id phaseA_20260217T120102Z_abc123

# 3. Preview (optional)
python -m phase_b_cli.cli preview --run-id phaseA_20260217T120102Z_abc123 --format markdown

# 4. Package for deployment
python -m phase_b_cli.cli package --run-id phaseA_20260217T120102Z_abc123
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 2 | CLI usage/parsing error |
| 10 | Validation error (schema invalid, missing input, policy violation, gate failure) |
| 11 | LIV failure (hash mismatch / provenance mismatch) |
| 13 | Internal error (unexpected exception) |

## Directory Structure

```
.acms_runs/{phase_a_run_id}/
├── phase_b_linkage.json
├── artifacts/
│   └── phase/
│       └── PHASE_B/
│           ├── validate/
│           │   └── phase_b_validation_report.json
│           ├── compile/
│           │   ├── execution_plan.json
│           │   ├── execution_manifest.json
│           │   ├── task_specs/
│           │   ├── test_harness.sh
│           │   └── rollback_plan.json
│           ├── preview/
│           │   └── execution_preview.md
│           └── package/
│               └── phase_b_execution_package_*.tar.gz
```

## Version

1.0.0 - Initial implementation
