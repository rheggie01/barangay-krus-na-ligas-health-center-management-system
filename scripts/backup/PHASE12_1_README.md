
# Phase 12.1 — Encrypted + Off-Device Backup

This helper configures the Phase 12 backup scripts to create encrypted `.7z`
archives and optionally copy them to an approved synced/off-device folder.

## Requirements

- Working Phase 12 local backup
- 7-Zip
- An approved synchronized/off-device folder if cloud copy is enabled

## OneDrive Auto-Detection

The configuration helper checks these Windows environment variables in this
order:

1. `OneDriveCommercial`
2. `OneDrive`
3. `OneDriveConsumer`

When found, it creates:

```text
<OneDrive>\BarangayHealthCenterBackups
```

For operational health-center data, use an organization-authorized OneDrive
or other approved storage location. Do not use a personal cloud account for
real patient information.

## Configure

```powershell
.\scripts\backup\Configure-EncryptedCloudBackup.ps1
```

If 7-Zip is missing:

```powershell
.\scripts\backup\Configure-EncryptedCloudBackup.ps1 -InstallSevenZip
```

Use a specific approved path:

```powershell
.\scripts\backup\Configure-EncryptedCloudBackup.ps1 `
    -CloudPath "D:\AuthorizedHealthCenterBackupSync"
```

Encryption only:

```powershell
.\scripts\backup\Configure-EncryptedCloudBackup.ps1 -SkipCloud
```

The script will prompt for a backup encryption passphrase.

Keep a separate authorized offline recovery copy of that passphrase. The
DPAPI-protected local secret is machine-protected and must not be treated as
the only disaster-recovery copy.

## Verify

```powershell
.\scripts\backup\Test-EncryptedCloudBackup.ps1
```

The test verifies:

- encrypted `.7z` creation
- local archive existence
- cloud copy when enabled
- encrypted archive restore into a temporary verification database

The existing scheduled task automatically uses the updated local settings on
its next run. Reinstalling the scheduled task is not required just to enable
encryption/cloud copy.
