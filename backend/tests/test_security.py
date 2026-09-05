from datetime import timedelta

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hash_round_trip():
    password = "CapstoneTestPassword!2026"

    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword!2026", hashed) is False


def test_access_token_round_trip():
    token = create_access_token(subject="42")

    assert decode_access_token(token) == "42"


def test_expired_access_token_is_rejected():
    token = create_access_token(
        subject="42",
        expires_delta=timedelta(seconds=-1),
    )

    assert decode_access_token(token) is None


def test_malformed_access_token_is_rejected():
    assert decode_access_token("not-a-valid-jwt") is None
