from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
from jose import jwt
from jose.exceptions import JOSEError, JWTError

from app.core.config import settings


ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_BYTES = 48
ALLOWED_TOKEN_ROLES = frozenset({"admin", "analyst", "viewer"})


def hash_password(plain_password: str) -> str:
    salt = bcrypt.gensalt(rounds=settings.bcrypt_rounds)
    return bcrypt.hashpw(plain_password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            password_hash.encode("utf-8"),
        )
    except ValueError:
        return False


def generate_refresh_token_value() -> str:
    return secrets.token_urlsafe(REFRESH_TOKEN_BYTES)


def hash_refresh_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def create_access_token(
    subject: str,
    *,
    expires_delta: timedelta | None = None,
    additional_claims: dict[str, Any] | None = None,
) -> str:
    expire = datetime.now(tz=UTC) + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode: dict[str, Any] = {
        "sub": subject,
        "typ": ACCESS_TOKEN_TYPE,
        "exp": expire,
        "iat": datetime.now(tz=UTC),
    }
    if additional_claims:
        to_encode.update(additional_claims)
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)


def _validate_access_claims(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("typ") != ACCESS_TOKEN_TYPE:
        raise JWTError("Invalid token type")

    sub = payload.get("sub")
    if not sub or not isinstance(sub, str):
        raise JWTError("Missing subject")
    try:
        uuid.UUID(sub)
    except ValueError as exc:
        raise JWTError("Invalid subject") from exc

    org_id = payload.get("org_id")
    if not org_id:
        raise JWTError("Missing organization")
    try:
        uuid.UUID(str(org_id))
    except ValueError as exc:
        raise JWTError("Invalid organization") from exc

    role = payload.get("role")
    if not role or not isinstance(role, str):
        raise JWTError("Missing role")
    if role not in ALLOWED_TOKEN_ROLES:
        raise JWTError("Invalid role")

    return payload


def decode_access_token(token: str) -> dict[str, Any]:
    if not token or not token.strip():
        raise JWTError("Empty token")
    payload = jwt.decode(
        token.strip(),
        settings.secret_key,
        algorithms=[settings.jwt_algorithm],
        options={"require": ["exp", "sub", "iat", "typ"]},
    )
    return _validate_access_claims(payload)


def safe_decode_access_token(token: str) -> dict[str, Any] | None:
    """Return claims or None on any decode/verify failure (do not leak details)."""
    try:
        return decode_access_token(token)
    except JOSEError:
        return None
