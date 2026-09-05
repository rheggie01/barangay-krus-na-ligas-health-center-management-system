from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.api.v1.endpoints import backup_recovery


class FakeSession:
    def __init__(self):
        self.commit_count = 0
        self.rollback_count = 0

    def commit(self):
        self.commit_count += 1

    def rollback(self):
        self.rollback_count += 1


def make_user(*role_names):
    return SimpleNamespace(
        id=42,
        username="phase13.backup",
        roles=[SimpleNamespace(name=name) for name in role_names],
    )


def request(path="/api/v1/backup-recovery/run-backup"):
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": path,
            "headers": [],
            "client": ("127.0.0.1", 50000),
            "server": ("testserver", 80),
            "scheme": "http",
            "query_string": b"",
        }
    )


def test_role_names_collects_all_assigned_roles():
    user = make_user("SYSTEM_ADMIN", "DOCTOR")
    assert backup_recovery._role_names(user) == {
        "SYSTEM_ADMIN",
        "DOCTOR",
    }


def test_system_admin_can_view_backup_status():
    backup_recovery._require_view_access(make_user("SYSTEM_ADMIN"))


def test_health_center_admin_can_view_backup_status():
    backup_recovery._require_view_access(
        make_user("HEALTH_CENTER_ADMIN")
    )


def test_clinical_role_cannot_view_backup_status():
    with pytest.raises(HTTPException) as exc:
        backup_recovery._require_view_access(make_user("NURSE"))
    assert exc.value.status_code == 403


def test_system_admin_can_run_backup_actions():
    backup_recovery._require_action_access(make_user("SYSTEM_ADMIN"))


def test_health_center_admin_is_view_only_for_backup_actions():
    with pytest.raises(HTTPException) as exc:
        backup_recovery._require_action_access(
            make_user("HEALTH_CENTER_ADMIN")
        )
    assert exc.value.status_code == 403
    assert "System Administrator" in exc.value.detail


def test_status_marks_system_admin_as_action_capable(monkeypatch):
    calls = []
    monkeypatch.setattr(
        backup_recovery,
        "get_backup_recovery_status",
        lambda **kwargs: calls.append(kwargs) or {"ok": True},
    )

    result = backup_recovery.backup_recovery_status(
        current_user=make_user("SYSTEM_ADMIN")
    )

    assert result == {"ok": True}
    assert calls == [{"viewer_can_run_actions": True}]


def test_status_marks_health_center_admin_as_view_only(monkeypatch):
    calls = []
    monkeypatch.setattr(
        backup_recovery,
        "get_backup_recovery_status",
        lambda **kwargs: calls.append(kwargs) or {"ok": True},
    )

    result = backup_recovery.backup_recovery_status(
        current_user=make_user("HEALTH_CENTER_ADMIN")
    )

    assert result == {"ok": True}
    assert calls == [{"viewer_can_run_actions": False}]


def test_manual_backup_success_is_audited_and_committed(monkeypatch):
    db = FakeSession()
    audits = []
    expected = {"success": True, "message": "Database backup completed."}
    monkeypatch.setattr(backup_recovery, "run_backup_now", lambda: expected)
    monkeypatch.setattr(
        backup_recovery,
        "get_request_ip",
        lambda _request: "127.0.0.1",
    )
    monkeypatch.setattr(
        backup_recovery,
        "create_audit_log",
        lambda _db, **kwargs: audits.append(kwargs),
    )

    result = backup_recovery.run_backup(
        request=request(),
        db=db,
        current_user=make_user("SYSTEM_ADMIN"),
    )

    assert result == expected
    assert db.commit_count == 1
    assert db.rollback_count == 0
    assert audits[0]["action"] == "BACKUP_RUN_MANUAL"
    assert audits[0]["module"] == "BACKUP_RECOVERY"


def test_manual_backup_failure_rolls_back_and_writes_failure_audit(monkeypatch):
    db = FakeSession()
    audits = []

    def fail_backup():
        raise RuntimeError("synthetic backup failure")

    monkeypatch.setattr(backup_recovery, "run_backup_now", fail_backup)
    monkeypatch.setattr(
        backup_recovery,
        "get_request_ip",
        lambda _request: "127.0.0.1",
    )
    monkeypatch.setattr(
        backup_recovery,
        "create_audit_log",
        lambda _db, **kwargs: audits.append(kwargs),
    )

    with pytest.raises(HTTPException) as exc:
        backup_recovery.run_backup(
            request=request(),
            db=db,
            current_user=make_user("SYSTEM_ADMIN"),
        )

    assert exc.value.status_code == 500
    assert "synthetic backup failure" in exc.value.detail
    assert db.rollback_count == 1
    assert db.commit_count == 1
    assert audits[0]["action"] == "BACKUP_RUN_MANUAL_FAILED"


def test_restore_verification_success_is_audited_and_committed(monkeypatch):
    db = FakeSession()
    audits = []
    expected = {"success": True, "message": "Restore verification passed."}
    monkeypatch.setattr(backup_recovery, "run_restore_test", lambda: expected)
    monkeypatch.setattr(
        backup_recovery,
        "get_request_ip",
        lambda _request: "127.0.0.1",
    )
    monkeypatch.setattr(
        backup_recovery,
        "create_audit_log",
        lambda _db, **kwargs: audits.append(kwargs),
    )

    result = backup_recovery.run_restore_verification(
        request=request("/api/v1/backup-recovery/run-restore-test"),
        db=db,
        current_user=make_user("SYSTEM_ADMIN"),
    )

    assert result == expected
    assert db.commit_count == 1
    assert db.rollback_count == 0
    assert audits[0]["action"] == "BACKUP_RESTORE_TEST"
    assert audits[0]["module"] == "BACKUP_RECOVERY"


def test_restore_verification_failure_rolls_back_and_audits(monkeypatch):
    db = FakeSession()
    audits = []

    def fail_restore():
        raise RuntimeError("synthetic restore failure")

    monkeypatch.setattr(backup_recovery, "run_restore_test", fail_restore)
    monkeypatch.setattr(
        backup_recovery,
        "get_request_ip",
        lambda _request: "127.0.0.1",
    )
    monkeypatch.setattr(
        backup_recovery,
        "create_audit_log",
        lambda _db, **kwargs: audits.append(kwargs),
    )

    with pytest.raises(HTTPException) as exc:
        backup_recovery.run_restore_verification(
            request=request("/api/v1/backup-recovery/run-restore-test"),
            db=db,
            current_user=make_user("SYSTEM_ADMIN"),
        )

    assert exc.value.status_code == 500
    assert "synthetic restore failure" in exc.value.detail
    assert db.rollback_count == 1
    assert db.commit_count == 1
    assert audits[0]["action"] == "BACKUP_RESTORE_TEST_FAILED"
