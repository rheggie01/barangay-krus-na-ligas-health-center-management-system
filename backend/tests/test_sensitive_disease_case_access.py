from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.api.v1.endpoints import disease_cases
from app.models.consultation import Consultation
from app.models.disease import Disease


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
        id=12,
        roles=[role],
    )


def make_disease(disease_id, *, sensitive):
    return SimpleNamespace(
        id=disease_id,
        is_active=True,
        is_sensitive=sensitive,
    )


class DiseaseCaseSession:
    def __init__(self, diseases):
        self.consultation = SimpleNamespace(id=50)
        self.diseases = diseases

    def get(self, model, record_id):
        if model is Consultation:
            return self.consultation
        if model is Disease:
            return self.diseases.get(record_id)
        raise AssertionError(f"Unexpected model lookup: {model}")


def test_general_disease_access_does_not_require_sensitive_permission():
    user = make_user("PATIENT_VIEW")
    disease = make_disease(1, sensitive=False)

    assert (
        disease_cases.ensure_sensitive_access(
            disease,
            user,
        )
        is None
    )


def test_sensitive_disease_access_requires_sensitive_permission():
    user = make_user("PATIENT_VIEW")
    disease = make_disease(2, sensitive=True)

    with pytest.raises(HTTPException) as exc:
        disease_cases.ensure_sensitive_access(
            disease,
            user,
        )

    assert exc.value.status_code == 403
    assert "sensitive disease record" in exc.value.detail


def test_sensitive_disease_access_allows_explicit_permission():
    user = make_user(
        "PATIENT_VIEW",
        "SENSITIVE_DISEASE_VIEW",
    )
    disease = make_disease(2, sensitive=True)

    assert (
        disease_cases.ensure_sensitive_access(
            disease,
            user,
        )
        is None
    )


def test_consultation_case_list_hides_sensitive_cases_without_permission(
    monkeypatch,
):
    user = make_user("PATIENT_VIEW")
    general_case = SimpleNamespace(id=1, disease_id=1)
    sensitive_case = SimpleNamespace(id=2, disease_id=2)
    db = DiseaseCaseSession(
        {
            1: make_disease(1, sensitive=False),
            2: make_disease(2, sensitive=True),
        }
    )

    monkeypatch.setattr(
        disease_cases,
        "get_consultation_disease_cases",
        lambda **_kwargs: [
            general_case,
            sensitive_case,
        ],
    )

    result = disease_cases.list_consultation_disease_cases(
        consultation_id=50,
        db=db,
        current_user=user,
    )

    assert result == [general_case]
    assert sensitive_case not in result


def test_consultation_case_list_returns_sensitive_cases_for_authorized_user(
    monkeypatch,
):
    user = make_user(
        "PATIENT_VIEW",
        "SENSITIVE_DISEASE_VIEW",
    )
    general_case = SimpleNamespace(id=1, disease_id=1)
    sensitive_case = SimpleNamespace(id=2, disease_id=2)
    db = DiseaseCaseSession(
        {
            1: make_disease(1, sensitive=False),
            2: make_disease(2, sensitive=True),
        }
    )

    monkeypatch.setattr(
        disease_cases,
        "get_consultation_disease_cases",
        lambda **_kwargs: [
            general_case,
            sensitive_case,
        ],
    )

    result = disease_cases.list_consultation_disease_cases(
        consultation_id=50,
        db=db,
        current_user=user,
    )

    assert result == [
        general_case,
        sensitive_case,
    ]


def test_get_sensitive_case_denied_before_record_is_returned(
    monkeypatch,
):
    user = make_user("PATIENT_VIEW")
    sensitive_case = SimpleNamespace(
        id=80,
        disease_id=2,
    )
    db = DiseaseCaseSession(
        {
            2: make_disease(2, sensitive=True),
        }
    )

    monkeypatch.setattr(
        disease_cases,
        "get_disease_case_by_id",
        lambda **_kwargs: sensitive_case,
    )

    with pytest.raises(HTTPException) as exc:
        disease_cases.get_disease_case(
            disease_case_id=80,
            db=db,
            current_user=user,
        )

    assert exc.value.status_code == 403


def test_create_sensitive_case_denied_before_service_call(
    monkeypatch,
):
    user = make_user("DISEASE_CASE_CREATE")
    db = DiseaseCaseSession(
        {
            2: make_disease(2, sensitive=True),
        }
    )
    service_called = False

    def fake_create(**_kwargs):
        nonlocal service_called
        service_called = True
        return object()

    monkeypatch.setattr(
        disease_cases,
        "create_disease_case",
        fake_create,
    )

    with pytest.raises(HTTPException) as exc:
        disease_cases.add_disease_case(
            consultation_id=50,
            data=SimpleNamespace(disease_id=2),
            db=db,
            current_user=user,
        )

    assert exc.value.status_code == 403
    assert service_called is False


def test_validation_of_sensitive_case_denied_before_service_call(
    monkeypatch,
):
    user = make_user("DISEASE_CASE_VALIDATE")
    sensitive_case = SimpleNamespace(
        id=80,
        disease_id=2,
    )
    db = DiseaseCaseSession(
        {
            2: make_disease(2, sensitive=True),
        }
    )
    service_called = False

    monkeypatch.setattr(
        disease_cases,
        "get_disease_case_by_id",
        lambda **_kwargs: sensitive_case,
    )

    def fake_validate(**_kwargs):
        nonlocal service_called
        service_called = True
        return sensitive_case

    monkeypatch.setattr(
        disease_cases,
        "validate_disease_case",
        fake_validate,
    )

    with pytest.raises(HTTPException) as exc:
        disease_cases.validate_case(
            disease_case_id=80,
            data=SimpleNamespace(
                validation_status="VALIDATED"
            ),
            db=db,
            current_user=user,
        )

    assert exc.value.status_code == 403
    assert service_called is False


def test_edit_cannot_switch_general_case_to_sensitive_without_permission(
    monkeypatch,
):
    user = make_user("DISEASE_CASE_CREATE")
    current_case = SimpleNamespace(
        id=81,
        disease_id=1,
    )
    db = DiseaseCaseSession(
        {
            1: make_disease(1, sensitive=False),
            2: make_disease(2, sensitive=True),
        }
    )
    service_called = False

    monkeypatch.setattr(
        disease_cases,
        "get_disease_case_by_id",
        lambda **_kwargs: current_case,
    )

    def fake_update(**_kwargs):
        nonlocal service_called
        service_called = True
        return current_case

    monkeypatch.setattr(
        disease_cases,
        "update_disease_case",
        fake_update,
    )

    with pytest.raises(HTTPException) as exc:
        disease_cases.edit_disease_case(
            disease_case_id=81,
            data=SimpleNamespace(disease_id=2),
            db=db,
            current_user=user,
        )

    assert exc.value.status_code == 403
    assert service_called is False
