from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.api.v1.endpoints import forecasts


def make_user(*permission_codes):
    permissions = [
        SimpleNamespace(code=code)
        for code in permission_codes
    ]
    role = SimpleNamespace(
        name="TEST_ROLE",
        permissions=permissions,
    )
    return SimpleNamespace(
        id=15,
        roles=[role],
    )


def test_catalog_explicit_sensitive_request_requires_permission(
    monkeypatch,
):
    user = make_user("FORECAST_VIEW")
    service_called = False

    def fake_catalog(*_args, **_kwargs):
        nonlocal service_called
        service_called = True
        return []

    monkeypatch.setattr(
        forecasts,
        "list_disease_forecast_catalog",
        fake_catalog,
    )

    with pytest.raises(HTTPException) as exc:
        forecasts.get_disease_forecast_catalog(
            include_sensitive=True,
            db=object(),
            current_user=user,
        )

    assert exc.value.status_code == 403
    assert "SENSITIVE_DISEASE_VIEW" in exc.value.detail
    assert service_called is False


def test_catalog_defaults_to_general_for_user_without_sensitive_permission(
    monkeypatch,
):
    user = make_user("FORECAST_VIEW")
    calls = []

    monkeypatch.setattr(
        forecasts,
        "list_disease_forecast_catalog",
        lambda _db, **kwargs: calls.append(kwargs) or [],
    )

    result = forecasts.get_disease_forecast_catalog(
        include_sensitive=None,
        db=object(),
        current_user=user,
    )

    assert result == []
    assert calls[0]["include_sensitive"] is False


def test_catalog_defaults_to_include_sensitive_for_authorized_user(
    monkeypatch,
):
    user = make_user(
        "FORECAST_VIEW",
        "SENSITIVE_DISEASE_VIEW",
    )
    calls = []

    monkeypatch.setattr(
        forecasts,
        "list_disease_forecast_catalog",
        lambda _db, **kwargs: calls.append(kwargs) or [],
    )

    result = forecasts.get_disease_forecast_catalog(
        include_sensitive=None,
        db=object(),
        current_user=user,
    )

    assert result == []
    assert calls[0]["include_sensitive"] is True


def test_sensitive_forecast_detail_denied_before_forecast_service(
    monkeypatch,
):
    user = make_user("FORECAST_VIEW")
    sensitive_disease = SimpleNamespace(
        code="HIV",
        is_sensitive=True,
    )
    service_called = False

    monkeypatch.setattr(
        forecasts,
        "get_disease_for_forecast_code",
        lambda *_args, **_kwargs: sensitive_disease,
    )

    def fake_forecast(*_args, **_kwargs):
        nonlocal service_called
        service_called = True
        return object()

    monkeypatch.setattr(
        forecasts,
        "get_disease_forecast",
        fake_forecast,
    )

    with pytest.raises(HTTPException) as exc:
        forecasts.get_disease_forecast_detail(
            disease_code="HIV",
            db=object(),
            current_user=user,
        )

    assert exc.value.status_code == 403
    assert "SENSITIVE_DISEASE_VIEW" in exc.value.detail
    assert service_called is False


def test_sensitive_forecast_detail_allowed_for_authorized_user(
    monkeypatch,
):
    user = make_user(
        "FORECAST_VIEW",
        "SENSITIVE_DISEASE_VIEW",
    )
    sensitive_disease = SimpleNamespace(
        code="HIV",
        is_sensitive=True,
    )
    expected = {"disease_code": "HIV"}

    monkeypatch.setattr(
        forecasts,
        "get_disease_for_forecast_code",
        lambda *_args, **_kwargs: sensitive_disease,
    )
    monkeypatch.setattr(
        forecasts,
        "get_disease_forecast",
        lambda *_args, **_kwargs: expected,
    )

    result = forecasts.get_disease_forecast_detail(
        disease_code="HIV",
        db=object(),
        current_user=user,
    )

    assert result is expected


def test_general_forecast_detail_does_not_require_sensitive_permission(
    monkeypatch,
):
    user = make_user("FORECAST_VIEW")
    general_disease = SimpleNamespace(
        code="DENGUE",
        is_sensitive=False,
    )
    expected = {"disease_code": "DENGUE"}

    monkeypatch.setattr(
        forecasts,
        "get_disease_for_forecast_code",
        lambda *_args, **_kwargs: general_disease,
    )
    monkeypatch.setattr(
        forecasts,
        "get_disease_forecast",
        lambda *_args, **_kwargs: expected,
    )

    result = forecasts.get_disease_forecast_detail(
        disease_code="DENGUE",
        db=object(),
        current_user=user,
    )

    assert result is expected


def test_sensitive_mapping_request_requires_permission(
    monkeypatch,
):
    user = make_user("FORECAST_VIEW")
    service_called = False

    def fake_mapping(*_args, **_kwargs):
        nonlocal service_called
        service_called = True
        return []

    monkeypatch.setattr(
        forecasts,
        "list_disease_medicine_mappings",
        fake_mapping,
    )

    with pytest.raises(HTTPException) as exc:
        forecasts.get_disease_medicine_mapping_rows(
            include_sensitive=True,
            db=object(),
            current_user=user,
        )

    assert exc.value.status_code == 403
    assert service_called is False


def test_mapping_defaults_to_general_for_unauthorized_user(
    monkeypatch,
):
    user = make_user("FORECAST_VIEW")
    calls = []

    monkeypatch.setattr(
        forecasts,
        "list_disease_medicine_mappings",
        lambda _db, **kwargs: calls.append(kwargs) or [],
    )

    result = forecasts.get_disease_medicine_mapping_rows(
        include_sensitive=None,
        db=object(),
        current_user=user,
    )

    assert result == []
    assert calls[0]["include_sensitive"] is False


def test_mapping_defaults_to_sensitive_capability_for_authorized_user(
    monkeypatch,
):
    user = make_user(
        "FORECAST_VIEW",
        "SENSITIVE_DISEASE_VIEW",
    )
    calls = []

    monkeypatch.setattr(
        forecasts,
        "list_disease_medicine_mappings",
        lambda _db, **kwargs: calls.append(kwargs) or [],
    )

    result = forecasts.get_disease_medicine_mapping_rows(
        include_sensitive=None,
        db=object(),
        current_user=user,
    )

    assert result == []
    assert calls[0]["include_sensitive"] is True
