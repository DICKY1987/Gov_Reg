# DOC_LINK: DOC-SCRIPT-START-AUTOSYNC-086
# Smart Auto-Start Git Sync
# Only starts sync if no other PowerShell window has it running
# Add this to your PowerShell profile: $PROFILE

param(
    [string]$RepoPath = "C:\Users\richg\ALL_AI\Complete AI Development Pipeline – Canonical Phase Plan"
)

# Use a simpler lock file approach instead of mutex
$lockFile = Join-Path $env:TEMP "GitAutoSync.lock"

# Check if lock file exists and job is still running
$shouldStart = $false
if (Test-Path $lockFile) {
    try {
        $lockData = Get-Content $lockFile -Raw | ConvertFrom-Json
        $existingJob = Get-Job -Id $lockData.JobId -ErrorAction SilentlyContinue

        if ($existingJob -and $existingJob.State -eq "Running") {
            # Sync already running in another window
            Write-Host "✓ Git Auto-Sync already running in another PowerShell window" -ForegroundColor Yellow
            Write-Host "  (Job ID: $($lockData.JobId), PID: $($lockData.ProcessId))" -ForegroundColor Gray
            $shouldStart = $false
        } else {
            # Lock file exists but job is dead - clean up and start fresh
            Remove-Item $lockFile -Force -ErrorAction SilentlyContinue
            $shouldStart = $true
        }
    } catch {
        # Lock file corrupted - start fresh
        Remove-Item $lockFile -Force -ErrorAction SilentlyContinue
        $shouldStart = $true
    }
} else {
    # No lock file - we're the first
    $shouldStart = $true
}

if ($shouldStart) {
    # We're the first PowerShell window - start the sync
    Write-Host "╔══════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║  Starting Git Auto-Sync (First Window)  ║" -ForegroundColor Cyan
    Write-Host "╚══════════════════════════════════════════╝" -ForegroundColor Cyan

    # Start sync job
    $global:GitSyncJob = Start-Job -Name "GitAutoSync-$PID" -ScriptBlock {
        param($RepoPath)
        Import-Module powershell-yaml -ErrorAction SilentlyContinue
        & "C:\Program Files\GitAutoSync\GitAutoSync.ps1" -RepoPath $RepoPath -CommitInterval 30 -SyncInterval 60
    } -ArgumentList $RepoPath

    # Create lock file
    $lockData = @{
        JobId = $global:GitSyncJob.Id
        ProcessId = $PID
        Started = Get-Date -Format "o"
        RepoPath = $RepoPath
    } | ConvertTo-Json

    $lockData | Out-File -FilePath $lockFile -Force

    # Wait a moment for startup
    Start-Sleep -Seconds 2

    Write-Host "`n✓ Sync active (Job ID: $($global:GitSyncJob.Id))" -ForegroundColor Green
    Write-Host "✓ Lock file created - other windows will not start duplicate sync" -ForegroundColor Green
    Write-Host "`n📝 Logs: Get-Content .sync-log.txt -Tail 20 -Wait" -ForegroundColor Gray

    # Clean up lock file when PowerShell window closes
    Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action {
        param($sender, $e)
        Stop-Job -Name "GitAutoSync-*" -ErrorAction SilentlyContinue
        Remove-Job -Name "GitAutoSync-*" -Force -ErrorAction SilentlyContinue
        Remove-Item -Path $using:lockFile -Force -ErrorAction SilentlyContinue
    } | Out-Null
}
