# Phase 13.5 — Backup & Recovery Authorization and Operational Tests

This phase adds regression tests for the backup/recovery administrative surface introduced in Phase 12.

## Scope

- `SYSTEM_ADMIN` may view status and run manual backup/restore-verification actions.
- `HEALTH_CENTER_ADMIN` may view backup/recovery status but cannot run actions.
- Clinical/non-administrative roles are denied backup/recovery status access.
- Successful and failed manual backup operations preserve their audit intents.
- Successful and failed restore-verification operations preserve their audit intents.
- Backup status parsing remains defensive when files/task metadata are absent or malformed.
- Restore verification writes status on both success and failure.
- Restore verification targets a generated `backup_verify_*` database, not the live application database.
- Temporary verification databases, temporary credentials, and temporary restore files are cleaned up.
- Database dumps preserve `--single-transaction` and `--set-gtid-purged=OFF` safety options.
- Cloud copy remains blocked when encryption is disabled unless explicitly allowed by configuration.

## Safety

These automated tests do **not** execute a real MySQL backup, restore, Windows Scheduled Task, or live database mutation. External scripts/processes are mocked for unit tests, while PowerShell safety properties are checked as static regression contracts.

The existing operational restore test remains the separate end-to-end verification of an actual encrypted backup restore into a disposable temporary database.
