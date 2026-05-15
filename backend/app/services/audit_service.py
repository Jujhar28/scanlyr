from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.enums import AuditActorType

logger = logging.getLogger(__name__)


def append_audit_event(
    db: Session,
    *,
    organization_id: uuid.UUID | None,
    actor_user_id: uuid.UUID | None,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    payload: dict[str, Any] | None = None,
    request_id: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> None:
    """Append an audit row (caller should ``commit`` with surrounding transaction)."""
    row = AuditLog(
        organization_id=organization_id,
        actor_user_id=actor_user_id,
        actor_type=AuditActorType.user.value if actor_user_id else AuditActorType.system.value,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        payload=payload,
        request_id=request_id,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(row)
    db.flush()
    logger.info(
        "audit_event",
        extra={"action": action, "resource_type": resource_type, "organization_id": str(organization_id)},
    )
