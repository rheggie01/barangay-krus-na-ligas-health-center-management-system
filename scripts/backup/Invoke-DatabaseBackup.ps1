param(
    [switch]$Quiet
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

. (Join-Path $PSScriptRoot "Common-BackupFunctions.ps1")

$started = Get-Date
$projectRoot = Get-ProjectRoot
$settings = Get-BackupSettings -ProjectRoot $projectRoot
$db = Get-DatabaseConfig -ProjectRoot $projectRoot

$backupRoot = Resolve-ConfiguredPath `
    -ProjectRoot $projectRoot `
    -PathValue ([string]$settings.BackupRoot)

$dailyDir = Join-Path $backupRoot "Daily"
$weeklyDir = Join-Path $backupRoot "Weekly"
$monthlyDir = Join-Path $backupRoot "Monthly"
$logsDir = Join-Path $backupRoot "Logs"
$statusDir = Join-Path $backupRoot "Status"

foreach ($dir in @(
    $backupRoot,
    $dailyDir,
    $weeklyDir,
    $monthlyDir,
    $logsDir,
    $statusDir
)) {
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
}

$logPath = Join-Path $logsDir (
    "backup-" + (Get-Date -Format "yyyy-MM") + ".log"
)

$statusPath = Join-Path $statusDir "backup-status.json"
$timestamp = Get-Date -Format "yyyy-MM-dd_HHmmss"
$safeDbName = ($db.Name -replace '[^A-Za-z0-9_-]', '_')
$sqlPath = Join-Path $dailyDir "$safeDbName`_$timestamp.sql"
$finalBackupPath = $sqlPath
$cloudStatus = "DISABLED"
$cloudPath = $null
$defaultsFile = $null

try {
    Write-BackupLog -LogPath $logPath -Message (
        "START database backup for $($db.Name)"
    )

    $mysqldump = Find-MySqlExecutable `
        -ConfiguredPath ([string]$settings.MySQL.DumpExecutable) `
        -Kind "dump"

    $defaultsFile = New-MySqlDefaultsFile -DatabaseConfig $db

    $arguments = @(
        "--defaults-extra-file=$defaultsFile",
        "--single-transaction",
        "--set-gtid-purged=OFF",
        "--quick",
        "--routines",
        "--triggers",
        "--events",
        "--hex-blob",
        "--default-character-set=utf8mb4",
        "--result-file=$sqlPath",
        $db.Name
    )

    & $mysqldump @arguments

    if ($LASTEXITCODE -ne 0) {
        throw "mysqldump failed with exit code $LASTEXITCODE"
    }

    if (
        -not (Test-Path $sqlPath) -or
        (Get-Item $sqlPath).Length -lt 100
    ) {
        throw "Backup SQL file was not created or is unexpectedly small."
    }

    if ([bool]$settings.Encryption.Enabled) {
        $sevenZip = Find-SevenZipExecutable `
            -ConfiguredPath ([string]$settings.Encryption.SevenZipExecutable)

        $secretFile = Resolve-ConfiguredPath `
            -ProjectRoot $projectRoot `
            -PathValue ([string]$settings.Encryption.SecretFile)

        $passphrase = Get-BackupSecret -SecretFile $secretFile
        $archivePath = [System.IO.Path]::ChangeExtension($sqlPath, ".7z")

        & $sevenZip `
            "a" `
            "-t7z" `
            "-mx=7" `
            "-mhe=on" `
            "-p$passphrase" `
            $archivePath `
            $sqlPath | Out-Null

        if ($LASTEXITCODE -ne 0 -or -not (Test-Path $archivePath)) {
            throw "7-Zip encryption failed."
        }

        Remove-Item $sqlPath -Force
        $finalBackupPath = $archivePath
    }

    $now = Get-Date

    if ($now.DayOfWeek -eq [DayOfWeek]::Sunday) {
        Copy-Item $finalBackupPath -Destination $weeklyDir -Force
    }

    if ($now.Day -eq 1) {
        Copy-Item $finalBackupPath -Destination $monthlyDir -Force
    }

    Remove-OldBackups `
        -Folder $dailyDir `
        -Keep ([int]$settings.Retention.Daily)

    Remove-OldBackups `
        -Folder $weeklyDir `
        -Keep ([int]$settings.Retention.Weekly)

    Remove-OldBackups `
        -Folder $monthlyDir `
        -Keep ([int]$settings.Retention.Monthly)

    if ([bool]$settings.Cloud.Enabled) {
        $cloudRoot = [string]$settings.Cloud.Path

        if ([string]::IsNullOrWhiteSpace($cloudRoot)) {
            throw "Cloud backup is enabled but Cloud.Path is empty."
        }

        if (
            -not [bool]$settings.Encryption.Enabled -and
            -not [bool]$settings.Cloud.AllowUnencryptedCopy
        ) {
            throw (
                "Cloud copy blocked: encryption is disabled. " +
                "Enable Encryption.Enabled or explicitly set " +
                "Cloud.AllowUnencryptedCopy=true for synthetic/development data only."
            )
        }

        $cloudDaily = Join-Path $cloudRoot "Daily"
        $cloudWeekly = Join-Path $cloudRoot "Weekly"
        $cloudMonthly = Join-Path $cloudRoot "Monthly"

        foreach ($dir in @(
            $cloudDaily,
            $cloudWeekly,
            $cloudMonthly
        )) {
            New-Item -ItemType Directory -Force -Path $dir | Out-Null
        }

        $cloudPath = Join-Path $cloudDaily (Split-Path $finalBackupPath -Leaf)
        Copy-Item $finalBackupPath -Destination $cloudPath -Force

        if ($now.DayOfWeek -eq [DayOfWeek]::Sunday) {
            Copy-Item $finalBackupPath -Destination $cloudWeekly -Force
        }

        if ($now.Day -eq 1) {
            Copy-Item $finalBackupPath -Destination $cloudMonthly -Force
        }

        Remove-OldBackups `
            -Folder $cloudDaily `
            -Keep ([int]$settings.Retention.Daily)

        Remove-OldBackups `
            -Folder $cloudWeekly `
            -Keep ([int]$settings.Retention.Weekly)

        Remove-OldBackups `
            -Folder $cloudMonthly `
            -Keep ([int]$settings.Retention.Monthly)

        $cloudStatus = "COPIED"
    }

    $finished = Get-Date
    $size = (Get-Item $finalBackupPath).Length

    $status = [ordered]@{
        success = $true
        database = $db.Name
        started_at = $started.ToString("o")
        finished_at = $finished.ToString("o")
        duration_seconds = [math]::Round(
            ($finished - $started).TotalSeconds,
            2
        )
        local_backup_path = $finalBackupPath
        local_size_bytes = $size
        encrypted = [bool]$settings.Encryption.Enabled
        cloud_status = $cloudStatus
        cloud_backup_path = $cloudPath
        message = "Backup completed successfully."
    }

    Write-BackupStatus `
        -StatusPath $statusPath `
        -StatusObject $status

    Write-BackupLog -LogPath $logPath -Message (
        "SUCCESS backup=$finalBackupPath size=$size cloud=$cloudStatus"
    )

    if (-not $Quiet) {
        Write-Host ""
        Write-Host "DATABASE BACKUP SUCCESSFUL"
        Write-Host "=========================="
        Write-Host "Database : $($db.Name)"
        Write-Host "Backup   : $finalBackupPath"
        Write-Host "Encrypted: $([bool]$settings.Encryption.Enabled)"
        Write-Host "Cloud    : $cloudStatus"
        Write-Host ""
    }

    exit 0
}
catch {
    $finished = Get-Date

    $status = [ordered]@{
        success = $false
        database = $db.Name
        started_at = $started.ToString("o")
        finished_at = $finished.ToString("o")
        duration_seconds = [math]::Round(
            ($finished - $started).TotalSeconds,
            2
        )
        local_backup_path = $null
        local_size_bytes = 0
        encrypted = [bool]$settings.Encryption.Enabled
        cloud_status = $cloudStatus
        cloud_backup_path = $cloudPath
        message = $_.Exception.Message
    }

    Write-BackupStatus `
        -StatusPath $statusPath `
        -StatusObject $status

    Write-BackupLog -LogPath $logPath -Message (
        "FAILED $($_.Exception.Message)"
    )

    Write-Error $_.Exception.Message
    exit 1
}
finally {
    if ($defaultsFile -and (Test-Path $defaultsFile)) {
        Remove-Item $defaultsFile -Force -ErrorAction SilentlyContinue
    }
}
