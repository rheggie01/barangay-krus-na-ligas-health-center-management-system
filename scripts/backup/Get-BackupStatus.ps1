$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

. (Join-Path $PSScriptRoot "Common-BackupFunctions.ps1")

$projectRoot = Get-ProjectRoot
$settings = Get-BackupSettings -ProjectRoot $projectRoot

$backupRoot = Resolve-ConfiguredPath `
    -ProjectRoot $projectRoot `
    -PathValue ([string]$settings.BackupRoot)

$statusPath = Join-Path $backupRoot "Status\backup-status.json"

if (-not (Test-Path $statusPath)) {
    Write-Host "No backup status exists yet."
    Write-Host "Run:"
    Write-Host ".\scripts\backup\Invoke-DatabaseBackup.ps1"
    exit 0
}

$status = Get-Content $statusPath -Raw | ConvertFrom-Json

Write-Host ""
Write-Host "DATABASE BACKUP STATUS"
Write-Host "======================"
Write-Host "Success    : $($status.success)"
Write-Host "Database   : $($status.database)"
Write-Host "Finished   : $($status.finished_at)"
Write-Host "Duration   : $($status.duration_seconds) seconds"
Write-Host "Encrypted  : $($status.encrypted)"
Write-Host "Cloud      : $($status.cloud_status)"
Write-Host "Local file : $($status.local_backup_path)"
Write-Host "Message    : $($status.message)"
Write-Host ""
