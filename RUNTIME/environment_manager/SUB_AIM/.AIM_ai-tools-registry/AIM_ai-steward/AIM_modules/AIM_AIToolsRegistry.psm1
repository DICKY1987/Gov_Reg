Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-RegistryRoot([string]$RegistryRoot) {
  if ($RegistryRoot) { return $RegistryRoot }
  if ($env:AI_TOOLS_REGISTRY_ROOT) { return $env:AI_TOOLS_REGISTRY_ROOT }
  return (Join-Path $HOME '.AIM_ai-tools-registry')
}

function Read-Registry([string]$RegistryRoot) {
  $root = Get-RegistryRoot $RegistryRoot
  $path = Join-Path $root 'AIM_registry.json'
  if (-not (Test-Path $path)) { throw "Registry not found: $path" }
  (Get-Content -Path $path -Raw | ConvertFrom-Json)
}

function Resolve-RegistryPath([string]$PathValue) {
  if (-not $PathValue) { return $null }
  $expanded = [Environment]::ExpandEnvironmentVariables($PathValue)
  $expanded = $expanded -replace '^~', $HOME
  # Normalize slashes
  $expanded = $expanded -replace '/', '\\'
  return $expanded
}

function Write-AuditEntry {
  param(
    [string] $RegistryRoot,
    [hashtable] $Entry
  )
  $root = Get-RegistryRoot $RegistryRoot
  $date = (Get-Date -Format 'yyyy-MM-dd')
  $auditDir = Join-Path $root (Join-Path 'AIM_audit' $date)
  if (-not (Test-Path $auditDir)) { New-Item -ItemType Directory -Path $auditDir | Out-Null }
  $stamp = (Get-Date).ToString('yyyy-MM-ddTHH-mm-ssZ')
  $file = Join-Path $auditDir ("{0}_{1}.json" -f $stamp, ($Entry.action ?? 'action'))
  $Entry.timestamp = (Get-Date).ToString('o')
  ($Entry | ConvertTo-Json -Depth 10) | Out-File -FilePath $file -Encoding utf8
}

function Test-AIRegistry {
  [CmdletBinding()]
  param(
    [string] $RegistryRoot,
    [switch] $AsJson
  )
  try {
    $reg = Read-Registry -RegistryRoot $RegistryRoot
    if (-not $reg.tools) { throw 'registry.tools missing' }
    foreach ($id in $reg.tools.PSObject.Properties.Name) {
      $tool = $reg.tools.$id
      if (-not $tool.name) { throw "tool[$id].name missing" }
      if (-not $tool.detectCommands -or $tool.detectCommands.Count -lt 1) { throw "tool[$id].detectCommands missing" }
      # Verify adapter path resolves or default adapter path exists under registry root
      $resolvedAdapter = $null
      if ($tool.adapterScript) { $resolvedAdapter = Resolve-RegistryPath $tool.adapterScript }
      $root = Get-RegistryRoot $RegistryRoot
      $defaultAdapter = Join-Path $root (Join-Path 'AIM_adapters' ("AIM_{0}.ps1" -f $id))
      if (-not ($resolvedAdapter -and (Test-Path $resolvedAdapter)) -and -not (Test-Path $defaultAdapter)) {
        throw "tool[$id].adapter not found (checked '$resolvedAdapter' and '$defaultAdapter')"
      }
    }
    # Verify coordination rules file exists (explicit or default)
    $root = Get-RegistryRoot $RegistryRoot
    $rulesPath = $null
    if ($reg.crossToolRulesPath) {
      $rulesPath = Resolve-RegistryPath $reg.crossToolRulesPath
    }
    $defaultRules = Join-Path $root 'AIM_cross-tool/AIM_coordination-rules.json'
    if (-not $rulesPath -or -not (Test-Path $rulesPath)) { $rulesPath = $defaultRules }
    if (-not (Test-Path $rulesPath)) { throw "coordination rules not found: $rulesPath" }
    $ok = @{ Success = $true; Message = 'Basic validation OK' }
    return $ok
  } catch {
    return @{ Success = $false; Message = $_.Exception.Message }
  }
}

function Get-AIToolStatus {
  [CmdletBinding()]
  param(
    [string] $RegistryRoot,
    [switch] $AsJson
  )
  $reg = Read-Registry -RegistryRoot $RegistryRoot
  $result = @{}
  foreach ($id in $reg.tools.PSObject.Properties.Name) {
    $tool = $reg.tools.$id
    $found = $false; $paths = @()
    foreach ($cmd in $tool.detectCommands) {
      try {
        $gc = Get-Command -All $cmd -ErrorAction SilentlyContinue
        if ($gc) {
          $found = $true
          $paths += ($gc | ForEach-Object { $_.Path })
        }
      } catch {}
    }
    # Try version if configured
    $version = $null
    if ($tool.versionCommand) {
      try {
        $verRes = Invoke-External -Command $tool.versionCommand
        if ($verRes.exit -eq 0 -and $verRes.stdout) { $version = ($verRes.stdout.Trim()) }
      } catch {}
    }
    $result[$id] = [pscustomobject]@{
      Name = $tool.name
      Found = $found
      Paths = $paths | Select-Object -Unique
      Version = $version
      ConfigPaths = $tool.configPaths
      LogPaths = $tool.logPaths
    }
  }
  if ($AsJson) { return $result }
  $result.GetEnumerator() | ForEach-Object {
    $id = $_.Key; $v = $_.Value
    Write-Host ("- {0}: Found={1}" -f $id, $v.Found)
    if ($v.Paths) { $v.Paths | ForEach-Object { Write-Host ("  exe: {0}" -f $_) } }
  }
}

function Invoke-AIToolApply {
  [CmdletBinding()]
  param(
    [string] $RegistryRoot,
    [switch] $WhatIf,
    [switch] $AsJson
  )
  $reg = Read-Registry -RegistryRoot $RegistryRoot
  $summary = @{ changed = $false; details = @() }
  # Placeholder: idempotent, no state changes
  $out = @{ Success = $true; Message = 'No changes (placeholder)'; Summary = $summary }
  Write-AuditEntry -RegistryRoot $RegistryRoot -Entry @{ actor='human:richg'; action='apply'; input=@{whatif=$WhatIf}; result=@{success=$true; message='noop'} }
  return $out
}

function Get-CoordinationRules([string]$RegistryRoot) {
  $root = Get-RegistryRoot $RegistryRoot
  $reg = Read-Registry -RegistryRoot $root
  $rulesPath = Resolve-RegistryPath $reg.crossToolRulesPath
  $defaultRules = Join-Path $root 'AIM_cross-tool/AIM_coordination-rules.json'
  if (-not $rulesPath -or -not (Test-Path $rulesPath)) { $rulesPath = $defaultRules }
  if (-not (Test-Path $rulesPath)) { throw "Coordination rules not found: $rulesPath" }
  Get-Content -Path $rulesPath -Raw | ConvertFrom-Json
}

function Invoke-AdapterScript {
  param(
    [string] $ScriptPath,
    [hashtable] $InputObject
  )
  if (-not (Test-Path $ScriptPath)) { throw "Adapter not found: $ScriptPath" }
  $json = $InputObject | ConvertTo-Json -Depth 10
  $psi = New-Object System.Diagnostics.ProcessStartInfo
  $pwshPath = Join-Path $PSHOME 'pwsh.exe'
  if (-not (Test-Path $pwshPath)) { $pwshPath = 'pwsh' }
  $psi.FileName = $pwshPath
  $quoted = '"' + $ScriptPath + '"'
  $psi.Arguments = "-NoLogo -NoProfile -File $quoted"
  $psi.RedirectStandardInput = $true
  $psi.RedirectStandardOutput = $true
  $psi.RedirectStandardError = $true
  $psi.UseShellExecute = $false
  $p = New-Object System.Diagnostics.Process
  $p.StartInfo = $psi
  [void]$p.Start()
  $p.StandardInput.WriteLine($json)
  $p.StandardInput.Close()
  $stdout = $p.StandardOutput.ReadToEnd()
  $stderr = $p.StandardError.ReadToEnd()
  $p.WaitForExit()
  $exit = $p.ExitCode
  $outObj = $null
  try { $outObj = $stdout | ConvertFrom-Json } catch { $outObj = @{ success=$false; message='Adapter returned non-JSON'; raw=$stdout; error=$stderr } }
  return @{ exit=$exit; stdout=$stdout; stderr=$stderr; obj=$outObj }
}

function Invoke-External {
  param(
    [Parameter(Mandatory)] [object] $Command
  )
  # $Command is expected to be an array like [exe, arg1, arg2]
  $arr = @()
  if ($Command -is [System.Array]) { $arr = @($Command) } else { $arr = @("$Command") }
  if ($arr.Count -lt 1) { throw 'Invoke-External requires at least one element' }
  $exe = [string]$arr[0]
  $args = @()
  if ($arr.Count -gt 1) { $args = $arr[1..($arr.Count-1)] }
  $psi = New-Object System.Diagnostics.ProcessStartInfo
  $psi.FileName = $exe
  $psi.Arguments = ($args | ForEach-Object { if($_ -match ' ') { '"' + $_ + '"' } else { $_ } }) -join ' '
  $psi.RedirectStandardOutput = $true
  $psi.RedirectStandardError = $true
  $psi.UseShellExecute = $false
  $p = New-Object System.Diagnostics.Process
  $p.StartInfo = $psi
  [void]$p.Start()
  $stdout = $p.StandardOutput.ReadToEnd()
  $stderr = $p.StandardError.ReadToEnd()
  $p.WaitForExit()
  return @{ exit=$p.ExitCode; stdout=$stdout; stderr=$stderr }
}

function Invoke-AICapability {
  [CmdletBinding()]
  param(
    [string] $RegistryRoot,
    [Parameter(Mandatory=$true)] [string] $Capability,
    [Parameter(Mandatory=$true)] [string] $PayloadJson,
    [switch] $AsJson
  )
  $root = Get-RegistryRoot $RegistryRoot
  $reg = Read-Registry -RegistryRoot $root
  $rules = Get-CoordinationRules -RegistryRoot $root

  $chain = @()
  if ($rules.capabilities.$Capability) {
    $chain += $rules.capabilities.$Capability.primary
    if ($rules.capabilities.$Capability.fallback) { $chain += $rules.capabilities.$Capability.fallback }
  } else {
    throw "No coordination rules for capability: $Capability"
  }

  $payload = $PayloadJson | ConvertFrom-Json
  foreach ($toolId in $chain) {
    $tool = $reg.tools.$toolId
    if (-not $tool) { continue }
    $adapter = Resolve-RegistryPath $tool.adapterScript
    if (-not $adapter) { $adapter = Join-Path $root (Join-Path 'AIM_adapters' ("AIM_{0}.ps1" -f $toolId)) }
    $input = @{ capability = $Capability; payload = $payload; tool = $toolId }
    try {
      $res = Invoke-AdapterScript -ScriptPath $adapter -InputObject $input
      $ok = $false; if ($res.obj -and $res.obj.success -eq $true -and $res.exit -eq 0) { $ok = $true }
      Write-AuditEntry -RegistryRoot $root -Entry @{ actor='human:richg'; action='capability'; input=$input; result=@{success=$ok; message=($res.obj.message ?? '')} }
      if ($ok) { return @{ Success=$true; Tool=$toolId; Result=$res.obj } }
    } catch {
      continue
    }
  }
  return @{ Success=$false; Message = 'All tools in chain failed'; Chain = $chain }
}

# Export public functions
Export-ModuleMember -Function Get-AIToolStatus, Test-AIRegistry, Invoke-AIToolApply, Invoke-AICapability
