"""Unit tests for JWT validation, bcrypt passwords, and auth dependencies."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from jose import jwt
from jose.exceptions import JWTError

from app.core.config import settings
from app.core.security import (
    ACCESS_TOKEN_TYPE,
    create_access_token,
    decode_access_token,
    hash_password,
    safe_decode_access_token,
    verify_password,
)


def test_bcrypt_hash_and_verify() -> None:
    hashed = hash_password("SecurePass1!")
    assert hashed.startswith("$2")
    assert verify_password("SecurePass1!", hashed)
    assert not verify_password("wrong", hashed)


def test_access_token_requires_org_and_role() -> None:
    user_id = str(uuid.uuid4())
    token = create_access_token(
        user_id,
        additional_claims={"org_id": str(uuid.uuid4()), "role": "admin"},
    )
    payload = decode_access_token(token)
    assert payload["sub"] == user_id
    assert payload["typ"] == ACCESS_TOKEN_TYPE
    assert payload["role"] == "admin"


def test_decode_rejects_missing_org_id() -> None:
    expire = datetime.now(tz=UTC) + timedelta(minutes=5)
    token = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "typ": ACCESS_TOKEN_TYPE,
            "exp": expire,
            "iat": datetime.now(tz=UTC),
            "role": "admin",
        },
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )
    with pytest.raises(JWTError):
        decode_access_token(token)


def test_decode_rejects_wrong_token_type() -> None:
    expire = datetime.now(tz=UTC) + timedelta(minutes=5)
    token = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "typ": "refresh",
            "exp": expire,
            "iat": datetime.now(tz=UTC),
            "org_id": str(uuid.uuid4()),
            "role": "admin",
        },
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )
    assert safe_decode_access_token(token) is None


def test_decode_rejects_invalid_role() -> None:
    user_id = str(uuid.uuid4())
    token = create_access_token(
        user_id,
        additional_claims={"org_id": str(uuid.uuid4()), "role": "superuser"},
    )
    assert safe_decode_access_token(token) is None
