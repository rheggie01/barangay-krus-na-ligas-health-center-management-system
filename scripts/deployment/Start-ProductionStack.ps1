param(
    [switch]$Once
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

. (Join-Path $PSScriptRoot "Common-DeploymentFunctions.ps1")

$projectRoot = Get-ProjectRoot
$settings = Get-DeploymentSettings -ProjectRoot $projectRoot
$runtime = Get-DeploymentRuntime -ProjectRoot $projectRoot

$backendDir = Join-Path $projectRoot "backend"
$frontendDir = Join-Path $projectRoot "frontend"
$frontendDist = Join-Path $frontendDir "dist"
$frontendIndex = Join-Path $frontendDist "index.html"

$python = Join-Path $backendDir ".venv\Scripts\python.exe"
$spaServer = Join-Path $PSScriptRoot "serve_spa.py"
$mysqlScript = Join-Path $PSScriptRoot "Ensure-MySqlReady.ps1"

if (-not (Test-Path $python)) {
    throw "Backend virtual environment Python not found: $python"
}

if (-not (Test-Path $spaServer)) {
    throw "SPA server script not found: $spaServer"
}

$previousStatus = Read-DeploymentStatus -Path $runtime.StatusFile

if (
    -not $Once -and
    $previousStatus -and
    $previousStatus.monitor_pid -and
    (Test-ProcessId -ProcessId ([int]$previousStatus.monitor_pid))
) {
    Write-Host "Deployment monitor is already running with PID $($previousStatus.monitor_pid)."
    exit 0
}

Remove-Item $runtime.StopFile -Force -ErrorAction SilentlyContinue

function Build-FrontendIfNeeded {
    $buildOnStart = [bool]$settings.Frontend.BuildOnStart

    if ((Test-Path $frontendIndex) -and -not $buildOnStart) {
        return
    }

    $npm = Get-Command "npm.cmd" -ErrorAction SilentlyContinue

    if (-not $npm) {
        throw "npm.cmd was not found. Build the frontend before installing automatic startup."
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

function Start-Backend {
    $outLog = New-DeploymentLogPath `
        -LogsFolder $runtime.Logs `
        -Component "backend" `
        -Stream "out"

    $errLog = New-DeploymentLogPath `
        -LogsFolder $runtime.Logs `
        -Component "backend" `
        -Stream "err"

    $arguments = @(
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        [string]$settings.Backend.Host,
        "--port",
        [string]$settings.Backend.Port
    )

    Write-Host "Starting backend..."

    return Start-Process `
        -FilePath $python `
        -ArgumentList $arguments `
        -WorkingDirectory $backendDir `
        -WindowStyle Hidden `
        -RedirectStandardOutput $outLog `
        -RedirectStandardError $errLog `
        -PassThru
}

function Start-Frontend {
    $outLog = New-DeploymentLogPath `
        -LogsFolder $runtime.Logs `
        -Component "frontend" `
        -Stream "out"

    $errLog = New-DeploymentLogPath `
        -LogsFolder $runtime.Logs `
        -Component "frontend" `
        -Stream "err"

    $arguments = @(
        "`"$spaServer`"",
        "--directory",
        "`"$frontendDist`"",
        "--host",
        [string]$settings.Frontend.Host,
        "--port",
        [string]$settings.Frontend.Port
    )

    Write-Host "Starting frontend production server..."

    return Start-Process `
        -FilePath $python `
        -ArgumentList $arguments `
        -WorkingDirectory $projectRoot `
        -WindowStyle Hidden `
        -RedirectStandardOutput $outLog `
        -RedirectStandardError $errLog `
        -PassThru
}

function Wait-BackendHealthy {
    $deadline = (Get-Date).AddSeconds(
        [int]$settings.Backend.StartupTimeoutSeconds
    )

    while ((Get-Date) -lt $deadline) {
        if (Test-BackendHealth -Url ([string]$settings.Backend.HealthUrl)) {
            return $true
        }

        Start-Sleep -Seconds 2
    }

    return $false
}

function Wait-FrontendHealthy {
    $deadline = (Get-Date).AddSeconds(
        [int]$settings.Frontend.StartupTimeoutSeconds
    )

    while ((Get-Date) -lt $deadline) {
        if (Test-FrontendHealth -Url ([string]$settings.Frontend.HealthUrl)) {
            return $true
        }

        Start-Sleep -Seconds 1
    }

    return $false
}

function Stop-KnownProcess {
    param(
        [Nullable[int]]$ProcessId
    )

    Stop-ProcessTree `
        -RootProcessId $ProcessId
}

function Save-Status {
    param(
        [bool]$MySqlReady,
        [bool]$BackendHealthy,
        [bool]$FrontendHealthy,
        [Nullable[int]]$BackendRootPid,
        [Nullable[int]]$BackendListenerPid,
        [Nullable[int]]$FrontendRootPid,
        [Nullable[int]]$FrontendListenerPid,
        [string]$State
    )

    $status = [ordered]@{
        state = $State
        checked_at = (Get-Date).ToString("o")
        monitor_pid = if ($Once) { $null } else { $PID }
        mysql = [ordered]@{
            ready = $MySqlReady
            host = [string]$settings.MySQL.Host
            port = [int]$settings.MySQL.Port
        }
        backend = [ordered]@{
            healthy = $BackendHealthy
            root_pid = $BackendRootPid
            pid = $BackendListenerPid
            owned = [bool](
                $BackendRootPid -and
                $BackendListenerPid
            )
            url = [string]$settings.Backend.HealthUrl
        }
        frontend = [ordered]@{
            healthy = $FrontendHealthy
            root_pid = $FrontendRootPid
            pid = $FrontendListenerPid
            owned = [bool](
                $FrontendRootPid -and
                $FrontendListenerPid
            )
            url = [string]$settings.Frontend.HealthUrl
        }
    }

    Write-DeploymentStatus `
        -Path $runtime.StatusFile `
        -StatusObject $status
}

Build-FrontendIfNeeded

$backendProcess = $null
$frontendProcess = $null

try {
    & $mysqlScript

    while ($true) {
        if ((Test-Path $runtime.StopFile) -and -not $Once) {
            break
        }

        $mysqlReady = Test-TcpEndpoint `
            -HostName ([string]$settings.MySQL.Host) `
            -Port ([int]$settings.MySQL.Port)

        if (-not $mysqlReady) {
            try {
                & $mysqlScript
                $mysqlReady = $true
            }
            catch {
                $mysqlReady = $false
            }
        }

        $backendHealthy = Test-BackendHealth `
            -Url ([string]$settings.Backend.HealthUrl)

        if (-not $backendHealthy -and $mysqlReady) {
            if (
                $backendProcess -and
                (Test-ProcessId -ProcessId $backendProcess.Id)
            ) {
                Stop-KnownProcess -ProcessId $backendProcess.Id
            }

            Start-Sleep -Seconds ([int]$settings.Monitor.RestartDelaySeconds)
            $backendProcess = Start-Backend
            $backendHealthy = Wait-BackendHealthy
        }

        $frontendHealthy = Test-FrontendHealth `
            -Url ([string]$settings.Frontend.HealthUrl)

        if (-not $frontendHealthy) {
            if (
                $frontendProcess -and
                (Test-ProcessId -ProcessId $frontendProcess.Id)
            ) {
                Stop-KnownProcess -ProcessId $frontendProcess.Id
            }

            Start-Sleep -Seconds ([int]$settings.Monitor.RestartDelaySeconds)
            $frontendProcess = Start-Frontend
            $frontendHealthy = Wait-FrontendHealthy
        }

        $backendRootPid = $null
        $backendListenerPid = $null
        $frontendRootPid = $null
        $frontendListenerPid = $null

        if (
            $backendProcess -and
            (Test-ProcessId -ProcessId $backendProcess.Id)
        ) {
            $backendRootPid = [int]$backendProcess.Id
            $backendListenerPid = Get-ManagedListenerProcessId `
                -RootProcessId $backendRootPid `
                -Port ([int]$settings.Backend.Port) `
                -LocalAddress ([string]$settings.Backend.Host)
        }

        if (
            $frontendProcess -and
            (Test-ProcessId -ProcessId $frontendProcess.Id)
        ) {
            $frontendRootPid = [int]$frontendProcess.Id
            $frontendListenerPid = Get-ManagedListenerProcessId `
                -RootProcessId $frontendRootPid `
                -Port ([int]$settings.Frontend.Port) `
                -LocalAddress ([string]$settings.Frontend.Host)
        }

        Save-Status `
            -MySqlReady $mysqlReady `
            -BackendHealthy $backendHealthy `
            -FrontendHealthy $frontendHealthy `
            -BackendRootPid $backendRootPid `
            -BackendListenerPid $backendListenerPid `
            -FrontendRootPid $frontendRootPid `
            -FrontendListenerPid $frontendListenerPid `
            -State $(if ($mysqlReady -and $backendHealthy -and $frontendHealthy) { "healthy" } else { "degraded" })

        if ($Once) {
            if (-not ($mysqlReady -and $backendHealthy -and $frontendHealthy)) {
                exit 1
            }

            exit 0
        }

        Start-Sleep -Seconds ([int]$settings.Monitor.IntervalSeconds)
    }
}
finally {
    if ((Test-Path $runtime.StopFile) -and -not $Once) {
        if ($backendProcess) {
            Stop-KnownProcess -ProcessId $backendProcess.Id
        }

        if ($frontendProcess) {
            Stop-KnownProcess -ProcessId $frontendProcess.Id
        }

        $mysqlReady = Test-TcpEndpoint `
            -HostName ([string]$settings.MySQL.Host) `
            -Port ([int]$settings.MySQL.Port)

        Save-Status `
            -MySqlReady $mysqlReady `
            -BackendHealthy $false `
            -FrontendHealthy $false `
            -BackendRootPid $null `
            -BackendListenerPid $null `
            -FrontendRootPid $null `
            -FrontendListenerPid $null `
            -State "stopped"

        Remove-Item $runtime.StopFile -Force -ErrorAction SilentlyContinue
    }
}
