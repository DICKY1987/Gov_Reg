# DOC_LINK: DOC-SCRIPT-CHECK-WORKSTREAM-STATUS-055
<#
.SYNOPSIS
  Workstream Status Checker (PowerShell)

.DESCRIPTION
  Mirrors scripts/check_workstream_status.sh to report status of key
  workstreams across PH-01 to PH-03 on Windows/PowerShell.
#>

param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Section($title) {
  Write-Host ('?' * 62)
  Write-Host ("?? $title")
  Write-Host ('?' * 62)
}

function Check-File($path) {
  if (Test-Path -LiteralPath $path -PathType Leaf) {
    Write-Host "    ? EXISTS" -ForegroundColor Green
    return $true
  }
  try {
    $null = git show "main:$path" 2>$null
    Write-Host "    ? EXISTS in main" -ForegroundColor Green
    return $true
  } catch {
    Write-Host "    ? NOT FOUND" -ForegroundColor Red
    return $false
  }
}

function Check-Implementation($path, $functionName) {
  $pattern = "def\s+$([regex]::Escape($functionName))\b"
  if ((Test-Path -LiteralPath $path -PathType Leaf) -and (Select-String -Path $path -Pattern $pattern -SimpleMatch:$false -ErrorAction SilentlyContinue)) {
    Write-Host "    ? IMPLEMENTED" -ForegroundColor Green
    return $true
  }
  try {
    $content = git show "main:$path" 2>$null
    if ($content -match $pattern) {
      Write-Host "    ? IMPLEMENTED in main" -ForegroundColor Green
      return $true
    }
  } catch {}
  Write-Host "    ? STUB ONLY" -ForegroundColor Red
  return $false
}

Write-Host "WORKSTREAM STATUS CHECKER - PH-01 to PH-03" -ForegroundColor Cyan
Write-Host

Write-Section "ACTIVE WORKSTREAM BRANCHES"
$branches = git branch -a | Select-String 'workstream/' | ForEach-Object { $_.Line -replace '^[+* ]*','  ' -replace 'remotes/origin/','' }
if ($branches) { $branches | ForEach-Object { Write-Host $_ } } else { Write-Host '  (none)' }
Write-Host

Write-Section "ACTIVE WORKTREES"
$worktrees = git worktree list | Select-String 'ws-ph'
if ($worktrees) { $worktrees | ForEach-Object { Write-Host ('  ' + $_.Line) } } else { Write-Host '  (none)' }
Write-Host

Write-Section "KEY FILE IMPLEMENTATION STATUS"

# PH-01
Write-Host "PH-01: Spec Alignment & Index Mapping"
Write-Host "  ws-ph01-module-stubs (Codex):"
# Resolve core DB module via path registry to avoid hardcoded paths
$dbPath = (& python scripts/paths_resolve_cli.py resolve core.db) 2>$null
if (-not $dbPath) { $dbPath = "src/pipeline/db.py" }
$dbPath = $dbPath.Trim()
Write-Host "    core DB module: $dbPath"
Check-File $dbPath | Out-Null
Write-Host
Write-Host "  ws-ph01-index-scanner (Codex):"
Write-Host "    scripts/generate_spec_index.py:"
Check-File "scripts/generate_spec_index.py" | Out-Null
Write-Host
Write-Host "  ws-ph01-spec-mapping (Claude):"
Write-Host "    docs/spec/spec_index_map.md:"
Check-File "docs/spec/spec_index_map.md" | Out-Null
Write-Host
Write-Host "  ws-ph01-tests (Claude):"
Write-Host "    tests/pipeline/test_spec_index.py:"
Check-File "tests/pipeline/test_spec_index.py" | Out-Null
Write-Host
Write-Host "  ws-ph01-docs (Codex):"
Write-Host "    docs/ARCHITECTURE.md (updated):"
$archPath = (& python scripts/paths_resolve_cli.py resolve docs.architecture_main) 2>$null
if (-not $archPath) { $archPath = "docs/ARCHITECTURE.md" }
$archPath = $archPath.Trim()
Check-File $archPath | Out-Null
Write-Host

# PH-02
Write-Host "PH-02: Data Model & State Machine"
Write-Host "  ws-ph02-schema (Codex):"
Write-Host "    schema/schema.sql:"
Check-File "schema/schema.sql" | Out-Null
Write-Host
Write-Host "  ws-ph02-db-core (Codex):"
Write-Host "    $dbPath::get_connection():"
Check-Implementation $dbPath "get_connection" | Out-Null
Write-Host
Write-Host "  ws-ph02-state-machine (Claude):"
Write-Host "    $dbPath::validate_state_transition():"
Check-Implementation $dbPath "validate_state_transition" | Out-Null
Write-Host
Write-Host "  ws-ph02-crud (Claude):"
Write-Host "    $dbPath::create_run():"
Check-Implementation $dbPath "create_run" | Out-Null
Write-Host
Write-Host "  ws-ph02-scripts (Codex):"
Write-Host "    scripts/init_db.py:"
Check-File "scripts/init_db.py" | Out-Null
Write-Host
Write-Host "  ws-ph02-docs (Codex):"
Write-Host "    docs/state_machine.md:"
Check-File "docs/state_machine.md" | Out-Null
Write-Host
Write-Host "  ws-ph02-tests (Claude):"
Write-Host "    tests/pipeline/test_db_state.py:"
Check-File "tests/pipeline/test_db_state.py" | Out-Null
Write-Host

# PH-03
Write-Host "PH-03: Tool Profiles & Adapter Layer"
Write-Host "  ws-ph03-profiles (Codex):"
Write-Host "    config/tool_profiles.json:"
Check-File "config/tool_profiles.json" | Out-Null
Write-Host
Write-Host "  ws-ph03-adapter-core (Claude):"
Write-Host "    src/pipeline/tools.py::run_tool():"
Check-Implementation "src/pipeline/tools.py" "run_tool" | Out-Null
Write-Host
Write-Host "  ws-ph03-db-integration (Claude):"
Write-Host "    src/pipeline/tools.py (with DB calls):"
$integrated = $false
if (Test-Path "src/pipeline/tools.py") {
  $integrated = Select-String -Path "src/pipeline/tools.py" -Pattern 'record_event|record_error' -SimpleMatch:$false -ErrorAction SilentlyContinue
}
if (-not $integrated) {
  try {
    $content = git show 'main:src/pipeline/tools.py' 2>$null
    if ($content -match 'record_event|record_error') { $integrated = $true }
  } catch {}
}
if ($integrated) { Write-Host "    ? INTEGRATED" -ForegroundColor Green } else { Write-Host "    ? NOT INTEGRATED" -ForegroundColor Red }
Write-Host
Write-Host "  ws-ph03-tests (Claude):"
Write-Host "    tests/pipeline/test_tools.py:"
Check-File "tests/pipeline/test_tools.py" | Out-Null
Write-Host
Write-Host "  ws-ph03-docs (Codex):"
Write-Host "    docs/PHASE_PLAN.md (updated):"
$phasePlan = (& python scripts/paths_resolve_cli.py resolve docs.phase_plan) 2>$null
if (-not $phasePlan) { $phasePlan = "docs/PHASE_PLAN.md" }
$phasePlan = $phasePlan.Trim()
Check-File $phasePlan | Out-Null
Write-Host

Write-Section "SUMMARY"
$totalBranches = (git branch -a | Select-String 'workstream/' | Measure-Object).Count
$totalWorktrees = (git worktree list | Select-String 'ws-ph' | Measure-Object).Count
Write-Host "  Total workstream branches: $totalBranches / 17"
Write-Host "  Active worktrees: $totalWorktrees"
Write-Host
