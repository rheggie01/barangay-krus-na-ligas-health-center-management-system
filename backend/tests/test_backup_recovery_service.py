import json
import subprocess
from types import SimpleNamespace

import pytest

from app.services import backup_recovery_service as service


def test_load_json_returns_none_when_file_is_missing(tmp_path):
    assert service._load_json(tmp_path / "missing.json") is None


def test_load_json_returns_none_for_invalid_json(tmp_path):
    path = tmp_path / "invalid.json"
    path.write_text("{not valid json", encoding="utf-8")
    assert service._load_json(path) is None


def test_parse_schtasks_value_extracts_value_and_normalizes_disabled():
    output = "Next Run Time: 09/06/2026 10:00:00 PM\nStatus: Ready\n"
    assert (
        service._parse_schtasks_value(output, "Next Run Time")
        == "09/06/2026 10:00:00 PM"
    )
    assert service._parse_schtasks_value("Next Run Time: N/A", "Next Run Time") is None


def test_parse_task_result_accepts_decimal_hex_and_rejects_invalid():
    assert service._parse_task_result("0") == 0
    assert service._parse_task_result("0x0") == 0
    assert service._parse_task_result("1") == 1
    assert service._parse_task_result("not-a-number") is None


def test_safe_file_summary_returns_only_name_size_and_encryption(tmp_path):
    path = tmp_path / "barangay_health_db_2026-09-06.7z"
    path.write_bytes(b"phase13")

    result = service._safe_file_summary(str(path), encrypted=True)

    assert result == {
        "file_name": path.name,
        "size_bytes": len(b"phase13"),
        "encrypted": True,
    }
    assert str(tmp_path) not in result["file_name"]


def test_count_backup_files_counts_only_sql_and_7z(monkeypatch, tmp_path):
    daily = tmp_path / "Daily"
    daily.mkdir()
    (daily / "one.sql").write_text("sql", encoding="utf-8")
    (daily / "two.7z").write_bytes(b"archive")
    (daily / "ignore.log").write_text("log", encoding="utf-8")
    monkeypatch.setattr(service, "BACKUP_ROOT", tmp_path)

    assert service._count_backup_files("Daily") == 2
    assert service._count_backup_files("Weekly") == 0


def test_status_contract_combines_settings_status_counts_and_access(monkeypatch, tmp_path):
    local_settings = tmp_path / "backup-settings.local.json"
    local_settings.write_text("{}", encoding="utf-8")
    example_settings = tmp_path / "backup-settings.example.json"
    example_settings.write_text("{}", encoding="utf-8")
    backup_status_file = tmp_path / "backup-status.json"
    restore_status_file = tmp_path / "restore-status.json"

    monkeypatch.setattr(service, "LOCAL_SETTINGS_FILE", local_settings)
    monkeypatch.setattr(service, "EXAMPLE_SETTINGS_FILE", example_settings)
    monkeypatch.setattr(service, "BACKUP_STATUS_FILE", backup_status_file)
    monkeypatch.setattr(service, "RESTORE_STATUS_FILE", restore_status_file)
    monkeypatch.setattr(
        service,
        "_settings",
        lambda: {
            "Encryption": {"Enabled": True},
            "Cloud": {"Enabled": True},
            "Retention": {"Daily": 7, "Weekly": 4, "Monthly": 6},
        },
    )

    def fake_load(path):
        if path == backup_status_file:
            return {
                "success": True,
                "database": "barangay_health_db",
                "finished_at": "2026-09-06T04:00:00+08:00",
                "duration_seconds": 2.5,
                "message": "Backup completed successfully.",
                "local_backup_path": str(tmp_path / "latest.7z"),
                "encrypted": True,
                "cloud_status": "COPIED",
            }
        if path == restore_status_file:
            return {
                "success": True,
                "finished_at": "2026-09-06T03:00:00+08:00",
                "message": "Restore verification passed.",
            }
        return None

    monkeypatch.setattr(service, "_load_json", fake_load)
    monkeypatch.setattr(
        service,
        "_count_backup_files",
        lambda name: {"Daily": 7, "Weekly": 4, "Monthly": 2}[name],
    )
    monkeypatch.setattr(
        service,
        "_scheduled_task_info",
        lambda: {
            "installed": True,
            "next_run_time": "09/06/2026 10:00:00 PM",
            "last_run_time": "09/05/2026 10:00:00 PM",
            "last_task_result": 0,
            "healthy": True,
        },
    )

    result = service.get_backup_recovery_status(
        viewer_can_run_actions=False
    )

    assert result["backup_configured"] is True
    assert result["backup_success"] is True
    assert result["database"] == "barangay_health_db"
    assert result["latest_backup"]["file_name"] == "latest.7z"
    assert result["cloud_status"] == "COPIED"
    assert result["encryption_enabled"] is True
    assert result["retention"]["daily_keep"] == 7
    assert result["retention"]["monthly_count"] == 2
    assert result["scheduled_task"]["healthy"] is True
    assert result["restore_test"]["success"] is True
    assert result["viewer_can_run_actions"] is False


def test_run_backup_now_returns_success_for_zero_exit(monkeypatch):
    monkeypatch.setattr(
        service,
        "_run_fixed_script",
        lambda *_args, **_kwargs: subprocess.CompletedProcess(
            args=["powershell"], returncode=0, stdout="ok", stderr=""
        ),
    )

    assert service.run_backup_now() == {
        "success": True,
        "message": "Database backup completed.",
    }


def test_run_backup_now_raises_script_error_on_failure(monkeypatch):
    monkeypatch.setattr(
        service,
        "_run_fixed_script",
        lambda *_args, **_kwargs: subprocess.CompletedProcess(
            args=["powershell"],
            returncode=1,
            stdout="",
            stderr="synthetic dump failure",
        ),
    )

    with pytest.raises(RuntimeError, match="synthetic dump failure"):
        service.run_backup_now()


def test_run_restore_test_success_writes_status_file(monkeypatch, tmp_path):
    status_dir = tmp_path / "Status"
    status_file = status_dir / "restore-test-status.json"
    monkeypatch.setattr(service, "STATUS_DIR", status_dir)
    monkeypatch.setattr(service, "RESTORE_STATUS_FILE", status_file)
    monkeypatch.setattr(
        service,
        "_run_fixed_script",
        lambda *_args, **_kwargs: subprocess.CompletedProcess(
            args=["powershell"],
            returncode=0,
            stdout="19 tables restored",
            stderr="",
        ),
    )

    result = service.run_restore_test()
    payload = json.loads(status_file.read_text(encoding="utf-8"))

    assert result["success"] is True
    assert result["message"] == "Restore verification passed."
    assert "19 tables restored" in result["output"]
    assert payload["success"] is True
    assert payload["message"] == "Restore verification passed."


def test_run_restore_test_failure_writes_status_before_raising(monkeypatch, tmp_path):
    status_dir = tmp_path / "Status"
    status_file = status_dir / "restore-test-status.json"
    monkeypatch.setattr(service, "STATUS_DIR", status_dir)
    monkeypatch.setattr(service, "RESTORE_STATUS_FILE", status_file)
    monkeypatch.setattr(
        service,
        "_run_fixed_script",
        lambda *_args, **_kwargs: subprocess.CompletedProcess(
            args=["powershell"],
            returncode=1,
            stdout="",
            stderr="synthetic restore failure",
        ),
    )

    with pytest.raises(RuntimeError, match="synthetic restore failure"):
        service.run_restore_test()

    payload = json.loads(status_file.read_text(encoding="utf-8"))
    assert payload["success"] is False
    assert payload["message"] == "synthetic restore failure"


def test_scheduled_task_info_is_safe_on_non_windows(monkeypatch):
    monkeypatch.setattr(service, "os", SimpleNamespace(name="posix"))

    assert service._scheduled_task_info() == {
        "installed": False,
        "next_run_time": None,
        "last_run_time": None,
        "last_task_result": None,
        "healthy": False,
    }
