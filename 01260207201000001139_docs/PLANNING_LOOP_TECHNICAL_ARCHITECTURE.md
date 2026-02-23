# Planning Loop - Technical Architecture

**Version:** 2.0.0  
**Date:** 2026-02-18  
**Status:** Beta

---

## System Architecture

### High-Level Overview

The Planning Loop CLI is a **deterministic, policy-driven plan refinement system** that operates as a closed feedback loop:

```
┌─────────────────────────────────────────────────────────────┐
│                        User Input                           │
│  (Objective, constraints, repository context)               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Context Generator                         │
│  • Scans repository                                         │
│  • Extracts templates, schemas, gates                       │
│  • Creates context_bundle.json                              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Planner Agent                            │
│  • Generates initial skeleton (iter 0)                      │
│  • Creates plan.json with 14 required fields                │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                     Critic Agent                            │
│  • Runs 5 deterministic linters                             │
│  • Classifies defects (hard/soft)                           │
│  • Generates CRITIC_REPORT.json                             │
└────────────────────────┬────────────────────────────────────┘
                         │
                ┌────────┴────────┐
                │                 │
           Hard Defects?          No (ZERO_HARD_DEFECTS)
                │                 │
               YES                ▼
                │            ┌─────────────┐
                ▼            │  Finalize   │
┌────────────────────────┐  │  • Package  │
│    Planner Agent       │  │  • Export   │
│  • Generate patch      │  └─────────────┘
│  • RFC-6902 ops        │
└──────────┬─────────────┘
           │
           ▼
┌────────────────────────┐
│   Patch Applicator     │
│  • Apply patch         │
│  • Verify hash         │
│  • Update plan         │
└──────────┬─────────────┘
           │
           ▼
  ┌────────────────────┐
  │ Termination Check  │
  │  • Max iterations? │
  │  • Plateau?        │
  │  • Stale context?  │
  └────────┬───────────┘
           │
      Loop back to Critic
```

---

## Component Details

### 1. Context Generator

**File:** `src/plan_refine_cli/context_generator.py`

**Purpose:** Extract structured snapshot of repository state

**Key Methods:**
```python
def generate_context_bundle() -> Dict:
    """Create context bundle with:
    - Repository metadata (git hash, branch)
    - Known templates (AUTONOMOUS_DELIVERY_TEMPLATE_V3)
    - Registries (gates, schemas, policies)
    - File structure snapshot
    """
```

**Output Schema:** `context_bundle.schema.json`

**Evidence:** Saves `context_bundle.json` in run directory

---

### 2. Policy Manager

**File:** `src/plan_refine_cli/policy_manager.py`

**Purpose:** Load and validate policy configurations

**Key Methods:**
```python
def load_policy(policy_path: Path) -> Dict:
    """Load policy from file, validate against schema"""

def create_policy_snapshot(base_policy: Dict, run_id: str) -> Dict:
    """Create immutable policy snapshot for run"""
```

**Output Schema:** `planning_policy_snapshot.schema.json`

**Validation:** GATE-009 ensures immutability

---

### 3. Planner Agent

**File:** `src/plan_refine_cli/agents/planner.py`

**Purpose:** Generate and refine plans

**Architecture:**
```
PlannerAgent
├── generate_skeleton()      # Create initial plan
│   ├── Load context bundle
│   ├── Apply policy rules
│   ├── Generate 14-field structure
│   └── Assign unique plan_id
│
└── refine_plan()            # Generate refinement patch
    ├── Analyze critic report
    ├── Identify hard defects
    ├── Generate RFC-6902 operations
    └── Compute target hash
```

**Modes:**
- `DETERMINISTIC` - Template-based (no LLM)
- `LLM` - GPT-4 powered (requires API key)

**Prompts:**
- `prompts/planner_skeleton.md` - Skeleton generation
- `prompts/planner_refine.md` - Refinement instructions

---

### 4. Critic Agent

**File:** `src/plan_refine_cli/agents/critic.py`

**Purpose:** Analyze plans for defects

**Architecture:**
```
CriticAgent
└── lint_plan()
    ├── detect_defects_deterministic()
    │   ├── CompletenessLinter (COMP-*)
    │   ├── SchemaComplianceLinter (SCHEMA-*)
    │   ├── ForbiddenPatternsLinter (PATTERN-*)
    │   ├── ReferenceValidityLinter (REF-*)
    │   └── AcceptanceCriteriaLinter (AC-*)
    │
    └── detect_defects_llm()  # Optional
        └── Invokes LLM with prompts/critic_llm.md
```

**Defect Classification:**
- **Hard Defects** (CRITICAL, HIGH) → Must fix (triggers refinement)
- **Soft Defects** (MEDIUM, LOW, INFO) → Can proceed

**Output Schema:** `CRITIC_REPORT.schema.json`

---

### 5. Patch Applicator

**File:** `src/plan_refine_cli/patch_applicator.py`

**Purpose:** Apply RFC-6902 patches to plans

**Key Methods:**
```python
def apply_patch(plan: Dict, patch: Dict) -> Tuple[Dict, bool, str]:
    """Apply patch operations to plan
    
    Steps:
    1. Verify target_plan_hash matches compute_json_hash(plan)
    2. Apply each operation sequentially
    3. Return patched plan, success flag, error message
    """

def validate_patch(patch: Dict) -> Tuple[bool, List[str]]:
    """Pre-flight patch validation
    
    Checks:
    - All operations have valid JSON pointers
    - Operation types are in allowed_patch_operations
    - Required fields present (patch_id, target_plan_hash, operations)
    """

def generate_rollback_patch(original: Dict, patched: Dict) -> Dict:
    """Generate reverse patch for rollback"""
```

**Supported Operations:**
- `add` - Insert at path
- `remove` - Delete from path
- `replace` - Update at path
- `move` - Relocate value
- `copy` - Duplicate value
- `test` - Assert condition

---

### 6. Staleness Checker

**File:** `src/plan_refine_cli/staleness_checker.py`

**Purpose:** Detect outdated context bundles

**Algorithm:**
```python
def check_context_staleness(context_bundle: Dict, 
                           threshold_hours: int = 24) -> Tuple[str, Dict]:
    """
    Status codes:
    - FRESH: Context is current
    - STALE: Context is outdated (triggers termination)
    
    Checks:
    1. Time elapsed since bundle generation
    2. Git HEAD changes (if in git repo)
    3. Critical file modifications
    """
```

**Thresholds:**
- Default: 24 hours
- Configurable via policy
- Git-aware (detects HEAD changes)

---

### 7. Termination Checker

**File:** `src/plan_refine_cli/termination_checker.py`

**Purpose:** Determine when to exit refinement loop

**Termination Conditions:**

```python
ZERO_HARD_DEFECTS       # Success - no blocking issues
MAX_ITERATIONS_REACHED  # Hit iteration limit
CONTEXT_STALE           # Context needs refresh
SOFT_DEFECTS_PLATEAUED  # No improvement for N iterations
```

**Plateau Detection:**
```python
def detect_plateau(trajectory: List[Dict], 
                  threshold: float = 0.05,
                  lookback: int = 3) -> bool:
    """
    Returns True if soft_count improvement < 5% over last 3 iterations
    """
```

**Priority:** hard_defects > staleness > iterations > plateau

---

### 8. Control Plane

**File:** `src/plan_refine_cli/control_plane.py`

**Purpose:** LangGraph-based orchestration

**State Machine:**
```
START → staleness_check → critic_node → termination_check
                ↓              ↓              ↓
              STALE          defects?       continue?
                ↓              ↓              ↓
               END      planner_node → patch_node
                              ↓              ↓
                          decision    → (loop back)
```

**GraphState Fields:**
- `current_plan` - Plan being refined
- `context_bundle` - Repository snapshot
- `policy_snapshot` - Immutable policy
- `critic_reports[]` - History of analyses
- `patches_applied[]` - Applied patches
- `iteration` - Current iteration number
- `termination_reason` - Why loop ended

---

### 9. Validation Gates

**File:** `src/plan_refine_cli/validation_gates.py`

**Purpose:** Executable validation checkpoints

**Gate Interface:**
```python
class ValidationGate:
    def execute(self, artifact_paths: Dict[str, Path]) -> Tuple[bool, Dict]:
        """
        Returns: (passed, report)
        
        Report contains:
        - gate_id (e.g., "GATE-001")
        - gate_type (e.g., "SCHEMA")
        - status ("PASSED" | "FAILED")
        - errors[] (if any)
        """
```

**Built-in Gates:**
1. **GATE-001: Schema Validation**
   - Uses `jsonschema` library
   - Validates against PLAN.schema.json
   
2. **GATE-002: Policy Compliance**
   - Checks required sections
   - Scans for forbidden patterns
   
3. **GATE-003: Dependency Validation**
   - Verifies dependencies available
   - Runs validation commands

---

### 10. Hash Utilities

**File:** `src/plan_refine_cli/hash_utils.py`

**Purpose:** Cryptographic hashing for integrity

**Key Functions:**
```python
def compute_json_hash(data: Dict) -> str:
    """Compute SHA256 hash of JSON (deterministic)
    
    Process:
    1. Sort keys recursively
    2. Convert to canonical JSON (no whitespace)
    3. Encode as UTF-8
    4. Compute SHA256
    5. Return hex digest (64 chars)
    """

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA256 hash of file contents"""
```

**Properties:**
- **Deterministic**: Same data always produces same hash
- **Collision-resistant**: SHA256 provides 2^256 space
- **Efficient**: Streaming for large files

---

## Data Schemas

### Field Definitions

#### Plan ID Format
```
Pattern: PLAN_20260218T120000Z_abc12345
         ^^^^_YYYYMMDDTHHMMSSZ_xxxxxxxx
         |    |                |
         |    Timestamp (UTC)  8-char UUID (hex)
         Prefix
```

#### Artifact ID Format
```
Pattern: {PREFIX}_{timestamp}_{uuid8}
Examples:
- CRITIC_20260218T120000Z_xyz78901
- PATCH_20260218T120000Z_def45678
- CONTEXT_20260218T120000Z_ghi12345
```

#### JSON Pointers (RFC-6901)
```
/workstreams/0/steps/2/command       # Specific step command
/acceptance_criteria/1               # Second acceptance criterion
/metadata/iteration                  # Metadata field
/declared_new_artifacts/-            # Append to array
```

---

## Algorithm Details

### Refinement Loop Algorithm

```python
def refinement_loop(context, policy, max_iterations=5):
    """
    Pseudo-code for refinement loop
    """
    plan = generate_skeleton(context, policy)
    iteration = 0
    defect_trajectory = []
    
    while iteration < max_iterations:
        # Staleness check
        if is_context_stale(context):
            return plan, "CONTEXT_STALE"
        
        # Critic analysis
        report = critic.lint_plan(plan, policy, context)
        hard_count = len(report["hard_defects"])
        soft_count = len(report["soft_defects"])
        
        # Track trajectory
        defect_trajectory.append({
            "iteration": iteration,
            "hard_count": hard_count,
            "soft_count": soft_count
        })
        
        # Termination check
        if hard_count == 0:
            return plan, "ZERO_HARD_DEFECTS"  # Success!
        
        if has_plateaued(defect_trajectory):
            return plan, "SOFT_DEFECTS_PLATEAUED"
        
        # Refinement
        patch = planner.generate_patch(plan, report)
        plan = apply_patch(plan, patch)
        
        iteration += 1
    
    return plan, "MAX_ITERATIONS_REACHED"
```

---

### Defect Prioritization

```python
def prioritize_defects(defects: List[Dict]) -> List[Dict]:
    """
    Priority order:
    1. CRITICAL severity
    2. HIGH severity
    3. MEDIUM severity
    4. LOW severity
    5. INFO severity
    
    Within same severity:
    - Schema violations first
    - Completeness issues second
    - Pattern violations third
    - Style issues last
    """
```

---

### Patch Generation

```python
def generate_patch_operations(defects: List[Dict]) -> List[Dict]:
    """
    For each hard defect:
    1. Locate defect via json_pointer
    2. Determine required fix action
    3. Generate minimal operation(s)
    4. Validate operation syntax
    
    Operation types by defect:
    - Missing section → "add" operation
    - Empty section → "replace" operation
    - Invalid value → "replace" operation
    - Forbidden pattern → "remove" or "replace"
    - Reference error → "add" to declared_new_artifacts
    """
```

---

## Security Considerations

### Hash Verification

All critical artifacts are hash-verified:

```python
# Before applying patch
assert compute_json_hash(plan) == patch["target_plan_hash"]

# After applying patch
new_hash = compute_json_hash(patched_plan)
save_to_audit_log(original_hash, new_hash, patch_id)
```

### Immutable Artifacts

Certain artifacts are immutable once created:
- `context_bundle.json` - Snapshot at run start (GATE-009)
- `policy_snapshot.json` - Fixed for entire run
- `manifest.json` - Created once during init

**Enforcement:** Filesystem permissions + hash checks

### Sensitive Data

**Not stored:**
- API keys (read from environment only)
- Credentials
- PII

**Logged:**
- File paths (for audit trail)
- Command executions
- Defect counts

---

## Performance Characteristics

### Time Complexity

| Operation | Complexity | Notes |
|-----------|------------|-------|
| Context generation | O(n) | n = number of files |
| Skeleton generation | O(1) | Template-based |
| Critic analysis | O(m) | m = plan size (KB) |
| Patch application | O(k) | k = patch operations |
| Hash computation | O(n) | n = JSON size |

### Space Complexity

| Artifact | Size | Notes |
|----------|------|-------|
| Context bundle | 50-200 KB | Depends on repo size |
| Plan document | 20-100 KB | Depends on complexity |
| Critic report | 5-50 KB | Depends on defects |
| Patch document | 1-20 KB | Minimal operations |
| Run directory | 500 KB - 2 MB | Includes all iterations |

### Scalability

- **Repositories:** Tested with 1,000+ files
- **Plan size:** Handles plans up to 5 MB
- **Iterations:** Practical limit 5-10
- **Concurrent runs:** Isolated state directories

---

## Error Handling

### Error Recovery

```python
class PlanningLoopError(Exception):
    """Base exception for planning loop errors"""

class ValidationError(PlanningLoopError):
    """Schema or policy validation failed"""
    exit_code = 1

class ExecutionError(PlanningLoopError):
    """Runtime execution failed"""
    exit_code = 2

class EscalationRequired(PlanningLoopError):
    """Manual intervention needed"""
    exit_code = 3
```

### Rollback Mechanism

```python
def handle_patch_failure(original_plan: Dict, failed_patch: Dict):
    """
    On patch application failure:
    1. Log failure details
    2. Restore original plan from iter_{N-1}
    3. Generate incident report
    4. Exit with code 2
    """
```

---

## Extension Points

### Adding Custom Linters

```python
# 1. Create linter class
from plan_refine_cli.linters.deterministic_linters import BaseLinter

class MyCustomLinter(BaseLinter):
    def __init__(self):
        super().__init__("CUSTOM")
    
    def lint(self, plan: Dict) -> List[Dict]:
        defects = []
        # Your validation logic
        if some_condition:
            defects.append(self.create_defect(
                "CUSTOM-001",
                "HIGH",
                "/some/path",
                "Description of issue",
                "Recommended fix"
            ))
        return defects

# 2. Register in CriticAgent
# Edit: src/plan_refine_cli/agents/critic.py
# Add to linters list in detect_defects_deterministic()
```

### Adding Custom Gates

```python
# 1. Create gate class
from plan_refine_cli.validation_gates import ValidationGate

class MyCustomGate(ValidationGate):
    def __init__(self, schema_dir: Path):
        super().__init__("GATE-999", "CUSTOM", schema_dir)
    
    def execute(self, artifact_paths: Dict[str, Path]) -> Tuple[bool, Dict]:
        # Your validation logic
        report = {
            "gate_id": self.gate_id,
            "gate_type": self.gate_type,
            "status": "PASSED",
            "errors": []
        }
        return True, report

# 2. Register in GateRegistry
# Edit: src/plan_refine_cli/validation_gates.py
# Add to _register_builtin_gates()
```

### Custom Prompts

Create custom LLM prompts in `prompts/`:

```markdown
# custom_planner.md

## Role
You are a custom planner for [specific domain]

## Input
- Context: {...}
- Policy: {...}

## Output
Generate plan focusing on [specific aspects]

## Constraints
- [Custom constraint 1]
- [Custom constraint 2]
```

---

## Integration

### Embedding in Other Tools

```python
# Import as library
from plan_refine_cli.agents.planner import PlannerAgent
from plan_refine_cli.agents.critic import CriticAgent

# Use in your application
planner = PlannerAgent(schema_dir, prompts_dir)
critic = CriticAgent(schema_dir, prompts_dir)

plan = planner.generate_skeleton(my_context, my_policy)
report = critic.lint_plan(plan, my_policy, my_context, "DETERMINISTIC")

if report["summary"]["hard_count"] == 0:
    print("Plan is ready!")
```

### API Wrapper

```python
# Create REST API wrapper
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/api/v1/generate-plan', methods=['POST'])
def generate_plan():
    context = request.json.get('context')
    policy = request.json.get('policy')
    
    planner = PlannerAgent(schema_dir, prompts_dir)
    plan = planner.generate_skeleton(context, policy)
    
    return jsonify(plan)
```

---

## Best Practices

### 1. Policy Configuration

**DO:**
- ✓ Use descriptive policy_ids
- ✓ Set realistic max_iterations (3-5)
- ✓ Define clear forbidden patterns
- ✓ Specify measurable criteria

**DON'T:**
- ✗ Modify policy during run (breaks GATE-009)
- ✗ Set max_iterations > 10 (diminishing returns)
- ✗ Use vague pattern descriptions

---

### 2. Context Generation

**DO:**
- ✓ Generate fresh context for each run
- ✓ Include all relevant templates
- ✓ Verify git state is committed
- ✓ Check staleness before long-running loops

**DON'T:**
- ✗ Reuse old context bundles (>24 hours)
- ✗ Generate context from dirty working tree
- ✗ Omit critical registries

---

### 3. Loop Execution

**DO:**
- ✓ Start with DETERMINISTIC mode
- ✓ Monitor defect trajectory
- ✓ Set cost caps for LLM mode
- ✓ Review soft defects before proceeding

**DON'T:**
- ✗ Run loops with stale context
- ✗ Ignore soft defect warnings
- ✗ Manually edit plans during loop
- ✗ Skip validation gates

---

## Maintenance

### Log Management

Logs are written to:
```
.planning_loop_state/runs/{run_id}/logs/
├── init.log
├── context.log
├── loop.log
└── finalize.log
```

**Rotation:** Logs are kept per-run (no rotation needed)

### Cleanup

```bash
# Remove old runs (older than 30 days)
find .planning_loop_state/runs/ -type d -mtime +30 -exec rm -rf {} \;

# Keep only final plans
find .planning_loop_state/runs/ -name "iterations" -exec rm -rf {} \;
```

---

## Metrics

### Tracked Metrics

Saved to `.planning_loop_state/metrics/metrics.jsonl`:

```json
{
  "timestamp": "2026-02-18T12:00:00Z",
  "run_id": "planning_20260218T120000Z_abc12345",
  "metric_type": "LOOP_COMPLETE",
  "data": {
    "iterations": 3,
    "duration_seconds": 8.5,
    "final_hard_defects": 0,
    "final_soft_defects": 2,
    "patches_applied": 2,
    "termination_reason": "ZERO_HARD_DEFECTS"
  }
}
```

### Analysis

```bash
# Count successful runs
jq 'select(.data.termination_reason == "ZERO_HARD_DEFECTS")' metrics.jsonl | wc -l

# Average iterations
jq -s 'map(.data.iterations) | add / length' metrics.jsonl

# Total LLM cost
jq -s 'map(.data.llm_cost_usd // 0) | add' metrics.jsonl
```

---

## References

### Standards

- **JSON Schema:** Draft 2020-12
- **JSON Patch:** RFC-6902
- **JSON Pointer:** RFC-6901
- **Template:** AUTONOMOUS_DELIVERY_TEMPLATE_V3

### Dependencies

- **jsonschema** 4.21+ - Schema validation
- **jsonpatch** 1.33+ - Patch application
- **click** 8.1+ - CLI framework
- **pyyaml** 6.0+ - YAML support
- **rich** 13.7+ - Terminal formatting
- **langgraph** - State machine orchestration

---

**End of Technical Architecture Documentation**
