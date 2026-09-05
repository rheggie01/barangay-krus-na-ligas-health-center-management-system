from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.api.v1.endpoints import users


class FakeField:
    def __eq__(self, _other):
        return self

    def is_(self, _value):
        return self


class FakeQuery:
    def join(self, *_args, **_kwargs):
        return self

    def where(self, *_args, **_kwargs):
        return self


class FakeFunc:
    @staticmethod
    def count(_value):
        return object()


class CountSession:
    def __init__(self, count):
        self.count = count
        self.scalar_calls = 0

    def scalar(self, _statement):
        self.scalar_calls += 1
        return self.count


class DummyUserModel:
    id = FakeField()
    roles = FakeField()
    account_status = FakeField()
    is_active = FakeField()


class DummyRoleModel:
    name = FakeField()


def install_fake_query_layer(monkeypatch):
    monkeypatch.setattr(users, "User", DummyUserModel)
    monkeypatch.setattr(users, "Role", DummyRoleModel)
    monkeypatch.setattr(users, "func", FakeFunc())
    monkeypatch.setattr(
        users,
        "select",
        lambda *_args, **_kwargs: FakeQuery(),
    )


def test_last_active_system_admin_cannot_be_deactivated(monkeypatch):
    install_fake_query_layer(monkeypatch)
    db = CountSession(count=1)
    target = SimpleNamespace(
        roles=[SimpleNamespace(name="SYSTEM_ADMIN")]
    )

    with pytest.raises(HTTPException) as exc:
        users._protect_last_system_admin(db, target)

    assert exc.value.status_code == 400
    assert "last active System Administrator" in exc.value.detail
    assert db.scalar_calls == 1


def test_system_admin_can_be_deactivated_when_another_active_admin_exists(
    monkeypatch,
):
    install_fake_query_layer(monkeypatch)
    db = CountSession(count=2)
    target = SimpleNamespace(
        roles=[SimpleNamespace(name="SYSTEM_ADMIN")]
    )

    users._protect_last_system_admin(db, target)

    assert db.scalar_calls == 1


def test_non_system_admin_skips_last_admin_count(monkeypatch):
    install_fake_query_layer(monkeypatch)
    db = CountSession(count=1)
    target = SimpleNamespace(
        roles=[SimpleNamespace(name="DOCTOR")]
    )

    users._protect_last_system_admin(db, target)

    assert db.scalar_calls == 0


def test_user_cannot_deactivate_own_account(monkeypatch):
    target = SimpleNamespace(id=55)
    current_user = SimpleNamespace(id=55)
    monkeypatch.setattr(
        users,
        "_require_target_user",
        lambda _db, _user_id: target,
    )

    with pytest.raises(HTTPException) as exc:
        users.deactivate_user(
            user_id=55,
            request=None,
            db=object(),
            current_user=current_user,
        )

    assert exc.value.status_code == 400
    assert exc.value.detail == "You cannot deactivate your own account."
