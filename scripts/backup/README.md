# Automated Database Backup & Recovery

Phase 12 adds unattended MySQL backup tooling for the Barangay Health Center Management System.

## Default Behavior

- Daily backup at `22:00` after the scheduled task is installed
- 7 daily backups retained
- 4 weekly backups retained
- 6 monthly backups retained
- MySQL transaction-safe dump using `--single-transaction`
- backup success/failure logs
- machine-readable backup status JSON
- optional 7-Zip AES archive encryption
- optional copy to a synced/cloud or off-device folder
- restore verification into a temporary database

## Important

The application source code is protected by Git/GitHub.

The MySQL database is separate and must be backed up independently.

For real patient data, do not enable unencrypted cloud copy. Use an authorized storage location and encryption approved for the deployment.

## Quick Start

From the project root:

```powershell
Set-ExecutionPolicy -Scope Process Bypass

.\scripts\backup\Initialize-BackupSettings.ps1

.\scripts\backup\Invoke-DatabaseBackup.ps1

.\scripts\backup\Get-BackupStatus.ps1
```

## Install Automatic Nightly Backup

Open PowerShell **as Administrator**:

```powershell
cd C:\Users\PC\Desktop\barangay-health-system
Set-ExecutionPolicy -Scope Process Bypass

.\scripts\backup\Install-BackupTask.ps1
```

Default schedule is `22:00`.

Custom example:

```powershell
.\scripts\backup\Install-BackupTask.ps1 -BackupTime "21:30"
```

## Encryption

Encryption requires 7-Zip.

1. Install 7-Zip.
2. Create the local settings file.
3. Change:

```json
"Encryption": {
  "Enabled": true
}
```

4. Initialize the secret:

```powershell
.\scripts\backup\Initialize-BackupEncryption.ps1
```

The encryption secret is protected with Windows DPAPI and stored inside `database_backups/`, which is ignored by Git.

**Disaster-recovery requirement:** keep the actual passphrase in a separate authorized offline record. A DPAPI secret file from the destroyed computer may not be usable on another computer.

## Cloud / Off-Device Copy

Set a local path that is synchronized or backed up by the approved provider:

```json
"Cloud": {
  "Enabled": true,
  "Path": "D:\\AuthorizedHealthCenterBackupSync",
  "AllowUnencryptedCopy": false
}
```

When cloud copy is enabled, the script blocks unencrypted cloud copy unless `AllowUnencryptedCopy` is explicitly enabled.

For actual health-center data, keep `AllowUnencryptedCopy` set to `false`.

## Restore Verification

Periodically test whether the newest backup can actually be restored:

```powershell
.\scripts\backup\Test-DatabaseBackup.ps1
```

This:

1. creates a temporary MySQL database,
2. restores the newest daily backup,
3. checks that tables exist,
4. drops the temporary verification database.

It does not overwrite the live database.

## Status

```powershell
.\scripts\backup\Get-BackupStatus.ps1
```

Status file:

```text
database_backups/Status/backup-status.json
```

Logs:

```text
database_backups/Logs/
```

## Brownout / Power Failure

Backups protect against data loss but do not replace a UPS.

Recommended deployment:

- UPS for the health-center server/main PC
- MySQL transactional storage
- Windows automatic startup
- MySQL automatic service startup
- nightly automated backup
- off-device encrypted copy
- periodic restore verification

If the PC is off at the scheduled backup time, the installed Windows task uses `StartWhenAvailable`, allowing Windows to run it after the machine becomes available again.
