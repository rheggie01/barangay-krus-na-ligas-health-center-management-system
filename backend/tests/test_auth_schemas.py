import pytest
from pydantic import ValidationError

from app.schemas.auth import RegisterRequest


def valid_registration(**overrides):
    values = {
        "first_name": "  Test  ",
        "last_name": "  Clinician  ",
        "email": "test.clinician@healthcenter-demo.com",
        "username": "test.clinician",
        "password": "StrongPassword123!",
        "confirm_password": "StrongPassword123!",
        "role_name": " doctor ",
        "privacy_accepted": True,
    }
    values.update(overrides)
    return values


def test_registration_normalizes_name_username_and_role():
    registration = RegisterRequest(**valid_registration())

    assert registration.first_name == "Test"
    assert registration.last_name == "Clinician"
    assert registration.username == "test.clinician"
    assert registration.role_name == "DOCTOR"


def test_self_registration_cannot_request_system_admin_role():
    with pytest.raises(ValidationError):
        RegisterRequest(
            **valid_registration(role_name="SYSTEM_ADMIN")
        )


def test_registration_requires_privacy_acknowledgement():
    with pytest.raises(ValidationError):
        RegisterRequest(
            **valid_registration(privacy_accepted=False)
        )


def test_registration_rejects_password_mismatch():
    with pytest.raises(ValidationError):
        RegisterRequest(
            **valid_registration(
                confirm_password="DifferentPassword123!"
            )
        )
