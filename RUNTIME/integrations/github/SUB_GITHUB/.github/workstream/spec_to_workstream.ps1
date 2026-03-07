#!/usr/bin/env pwsh
# DOC_LINK: DOC-SCRIPT-SPEC-TO-WORKSTREAM-071
<#
.SYNOPSIS
    Convert OpenSpec proposals to workstream bundles (PowerShell wrapper).

.DESCRIPTION
    PowerShell wrapper for spec_to_workstream.py that provides a native
    PowerShell experience for Windows users.

.PARAMETER ChangeId
    OpenSpec change ID to convert.

.PARAMETER Output
    Output workstream JSON path (default: workstreams/<ws-id>.json).

.PARAMETER WsId
    Override workstream ID (default: auto-generated from title).

.PARAMETER List
    List all available OpenSpec changes.

.PARAMETER Interactive
    Interactive mode for selecting and converting changes.

.PARAMETER DryRun
    Print bundle JSON without saving.

.EXAMPLE
    ./scripts/spec_to_workstream.ps1 -List

.EXAMPLE
    ./scripts/spec_to_workstream.ps1 -Interactive

.EXAMPLE
    ./scripts/spec_to_workstream.ps1 -ChangeId test-001

.EXAMPLE
    ./scripts/spec_to_workstream.ps1 -ChangeId test-001 -Output workstreams/custom-ws.json
#>

[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [string]$ChangeId,

    [Parameter()]
    [string]$Output,

    [Parameter()]
    [string]$WsId,

    [Parameter()]
    [switch]$List,

    [Parameter()]
    [Alias("i")]
    [switch]$Interactive,

    [Parameter()]
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Determine repository root
$RepoRoot = Split-Path -Parent $PSScriptRoot
$PythonScript = Join-Path $RepoRoot "scripts" "spec_to_workstream.py"

# Verify Python script exists
if (-not (Test-Path $PythonScript)) {
    Write-Error "Python script not found: $PythonScript"
    exit 1
}

# Build Python command arguments
$PythonArgs = @()

if ($List) {
    $PythonArgs += "--list"
}
elseif ($Interactive) {
    $PythonArgs += "--interactive"
}
else {
    if (-not $ChangeId) {
        Write-Error "ChangeId is required (or use -Interactive or -List)"
        exit 1
    }

    $PythonArgs += "--change-id", $ChangeId

    if ($Output) {
        $PythonArgs += "--output", $Output
    }

    if ($WsId) {
        $PythonArgs += "--ws-id", $WsId
    }

    if ($DryRun) {
        $PythonArgs += "--dry-run"
    }
}

# Execute Python script
try {
    & python $PythonScript @PythonArgs
    exit $LASTEXITCODE
}
catch {
    Write-Error "Failed to execute Python script: $_"
    exit 1
}
