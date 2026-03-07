# DOC_LINK: DOC-PAT-VALIDATE-INSTALLATION-235
<#
.SYNOPSIS
    Validate Safe Merge Pattern Installation

.DESCRIPTION
    Checks that all Safe Merge patterns are correctly installed and functional.
#>

param(
    [string]$WorkDir = "."
)

$ErrorActionPreference = "Continue"
$script:FailCount = 0

function Test-Pattern {
    param(
        [string]$Name,
        [string]$Path,
        [string]$Type
    )

    Write-Host "Testing $Name..." -ForegroundColor Cyan

    if (Test-Path $Path) {
        Write-Host "  ✅ $Type exists: $Path" -ForegroundColor Green
        return $true
    } else {
        Write-Host "  ❌ $Type missing: $Path" -ForegroundColor Red
        $script:FailCount++
        return $false
    }
}

Write-Host ""
Write-Host "🔍 Safe Merge Pattern Validation" -ForegroundColor Yellow
Write-Host "================================" -ForegroundColor Yellow
Write-Host ""

# Test documentation
Write-Host "📄 Documentation Files:" -ForegroundColor Yellow
Test-Pattern "README" "README.md" "File"
Test-Pattern "QUICKSTART" "QUICKSTART.md" "File"
Test-Pattern "REGISTRY" "REGISTRY.md" "File"
Test-Pattern "COMPLETION_REPORT" "COMPLETION_REPORT.md" "File"
Test-Pattern "IMPLEMENTATION_SUMMARY" "IMPLEMENTATION_SUMMARY.md" "File"
Test-Pattern "TEST_SUITE" "TEST_SUITE.md" "File"

Write-Host ""
Write-Host "🔧 Pattern Scripts:" -ForegroundColor Yellow

# Test PowerShell scripts
Test-Pattern "MERGE-001 (Environment Scan)" "scripts\merge_env_scan.ps1" "Script"
Test-Pattern "MERGE-006 (Safe Pull and Push)" "scripts\safe_pull_and_push.ps1" "Script"

# Test Python scripts
Test-Pattern "MERGE-002 (Sync Log Summary)" "scripts\sync_log_summary.py" "Script"
Test-Pattern "MERGE-003 (Nested Repo Detector)" "scripts\nested_repo_detector.py" "Script"
Test-Pattern "MERGE-008 (File Classifier)" "scripts\merge_file_classifier.py" "Script"

Write-Host ""
Write-Host "🐍 Python Environment:" -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✅ Python available: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "  ⚠️ Python not found (required for .py scripts)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "📦 Git Environment:" -ForegroundColor Yellow
$gitVersion = git --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✅ Git available: $gitVersion" -ForegroundColor Green
} else {
    Write-Host "  ❌ Git not found (required for all patterns)" -ForegroundColor Red
    $script:FailCount++
}

Write-Host ""
Write-Host "================================" -ForegroundColor Yellow

if ($script:FailCount -eq 0) {
    Write-Host "✅ All checks passed!" -ForegroundColor Green
    Write-Host "   Safe Merge patterns are ready to use." -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Review QUICKSTART.md for usage examples" -ForegroundColor Gray
    Write-Host "  2. Run: python scripts\nested_repo_detector.py ../../../../" -ForegroundColor Gray
    Write-Host "  3. Run: .\scripts\merge_env_scan.ps1 -BaseBranch main -FeatureBranch <your-branch>" -ForegroundColor Gray
    exit 0
} else {
    Write-Host "❌ $script:FailCount check(s) failed" -ForegroundColor Red
    Write-Host "   Please review errors above and fix missing components." -ForegroundColor Red
    exit 1
}
