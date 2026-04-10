# Script Issue Verification

**User:** bill reed (richgwilks@gmail.com)  
**Created:** 3/27/2026 3:06:19  
**Updated:** 3/27/2026 18:28:18  
**Exported:** 3/28/2026 8:48:42  
**Link:** [https://chatgpt.com/g/g-p-69123063d95c819197adfc91fffb052b-plan/c/69c63a77-a368-832f-8b7f-8635d2329f9e](https://chatgpt.com/g/g-p-69123063d95c819197adfc91fffb052b-plan/c/69c63a77-a368-832f-8b7f-8635d2329f9e)  

## Response:
Code Copilot

Thought for 5m 34s

Yep — the _three_ flagged items are real in **this script**, and there are **two bigger correctness problems** that weren’t mentioned.

Verified: the reported issues are real
--------------------------------------

### 1) `snakefood` is still required → will break on Python 3

In your `$Tools` list, `snakefood` is present and `required = $true` (line **349**), installed via pip, then verified via `sfood.exe`. Given upstream explicitly says Python 3.x is **not supported**, this is a high-probability failure path (either install/runtime). [GitHub](https://github.com/blais/snakefood?utm_source=chatgpt.com)

### 2) `pipreqs` verification uses `--version` (line **345**) → likely fails every run

Your `pipreqs` tool entry uses `verify_args = @("--version")`. The pipreqs README documents its CLI options and **does not include `--version`**, so the verification will exit non-zero and you’ll reinstall every execution. [GitHub](https://github.com/bndr/pipreqs)

### 3) Type contract mismatch: `Get-VenvPaths` returns `[ordered]@{}` (line **227**) but `$Venv` params are `[hashtable]`

`Get-VenvPaths` returns an `OrderedDictionary`. `Verify-CliTool`, `Verify-ImportTool`, `Verify-Tool`, and `Install-Tool` type `$Venv` as `[hashtable]` (e.g., lines **238–239**, **269–270**, **292–293**, **307–308**). Under `Set-StrictMode -Version Latest`, relying on implicit coercion here is fragile.

Also verified: the “minor issues” are accurate
----------------------------------------------

*   The venv directory creation “placeholder file” hack is exactly as described (lines **461–462**).
*   Import-tool `ResolvedPath` is set to `$Venv.Python` (line **282**), so the JSON field is misleading (it’s the interpreter, not the module).
*   Retry sleep is a flat 2s (lines **528**, **555**).

* * *

Additional problems not mentioned (these are the big ones)
----------------------------------------------------------

### A) **Guaranteed failure on Windows PowerShell 5.1**: `ProcessStartInfo.ArgumentList`

`Invoke-ProcessCapture` does: `$psi = New-Object System.Diagnostics.ProcessStartInfo` and then `$psi.ArgumentList.Add(...)` (line **122**).

`ProcessStartInfo.ArgumentList` is supported starting in **.NET Core 2.1 / .NET Standard 2.1**, not .NET Framework-era hosts (which is what Windows PowerShell 5.1 runs on). So if someone runs this in PS **5.1**, it can crash immediately. [Microsoft Learn+1](https://learn.microsoft.com/en-us/dotnet/api/system.diagnostics.processstartinfo.arguments?view=net-10.0&utm_source=chatgpt.com)

**Fix choices:**

*   Either bump `#requires` to PowerShell **7+**, **or**
*   Implement a fallback that uses `.Arguments` with proper Windows quoting when `ArgumentList` isn’t available.

### B) Your timeout handling in `Invoke-ProcessCapture` is effectively broken (and can deadlock)

You call:

*   `$stdout = $p.StandardOutput.ReadToEnd()` (line **139**)
*   `$stderr = $p.StandardError.ReadToEnd()` (line **140**)  
    …and only **after that** do you call `WaitForExit(timeout)` (line **142**).

If the child process hangs, `ReadToEnd()` can block forever, so you never reach your timeout logic. Also, sequential `ReadToEnd()` can deadlock if stderr fills its buffer while you’re blocked reading stdout (classic Process redirection pitfall).

**Net:** the “timeout handling” is not actually protecting you in the failure mode you care about most (pip installs hanging).

### C) Launcher resolution is brittle: `Get-Command ... | .Source`

`Get-PythonLauncher` returns `$cmd.Source`. For non-Application command types (alias/function), `.Source` is not a filesystem path. If a user has a `python` alias/function in their profile, this can point to a module name and break process launch. Safer is to require `CommandType -eq Application` and use `.Path`.

### D) “Deterministic” is not true as-written

You install floating latest versions (`pip install <package>`), and also upgrade pip to latest. That’s reproducible **only** at a point in time. If “deterministic” is a real requirement, you need pinned versions or a constraints/lock file.

* * *

Minimal patch suggestions (high impact)
---------------------------------------

If you want the shortest path to “reliable”:

1.  Remove `snakefood` (or replace with a Python 3 fork like `snakefood3` if that’s your intent). [GitHub+1](https://github.com/blais/snakefood?utm_source=chatgpt.com)
2.  Change pipreqs verify to `--help` (or similar stable no-op). [GitHub](https://github.com/bndr/pipreqs)
3.  Change `$Venv` param types to `[System.Collections.IDictionary]` (or untyped).
4.  Fix `Invoke-ProcessCapture` for:
    *   PS 5.1 compatibility (no `ArgumentList`)
    *   real timeouts + no deadlocks (async read or temp-file redirection)

```
--- a/python-analysis-tool-setup.ps1
+++ b/python-analysis-tool-setup.ps1
@@
 function Invoke-ProcessCapture {
@@
-    $psi = New-Object System.Diagnostics.ProcessStartInfo
-    $psi.FileName = $FilePath
-    foreach ($arg in $ArgumentList) {
-        [void]$psi.ArgumentList.Add($arg)
-    }
+    $psi = New-Object System.Diagnostics.ProcessStartInfo
+    $psi.FileName = $FilePath
+    # PS5.1/.NET Framework doesn't have ProcessStartInfo.ArgumentList
+    if ($psi.PSObject.Properties.Match("ArgumentList").Count -gt 0) {
+        foreach ($arg in $ArgumentList) { [void]$psi.ArgumentList.Add($arg) }
+    } else {
+        $psi.Arguments = ($ArgumentList | ForEach-Object { ConvertTo-WindowsCommandLineArg $_ }) -join " "
+    }
@@
-    [void]$p.Start()
-    $stdout = $p.StandardOutput.ReadToEnd()
-    $stderr = $p.StandardError.ReadToEnd()
-
-    if (-not $p.WaitForExit($TimeoutSeconds * 1000)) {
+    # TODO: replace ReadToEnd() pattern with async reads so timeout can work
+    [void]$p.Start()
+    if (-not $p.WaitForExit($TimeoutSeconds * 1000)) {
         try { $p.Kill() } catch {}
         Write-Log "EXEC TIMEOUT :: $cmdDisplay"
         return [ordered]@{
             ExitCode = 124
-            StdOut = $stdout
-            StdErr = ($stderr + [Environment]::NewLine + "Timed out after $TimeoutSeconds seconds.")
+            StdOut = ""
+            StdErr = ("Timed out after $TimeoutSeconds seconds.")
             Command = $cmdDisplay
         }
     }
+    $stdout = $p.StandardOutput.ReadToEnd()
+    $stderr = $p.StandardError.ReadToEnd()
@@
 function Get-VenvPaths {
@@
-    return [ordered]@{
+    return [ordered]@{
         Root = $fullRoot
@@
 function Verify-CliTool {
     param(
         [Parameter(Mandatory = $true)][hashtable]$Tool,
-        [Parameter(Mandatory = $true)][hashtable]$Venv
+        [Parameter(Mandatory = $true)][System.Collections.IDictionary]$Venv
     )
@@
 function Verify-ImportTool {
     param(
         [Parameter(Mandatory = $true)][hashtable]$Tool,
-        [Parameter(Mandatory = $true)][hashtable]$Venv
+        [Parameter(Mandatory = $true)][System.Collections.IDictionary]$Venv
     )
@@
     @{
         name = "pipreqs"
@@
-        verify_args = @("--version")
-        verify_command = "pipreqs --version"
+        verify_args = @("--help")
+        verify_command = "pipreqs --help"
     },
-    @{
-        name = "snakefood"
-        package = "snakefood"
-        required = $true
-        install_source = "pip"
-        verify_type = "cli"
-        exe_name = "sfood.exe"
-        verify_args = @("--help")
-        verify_command = "sfood --help"
-    },
@@
-        Ensure-Directory -Path (Join-Path $venv.Root "placeholder.txt")
-        Remove-Item -LiteralPath (Join-Path $venv.Root "placeholder.txt") -ErrorAction SilentlyContinue
+        New-Item -ItemType Directory -Path $venv.Root -Force | Out-Null
```

> Note: the diff above still leaves the **deadlock/timeout** issue partially addressed; the _real_ fix is async output capture (or temp-file redirection + timed Wait/Kill). The placeholder change is clean and safe.

* * *

**a.** Want me to drop in a fully-correct `Invoke-ProcessCapture` implementation that works on PS 5.1 _and_ enforces timeouts without deadlocks?  
**b.** Should this script be truly “deterministic” (pinned versions/constraints), or is “latest tools” acceptable?

## Response:
Code Copilot

You’re asking about those two bullets (**a** and **b**) I wrote at the end. Here’s what they mean in plain English:

a) “Drop in a fully-correct `Invoke-ProcessCapture`…timeouts without deadlocks”
-------------------------------------------------------------------------------

Your script runs external commands (like `python`, `pip`, `pipreqs`) via `Invoke-ProcessCapture`. Right now that function can:

*   **Hang forever** even though it _looks_ like it has a timeout, because it reads all stdout/stderr (`ReadToEnd()`) **before** it waits with a timeout.
*   **Deadlock** if the child process writes lots to stderr while you’re blocked reading stdout (Windows process pipe buffering issue).
*   **Fail on PowerShell 5.1** because it uses `.ArgumentList`, which isn’t available on the .NET runtime PS 5.1 uses.

So “drop in a fully-correct implementation” means: replace that function with a version that:

*   works in **PS 5.1 and PS 7+**
*   captures stdout/stderr safely (no deadlocks)
*   actually enforces timeouts (kills the process if it exceeds the limit)

b) “Deterministic vs latest tools”
----------------------------------

Your script installs tools with commands like `pip install <tool>`, which pulls **whatever the newest version is that day**. That means:

*   the script can succeed today but fail later due to upstream changes
*   results can differ from run to run

So I was asking which you want:

*   **Deterministic**: pin versions (e.g., `pipreqs==0.4.13`) or use a constraints/lock file so installs are reproducible.
*   **Latest acceptable**: always install the newest versions (simpler, but less predictable).

**a.** Want me to paste a replacement `Invoke-ProcessCapture` function (PS 5.1 + PS 7 compatible) that correctly captures output and enforces timeouts?  
**b.** Do you prefer pinned tool versions (reproducible) or “latest available” (always up to date)?

## Response:
Code Copilot

Thought for 6m 18s

TL;DR: You’re on **PowerShell 7.5.5** and want **real timeouts** + **latest available** installs. Below is a fixed version of your script that:

*   enforces timeouts correctly (no `ReadToEnd()` hang/deadlock)
*   removes `snakefood`
*   fixes `pipreqs` verification (`--help`)
*   fixes `$Venv` type mismatch (`IDictionary`)
*   reports import-tool “resolved path” as the module origin (not `python.exe`)
*   cleans up venv dir creation

Download the fixed script

Plan (pseudocode)
-----------------

1.  Require PowerShell 7+.
2.  Make `Get-CommandSourceSafe` return only real application paths.
3.  Add `Format-ArgumentForDisplay` for clean logging.
4.  Rewrite `Invoke-ProcessCapture`:
    *   start process with redirected stdout/stderr
    *   start async reads (`ReadToEndAsync`)
    *   race `WaitForExitAsync()` vs `Task.Delay(timeout)`
    *   on timeout: kill **process tree**, drain output briefly, return exit code **124**
5.  Change `Get-VenvPaths` consumer param types from `[hashtable]` to `[IDictionary]`.
6.  Fix import verification to return JSON `{origin, version}` and parse it.
7.  Update tool list:
    *   `pipreqs` verify via `--help`
    *   remove `snakefood`
8.  Replace placeholder-file venv dir hack with `New-Item -ItemType Directory`.

```
#requires -Version 7.0
<#
.SYNOPSIS
Setup script for Python analysis tools on Windows.

.DESCRIPTION
Creates or reuses a dedicated virtual environment, checks whether each required
tool is installed and valid, installs missing/invalid tools via pip inside the
venv, verifies each tool, and writes a structured JSON report plus a text log.

This script is intentionally bounded to setup/configure/verify/report.
It does not create registries, SSOT sidecars, or long-lived orchestration artifacts.

.NOTES
- Windows-oriented
- User-level only
- No global package installs
- No package uninstall rollback
- Leaves partially populated venv intact for inspection on failure
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

param(
    [string]$VenvPath = ".tools\python-analysis-venv",
    [string]$ReportPath = ".tools\reports\python-analysis-tool-setup-report.json",
    [string]$LogPath = ".tools\reports\python-analysis-tool-setup.log",
    [int]$MaxInstallAttempts = 2
)

# ----------------------------
# Utility functions
# ----------------------------

function Get-UtcIsoNow {
    return ([DateTime]::UtcNow.ToString("o"))
}

function Ensure-Directory {
    param([Parameter(Mandatory = $true)][string]$Path)
    $dir = Split-Path -Parent $Path
    if (-not [string]::IsNullOrWhiteSpace($dir) -and -not (Test-Path -LiteralPath $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

function Write-Log {
    param(
        [Parameter(Mandatory = $true)][string]$Message
    )
    Ensure-Directory -Path $script:LogPath
    $line = "[{0}] {1}" -f (Get-UtcIsoNow), $Message
    Add-Content -LiteralPath $script:LogPath -Value $line -Encoding UTF8
}

function Get-CommandSourceSafe {
    param([Parameter(Mandatory = $true)][string]$CommandName)

    try {
        $cmd = Get-Command $CommandName -ErrorAction Stop | Where-Object { $_.CommandType -eq "Application" } | Select-Object -First 1
        if ($null -eq $cmd) {
            return $null
        }

        if ($cmd.PSObject.Properties.Match("Path").Count -gt 0 -and -not [string]::IsNullOrWhiteSpace($cmd.Path) -and (Test-Path -LiteralPath $cmd.Path)) {
            return $cmd.Path
        }

        if (-not [string]::IsNullOrWhiteSpace($cmd.Source) -and (Test-Path -LiteralPath $cmd.Source)) {
            return $cmd.Source
        }

        return $null
    } catch {
        return $null
    }
}

function New-ToolResult {
    param(
        [Parameter(Mandatory = $true)][string]$ToolName,
        [Parameter(Mandatory = $true)][string]$PackageName,
        [Parameter(Mandatory = $true)][bool]$Required,
        [Parameter(Mandatory = $true)][string]$InstallSource,
        [Parameter(Mandatory = $true)][string]$VerifyCommand
    )

    return [ordered]@{
        name = $ToolName
        package = $PackageName
        required = $Required
        install_source = $InstallSource
        verify_command = $VerifyCommand
        status = "UNKNOWN"
        install_attempts = 0
        verify_exit_code = $null
        resolved_executable_path = $null
        version = $null
        stdout_tail = $null
        stderr_tail = $null
        failure_reason = $null
    }
}

function Get-StringTail {
    param(
        [string]$Text,
        [int]$MaxLines = 20
    )

    if ([string]::IsNullOrWhiteSpace($Text)) {
        return $null
    }

    $lines = ($Text -split "(`r`n|`n|`r)")
    if ($lines.Length -le $MaxLines) {
        return ($lines -join [Environment]::NewLine).TrimEnd()
    }

    return (($lines[-$MaxLines..-1]) -join [Environment]::NewLine).TrimEnd()
}

function Format-ArgumentForDisplay {
    param([Parameter(Mandatory = $true)][string]$Arg)

    if ($Arg -match '\s|"') {
        return '"' + ($Arg -replace '"', '\"') + '"'
    }
    return $Arg
}

function Invoke-ProcessCapture {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(Mandatory = $true)][string[]]$ArgumentList,
        [string]$WorkingDirectory = (Get-Location).Path,
        [int]$TimeoutSeconds = 1800
    )

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $FilePath
    foreach ($arg in $ArgumentList) {
        [void]$psi.ArgumentList.Add($arg)
    }
    $psi.WorkingDirectory = $WorkingDirectory
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $psi.StandardOutputEncoding = [System.Text.Encoding]::UTF8
    $psi.StandardErrorEncoding = [System.Text.Encoding]::UTF8

    $p = New-Object System.Diagnostics.Process
    $p.StartInfo = $psi

    $cmdDisplay = "$FilePath " + (($ArgumentList | ForEach-Object { Format-ArgumentForDisplay -Arg $_ }) -join ' ')
    Write-Log "EXEC START :: $cmdDisplay"

    $sw = [System.Diagnostics.Stopwatch]::StartNew()

    try {
        [void]$p.Start()
    } catch {
        $sw.Stop()
        Write-Log ("EXEC START FAILED :: {0} :: {1}" -f $cmdDisplay, $_.Exception.Message)
        return [ordered]@{
            ExitCode = 127
            StdOut = ""
            StdErr = $_.Exception.Message
            Command = $cmdDisplay
            DurationMs = $sw.ElapsedMilliseconds
        }
    }

    $stdoutTask = $p.StandardOutput.ReadToEndAsync()
    $stderrTask = $p.StandardError.ReadToEndAsync()
    $exitTask = $p.WaitForExitAsync()

    $timedOut = $false
    $timeoutTask = [System.Threading.Tasks.Task]::Delay([TimeSpan]::FromSeconds([Math]::Max(0, $TimeoutSeconds)))

    $winner = [System.Threading.Tasks.Task]::WhenAny($exitTask, $timeoutTask).GetAwaiter().GetResult()
    if ($winner -eq $timeoutTask) {
        $timedOut = $true
        try { $p.Kill($true) } catch {}
    }

    try { $exitTask.GetAwaiter().GetResult() | Out-Null } catch {}

    $drainMs = 5000
    [void]$stdoutTask.Wait($drainMs)
    [void]$stderrTask.Wait($drainMs)

    $stdout = ""
    $stderr = ""
    try { if ($stdoutTask.IsCompleted) { $stdout = $stdoutTask.GetAwaiter().GetResult() } } catch {}
    try { if ($stderrTask.IsCompleted) { $stderr = $stderrTask.GetAwaiter().GetResult() } } catch {}

    $sw.Stop()

    if ($timedOut) {
        Write-Log "EXEC TIMEOUT :: $cmdDisplay"
        $timeoutMsg = "Timed out after $TimeoutSeconds seconds."
        if ($stderr) {
            $stderr = ($stderr.TrimEnd() + [Environment]::NewLine + $timeoutMsg)
        } else {
            $stderr = $timeoutMsg
        }

        return [ordered]@{
            ExitCode = 124
            StdOut = $stdout
            StdErr = $stderr
            Command = $cmdDisplay
            DurationMs = $sw.ElapsedMilliseconds
        }
    }

    Write-Log ("EXEC END   :: exit={0} :: {1}" -f $p.ExitCode, $cmdDisplay)
    if ($stdout) { Write-Log ("STDOUT TAIL :: " + (Get-StringTail -Text $stdout -MaxLines 10)) }
    if ($stderr) { Write-Log ("STDERR TAIL :: " + (Get-StringTail -Text $stderr -MaxLines 10)) }

    return [ordered]@{
        ExitCode = $p.ExitCode
        StdOut = $stdout
        StdErr = $stderr
        Command = $cmdDisplay
        DurationMs = $sw.ElapsedMilliseconds
    }
}

function Get-PythonLauncher {
    $pySource = Get-CommandSourceSafe -CommandName "py"
    if ($pySource) {
        return [ordered]@{ Command = $pySource; Args = @() }
    }

    $pythonSource = Get-CommandSourceSafe -CommandName "python"
    if ($pythonSource) {
        return [ordered]@{ Command = $pythonSource; Args = @() }
    }

    return $null
}

function Get-VersionFromOutput {
    param([string]$StdOut, [string]$StdErr)

    $text = (($StdOut, $StdErr) -join [Environment]::NewLine).Trim()
    if ([string]::IsNullOrWhiteSpace($text)) {
        return $null
    }

    $match = [regex]::Match($text, '\b\d+\.\d+(?:\.\d+)?(?:[-+a-zA-Z0-9\.]*)?\b')
    if ($match.Success) {
        return $match.Value
    }

    return $null
}

function Test-IsRetryableInstallError {
    param([string]$StdErr, [string]$StdOut)

    $text = (($StdErr, $StdOut) -join [Environment]::NewLine)
    if ([string]::IsNullOrWhiteSpace($text)) {
        return $false
    }

    $patterns = @(
        "Read timed out",
        "Connection reset by peer",
        "Connection aborted",
        "Temporary failure in name resolution",
        "TLSV1_ALERT",
        "EOF occurred in violation of protocol",
        "The remote name could not be resolved",
        "Max retries exceeded with url",
        "HTTPConnectionPool",
        "HTTPSConnectionPool",
        "SSLError",
        "ProxyError"
    )

    foreach ($p in $patterns) {
        if ($text -match [regex]::Escape($p)) {
            return $true
        }
    }

    return $false
}

function Get-VenvPaths {
    param([Parameter(Mandatory = $true)][string]$Root)

    $fullRoot = [System.IO.Path]::GetFullPath($Root)
    return [ordered]@{
        Root = $fullRoot
        Python = Join-Path $fullRoot "Scripts\python.exe"
        Pip = Join-Path $fullRoot "Scripts\pip.exe"
        ScriptsDir = Join-Path $fullRoot "Scripts"
    }
}

function Verify-CliTool {
    param(
        [Parameter(Mandatory = $true)][hashtable]$Tool,
        [Parameter(Mandatory = $true)][System.Collections.IDictionary]$Venv
    )

    $exeName = $Tool.exe_name
    $exePath = Join-Path $Venv.ScriptsDir $exeName
    if (-not (Test-Path -LiteralPath $exePath)) {
        return [ordered]@{
            Ok = $false
            ExitCode = 127
            ResolvedPath = $exePath
            Version = $null
            StdOut = ""
            StdErr = "Executable not found."
        }
    }

    $invoke = Invoke-ProcessCapture -FilePath $exePath -ArgumentList $Tool.verify_args -TimeoutSeconds 120
    return [ordered]@{
        Ok = ($invoke.ExitCode -eq 0)
        ExitCode = $invoke.ExitCode
        ResolvedPath = $exePath
        Version = (Get-VersionFromOutput -StdOut $invoke.StdOut -StdErr $invoke.StdErr)
        StdOut = $invoke.StdOut
        StdErr = $invoke.StdErr
    }
}

function Verify-ImportTool {
    param(
        [Parameter(Mandatory = $true)][hashtable]$Tool,
        [Parameter(Mandatory = $true)][System.Collections.IDictionary]$Venv
    )

    $pyCode = @"
import json
import importlib
import importlib.util

name = r"$($Tool.import_name)"
spec = importlib.util.find_spec(name)
origin = getattr(spec, "origin", None) if spec else None
m = importlib.import_module(name)
version = getattr(m, "__version__", "unknown")
print(json.dumps({"origin": origin, "version": version}))
"@

    $invoke = Invoke-ProcessCapture -FilePath $Venv.Python -ArgumentList @("-c", $pyCode)

    $origin = $null
    $version = $null

    if ($invoke.ExitCode -eq 0 -and -not [string]::IsNullOrWhiteSpace($invoke.StdOut)) {
        try {
            $info = $invoke.StdOut.Trim() | ConvertFrom-Json -ErrorAction Stop
            $origin = $info.origin
            $version = $info.version
        } catch {
            $version = (Get-VersionFromOutput -StdOut $invoke.StdOut -StdErr $invoke.StdErr)
        }
    }

    return [ordered]@{
        Ok = ($invoke.ExitCode -eq 0)
        ExitCode = $invoke.ExitCode
        ResolvedPath = $origin
        Version = $version
        StdOut = $invoke.StdOut
        StdErr = $invoke.StdErr
    }
}

function Verify-Tool {
    param(
        [Parameter(Mandatory = $true)][hashtable]$Tool,
        [Parameter(Mandatory = $true)][System.Collections.IDictionary]$Venv
    )

    switch ($Tool.verify_type) {
        "cli" { return (Verify-CliTool -Tool $Tool -Venv $Venv) }
        "import" { return (Verify-ImportTool -Tool $Tool -Venv $Venv) }
        default {
            return [ordered]@{
                Ok = $false
                ExitCode = 128
                ResolvedPath = $null
                Version = $null
                StdOut = ""
                StdErr = "Unknown verify_type '$($Tool.verify_type)'."
            }
        }
    }
}

function Install-Tool {
    param(
        [Parameter(Mandatory = $true)][hashtable]$Tool,
        [Parameter(Mandatory = $true)][System.Collections.IDictionary]$Venv
    )

    return Invoke-ProcessCapture -FilePath $Venv.Python -ArgumentList @("-m", "pip", "install", $Tool.package)
}

# ----------------------------
# Tool definitions
# ----------------------------

$Tools = @(
    @{
        name = "semgrep"
        package = "semgrep"
        required = $true
        install_source = "pip"
        verify_type = "cli"
        exe_name = "semgrep.exe"
        verify_args = @("--version")
        verify_command = "semgrep --version"
    },
    @{
        name = "radon"
        package = "radon"
        required = $true
        install_source = "pip"
        verify_type = "cli"
        exe_name = "radon.exe"
        verify_args = @("--version")
        verify_command = "radon --version"
    },
    @{
        name = "pipreqs"
        package = "pipreqs"
        required = $true
        install_source = "pip"
        verify_type = "cli"
        exe_name = "pipreqs.exe"
        verify_args = @("--help")
        verify_command = "pipreqs --help"
    },
    @{
        name = "networkx"
        package = "networkx"
        required = $true
        install_source = "pip"
        verify_type = "import"
        import_name = "networkx"
        verify_command = 'python -c "import networkx; print(networkx.__version__)"'
    },
    @{
        name = "jedi"
        package = "jedi"
        required = $true
        install_source = "pip"
        verify_type = "import"
        import_name = "jedi"
        verify_command = 'python -c "import jedi; print(jedi.__version__)"'
    },
    @{
        name = "astroid"
        package = "astroid"
        required = $true
        install_source = "pip"
        verify_type = "import"
        import_name = "astroid"
        verify_command = 'python -c "import astroid; print(astroid.__version__)"'
    },
    @{
        name = "libcst"
        package = "libcst"
        required = $true
        install_source = "pip"
        verify_type = "import"
        import_name = "libcst"
        verify_command = 'python -c "import libcst; print(libcst.__version__)"'
    },
    @{
        name = "ruff"
        package = "ruff"
        required = $true
        install_source = "pip"
        verify_type = "cli"
        exe_name = "ruff.exe"
        verify_args = @("--version")
        verify_command = "ruff --version"
    },
    @{
        name = "mccabe"
        package = "mccabe"
        required = $true
        install_source = "pip"
        verify_type = "import"
        import_name = "mccabe"
        verify_command = 'python -c "import mccabe; print(getattr(mccabe, ''__version__'', ''unknown''))"'
    },
    @{
        name = "mypy"
        package = "mypy"
        required = $true
        install_source = "pip"
        verify_type = "cli"
        exe_name = "mypy.exe"
        verify_args = @("--version")
        verify_command = "mypy --version"
    }
)

# ----------------------------
# Main
# ----------------------------

$script:LogPath = [System.IO.Path]::GetFullPath($LogPath)
$reportFullPath = [System.IO.Path]::GetFullPath($ReportPath)
$venv = Get-VenvPaths -Root $VenvPath

Ensure-Directory -Path $script:LogPath
Ensure-Directory -Path $reportFullPath

Write-Log "=== PYTHON ANALYSIS TOOL SETUP START ==="
Write-Log ("Requested venv path: {0}" -f $venv.Root)
Write-Log ("Requested report path: {0}" -f $reportFullPath)

$overallStatus = "SUCCESS"
$toolResults = New-Object System.Collections.Generic.List[object]
$pythonExecutable = $null
$pipVersion = $null

try {
    # Step 1: Validate Python availability
    $launcher = Get-PythonLauncher
    if ($null -eq $launcher) {
        throw "Neither 'py' nor 'python' was found on PATH."
    }

    Write-Log ("Python launcher resolved: {0}" -f $launcher.Command)
    $pyVersionCheck = Invoke-ProcessCapture -FilePath $launcher.Command -ArgumentList @("--version")
    if ($pyVersionCheck.ExitCode -ne 0) {
        throw "Python launcher exists but version check failed."
    }

    # Step 2: Create venv if missing
    if (-not (Test-Path -LiteralPath $venv.Python)) {
        Write-Log "Virtual environment missing. Creating new venv."
        New-Item -ItemType Directory -Path $venv.Root -Force | Out-Null

        $venvCreate = Invoke-ProcessCapture -FilePath $launcher.Command -ArgumentList @("-m", "venv", $venv.Root)
        if ($venvCreate.ExitCode -ne 0) {
            throw ("Failed to create venv at '{0}'. {1}" -f $venv.Root, (Get-StringTail -Text $venvCreate.StdErr))
        }
    } else {
        Write-Log "Virtual environment already exists. Reusing existing venv."
    }

    if (-not (Test-Path -LiteralPath $venv.Python)) {
        throw "Venv creation completed but python.exe not found inside venv."
    }

    $pythonExecutable = $venv.Python

    # Step 3/4: Upgrade pip
    $pipUpgrade = Invoke-ProcessCapture -FilePath $venv.Python -ArgumentList @("-m", "pip", "install", "--upgrade", "pip")
    if ($pipUpgrade.ExitCode -ne 0) {
        throw ("Failed to upgrade pip in venv. {0}" -f (Get-StringTail -Text $pipUpgrade.StdErr))
    }

    $pipVersionCheck = Invoke-ProcessCapture -FilePath $venv.Python -ArgumentList @("-m", "pip", "--version")
    if ($pipVersionCheck.ExitCode -eq 0) {
        $pipVersion = (Get-VersionFromOutput -StdOut $pipVersionCheck.StdOut -StdErr $pipVersionCheck.StdErr)
    }

    # Step 5/6/7: Detect, install if needed, verify
    foreach ($tool in $Tools) {
        Write-Log ("--- TOOL START :: {0} ---" -f $tool.name)
        $result = New-ToolResult -ToolName $tool.name -PackageName $tool.package -Required ([bool]$tool.required) -InstallSource $tool.install_source -VerifyCommand $tool.verify_command

        # First verification (detection)
        $verification = Verify-Tool -Tool $tool -Venv $venv
        $result.verify_exit_code = $verification.ExitCode
        $result.resolved_executable_path = $verification.ResolvedPath
        $result.version = $verification.Version
        $result.stdout_tail = Get-StringTail -Text $verification.StdOut
        $result.stderr_tail = Get-StringTail -Text $verification.StdErr

        if ($verification.Ok) {
            $result.status = "SKIPPED_ALREADY_VALID"
            $toolResults.Add([pscustomobject]$result) | Out-Null
            Write-Log ("TOOL VALID :: {0} :: status={1} :: version={2}" -f $tool.name, $result.status, $result.version)
            continue
        }

        Write-Log ("TOOL INVALID/MISSING :: {0} :: beginning install attempts" -f $tool.name)

        $installed = $false
        $finalFailure = $null

        for ($attempt = 1; $attempt -le $MaxInstallAttempts; $attempt++) {
            $result.install_attempts = $attempt
            Write-Log ("INSTALL ATTEMPT :: tool={0} attempt={1}" -f $tool.name, $attempt)

            $install = Install-Tool -Tool $tool -Venv $venv
            $retryable = Test-IsRetryableInstallError -StdErr $install.StdErr -StdOut $install.StdOut

            if ($install.ExitCode -ne 0) {
                $result.stdout_tail = Get-StringTail -Text $install.StdOut
                $result.stderr_tail = Get-StringTail -Text $install.StdErr
                $finalFailure = (Get-StringTail -Text $install.StdErr)

                if ($retryable -and $attempt -lt $MaxInstallAttempts) {
                    Write-Log ("INSTALL RETRYABLE FAILURE :: tool={0} attempt={1}" -f $tool.name, $attempt)
                    Start-Sleep -Seconds 2
                    continue
                }

                Write-Log ("INSTALL NON-SUCCESS :: tool={0} attempt={1} retryable={2}" -f $tool.name, $attempt, $retryable)
                break
            }

            # Re-verify after successful install
            $verification = Verify-Tool -Tool $tool -Venv $venv
            $result.verify_exit_code = $verification.ExitCode
            $result.resolved_executable_path = $verification.ResolvedPath
            $result.version = $verification.Version
            $result.stdout_tail = Get-StringTail -Text $verification.StdOut
            $result.stderr_tail = Get-StringTail -Text $verification.StdErr

            if ($verification.Ok) {
                $result.status = "INSTALLED"
                $installed = $true
                Write-Log ("INSTALL VERIFIED :: tool={0} version={1}" -f $tool.name, $result.version)
                break
            }

            $finalFailure = (Get-StringTail -Text $verification.StdErr)
            Write-Log ("POST-INSTALL VERIFY FAILED :: tool={0} attempt={1}" -f $tool.name, $attempt)

            if ($attempt -lt $MaxInstallAttempts) {
                Start-Sleep -Seconds 2
            }
        }

        if (-not $installed) {
            $result.status = "FAILED"
            $result.failure_reason = if ([string]::IsNullOrWhiteSpace($finalFailure)) {
                "Install or verification failed."
            } else {
                $finalFailure
            }

            if ($overallStatus -eq "SUCCESS") {
                $overallStatus = "PARTIAL_FAILURE"
            }

            Write-Log ("TOOL FAILED :: {0} :: reason={1}" -f $tool.name, $result.failure_reason)
        }

        $toolResults.Add([pscustomobject]$result) | Out-Null
    }
}
catch {
    $overallStatus = "FAILED"
    Write-Log ("HARD FAILURE :: {0}" -f $_.Exception.Message)
}
finally {
    # Step 8: Always write report and log
    $reportObject = [ordered]@{
        run_timestamp_utc = Get-UtcIsoNow
        overall_status = $overallStatus
        os = "Windows"
        venv_path = $venv.Root
        python_executable = $pythonExecutable
        pip_version = $pipVersion
        tools = @($toolResults)
    }

    try {
        Ensure-Directory -Path $reportFullPath
        $reportObject | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $reportFullPath -Encoding UTF8
        Write-Log ("REPORT WRITTEN :: {0}" -f $reportFullPath)
    }
    catch {
        Write-Log ("REPORT WRITE FAILURE :: {0}" -f $_.Exception.Message)
        throw "Could not write JSON report to '$reportFullPath'."
    }

    Write-Log ("FINAL STATUS :: {0}" -f $overallStatus)
    Write-Log "=== PYTHON ANALYSIS TOOL SETUP END ==="
}

if ($overallStatus -eq "FAILED") {
    Write-Host "Setup FAILED. See report: $reportFullPath"
    exit 2
}
elseif ($overallStatus -eq "PARTIAL_FAILURE") {
    Write-Host "Setup completed with PARTIAL_FAILURE. See report: $reportFullPath"
    exit 1
}
else {
    Write-Host "Setup SUCCESS. See report: $reportFullPath"
    exit 0
}
```

**a.** Want the timeout path to also include a clearer `failure_reason` (e.g., `TIMED_OUT`) per tool in the JSON report?  
**b.** Want exponential backoff for retries (still “latest available”, but better resilience)?

## Response:
Code Copilot

Thought for 9s

Here are my **other recommendations** (beyond removing `snakefood`, fixing `pipreqs` verify, and fixing `$Venv` typing + enforcing real timeouts) to make the **final** script production-hard.

Reliability + correctness
-------------------------

1.  **Per-tool timeout + install timeout**
    *   Separate timeouts:
    *   `verify_timeout_seconds` (fast, e.g., 30–120s)
    *   `install_timeout_seconds` (slower, e.g., 600–1800s)
*   Rationale: installs can legitimately take longer than `--version/--help`.
    2.  **Mark timeout explicitly in JSON**
    *   Add `failure_reason = "TIMED_OUT"` and maybe `timed_out = true`.
*   Add `duration_ms` for verify + install.
*   Rationale: makes timeouts searchable/actionable in CI logs.
    3.  **Capture “what failed”: phase + last command**
    *   Add fields like:
    *   `failed_phase`: `verify_initial | install | verify_postinstall`
    *   `last_command`: already present in invoke result—surface it on the tool record too.
*   Rationale: eliminates guessing from tail logs.
    4.  **Always use `python -m pip` (never `pip.exe`)**
    *   You already do this in the fixed version. Keep it as a rule everywhere.
*   Rationale: avoids PATH/launcher ambiguity.
    5.  **Verify CLI tools via module fallback**
    *   Some packages don’t reliably create an exe on Windows (or name differs).
*   Add optional fallback for CLI tools:
    *   try `Scripts\<exe>` first
    *   if missing, try `python -m <module> <verify_args>`
*   Rationale: makes verification resilient to entrypoint naming/creation differences.
    6.  **After installing all tools, run `pip check` once**
    *   `python -m pip check` catches broken dependency sets early.
*   Rationale: fast sanity check that prevents “installed but unusable”.

Install behavior (“latest available” but stable-ish)
----------------------------------------------------

7.  **Prefer `--upgrade` only when needed**
    *   For “latest available” you may still want upgrades, but consider:
    *   install missing: `pip install <pkg>`
    *   if already present but invalid: `pip install --upgrade <pkg>`
*   Rationale: avoids churn on every run.
    8.  **Use pip flags to reduce flakiness/noise**
    *   Recommended flags for CI-ish usage:
    *   `--disable-pip-version-check`
    *   `--no-input`
    *   optionally `--retries N` and `--timeout S` (pip’s own network timeout)
*   Rationale: fewer interactive hangs and fewer spurious logs.
    9.  **Proxy / corporate network support**
    *   Allow pass-through of:
    *   `PIP_INDEX_URL`, `PIP_EXTRA_INDEX_URL`, `PIP_TRUSTED_HOST`, `HTTPS_PROXY`, etc.
*   Don’t hardcode; just document + ensure you don’t clear env.
*   Rationale: real-world enterprise survivability.

Reporting improvements
----------------------

10.  **Record versions deterministically (even if installs aren’t)**
    *   In report add:
    *   `python_version`
    *   `pip_version`
    *   `tools[*].version`
    *   optionally `pip_freeze` output (or at least a `requirements.txt` snapshot)
*   Rationale: when something breaks later, you can diff what changed.
    11.  **Include structured stderr/stdout tails per phase**
    *   Right now you store tails, but they can get overwritten between verify/install.
*   Store:
    *   `initial_verify_stdout_tail`, `initial_verify_stderr_tail`
    *   `install_stdout_tail`, `install_stderr_tail`
    *   `post_verify_stdout_tail`, `post_verify_stderr_tail`
*   Rationale: no lost evidence.
    12.  **Normalize status taxonomy**
    *   Recommend consistent statuses:
    *   `VALID` (already good)
    *   `INSTALLED`
    *   `FAILED_VERIFY`
    *   `FAILED_INSTALL`
    *   `TIMED_OUT`
*   Rationale: easier downstream automation (CI gates, dashboards).

Small maintainability wins
--------------------------

13.  **Put tools in a data file (optional)**
    *   e.g., JSON/PSD1 list of tools to keep script smaller and diffs cleaner.
*   Rationale: tool list changes shouldn’t touch code paths.
    14.  **Make “required” meaningful**
    *   If `required = $false`, don’t flip overall status to `PARTIAL_FAILURE`.
*   Rationale: optional tools shouldn’t fail the run.
    15.  **Add `#requires -Version 7.0`**
    *   You’re on PS 7.5.5—make it explicit.
*   Rationale: avoids support confusion and edge host behavior.

* * *

Direct answers to your two prompts
----------------------------------

*   **a)** Yes, strongly recommended. Add `TIMED_OUT` per tool + `duration_ms`.
*   **b)** Yes, recommended if this will run in CI or behind flaky networking. Add exponential backoff with small jitter; keep max bounded (e.g., 2–3 attempts).

**a.** Want me to implement (a) + (b) _and_ the “phase-specific tails + duration\_ms” reporting in the final script?  
**b.** Should optional tools (`required = $false`) be allowed to fail without making the overall run `PARTIAL_FAILURE`?

## Response:
Code Copilot

Thought for 4s

I reviewed both attachments:

*   **“Modification Specification: Global Tooling Upgrades & Configuration Decoupling”** Py script changes 2
*   **“Now I have the full picture…” (verdict + priority table)** Py script changes

Below is my feedback + what I recommend you change (and what I _don’t_ recommend), so we can build the **final** version cleanly.

* * *

1) Big architectural change: **remove venv + go global installs**
-----------------------------------------------------------------

Your spec (file0) wants to **eradicate venv scaffolding** and run everything via global Python. Py script changes 2

### My recommendation

**Do it only if disk space is the #1 constraint** and you accept the trade-offs:

**Pros**

*   Much less disk use (no duplicate stdlib + site-packages per venv).
*   Simpler runtime paths.

**Cons (real operational risk)**

*   **Dependency collisions** across projects (explicitly acknowledged in spec). Py script changes 2
*   **Permissions** vary by environment (pip may default to user site, and PATH might not include Scripts).
*   Harder to make runs reproducible.

### Modification guidance if you go global (recommended implementation pattern)

Instead of “system-wide” installs, strongly prefer **user-level** global:

*   Always install with `python -m pip install --user ...` (unless you detect you’re already inside an isolated environment).
*   Then resolve executables by asking Python where the user scripts dir is (not PATH).

This avoids admin requirements while still meeting “no venv” storage goals.

* * *

2) Externalize `$Tools` to SSOT JSON
------------------------------------

Spec says: move tool list to `tools_config.json`. Py script changes 2  
Verdict says: valid but optional. Py script changes

### My recommendation

✅ **Yes, do it** — not just for cleanliness, but because it allows:

*   tool changes without touching logic
*   per-tool timeouts, verify methods, import names, optional flags
*   clean CI diffs

**Must-have addition to the config format**  
Add these fields per tool:

*   `verify_timeout_seconds`
*   `install_timeout_seconds`
*   `required`
*   `verify_type` (`cli`/`import`)
*   `cli` tools: `exe_name`, `verify_args`
*   `import` tools: `import_name`
*   optionally: `module_entrypoint` (for `python -m X` fallback)

* * *

3) “Always upgrade” vs “upgrade only when needed”
-------------------------------------------------

Spec requests: inject `--upgrade` into install always. Py script changes 2  
Verdict suggests nuanced approach: upgrade only when needed. Py script changes

### My recommendation (given you want “latest available”)

✅ Use `--upgrade` **when verification fails** (or when tool missing).  
In practice that means: **always upgrade** is fine and simpler for your goal. BUT:

**Add one guard:** don’t upgrade if tool is already valid and you’re optimizing runtime speed.

So:

*   If tool verifies OK → skip install.
*   Else → `pip install --upgrade ...`

That matches “latest available” while avoiding pointless upgrades.

* * *

4) CLI path resolution: don’t hardcode Scripts dir
--------------------------------------------------

Spec calls out PATH issues for global installs and says: resolve install path dynamically (suggesting `pip show`). Py script changes 2  
Verdict confirms current script hardcodes `Scripts\<exe>` and will fail if exe is elsewhere. Py script changes

### My recommendation

✅ Don’t rely on PATH. Don’t rely on `pip show` alone either.

**Best approach for global user installs (Windows):**

*   Resolve scripts dir via python:
    *   `python -c "import sysconfig; print(sysconfig.get_path('scripts'))"`
*   Then check `${scriptsDir}\ruff.exe`, etc.
*   If missing, fallback to `python -m <module> ...` if you have a module entrypoint.

This is more reliable than `pip show` because it doesn’t depend on parsing location strings or pip formatting.

* * *

5) Timeouts + reporting improvements (high priority)
----------------------------------------------------

Your verdict doc identifies concrete gaps: timeout not labeled, phase evidence overwritten, and missing phase/command fields. Py script changes

### My recommendation (do all of these)

✅ **A. Split timeouts**

*   verify: 30–120s
*   install: 600–1800s  
    (Your current design uses one default for everything; that’s bad operationally.) Py script changes

✅ **B. Mark timeouts explicitly**

*   if `ExitCode == 124`: set `status = "TIMED_OUT"` and `failure_reason = "TIMED_OUT"` (not a stderr substring). Py script changes

✅ **C. Preserve phase outputs**  
Right now stdout/stderr tails get overwritten across phases. Py script changes  
Add:

*   `initial_verify_*`
*   `install_*`
*   `post_verify_*`

✅ **D. Surface `last_command`, `duration_ms`, and `failed_phase`**  
Verdict: these exist in invoke results but aren’t retained in tool record. Py script changes

* * *

6) Critical correctness bug: optional tools still trigger PARTIAL\_FAILURE
--------------------------------------------------------------------------

Verdict flags this as **critical**: required flag isn’t honored when computing overall status. Py script changes

### My recommendation

✅ Fix immediately:

*   Only set overall status to `PARTIAL_FAILURE` if a **required** tool fails.
*   Optional tool failures should be recorded but not gate CI unless you explicitly want them to.

* * *

7) Add `pip check` at end
-------------------------

Verdict: low-cost safety net; not present. Py script changes

### My recommendation

✅ Add:

*   `python -m pip check`
*   If fails: set `overall_status = PARTIAL_FAILURE` (or `FAILED` depending on your policy), attach output to report.

* * *

8) Extra “global mode” hardening I recommend adding
---------------------------------------------------

Not explicitly in the two files, but becomes important if you go global:

1.  **Force `--no-input` for pip**  
    Prevents hangs.
2.  **Pass pip network knobs**  
    `--retries`, `--timeout` (pip’s own).
3.  **Detect multiple Pythons**  
    Record:
    *   python executable path
*   python version string
*   whether running under Store Python vs traditional install

(These help explain weird installs.)

* * *

Concrete “final build” checklist (recommended order)
----------------------------------------------------

1.  Implement **required flag gating** for overall status. Py script changes
2.  Implement **phase-separated tails + failed\_phase + last\_command + duration\_ms**. Py script changes
3.  Implement **per-tool verify/install timeouts** and label `TIMED_OUT`. Py script changes
4.  If going global: remove venv, implement **sysconfig scripts dir resolution**. Py script changes 2
5.  Load tools from `tools_config.json`. Py script changes 2
6.  Add `pip check`. Py script changes

* * *

**a.** Do you want “global installs” to be **user-only (`--user`)** to avoid admin prompts, or truly system-wide?  
**b.** Want me to generate the final `tools_config.json` schema + a sample file matching your current tool set?

## Response:
Code Copilot

You can “preflight” global installs pretty well **before running** by doing three quick audits: **environment isolation risk**, **permissions/paths**, and **reproducibility drift**. Here’s a practical checklist you can run as a **read-only diagnostic** (no installs).

* * *

1) Dependency collisions across projects — how to gauge risk
------------------------------------------------------------

### What you’re trying to detect

Global site-packages becomes a shared bucket. Collisions happen when:

*   two tools require incompatible versions of the same dependency
*   some other project already pinned/installed a conflicting version
*   PATH resolves to the “wrong” tool executable (another Python install or old Scripts dir)

### Preflight checks

**A. Identify where this Python installs packages**

```
python -c "import sys,site,sysconfig; print('exe:',sys.executable); print('prefix:',sys.prefix); print('userbase:',site.USER_BASE); print('usersite:',site.getusersitepackages()); print('purelib:',sysconfig.get_path('purelib')); print('scripts:',sysconfig.get_path('scripts'))"
```

**B. Snapshot currently installed packages**

```
python -m pip list --format=json > .\pip-list.before.json
python -m pip freeze > .\pip-freeze.before.txt
python -m pip check
```

*   `pip check` is the fastest early signal of an already-broken environment.

**C. Detect “multiple Python” + PATH ambiguity**

```
Get-Command python, py -All | Format-Table CommandType, Name, Source
python -c "import sys; print(sys.executable)"
py -0p 2>$null
```

If you see multiple `python.exe` locations, collision risk is higher.

**D. Dry-run dependency impact (best-effort)**  
Pip has `--dry-run` in newer versions (behavior varies by version), but you can often do:

```
python -m pip install --dry-run --upgrade pipreqs semgrep radon ruff mypy 2>$null
```

If `--dry-run` isn’t supported in your pip, skip it; rely on snapshots + `pip check`.

**How to interpret**

*   If `pip check` fails **before** installing anything: you already have conflicts.
*   If you have **many** globally installed libraries: collision risk increases.
*   If your machine has **multiple Pythons** (Store + python.org + conda): PATH risk increases.

* * *

2) Permissions / where pip will install — how to gauge risk
-----------------------------------------------------------

### What you’re trying to detect

Whether pip can write to the target site-packages and whether executables will be discoverable.

### Preflight checks

**A. See pip’s install scheme + whether it’s using user-site**

```
python -m pip debug --verbose | Select-String -Pattern "user site|site-packages|scheme|scripts|prefix"
```

**B. Confirm scripts directory exists and is on PATH**

```
$scripts = python -c "import sysconfig; print(sysconfig.get_path('scripts'))"
$scripts
$env:Path -split ';' | Where-Object { $_ -eq $scripts }
Test-Path $scripts
```

If `$scripts` is not on PATH, `ruff`, `mypy`, `pipreqs` may install but not be invokable by name.

**C. Confirm user-site is enabled (important if you plan `--user`)**

```
python -c "import site; print('ENABLE_USER_SITE=', site.ENABLE_USER_SITE); print('USER_SITE=', site.getusersitepackages())"
```

**How to interpret**

*   If user-site is disabled or scripts dir isn’t on PATH, you’ll get “installed but not found” behavior.
*   If you don’t have permissions to system site-packages, `pip install` may fail unless `--user` is used.

* * *

3) Reproducibility — how to gauge drift risk
--------------------------------------------

### What you’re trying to detect

“latest available” means you can’t guarantee the same set of versions tomorrow.

### Preflight checks / mitigations

**A. Record a baseline lock snapshot**  
Even if you don’t pin, you can _record_ what you got:

```
python -m pip freeze > .\pip-freeze.baseline.txt
python -m pip list --format=json > .\pip-list.baseline.json
python -c "import sys; print(sys.version); print(sys.executable)" > .\python-baseline.txt
```

**B. Record index source**

```
python -m pip config list
python -m pip debug --verbose | Select-String -Pattern "index-url|extra-index-url|trusted-host"
```

**How to interpret**

*   If you can’t accept drift, you need constraints/lock later.
*   If you can accept drift but want debuggability, snapshots are enough.

* * *

Recommended “preflight gate” policy (simple)
--------------------------------------------

Before running the real install:

1.  `python -m pip check` must be clean (or you accept preexisting broken state)
2.  Ensure the intended Python is the one on PATH (verify `sys.executable`)
3.  Ensure scripts dir is discoverable (PATH or direct path usage)
4.  Save `pip freeze` snapshot for rollback / diff

* * *

If you want, I can give you a single **Preflight.ps1** script that runs all checks and outputs a **red/yellow/green** summary + saves snapshots—no installs.

**a.** Do you intend to install globally as **system site-packages** or **user site (`--user`)**?  
**b.** Do you want the preflight to fail hard if `pip check` is already broken, or just warn?

## Response:
Code Copilot

TL;DR: A local-environment CLI should run **read-only probes**, classify findings into **machine-readable codes**, and emit a **stable JSON report** (plus optional human text). That lets _another_ CLI app consume the report and decide what to do next.

What it should do
-----------------

### 1) Collect environment facts (no writes)

*   Resolve Python executables:
    *   `python` on PATH
    *   `py` launcher (Windows) and discovered installs
*   Capture interpreter identity:
    *   `sys.executable`, `sys.version`, `sys.prefix`, `sys.base_prefix`
    *   `venv/conda` detection (e.g., `sys.prefix != sys.base_prefix`, `CONDA_PREFIX`)
*   Capture install locations:
    *   `site.getusersitepackages()`, `site.USER_BASE`, `site.ENABLE_USER_SITE`
    *   `sysconfig.get_path('purelib')`, `sysconfig.get_path('scripts')`
*   Capture pip configuration + index sources:
    *   `pip config list`
    *   `pip debug --verbose` (extract index-url/extra-index-url/trusted-host + scheme paths)

### 2) Run “health checks” (still read-only)

*   Dependency integrity:
    *   `python -m pip check`
*   Snapshot inventory:
    *   `python -m pip list --format=json`
    *   optionally `python -m pip freeze`
*   PATH discoverability:
    *   verify `sysconfig scripts` directory exists
    *   verify scripts dir is in PATH (or flag “invocation may fail”)
*   Multi-Python ambiguity:
    *   list all `python`/`py` resolutions on PATH and flag if >1
*   Optional: “planned install impact” (best-effort)
    *   attempt `pip install --dry-run --upgrade <tools>` if supported; otherwise skip with a capability flag

### 3) Detect risk signals + classify them

This is the key: **turn raw data into stable findings** with:

*   `id` (stable code) e.g. `PYTHON.MULTIPLE_ON_PATH`
*   `severity` (`INFO|WARN|ERROR`)
*   `summary` (short human sentence)
*   `evidence` (structured fields: paths, outputs, exit codes)
*   `remediation` (actionable suggestions)
*   `tags` (e.g., `["collision", "permissions", "reproducibility"]`)

### 4) Report in a way another CLI can modify/act on

Emit:

1.  **JSON** (primary, stable schema)
2.  optional **human-readable** text (secondary)

Also provide:

*   exit code policy (e.g., any `ERROR` → nonzero)
*   allow filtering (e.g., `--only collision,permissions`)
*   allow “fix-mode” later (separate command), but keep preflight read-only by default

* * *

Suggested JSON schema (practical + extensible)
----------------------------------------------

Use this shape so downstream tooling can easily parse/transform:

```
{
  "meta": {
    "tool": "py-env-preflight",
    "version": "1.0.0",
    "timestamp_utc": "2026-03-27T18:00:00Z",
    "host": { "os": "Windows", "arch": "x64" }
  },
  "environment": {
    "python": {
      "primary_executable": "C:\\...\\python.exe",
      "version": "3.12.2",
      "prefix": "C:\\...\\",
      "base_prefix": "C:\\...\\",
      "is_venv": false,
      "is_conda": false
    },
    "pip": {
      "version": "24.3.1",
      "indexes": { "index_url": "...", "extra_index_urls": [] },
      "paths": { "purelib": "...", "scripts": "..." },
      "user_site": { "enabled": true, "path": "..." }
    },
    "path": {
      "entries": ["..."],
      "python_commands": [
        { "name": "python", "path": "C:\\...\\python.exe" },
        { "name": "python", "path": "C:\\...\\other\\python.exe" }
      ]
    }
  },
  "checks": [
    { "name": "pip_check", "exit_code": 0, "stdout": "", "stderr": "" },
    { "name": "pip_list", "exit_code": 0, "packages_count": 312 }
  ],
  "findings": [
    {
      "id": "PYTHON.MULTIPLE_ON_PATH",
      "severity": "WARN",
      "summary": "Multiple python executables found on PATH; tool resolution may be inconsistent.",
      "evidence": { "paths": ["C:\\...\\python.exe", "C:\\...\\python.exe"] },
      "remediation": [
        "Pin to a specific python executable path in config.",
        "Ensure only one python is early in PATH."
      ],
      "tags": ["collision", "permissions"]
    }
  ],
  "capabilities": {
    "pip_dry_run_supported": true
  },
  "exit_code_policy": {
    "errors": 2,
    "warnings": 0
  }
}
```

Downstream CLI can:

*   gate on `severity`
*   map `findings[].id` to automatic fixes
*   rewrite config based on `environment.pip.paths.scripts`
*   store snapshots for reproducibility

* * *

CLI UX pattern that scales
--------------------------

Implement as subcommands:

*   `preflight scan --json out.json --text out.txt`
*   `preflight scan --format json` (stdout)
*   `preflight explain PYTHON.MULTIPLE_ON_PATH`
*   later: `preflight fix --apply` (separate, explicit)

Flags:

*   `--tools tools_config.json` (optional) so it can assess “planned” tool installs
*   `--strict` (warnings become nonzero)
*   `--redact` (hide usernames/paths if needed)
*   `--timeout 30` per subprocess call

* * *

Mapping to your three risk categories
-------------------------------------

### Dependency collisions

Signals:

*   `pip check` nonzero
*   huge global package set
*   multiple Pythons on PATH
*   conda/venv mixed with global user-site

Finding IDs (examples):

*   `PIP.CHECK_FAILED` (ERROR)
*   `PYTHON.MULTIPLE_ON_PATH` (WARN)
*   `ENV.MIXED_CONDA_AND_SYSTEM` (WARN)

### Permissions / PATH variability

Signals:

*   scripts dir not in PATH
*   user-site disabled + no admin rights
*   pip scheme indicates system site-packages but not writable

Finding IDs:

*   `PATH.SCRIPTS_DIR_NOT_ON_PATH` (WARN)
*   `PIP.USER_SITE_DISABLED` (WARN/ERROR)
*   `FS.SITEPACKAGES_NOT_WRITABLE` (ERROR)

### Reproducibility drift

Signals:

*   “latest available” mode with no snapshot output
*   index URL differs across hosts
*   pip config includes extra indexes

Finding IDs:

*   `REPRO.NO_SNAPSHOT` (WARN)
*   `PIP.NONDEFAULT_INDEX` (INFO/WARN)

* * *

If you tell me what language you want for the CLI (Go/Rust/Python/Node) and target OS (Windows-only or cross-platform), I can write the full implementation with this schema.

**a.** Which language do you want for the preflight CLI (Go/Rust/Python/Node)?  
**b.** Should the CLI emit only JSON by default (for automation) and a `--pretty` human view as optional?

## Response:
Code Copilot

Thought for 6s

TL;DR: Here’s a **Windows-only Python CLI** that runs **read-only preflight checks** (pip health, paths, multi-python ambiguity, permissions-ish signals, reproducibility context) and emits **JSON only** to stdout (or `--out`).

Plan (pseudocode)
-----------------

1.  Parse args:
    *   `--python` optional (defaults to current `sys.executable`)
    *   `--tools-config` optional (JSON list; used only to attempt `--dry-run` impact if supported)
    *   `--timeout-seconds` per subprocess
    *   `--out` optional (write JSON file)
    *   `--exit-nonzero-on-error` optional
2.  Run probes (read-only):
    *   Python facts via `python -c` JSON emitter
    *   `where python` / `where py` to enumerate candidates
    *   `python -m pip --version`
    *   `python -m pip debug --verbose`
    *   `python -m pip config list`
    *   `python -m pip check`
    *   `python -m pip list --format=json`
    *   Determine pip `--dry-run` support from `pip install --help`
    *   If supported + tools-config provided: attempt `pip install --dry-run --upgrade <pkgs>`
3.  Compute findings with stable IDs:
    *   Multiple python executables on PATH
    *   Scripts dir missing / not in PATH
    *   User site disabled
    *   `pip check` failed
    *   Non-default index URL present
    *   Mixed conda/venv indicators
4.  Emit JSON:
    *   meta/environment/checks/findings/capabilities/exit\_code\_policy
5.  Exit policy:
    *   default exit 0
    *   if `--exit-nonzero-on-error` and any ERROR finding → exit 2

```
# py_env_preflight.py
"""
Windows-only Python environment preflight scanner.

Emits JSON only (to stdout by default) describing:
- Python identity and installation paths
- pip configuration and scheme paths
- dependency integrity (pip check)
- PATH discoverability of Scripts directory
- multi-python ambiguity
- reproducibility context (index urls, config, snapshots via pip list)

This tool is intentionally read-only: it does not install, upgrade, or modify env state.
Optionally, it can attempt a best-effort pip --dry-run impact check if supported and
a tools config is provided.

Usage:
  python py_env_preflight.py
  python py_env_preflight.py --out preflight.json
  python py_env_preflight.py --python C:\\Path\\to\\python.exe
  python py_env_preflight.py --tools-config tools_config.json

Exit codes:
  0 - completed (default; even if findings exist)
  2 - only if --exit-nonzero-on-error and at least one ERROR finding exists
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

@dataclass(frozen=True)
class CmdResult:
    argv: List[str]
    exit_code: int
    duration_ms: int
    stdout: str
    stderr: str
    timed_out: bool

def run_cmd(argv: List[str], timeout_s: int) -> CmdResult:
    start = time.perf_counter()
    try:
        cp = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            shell=False,
        )
        dur_ms = int((time.perf_counter() - start) * 1000)
        return CmdResult(
            argv=argv,
            exit_code=cp.returncode,
            duration_ms=dur_ms,
            stdout=cp.stdout or "",
            stderr=cp.stderr or "",
            timed_out=False,
        )
    except subprocess.TimeoutExpired as e:
        dur_ms = int((time.perf_counter() - start) * 1000)
        return CmdResult(
            argv=argv,
            exit_code=124,
            duration_ms=dur_ms,
            stdout=(e.stdout or "") if isinstance(e.stdout, str) else "",
            stderr=(e.stderr or "") if isinstance(e.stderr, str) else "",
            timed_out=True,
        )
    except FileNotFoundError as e:
        dur_ms = int((time.perf_counter() - start) * 1000)
        return CmdResult(
            argv=argv,
            exit_code=127,
            duration_ms=dur_ms,
            stdout="",
            stderr=str(e),
            timed_out=False,
        )

def where_all(command: str, timeout_s: int) -> List[str]:
    res = run_cmd(["where", command], timeout_s=timeout_s)
    if res.exit_code != 0:
        return []
    lines = [ln.strip() for ln in res.stdout.splitlines() if ln.strip()]
    # de-dup while preserving order
    seen: set[str] = set()
    out: List[str] = []
    for p in lines:
        if p.lower() not in seen:
            out.append(p)
            seen.add(p.lower())
    return out

def load_tools_config(path: Path) -> List[Dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, dict) and "tools" in raw and isinstance(raw["tools"], list):
        return raw["tools"]
    if isinstance(raw, list):
        return raw
    raise ValueError("tools config must be a list or an object with a 'tools' list")

def python_json_probe(python_exe: str, timeout_s: int) -> Tuple[Optional[Dict[str, Any]], CmdResult]:
    code = r"""
import json, os, sys, site, sysconfig
data = {
  "sys_executable": sys.executable,
  "sys_version": sys.version,
  "version_info": list(sys.version_info),
  "prefix": sys.prefix,
  "base_prefix": getattr(sys, "base_prefix", sys.prefix),
  "real_prefix": getattr(sys, "real_prefix", None),
  "is_venv": (getattr(sys, "base_prefix", sys.prefix) != sys.prefix) or (getattr(sys, "real_prefix", None) is not None),
  "is_conda": bool(os.environ.get("CONDA_PREFIX")),
  "conda_prefix": os.environ.get("CONDA_PREFIX"),
  "enable_user_site": getattr(site, "ENABLE_USER_SITE", None),
  "user_base": getattr(site, "USER_BASE", None),
  "user_site": (site.getusersitepackages() if hasattr(site, "getusersitepackages") else None),
  "purelib": sysconfig.get_path("purelib"),
  "platlib": sysconfig.get_path("platlib"),
  "scripts": sysconfig.get_path("scripts"),
}
print(json.dumps(data))
""".strip()
    res = run_cmd([python_exe, "-c", code], timeout_s=timeout_s)
    if res.exit_code != 0 or not res.stdout.strip():
        return None, res
    try:
        return json.loads(res.stdout.strip()), res
    except json.JSONDecodeError:
        return None, res

def parse_pip_indexes(pip_debug_text: str) -> Dict[str, Any]:
    # Best-effort parsing across pip versions; keep raw in checks anyway.
    index_url = None
    extra: List[str] = []
    trusted: List[str] = []

    # Patterns seen in pip debug --verbose output.
    m = re.search(r"index-url:\s*(\S+)", pip_debug_text, re.IGNORECASE)
    if m:
        index_url = m.group(1).strip()

    for m in re.finditer(r"extra-index-url:\s*(\S+)", pip_debug_text, re.IGNORECASE):
        extra.append(m.group(1).strip())

    for m in re.finditer(r"trusted-host:\s*(\S+)", pip_debug_text, re.IGNORECASE):
        trusted.append(m.group(1).strip())

    return {
        "index_url": index_url,
        "extra_index_urls": extra,
        "trusted_hosts": trusted,
    }

def scripts_dir_on_path(scripts_dir: Optional[str]) -> bool:
    if not scripts_dir:
        return False
    target = scripts_dir.rstrip("\\/").lower()
    for entry in os.environ.get("PATH", "").split(";"):
        if entry.rstrip("\\/").lower() == target:
            return True
    return False

def add_finding(
    findings: List[Dict[str, Any]],
    *,
    fid: str,
    severity: str,
    summary: str,
    evidence: Dict[str, Any],
    remediation: List[str],
    tags: List[str],
) -> None:
    findings.append(
        {
            "id": fid,
            "severity": severity,
            "summary": summary,
            "evidence": evidence,
            "remediation": remediation,
            "tags": tags,
        }
    )

def main() -> int:
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--python", default=sys.executable, help="Path to python.exe to inspect (default: current interpreter).")
    ap.add_argument("--tools-config", default=None, help="Optional tools config JSON. Used only for best-effort pip --dry-run checks.")
    ap.add_argument("--timeout-seconds", type=int, default=30, help="Timeout per subprocess call.")
    ap.add_argument("--out", default=None, help="Optional output JSON file path.")
    ap.add_argument("--exit-nonzero-on-error", action="store_true", help="Exit 2 if any ERROR finding exists.")
    args = ap.parse_args()

    python_exe = str(Path(args.python).expanduser())
    timeout_s = max(1, int(args.timeout_seconds))

    checks: List[Dict[str, Any]] = []
    findings: List[Dict[str, Any]] = []

    # Resolve PATH candidates (Windows-only)
    python_candidates = where_all("python", timeout_s=timeout_s)
    py_candidates = where_all("py", timeout_s=timeout_s)

    # Probe python facts
    py_info, py_probe_res = python_json_probe(python_exe, timeout_s=timeout_s)
    checks.append(
        {
            "name": "python_probe",
            "argv": py_probe_res.argv,
            "exit_code": py_probe_res.exit_code,
            "duration_ms": py_probe_res.duration_ms,
            "timed_out": py_probe_res.timed_out,
            "stdout_tail": (py_probe_res.stdout[-4000:] if py_probe_res.stdout else ""),
            "stderr_tail": (py_probe_res.stderr[-4000:] if py_probe_res.stderr else ""),
        }
    )

    # pip basics
    pip_version_res = run_cmd([python_exe, "-m", "pip", "--version"], timeout_s=timeout_s)
    checks.append(
        {
            "name": "pip_version",
            "argv": pip_version_res.argv,
            "exit_code": pip_version_res.exit_code,
            "duration_ms": pip_version_res.duration_ms,
            "timed_out": pip_version_res.timed_out,
            "stdout_tail": pip_version_res.stdout[-4000:],
            "stderr_tail": pip_version_res.stderr[-4000:],
        }
    )

    pip_debug_res = run_cmd([python_exe, "-m", "pip", "debug", "--verbose"], timeout_s=timeout_s)
    checks.append(
        {
            "name": "pip_debug_verbose",
            "argv": pip_debug_res.argv,
            "exit_code": pip_debug_res.exit_code,
            "duration_ms": pip_debug_res.duration_ms,
            "timed_out": pip_debug_res.timed_out,
            "stdout_tail": pip_debug_res.stdout[-4000:],
            "stderr_tail": pip_debug_res.stderr[-4000:],
        }
    )

    pip_config_res = run_cmd([python_exe, "-m", "pip", "config", "list"], timeout_s=timeout_s)
    checks.append(
        {
            "name": "pip_config_list",
            "argv": pip_config_res.argv,
            "exit_code": pip_config_res.exit_code,
            "duration_ms": pip_config_res.duration_ms,
            "timed_out": pip_config_res.timed_out,
            "stdout_tail": pip_config_res.stdout[-4000:],
            "stderr_tail": pip_config_res.stderr[-4000:],
        }
    )

    pip_check_res = run_cmd([python_exe, "-m", "pip", "check"], timeout_s=timeout_s)
    checks.append(
        {
            "name": "pip_check",
            "argv": pip_check_res.argv,
            "exit_code": pip_check_res.exit_code,
            "duration_ms": pip_check_res.duration_ms,
            "timed_out": pip_check_res.timed_out,
            "stdout_tail": pip_check_res.stdout[-4000:],
            "stderr_tail": pip_check_res.stderr[-4000:],
        }
    )

    pip_list_res = run_cmd([python_exe, "-m", "pip", "list", "--format=json"], timeout_s=timeout_s)
    packages_count = None
    if pip_list_res.exit_code == 0 and pip_list_res.stdout.strip():
        try:
            pkgs = json.loads(pip_list_res.stdout)
            if isinstance(pkgs, list):
                packages_count = len(pkgs)
        except json.JSONDecodeError:
            pass
    checks.append(
        {
            "name": "pip_list_json",
            "argv": pip_list_res.argv,
            "exit_code": pip_list_res.exit_code,
            "duration_ms": pip_list_res.duration_ms,
            "timed_out": pip_list_res.timed_out,
            "packages_count": packages_count,
            "stdout_tail": pip_list_res.stdout[-4000:],
            "stderr_tail": pip_list_res.stderr[-4000:],
        }
    )

    # Determine pip --dry-run support
    pip_install_help = run_cmd([python_exe, "-m", "pip", "install", "--help"], timeout_s=timeout_s)
    dry_run_supported = "--dry-run" in (pip_install_help.stdout or "")
    checks.append(
        {
            "name": "pip_install_help",
            "argv": pip_install_help.argv,
            "exit_code": pip_install_help.exit_code,
            "duration_ms": pip_install_help.duration_ms,
            "timed_out": pip_install_help.timed_out,
            "stdout_tail": pip_install_help.stdout[-4000:],
            "stderr_tail": pip_install_help.stderr[-4000:],
        }
    )

    # Optional dry-run impact check against planned tools
    dry_run_impact_res: Optional[CmdResult] = None
    planned_packages: List[str] = []
    if args.tools_config:
        try:
            tools = load_tools_config(Path(args.tools_config))
            for t in tools:
                pkg = t.get("package") or t.get("name")
                if isinstance(pkg, str) and pkg.strip():
                    planned_packages.append(pkg.strip())
        except Exception as e:
            add_finding(
                findings,
                fid="CONFIG.TOOLS_CONFIG_INVALID",
                severity="WARN",
                summary="tools-config could not be parsed; dry-run impact check skipped.",
                evidence={"tools_config": args.tools_config, "error": str(e)},
                remediation=["Fix the JSON format or omit --tools-config."],
                tags=["reproducibility"],
            )

    if planned_packages and dry_run_supported:
        argv = [python_exe, "-m", "pip", "install", "--dry-run", "--upgrade"] + planned_packages
        dry_run_impact_res = run_cmd(argv, timeout_s=max(timeout_s, 60))
        checks.append(
            {
                "name": "pip_install_dry_run_upgrade",
                "argv": dry_run_impact_res.argv,
                "exit_code": dry_run_impact_res.exit_code,
                "duration_ms": dry_run_impact_res.duration_ms,
                "timed_out": dry_run_impact_res.timed_out,
                "stdout_tail": dry_run_impact_res.stdout[-4000:],
                "stderr_tail": dry_run_impact_res.stderr[-4000:],
            }
        )

    # Findings synthesis
    # 1) Multi-python ambiguity
    if len(python_candidates) > 1:
        add_finding(
            findings,
            fid="PYTHON.MULTIPLE_ON_PATH",
            severity="WARN",
            summary="Multiple python executables found on PATH; tool resolution may be inconsistent.",
            evidence={"where_python": python_candidates},
            remediation=[
                "Pin the python executable path in your automation/config.",
                "Ensure the intended python is first on PATH.",
            ],
            tags=["collision", "permissions"],
        )

    if not python_candidates:
        add_finding(
            findings,
            fid="PYTHON.NOT_FOUND_ON_PATH",
            severity="WARN",
            summary="No 'python' found via PATH resolution (where python).",
            evidence={"where_python": python_candidates},
            remediation=[
                "Ensure python.exe is on PATH or run automation using an absolute python path.",
            ],
            tags=["permissions"],
        )

    # 2) Dependency integrity
    if pip_check_res.exit_code != 0:
        sev = "ERROR" if pip_check_res.exit_code not in (124, 127) else "WARN"
        add_finding(
            findings,
            fid="PIP.CHECK_FAILED",
            severity=sev,
            summary="pip check reported broken/incompatible dependencies.",
            evidence={
                "exit_code": pip_check_res.exit_code,
                "stdout_tail": pip_check_res.stdout[-2000:],
                "stderr_tail": pip_check_res.stderr[-2000:],
            },
            remediation=[
                "Resolve dependency conflicts before installing additional tools.",
                "Consider using a venv if conflicts are frequent.",
            ],
            tags=["collision"],
        )

    # 3) Scripts dir discoverability
    scripts_dir = (py_info or {}).get("scripts") if py_info else None
    scripts_exists = bool(scripts_dir and Path(str(scripts_dir)).exists())
    if scripts_dir and not scripts_exists:
        add_finding(
            findings,
            fid="PATH.SCRIPTS_DIR_MISSING",
            severity="ERROR",
            summary="Python scripts directory does not exist; console entrypoints may not be created or discoverable.",
            evidence={"scripts_dir": scripts_dir},
            remediation=[
                "Reinstall/repair Python or ensure sysconfig scripts path is valid.",
                "If using --user installs, ensure user base is configured correctly.",
            ],
            tags=["permissions"],
        )
    elif scripts_dir and not scripts_dir_on_path(str(scripts_dir)):
        add_finding(
            findings,
            fid="PATH.SCRIPTS_DIR_NOT_ON_PATH",
            severity="WARN",
            summary="Python scripts directory is not on PATH; installed CLI tools may not be invokable by name.",
            evidence={
                "scripts_dir": scripts_dir,
                "path_contains_scripts_dir": False,
            },
            remediation=[
                "Add the scripts directory to PATH, or invoke tools via absolute path.",
                "Alternatively, use 'python -m <module>' invocation when available.",
            ],
            tags=["permissions"],
        )

    # 4) User site enabled
    enable_user_site = (py_info or {}).get("enable_user_site") if py_info else None
    if enable_user_site is False:
        add_finding(
            findings,
            fid="PIP.USER_SITE_DISABLED",
            severity="WARN",
            summary="Python user site-packages is disabled; pip may require admin/system write access for global installs.",
            evidence={"enable_user_site": enable_user_site},
            remediation=[
                "Avoid relying on --user installs; use an isolated env if permissions are restricted.",
                "If this is intentional, ensure your automation runs with appropriate permissions.",
            ],
            tags=["permissions"],
        )

    # 5) Reproducibility context: non-default indexes
    idx = parse_pip_indexes(pip_debug_res.stdout or "")
    if idx.get("extra_index_urls") or idx.get("trusted_hosts") or (idx.get("index_url") and "pypi.org" not in idx["index_url"]):
        add_finding(
            findings,
            fid="PIP.NONDEFAULT_INDEX",
            severity="INFO",
            summary="pip appears configured to use non-default index/trusted hosts; installs may differ across machines.",
            evidence=idx,
            remediation=[
                "Record pip config and index URLs in your build artifacts for traceability.",
                "If reproducibility is important, standardize pip config across environments.",
            ],
            tags=["reproducibility"],
        )

    # 6) Mixed env signals
    is_venv = bool((py_info or {}).get("is_venv")) if py_info else False
    is_conda = bool((py_info or {}).get("is_conda")) if py_info else False
    if is_venv and is_conda:
        add_finding(
            findings,
            fid="ENV.MIXED_CONDA_AND_VENV",
            severity="WARN",
            summary="Both venv and conda indicators detected; environment behavior may be inconsistent.",
            evidence={"is_venv": is_venv, "is_conda": is_conda, "conda_prefix": (py_info or {}).get("conda_prefix")},
            remediation=[
                "Prefer a single environment manager (conda OR venv).",
                "Pin python executable explicitly in automation.",
            ],
            tags=["collision", "permissions"],
        )

    # Meta & environment object
    host = {
        "os": "Windows",
        "platform": sys.platform,
        "arch": os.environ.get("PROCESSOR_ARCHITECTURE"),
    }

    pip_version = None
    if pip_version_res.exit_code == 0:
        pip_version = pip_version_res.stdout.strip()

    env_obj: Dict[str, Any] = {
        "python": {
            "primary_executable": python_exe,
            "probe": py_info,
            "where_python": python_candidates,
            "where_py": py_candidates,
        },
        "pip": {
            "version": pip_version,
            "indexes": idx,
            "config_list_tail": pip_config_res.stdout[-4000:],
        },
        "path": {
            "entries": os.environ.get("PATH", "").split(";"),
            "scripts_dir": scripts_dir,
            "scripts_dir_exists": scripts_exists,
            "scripts_dir_on_path": scripts_dir_on_path(str(scripts_dir)) if scripts_dir else False,
        },
    }

    any_error = any(f.get("severity") == "ERROR" for f in findings)

    report = {
        "meta": {
            "tool": "py-env-preflight",
            "version": "1.0.0",
            "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "host": host,
        },
        "environment": env_obj,
        "capabilities": {
            "pip_dry_run_supported": dry_run_supported,
        },
        "checks": checks,
        "findings": findings,
        "exit_code_policy": {
            "default": 0,
            "error_exit": 2,
            "nonzero_requires_flag": True,
        },
    }

    out_json = json.dumps(report, indent=2, sort_keys=False)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(out_json, encoding="utf-8")

    # JSON only
    sys.stdout.write(out_json)
    sys.stdout.write("\n")

    if args.exit_nonzero_on_error and any_error:
        return 2
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
```

**a.** Want this CLI to also emit a **normalized “risk score”** (0–100) in JSON for easy gating?  
**b.** Want it to accept your existing `tools_config.json` schema and produce a **“planned-install summary”** section (packages + verification types)?



---
Powered by [ChatGPT Exporter](https://www.chatgptexporter.com)