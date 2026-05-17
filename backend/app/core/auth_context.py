"""Typed JWT auth context for dependency-injected route handlers."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Annotated, Any

from fastapi import Depends

from app.core.deps import get_token_payload


@dataclass(frozen=True)
class AuthContext:
    """Validated access-token claims for tenant-scoped API routes."""

    user_id: uuid.UUID
    org_id: uuid.UUID
    role: str
    payload: dict[str, Any]


def get_auth_context(
    payload: Annotated[dict[str, Any], Depends(get_token_payload)],
) -> AuthContext:
    return AuthContext(
        user_id=uuid.UUID(str(payload["sub"])),
        org_id=uuid.UUID(str(payload["org_id"])),
        role=str(payload["role"]),
        payload=payload,
    )


def require_authenticated(
    _payload: Annotated[dict[str, Any], Depends(get_token_payload)],
) -> None:
    """Router-level dependency: require a valid Bearer access JWT."""
