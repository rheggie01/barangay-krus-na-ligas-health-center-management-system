param(
    [int]$WaitSeconds = 90
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

. (Join-Path $PSScriptRoot "Common-DeploymentFunctions.ps1")

$projectRoot = Get-ProjectRoot
$runtime = Get-DeploymentRuntime -ProjectRoot $projectRoot
$status = Read-DeploymentStatus -Path $runtime.StatusFile

if (-not $status) {
    throw "Deployment runtime status is unavailable. Start the automatic application task first."
}

if (-not $status.monitor_pid) {
    throw "The deployment monitor is not recorded as running."
}

if (-not (Test-ProcessId -ProcessId ([int]$status.monitor_pid))) {
    throw "The deployment monitor process is not running."
}

$backendRootPid = Get-OptionalPropertyValue `
    -Object $status.backend `
    -Name "root_pid"

$backendListenerPid = Get-OptionalPropertyValue `
    -Object $status.backend `
    -Name "pid"

$frontendRootPid = Get-OptionalPropertyValue `
    -Object $status.frontend `
    -Name "root_pid"

$frontendListenerPid = Get-OptionalPropertyValue `
    -Object $status.frontend `
    -Name "pid"

if (
    -not $backendRootPid -or
    -not $frontendRootPid
) {
    throw "The runtime status is still using the pre-12.3.1 schema. Run Restart-ProductionStack.ps1 once after applying this hotfix, wait for healthy status, then retry."
}

if (
    -not $backendRootPid -or
    -not $backendListenerPid -or
    -not $frontendRootPid -or
    -not $frontendListenerPid
) {
    throw "The monitor does not currently own both app process trees. Restart the managed task, wait for healthy status, then retry."
}

if (
    -not (
        Test-ProcessDescendantOf `
            -ProcessId ([int]$backendListenerPid) `
            -AncestorProcessId ([int]$backendRootPid)
    )
) {
    throw "Backend listener PID is not owned by the recorded managed backend process tree."
}

if (
    -not (
        Test-ProcessDescendantOf `
            -ProcessId ([int]$frontendListenerPid) `
            -AncestorProcessId ([int]$frontendRootPid)
    )
) {
    throw "Frontend listener PID is not owned by the recorded managed frontend process tree."
}

Write-Host ""
Write-Host "AUTO-RECOVERY SIMULATION"
Write-Host "========================"
Write-Host "This test stops ONLY the managed backend and frontend processes."
Write-Host "MySQL and the live database are not stopped."
Write-Host ""

Stop-ProcessTree `
    -RootProcessId ([int]$backendRootPid)

Stop-ProcessTree `
    -RootProcessId ([int]$frontendRootPid)

Write-Host "Managed app processes were stopped."
Write-Host "Waiting for the deployment monitor to restart them..."

& (Join-Path $PSScriptRoot "Test-DeploymentHealth.ps1") -WaitSeconds $WaitSeconds

if ($LASTEXITCODE -ne 0) {
    throw "Automatic process recovery test failed."
}

Write-Host ""
Write-Host "AUTO-RECOVERY TEST PASSED"
