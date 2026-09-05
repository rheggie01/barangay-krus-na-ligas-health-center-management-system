param()

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

. (Join-Path $PSScriptRoot "Common-DeploymentFunctions.ps1")

if (-not (Test-IsAdministrator)) {
    throw "Run PowerShell as Administrator to restart the managed application task."
}

$taskName = "Health Center Application Auto-Start"
$taskPath = "\BarangayHealthSystem\"

$task = Get-ScheduledTask `
    -TaskName $taskName `
    -TaskPath $taskPath `
    -ErrorAction Stop

& (Join-Path $PSScriptRoot "Stop-ProductionStack.ps1")

Stop-ScheduledTask `
    -TaskName $taskName `
    -TaskPath $taskPath `
    -ErrorAction SilentlyContinue

Start-Sleep -Seconds 2

Start-ScheduledTask `
    -TaskName $taskName `
    -TaskPath $taskPath

& (Join-Path $PSScriptRoot "Test-DeploymentHealth.ps1") -WaitSeconds 90

if ($LASTEXITCODE -ne 0) {
    throw "Application restart health verification failed."
}

Write-Host ""
Write-Host "APPLICATION RESTART VERIFIED"
