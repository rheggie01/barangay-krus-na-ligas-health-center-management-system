param(
    [string]$SessionName = "UAT"
)

$ErrorActionPreference = "Stop"

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$safeName = ($SessionName -replace '[^A-Za-z0-9_-]', '_')
$evidenceRoot = Join-Path $projectRoot "runtime\testing\uat\${timestamp}_${safeName}"

New-Item -ItemType Directory -Path $evidenceRoot -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $evidenceRoot "screenshots") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $evidenceRoot "logs") -Force | Out-Null

$manifestPath = Join-Path $evidenceRoot "session-manifest.txt"
@(
    "Barangay Health System - UAT Evidence Session"
    "Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz')"
    "Session: $SessionName"
    "Project: $projectRoot"
    ""
    "Place screenshots under: screenshots\"
    "Place copied command/output logs under: logs\"
    "Record PASS/FAIL/BLOCKED/N/A in docs\uat\UAT_TEST_MATRIX.md or a working copy."
) | Set-Content -Path $manifestPath -Encoding UTF8

Write-Host "UAT EVIDENCE SESSION READY"
Write-Host "Folder: $evidenceRoot"
Write-Host "Manifest: $manifestPath"
