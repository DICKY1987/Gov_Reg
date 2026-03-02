# Planning-Only Refinement Loop CLI

**Version 2.0** | **Status: Beta** | **Template: v3.0.0**

A deterministic, auditable CLI tool for generating and refining structural implementation plans through iterative planner-critic cycles.

## Features

✅ **Deterministic by Default** - Works without LLM dependency  
✅ **Schema-Validated** - All artifacts conform to JSON schemas  
✅ **Policy-Driven** - Configurable rules and constraints  
✅ **Evidence-Tracked** - Full audit trail with SHA256 hashes  
✅ **RFC-6902 Patches** - Surgical, minimal plan modifications  
✅ **LangGraph Orchestrated** - Reliable state machine control  

## Quick Start

### Installation
```bash
pip install jsonschema>=4.21 jsonpatch>=1.33 click>=8.1 pyyaml>=6.0 rich>=13.7
```

### Basic Usage
```bash
# 1. Initialize planning run
python src/plan_refine_cli/main.py init \
  --policy config/baseline_planning_policy.json \
  --run-id planning_20260218T120000Z_abc12345

# 2. Generate context bundle
python src/plan_refine_cli/main.py context \
  --run-id planning_20260218T120000Z_abc12345 \
  --output .planning_loop_state/runs/planning_20260218T120000Z_abc12345/context_bundle.json

# 3. Generate plan skeleton
python src/plan_refine_cli/main.py skeleton \
  --run-id planning_20260218T120000Z_abc12345 \
  --context .planning_loop_state/runs/planning_20260218T120000Z_abc12345/context_bundle.json \
  --output .planning_loop_state/runs/planning_20260218T120000Z_abc12345/plan_skeleton.json

# 4. Run refinement loop
python src/plan_refine_cli/main.py loop \
  --run-id planning_20260218T120000Z_abc12345 \
  --context .planning_loop_state/runs/planning_20260218T120000Z_abc12345/context_bundle.json \
  --max-iterations 5 \
  --critic-mode DETERMINISTIC

# 5. Finalize and package
python src/plan_refine_cli/main.py finalize \
  --run-id planning_20260218T120000Z_abc12345 \
  --output-dir ./planning_output
```

## Architecture

### Directory Structure
```
.planning_loop_state/
├── runs/
│   └── {run_id}/
│       ├── manifest.json
│       ├── context_bundle.json
│       ├── policy_snapshot.json
│       ├── iterations/
│       │   ├── iter_000/plan.json
│       │   ├── iter_001/plan.json + patch.json
│       │   └── ...
│       ├── patches/
│       ├── critic_reports/
│       └── artifacts/
├── evidence/
│   └── {run_id}/{phase_id}/{step_id}/
└── metrics/
    └── metrics.jsonl
```

### Core Components

#### 1. Schemas (12)
- `PLAN.schema.json` - 14 required fields
- `CRITIC_REPORT.schema.json` - Hard/soft defects
- `PATCH.schema.json` - RFC-6902 patches
- `planning_policy_snapshot.schema.json` - Policy config
- 8 more supporting schemas

#### 2. CLI Commands (6)
- `init` - Initialize planning run
- `context` - Generate context bundle
- `skeleton` - Generate plan skeleton
- `lint` - Run critic analysis
- `loop` - Execute refinement loop
- `finalize` - Package results

#### 3. Agents (2)
- **PlannerAgent** - Generates skeletons and refinement patches
- **CriticAgent** - Analyzes plans for defects

#### 4. Linters (5)
- **CompletenessLinter** - Required sections check
- **SchemaComplianceLinter** - JSON schema validation
- **ForbiddenPatternsLinter** - Pattern scanning
- **ReferenceValidityLinter** - Artifact reference checks
- **AcceptanceCriteriaLinter** - Measurability validation

#### 5. Utilities
- **RunDirectoryManager** - State directory management
- **PolicyManager** - Policy loading and validation
- **ContextGenerator** - Repository context extraction
- **PatchApplicator** - RFC-6902 patch application
- **StalenessChecker** - Context freshness detection
- **TerminationChecker** - Loop termination logic
- **HashUtils** - SHA256 hashing
- **ValidationGates** - 3 built-in gates

## Configuration

### Baseline Policy
`config/baseline_planning_policy.json` provides default configuration:
- **Critic Mode**: DETERMINISTIC (no LLM required)
- **Max Iterations**: 5
- **Plateau Threshold**: 5% improvement required
- **Forbidden Patterns**: Vague language, placeholders
- **Required Sections**: 14 fields per PLAN.schema.json

### Customization
```json
{
  "iteration_limits": {
    "max_iterations": 10,
    "soft_defect_improvement_threshold": 0.1
  },
  "critic_mode": "HYBRID",
  "forbidden_patterns": [
    {
      "pattern_id": "CUSTOM-001",
      "regex": "\\bTBD\\b",
      "reason": "Incomplete content"
    }
  ]
}
```

## Validation

### Pre-Implementation Checks
```bash
python scripts/P_01260207201000000005_validate_dependencies.py  # Check packages
python scripts/P_01260207201000000004_validate_all_schemas.py   # Validate schemas
python scripts/check_resources.py        # Check RAM/disk
python scripts/check_permissions.py      # Check permissions
```

### Test Suite
```bash
pytest tests/ -v                         # Run all tests
pytest tests/test_schemas.py -v          # Schema tests only
pytest tests/test_planning_loop.py -v    # Core module tests
```

## Exit Codes

- `0` - Success
- `1` - Validation error
- `2` - Execution error
- `3` - Manual escalation required

## Evidence Artifacts

All operations generate evidence in `.planning_loop_state/evidence/`:
- Schema validation reports
- Dependency check results
- Resource validation
- Permission checks
- Staleness reports
- Termination decisions

## Development Status

### ✅ Implemented (67%)
- Core infrastructure (schemas, CLI, agents)
- Deterministic critic with 5 linters
- Policy management
- Validation framework
- Test suite (12 tests passing)

### 🚧 In Progress (33%)
- LLM integration (placeholder)
- Additional validation gates (21 more planned)
- Integration examples
- Performance optimization

### 📋 Roadmap
- **Week 9**: Integration testing
- **Week 10**: Documentation completion
- **Week 11**: Performance tuning
- **Week 12**: Production readiness validation

## Contributing

Follow the implementation plan in:
`01260207201000001139_docs/01260207201000001145_planning/PLANNING_LOOP_IMPLEMENTATION_PLAN.md`

## License

Internal use only - Gov_Reg project
