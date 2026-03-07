# DOC_LINK: DOC-PAT-SAFE-MERGE-234
<#
.SYNOPSIS
    Safe Merge Patterns - Complete Workflow Wrapper

.DESCRIPTION
    Comprehensive wrapper that orchestrates all safe merge patterns.
    Use this as your primary merge interface.

.PARAMETER Action
    Action to perform: scan, normalize, merge, push

.PARAMETER BaseBranch
    Target branch (default: main)

.PARAMETER FeatureBranch
    Source branch to merge

.PARAMETER AllowAutoPush
    Enable automatic push after successful merge

.EXAMPLE
    .\safe_merge.ps1 -Action scan -BaseBranch main -FeatureBranch feature/xyz

.EXAMPLE
    .\safe_merge.ps1 -Action normalize

.EXAMPLE
    .\safe_merge.ps1 -Action merge -BaseBranch main -FeatureBranch feature/xyz -AllowAutoPush

.EXAMPLE
    .\safe_merge.ps1 -Action push
#>

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("scan", "normalize", "merge", "push", "full")]
    [string]$Action,

    [string]$BaseBranch = "main",
    [string]$FeatureBranch = "",
    [string]$RemoteName = "origin",
    [switch]$AllowAutoPush,
    [ValidateSet("absorb_as_folder", "keep_as_submodule")]
    [string]$NormalizePolicy = "absorb_as_folder",
    [string]$InstanceId = "powershell_$(Get-Date -Format 'HHmmss')"
)

$ErrorActionPreference = "Stop"
$ScriptDir = $PSScriptRoot

Write-Host ""
Write-Host "🚀 Safe Merge Pattern Library" -ForegroundColor Cyan
Write-Host "   Action: $Action" -ForegroundColor Gray
Write-Host ""

function Invoke-Pattern {
    param(
        [string]$PatternName,
        [string]$Script,
        [hashtable]$Params
    )

    Write-Host "▶️  Running $PatternName..." -ForegroundColor Yellow

    # Handle both direct scripts and scripts/ subdirectory
    if ($Script.Contains('\') -or $Script.Contains('/')) {
        $scriptPath = Join-Path $ScriptDir $Script
    } else {
        $scriptPath = Join-Path $ScriptDir "scripts\$Script"
    }

    if ($Script.EndsWith('.ps1')) {
        & $scriptPath @Params
    } else {
        $pythonArgs = @($scriptPath)
        foreach ($key in $Params.Keys) {
            if ($Params[$key] -is [switch] -or $Params[$key] -is [bool]) {
                if ($Params[$key]) {
                    $pythonArgs += "--$($key.ToLower())"
                }
            } else {
                $pythonArgs += "--$($key.ToLower())", $Params[$key]
            }
        }
        python @pythonArgs
    }

    $exitCode = $LASTEXITCODE

    if ($exitCode -eq 0) {
        Write-Host "   ✅ $PatternName completed successfully" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️ $PatternName exited with code $exitCode" -ForegroundColor Yellow
    }

    Write-Host ""
    return $exitCode
}

try {
    switch ($Action) {
        "scan" {
            Write-Host "📋 SCAN MODE: Environment + Nested Repos + File Classification" -ForegroundColor Cyan
            Write-Host ""

            if (-not $FeatureBranch) {
                $FeatureBranch = git branch --show-current
                Write-Host "Using current branch as feature: $FeatureBranch" -ForegroundColor Gray
                Write-Host ""
            }

            # MERGE-001: Environment Scan
            Invoke-Pattern -PatternName "MERGE-001 (Environment Scan)" `
                          -Script "merge_env_scan.ps1" `
                          -Params @{
                              BaseBranch = $BaseBranch
                              FeatureBranch = $FeatureBranch
                              RemoteName = $RemoteName
                          }

            # MERGE-003: Nested Repo Detector
            Invoke-Pattern -PatternName "MERGE-003 (Nested Repo Detector)" `
                          -Script "nested_repo_detector.py" `
                          -Params @{
                              work_dir = "."
                          }

            # MERGE-008: File Classifier
            Invoke-Pattern -PatternName "MERGE-008 (File Classifier)" `
                          -Script "merge_file_classifier.py" `
                          -Params @{
                              work_dir = "."
                          }

            Write-Host "📊 Scan complete! Review the following files:" -ForegroundColor Green
            Write-Host "   - env_scan.safe_merge.json" -ForegroundColor Gray
            Write-Host "   - nested_repos_report.json" -ForegroundColor Gray
            Write-Host "   - merge_file_classes.json" -ForegroundColor Gray
        }

        "normalize" {
            Write-Host "🔧 NORMALIZE MODE: Fix Nested Repos" -ForegroundColor Cyan
            Write-Host ""

            # MERGE-005: Nested Repo Normalizer
            Invoke-Pattern -PatternName "MERGE-005 (Nested Repo Normalizer)" `
                          -Script "nested_repo_normalizer.py" `
                          -Params @{
                              work_dir = "."
                              policy = $NormalizePolicy
                          }

            Write-Host "✅ Normalization complete!" -ForegroundColor Green
        }

        "merge" {
            Write-Host "🔀 MERGE MODE: Full Safe Merge Workflow" -ForegroundColor Cyan
            Write-Host ""

            if (-not $FeatureBranch) {
                throw "FeatureBranch parameter required for merge action"
            }

            # MERGE-004: Safe Merge Automation
            $params = @{
                BaseBranch = $BaseBranch
                FeatureBranch = $FeatureBranch
                RemoteName = $RemoteName
            }

            if ($AllowAutoPush) {
                $params.AllowAutoPush = $true
            }

            Invoke-Pattern -PatternName "MERGE-004 (Safe Merge Automation)" `
                          -Script "safe_merge_auto.ps1" `
                          -Params $params

            Write-Host "✅ Merge workflow complete!" -ForegroundColor Green
        }

        "push" {
            Write-Host "📤 PUSH MODE: Safe Push with Multi-Clone Guard" -ForegroundColor Cyan
            Write-Host ""

            $currentBranch = git branch --show-current

            # MERGE-007: Multi-Clone Guard
            Invoke-Pattern -PatternName "MERGE-007 (Multi-Clone Guard)" `
                          -Script "multi_clone_guard.py" `
                          -Params @{
                              instance_id = $InstanceId
                              branch = $currentBranch
                              remote = $RemoteName
                          }

            Write-Host "✅ Push complete!" -ForegroundColor Green
        }

        "full" {
            Write-Host "🚀 FULL MODE: Complete Safe Merge Pipeline" -ForegroundColor Cyan
            Write-Host ""

            if (-not $FeatureBranch) {
                throw "FeatureBranch parameter required for full workflow"
            }

            Write-Host "Step 1/4: Scan" -ForegroundColor Yellow
            & $PSCommandPath -Action scan -BaseBranch $BaseBranch -FeatureBranch $FeatureBranch -RemoteName $RemoteName

            Write-Host "Step 2/4: Normalize" -ForegroundColor Yellow
            & $PSCommandPath -Action normalize -NormalizePolicy $NormalizePolicy

            Write-Host "Step 3/4: Merge" -ForegroundColor Yellow
            $mergeParams = @{
                Action = "merge"
                BaseBranch = $BaseBranch
                FeatureBranch = $FeatureBranch
                RemoteName = $RemoteName
            }
            if ($AllowAutoPush) {
                $mergeParams.AllowAutoPush = $true
            }
            & $PSCommandPath @mergeParams

            Write-Host "✅ Full workflow complete!" -ForegroundColor Green
        }
    }

    Write-Host ""
    Write-Host "✅ Action '$Action' completed successfully" -ForegroundColor Green
    exit 0

} catch {
    Write-Host ""
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "💡 Troubleshooting:" -ForegroundColor Yellow
    Write-Host "   1. Check pattern outputs (*.json files)" -ForegroundColor Gray
    Write-Host "   2. Review error message above" -ForegroundColor Gray
    Write-Host "   3. Run with -Action scan to diagnose" -ForegroundColor Gray
    exit 1
}
