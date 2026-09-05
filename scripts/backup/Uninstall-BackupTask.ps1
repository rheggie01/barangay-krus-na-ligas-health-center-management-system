$ErrorActionPreference = "Stop"

$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($identity)

if (
    -not $principal.IsInRole(
        [Security.Principal.WindowsBuiltInRole]::Administrator
    )
) {
    throw "Run PowerShell as Administrator to remove the scheduled backup task."
}

$taskName = "Nightly Database Backup"
$taskPath = "\BarangayHealthSystem\"

$existing = Get-ScheduledTask `
    -TaskName $taskName `
    -TaskPath $taskPath `
    -ErrorAction SilentlyContinue

if (-not $existing) {
    Write-Host "Backup task is not installed."
    exit 0
}

Unregister-ScheduledTask `
    -TaskName $taskName `
    -TaskPath $taskPath `
    -Confirm:$false

Write-Host "Backup task removed."
