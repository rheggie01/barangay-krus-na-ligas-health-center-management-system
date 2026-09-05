from __future__ import annotations

from datetime import datetime
import json
import os
from pathlib import Path
import re
import subprocess
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[3]

BACKUP_ROOT = PROJECT_ROOT / "database_backups"
STATUS_DIR = BACKUP_ROOT / "Status"
BACKUP_STATUS_FILE = STATUS_DIR / "backup-status.json"
RESTORE_STATUS_FILE = STATUS_DIR / "restore-test-status.json"

BACKUP_SCRIPT = (
    PROJECT_ROOT
    / "scripts"
    / "backup"
    / "Invoke-DatabaseBackup.ps1"
)

RESTORE_TEST_SCRIPT = (
    PROJECT_ROOT
    / "scripts"
    / "backup"
    / "Test-DatabaseBackup.ps1"
)

LOCAL_SETTINGS_FILE = (
    PROJECT_ROOT
    / "scripts"
    / "backup"
    / "backup-settings.local.json"
)

EXAMPLE_SETTINGS_FILE = (
    PROJECT_ROOT
    / "scripts"
    / "backup"
    / "backup-settings.example.json"
)


def _load_json(
    path: Path,
) -> dict[str, Any] | None:
    if not path.exists():
        return None

    try:
        return json.loads(
            path.read_text(
                encoding="utf-8-sig",
            )
        )
    except (
        OSError,
        UnicodeDecodeError,
        json.JSONDecodeError,
    ):
        return None


def _settings() -> dict[str, Any]:
    return (
        _load_json(LOCAL_SETTINGS_FILE)
        or _load_json(EXAMPLE_SETTINGS_FILE)
        or {}
    )


def _count_backup_files(
    folder_name: str,
) -> int:
    folder = BACKUP_ROOT / folder_name

    if not folder.exists():
        return 0

    return sum(
        1
        for path in folder.iterdir()
        if (
            path.is_file()
            and path.suffix.lower()
            in {".sql", ".7z"}
        )
    )


def _safe_file_summary(
    path_value: str | None,
    encrypted: bool,
) -> dict[str, Any]:
    if not path_value:
        return {
            "file_name": None,
            "size_bytes": 0,
            "encrypted": encrypted,
        }

    path = Path(path_value)

    try:
        size = path.stat().st_size
    except OSError:
        size = 0

    return {
        "file_name": path.name,
        "size_bytes": size,
        "encrypted": encrypted,
    }


def _parse_schtasks_value(
    output: str,
    label: str,
) -> str | None:
    pattern = re.compile(
        rf"^{re.escape(label)}\s*:\s*(.+)$",
        re.IGNORECASE | re.MULTILINE,
    )

    match = pattern.search(output)

    if not match:
        return None

    value = match.group(1).strip()

    if value.lower() in {
        "n/a",
        "disabled",
        "never",
    }:
        return None

    return value


def _parse_task_result(
    value: str | None,
) -> int | None:
    if not value:
        return None

    cleaned = value.strip()

    try:
        return int(
            cleaned,
            0,
        )
    except ValueError:
        return None


def _scheduled_task_info() -> dict[str, Any]:
    if os.name != "nt":
        return {
            "installed": False,
            "next_run_time": None,
            "last_run_time": None,
            "last_task_result": None,
            "healthy": False,
        }

    task_full_name = (
        r"\BarangayHealthSystem"
        r"\Nightly Database Backup"
    )

    try:
        completed = subprocess.run(
            [
                "schtasks.exe",
                "/Query",
                "/TN",
                task_full_name,
                "/V",
                "/FO",
                "LIST",
            ],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )

        if completed.returncode != 0:
            return {
                "installed": False,
                "next_run_time": None,
                "last_run_time": None,
                "last_task_result": None,
                "healthy": False,
            }

        output = completed.stdout

        next_run = _parse_schtasks_value(
            output,
            "Next Run Time",
        )

        last_run = _parse_schtasks_value(
            output,
            "Last Run Time",
        )

        last_result = _parse_task_result(
            _parse_schtasks_value(
                output,
                "Last Result",
            )
        )

        backup_status = (
            _load_json(
                BACKUP_STATUS_FILE
            )
            or {}
        )

        latest_backup_success = (
            backup_status.get("success")
            is True
        )

        healthy = (
            last_result == 0
            or (
                last_result is None
                and latest_backup_success
            )
        )

        return {
            "installed": True,
            "next_run_time": next_run,
            "last_run_time": (
                last_run
                or backup_status.get(
                    "finished_at"
                )
            ),
            "last_task_result": (
                last_result
                if last_result is not None
                else (
                    0
                    if latest_backup_success
                    else None
                )
            ),
            "healthy": healthy,
        }

    except (
        OSError,
        subprocess.SubprocessError,
    ):
        return {
            "installed": False,
            "next_run_time": None,
            "last_run_time": None,
            "last_task_result": None,
            "healthy": False,
        }


def get_backup_recovery_status(
    *,
    viewer_can_run_actions: bool,
) -> dict[str, Any]:
    settings = _settings()
    backup_status = (
        _load_json(
            BACKUP_STATUS_FILE
        )
        or {}
    )
    restore_status = (
        _load_json(
            RESTORE_STATUS_FILE
        )
        or {}
    )

    encryption = settings.get(
        "Encryption",
        {},
    )
    cloud = settings.get(
        "Cloud",
        {},
    )
    retention = settings.get(
        "Retention",
        {},
    )

    encrypted = bool(
        backup_status.get(
            "encrypted",
            encryption.get(
                "Enabled",
                False,
            ),
        )
    )

    return {
        "backup_configured": (
            LOCAL_SETTINGS_FILE.exists()
            or EXAMPLE_SETTINGS_FILE.exists()
        ),
        "backup_success": (
            backup_status.get(
                "success"
            )
        ),
        "database": (
            backup_status.get(
                "database"
            )
        ),
        "finished_at": (
            backup_status.get(
                "finished_at"
            )
        ),
        "duration_seconds": (
            backup_status.get(
                "duration_seconds"
            )
        ),
        "message": (
            backup_status.get(
                "message"
            )
        ),
        "latest_backup": (
            _safe_file_summary(
                backup_status.get(
                    "local_backup_path"
                ),
                encrypted,
            )
        ),
        "cloud_enabled": bool(
            cloud.get(
                "Enabled",
                False,
            )
        ),
        "cloud_status": str(
            backup_status.get(
                "cloud_status",
                "DISABLED",
            )
        ),
        "encryption_enabled": bool(
            encryption.get(
                "Enabled",
                False,
            )
        ),
        "retention": {
            "daily_keep": int(
                retention.get(
                    "Daily",
                    0,
                )
                or 0
            ),
            "weekly_keep": int(
                retention.get(
                    "Weekly",
                    0,
                )
                or 0
            ),
            "monthly_keep": int(
                retention.get(
                    "Monthly",
                    0,
                )
                or 0
            ),
            "daily_count": (
                _count_backup_files(
                    "Daily"
                )
            ),
            "weekly_count": (
                _count_backup_files(
                    "Weekly"
                )
            ),
            "monthly_count": (
                _count_backup_files(
                    "Monthly"
                )
            ),
        },
        "scheduled_task": (
            _scheduled_task_info()
        ),
        "restore_test": {
            "available": bool(
                restore_status
            ),
            "success": (
                restore_status.get(
                    "success"
                )
            ),
            "finished_at": (
                restore_status.get(
                    "finished_at"
                )
            ),
            "message": (
                restore_status.get(
                    "message"
                )
            ),
        },
        "viewer_can_run_actions": (
            viewer_can_run_actions
        ),
    }


def _run_fixed_script(
    script_path: Path,
    *,
    timeout_seconds: int,
) -> subprocess.CompletedProcess[str]:
    if os.name != "nt":
        raise RuntimeError(
            "Backup operations are only "
            "supported on the Windows "
            "deployment computer."
        )

    if not script_path.exists():
        raise RuntimeError(
            "Required backup script "
            f"not found: {script_path.name}"
        )

    return subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script_path),
        ],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )


def run_backup_now() -> dict[str, Any]:
    completed = _run_fixed_script(
        BACKUP_SCRIPT,
        timeout_seconds=180,
    )

    if completed.returncode != 0:
        detail = (
            completed.stderr.strip()
            or completed.stdout.strip()
            or "Backup script failed."
        )

        raise RuntimeError(detail)

    return {
        "success": True,
        "message": (
            "Database backup completed."
        ),
    }


def run_restore_test() -> dict[str, Any]:
    STATUS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    completed = _run_fixed_script(
        RESTORE_TEST_SCRIPT,
        timeout_seconds=300,
    )

    success = (
        completed.returncode == 0
    )

    output = (
        completed.stdout.strip()
        or completed.stderr.strip()
    )

    message = (
        "Restore verification passed."
        if success
        else (
            completed.stderr.strip()
            or completed.stdout.strip()
            or "Restore verification failed."
        )
    )

    payload = {
        "success": success,
        "finished_at": (
            datetime.now()
            .astimezone()
            .isoformat()
        ),
        "message": message,
    }

    RESTORE_STATUS_FILE.write_text(
        json.dumps(
            payload,
            indent=2,
        ),
        encoding="utf-8",
    )

    if not success:
        raise RuntimeError(message)

    return {
        "success": True,
        "message": message,
        "output": output,
    }
