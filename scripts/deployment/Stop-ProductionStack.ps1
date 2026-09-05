param()

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

. (Join-Path $PSScriptRoot "Common-DeploymentFunctions.ps1")

$projectRoot = Get-ProjectRoot
$runtime = Get-DeploymentRuntime -ProjectRoot $projectRoot

New-Item -ItemType File -Force -Path $runtime.StopFile | Out-Null

$status = Read-DeploymentStatus -Path $runtime.StatusFile

if ($status -and $status.monitor_pid) {
    $monitorPid = [int]$status.monitor_pid

    Write-Host "Requesting deployment monitor shutdown (PID $monitorPid)..."

    $deadline = (Get-Date).AddSeconds(15)

    while (
        (Get-Date) -lt $deadline -and
        (Test-ProcessId -ProcessId $monitorPid)
    ) {
        Start-Sleep -Seconds 1
    }
}

$status = Read-DeploymentStatus -Path $runtime.StatusFile

if ($status) {
    $backendRoot = Get-OptionalPropertyValue `
        -Object $status.backend `
        -Name "root_pid" `
        -Default (
            Get-OptionalPropertyValue `
                -Object $status.backend `
                -Name "pid"
        )

    $frontendRoot = Get-OptionalPropertyValue `
        -Object $status.frontend `
        -Name "root_pid" `
        -Default (
            Get-OptionalPropertyValue `
                -Object $status.frontend `
                -Name "pid"
        )

    foreach ($pidValue in @(
        $backendRoot,
        $frontendRoot
    )) {
        if ($pidValue) {
            Stop-ProcessTree `
                -RootProcessId ([int]$pidValue)
        }
    }
}

Write-Host "Application stack stop request completed."
Write-Host "MySQL is intentionally left running."
