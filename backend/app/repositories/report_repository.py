from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.report import Report


def fetch_report(
    session: Session,
    organization_id: uuid.UUID,
    report_id: uuid.UUID,
) -> Report | None:
    return session.scalar(
        select(Report).where(Report.organization_id == organization_id, Report.id == report_id),
    )


def list_reports_for_organization(
    session: Session,
    organization_id: uuid.UUID,
    *,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Report], int]:
    limit = min(max(limit, 1), 100)
    offset = max(offset, 0)
    total = session.scalar(
        select(func.count()).select_from(Report).where(Report.organization_id == organization_id),
    )
    rows = session.scalars(
        select(Report)
        .where(Report.organization_id == organization_id)
        .order_by(Report.created_at.desc())
        .offset(offset)
        .limit(limit),
    ).all()
    return list(rows), int(total or 0)
