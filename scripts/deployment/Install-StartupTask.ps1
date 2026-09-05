param(
    [switch]$SkipFrontendBuild
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

. (Join-Path $PSScriptRoot "Common-DeploymentFunctions.ps1")

if (-not (Test-IsAdministrator)) {
    throw "Run PowerShell as Administrator before installing the startup task."
}

$projectRoot = Get-ProjectRoot
$localSettings = Join-Path $PSScriptRoot "deployment-settings.local.json"

if (-not (Test-Path $localSettings)) {
    & (Join-Path $PSScriptRoot "Initialize-DeploymentSettings.ps1")
}

$settings = Get-DeploymentSettings -ProjectRoot $projectRoot

if (-not $SkipFrontendBuild) {
    $frontendDir = Join-Path $projectRoot "frontend"
    $npm = Get-Command "npm.cmd" -ErrorAction SilentlyContinue

    if (-not $npm) {
        throw "npm.cmd was not found. Node.js/npm is required for the frontend production build."
    }

    Write-Host "Building frontend production assets..."

    Push-Location $frontendDir

    try {
        & $npm.Source run build

        if ($LASTEXITCODE -ne 0) {
            throw "Frontend production build failed."
        }
    }
    finally {
        Pop-Location
    }
}

& (Join-Path $PSScriptRoot "Ensure-MySqlReady.ps1")

$taskName = "Health Center Application Auto-Start"
$taskPath = "\BarangayHealthSystem\"
$startupScript = Join-Path $PSScriptRoot "Start-ProductionStack.ps1"

$taskService = New-Object -ComObject "Schedule.Service"
$taskService.Connect()
$rootFolder = $taskService.GetFolder("\")

try {
    $null = $rootFolder.GetFolder("BarangayHealthSystem")
}
catch {
    $null = $rootFolder.CreateFolder("BarangayHealthSystem")
}

$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument (
        "-NoProfile -ExecutionPolicy Bypass -File `"$startupScript`""
    )

$trigger = New-ScheduledTaskTrigger -AtStartup
$delaySeconds = [int]$settings.Task.StartupDelaySeconds
$trigger.Delay = "PT${delaySeconds}S"

$principal = New-ScheduledTaskPrincipal `
    -UserId "SYSTEM" `
    -LogonType ServiceAccount `
    -RunLevel Highest

$taskSettings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -RestartCount 999 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -MultipleInstances IgnoreNew

Register-ScheduledTask `
    -TaskName $taskName `
    -TaskPath $taskPath `
    -Action $action `
    -Trigger $trigger `
    -Principal $principal `
    -Settings $taskSettings `
    -Description "Starts and monitors the Barangay Krus na Ligas Health Center application after Windows startup." `
    -Force | Out-Null

Write-Host ""
Write-Host "APPLICATION STARTUP TASK INSTALLED"
Write-Host "=================================="
Write-Host "Task  : $taskPath$taskName"
Write-Host "User  : SYSTEM"
Write-Host "Delay : $delaySeconds seconds after Windows startup"
Write-Host ""

Start-ScheduledTask `
    -TaskName $taskName `
    -TaskPath $taskPath

Write-Host "Started the task now for verification."
Write-Host "Waiting for application health..."

& (Join-Path $PSScriptRoot "Test-DeploymentHealth.ps1") -WaitSeconds 90

if ($LASTEXITCODE -ne 0) {
    throw "Startup task was installed, but the application health test failed. Check runtime\deployment\logs."
}

Write-Host ""
Write-Host "AUTO-START INSTALLATION VERIFIED"
