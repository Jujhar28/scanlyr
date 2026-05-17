"""Security-relevant audit events (auth, scans)."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.services.audit_service import append_audit_event

logger = logging.getLogger(__name__)


def record_security_audit(
    db: Session,
    *,
    action: str,
    organization_id: uuid.UUID | None = None,
    actor_user_id: uuid.UUID | None = None,
    resource_type: str = "security",
    resource_id: str | None = None,
    payload: dict[str, Any] | None = None,
    request_id: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> None:
    try:
        append_audit_event(
            db,
            organization_id=organization_id,
            actor_user_id=actor_user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            payload=payload,
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    except Exception:
        logger.exception("failed_to_record_security_audit", extra={"action": action})
