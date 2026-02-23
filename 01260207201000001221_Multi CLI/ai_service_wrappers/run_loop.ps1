# Plan-Evaluate Loop Orchestrator (PowerShell version)
# FIXED: Proper argument passing to Python inline script, added auth preflight, added convergence tracking
# ENHANCED: Added retry/backoff for transient failures
param(
    [Parameter(Mandatory=$true)]
    [string]$RequestPath,
    
    [int]$MaxAttempts = 3,
    
    [string]$Model = "",
    
    [int]$MaxTransientRetries = 3,
    
    [int]$BackoffBaseSeconds = 2,
    
    [int]$BackoffMaxSeconds = 60,
    
    [int[]]$RetryableExitCodes = @(124, 408, 429)
)

$ErrorActionPreference = "Stop"

# Invoke-WithRetry: Execute command with exponential backoff on transient failures
function Invoke-WithRetry {
    param(
        [Parameter(Mandatory=$true)]
        [ScriptBlock]$Command,
        
        [Parameter(Mandatory=$true)]
        [string]$ToolName,
        
        [Parameter(Mandatory=$true)]
        [string]$RunId,
        
        [int]$MaxRetries = $MaxTransientRetries,
        
        [int[]]$RetryableCodes = $RetryableExitCodes
    )
    
    $attempt = 0
    $lastExitCode = 0
    
    while ($attempt -le $MaxRetries) {
        if ($attempt -gt 0) {
            # Calculate deterministic backoff with jitter
            $backoffSeconds = [Math]::Min(
                [Math]::Pow(2, $attempt - 1) * $BackoffBaseSeconds,
                $BackoffMaxSeconds
            )
            
            # Deterministic jitter: seed from run_id + tool_name + attempt
            $seed = ($RunId + $ToolName + $attempt).GetHashCode()
            $random = New-Object System.Random($seed)
            $jitter = $random.NextDouble() * 0.3 * $backoffSeconds  # 0-30% jitter
            $sleepSeconds = [Math]::Ceiling($backoffSeconds + $jitter)
            
            Write-Host "  Retry $attempt/$MaxRetries after ${sleepSeconds}s (backoff + jitter)..." -ForegroundColor Yellow
            Start-Sleep -Seconds $sleepSeconds
        }
        
        $attempt++
        
        # Execute command
        & $Command
        $lastExitCode = $LASTEXITCODE
        
        # Check if retry warranted
        if ($lastExitCode -eq 0) {
            return @{
                ExitCode = $lastExitCode
                Attempt = $attempt
                Success = $true
            }
        }
        
        $isRetryable = $RetryableCodes -contains $lastExitCode
        
        if (-not $isRetryable) {
            Write-Host "  Exit code $lastExitCode is non-retryable" -ForegroundColor Red
            return @{
                ExitCode = $lastExitCode
                Attempt = $attempt
                Success = $false
            }
        }
        
        if ($attempt -gt $MaxRetries) {
            Write-Host "  Max retries exhausted" -ForegroundColor Red
            return @{
                ExitCode = $lastExitCode
                Attempt = $attempt
                Success = $false
            }
        }
    }
    
    return @{
        ExitCode = $lastExitCode
        Attempt = $attempt
        Success = $false
    }
}

# Generate run ID
$RunId = "RUN_$(Get-Date -Format 'yyyyMMddTHHmmss')_$([System.Guid]::NewGuid().ToString().Substring(0,8))"
$StartTime = Get-Date

$BaseDir = $PSScriptRoot
$SchemaDir = Join-Path $BaseDir "..\schemas_langgraph"
$ArtifactsBase = Join-Path $BaseDir "..\.state\evidence\plan_loop_runs\$RunId"

# Initialize tool call manifest
$ToolCallManifest = @()

Write-Host "=== Plan-Evaluate Loop ===" -ForegroundColor Cyan
Write-Host "Run ID: $RunId" -ForegroundColor Yellow
Write-Host "Request: $RequestPath" -ForegroundColor Yellow
Write-Host "Max attempts: $MaxAttempts" -ForegroundColor Yellow

# Auth preflight
Write-Host "`n=== Auth Preflight ===" -ForegroundColor Cyan
$authOk = $true

if (-not $env:CODEX_API_KEY) {
    Write-Host "ERROR: CODEX_API_KEY not set" -ForegroundColor Red
    $authOk = $false
}

if (-not ($env:GH_TOKEN -or $env:GITHUB_TOKEN)) {
    Write-Host "ERROR: GH_TOKEN or GITHUB_TOKEN not set" -ForegroundColor Red
    $authOk = $false
}

if (-not $authOk) {
    Write-Host "`nSet environment variables:" -ForegroundColor Yellow
    Write-Host '  $env:CODEX_API_KEY = "sk-..."' -ForegroundColor Gray
    Write-Host '  $env:GH_TOKEN = "ghp_..."' -ForegroundColor Gray
    exit 1
}

Write-Host "✓ Auth credentials found" -ForegroundColor Green

# Create run directory
New-Item -ItemType Directory -Path $ArtifactsBase -Force | Out-Null

$PlanPath = ""
$Converged = $false
$LastFailure = $null
$TotalRetries = 0

for ($i = 1; $i -le $MaxAttempts; $i++) {
    $IterDir = Join-Path $ArtifactsBase $i.ToString()
    $LogsDir = Join-Path $IterDir "logs"
    $EvidenceDir = Join-Path $IterDir "evidence"
    New-Item -ItemType Directory -Path $LogsDir -Force | Out-Null
    New-Item -ItemType Directory -Path $EvidenceDir -Force | Out-Null

    Write-Host "`n=== Iteration $i/$MaxAttempts ===" -ForegroundColor Cyan

    # Phase 1: Planner (first iteration only)
    if ($i -eq 1) {
        Write-Host "Phase: Planner" -ForegroundColor Yellow
        $PlanPath = Join-Path $IterDir "draft_plan.json"
        
        $plannerArgs = @(
            "--request", $RequestPath,
            "--schema", (Join-Path $SchemaDir "draft_plan.schema.json"),
            "--out-plan", $PlanPath,
            "--out-envelope", (Join-Path $IterDir "planner_envelope.json"),
            "--log-stdout", (Join-Path $LogsDir "planner.stdout.log"),
            "--log-stderr", (Join-Path $LogsDir "planner.stderr.log"),
            "--run-id", $RunId
        )
        
        if ($Model) { $plannerArgs += @("--model", $Model) }
        
        $plannerStart = Get-Date
        $plannerResult = Invoke-WithRetry `
            -Command { python (Join-Path $BaseDir "planner.py") @plannerArgs } `
            -ToolName "planner" `
            -RunId $RunId `
            -MaxRetries $MaxTransientRetries `
            -RetryableCodes $RetryableExitCodes
        $plannerEnd = Get-Date
        
        # Log tool call
        $TotalRetries += ($plannerResult.Attempt - 1)
        $ToolCallManifest += @{
            tool_name = "planner"
            command = "python"
            args = $plannerArgs -join " "
            start_time = $plannerStart.ToString("o")
            end_time = $plannerEnd.ToString("o")
            exit_code = $plannerResult.ExitCode
            stdout_log = (Join-Path $LogsDir "planner.stdout.log")
            stderr_log = (Join-Path $LogsDir "planner.stderr.log")
            retry_count = ($plannerResult.Attempt - 1)
        }
        
        if (-not $plannerResult.Success) {
            Write-Host "Planner failed with exit code $($plannerResult.ExitCode)" -ForegroundColor Red
            $LastFailure = @{
                phase = "planner"
                message = "Planner failed after $($plannerResult.Attempt) attempts"
                exit_code = $plannerResult.ExitCode
            }
            break
        }
    }

    # Phase 2: Quality Gate
    Write-Host "Phase: Quality Gate" -ForegroundColor Yellow
    $GateReportPath = Join-Path $IterDir "gate_report.json"
    $PlanEnvelopePath = Join-Path $IterDir "planner_envelope.json"
    $GateEnvelopePath = Join-Path $IterDir "gate_envelope.json"
    
    $gateStart = Get-Date
    python (Join-Path $BaseDir "plan_quality_gate.py") `
        --plan $PlanPath `
        --plan-envelope $PlanEnvelopePath `
        --schema (Join-Path $SchemaDir "draft_plan.schema.json") `
        --out $GateReportPath `
        --out-envelope $GateEnvelopePath `
        --run-id $RunId `
        --evidence-dir $EvidenceDir
    $gateEnd = Get-Date
    $gateExitCode = $LASTEXITCODE
    
    # Log tool call
    $ToolCallManifest += @{
        tool_name = "quality_gate"
        command = "python"
        start_time = $gateStart.ToString("o")
        end_time = $gateEnd.ToString("o")
        exit_code = $gateExitCode
        retry_count = 0
    }
    
    $gateReport = Get-Content $GateReportPath | ConvertFrom-Json
    
    Write-Host "Gate: $($gateReport.summary)" -ForegroundColor $(if ($gateReport.passed) { "Green" } else { "Yellow" })

    # Phase 3: Critic (only if gate passed)
    if ($gateReport.passed) {
        Write-Host "Phase: Critic" -ForegroundColor Yellow
        $CritiqueReportPath = Join-Path $IterDir "critique_report.json"
        $CriticEnvelopePath = Join-Path $IterDir "critic_envelope.json"
        
        $criticStart = Get-Date
        $criticResult = Invoke-WithRetry `
            -Command {
                python (Join-Path $BaseDir "critic.py") `
                    --plan $PlanPath `
                    --plan-envelope $PlanEnvelopePath `
                    --schema (Join-Path $SchemaDir "critique_report.schema.json") `
                    --out $CritiqueReportPath `
                    --out-envelope $CriticEnvelopePath `
                    --run-id $RunId `
                    --evidence-dir $EvidenceDir `
                    --log-stdout (Join-Path $LogsDir "critic.stdout.log") `
                    --log-stderr (Join-Path $LogsDir "critic.stderr.log")
            } `
            -ToolName "critic" `
            -RunId $RunId `
            -MaxRetries $MaxTransientRetries `
            -RetryableCodes $RetryableExitCodes
        $criticEnd = Get-Date
        
        # Log tool call
        $TotalRetries += ($criticResult.Attempt - 1)
        $ToolCallManifest += @{
            tool_name = "critic"
            command = "python"
            start_time = $criticStart.ToString("o")
            end_time = $criticEnd.ToString("o")
            exit_code = $criticResult.ExitCode
            stdout_log = (Join-Path $LogsDir "critic.stdout.log")
            stderr_log = (Join-Path $LogsDir "critic.stderr.log")
            retry_count = ($criticResult.Attempt - 1)
        }

        if ($criticResult.Success) {
            $critique = Get-Content $CritiqueReportPath | ConvertFrom-Json
            Write-Host "Critic verdict: $($critique.verdict)" -ForegroundColor $(if ($critique.verdict -eq "pass") { "Green" } else { "Yellow" })
            
            # Check convergence
            if ($critique.verdict -eq "pass") {
                $Converged = $true
                Write-Host "`n✓ CONVERGED at iteration $i" -ForegroundColor Green
                break
            }
        } else {
            $LastFailure = @{
                phase = "critic"
                message = "Critic failed after $($criticResult.Attempt) attempts"
                exit_code = $criticResult.ExitCode
            }
        }
    }

    # Phase 4: Refiner (if not converged and not last iteration)
    if ($i -lt $MaxAttempts) {
        Write-Host "Phase: Refiner" -ForegroundColor Yellow
        $NextIterDir = Join-Path $ArtifactsBase ($i + 1).ToString()
        $NextLogsDir = Join-Path $NextIterDir "logs"
        $NextEvidenceDir = Join-Path $NextIterDir "evidence"
        New-Item -ItemType Directory -Path $NextLogsDir -Force | Out-Null
        New-Item -ItemType Directory -Path $NextEvidenceDir -Force | Out-Null
        
        $NextPlanPath = Join-Path $NextIterDir "draft_plan.json"
        $RefinerEnvelopePath = Join-Path $NextIterDir "planner_envelope.json"  # Refiner outputs a plan
        
        $refinerStart = Get-Date
        $refinerResult = Invoke-WithRetry `
            -Command {
                python (Join-Path $BaseDir "refiner.py") `
                    --plan $PlanPath `
                    --plan-envelope $PlanEnvelopePath `
                    --gate $GateReportPath `
                    --gate-envelope $GateEnvelopePath `
                    --critique $(if (Test-Path $CritiqueReportPath) { $CritiqueReportPath } else { $GateReportPath }) `
                    --critique-envelope $(if (Test-Path $CriticEnvelopePath) { $CriticEnvelopePath } else { $GateEnvelopePath }) `
                    --schema (Join-Path $SchemaDir "draft_plan.schema.json") `
                    --out-plan $NextPlanPath `
                    --out-envelope $RefinerEnvelopePath `
                    --run-id $RunId `
                    --evidence-dir $NextEvidenceDir `
                    --log-stdout (Join-Path $NextLogsDir "refiner.stdout.log") `
                    --log-stderr (Join-Path $NextLogsDir "refiner.stderr.log")
            } `
            -ToolName "refiner" `
            -RunId $RunId `
            -MaxRetries $MaxTransientRetries `
            -RetryableCodes $RetryableExitCodes
        $refinerEnd = Get-Date
        
        # Log tool call
        $TotalRetries += ($refinerResult.Attempt - 1)
        $ToolCallManifest += @{
            tool_name = "refiner"
            command = "python"
            start_time = $refinerStart.ToString("o")
            end_time = $refinerEnd.ToString("o")
            exit_code = $refinerResult.ExitCode
            stdout_log = (Join-Path $NextLogsDir "refiner.stdout.log")
            stderr_log = (Join-Path $NextLogsDir "refiner.stderr.log")
            retry_count = ($refinerResult.Attempt - 1)
        }

        if (-not $refinerResult.Success) {
            Write-Host "Refiner failed with exit code $($refinerResult.ExitCode)" -ForegroundColor Red
            $LastFailure = @{
                phase = "refiner"
                message = "Refiner failed after $($refinerResult.Attempt) attempts"
                exit_code = $refinerResult.ExitCode
            }
            break
        }
        
        $PlanPath = $NextPlanPath
    }
}

# Final summary
Write-Host "`n=== Summary ===" -ForegroundColor Cyan

$EndTime = Get-Date
$FinalExitCode = 0
$Status = "CONVERGED"

if ($Converged) {
    Write-Host "Status: CONVERGED" -ForegroundColor Green
    Write-Host "Final plan: $PlanPath" -ForegroundColor Green
    $FinalExitCode = 0
    $Status = "CONVERGED"
} elseif ($LastFailure) {
    Write-Host "Status: ERROR - $($LastFailure.phase) failed" -ForegroundColor Red
    Write-Host "Artifacts: $ArtifactsBase" -ForegroundColor Yellow
    $FinalExitCode = $LastFailure.exit_code
    $Status = "ERROR"
} else {
    Write-Host "Status: FAILED TO CONVERGE after $MaxAttempts attempts" -ForegroundColor Red
    Write-Host "Artifacts: $ArtifactsBase" -ForegroundColor Yellow
    $FinalExitCode = 2
    $Status = "FAILED_TO_CONVERGE"
}

# Write run summary
$RunSummary = @{
    schema_id = "acms.run_summary.v1"
    schema_version = "1.0.0"
    run_id = $RunId
    status = $Status
    started_at = $StartTime.ToString("o")
    completed_at = $EndTime.ToString("o")
    iterations = $i
    final_plan_path = $PlanPath
    exit_code = $FinalExitCode
    retry_statistics = @{
        total_retries = $TotalRetries
        retries_by_phase = @{}
    }
    telemetry = @{
        usage_status = "UNAVAILABLE"
        total_tokens = 0
        total_cost_usd = 0.0
        by_tool = @()
    }
}

if ($LastFailure) {
    $RunSummary.last_failure = $LastFailure
}

$RunSummaryPath = Join-Path $ArtifactsBase "run_summary.json"
$RunSummary | ConvertTo-Json -Depth 10 | Set-Content $RunSummaryPath

# Write tool call manifest
$ToolCallManifestPath = Join-Path $ArtifactsBase "tool_call_manifest.jsonl"
foreach ($call in $ToolCallManifest) {
    $call | ConvertTo-Json -Compress | Add-Content $ToolCallManifestPath
}

Write-Host "Run summary: $RunSummaryPath" -ForegroundColor Cyan
Write-Host "Tool manifest: $ToolCallManifestPath" -ForegroundColor Cyan

exit $FinalExitCode
