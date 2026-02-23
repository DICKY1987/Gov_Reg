---
doc_id: DOC-GUIDE-EXECUTION-PATTERN-DATA-FLOW-VALIDATION-154
---

# Execution Pattern: Data Flow Validation (EXEC-DATAFLOW-001)

**Pattern ID**: EXEC-DATAFLOW-001
**Created**: 2025-11-27
**Status**: ACTIVE
**Task Type**: Validate data flows from system diagrams
**Trigger**: N ≥ 5 data flows or modules to validate

---

## 1. Pattern Overview

### Purpose
Systematically validate that all data flows described in system diagrams exist in the codebase and function as designed.

### Success Criteria (Ground Truth)
- [ ] All referenced modules/files exist (file.exists())
- [ ] All referenced functions/classes exist (import succeeds)
- [ ] All data flow paths are importable
- [ ] All critical integrations have evidence (tests, imports, usage)

### Anti-Pattern Guards Enabled
- ✅ Hallucination of Success (verify programmatically)
- ✅ Silent Failures (explicit error handling)
- ✅ Incomplete Implementation (no TODO placeholders)
- ✅ Planning Loop (max 2 iterations)
- ✅ Approval Loop (no human approval for file checks)

---

## 2. Validation Template

```python
# Template for validating each data flow component
validation_item = {
    "component": "schema/validation",
    "diagram_reference": "Line 21-23",
    "checks": [
        {"type": "directory_exists", "path": "schema/"},
        {"type": "files_exist", "pattern": "schema/**/*.json"},
        {"type": "python_module", "import": "core.planner"},
        {"type": "function_exists", "module": "core.planner", "function": "validate_schema"}
    ],
    "ground_truth": "schema/ directory exists AND at least 1 .json file exists"
}
```

---

## 3. Batch Structure

### Batch Size: 8 components per batch

**Batch 1: Input Layer (Lines 10-25)**
- Workstream input
- PM Epic input
- Manual Spec input
- Schema validation
- Config/templates loading

**Batch 2: Core Planning Layer (Lines 26-47)**
- core/planner
- Decomposition
- core/scheduler
- Dependency resolution
- engine/queue

**Batch 3: Execution Layer (Lines 48-85)**
- Task routing
- engine/adapters (aider, claude, copilot)
- aim/ tool registry
- Execution phase
- Error detection

**Batch 4: State Management (Lines 86-106)**
- state/ runtime
- logs/ events
- modules/ artifacts
- gui/ dashboard

**Batch 5: Error Pipeline (Lines 299-395)**
- error/plugins
- error/engine/aggregator
- error/engine/classifier
- Auto-fix mechanism
- Re-validation

**Batch 6: Module Dependencies (Lines 119-197)**
- Layer 0: Foundation
- Layer 1: Infrastructure
- Layer 2: Domain Core
- Layer 3: Execution
- Layer 4: Interface

---

## 4. Execution Commands

### Phase 1: Discovery (Load All Context Once)
```bash
# Discover all Python modules
find . -name "*.py" -type f > discovered_files.txt

# Discover all directories mentioned in diagrams
grep -oP 'schema/|config/|core/|engine/|error/|aim/|state/|logs/|modules/' SYSTEM_VISUAL_DIAGRAMS.md | sort -u > referenced_dirs.txt
```

### Phase 2: Batch Validation (No Mid-Batch Checks)
```python
# Execute all validations in batch
results = []
for component in batch:
    result = {
        "component": component["name"],
        "exists": check_exists(component["path"]),
        "importable": check_import(component["module"]),
        "has_tests": check_tests(component["test_pattern"])
    }
    results.append(result)

# Verify ALL at end
assert all(r["exists"] for r in results), "Missing components found"
```

### Phase 3: Ground Truth Verification
```bash
# Directory existence
test -d schema && echo "✅ schema/" || echo "❌ MISSING: schema/"
test -d core && echo "✅ core/" || echo "❌ MISSING: core/"
test -d engine && echo "✅ engine/" || echo "❌ MISSING: engine/"

# Module importability
python -c "from UNIVERSAL_EXECUTION_TEMPLATES_FRAMEWORK.core.state import db" && echo "✅" || echo "❌"
python -c "from UNIVERSAL_EXECUTION_TEMPLATES_FRAMEWORK.core.engine import orchestrator" && echo "✅" || echo "❌"
python -c "from error.engine import error_engine" && echo "✅" || echo "❌"
```

---

## 5. Validation Criteria by Component Type

### Type 1: Directories
**Ground Truth**: `test -d <path>` returns 0

### Type 2: Python Modules
**Ground Truth**: `python -c "import <module>"` returns 0

### Type 3: Configuration Files
**Ground Truth**: `test -f <path>` AND valid JSON/YAML

### Type 4: Data Flow Integration
**Ground Truth**: Source module imports target module OR shares database/state

### Type 5: Error Handling
**Ground Truth**: Error plugin exists AND has parse() method

---

## 6. Report Template

```markdown
## Data Flow Validation Report

**Diagram Source**: SYSTEM_VISUAL_DIAGRAMS.md
**Validation Date**: {timestamp}
**Total Flows Checked**: {N}
**Success Rate**: {passed/total}%

### Summary
- ✅ Validated: {count}
- ❌ Missing: {count}
- ⚠️  Partial: {count}

### Detailed Findings

#### Diagram 1: Data Flow & State Transitions (Lines 5-107)
| Component | Expected Path | Status | Evidence |
|-----------|--------------|--------|----------|
| schema/validation | schema/ | ✅ | Directory exists, 15 .json files |
| core/planner | core/planner.py | ✅ | Module imports successfully |
| engine/queue | engine/queue/ | ✅ | Package with __init__.py |

#### Missing Components
| Component | Diagram Reference | Impact |
|-----------|------------------|--------|
| config/rules | Line 28 | Medium - No validation rules found |

#### Recommendations
1. Create missing components
2. Update diagrams to reflect actual structure
3. Add integration tests for critical flows
```

---

## 7. Decision Elimination Checklist

**Made ONCE before execution:**
- [x] Report format: Markdown table
- [x] Validation depth: File/directory existence + import checks
- [x] Success criterion: 100% of critical flows exist
- [x] Batch size: 8 components
- [x] Verification method: Shell test commands

**NOT decisions (ignored):**
- [ ] Code quality of found modules
- [ ] Performance optimization
- [ ] Completeness of implementations
- [ ] Documentation quality

---

## 8. Time Estimate

**Pattern Creation**: 15 min (template + batching)
**Per-Batch Execution**: 3 min × 6 batches = 18 min
**Ground Truth Verification**: 5 min
**Report Generation**: 5 min
**Total**: ~43 minutes

**Traditional Approach**: ~3 hours (manual checking each flow)
**Speedup**: 4.2x faster

---

## 9. Reusability

This pattern applies to:
- Architecture validation
- Migration verification
- System health checks
- Documentation accuracy audits
- Dependency validation

**Customization Points:**
- Batch composition (group by layer vs. by function)
- Validation depth (existence vs. functionality)
- Report format (JSON vs. Markdown vs. YAML)
