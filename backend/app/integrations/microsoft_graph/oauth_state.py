from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt

from app.core.config import Settings

OAUTH_STATE_TYP = "msft_oauth_state"


def create_oauth_state_token(settings: Settings, *, organization_id: uuid.UUID, user_id: uuid.UUID) -> str:
    expire = datetime.now(tz=UTC) + timedelta(minutes=10)
    payload: dict[str, Any] = {
        "typ": OAUTH_STATE_TYP,
        "org_id": str(organization_id),
        "admin_user_id": str(user_id),
        "exp": expire,
        "iat": datetime.now(tz=UTC),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_oauth_state_token(settings: Settings, token: str) -> dict[str, Any]:
    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    if payload.get("typ") != OAUTH_STATE_TYP:
        raise JWTError("Invalid OAuth state token type")
    return payload
