$ErrorActionPreference = "Stop"

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$example = Join-Path $PSScriptRoot "backup-settings.example.json"
$local = Join-Path $PSScriptRoot "backup-settings.local.json"

if (Test-Path $local) {
    Write-Host "Local backup settings already exist:"
    Write-Host $local
    exit 0
}

Copy-Item $example $local

Write-Host ""
Write-Host "Local backup settings created:"
Write-Host $local
Write-Host ""
Write-Host "This file is ignored by Git."
Write-Host "Edit it if you need:"
Write-Host "- custom mysqldump/mysql paths"
Write-Host "- encryption"
Write-Host "- cloud/synced-folder copy"
Write-Host "- different retention"
Write-Host "- a different nightly time"
