# ACMS File Index

Quick reference guide to all ACMS files and their purposes.

---

## 📘 Start Here

| File | Purpose | For |
|------|---------|-----|
| **README_ACMS.md** | Project overview & reference | Everyone |
| **ACMS_QUICK_START.md** | 5-minute tutorial | New users |
| **demo_acms_pipeline.py** | Interactive demonstration | Learning the system |

---

## 🐍 Core Python Modules

| File | Lines | Purpose | Import As |
|------|-------|---------|-----------|
| **acms_controller.py** | 307 | Top-level orchestrator, CLI entry point | `from acms_controller import ACMSController` |
| **gap_registry.py** | 207 | Gap storage, normalization, queries | `from gap_registry import GapRegistry` |
| **execution_planner.py** | 270 | Workstream clustering & prioritization | `from execution_planner import ExecutionPlanner` |
| **phase_plan_compiler.py** | 268 | Phase plan → MINI_PIPE compilation | `from phase_plan_compiler import PhasePlanCompiler` |

**Usage:**
```bash
# CLI
python acms_controller.py /path/to/repo --mode full

# Demo
python demo_acms_pipeline.py
```

---

## 📚 Documentation

### User Guides

| File | Size | Audience | Content |
|------|------|----------|---------|
| **ACMS_QUICK_START.md** | 4.8 KB | New users | 5-minute tutorial, basic commands |
| **README_ACMS.md** | 9.6 KB | All users | Overview, architecture, examples |

### Technical Documentation

| File | Size | Audience | Content |
|------|------|----------|---------|
| **ACMS_IMPLEMENTATION_GUIDE.md** | 11.5 KB | Developers | Complete technical reference, API docs |
| **ACMS_IMPLEMENTATION_SUMMARY.md** | 8.3 KB | Project managers | Metrics, verification, integration status |
| **ACMS_PROJECT_COMPLETION_REPORT.md** | 12.3 KB | Stakeholders | Deliverables, compliance, recommendations |

---

## 📊 Example & Test Data

| File | Size | Purpose |
|------|------|---------|
| **example_gap_report.json** | 9.7 KB | Example gap analysis with 12 realistic gaps |
| **demo_execution_plan.json** | 10.4 KB | Sample 22-task execution plan (generated) |

**How to Use:**
```python
# Load example data
from gap_registry import GapRegistry
registry = GapRegistry()
registry.load_from_report("example_gap_report.json")
```

---

## 🗂️ Generated Artifacts

### Per-Run Directory Structure

```
.acms_runs/{run_id}/
├── acms_state.json              # Controller state
├── gap_analysis_report.json     # Raw gap analysis
├── gap_registry.json            # Normalized gaps
├── workstreams.json             # Clustered workstreams
├── mini_pipe_execution_plan.json # Task DAG
└── summary_report.json          # Final summary
```

**Example:**
```
.acms_runs/20251206192326_C2D3A0952377/
```

---

## 🔧 Related MINI_PIPE Files

These files are referenced by ACMS but are part of the broader MINI_PIPE ecosystem:

| File | Purpose in ACMS |
|------|-----------------|
| `OVERLAP_AUTOMATION_AND_MASTER_GAP_ANALYSIS.merged.json` | Phase 1 gap analysis prompt |
| `MASTER_SPLINTER_PHASE_PLAN_TEMPLATE_GUIDE.json` | Phase 3 plan generation guide |
| `COMPREHENSIVE_GAP_FINDING_FRAMEWORK.json` | Gap analysis framework reference |
| `MINI_PIPE_orchestrator.py` | Phase 4 execution engine (integration pending) |
| `MINI_PIPE_orchestrator_cli.py` | Phase 4 CLI interface (integration pending) |
| `MINI_PIPE_patch_converter.py` | Phase 5 patch normalization (optional) |
| `MINI_PIPE_patch_ledger.py` | Phase 5 audit trail (optional) |

---

## 📁 File Organization by Purpose

### Pipeline Implementation
```
acms_controller.py          # Orchestrates all phases
gap_registry.py             # Phase 1-2: Gap storage
execution_planner.py        # Phase 2: Clustering
phase_plan_compiler.py      # Phase 3: Plan generation
```

### Getting Started
```
README_ACMS.md              # Overview
ACMS_QUICK_START.md         # Tutorial
demo_acms_pipeline.py       # Interactive demo
example_gap_report.json     # Sample data
```

### Reference
```
ACMS_IMPLEMENTATION_GUIDE.md    # Technical docs
ACMS_IMPLEMENTATION_SUMMARY.md  # Metrics & status
ACMS_PROJECT_COMPLETION_REPORT.md # Final report
```

---

## 🚀 Quick Access Paths

### I want to...

**...understand what ACMS does**
→ Read `README_ACMS.md`

**...get started in 5 minutes**
→ Follow `ACMS_QUICK_START.md`

**...see it in action**
→ Run `python demo_acms_pipeline.py`

**...use it on my repo**
→ Run `python acms_controller.py /path/to/repo --mode plan_only`

**...integrate AI gap analysis**
→ See `ACMS_IMPLEMENTATION_GUIDE.md` → Integration Points → AI Gap Analysis

**...integrate MINI_PIPE execution**
→ See `ACMS_IMPLEMENTATION_GUIDE.md` → Integration Points → MINI_PIPE Execution

**...understand the API**
→ Read `ACMS_IMPLEMENTATION_GUIDE.md` → Components

**...extend the system**
→ Read `ACMS_IMPLEMENTATION_GUIDE.md` → Contributing

**...check implementation status**
→ Read `ACMS_IMPLEMENTATION_SUMMARY.md`

**...review deliverables**
→ Read `ACMS_PROJECT_COMPLETION_REPORT.md`

---

## 📖 Reading Order

### For New Users
1. `README_ACMS.md` - Get the big picture
2. `ACMS_QUICK_START.md` - Try basic commands
3. Run `demo_acms_pipeline.py` - See it work
4. `ACMS_IMPLEMENTATION_GUIDE.md` - Learn the details

### For Developers
1. `ACMS_IMPLEMENTATION_GUIDE.md` - Technical overview
2. `gap_registry.py`, `execution_planner.py`, `phase_plan_compiler.py` - Core logic
3. `acms_controller.py` - Pipeline orchestration
4. `example_gap_report.json` - Data format reference

### For Integration
1. `ACMS_IMPLEMENTATION_GUIDE.md` → Integration Points
2. `acms_controller.py` - Find TODO markers
3. `ACMS_PROJECT_COMPLETION_REPORT.md` → Integration Readiness

### For Project Management
1. `ACMS_PROJECT_COMPLETION_REPORT.md` - Full status
2. `ACMS_IMPLEMENTATION_SUMMARY.md` - Metrics
3. `README_ACMS.md` → Development Roadmap

---

## 🔍 Find Specific Information

### Architecture & Design
- Overview: `README_ACMS.md` → Architecture
- Detailed: `ACMS_IMPLEMENTATION_GUIDE.md` → Architecture Alignment
- Components: `ACMS_IMPLEMENTATION_GUIDE.md` → Components

### Usage & Commands
- CLI: `ACMS_QUICK_START.md` → Command Reference
- Python API: `ACMS_IMPLEMENTATION_GUIDE.md` → Gap Registry API
- Examples: `README_ACMS.md` → Example Output

### Integration
- AI: `ACMS_IMPLEMENTATION_GUIDE.md` → Integration Points → AI
- MINI_PIPE: `ACMS_IMPLEMENTATION_GUIDE.md` → Integration Points → MINI_PIPE
- Status: `ACMS_PROJECT_COMPLETION_REPORT.md` → Integration Readiness

### Metrics & Status
- Summary: `ACMS_IMPLEMENTATION_SUMMARY.md` → Metrics
- Verification: `ACMS_IMPLEMENTATION_SUMMARY.md` → Verification
- Completion: `ACMS_PROJECT_COMPLETION_REPORT.md` → Success Metrics

### Testing & Demo
- Demo script: `demo_acms_pipeline.py`
- Test data: `example_gap_report.json`
- Manual tests: `ACMS_IMPLEMENTATION_GUIDE.md` → Testing

---

## 📋 Cheat Sheet

```bash
# View help
python acms_controller.py --help

# Run demo
python demo_acms_pipeline.py

# Analyze repository
python acms_controller.py . --mode analyze_only

# Full pipeline
python acms_controller.py . --mode full

# Check what was created
ls .acms_runs/

# View execution plan
cat demo_execution_plan.json
```

---

**Total ACMS Files:** 11 (5 Python, 5 Markdown, 1 JSON)  
**Total Size:** ~88 KB  
**Total Lines of Code:** 1,216 (Python only)

**Last Updated:** 2025-12-06
