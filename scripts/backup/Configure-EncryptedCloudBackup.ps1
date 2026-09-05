param(
    [string]$CloudPath = "",
    [switch]$SkipCloud,
    [switch]$InstallSevenZip
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

. (Join-Path $PSScriptRoot "Common-BackupFunctions.ps1")

$projectRoot = Get-ProjectRoot
$settingsPath = Join-Path $PSScriptRoot "backup-settings.local.json"
$examplePath = Join-Path $PSScriptRoot "backup-settings.example.json"

if (-not (Test-Path $settingsPath)) {
    if (-not (Test-Path $examplePath)) {
        throw "Missing backup settings template: $examplePath"
    }

    Copy-Item $examplePath $settingsPath
    Write-Host "Created local backup settings."
}

function Find-SevenZip {
    $configured = $null

    try {
        $current = Get-Content $settingsPath -Raw | ConvertFrom-Json
        $configured = [string]$current.Encryption.SevenZipExecutable
    }
    catch {
        $configured = ""
    }

    if (
        -not [string]::IsNullOrWhiteSpace($configured) -and
        (Test-Path $configured)
    ) {
        return (Resolve-Path $configured).Path
    }

    $command = Get-Command "7z.exe" -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    foreach ($candidate in @(
        "C:\Program Files\7-Zip\7z.exe",
        "C:\Program Files (x86)\7-Zip\7z.exe"
    )) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    return $null
}

$sevenZip = Find-SevenZip

if (-not $sevenZip -and $InstallSevenZip) {
    $winget = Get-Command "winget.exe" -ErrorAction SilentlyContinue

    if (-not $winget) {
        throw "7-Zip is missing and winget is not available."
    }

    Write-Host "Installing 7-Zip with winget..."
    & winget install --id 7zip.7zip --exact --accept-source-agreements --accept-package-agreements

    if ($LASTEXITCODE -ne 0) {
        throw "7-Zip installation failed."
    }

    $sevenZip = Find-SevenZip
}

if (-not $sevenZip) {
    Write-Host ""
    Write-Host "7-Zip is required for encrypted backups."
    Write-Host ""
    Write-Host "Install it, then run this script again."
    Write-Host ""
    Write-Host "Option 1:"
    Write-Host "winget install --id 7zip.7zip --exact"
    Write-Host ""
    Write-Host "Option 2:"
    Write-Host ".\scripts\backup\Configure-EncryptedCloudBackup.ps1 -InstallSevenZip"
    Write-Host ""
    exit 2
}

if (
    [string]::IsNullOrWhiteSpace($CloudPath) -and
    -not $SkipCloud
) {
    # Prefer OneDriveCommercial when an organization/work account exists.
    $candidates = @(
        $env:OneDriveCommercial,
        $env:OneDrive,
        $env:OneDriveConsumer
    ) | Where-Object {
        -not [string]::IsNullOrWhiteSpace($_)
    } | Select-Object -Unique

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            $CloudPath = Join-Path $candidate "BarangayHealthCenterBackups"
            break
        }
    }
}

if (
    [string]::IsNullOrWhiteSpace($CloudPath) -and
    -not $SkipCloud
) {
    Write-Host ""
    Write-Host "No synced cloud folder was auto-detected."
    Write-Host ""
    Write-Host "Run again with an approved synced folder, for example:"
    Write-Host '.\scripts\backup\Configure-EncryptedCloudBackup.ps1 -CloudPath "D:\AuthorizedHealthCenterBackupSync"'
    Write-Host ""
    Write-Host "Or use -SkipCloud to enable encryption only."
    exit 3
}

$settings = Get-Content $settingsPath -Raw | ConvertFrom-Json

$settings.Encryption.Enabled = $true
$settings.Encryption.SevenZipExecutable = $sevenZip
$settings.Cloud.AllowUnencryptedCopy = $false

if ($SkipCloud) {
    $settings.Cloud.Enabled = $false
}
else {
    New-Item -ItemType Directory -Force -Path $CloudPath | Out-Null
    $settings.Cloud.Enabled = $true
    $settings.Cloud.Path = $CloudPath
}

$settings |
    ConvertTo-Json -Depth 6 |
    Set-Content -Path $settingsPath -Encoding UTF8

Write-Host ""
Write-Host "ENCRYPTED BACKUP SETTINGS UPDATED"
Write-Host "================================="
Write-Host "7-Zip     : $sevenZip"
Write-Host "Encryption: ENABLED"

if ($SkipCloud) {
    Write-Host "Cloud      : DISABLED"
}
else {
    Write-Host "Cloud      : ENABLED"
    Write-Host "Cloud path : $CloudPath"
}

Write-Host ""
Write-Host "Next, initialize the encryption passphrase."
Write-Host ""
Write-Host "IMPORTANT:"
Write-Host "- Use a strong unique passphrase."
Write-Host "- Store an authorized offline copy of the passphrase."
Write-Host "- Do not store the passphrase in GitHub."
Write-Host "- For real patient data, use only an authorized organization cloud account."
Write-Host ""

& (Join-Path $PSScriptRoot "Initialize-BackupEncryption.ps1")

if ($LASTEXITCODE -ne 0) {
    throw "Backup encryption initialization failed."
}

Write-Host ""
Write-Host "Configuration complete."
Write-Host "Run:"
Write-Host ".\scripts\backup\Test-EncryptedCloudBackup.ps1"
