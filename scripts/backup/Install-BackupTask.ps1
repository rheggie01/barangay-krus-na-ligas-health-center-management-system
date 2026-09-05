param(
    [string]$BackupTime = "",
    [switch]$SkipInitialBackup
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

. (Join-Path $PSScriptRoot "Common-BackupFunctions.ps1")

$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($identity)

if (
    -not $principal.IsInRole(
        [Security.Principal.WindowsBuiltInRole]::Administrator
    )
) {
    throw "Run PowerShell as Administrator to install the scheduled backup task."
}

$projectRoot = Get-ProjectRoot
$settings = Get-BackupSettings -ProjectRoot $projectRoot

if ([string]::IsNullOrWhiteSpace($BackupTime)) {
    $BackupTime = [string]$settings.ScheduleTime
}

try {
    $time = [DateTime]::ParseExact(
        $BackupTime,
        "HH:mm",
        [Globalization.CultureInfo]::InvariantCulture
    )
}
catch {
    throw "BackupTime must use 24-hour HH:mm format, for example 22:00."
}

$backupScript = Join-Path $PSScriptRoot "Invoke-DatabaseBackup.ps1"

if (-not $SkipInitialBackup) {
    Write-Host "Running one backup before installing the task..."
    & $backupScript

    if ($LASTEXITCODE -ne 0) {
        throw "Initial backup failed. Scheduled task was not installed."
    }
}

$taskName = "Nightly Database Backup"
$taskPath = "\BarangayHealthSystem\"

$actionArguments = (
    '-NoProfile -ExecutionPolicy Bypass -File "' +
    $backupScript +
    '" -Quiet'
)

$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument $actionArguments

$trigger = New-ScheduledTaskTrigger `
    -Daily `
    -At $time

$taskPrincipal = New-ScheduledTaskPrincipal `
    -UserId "SYSTEM" `
    -LogonType ServiceAccount `
    -RunLevel Highest

$taskSettings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Hours 2)

Register-ScheduledTask `
    -TaskName $taskName `
    -TaskPath $taskPath `
    -Action $action `
    -Trigger $trigger `
    -Principal $taskPrincipal `
    -Settings $taskSettings `
    -Description "Automatic nightly MySQL backup for Barangay Health Center Management System." `
    -Force | Out-Null

Write-Host ""
Write-Host "BACKUP TASK INSTALLED"
Write-Host "====================="
Write-Host "Task : $taskPath$taskName"
Write-Host "Time : $BackupTime daily"
Write-Host "User : SYSTEM"
Write-Host ""
Write-Host "The task uses StartWhenAvailable, so if the PC is off at the scheduled"
Write-Host "time, Windows can run it after the machine becomes available again."
