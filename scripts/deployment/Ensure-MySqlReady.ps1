param()

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

. (Join-Path $PSScriptRoot "Common-DeploymentFunctions.ps1")

$projectRoot = Get-ProjectRoot
$settings = Get-DeploymentSettings -ProjectRoot $projectRoot

$hostName = [string]$settings.MySQL.Host
$port = [int]$settings.MySQL.Port
$timeout = [int]$settings.MySQL.StartupTimeoutSeconds

if (Test-TcpEndpoint -HostName $hostName -Port $port) {
    Write-Host "MySQL is already reachable at ${hostName}:$port."
    exit 0
}

$isLocalHost = $hostName -in @(
    "127.0.0.1",
    "localhost",
    "::1"
)

if (-not $isLocalHost) {
    throw "Remote MySQL is not reachable at ${hostName}:$port. This script will not attempt to start a remote database."
}

$serviceName = [string]$settings.MySQL.ServiceName
$service = $null

if (-not [string]::IsNullOrWhiteSpace($serviceName)) {
    $service = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
}

if (-not $service) {
    $service = Get-Service -ErrorAction SilentlyContinue |
        Where-Object {
            $_.Name -match "^(mysql|mysql\d+|mariadb)$" -or
            $_.DisplayName -match "^(MySQL|MariaDB)"
        } |
        Select-Object -First 1
}

if ($service) {
    if ($service.Status -ne "Running") {
        Write-Host "Starting MySQL service: $($service.Name)"
        Start-Service -Name $service.Name
    }
}
else {
    $mysqld = [string]$settings.MySQL.XamppMysqld
    $myIni = [string]$settings.MySQL.XamppMyIni

    if (
        (Test-Path $mysqld) -and
        (Test-Path $myIni)
    ) {
        $running = Get-Process -Name "mysqld" -ErrorAction SilentlyContinue |
            Select-Object -First 1

        if (-not $running) {
            Write-Host "No MySQL Windows service found."
            Write-Host "Starting XAMPP MySQL directly..."

            Start-Process `
                -FilePath $mysqld `
                -ArgumentList "--defaults-file=`"$myIni`"" `
                -WindowStyle Hidden | Out-Null
        }
    }
    else {
        throw "MySQL is offline and no Windows service or XAMPP mysqld configuration was found."
    }
}

$deadline = (Get-Date).AddSeconds($timeout)

while ((Get-Date) -lt $deadline) {
    if (Test-TcpEndpoint -HostName $hostName -Port $port) {
        Write-Host "MySQL is ready at ${hostName}:$port."
        exit 0
    }

    Start-Sleep -Seconds 2
}

throw "MySQL did not become ready within $timeout seconds."
