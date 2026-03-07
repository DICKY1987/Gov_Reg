# DOC_LINK: DOC-INFRA-GITAUTOSYNC-013
# DOC_LINK: DOC-INFRA-GITAUTOSYNC-006
# DOC_LINK: DOC-INFRA-GITAUTOSYNC-002
# DOC_LINK: DOC-SCRIPT-GITAUTOSYNC-084
#Requires -Version 7.0
<#
.SYNOPSIS
    Zero-touch Git sync daemon - runs as Windows Service
.DESCRIPTION
    Monitors repository for changes and automatically commits/pushes/pulls
    User never needs to think about sync - it's always happening in background
.PARAMETER RepoPath
    Path to Git repository to monitor
.PARAMETER CommitInterval
    Seconds between auto-commits (default: 30)
.PARAMETER SyncInterval
    Seconds between push/pull operations (default: 60)
.PARAMETER ConfigFile
    Path to .gitsync.yml configuration (default: .gitsync.yml in repo root)
#>

param(
    [Parameter(Mandatory)]
    [string]$RepoPath,

    [int]$CommitInterval = 30,
    [int]$SyncInterval = 60,
    [string]$ConfigFile = ".gitsync.yml"
)

# State tracking
$script:pendingChanges = [System.Collections.Generic.HashSet[string]]::new()
$script:lastCommit = Get-Date
$script:lastSync = Get-Date
$script:isProcessing = $false

# Load configuration
$configPath = Join-Path $RepoPath $ConfigFile
$config = if (Test-Path $configPath) {
    Get-Content $configPath -Raw | ConvertFrom-Yaml -ErrorAction SilentlyContinue
} else {
    @{
        ignore = @('.git', '.sync*', 'node_modules', '.venv', '__pycache__', '*.log', '*.tmp')
        commit_message_template = 'Auto-sync: {count} files updated'
        auto_merge_strategies = @{}
        enabled = $true
    }
}

function Write-SyncLog {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logFile = Join-Path $RepoPath ".sync-log.txt"
    "$timestamp [$Level] $Message" | Out-File -FilePath $logFile -Append
    Write-Host "[$Level] $Message" -ForegroundColor $(
        switch ($Level) {
            "ERROR" { "Red" }
            "WARN" { "Yellow" }
            "SUCCESS" { "Green" }
            default { "Gray" }
        }
    )
}

function Test-ShouldIgnore {
    param([string]$Path)

    $relativePath = $Path.Replace($RepoPath, '').TrimStart('\', '/')

    foreach ($pattern in $config.ignore) {
        if ($relativePath -like $pattern) {
            return $true
        }
    }
    return $false
}

function Invoke-AutoCommit {
    if ($script:isProcessing -or $script:pendingChanges.Count -eq 0) {
        return
    }

    $script:isProcessing = $true

    try {
        Push-Location $RepoPath

        # Filter out ignored files
        $filesToCommit = $script:pendingChanges | Where-Object { -not (Test-ShouldIgnore $_) }

        if ($filesToCommit.Count -eq 0) {
            Write-SyncLog "No changes to commit after filtering" -Level "INFO"
            $script:pendingChanges.Clear()
            return
        }

        # Stage changes
        git add -A 2>&1 | Out-Null

        # Check if there are staged changes
        $status = git status --porcelain
        if (-not $status) {
            Write-SyncLog "No staged changes detected" -Level "INFO"
            $script:pendingChanges.Clear()
            return
        }

        # Generate commit message
        $count = $filesToCommit.Count
        $message = $config.commit_message_template -replace '\{count\}', $count

        # Commit
        git commit -m $message 2>&1 | Out-Null

        if ($LASTEXITCODE -eq 0) {
            Write-SyncLog "Committed $count files" -Level "SUCCESS"
            Show-Notification "📦 Committed" "$count files committed" "Info"
            $script:lastCommit = Get-Date
            $script:pendingChanges.Clear()
        } else {
            Write-SyncLog "Commit failed with exit code $LASTEXITCODE" -Level "ERROR"
        }

    } catch {
        Write-SyncLog "Error during commit: $_" -Level "ERROR"
    } finally {
        Pop-Location
        $script:isProcessing = $false
    }
}

function Invoke-AutoSync {
    if ($script:isProcessing) {
        return
    }

    $script:isProcessing = $true

    try {
        Push-Location $RepoPath

        # Push local commits
        Write-SyncLog "Pushing to remote..." -Level "INFO"
        $pushOutput = git push origin main 2>&1

        if ($LASTEXITCODE -eq 0) {
            Write-SyncLog "Push successful" -Level "SUCCESS"
            Show-Notification "⬆️ Pushed" "Changes synced to remote" "Success"
        } elseif ($pushOutput -match "Everything up-to-date") {
            Write-SyncLog "Already up-to-date" -Level "INFO"
        } elseif ($pushOutput -match "non-fast-forward") {
            Write-SyncLog "Push rejected - need to pull first" -Level "WARN"
        } else {
            Write-SyncLog "Push failed: $pushOutput" -Level "ERROR"
            Show-Notification "❌ Push Failed" "$pushOutput" "Error"
        }

        # Pull remote changes
        Write-SyncLog "Pulling from remote..." -Level "INFO"
        $pullOutput = git pull origin main --no-edit 2>&1 | Out-String

        if ($LASTEXITCODE -eq 0) {
            if ($pullOutput -match "Already up to date") {
                Write-SyncLog "Already up-to-date" -Level "INFO"
            } else {
                Write-SyncLog "Pull successful" -Level "SUCCESS"
                Show-Notification "⬇️ Pulled" "Remote changes downloaded" "Success"
            }
        } elseif ($pullOutput -match "CONFLICT") {
            Write-SyncLog "CONFLICT detected - manual resolution required" -Level "ERROR"
            Show-Notification "⚠️ Conflict" "Manual merge required!" "Warning"
        } else {
            Write-SyncLog "Pull failed: $pullOutput" -Level "ERROR"
            Show-Notification "❌ Pull Failed" "$pullOutput" "Error"
        }

        $script:lastSync = Get-Date

    } catch {
        Write-SyncLog "Error during sync: $_" -Level "ERROR"
    } finally {
        Pop-Location
        $script:isProcessing = $false
    }
}

function Show-Notification {
    param(
        [string]$Title,
        [string]$Message,
        [string]$Type = "Info"
    )

    # Console notification (always visible in PowerShell window)
    $emoji = switch ($Type) {
        "Success" { "✅" }
        "Warning" { "⚠️" }
        "Error" { "❌" }
        default { "ℹ️" }
    }

    $color = switch ($Type) {
        "Success" { "Green" }
        "Warning" { "Yellow" }
        "Error" { "Red" }
        default { "Cyan" }
    }

    $timestamp = Get-Date -Format "HH:mm:ss"
    Write-Host "`n$emoji [$timestamp] $Title - $Message" -ForegroundColor $color

    # Windows Toast Notification
    try {
        [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
        [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null

        $template = @"
<toast>
    <visual>
        <binding template="ToastGeneric">
            <text>Git Auto-Sync</text>
            <text>$Title</text>
            <text>$Message</text>
        </binding>
    </visual>
</toast>
"@

        $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
        $xml.LoadXml($template)
        $toast = New-Object Windows.UI.Notifications.ToastNotification $xml
        [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Git Auto-Sync").Show($toast)
    } catch {
        # Toast notifications not available, skip silently
    }
}

function Start-FileWatcher {
    Write-SyncLog "Starting file watcher on: $RepoPath" -Level "INFO"

    $watcher = New-Object System.IO.FileSystemWatcher
    $watcher.Path = $RepoPath
    $watcher.Filter = "*.*"
    $watcher.IncludeSubdirectories = $true
    $watcher.NotifyFilter = [System.IO.NotifyFilters]::LastWrite -bor
                            [System.IO.NotifyFilters]::FileName -bor
                            [System.IO.NotifyFilters]::DirectoryName

    $onChanged = {
        param($sender, $e)

        $path = $e.FullPath

        if (Test-ShouldIgnore $path) {
            return
        }

        $null = $script:pendingChanges.Add($path)
        Write-SyncLog "Detected change: $($e.ChangeType) - $(Split-Path $path -Leaf)" -Level "INFO"
    }

    $handlers = @(
        Register-ObjectEvent -InputObject $watcher -EventName Changed -Action $onChanged
        Register-ObjectEvent -InputObject $watcher -EventName Created -Action $onChanged
        Register-ObjectEvent -InputObject $watcher -EventName Deleted -Action $onChanged
        Register-ObjectEvent -InputObject $watcher -EventName Renamed -Action $onChanged
    )

    $watcher.EnableRaisingEvents = $true

    Write-SyncLog "File watcher active" -Level "SUCCESS"

    return @{
        Watcher = $watcher
        Handlers = $handlers
    }
}

try {
    if (-not $config.enabled) {
        Write-SyncLog "Sync is disabled in config - exiting" -Level "WARN"
        exit 0
    }

    if (-not (Test-Path (Join-Path $RepoPath ".git"))) {
        Write-SyncLog "Not a Git repository: $RepoPath" -Level "ERROR"
        exit 1
    }

    Write-SyncLog "=== Git Auto-Sync Started ===" -Level "INFO"
    Write-SyncLog "Repository: $RepoPath" -Level "INFO"
    Write-SyncLog "Commit interval: ${CommitInterval}s" -Level "INFO"
    Write-SyncLog "Sync interval: ${SyncInterval}s" -Level "INFO"

    Show-Notification "🚀 Auto-Sync Started" "Monitoring repository for changes" "Success"

    $watcherInfo = Start-FileWatcher

    while ($true) {
        $timeSinceCommit = ((Get-Date) - $script:lastCommit).TotalSeconds
        if ($script:pendingChanges.Count -gt 0 -and $timeSinceCommit -ge $CommitInterval) {
            Invoke-AutoCommit
        }

        $timeSinceSync = ((Get-Date) - $script:lastSync).TotalSeconds
        if ($timeSinceSync -ge $SyncInterval) {
            Invoke-AutoSync
        }

        Start-Sleep -Seconds 5
    }

} catch {
    Write-SyncLog "Fatal error: $_" -Level "ERROR"
    exit 1
} finally {
    if ($watcherInfo) {
        $watcherInfo.Watcher.EnableRaisingEvents = $false
        $watcherInfo.Handlers | ForEach-Object { Unregister-Event -SourceIdentifier $_.Name }
        $watcherInfo.Watcher.Dispose()
    }
    Write-SyncLog "=== Git Auto-Sync Stopped ===" -Level "INFO"
}
