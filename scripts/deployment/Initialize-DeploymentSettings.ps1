param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

. (Join-Path $PSScriptRoot "Common-DeploymentFunctions.ps1")

$projectRoot = Get-ProjectRoot
$localPath = Join-Path $PSScriptRoot "deployment-settings.local.json"
$examplePath = Join-Path $PSScriptRoot "deployment-settings.example.json"

if ((Test-Path $localPath) -and -not $Force) {
    Write-Host "Local deployment settings already exist:"
    Write-Host $localPath
    exit 0
}

if (-not (Test-Path $examplePath)) {
    throw "Missing deployment settings template: $examplePath"
}

Copy-Item $examplePath $localPath -Force

$settings = Get-Content $localPath -Raw | ConvertFrom-Json

$service = Get-Service -ErrorAction SilentlyContinue |
    Where-Object {
        $_.Name -match "^(mysql|mysql\d+|mariadb)$" -or
        $_.DisplayName -match "^(MySQL|MariaDB)"
    } |
    Select-Object -First 1

if ($service) {
    $settings.MySQL.ServiceName = $service.Name
}

$settings |
    ConvertTo-Json -Depth 6 |
    Set-Content -Path $localPath -Encoding UTF8

Write-Host ""
Write-Host "DEPLOYMENT SETTINGS INITIALIZED"
Write-Host "==============================="
Write-Host "File         : $localPath"
Write-Host "Backend      : $($settings.Backend.HealthUrl)"
Write-Host "Frontend     : $($settings.Frontend.HealthUrl)"
Write-Host "MySQL        : $($settings.MySQL.Host):$($settings.MySQL.Port)"
Write-Host "MySQL service: $($settings.MySQL.ServiceName)"
Write-Host ""
Write-Host "This local settings file is ignored by Git."
