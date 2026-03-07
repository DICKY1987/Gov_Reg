# DOC_LINK: DOC-SCRIPT-INSTALL-GITAUTOSYNC-085
#Requires -Version 7.0
<#
.SYNOPSIS
    Install Git Auto-Sync as a Windows Service
.DESCRIPTION
    One-command installation of zero-touch Git sync
    Sets up background service, configures Git, creates startup shortcuts
.PARAMETER RepoPath
    Path to Git repository (default: current directory)
.PARAMETER ServiceName
    Custom service name (default: auto-generated from repo name)
.PARAMETER StartImmediately
    Start service immediately after installation (default: true)
#>

param(
    [string]$RepoPath = $PWD.Path,
    [string]$ServiceName = "",
    [switch]$StartImmediately = $true
)

$ErrorActionPreference = "Stop"

function Write-InstallStep {
    param([string]$Message, [string]$Status = "INFO")
    $color = switch ($Status) {
        "SUCCESS" { "Green" }
        "ERROR" { "Red" }
        "WARN" { "Yellow" }
        default { "Cyan" }
    }
    Write-Host "  $Message" -ForegroundColor $color
}

function Test-Prerequisites {
    Write-Host "`n[Checking Prerequisites]" -ForegroundColor Cyan

    $git = Get-Command git -ErrorAction SilentlyContinue
    if (-not $git) {
        Write-InstallStep "✗ Git not found" -Status "ERROR"
        Write-Host "`nInstall Git: winget install Git.Git" -ForegroundColor Yellow
        exit 1
    }
    Write-InstallStep "✓ Git ($($git.Version))" -Status "SUCCESS"

    if ($PSVersionTable.PSVersion.Major -lt 7) {
        Write-InstallStep "✗ PowerShell 7+ required (current: $($PSVersionTable.PSVersion))" -Status "ERROR"
        Write-Host "`nInstall PowerShell 7: winget install Microsoft.PowerShell" -ForegroundColor Yellow
        exit 1
    }
    Write-InstallStep "✓ PowerShell $($PSVersionTable.PSVersion)" -Status "SUCCESS"

    if (-not (Test-Path (Join-Path $RepoPath ".git"))) {
        Write-InstallStep "✗ Not a Git repository: $RepoPath" -Status "ERROR"
        exit 1
    }
    Write-InstallStep "✓ Git repository detected" -Status "SUCCESS"

    $isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    if (-not $isAdmin) {
        Write-InstallStep "✗ Administrator privileges required" -Status "ERROR"
        Write-Host "`nRestart PowerShell as Administrator" -ForegroundColor Yellow
        exit 1
    }
    Write-InstallStep "✓ Running as Administrator" -Status "SUCCESS"
}

function Install-SyncService {
    Write-Host "`n[Installing Service]" -ForegroundColor Cyan

    $repoName = Split-Path $RepoPath -Leaf
    $serviceName = if ($ServiceName) { $ServiceName } else { "GitAutoSync-$repoName" }

    $installPath = "C:\Program Files\GitAutoSync"
    New-Item -Path $installPath -ItemType Directory -Force | Out-Null

    $scriptSource = Join-Path $PSScriptRoot "GitAutoSync.ps1"
    $scriptDest = Join-Path $installPath "GitAutoSync.ps1"

    if (Test-Path $scriptSource) {
        Copy-Item -Path $scriptSource -Destination $scriptDest -Force
        Write-InstallStep "✓ Copied GitAutoSync.ps1 to $installPath" -Status "SUCCESS"
    } else {
        Write-InstallStep "✗ GitAutoSync.ps1 not found at $scriptSource" -Status "ERROR"
        exit 1
    }

    $existingService = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
    if ($existingService) {
        Write-InstallStep "Service already exists - removing..." -Status "WARN"
        Stop-Service -Name $serviceName -Force -ErrorAction SilentlyContinue
        sc.exe delete $serviceName | Out-Null
        Start-Sleep -Seconds 2
    }

    $pwshPath = (Get-Command pwsh).Source
    $serviceParams = @"
-NoProfile -ExecutionPolicy Bypass -File "$scriptDest" -RepoPath "$RepoPath" -CommitInterval 30 -SyncInterval 60
"@

    sc.exe create $serviceName binPath= "`"$pwshPath`" $serviceParams" start= auto displayname= "Git Auto Sync - $repoName" | Out-Null

    if ($LASTEXITCODE -eq 0) {
        Write-InstallStep "✓ Service created: $serviceName" -Status "SUCCESS"
    } else {
        Write-InstallStep "✗ Service creation failed" -Status "ERROR"
        exit 1
    }

    sc.exe description $serviceName "Automatically syncs Git repository with remote: $RepoPath" | Out-Null

    return $serviceName
}

function Install-ConfigFile {
    Write-Host "`n[Creating Configuration]" -ForegroundColor Cyan

    $configPath = Join-Path $RepoPath ".gitsync.yml"

    if (Test-Path $configPath) {
        Write-InstallStep "✓ Config already exists: .gitsync.yml" -Status "INFO"
        return
    }

    $defaultConfig = @"
# Git Auto-Sync Configuration

enabled: true

# Files/folders to ignore
ignore:
  - .git
  - .sync*
  - node_modules
  - .venv
  - __pycache__
  - '*.log'
  - '*.tmp'
  - .worktrees
  - logs

# Commit message template ({count} = number of files)
commit_message_template: 'Auto-sync: {count} files updated'

# Auto-merge strategies (optional)
auto_merge_strategies:
  # '*.md': 'ours'     # Always keep local markdown
  # '*.json': 'theirs' # Always take remote JSON
"@

    $defaultConfig | Out-File -FilePath $configPath -Encoding UTF8
    Write-InstallStep "✓ Created .gitsync.yml" -Status "SUCCESS"
}

function Install-GitIgnore {
    Write-Host "`n[Updating .gitignore]" -ForegroundColor Cyan

    $gitignorePath = Join-Path $RepoPath ".gitignore"

    $syncPatterns = @(
        ".sync-log.txt"
        ".sync-lock"
        ".sync-manifest.json"
    )

    $existingContent = if (Test-Path $gitignorePath) {
        Get-Content $gitignorePath -Raw
    } else {
        ""
    }

    $added = 0
    foreach ($pattern in $syncPatterns) {
        if ($existingContent -notmatch [regex]::Escape($pattern)) {
            Add-Content -Path $gitignorePath -Value $pattern
            $added++
        }
    }

    if ($added -gt 0) {
        Write-InstallStep "✓ Added $added patterns to .gitignore" -Status "SUCCESS"
    } else {
        Write-InstallStep "✓ .gitignore already configured" -Status "INFO"
    }
}

function Set-GitConfiguration {
    Write-Host "`n[Configuring Git]" -ForegroundColor Cyan

    Push-Location $RepoPath

    git config pull.rebase false | Out-Null
    Write-InstallStep "✓ Set pull.rebase = false" -Status "SUCCESS"

    git config merge.conflictstyle diff3 | Out-Null
    Write-InstallStep "✓ Set merge.conflictstyle = diff3" -Status "SUCCESS"

    $credential = git config credential.helper
    if (-not $credential) {
        git config credential.helper manager-core | Out-Null
        Write-InstallStep "✓ Set credential.helper = manager-core" -Status "SUCCESS"
    } else {
        Write-InstallStep "✓ Credential helper already configured: $credential" -Status "INFO"
    }

    Pop-Location
}

function Start-SyncService {
    param([string]$ServiceName)

    Write-Host "`n[Starting Service]" -ForegroundColor Cyan

    Start-Service -Name $ServiceName

    Start-Sleep -Seconds 2

    $service = Get-Service -Name $ServiceName
    if ($service.Status -eq "Running") {
        Write-InstallStep "✓ Service started successfully" -Status "SUCCESS"
    } else {
        Write-InstallStep "✗ Service failed to start (Status: $($service.Status))" -Status "ERROR"
    }
}

function Show-Summary {
    param([string]$ServiceName)

    Write-Host "`n╔════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║  Git Auto-Sync Installation Complete!             ║" -ForegroundColor Green
    Write-Host "╚════════════════════════════════════════════════════╝" -ForegroundColor Green

    Write-Host "`nService Details:" -ForegroundColor Cyan
    Write-Host "  Name:       $ServiceName"
    Write-Host "  Repository: $RepoPath"
    Write-Host "  Status:     $(( Get-Service -Name $ServiceName).Status)"

    Write-Host "`nWhat happens now:" -ForegroundColor Cyan
    Write-Host "  1. Save any file in the repository"
    Write-Host "  2. Changes auto-commit within 30 seconds"
    Write-Host "  3. Commits auto-push within 60 seconds"
    Write-Host "  4. Remote changes auto-pull every 60 seconds"

    Write-Host "`nManagement Commands:" -ForegroundColor Cyan
    Write-Host "  Stop:    Stop-Service $ServiceName"
    Write-Host "  Start:   Start-Service $ServiceName"
    Write-Host "  Status:  Get-Service $ServiceName"
    Write-Host "  Logs:    Get-Content '$RepoPath\.sync-log.txt' -Tail 20 -Wait"

    Write-Host "`nConfiguration:" -ForegroundColor Cyan
    Write-Host "  Edit: $RepoPath\.gitsync.yml"
    Write-Host "  Restart service after config changes"

    Write-Host "`n✨ You can now work normally. Sync happens automatically! ✨`n" -ForegroundColor Yellow
}

try {
    Write-Host "`n╔════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║  Git Auto-Sync Installer                           ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════════════╝" -ForegroundColor Cyan

    Test-Prerequisites

    $serviceName = Install-SyncService
    Install-ConfigFile
    Install-GitIgnore
    Set-GitConfiguration

    if ($StartImmediately) {
        Start-SyncService -ServiceName $serviceName
    }

    Show-Summary -ServiceName $serviceName

} catch {
    Write-Host "`n✗ Installation failed: $_" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor Gray
    exit 1
}
