from datetime import date
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.api.v1.endpoints import surveillance


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
        id=10,
        roles=[role],
    )


def test_general_scope_never_includes_sensitive_rows():
    user = make_user(
        "SURVEILLANCE_VIEW",
        "SENSITIVE_DISEASE_VIEW",
    )

    assert surveillance.resolve_surveillance_scope(
        user,
        "GENERAL",
    ) == (False, False)


def test_sensitive_scope_requires_explicit_permission():
    user = make_user("SURVEILLANCE_VIEW")

    with pytest.raises(HTTPException) as exc:
        surveillance.resolve_surveillance_scope(
            user,
            "SENSITIVE",
        )

    assert exc.value.status_code == 403
    assert "SENSITIVE_DISEASE_VIEW" in exc.value.detail


def test_sensitive_scope_is_aggregate_only_for_authorized_user():
    user = make_user(
        "SURVEILLANCE_VIEW",
        "SENSITIVE_DISEASE_VIEW",
    )

    assert surveillance.resolve_surveillance_scope(
        user,
        "SENSITIVE",
    ) == (True, True)


def test_disease_case_counts_general_passes_non_sensitive_flags(
    monkeypatch,
):
    user = make_user("SURVEILLANCE_VIEW")
    calls = []

    monkeypatch.setattr(
        surveillance,
        "get_disease_case_counts",
        lambda **kwargs: calls.append(kwargs) or [],
    )

    result = surveillance.disease_case_counts(
        start_date=None,
        end_date=None,
        scope="GENERAL",
        db=object(),
        current_user=user,
    )

    assert result == []
    assert calls[0]["include_sensitive"] is False
    assert calls[0]["sensitive_only"] is False


def test_disease_case_counts_sensitive_passes_sensitive_only_flags(
    monkeypatch,
):
    user = make_user(
        "SURVEILLANCE_VIEW",
        "SENSITIVE_DISEASE_VIEW",
    )
    calls = []

    monkeypatch.setattr(
        surveillance,
        "get_disease_case_counts",
        lambda **kwargs: calls.append(kwargs) or [],
    )

    result = surveillance.disease_case_counts(
        start_date=None,
        end_date=None,
        scope="SENSITIVE",
        db=object(),
        current_user=user,
    )

    assert result == []
    assert calls[0]["include_sensitive"] is True
    assert calls[0]["sensitive_only"] is True


def test_weekly_sensitive_scope_passes_aggregate_sensitive_flags(
    monkeypatch,
):
    user = make_user(
        "SURVEILLANCE_VIEW",
        "SENSITIVE_DISEASE_VIEW",
    )
    calls = []

    monkeypatch.setattr(
        surveillance,
        "get_weekly_disease_comparison",
        lambda **kwargs: calls.append(kwargs) or [],
    )

    result = surveillance.weekly_disease_comparison(
        scope="SENSITIVE",
        db=object(),
        current_user=user,
    )

    assert result == []
    assert calls[0]["include_sensitive"] is True
    assert calls[0]["sensitive_only"] is True


def test_sensitive_street_mapping_denied_even_when_authorized(
    monkeypatch,
):
    user = make_user(
        "SURVEILLANCE_VIEW",
        "SENSITIVE_DISEASE_VIEW",
    )
    service_called = False

    def fake_service(**_kwargs):
        nonlocal service_called
        service_called = True
        return []

    monkeypatch.setattr(
        surveillance,
        "get_disease_cases_by_street",
        fake_service,
    )

    with pytest.raises(HTTPException) as exc:
        surveillance.disease_cases_by_street(
            start_date=None,
            end_date=None,
            disease_id=None,
            scope="SENSITIVE",
            db=object(),
            current_user=user,
        )

    assert exc.value.status_code == 403
    assert "Street-level mapping is disabled" in exc.value.detail
    assert service_called is False


def test_sensitive_street_mapping_without_permission_is_denied_first(
    monkeypatch,
):
    user = make_user("SURVEILLANCE_VIEW")
    service_called = False

    def fake_service(**_kwargs):
        nonlocal service_called
        service_called = True
        return []

    monkeypatch.setattr(
        surveillance,
        "get_disease_cases_by_street",
        fake_service,
    )

    with pytest.raises(HTTPException) as exc:
        surveillance.disease_cases_by_street(
            start_date=None,
            end_date=None,
            disease_id=None,
            scope="SENSITIVE",
            db=object(),
            current_user=user,
        )

    assert exc.value.status_code == 403
    assert "SENSITIVE_DISEASE_VIEW" in exc.value.detail
    assert service_called is False


def test_general_street_mapping_forces_sensitive_exclusion(
    monkeypatch,
):
    user = make_user("SURVEILLANCE_VIEW")
    calls = []

    monkeypatch.setattr(
        surveillance,
        "get_disease_cases_by_street",
        lambda **kwargs: calls.append(kwargs) or [],
    )

    result = surveillance.disease_cases_by_street(
        start_date=None,
        end_date=None,
        disease_id=7,
        scope="GENERAL",
        db=object(),
        current_user=user,
    )

    assert result == []
    assert calls[0]["disease_id"] == 7
    assert calls[0]["include_sensitive"] is False
    assert calls[0]["sensitive_only"] is False


def test_invalid_date_range_is_rejected_before_surveillance_query(
    monkeypatch,
):
    user = make_user("SURVEILLANCE_VIEW")
    service_called = False

    def fake_service(**_kwargs):
        nonlocal service_called
        service_called = True
        return []

    monkeypatch.setattr(
        surveillance,
        "get_disease_case_counts",
        fake_service,
    )

    with pytest.raises(HTTPException) as exc:
        surveillance.disease_case_counts(
            start_date=date(2026, 9, 10),
            end_date=date(2026, 9, 1),
            scope="GENERAL",
            db=object(),
            current_user=user,
        )

    assert exc.value.status_code == 400
    assert service_called is False
