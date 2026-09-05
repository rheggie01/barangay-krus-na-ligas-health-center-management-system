param(
    [switch]$KeepApplicationRunning
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

. (Join-Path $PSScriptRoot "Common-DeploymentFunctions.ps1")

if (-not (Test-IsAdministrator)) {
    throw "Run PowerShell as Administrator before uninstalling the startup task."
}

$taskName = "Health Center Application Auto-Start"
$taskPath = "\BarangayHealthSystem\"

if (-not $KeepApplicationRunning) {
    & (Join-Path $PSScriptRoot "Stop-ProductionStack.ps1")
}

Stop-ScheduledTask `
    -TaskName $taskName `
    -TaskPath $taskPath `
    -ErrorAction SilentlyContinue

Unregister-ScheduledTask `
    -TaskName $taskName `
    -TaskPath $taskPath `
    -Confirm:$false `
    -ErrorAction SilentlyContinue

Write-Host "Application auto-start task removed."
