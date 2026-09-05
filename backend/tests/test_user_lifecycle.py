from types import SimpleNamespace

import pytest

from app.services import user_service


class FakeSession:
    def __init__(self):
        self.flush_count = 0
        self.deleted = []

    def flush(self):
        self.flush_count += 1

    def delete(self, user):
        self.deleted.append(user)


def actor():
    return SimpleNamespace(
        id=99,
        first_name="System",
        last_name="Administrator",
        roles=[],
    )


def account(status, *, user_id=20):
    return SimpleNamespace(
        id=user_id,
        account_status=status,
        is_active=(status == user_service.ACCOUNT_ACTIVE),
        status_changed_at=None,
        status_changed_by=None,
        status_changed_by_name_snapshot=None,
        status_changed_by_role_snapshot=None,
    )


def install_snapshot(monkeypatch):
    monkeypatch.setattr(
        user_service,
        "snapshot_user",
        lambda _user: {
            "display_name": "System Administrator",
            "role_names": "SYSTEM_ADMIN",
        },
    )


def test_pending_account_can_be_approved(monkeypatch):
    install_snapshot(monkeypatch)
    db = FakeSession()
    user = account(user_service.ACCOUNT_PENDING)

    result = user_service.transition_user_account(
        db,
        user=user,
        new_status=user_service.ACCOUNT_ACTIVE,
        changed_by=actor(),
    )

    assert result is user
    assert user.account_status == user_service.ACCOUNT_ACTIVE
    assert user.is_active is True
    assert user.status_changed_by == 99
    assert user.status_changed_by_name_snapshot == "System Administrator"
    assert user.status_changed_by_role_snapshot == "SYSTEM_ADMIN"
    assert user.status_changed_at is not None
    assert db.flush_count == 1


def test_active_account_can_be_deactivated(monkeypatch):
    install_snapshot(monkeypatch)
    db = FakeSession()
    user = account(user_service.ACCOUNT_ACTIVE)

    user_service.transition_user_account(
        db,
        user=user,
        new_status=user_service.ACCOUNT_INACTIVE,
        changed_by=actor(),
    )

    assert user.account_status == user_service.ACCOUNT_INACTIVE
    assert user.is_active is False
    assert db.flush_count == 1


def test_inactive_account_can_be_reactivated(monkeypatch):
    install_snapshot(monkeypatch)
    db = FakeSession()
    user = account(user_service.ACCOUNT_INACTIVE)

    user_service.transition_user_account(
        db,
        user=user,
        new_status=user_service.ACCOUNT_ACTIVE,
        changed_by=actor(),
    )

    assert user.account_status == user_service.ACCOUNT_ACTIVE
    assert user.is_active is True
    assert db.flush_count == 1


def test_invalid_lifecycle_transition_is_rejected(monkeypatch):
    install_snapshot(monkeypatch)
    db = FakeSession()
    user = account(user_service.ACCOUNT_PENDING)

    with pytest.raises(ValueError, match="Invalid account lifecycle transition"):
        user_service.transition_user_account(
            db,
            user=user,
            new_status=user_service.ACCOUNT_INACTIVE,
            changed_by=actor(),
        )

    assert db.flush_count == 0


def test_same_lifecycle_status_is_idempotent(monkeypatch):
    install_snapshot(monkeypatch)
    db = FakeSession()
    user = account(user_service.ACCOUNT_ACTIVE)

    result = user_service.transition_user_account(
        db,
        user=user,
        new_status=user_service.ACCOUNT_ACTIVE,
        changed_by=actor(),
    )

    assert result is user
    assert db.flush_count == 0


def test_only_pending_accounts_can_be_hard_deleted(monkeypatch):
    db = FakeSession()
    user = account(user_service.ACCOUNT_ACTIVE)
    monkeypatch.setattr(
        user_service,
        "get_user_reference_counts",
        lambda *_args: {},
    )

    with pytest.raises(ValueError, match="Only never-approved PENDING"):
        user_service.delete_pending_user(db, user)

    assert db.deleted == []


def test_pending_account_with_operational_reference_cannot_be_deleted(
    monkeypatch,
):
    db = FakeSession()
    user = account(user_service.ACCOUNT_PENDING)
    monkeypatch.setattr(
        user_service,
        "get_user_reference_counts",
        lambda *_args: {"audit_logs_as_actor": 1},
    )

    with pytest.raises(ValueError, match="cannot be hard-deleted"):
        user_service.delete_pending_user(db, user)

    assert db.deleted == []


def test_unreferenced_pending_account_can_be_deleted(monkeypatch):
    db = FakeSession()
    user = account(user_service.ACCOUNT_PENDING)
    monkeypatch.setattr(
        user_service,
        "get_user_reference_counts",
        lambda *_args: {
            "consultations": 0,
            "consultation_medicines": 0,
            "inventory_transactions": 0,
            "disease_cases_recorded": 0,
            "disease_cases_validated": 0,
            "patient_histories": 0,
            "audit_logs_as_actor": 0,
        },
    )

    user_service.delete_pending_user(db, user)

    assert db.deleted == [user]
    assert db.flush_count == 1
