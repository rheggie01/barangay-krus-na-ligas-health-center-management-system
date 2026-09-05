Set-StrictMode -Version Latest

function Get-ProjectRoot {
    return (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}

function Get-DeploymentSettings {
    param(
        [string]$ProjectRoot = (Get-ProjectRoot)
    )

    $localPath = Join-Path $ProjectRoot "scripts\deployment\deployment-settings.local.json"
    $examplePath = Join-Path $ProjectRoot "scripts\deployment\deployment-settings.example.json"

    if (Test-Path $localPath) {
        return Get-Content $localPath -Raw | ConvertFrom-Json
    }

    if (-not (Test-Path $examplePath)) {
        throw "Deployment settings file not found: $examplePath"
    }

    return Get-Content $examplePath -Raw | ConvertFrom-Json
}

function Get-DeploymentRuntime {
    param(
        [string]$ProjectRoot = (Get-ProjectRoot)
    )

    $root = Join-Path $ProjectRoot "runtime\deployment"
    $logs = Join-Path $root "logs"

    New-Item -ItemType Directory -Force -Path $root | Out-Null
    New-Item -ItemType Directory -Force -Path $logs | Out-Null

    return [pscustomobject]@{
        Root = $root
        Logs = $logs
        StatusFile = (Join-Path $root "deployment-status.json")
        StopFile = (Join-Path $root "stop.request")
    }
}

function Test-ProcessId {
    param(
        [Nullable[int]]$ProcessId
    )

    if (-not $ProcessId) {
        return $false
    }

    return $null -ne (
        Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    )
}

function Test-TcpEndpoint {
    param(
        [Parameter(Mandatory)]
        [string]$HostName,

        [Parameter(Mandatory)]
        [int]$Port,

        [int]$TimeoutMilliseconds = 2000
    )

    $client = New-Object System.Net.Sockets.TcpClient

    try {
        $async = $client.BeginConnect(
            $HostName,
            $Port,
            $null,
            $null
        )

        if (-not $async.AsyncWaitHandle.WaitOne($TimeoutMilliseconds, $false)) {
            return $false
        }

        $client.EndConnect($async)
        return $true
    }
    catch {
        return $false
    }
    finally {
        $client.Close()
    }
}

function Test-BackendHealth {
    param(
        [Parameter(Mandatory)]
        [string]$Url
    )

    try {
        $result = Invoke-RestMethod `
            -Uri $Url `
            -Method Get `
            -TimeoutSec 5

        return (
            $result.status -eq "ok" -and
            $result.backend -eq "connected" -and
            $result.database -eq "connected"
        )
    }
    catch {
        return $false
    }
}

function Test-FrontendHealth {
    param(
        [Parameter(Mandatory)]
        [string]$Url
    )

    try {
        $response = Invoke-WebRequest `
            -Uri $Url `
            -Method Get `
            -UseBasicParsing `
            -TimeoutSec 5

        return (
            $response.StatusCode -ge 200 -and
            $response.StatusCode -lt 400
        )
    }
    catch {
        return $false
    }
}

function Write-DeploymentStatus {
    param(
        [Parameter(Mandatory)]
        [string]$Path,

        [Parameter(Mandatory)]
        $StatusObject
    )

    $temp = "$Path.tmp"

    $StatusObject |
        ConvertTo-Json -Depth 6 |
        Set-Content -Path $temp -Encoding UTF8

    Move-Item -Path $temp -Destination $Path -Force
}

function Read-DeploymentStatus {
    param(
        [Parameter(Mandatory)]
        [string]$Path
    )

    if (-not (Test-Path $Path)) {
        return $null
    }

    try {
        return Get-Content $Path -Raw | ConvertFrom-Json
    }
    catch {
        return $null
    }
}

function New-DeploymentLogPath {
    param(
        [Parameter(Mandatory)]
        [string]$LogsFolder,

        [Parameter(Mandatory)]
        [string]$Component,

        [Parameter(Mandatory)]
        [ValidateSet("out", "err")]
        [string]$Stream
    )

    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

    return Join-Path $LogsFolder (
        "$Component-$timestamp.$Stream.log"
    )
}

function Test-IsAdministrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()

    $principal = New-Object Security.Principal.WindowsPrincipal(
        $identity
    )

    return $principal.IsInRole(
        [Security.Principal.WindowsBuiltInRole]::Administrator
    )
}


function Get-ListeningProcessId {
    param(
        [Parameter(Mandatory)]
        [int]$Port,

        [string]$LocalAddress = "127.0.0.1"
    )

    $listeners = Get-NetTCPConnection `
        -State Listen `
        -LocalPort $Port `
        -ErrorAction SilentlyContinue

    if (-not $listeners) {
        return $null
    }

    $preferred = $listeners |
        Where-Object {
            $_.LocalAddress -eq $LocalAddress
        } |
        Select-Object -First 1

    if (-not $preferred) {
        $preferred = $listeners |
            Select-Object -First 1
    }

    if (-not $preferred) {
        return $null
    }

    return [int]$preferred.OwningProcess
}

function Test-ProcessDescendantOf {
    param(
        [Parameter(Mandatory)]
        [int]$ProcessId,

        [Parameter(Mandatory)]
        [int]$AncestorProcessId
    )

    if ($ProcessId -eq $AncestorProcessId) {
        return $true
    }

    $visited = @{}
    $current = $ProcessId

    while ($current -gt 0) {
        if ($visited.ContainsKey($current)) {
            return $false
        }

        $visited[$current] = $true

        $process = Get-CimInstance Win32_Process `
            -Filter "ProcessId = $current" `
            -ErrorAction SilentlyContinue

        if (-not $process) {
            return $false
        }

        $parent = [int]$process.ParentProcessId

        if ($parent -eq $AncestorProcessId) {
            return $true
        }

        if ($parent -le 0 -or $parent -eq $current) {
            return $false
        }

        $current = $parent
    }

    return $false
}

function Get-ManagedListenerProcessId {
    param(
        [Nullable[int]]$RootProcessId,

        [Parameter(Mandatory)]
        [int]$Port,

        [string]$LocalAddress = "127.0.0.1"
    )

    if (-not $RootProcessId) {
        return $null
    }

    $listenerPid = Get-ListeningProcessId `
        -Port $Port `
        -LocalAddress $LocalAddress

    if (-not $listenerPid) {
        return $null
    }

    if (
        Test-ProcessDescendantOf `
            -ProcessId $listenerPid `
            -AncestorProcessId ([int]$RootProcessId)
    ) {
        return [int]$listenerPid
    }

    return $null
}

function Stop-ProcessTree {
    param(
        [Nullable[int]]$RootProcessId
    )

    if (-not $RootProcessId) {
        return
    }

    $rootPid = [int]$RootProcessId

    if (-not (Test-ProcessId -ProcessId $rootPid)) {
        return
    }

    & taskkill.exe `
        /PID $rootPid `
        /T `
        /F `
        2>$null |
        Out-Null

    Start-Sleep -Milliseconds 750
}


function Get-OptionalPropertyValue {
    param(
        $Object,

        [Parameter(Mandatory)]
        [string]$Name,

        $Default = $null
    )

    if ($null -eq $Object) {
        return $Default
    }

    $property = $Object.PSObject.Properties[$Name]

    if ($null -eq $property) {
        return $Default
    }

    return $property.Value
}
