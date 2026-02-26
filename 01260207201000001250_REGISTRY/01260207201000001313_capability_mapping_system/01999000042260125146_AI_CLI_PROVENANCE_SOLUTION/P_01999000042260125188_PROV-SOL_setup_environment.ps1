#!/usr/bin/env pwsh
# DOC_ID: DOC-SCRIPT-1024
<#
.SYNOPSIS
    Setup script for AI CLI Provenance Solution
.DESCRIPTION
    Automates virtual environment creation, dependency installation, and validation
.EXAMPLE
    .\setup_environment.ps1
.EXAMPLE
    .\setup_environment.ps1 -SkipTests
#>

param(
    [switch]$SkipTests = $false,
    [switch]$Verbose = $false
)

# ============================================================================
# CONFIGURATION
# ============================================================================

$ErrorActionPreference = "Stop"
$SOLUTION_ROOT = $PSScriptRoot
$VENV_PATH = Join-Path $SOLUTION_ROOT ".venv"
$REQUIREMENTS_FILE = Join-Path $SOLUTION_ROOT "requirements.txt"
$SCHEMA_FILE = Join-Path $SOLUTION_ROOT "EVIDENCE_SCHEMA_EXTENDED.yaml"

# ============================================================================
# FUNCTIONS
# ============================================================================

function Write-Header {
    param([string]$Message)
    Write-Host ""
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-Host $Message -ForegroundColor Cyan
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-Host ""
}

function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Error {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ️  $Message" -ForegroundColor Blue
}

function Test-PythonVersion {
    Write-Info "Checking Python version..."

    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Python not found. Please install Python 3.8+"
        exit 1
    }

    Write-Success "Found Python: $pythonVersion"

    # Check if Python 3.8+
    if ($pythonVersion -match "Python (\d+)\.(\d+)") {
        $major = [int]$Matches[1]
        $minor = [int]$Matches[2]

        if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 8)) {
            Write-Error "Python 3.8+ required. Found: $pythonVersion"
            exit 1
        }
    }
}

function Create-VirtualEnvironment {
    Write-Info "Creating virtual environment..."

    if (Test-Path $VENV_PATH) {
        Write-Info "Virtual environment already exists at: $VENV_PATH"
        $response = Read-Host "Recreate? (y/N)"
        if ($response -eq 'y' -or $response -eq 'Y') {
            Remove-Item -Path $VENV_PATH -Recurse -Force
            Write-Info "Removed existing virtual environment"
        } else {
            Write-Info "Using existing virtual environment"
            return
        }
    }

    python -m venv $VENV_PATH

    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to create virtual environment"
        exit 1
    }

    Write-Success "Virtual environment created: $VENV_PATH"
}

function Activate-VirtualEnvironment {
    Write-Info "Activating virtual environment..."

    $activateScript = Join-Path $VENV_PATH "Scripts\Activate.ps1"

    if (-not (Test-Path $activateScript)) {
        Write-Error "Activate script not found: $activateScript"
        exit 1
    }

    # Run activation script in current scope
    & $activateScript

    Write-Success "Virtual environment activated"
}

function Install-Dependencies {
    Write-Info "Installing dependencies from: $REQUIREMENTS_FILE"

    if (-not (Test-Path $REQUIREMENTS_FILE)) {
        Write-Error "Requirements file not found: $REQUIREMENTS_FILE"
        exit 1
    }

    python -m pip install --upgrade pip
    python -m pip install -r $REQUIREMENTS_FILE

    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to install dependencies"
        exit 1
    }

    Write-Success "Dependencies installed successfully"
}

function Test-Installation {
    Write-Info "Verifying installation..."

    # Test PyYAML
    $yamlTest = python -c "import yaml; print('PyYAML OK')" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "PyYAML: $yamlTest"
    } else {
        Write-Error "PyYAML import failed"
        exit 1
    }

    # Test pytest
    $pytestVersion = pytest --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "pytest: $pytestVersion"
    } else {
        Write-Error "pytest not found"
        exit 1
    }

    # Test pytest-cov
    $covVersion = python -c "import pytest_cov; print('pytest-cov OK')" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "pytest-cov: $covVersion"
    } else {
        Write-Error "pytest-cov not found"
        exit 1
    }
}

function Validate-Schema {
    Write-Info "Validating evidence schema..."

    if (-not (Test-Path $SCHEMA_FILE)) {
        Write-Error "Schema file not found: $SCHEMA_FILE"
        exit 1
    }

    $validatorScript = Join-Path $SOLUTION_ROOT "validate_evidence_schema.py"

    if (-not (Test-Path $validatorScript)) {
        Write-Info "Schema validator not found, skipping validation"
        return
    }

    python $validatorScript --schema $SCHEMA_FILE

    if ($LASTEXITCODE -eq 0) {
        Write-Success "Evidence schema is valid"
    } else {
        Write-Error "Evidence schema validation failed"
        exit 1
    }
}

function Run-Tests {
    Write-Info "Running tests..."

    $testsPath = Join-Path $SOLUTION_ROOT "tests"

    if (-not (Test-Path $testsPath)) {
        Write-Info "Tests directory not found, skipping tests"
        return
    }

    pytest $testsPath -v

    if ($LASTEXITCODE -eq 0) {
        Write-Success "All tests passed"
    } else {
        Write-Error "Some tests failed"
        # Don't exit - tests may not be fully implemented yet
    }
}

function Show-NextSteps {
    Write-Header "Setup Complete!"

    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "1. Activate the virtual environment:" -ForegroundColor White
    Write-Host "   .venv\Scripts\Activate.ps1" -ForegroundColor Gray
    Write-Host ""
    Write-Host "2. Validate the evidence schema:" -ForegroundColor White
    Write-Host "   python validate_evidence_schema.py --verbose" -ForegroundColor Gray
    Write-Host ""
    Write-Host "3. Run tests (once implemented):" -ForegroundColor White
    Write-Host "   pytest tests/ -v --cov" -ForegroundColor Gray
    Write-Host ""
    Write-Host "4. Start Phase 2 implementation:" -ForegroundColor White
    Write-Host "   - Create ai_cli_provenance_collector.py" -ForegroundColor Gray
    Write-Host "   - Implement parsers for Claude/Codex/Copilot" -ForegroundColor Gray
    Write-Host "   - Build SQLite index" -ForegroundColor Gray
    Write-Host ""
}

# ============================================================================
# MAIN
# ============================================================================

try {
    Write-Header "AI CLI Provenance Solution - Environment Setup"

    # Step 1: Check Python
    Test-PythonVersion

    # Step 2: Create virtual environment
    Create-VirtualEnvironment

    # Step 3: Activate virtual environment
    Activate-VirtualEnvironment

    # Step 4: Install dependencies
    Install-Dependencies

    # Step 5: Verify installation
    Test-Installation

    # Step 6: Validate schema
    Validate-Schema

    # Step 7: Run tests (optional)
    if (-not $SkipTests) {
        Run-Tests
    }

    # Step 8: Show next steps
    Show-NextSteps

} catch {
    Write-Error "Setup failed: $_"
    exit 1
}
