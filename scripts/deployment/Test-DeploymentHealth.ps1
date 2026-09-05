param(
    [int]$WaitSeconds = 0
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

. (Join-Path $PSScriptRoot "Common-DeploymentFunctions.ps1")

$projectRoot = Get-ProjectRoot
$settings = Get-DeploymentSettings -ProjectRoot $projectRoot

$deadline = (Get-Date).AddSeconds(
    [Math]::Max(0, $WaitSeconds)
)

do {
    $mysqlReady = Test-TcpEndpoint `
        -HostName ([string]$settings.MySQL.Host) `
        -Port ([int]$settings.MySQL.Port)

    $backendHealthy = Test-BackendHealth `
        -Url ([string]$settings.Backend.HealthUrl)

    $frontendHealthy = Test-FrontendHealth `
        -Url ([string]$settings.Frontend.HealthUrl)

    if (
        $mysqlReady -and
        $backendHealthy -and
        $frontendHealthy
    ) {
        break
    }

    if ((Get-Date) -ge $deadline) {
        break
    }

    Start-Sleep -Seconds 2
}
while ($true)

Write-Host ""
Write-Host "DEPLOYMENT HEALTH CHECK"
Write-Host "======================="

Write-Host ("[{0}] MySQL   {1}:{2}" -f `
    $(if ($mysqlReady) { "PASS" } else { "FAIL" }), `
    $settings.MySQL.Host, `
    $settings.MySQL.Port
)

Write-Host ("[{0}] Backend {1}" -f `
    $(if ($backendHealthy) { "PASS" } else { "FAIL" }), `
    $settings.Backend.HealthUrl
)

Write-Host ("[{0}] Frontend {1}" -f `
    $(if ($frontendHealthy) { "PASS" } else { "FAIL" }), `
    $settings.Frontend.HealthUrl
)

if (
    -not $mysqlReady -or
    -not $backendHealthy -or
    -not $frontendHealthy
) {
    exit 1
}

Write-Host ""
Write-Host "APPLICATION HEALTHY"
