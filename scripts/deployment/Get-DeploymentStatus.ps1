param()

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

. (Join-Path $PSScriptRoot "Common-DeploymentFunctions.ps1")

$projectRoot = Get-ProjectRoot
$settings = Get-DeploymentSettings -ProjectRoot $projectRoot
$runtime = Get-DeploymentRuntime -ProjectRoot $projectRoot

$status = Read-DeploymentStatus -Path $runtime.StatusFile

$taskName = "Health Center Application Auto-Start"
$taskPath = "\BarangayHealthSystem\"

$task = Get-ScheduledTask `
    -TaskName $taskName `
    -TaskPath $taskPath `
    -ErrorAction SilentlyContinue

$taskInfo = $null

if ($task) {
    $taskInfo = Get-ScheduledTaskInfo `
        -TaskName $taskName `
        -TaskPath $taskPath `
        -ErrorAction SilentlyContinue
}

$mysqlReady = Test-TcpEndpoint `
    -HostName ([string]$settings.MySQL.Host) `
    -Port ([int]$settings.MySQL.Port)

$backendHealthy = Test-BackendHealth `
    -Url ([string]$settings.Backend.HealthUrl)

$frontendHealthy = Test-FrontendHealth `
    -Url ([string]$settings.Frontend.HealthUrl)

Write-Host ""
Write-Host "APPLICATION DEPLOYMENT STATUS"
Write-Host "============================="
Write-Host "MySQL          : $(if ($mysqlReady) { 'READY' } else { 'DOWN' })"
Write-Host "Backend        : $(if ($backendHealthy) { 'HEALTHY' } else { 'DOWN' })"
Write-Host "Frontend       : $(if ($frontendHealthy) { 'HEALTHY' } else { 'DOWN' })"
Write-Host "Startup task   : $(if ($task) { $task.State } else { 'NOT INSTALLED' })"

if ($taskInfo) {
    Write-Host "Last task run  : $($taskInfo.LastRunTime)"
}

if ($status) {
    $monitorPid = Get-OptionalPropertyValue `
        -Object $status `
        -Name "monitor_pid"

    $backendPid = Get-OptionalPropertyValue `
        -Object $status.backend `
        -Name "pid"

    $backendRoot = Get-OptionalPropertyValue `
        -Object $status.backend `
        -Name "root_pid" `
        -Default $backendPid

    $backendOwned = Get-OptionalPropertyValue `
        -Object $status.backend `
        -Name "owned" `
        -Default $false

    $frontendPid = Get-OptionalPropertyValue `
        -Object $status.frontend `
        -Name "pid"

    $frontendRoot = Get-OptionalPropertyValue `
        -Object $status.frontend `
        -Name "root_pid" `
        -Default $frontendPid

    $frontendOwned = Get-OptionalPropertyValue `
        -Object $status.frontend `
        -Name "owned" `
        -Default $false

    $checkedAt = Get-OptionalPropertyValue `
        -Object $status `
        -Name "checked_at"

    $runtimeState = Get-OptionalPropertyValue `
        -Object $status `
        -Name "state"

    Write-Host "Monitor PID    : $monitorPid"
    Write-Host "Backend root   : $backendRoot"
    Write-Host "Backend PID    : $backendPid"
    Write-Host "Backend owned  : $backendOwned"
    Write-Host "Frontend root  : $frontendRoot"
    Write-Host "Frontend PID   : $frontendPid"
    Write-Host "Frontend owned : $frontendOwned"
    Write-Host "Last checked   : $checkedAt"
    Write-Host "Runtime state  : $runtimeState"
}

Write-Host ""
Write-Host "Runtime folder : $($runtime.Root)"
