from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.api.v1.endpoints import auth
from app.models.role import Role
from app.schemas.auth import LoginRequest, RegisterRequest


class FakeSession:
    def __init__(self, scalar_results=None):
        self.scalar_results = list(scalar_results or [])
        self.added = []
        self.commit_count = 0
        self.rollback_count = 0
        self.refresh_count = 0

    def scalar(self, _statement):
        if not self.scalar_results:
            return None
        return self.scalar_results.pop(0)

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        self.commit_count += 1

    def rollback(self):
        self.rollback_count += 1

    def refresh(self, obj):
        self.refresh_count += 1
        if getattr(obj, "id", None) is None:
            obj.id = 501


def request():
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/auth/login",
            "headers": [],
            "client": ("127.0.0.1", 50000),
            "server": ("testserver", 80),
            "scheme": "http",
            "query_string": b"",
        }
    )


def test_login_failure_returns_401_and_writes_audit(monkeypatch):
    db = FakeSession()
    audit_calls = []
    monkeypatch.setattr(
        auth,
        "authenticate_user",
        lambda *_args: None,
    )
    monkeypatch.setattr(
        auth,
        "get_request_ip",
        lambda _request: "127.0.0.1",
    )
    monkeypatch.setattr(
        auth,
        "create_audit_log",
        lambda _db, **kwargs: audit_calls.append(kwargs),
    )
    credentials = LoginRequest(
        username="unknown.user",
        password="Password123!",
    )

    with pytest.raises(HTTPException) as exc:
        auth.login(
            credentials=credentials,
            request=request(),
            db=db,
        )

    assert exc.value.status_code == 401
    assert db.commit_count == 1
    assert audit_calls[0]["action"] == "LOGIN_FAILED"
    assert audit_calls[0]["module"] == "authentication"


def test_login_success_returns_bearer_token_and_writes_audit(monkeypatch):
    db = FakeSession()
    user = SimpleNamespace(id=77, username="doctor.one")
    audit_calls = []
    monkeypatch.setattr(
        auth,
        "authenticate_user",
        lambda *_args: user,
    )
    monkeypatch.setattr(
        auth,
        "create_access_token",
        lambda subject: f"token-for-{subject}",
    )
    monkeypatch.setattr(
        auth,
        "get_request_ip",
        lambda _request: "127.0.0.1",
    )
    monkeypatch.setattr(
        auth,
        "create_audit_log",
        lambda _db, **kwargs: audit_calls.append(kwargs),
    )

    result = auth.login(
        credentials=LoginRequest(
            username="doctor.one",
            password="Password123!",
        ),
        request=request(),
        db=db,
    )

    assert result.access_token == "token-for-77"
    assert result.token_type == "bearer"
    assert db.commit_count == 1
    assert audit_calls[0]["action"] == "LOGIN_SUCCESS"
    assert audit_calls[0]["record_id"] == 77


def test_self_registration_creates_pending_inactive_account(monkeypatch):
    role = Role(
        name="DOCTOR",
        description="Health Center Doctor",
    )
    db = FakeSession(
        scalar_results=[
            None,  # username not taken
            None,  # email not taken
            role,  # requested role exists
        ]
    )
    audit_calls = []
    monkeypatch.setattr(
        auth,
        "get_request_ip",
        lambda _request: "127.0.0.1",
    )
    monkeypatch.setattr(
        auth,
        "create_audit_log",
        lambda _db, **kwargs: audit_calls.append(kwargs),
    )
    monkeypatch.setattr(
        auth,
        "hash_password",
        lambda password: f"hashed::{password}",
    )
    registration = RegisterRequest(
        first_name="Test",
        last_name="Doctor",
        email="test.doctor@healthcenter-demo.com",
        username="test.doctor",
        password="Password123!",
        confirm_password="Password123!",
        role_name="DOCTOR",
        privacy_accepted=True,
    )

    result = auth.register(
        registration=registration,
        request=request(),
        db=db,
    )

    created_user = db.added[0]
    assert created_user.account_status == "PENDING"
    assert created_user.is_active is False
    assert created_user.roles == [role]
    assert created_user.password_hash == "hashed::Password123!"
    assert result.id == 501
    assert result.role == "DOCTOR"
    assert result.is_active is False
    assert db.commit_count == 1
    assert audit_calls[0]["action"] == "REGISTER"
