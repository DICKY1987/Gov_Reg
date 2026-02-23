#!/usr/bin/env pwsh
# REGISTRY Duplicate Cleanup Strategy
# Generated: 2026-02-03
# Purpose: Remove near-duplicate validation files and consolidate registry snapshots

$ErrorActionPreference = "Stop"

# Define backup directory
$backupDir = "C:\Users\richg\Gov_Reg\REGISTRY\BACKUP_FILES\20260203_duplicate_cleanup"
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null

Write-Host "=== REGISTRY Duplicate Cleanup ===" -ForegroundColor Cyan
Write-Host ""

# ====================================================================
# VALIDATION FILES - Progressive validation runs
# ====================================================================
Write-Host "[1] Validation Files (Progressive Validation Runs)" -ForegroundColor Yellow
Write-Host "    These are snapshots from successive validation gate executions:"
Write-Host "    - 104: Initial run (152 errors, 20.2 KB)"
Write-Host "    - 105: Second run (87 errors, 16.2 KB)"
Write-Host "    - 106: Final run (PASSED, 583 bytes) ✓ KEEP"
Write-Host ""

$validationFiles = @(
    @{
        Path = "01260202173939000104_validation_file_id_20260202_134237.json"
        Reason = "Superseded by subsequent validation runs"
        Keep = $false
    },
    @{
        Path = "01260202173939000105_validation_file_id_20260202_134247.json"
        Reason = "Superseded by final successful validation"
        Keep = $false
    },
    @{
        Path = "01260202173939000106_validation_file_id_20260202_134357.json"
        Reason = "FINAL VALIDATION - All tests passed"
        Keep = $true
    }
)

foreach ($file in $validationFiles) {
    $fullPath = Join-Path "C:\Users\richg\Gov_Reg\REGISTRY" $file.Path
    if (Test-Path $fullPath) {
        if (-not $file.Keep) {
            Write-Host "  ARCHIVE: $($file.Path)" -ForegroundColor Gray
            Write-Host "    Reason: $($file.Reason)" -ForegroundColor DarkGray
            Copy-Item -Path $fullPath -Destination $backupDir -Force
        } else {
            Write-Host "  KEEP:    $($file.Path)" -ForegroundColor Green
            Write-Host "    Reason: $($file.Reason)" -ForegroundColor DarkGreen
        }
    }
}

Write-Host ""

# ====================================================================
# REGISTRY FILES - Different formats of same logical registry
# ====================================================================
Write-Host "[2] REGISTRY Files (Multiple Format Snapshots)" -ForegroundColor Yellow
Write-Host "    These represent the same registry data in different formats:"
Write-Host "    - 036: YAML format (33.5 KB, older)"
Write-Host "    - 037: YAML format (47.6 KB, newer) ✓ KEEP as YAML reference"
Write-Host "    - 038: JSON format (258 KB, canonical) ✓ KEEP as primary"
Write-Host ""

$registryFiles = @(
    @{
        Path = "01260202173939000036_REGISTRY_file.yaml"
        Reason = "Older YAML snapshot, superseded by 037"
        Keep = $false
    },
    @{
        Path = "01260202173939000037_REGISTRY_file.yaml"
        Reason = "Latest YAML format - keep for human readability"
        Keep = $true
    },
    @{
        Path = "01260202173939000038_REGISTRY_file.json"
        Reason = "CANONICAL JSON - primary machine-readable format"
        Keep = $true
    }
)

foreach ($file in $registryFiles) {
    $fullPath = Join-Path "C:\Users\richg\Gov_Reg\REGISTRY" $file.Path
    if (Test-Path $fullPath) {
        if (-not $file.Keep) {
            Write-Host "  ARCHIVE: $($file.Path)" -ForegroundColor Gray
            Write-Host "    Reason: $($file.Reason)" -ForegroundColor DarkGray
            Copy-Item -Path $fullPath -Destination $backupDir -Force
        } else {
            Write-Host "  KEEP:    $($file.Path)" -ForegroundColor Green
            Write-Host "    Reason: $($file.Reason)" -ForegroundColor DarkGreen
        }
    }
}

Write-Host ""
Write-Host "=== EXECUTE CLEANUP ===" -ForegroundColor Cyan
Write-Host "Files have been backed up to: $backupDir" -ForegroundColor Green
Write-Host ""
Write-Host "To complete cleanup (remove archived files from REGISTRY/), run:" -ForegroundColor Yellow
Write-Host "  Get-ChildItem '$backupDir' | ForEach-Object { Remove-Item (Join-Path 'C:\Users\richg\Gov_Reg\REGISTRY' `$_.Name) -Force }" -ForegroundColor White
Write-Host ""
Write-Host "Files to retain in REGISTRY/:" -ForegroundColor Cyan
Write-Host "  ✓ 01260202173939000106_validation_file_id_20260202_134357.json (PASSED validation)" -ForegroundColor Green
Write-Host "  ✓ 01260202173939000037_REGISTRY_file.yaml (Latest YAML)" -ForegroundColor Green
Write-Host "  ✓ 01260202173939000038_REGISTRY_file.json (Canonical JSON)" -ForegroundColor Green
Write-Host ""
Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "  - Archived: 3 files (2 validation snapshots + 1 YAML snapshot)" -ForegroundColor Yellow
Write-Host "  - Retained: 3 files (1 validation + 2 registry formats)" -ForegroundColor Green
Write-Host "  - Space saved: ~36 KB" -ForegroundColor Cyan
Write-Host ""
