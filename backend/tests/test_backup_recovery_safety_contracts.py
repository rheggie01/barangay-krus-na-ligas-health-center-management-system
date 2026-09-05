from pathlib import Path

from app.schemas.backup_recovery import BackupRecoveryStatus


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESTORE_SCRIPT = PROJECT_ROOT / "scripts" / "backup" / "Test-DatabaseBackup.ps1"
BACKUP_SCRIPT = PROJECT_ROOT / "scripts" / "backup" / "Invoke-DatabaseBackup.ps1"


def status_payload():
    return {
        "backup_configured": True,
        "backup_success": True,
        "database": "barangay_health_db",
        "finished_at": "2026-09-06T04:00:00+08:00",
        "duration_seconds": 2.25,
        "message": "Backup completed successfully.",
        "latest_backup": {
            "file_name": "barangay_health_db_2026-09-06.7z",
            "size_bytes": 12345,
            "encrypted": True,
        },
        "cloud_enabled": True,
        "cloud_status": "COPIED",
        "encryption_enabled": True,
        "retention": {
            "daily_keep": 7,
            "weekly_keep": 4,
            "monthly_keep": 6,
            "daily_count": 7,
            "weekly_count": 4,
            "monthly_count": 2,
        },
        "scheduled_task": {
            "installed": True,
            "next_run_time": "09/06/2026 10:00:00 PM",
            "last_run_time": "09/05/2026 10:00:00 PM",
            "last_task_result": 0,
            "healthy": True,
        },
        "restore_test": {
            "available": True,
            "success": True,
            "finished_at": "2026-09-06T03:00:00+08:00",
            "message": "Restore verification passed.",
        },
        "viewer_can_run_actions": False,
    }


def test_backup_recovery_status_schema_accepts_complete_contract():
    model = BackupRecoveryStatus(**status_payload())
    assert model.database == "barangay_health_db"
    assert model.latest_backup.encrypted is True
    assert model.scheduled_task.healthy is True
    assert model.restore_test.success is True


def test_backup_recovery_status_preserves_view_only_capability_flag():
    payload = status_payload()
    payload["viewer_can_run_actions"] = False
    assert BackupRecoveryStatus(**payload).viewer_can_run_actions is False
    payload["viewer_can_run_actions"] = True
    assert BackupRecoveryStatus(**payload).viewer_can_run_actions is True


def test_restore_verifier_uses_generated_temporary_database_name():
    script = RESTORE_SCRIPT.read_text(encoding="utf-8").lower()
    assert '"backup_verify_"' in script
    assert "$verificationdb" in script


def test_restore_import_targets_verification_database_not_live_database():
    script = RESTORE_SCRIPT.read_text(encoding="utf-8").lower()
    assert "-databasename $verificationdb" in script
    assert "-databasename $db.name" not in script


def test_restore_verifier_drops_temporary_database_in_finally():
    script = RESTORE_SCRIPT.read_text(encoding="utf-8").lower()
    assert "finally {" in script
    assert "drop database if exists ``$verificationdb``;" in script


def test_restore_verifier_cleans_temporary_credentials_and_files():
    script = RESTORE_SCRIPT.read_text(encoding="utf-8").lower()
    assert "remove-item $defaultsfile" in script
    assert "remove-item $tempdir -recurse" in script


def test_database_backup_uses_transactional_gtid_safe_dump_options():
    script = BACKUP_SCRIPT.read_text(encoding="utf-8")
    assert '"--single-transaction"' in script
    assert '"--set-gtid-purged=OFF"' in script


def test_cloud_copy_has_unencrypted_backup_safety_gate():
    script = BACKUP_SCRIPT.read_text(encoding="utf-8")
    assert "AllowUnencryptedCopy" in script
    assert "Cloud copy blocked: encryption is disabled" in script
