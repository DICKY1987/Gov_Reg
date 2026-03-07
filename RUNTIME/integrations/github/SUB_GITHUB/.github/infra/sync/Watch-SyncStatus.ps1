# DOC_LINK: DOC-SCRIPT-WATCH-SYNCSTATUS-087
# Watch Git Auto-Sync Status in Real-Time
# Run this in a separate PowerShell window to monitor sync activity

param(
    [int]$RefreshSeconds = 5
)

$repoPath = "C:\Users\richg\ALL_AI\Complete AI Development Pipeline – Canonical Phase Plan"
$logFile = Join-Path $repoPath ".sync-log.txt"
$lockFile = Join-Path $env:TEMP "GitAutoSync.lock"

Write-Host "╔═══════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║      Git Auto-Sync Status Monitor           ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

try {
    while ($true) {
        Clear-Host

        Write-Host "╔═══════════════════════════════════════════════╗" -ForegroundColor Cyan
        Write-Host "║      Git Auto-Sync Status Monitor           ║" -ForegroundColor Cyan
        Write-Host "╚═══════════════════════════════════════════════╝" -ForegroundColor Cyan
        Write-Host ""

        # Check sync status
        $isRunning = $false
        $jobInfo = $null

        if (Test-Path $lockFile) {
            try {
                $lockData = Get-Content $lockFile -Raw | ConvertFrom-Json
                $job = Get-Job -Id $lockData.JobId -ErrorAction SilentlyContinue

                if ($job -and $job.State -eq "Running") {
                    $isRunning = $true
                    $jobInfo = $lockData
                    Write-Host "🟢 Status: " -NoNewline -ForegroundColor Green
                    Write-Host "RUNNING" -ForegroundColor Green -BackgroundColor DarkGreen
                    Write-Host "   Job ID: $($lockData.JobId)" -ForegroundColor Gray
                    Write-Host "   Started: $($lockData.Started)" -ForegroundColor Gray
                    Write-Host "   PID: $($lockData.ProcessId)" -ForegroundColor Gray
                } else {
                    Write-Host "🔴 Status: " -NoNewline -ForegroundColor Red
                    Write-Host "STOPPED (stale lock file)" -ForegroundColor Red -BackgroundColor DarkRed
                }
            } catch {
                Write-Host "🟡 Status: " -NoNewline -ForegroundColor Yellow
                Write-Host "UNKNOWN (lock file error)" -ForegroundColor Yellow -BackgroundColor DarkYellow
            }
        } else {
            Write-Host "🔴 Status: " -NoNewline -ForegroundColor Red
            Write-Host "NOT RUNNING" -ForegroundColor Red -BackgroundColor DarkRed
        }

        Write-Host ""
        Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
        Write-Host "Recent Activity (last 10 events):" -ForegroundColor Cyan
        Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray

        if (Test-Path $logFile) {
            $logs = Get-Content $logFile -Tail 10

            foreach ($line in $logs) {
                if ($line -match '\[SUCCESS\]') {
                    Write-Host $line -ForegroundColor Green
                } elseif ($line -match '\[ERROR\]') {
                    Write-Host $line -ForegroundColor Red
                } elseif ($line -match '\[WARN\]') {
                    Write-Host $line -ForegroundColor Yellow
                } else {
                    Write-Host $line -ForegroundColor Gray
                }
            }
        } else {
            Write-Host "  No log file found" -ForegroundColor DarkGray
        }

        Write-Host ""
        Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
        Write-Host "Repository Status:" -ForegroundColor Cyan
        Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray

        Push-Location $repoPath
        try {
            # Current branch
            $branch = git branch --show-current 2>$null
            Write-Host "  Branch: " -NoNewline -ForegroundColor Gray
            Write-Host $branch -ForegroundColor Cyan

            # Uncommitted changes
            $status = git status --porcelain 2>$null
            if ($status) {
                $changedFiles = ($status | Measure-Object).Count
                Write-Host "  Uncommitted: " -NoNewline -ForegroundColor Gray
                Write-Host "$changedFiles files" -ForegroundColor Yellow
            } else {
                Write-Host "  Uncommitted: " -NoNewline -ForegroundColor Gray
                Write-Host "None" -ForegroundColor Green
            }

            # Last commit
            $lastCommit = git log -1 --pretty=format:"%h - %s (%ar)" 2>$null
            Write-Host "  Last Commit: " -NoNewline -ForegroundColor Gray
            Write-Host $lastCommit -ForegroundColor White

        } catch {
            Write-Host "  Error reading git status" -ForegroundColor Red
        } finally {
            Pop-Location
        }

        Write-Host ""
        Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
        Write-Host "Refreshing in $RefreshSeconds seconds... (Ctrl+C to exit)" -ForegroundColor DarkGray

        Start-Sleep -Seconds $RefreshSeconds
    }
} catch {
    Write-Host "`nMonitor stopped" -ForegroundColor Yellow
}
