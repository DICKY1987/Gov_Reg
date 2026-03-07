# Fix Scheduled Tasks - Update Paths to Current Architecture
# DOC_ID: DOC-SCRIPT-FIX-SCHEDULED-TASKS-001
# Purpose: Update DOC_ID_V3_* scheduled tasks to point to correct .bat files

Write-Host "=== Fixing DOC-ID Scheduled Tasks ===" -ForegroundColor Cyan
Write-Host ""

$repoRoot = "C:\Users\richg\ALL_AI"
$docIdRoot = "$repoRoot\RUNTIME\doc_id\SUB_DOC_ID"
$hooksPath = "$docIdRoot\3_AUTOMATION_HOOKS"

$tasks = @(
    @{
        Name = "DOC_ID_V3_Nightly_Scan"
        Script = "$hooksPath\run_nightly_scan.bat"
        Time = "03:00"
    },
    @{
        Name = "DOC_ID_V3_Health_Check"
        Script = "$hooksPath\run_health_check.bat"
        Time = "09:00"
    },
    @{
        Name = "DOC_ID_V3_Dashboard"
        Script = "$hooksPath\run_dashboard.bat"
        Time = "08:00"
    }
)

foreach ($task in $tasks) {
    Write-Host "Updating $($task.Name)..." -ForegroundColor Yellow

    # Check if task exists
    $existingTask = Get-ScheduledTask -TaskName $task.Name -ErrorAction SilentlyContinue

    if ($existingTask) {
        # Unregister old task
        Unregister-ScheduledTask -TaskName $task.Name -Confirm:$false
        Write-Host "  Removed old task" -ForegroundColor Gray
    }

    # Verify script exists
    if (-not (Test-Path $task.Script)) {
        Write-Host "  ERROR: Script not found: $($task.Script)" -ForegroundColor Red
        continue
    }

    # Create action
    $action = New-ScheduledTaskAction -Execute $task.Script

    # Create trigger (daily at specified time)
    $trigger = New-ScheduledTaskTrigger -Daily -At $task.Time

    # Create principal (run as current user)
    $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive

    # Create settings
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

    # Register task
    Register-ScheduledTask -TaskName $task.Name `
                          -Action $action `
                          -Trigger $trigger `
                          -Principal $principal `
                          -Settings $settings `
                          -Description "DOC-ID Automation - $($task.Name.Replace('DOC_ID_V3_', ''))" | Out-Null

    Write-Host "  Registered new task pointing to: $($task.Script)" -ForegroundColor Green
    Write-Host "  Scheduled for: $($task.Time) daily" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== Verification ===" -ForegroundColor Cyan
Get-ScheduledTask -TaskName "DOC_ID_V3_*" | ForEach-Object {
    $info = Get-ScheduledTaskInfo -TaskName $_.TaskName
    Write-Host "$($_.TaskName):" -ForegroundColor Yellow
    Write-Host "  Path: $($_.Actions[0].Execute)" -ForegroundColor White
    Write-Host "  State: $($_.State)" -ForegroundColor $(if ($_.State -eq "Ready") { "Green" } else { "Red" })
    Write-Host "  Next Run: $($info.NextRunTime)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Scheduled tasks updated successfully!" -ForegroundColor Green
