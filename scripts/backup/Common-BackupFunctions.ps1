Set-StrictMode -Version Latest

function Get-ProjectRoot {
    return (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}

function Get-BackupSettings {
    param(
        [string]$ProjectRoot = (Get-ProjectRoot)
    )

    $localPath = Join-Path $ProjectRoot "scripts\backup\backup-settings.local.json"
    $examplePath = Join-Path $ProjectRoot "scripts\backup\backup-settings.example.json"

    if (Test-Path $localPath) {
        return Get-Content $localPath -Raw | ConvertFrom-Json
    }

    if (-not (Test-Path $examplePath)) {
        throw "Backup settings file not found: $examplePath"
    }

    return Get-Content $examplePath -Raw | ConvertFrom-Json
}

function Resolve-ConfiguredPath {
    param(
        [Parameter(Mandatory)]
        [string]$ProjectRoot,

        [Parameter(Mandatory)]
        [string]$PathValue
    )

    if ([string]::IsNullOrWhiteSpace($PathValue)) {
        return $null
    }

    if ([System.IO.Path]::IsPathRooted($PathValue)) {
        return $PathValue
    }

    return Join-Path $ProjectRoot $PathValue
}

function Read-DotEnv {
    param(
        [Parameter(Mandatory)]
        [string]$Path
    )

    if (-not (Test-Path $Path)) {
        throw "Backend .env file not found: $Path"
    }

    $values = @{}

    foreach ($line in Get-Content $Path) {
        $trimmed = $line.Trim()

        if (
            [string]::IsNullOrWhiteSpace($trimmed) -or
            $trimmed.StartsWith("#")
        ) {
            continue
        }

        $index = $trimmed.IndexOf("=")

        if ($index -lt 1) {
            continue
        }

        $key = $trimmed.Substring(0, $index).Trim()
        $value = $trimmed.Substring($index + 1).Trim()

        if (
            ($value.StartsWith('"') -and $value.EndsWith('"')) -or
            ($value.StartsWith("'") -and $value.EndsWith("'"))
        ) {
            $value = $value.Substring(1, $value.Length - 2)
        }

        $values[$key] = $value
    }

    return $values
}

function Get-DatabaseConfig {
    param(
        [Parameter(Mandatory)]
        [string]$ProjectRoot
    )

    $envPath = Join-Path $ProjectRoot "backend\.env"
    $env = Read-DotEnv -Path $envPath

    $required = @(
        "DATABASE_HOST",
        "DATABASE_PORT",
        "DATABASE_NAME",
        "DATABASE_USER",
        "DATABASE_PASSWORD"
    )

    foreach ($key in $required) {
        if (-not $env.ContainsKey($key)) {
            throw "Missing $key in backend\.env"
        }
    }

    return [pscustomobject]@{
        Host = $env["DATABASE_HOST"]
        Port = $env["DATABASE_PORT"]
        Name = $env["DATABASE_NAME"]
        User = $env["DATABASE_USER"]
        Password = $env["DATABASE_PASSWORD"]
    }
}

function Find-MySqlExecutable {
    param(
        [string]$ConfiguredPath,
        [ValidateSet("dump", "client")]
        [string]$Kind
    )

    if (
        -not [string]::IsNullOrWhiteSpace($ConfiguredPath) -and
        (Test-Path $ConfiguredPath)
    ) {
        return (Resolve-Path $ConfiguredPath).Path
    }

    $commandName = if ($Kind -eq "dump") {
        "mysqldump.exe"
    }
    else {
        "mysql.exe"
    }

    $command = Get-Command $commandName -ErrorAction SilentlyContinue

    if ($command) {
        return $command.Source
    }

    $common = @()

    if ($Kind -eq "dump") {
        $common += "C:\xampp\mysql\bin\mysqldump.exe"
    }
    else {
        $common += "C:\xampp\mysql\bin\mysql.exe"
    }

    $mysqlBase = "C:\Program Files\MySQL"

    if (Test-Path $mysqlBase) {
        $pattern = if ($Kind -eq "dump") {
            "mysqldump.exe"
        }
        else {
            "mysql.exe"
        }

        $found = Get-ChildItem $mysqlBase -Recurse -Filter $pattern -ErrorAction SilentlyContinue |
            Select-Object -First 1

        if ($found) {
            return $found.FullName
        }
    }

    foreach ($candidate in $common) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    throw "Could not locate MySQL $Kind executable. Configure it in backup-settings.local.json."
}

function Find-SevenZipExecutable {
    param(
        [string]$ConfiguredPath
    )

    if (
        -not [string]::IsNullOrWhiteSpace($ConfiguredPath) -and
        (Test-Path $ConfiguredPath)
    ) {
        return (Resolve-Path $ConfiguredPath).Path
    }

    $command = Get-Command "7z.exe" -ErrorAction SilentlyContinue

    if ($command) {
        return $command.Source
    }

    $common = @(
        "C:\Program Files\7-Zip\7z.exe",
        "C:\Program Files (x86)\7-Zip\7z.exe"
    )

    foreach ($candidate in $common) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    throw "7-Zip was not found. Install 7-Zip or configure SevenZipExecutable."
}

function New-MySqlDefaultsFile {
    param(
        [Parameter(Mandatory)]
        $DatabaseConfig
    )

    $temp = Join-Path $env:TEMP (
        "barangay-health-mysql-" +
        [Guid]::NewGuid().ToString("N") +
        ".cnf"
    )

    $content = @"
[client]
host=$($DatabaseConfig.Host)
port=$($DatabaseConfig.Port)
user=$($DatabaseConfig.User)
password=$($DatabaseConfig.Password)
default-character-set=utf8mb4
"@

    Set-Content -Path $temp -Value $content -Encoding ASCII
    return $temp
}

function Get-BackupSecret {
    param(
        [Parameter(Mandatory)]
        [string]$SecretFile
    )

    if (-not (Test-Path $SecretFile)) {
        throw "Encrypted backup secret file not found: $SecretFile"
    }

    Add-Type -AssemblyName System.Security

    $protectedBytes = [Convert]::FromBase64String(
        (Get-Content $SecretFile -Raw).Trim()
    )

    $plainBytes = [System.Security.Cryptography.ProtectedData]::Unprotect(
        $protectedBytes,
        $null,
        [System.Security.Cryptography.DataProtectionScope]::LocalMachine
    )

    return [Text.Encoding]::UTF8.GetString($plainBytes)
}

function Write-BackupLog {
    param(
        [Parameter(Mandatory)]
        [string]$LogPath,

        [Parameter(Mandatory)]
        [string]$Message
    )

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path $LogPath -Value "[$timestamp] $Message"
}

function Remove-OldBackups {
    param(
        [Parameter(Mandatory)]
        [string]$Folder,

        [Parameter(Mandatory)]
        [int]$Keep
    )

    if ($Keep -lt 1 -or -not (Test-Path $Folder)) {
        return
    }

    Get-ChildItem $Folder -File |
        Sort-Object LastWriteTime -Descending |
        Select-Object -Skip $Keep |
        Remove-Item -Force
}

function Write-BackupStatus {
    param(
        [Parameter(Mandatory)]
        [string]$StatusPath,

        [Parameter(Mandatory)]
        $StatusObject
    )

    $StatusObject |
        ConvertTo-Json -Depth 5 |
        Set-Content -Path $StatusPath -Encoding UTF8
}
