# Plan-Evaluate Loop with CLI Applications

This directory contains the implementation of a **self-healing planner-critic loop** using:
- **Codex CLI** (Planner and Refiner - schema-enforced JSON output)
- **Copilot CLI** (Critic - cross-model validation)
- **Deterministic Python gate** (Quality validation without AI)

## Architecture

```
Planning Request
    ↓
[1] Planner (Codex) → Draft Plan
    ↓
[2] Quality Gate (Python) → Pass/Fail
    ↓ (if pass)
[3] Critic (Copilot) → Critique Report → Verdict
    ↓ (if needs_revision)
[4] Refiner (Codex) → Revised Plan → back to [2]
    ↓ (if converged)
Done ✓
```

## Prerequisites

### 1. Install CLIs

**Copilot CLI:**
```bash
npm install -g @github/copilot
```

**Codex CLI:**
```bash
npm install -g @openai/codex
# or
brew install --cask codex
```

### 2. Install Python Dependencies

```bash
pip install jsonschema==4.*
```

### 3. Set Authentication

**For Codex (Planner/Refiner):**
```powershell
$env:CODEX_API_KEY = "sk-...your-openai-api-key..."
```

**For Copilot (Critic):**
```powershell
$env:GH_TOKEN = "ghp_...your-github-token..."
# or
$env:GITHUB_TOKEN = "ghp_...your-github-token..."
```

> **GitHub Token:** Create a fine-grained personal access token with "Copilot Requests" permission.

## Quick Start

### Run the Loop

```powershell
cd ai_service_wrappers
.\run_loop.ps1 -RequestPath ..\inputs\example_planning_request.json -MaxAttempts 3
```

**Output:**
- Artifacts stored in: `.state/evidence/plan_loop_runs/{RUN_ID}/`
- Each iteration folder contains:
  - `draft_plan.json` (current plan)
  - `gate_report.json` (deterministic validation)
  - `critique_report.json` (AI critique)
  - `logs/` (stdout/stderr from each tool)

### Test Individual Components

**Test Planner:**
```powershell
python ai_service_wrappers\planner.py `
  --request inputs\example_planning_request.json `
  --schema schemas_langgraph\draft_plan.schema.json `
  --out-plan test_plan.json `
  --out-envelope test_envelope.json `
  --log-stdout test_planner.stdout `
  --log-stderr test_planner.stderr
```

**Test Quality Gate:**
```powershell
python ai_service_wrappers\plan_quality_gate.py `
  --plan test_plan.json `
  --schema schemas_langgraph\draft_plan.schema.json `
  --out test_gate_report.json
```

**Test Critic:**
```powershell
python ai_service_wrappers\critic.py `
  --plan test_plan.json `
  --schema schemas_langgraph\critique_report.schema.json `
  --out test_critique.json `
  --log-stdout test_critic.stdout `
  --log-stderr test_critic.stderr
```

## Convergence Logic

The loop **converges** when:
1. Quality Gate passes (no blocker defects)
2. Critic verdict is "pass"

The loop **terminates** when:
- Convergence achieved, OR
- Max attempts reached (default: 3)

Exit codes:
- `0` - Converged successfully
- `2` - Failed to converge
- `10` - Gate failed
- `30` - Planner failed
- `40` - Critic failed
- `50` - Refiner failed

## Bug Fixes Applied

This implementation fixes all **14 critical bugs** documented in `Errors in ChatGPT research.txt`:

### Runtime Breakers (FIXED)
1. ✅ Argparse attributes: `args.out_plan` not `args.out-plan`
2. ✅ UUID generation: `uuid.uuid4()` not `uuid.uuid-4()`
3. ✅ PowerShell argument passing: proper parameter handling
4. ✅ Copilot CLI flags: removed invalid `--stream off`

### Logic/Design (FIXED)
5. ✅ Critic now runs after refinement iterations
6. ✅ Auth preflight checks added
7. ✅ Convergence tracking implemented

## Directory Structure

```
01260207201000001221_Multi_CLI/
├── ai_service_wrappers/
│   ├── planner.py              # Codex wrapper for planning
│   ├── critic.py               # Copilot wrapper for critique
│   ├── refiner.py              # Codex wrapper for refinement
│   ├── plan_quality_gate.py    # Deterministic validation
│   └── run_loop.ps1            # Main orchestrator
├── schemas_langgraph/
│   ├── draft_plan.schema.json
│   ├── critique_report.schema.json
│   ├── gate_report.schema.json
│   ├── envelope.schema.json
│   └── planning_request.schema.json
├── templates/
│   └── heal_templates.json     # Remediation templates
├── inputs/
│   └── example_planning_request.json
└── .state/
    └── evidence/
        └── plan_loop_runs/     # Run artifacts
```

## Next Steps

1. **Test the loop:**
   ```powershell
   .\ai_service_wrappers\run_loop.ps1 -RequestPath inputs\example_planning_request.json
   ```

2. **Integrate with LangGraph** (optional):
   - See `LangGraph Integration Architecture.md`
   - LangGraph becomes control-plane orchestrator
   - These wrappers become LangGraph tool nodes

3. **Add monitoring:**
   - Track convergence rates
   - Monitor token usage
   - Alert on repeated failures

## Troubleshooting

**Issue: "CODEX_API_KEY not set"**
```powershell
$env:CODEX_API_KEY = "sk-...your-key..."
```

**Issue: "GH_TOKEN not set"**
```powershell
$env:GH_TOKEN = "ghp_...your-token..."
```

**Issue: Critic returns markdown instead of JSON**
- Retry logic auto-handles this (max 2 attempts)
- JSON extraction removes markdown code blocks

**Issue: Rate limits**
- Add backoff/retry in orchestrator
- Monitor API tier limits

## Design Principles

1. **Artifact-Based:** All inter-tool messages are JSON files (not free-text)
2. **Schema-Enforced:** Codex `--output-schema` guarantees JSON validity
3. **Deterministic Gates:** Quality checks without AI for consistency
4. **Fail-Closed:** Auth checks, validation failures stop execution
5. **Evidence-First:** Every iteration artifacts preserved for audit

## References

- Deep Research Report: Contract-first self-healing architecture
- LangGraph Integration Architecture: Control-plane positioning
- Errors Document: Bug fixes applied
- Integration Summary: Complete system specifications
