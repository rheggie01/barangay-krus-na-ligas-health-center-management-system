param(
    [switch]$SkipRestoreVerification
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

. (Join-Path $PSScriptRoot "Common-BackupFunctions.ps1")

$projectRoot = Get-ProjectRoot
$settings = Get-BackupSettings -ProjectRoot $projectRoot

if (-not [bool]$settings.Encryption.Enabled) {
    throw "Encryption.Enabled is false. Configure encrypted backup first."
}

Write-Host ""
Write-Host "Creating encrypted database backup..."
Write-Host ""

& (Join-Path $PSScriptRoot "Invoke-DatabaseBackup.ps1")

if ($LASTEXITCODE -ne 0) {
    throw "Encrypted backup creation failed."
}

$backupRoot = Resolve-ConfiguredPath `
    -ProjectRoot $projectRoot `
    -PathValue ([string]$settings.BackupRoot)

$statusPath = Join-Path $backupRoot "Status\backup-status.json"

if (-not (Test-Path $statusPath)) {
    throw "Backup status file was not created."
}

$status = Get-Content $statusPath -Raw | ConvertFrom-Json

$checks = [ordered]@{
    "Backup success" = [bool]$status.success
    "Encrypted" = [bool]$status.encrypted
    "Local archive exists" = (
        -not [string]::IsNullOrWhiteSpace([string]$status.local_backup_path) -and
        (Test-Path ([string]$status.local_backup_path))
    )
    "Local archive is .7z" = (
        [System.IO.Path]::GetExtension(
            [string]$status.local_backup_path
        ) -eq ".7z"
    )
}

if ([bool]$settings.Cloud.Enabled) {
    $checks["Cloud status copied"] = (
        [string]$status.cloud_status -eq "COPIED"
    )
    $checks["Cloud archive exists"] = (
        -not [string]::IsNullOrWhiteSpace([string]$status.cloud_backup_path) -and
        (Test-Path ([string]$status.cloud_backup_path))
    )
}

$failed = @()

Write-Host ""
Write-Host "ENCRYPTED BACKUP CHECKS"
Write-Host "======================="

foreach ($entry in $checks.GetEnumerator()) {
    $label = if ($entry.Value) { "PASS" } else { "FAIL" }
    Write-Host "[$label] $($entry.Key)"

    if (-not $entry.Value) {
        $failed += $entry.Key
    }
}

if ($failed.Count -gt 0) {
    throw (
        "Encrypted/cloud backup validation failed: " +
        ($failed -join ", ")
    )
}

if (-not $SkipRestoreVerification) {
    Write-Host ""
    Write-Host "Running encrypted restore verification..."
    Write-Host ""

    & (Join-Path $PSScriptRoot "Test-DatabaseBackup.ps1")

    if ($LASTEXITCODE -ne 0) {
        throw "Encrypted restore verification failed."
    }
}

Write-Host ""
Write-Host "ENCRYPTED BACKUP VALIDATION PASSED"
Write-Host "=================================="
Write-Host "Local : $($status.local_backup_path)"
Write-Host "Cloud : $($status.cloud_backup_path)"
Write-Host ""
