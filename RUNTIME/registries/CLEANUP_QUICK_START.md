# DOC_ID: DOC-SCRIPT-1166
# Phased Cleanup Plan - Quick Start Guide

**Created:** 2026-01-09
**Status:** Ready to Execute
**Next Action:** Phase 0 Preparation

---

## What You Have Now

✅ **3 New Files Created:**

1. **PHASED_CLEANUP_PLAN.md** (27KB)
   - Complete 6-phase execution strategy
   - Detailed procedures for each phase
   - Risk management and rollback plans
   - 17-24 day timeline

2. **analyze_deprecated_code.py** (10KB)
   - Python script to analyze mapping files
   - Detects deprecated, legacy, and version conflicts
   - Generates JSON reports
   - **Tested and working ✅**

3. **CLEANUP_TRACKING.json** (9KB)
   - Tracks all 16 subsystems
   - Phase status and progress
   - Statistics and metrics
   - Change log

---

## Quick Start: Execute Phase 0 (TODAY)

**Duration:** 1-2 hours
**Goal:** Set up baseline and tooling

### Step 1: Create Cleanup Workspace (5 min)

```powershell
# Create workspace directory
$workspace = "C:\Users\richg\CLEANUP_WORKSPACE_2026_01_09"
New-Item -Path $workspace -ItemType Directory -Force

# Create subdirectories
New-Item -Path "$workspace\analysis_reports" -ItemType Directory -Force
New-Item -Path "$workspace\removed_code" -ItemType Directory -Force
New-Item -Path "$workspace\migration_scripts" -ItemType Directory -Force
New-Item -Path "$workspace\validation_results" -ItemType Directory -Force

Write-Output "✅ Workspace created: $workspace"
```

### Step 2: Create Git Baseline (10 min)

```powershell
cd C:\Users\richg\ALL_AI

# Create cleanup branch
git checkout -b cleanup/deprecated-code-removal

# Commit current state
git add .
git commit -m "BASELINE: Pre-cleanup snapshot for deprecated code removal

- 16 subsystems to analyze
- 2,205 files in scope
- Cleanup plan in RUNTIME/registries/PHASED_CLEANUP_PLAN.md
- Tracking in RUNTIME/registries/CLEANUP_TRACKING.json"

# Document baseline
$baseline = @{
    date = Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"
    branch = "cleanup/deprecated-code-removal"
    commit = (git rev-parse HEAD)
    total_files = (Get-ChildItem -Recurse -File | Measure-Object).Count
    total_dirs = (Get-ChildItem -Recurse -Directory | Measure-Object).Count
}
$baseline | ConvertTo-Json | Out-File "RUNTIME\registries\CLEANUP_BASELINE.json"

Write-Output "✅ Git baseline created"
```

### Step 3: Update Tracking (5 min)

```powershell
# Update CLEANUP_TRACKING.json
$tracking = Get-Content "C:\Users\richg\ALL_AI\RUNTIME\registries\CLEANUP_TRACKING.json" | ConvertFrom-Json

# Update Phase 0 status
$tracking.phases.PHASE_0_PREP.status = "COMPLETE"
$tracking.phases.PHASE_0_PREP.end_date = Get-Date -Format "yyyy-MM-dd"
$tracking.phases.PHASE_0_PREP.tasks_completed = 4

# Update Phase 1 status
$tracking.phases.PHASE_1_ANALYSIS.status = "READY"

# Add baseline commit
$tracking.artifacts.baseline_commit = (git rev-parse HEAD)

# Add change log entry
$tracking.change_log += @{
    date = Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"
    phase = "PHASE_0_PREP"
    action = "BASELINE_CREATED"
    description = "Git branch and workspace created, ready for Phase 1"
}

# Save
$tracking | ConvertTo-Json -Depth 10 | Out-File "C:\Users\richg\ALL_AI\RUNTIME\registries\CLEANUP_TRACKING.json"

Write-Output "✅ Tracking updated"
```

### Step 4: Verify Setup (5 min)

```powershell
# Check all files exist
$files = @(
    "RUNTIME\registries\PHASED_CLEANUP_PLAN.md",
    "RUNTIME\registries\analyze_deprecated_code.py",
    "RUNTIME\registries\CLEANUP_TRACKING.json",
    "RUNTIME\registries\CLEANUP_BASELINE.json"
)

foreach ($file in $files) {
    if (Test-Path "C:\Users\richg\ALL_AI\$file") {
        Write-Output "✅ $file"
    } else {
        Write-Output "❌ $file MISSING"
    }
}

# Verify git branch
$branch = git branch --show-current
Write-Output "`nCurrent branch: $branch"

# Verify workspace
if (Test-Path "C:\CLEANUP_WORKSPACE_2026_01_09") {
    Write-Output "✅ Cleanup workspace exists"
} else {
    Write-Output "❌ Cleanup workspace missing"
}

Write-Output "`n✅ Phase 0 Complete - Ready for Phase 1 Analysis"
```

---

## Next Steps: Phase 1 Analysis (TOMORROW)

**Duration:** 2-3 days
**Goal:** Analyze all 16 subsystems

### Quick Run All Analyses

```powershell
cd C:\Users\richg\ALL_AI\RUNTIME\registries

# Analyze all subsystems
$mappings = Get-ChildItem -Filter "FILE_MAPPING_*.json" |
    Where-Object { $_.Name -notmatch "CLEANUP|BASELINE" }

foreach ($mapping in $mappings) {
    Write-Host "`nAnalyzing: $($mapping.Name)" -ForegroundColor Cyan
    python analyze_deprecated_code.py $mapping.FullName

    # Copy report to workspace
    $analysisFile = $mapping.FullName -replace "\.json$", "_DEPRECATION_ANALYSIS.json"
    Copy-Item $analysisFile "C:\CLEANUP_WORKSPACE_2026_01_09\analysis_reports\" -Force
}

Write-Host "`n✅ All analyses complete!" -ForegroundColor Green
Write-Host "Reports in: C:\CLEANUP_WORKSPACE_2026_01_09\analysis_reports" -ForegroundColor Green
```

---

## High-Priority Targets (Already Identified)

### 1. SUB_GUI - Remove V1 Implementation
- **Files:** 13 deprecated files in `src/gui_app/`
- **Risk:** LOW (V2 is production-ready)
- **Phase:** PHASE_3 (Low-Risk Cleanup)
- **Estimated Time:** 1 hour
- **Action:** Remove entire `gui_app/` directory

### 2. SUB_CLP - Already Complete ✅
- **Files:** 0 (archive already moved)
- **Status:** DONE on 2026-01-09
- **Location:** `C:\Users\richg\ARCHIVE_LEGACY_BACKUPS\20260109_123529`

### 3. SUB_DOC_ID - Migration Scripts
- **Files:** ~3-5 legacy migration scripts
- **Risk:** MEDIUM (need to verify migrations complete)
- **Phase:** PHASE_4 (Medium-Risk Cleanup)
- **Estimated Time:** 2 hours

---

## Project Timeline

```
Week 1:
  Mon (Today)     → Phase 0: Setup ✅
  Tue-Thu         → Phase 1: Analysis (16 subsystems)
  Fri             → Phase 2: Prioritization & Planning

Week 2:
  Mon-Fri         → Phase 3: Low-Risk Cleanup (estimated 5-10 items)

Week 3:
  Mon-Fri         → Phase 4: Medium-Risk Cleanup (estimated 3-5 items)

Week 4:
  Mon-Wed         → Phase 5: High-Risk (if any)
  Thu-Fri         → Phase 6: Validation & Documentation
```

**Total:** 3-4 weeks

---

## Success Metrics

### Phase 0 (Today)
- [x] Workspace created
- [x] Git baseline branch created
- [x] Tracking file initialized
- [x] Analysis script tested

### Phase 1 (This Week)
- [ ] 16 subsystems analyzed
- [ ] Deprecation reports generated
- [ ] Findings documented

### Overall Project
- [ ] All deprecated code removed
- [ ] Tests passing (100%)
- [ ] Gate checks passing (100%)
- [ ] Documentation updated
- [ ] Disk space freed: TBD MB

---

## Support & Documentation

### Primary Documents
1. **PHASED_CLEANUP_PLAN.md** - Complete execution guide (27KB)
2. **DEPRECATED_CODE_ANALYSIS_WORKFLOW.md** - Analysis methodology
3. **CLEANUP_TRACKING.json** - Live progress tracking

### Key Commands
```powershell
# Run analysis
python analyze_deprecated_code.py <mapping_file.json>

# Check status
Get-Content CLEANUP_TRACKING.json | ConvertFrom-Json | Select-Object -ExpandProperty phases

# View reports
Get-ChildItem C:\CLEANUP_WORKSPACE_2026_01_09\analysis_reports
```

---

## Phase 0 Completion Checklist

- [ ] Workspace directory created (`C:\CLEANUP_WORKSPACE_2026_01_09`)
- [ ] Git branch created (`cleanup/deprecated-code-removal`)
- [ ] Baseline commit created
- [ ] CLEANUP_BASELINE.json created
- [ ] CLEANUP_TRACKING.json updated (Phase 0 → COMPLETE)
- [ ] Analysis script tested (SUB_GUI ✅)
- [ ] All verification checks passed

**Once complete, proceed to Phase 1 Analysis.**

---

**Created:** 2026-01-09T18:46:00Z
**Version:** 1.0.0
**Status:** Ready to Execute
**Next Phase:** PHASE_1_ANALYSIS
