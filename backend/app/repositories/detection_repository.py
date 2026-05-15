from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.ai_detection_event import AIDetectionEvent


def fetch_detection_event(
    session: Session,
    organization_id: uuid.UUID,
    event_id: uuid.UUID,
) -> AIDetectionEvent | None:
    return session.scalar(
        select(AIDetectionEvent)
        .where(
            AIDetectionEvent.organization_id == organization_id,
            AIDetectionEvent.id == event_id,
        )
        .options(selectinload(AIDetectionEvent.risk_scores)),
    )


def list_detection_events_for_organization(
    session: Session,
    organization_id: uuid.UUID,
    *,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[AIDetectionEvent], int]:
    limit = min(max(limit, 1), 100)
    offset = max(offset, 0)
    total = session.scalar(
        select(func.count())
        .select_from(AIDetectionEvent)
        .where(AIDetectionEvent.organization_id == organization_id),
    )
    rows = session.scalars(
        select(AIDetectionEvent)
        .where(AIDetectionEvent.organization_id == organization_id)
        .order_by(AIDetectionEvent.occurred_at.desc())
        .offset(offset)
        .limit(limit)
        .options(selectinload(AIDetectionEvent.risk_scores)),
    ).all()
    return list(rows), int(total or 0)
