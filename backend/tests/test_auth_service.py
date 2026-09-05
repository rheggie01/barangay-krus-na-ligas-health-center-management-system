from types import SimpleNamespace

import pytest

from app.services import auth_service


class ScalarSession:
    def __init__(self, result):
        self.result = result
        self.statement = None

    def scalar(self, statement):
        self.statement = statement
        return self.result


def make_user(**overrides):
    values = {
        "id": 7,
        "username": "active.user",
        "email": "active.user@healthcenter-demo.com",
        "password_hash": "stored-hash",
        "account_status": "ACTIVE",
        "is_active": True,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_authenticate_user_returns_none_when_user_does_not_exist(monkeypatch):
    db = ScalarSession(None)
    monkeypatch.setattr(
        auth_service,
        "verify_password",
        lambda *_args: pytest.fail("password verification should not run"),
    )

    result = auth_service.authenticate_user(
        db,
        "missing.user",
        "Password123!",
    )

    assert result is None


@pytest.mark.parametrize(
    ("account_status", "is_active"),
    [
        ("PENDING", False),
        ("INACTIVE", False),
        ("ACTIVE", False),
    ],
)
def test_authenticate_user_rejects_non_active_accounts(
    monkeypatch,
    account_status,
    is_active,
):
    user = make_user(
        account_status=account_status,
        is_active=is_active,
    )
    db = ScalarSession(user)
    monkeypatch.setattr(
        auth_service,
        "verify_password",
        lambda *_args: pytest.fail("password verification should not run"),
    )

    result = auth_service.authenticate_user(
        db,
        user.username,
        "Password123!",
    )

    assert result is None


def test_authenticate_user_rejects_wrong_password(monkeypatch):
    user = make_user()
    db = ScalarSession(user)
    monkeypatch.setattr(
        auth_service,
        "verify_password",
        lambda plain, hashed: False,
    )

    result = auth_service.authenticate_user(
        db,
        user.username,
        "WrongPassword123!",
    )

    assert result is None


def test_authenticate_user_accepts_active_user_with_valid_password(monkeypatch):
    user = make_user()
    db = ScalarSession(user)
    monkeypatch.setattr(
        auth_service,
        "verify_password",
        lambda plain, hashed: (
            plain == "CorrectPassword123!"
            and hashed == "stored-hash"
        ),
    )

    result = auth_service.authenticate_user(
        db,
        user.username,
        "CorrectPassword123!",
    )

    assert result is user


def test_authenticate_user_normalizes_login_values(monkeypatch):
    user = make_user()
    db = ScalarSession(user)
    monkeypatch.setattr(
        auth_service,
        "verify_password",
        lambda *_args: True,
    )

    auth_service.authenticate_user(
        db,
        "  Mixed.Email@HealthCenter-Demo.COM  ",
        "CorrectPassword123!",
    )

    params = db.statement.compile().params
    assert params["username_1"] == "Mixed.Email@HealthCenter-Demo.COM"
    assert params["email_1"] == "mixed.email@healthcenter-demo.com"
