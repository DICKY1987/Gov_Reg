# ACMS Quick Start Guide

**Last Updated:** 2025-12-07  
**Version:** 1.0 (Hardened)  
**Status:** Production Ready

---

## Three Commands to Get Started

### 1. Run Test Scenario
```bash
python demo_minimal_scenario.py
```
Analyzes test repository safely (no code changes).

### 2. View Run Status
```bash
python acms_show_run.py
```
Shows latest run metrics and artifacts.

### 3. Validate Artifacts
```bash
python validate_everything.py
```
Validates all data against schemas.

---

## Full Pipeline

```bash
python acms_controller.py <repo_root> [--mode {full|analyze_only|plan_only}]
```

**Modes:**
- `analyze_only` - Gap analysis only (safe)
- `plan_only` - Analysis + planning (safe)  
- `full` - Complete pipeline (analysis → execution)

See ACMS_IMPLEMENTATION_GUIDE.md for full documentation.
See REC_006_OPTIONAL_FEATURES_GUIDE.md for optional features.

**Status:** ✅ Production Ready
