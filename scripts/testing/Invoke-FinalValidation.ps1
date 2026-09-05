param(
    [switch]$IncludeDeploymentHealth
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = (Resolve-Path (Join-Path $scriptDir '..\..')).Path
$pythonExe = Join-Path $projectRoot 'backend\.venv\Scripts\python.exe'
$pytestPath = Join-Path $projectRoot 'backend\tests'
$qualityScript = Join-Path $projectRoot 'scripts\repo-quality-check.ps1'
$runtimeDir = Join-Path $projectRoot 'runtime\testing'

if (-not (Test-Path $pythonExe)) {
    throw "Backend virtualenv Python not found: $pythonExe"
}
if (-not (Test-Path $qualityScript)) {
    throw "Repository quality script not found: $qualityScript"
}

New-Item -ItemType Directory -Path $runtimeDir -Force | Out-Null
$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$reportPath = Join-Path $runtimeDir "final-validation-$timestamp.txt"

function Write-ReportLine {
    param([string]$Text = '')
    $Text | Tee-Object -FilePath $reportPath -Append
}

function Invoke-RecordedCommand {
    param(
        [string]$Title,
        [scriptblock]$Command
    )

    Write-ReportLine ''
    Write-ReportLine ('=' * 72)
    Write-ReportLine $Title
    Write-ReportLine ('=' * 72)

    $previousErrorActionPreference = $ErrorActionPreference
    $global:LASTEXITCODE = 0

    try {
        # Native tools such as Vite can write warnings to STDERR even when
        # they exit successfully. When STDERR is merged into this recording
        # pipeline, Windows PowerShell can surface those records as errors.
        # Keep recording them, but determine success from the actual command
        # exit code instead of treating warning output as validation failure.
        $ErrorActionPreference = 'Continue'

        & $Command 2>&1 | ForEach-Object {
            $_ | Tee-Object -FilePath $reportPath -Append
        }

        $commandExitCode = $LASTEXITCODE
        $ErrorActionPreference = $previousErrorActionPreference

        if ($commandExitCode -ne 0) {
            throw "$Title failed with exit code $commandExitCode"
        }

        Write-ReportLine "PASS: $Title"
    }
    catch {
        $ErrorActionPreference = $previousErrorActionPreference
        Write-ReportLine "FAIL: $Title"
        Write-ReportLine $_.Exception.Message
        throw
    }
    finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
}

Write-ReportLine 'Barangay Health System - Final Validation Evidence'
Write-ReportLine "Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz')"
Write-ReportLine "Project: $projectRoot"
Write-ReportLine 'Expected automated regression baseline: 161 tests'

Push-Location $projectRoot
try {
    Invoke-RecordedCommand -Title 'Git status before validation' -Command {
        git status --short
    }

    Invoke-RecordedCommand -Title 'Full backend regression suite' -Command {
        & $pythonExe -m pytest $pytestPath -q
    }

    Invoke-RecordedCommand -Title 'Repository quality check' -Command {
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $qualityScript
    }

    if ($IncludeDeploymentHealth) {
        $deploymentHealth = Join-Path $projectRoot 'scripts\deployment\Test-DeploymentHealth.ps1'
        if (-not (Test-Path $deploymentHealth)) {
            throw "Deployment health script not found: $deploymentHealth"
        }

        Invoke-RecordedCommand -Title 'Managed deployment health check' -Command {
            & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $deploymentHealth
        }
    }

    Write-ReportLine ''
    Write-ReportLine ('=' * 72)
    Write-ReportLine 'FINAL RESULT: PASS'
    Write-ReportLine 'All requested validation commands completed successfully.'
}
catch {
    Write-ReportLine ''
    Write-ReportLine ('=' * 72)
    Write-ReportLine 'FINAL RESULT: FAIL'
    Write-ReportLine 'Review the failing section above before release or defense evidence capture.'
    Write-Host "`nValidation report: $reportPath" -ForegroundColor Yellow
    exit 1
}
finally {
    Pop-Location
}

Write-Host "`nFINAL VALIDATION PASSED" -ForegroundColor Green
Write-Host "Evidence report: $reportPath"
