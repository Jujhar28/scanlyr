from collections.abc import Callable
from typing import Annotated, Any
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import safe_decode_access_token
from app.db.session import get_db
from app.models.enums import MembershipStatus
from app.models.membership import Membership
from app.models.role import Role
from app.models.user import User

http_bearer = HTTPBearer(auto_error=False)


def get_bearer_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(http_bearer)],
) -> str | None:
    if credentials is None or credentials.scheme.lower() != "bearer":
        return None
    return credentials.credentials


def get_token_payload(
    token: Annotated[str | None, Depends(get_bearer_token)],
) -> dict[str, Any]:
    """Require a valid access JWT; raises 401 if missing or invalid."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = safe_decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


def get_current_subject(payload: Annotated[dict[str, Any], Depends(get_token_payload)]) -> str:
    sub = payload.get("sub")
    if not sub or not isinstance(sub, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token subject missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return sub


def get_current_user(
    payload: Annotated[dict[str, Any], Depends(get_token_payload)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    try:
        user_id = uuid.UUID(str(payload.get("sub")))
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid subject",
        ) from exc

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return user


def require_roles(*allowed_roles: str) -> Callable[..., Membership]:
    allowed = set(allowed_roles)

    def _dependency(
        payload: Annotated[dict[str, Any], Depends(get_token_payload)],
        db: Annotated[Session, Depends(get_db)],
    ) -> Membership:
        org_raw = payload.get("org_id")
        user_raw = payload.get("sub")
        if not org_raw or not user_raw:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Missing organization or user context",
            )
        try:
            org_id = uuid.UUID(str(org_raw))
            user_id = uuid.UUID(str(user_raw))
        except (TypeError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid authorization context",
            ) from exc

        row = db.execute(
            select(Membership, Role)
            .join(Role, Role.id == Membership.role_id)
            .where(
                Membership.organization_id == org_id,
                Membership.user_id == user_id,
                Membership.status == MembershipStatus.active.value,
                Role.slug.in_(allowed),
            )
            .limit(1)
        ).one_or_none()
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        membership, _role = row
        return membership

    return _dependency
