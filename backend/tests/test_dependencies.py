from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.api import dependencies


class ScalarSession:
    def __init__(self, result):
        self.result = result

    def scalar(self, _statement):
        return self.result


def credentials(token="test-token"):
    return HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )


def make_user(**overrides):
    values = {
        "id": 10,
        "account_status": "ACTIVE",
        "is_active": True,
        "roles": [],
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_get_current_user_rejects_invalid_or_expired_token(monkeypatch):
    monkeypatch.setattr(
        dependencies,
        "decode_access_token",
        lambda _token: None,
    )

    with pytest.raises(HTTPException) as exc:
        dependencies.get_current_user(
            credentials=credentials(),
            db=ScalarSession(None),
        )

    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid or expired token"


def test_get_current_user_rejects_non_numeric_subject(monkeypatch):
    monkeypatch.setattr(
        dependencies,
        "decode_access_token",
        lambda _token: "not-an-integer",
    )

    with pytest.raises(HTTPException) as exc:
        dependencies.get_current_user(
            credentials=credentials(),
            db=ScalarSession(None),
        )

    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid token subject"


def test_get_current_user_rejects_missing_user(monkeypatch):
    monkeypatch.setattr(
        dependencies,
        "decode_access_token",
        lambda _token: "10",
    )

    with pytest.raises(HTTPException) as exc:
        dependencies.get_current_user(
            credentials=credentials(),
            db=ScalarSession(None),
        )

    assert exc.value.status_code == 401
    assert exc.value.detail == "User not found"


@pytest.mark.parametrize(
    ("account_status", "is_active"),
    [
        ("PENDING", False),
        ("INACTIVE", False),
        ("ACTIVE", False),
    ],
)
def test_get_current_user_rejects_non_active_account(
    monkeypatch,
    account_status,
    is_active,
):
    monkeypatch.setattr(
        dependencies,
        "decode_access_token",
        lambda _token: "10",
    )
    user = make_user(
        account_status=account_status,
        is_active=is_active,
    )

    with pytest.raises(HTTPException) as exc:
        dependencies.get_current_user(
            credentials=credentials(),
            db=ScalarSession(user),
        )

    assert exc.value.status_code == 403
    assert exc.value.detail == "User account is not active"


def test_get_current_user_returns_active_user(monkeypatch):
    monkeypatch.setattr(
        dependencies,
        "decode_access_token",
        lambda _token: "10",
    )
    user = make_user()

    result = dependencies.get_current_user(
        credentials=credentials(),
        db=ScalarSession(user),
    )

    assert result is user


def user_with_permissions(*permission_codes):
    permissions = [
        SimpleNamespace(code=code)
        for code in permission_codes
    ]
    role = SimpleNamespace(
        name="TEST_ROLE",
        permissions=permissions,
    )
    return make_user(roles=[role])


def test_require_permission_allows_explicit_permission():
    user = user_with_permissions(
        "FORECAST_VIEW",
        "SENSITIVE_DISEASE_VIEW",
    )
    checker = dependencies.require_permission(
        "SENSITIVE_DISEASE_VIEW"
    )

    assert checker(current_user=user) is user


def test_require_permission_denies_missing_permission():
    user = user_with_permissions("FORECAST_VIEW")
    checker = dependencies.require_permission(
        "SENSITIVE_DISEASE_VIEW"
    )

    with pytest.raises(HTTPException) as exc:
        checker(current_user=user)

    assert exc.value.status_code == 403
    assert (
        exc.value.detail
        == "You do not have permission to perform this action."
    )
