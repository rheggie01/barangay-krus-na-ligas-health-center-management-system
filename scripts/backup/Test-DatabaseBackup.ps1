param(
    [switch]$KeepVerificationDatabase
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

. (Join-Path $PSScriptRoot "Common-BackupFunctions.ps1")

$projectRoot = Get-ProjectRoot
$settings = Get-BackupSettings -ProjectRoot $projectRoot
$db = Get-DatabaseConfig -ProjectRoot $projectRoot

$backupRoot = Resolve-ConfiguredPath `
    -ProjectRoot $projectRoot `
    -PathValue ([string]$settings.BackupRoot)

$dailyDir = Join-Path $backupRoot "Daily"

$latest = Get-ChildItem $dailyDir -File -ErrorAction Stop |
    Where-Object {
        $_.Extension -in @(".sql", ".7z")
    } |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

if (-not $latest) {
    throw "No database backup found in $dailyDir"
}

$mysql = Find-MySqlExecutable `
    -ConfiguredPath ([string]$settings.MySQL.ClientExecutable) `
    -Kind "client"

$defaultsFile = New-MySqlDefaultsFile -DatabaseConfig $db

$tempDir = Join-Path $env:TEMP (
    "barangay-health-restore-" +
    [Guid]::NewGuid().ToString("N")
)

New-Item -ItemType Directory -Force -Path $tempDir | Out-Null

$verificationDb = (
    "backup_verify_" +
    (Get-Date -Format "yyyyMMdd_HHmmss")
)

$sqlFile = $null
$restoreSqlFile = $null
$createdDb = $false

function New-GtidSafeRestoreCopy {
    param(
        [Parameter(Mandatory)]
        [string]$InputSqlFile,

        [Parameter(Mandatory)]
        [string]$OutputSqlFile
    )

    $reader = [System.IO.StreamReader]::new(
        $InputSqlFile,
        [Text.Encoding]::UTF8,
        $true
    )

    $writer = [System.IO.StreamWriter]::new(
        $OutputSqlFile,
        $false,
        [Text.UTF8Encoding]::new($false)
    )

    $skipStatement = $false
    $removedCount = 0

    try {
        while (-not $reader.EndOfStream) {
            $line = $reader.ReadLine()

            if (-not $skipStatement -and $line -match 'GTID_PURGED') {
                $removedCount++

                if ($line -notmatch ';\s*$') {
                    $skipStatement = $true
                }

                continue
            }

            if ($skipStatement) {
                if ($line -match ';\s*$') {
                    $skipStatement = $false
                }

                continue
            }

            $writer.WriteLine($line)
        }
    }
    finally {
        $reader.Dispose()
        $writer.Dispose()
    }

    return $removedCount
}

function Invoke-MySqlFileImport {
    param(
        [Parameter(Mandatory)]
        [string]$MySqlExecutable,

        [Parameter(Mandatory)]
        [string]$DefaultsFile,

        [Parameter(Mandatory)]
        [string]$DatabaseName,

        [Parameter(Mandatory)]
        [string]$SqlFile,

        [Parameter(Mandatory)]
        [string]$TempDirectory
    )

    $stdoutFile = Join-Path $TempDirectory "mysql-restore-stdout.txt"
    $stderrFile = Join-Path $TempDirectory "mysql-restore-stderr.txt"

    $commandLine = (
        '""' +
        $MySqlExecutable +
        '" "--defaults-extra-file=' +
        $DefaultsFile +
        '" "' +
        $DatabaseName +
        '" < "' +
        $SqlFile +
        '" 1> "' +
        $stdoutFile +
        '" 2> "' +
        $stderrFile +
        '""'
    )

    $process = Start-Process `
        -FilePath "cmd.exe" `
        -ArgumentList @(
            "/d",
            "/s",
            "/c",
            $commandLine
        ) `
        -Wait `
        -PassThru `
        -NoNewWindow

    $stdout = if (Test-Path $stdoutFile) {
        Get-Content $stdoutFile -Raw
    }
    else {
        ""
    }

    $stderr = if (Test-Path $stderrFile) {
        Get-Content $stderrFile -Raw
    }
    else {
        ""
    }

    return [pscustomobject]@{
        ExitCode = $process.ExitCode
        StdOut = $stdout
        StdErr = $stderr
    }
}

try {
    if ($latest.Extension -eq ".sql") {
        $sqlFile = $latest.FullName
    }
    else {
        $sevenZip = Find-SevenZipExecutable `
            -ConfiguredPath ([string]$settings.Encryption.SevenZipExecutable)

        $secretFile = Resolve-ConfiguredPath `
            -ProjectRoot $projectRoot `
            -PathValue ([string]$settings.Encryption.SecretFile)

        $passphrase = Get-BackupSecret -SecretFile $secretFile

        & $sevenZip `
            "x" `
            "-y" `
            "-p$passphrase" `
            "-o$tempDir" `
            $latest.FullName | Out-Null

        if ($LASTEXITCODE -ne 0) {
            throw "Could not decrypt/extract backup archive."
        }

        $sqlCandidate = Get-ChildItem `
            $tempDir `
            -Filter "*.sql" `
            -File |
            Select-Object -First 1

        if ($sqlCandidate) {
            $sqlFile = $sqlCandidate.FullName
        }
    }

    if (-not $sqlFile -or -not (Test-Path $sqlFile)) {
        throw "SQL file could not be prepared for restore verification."
    }

    # Older backups may contain SET @@GLOBAL.GTID_PURGED.
    # Restoring such a dump into the same MySQL server can fail because
    # those GTIDs already exist in @@GLOBAL.GTID_EXECUTED.
    # Create a temporary restore-only copy with that statement removed.
    $restoreSqlFile = Join-Path $tempDir "restore-safe.sql"

    $removedGtidStatements = New-GtidSafeRestoreCopy `
        -InputSqlFile $sqlFile `
        -OutputSqlFile $restoreSqlFile

    & $mysql `
        "--defaults-extra-file=$defaultsFile" `
        "-e" `
        "CREATE DATABASE ``$verificationDb`` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

    if ($LASTEXITCODE -ne 0) {
        throw "Could not create verification database."
    }

    $createdDb = $true

    Write-Host ""
    Write-Host "Restoring backup into temporary verification database..."
    Write-Host "Backup : $($latest.FullName)"
    Write-Host "Target : $verificationDb"

    if ($removedGtidStatements -gt 0) {
        Write-Host (
            "GTID   : removed $removedGtidStatements " +
            "GTID_PURGED statement(s) from temporary restore copy"
        )
    }
    else {
        Write-Host "GTID   : no GTID_PURGED statement found"
    }

    Write-Host ""

    $importResult = Invoke-MySqlFileImport `
        -MySqlExecutable $mysql `
        -DefaultsFile $defaultsFile `
        -DatabaseName $verificationDb `
        -SqlFile $restoreSqlFile `
        -TempDirectory $tempDir

    if ($importResult.ExitCode -ne 0) {
        $errorText = $importResult.StdErr.Trim()

        if ([string]::IsNullOrWhiteSpace($errorText)) {
            $errorText = "mysql returned no stderr details."
        }

        throw (
            "Restore verification import failed with exit code " +
            "$($importResult.ExitCode).`n`n" +
            "MYSQL ERROR:`n" +
            $errorText
        )
    }

    $query = (
        "SELECT COUNT(*) FROM information_schema.tables " +
        "WHERE table_schema='$verificationDb';"
    )

    $tableCount = & $mysql `
        "--defaults-extra-file=$defaultsFile" `
        "--batch" `
        "--skip-column-names" `
        "-e" `
        $query

    if ($LASTEXITCODE -ne 0) {
        throw "Could not verify restored table count."
    }

    $tableCountValue = [int]("$tableCount".Trim())

    if ($tableCountValue -lt 1) {
        throw "Restore completed but no tables were found."
    }

    Write-Host ""
    Write-Host "RESTORE VERIFICATION PASSED"
    Write-Host "==========================="
    Write-Host "Backup          : $($latest.FullName)"
    Write-Host "Verification DB : $verificationDb"
    Write-Host "Tables restored : $tableCountValue"
    Write-Host ""

    if ($KeepVerificationDatabase) {
        Write-Warning (
            "Verification database was kept because " +
            "-KeepVerificationDatabase was used."
        )
        $createdDb = $false
    }
}
finally {
    if ($createdDb) {
        & $mysql `
            "--defaults-extra-file=$defaultsFile" `
            "-e" `
            "DROP DATABASE IF EXISTS ``$verificationDb``;" | Out-Null
    }

    if (Test-Path $defaultsFile) {
        Remove-Item $defaultsFile -Force -ErrorAction SilentlyContinue
    }

    if (Test-Path $tempDir) {
        Remove-Item $tempDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}
