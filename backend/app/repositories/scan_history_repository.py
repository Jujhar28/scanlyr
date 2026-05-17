from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.models.security_text_scan import SecurityTextScan


@dataclass(frozen=True)
class ScanHistoryFilters:
    risk_level: str | None = None
    content_type: str | None = None
    user_id: uuid.UUID | None = None
    scanned_from: datetime | None = None
    scanned_to: datetime | None = None
    min_risk_score: int | None = None
    max_risk_score: int | None = None


def _apply_filters(stmt: Any, organization_id: uuid.UUID, filters: ScanHistoryFilters) -> Any:
    stmt = stmt.where(SecurityTextScan.organization_id == organization_id)
    if filters.risk_level:
        stmt = stmt.where(SecurityTextScan.risk_level == filters.risk_level)
    if filters.content_type:
        stmt = stmt.where(SecurityTextScan.content_type == filters.content_type)
    if filters.user_id:
        stmt = stmt.where(SecurityTextScan.user_id == filters.user_id)
    if filters.scanned_from:
        stmt = stmt.where(SecurityTextScan.scanned_at >= filters.scanned_from)
    if filters.scanned_to:
        stmt = stmt.where(SecurityTextScan.scanned_at <= filters.scanned_to)
    if filters.min_risk_score is not None:
        stmt = stmt.where(SecurityTextScan.risk_score >= filters.min_risk_score)
    if filters.max_risk_score is not None:
        stmt = stmt.where(SecurityTextScan.risk_score <= filters.max_risk_score)
    return stmt


def create_security_text_scan(
    session: Session,
    *,
    organization_id: uuid.UUID,
    user_id: uuid.UUID | None,
    detection_event_id: uuid.UUID | None,
    scanned_at: datetime,
    content_type: str,
    risk_score: int,
    risk_level: str,
    confidence: float,
    finding_count: int,
    input_text: str,
    input_preview: str,
    result_payload: dict[str, Any],
    engine_version: str,
) -> SecurityTextScan:
    row = SecurityTextScan(
        organization_id=organization_id,
        user_id=user_id,
        detection_event_id=detection_event_id,
        scanned_at=scanned_at,
        content_type=content_type,
        risk_score=risk_score,
        risk_level=risk_level,
        confidence=confidence,
        finding_count=finding_count,
        input_text=input_text,
        input_preview=input_preview,
        result_payload=result_payload,
        engine_version=engine_version,
    )
    session.add(row)
    session.flush()
    return row


def fetch_security_text_scan(
    session: Session,
    organization_id: uuid.UUID,
    scan_id: uuid.UUID,
) -> SecurityTextScan | None:
    return session.scalar(
        select(SecurityTextScan).where(
            SecurityTextScan.organization_id == organization_id,
            SecurityTextScan.id == scan_id,
        ),
    )


def list_security_text_scans(
    session: Session,
    organization_id: uuid.UUID,
    *,
    filters: ScanHistoryFilters,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[SecurityTextScan], int]:
    limit = min(max(limit, 1), 100)
    offset = max(offset, 0)

    filtered = _apply_filters(select(SecurityTextScan), organization_id, filters)

    total = session.scalar(select(func.count()).select_from(filtered.subquery()))
    rows = session.scalars(
        filtered.order_by(SecurityTextScan.scanned_at.desc()).offset(offset).limit(limit),
    ).all()
    return list(rows), int(total or 0)


def count_scans_for_organization(
    session: Session,
    organization_id: uuid.UUID,
    *,
    filters: ScanHistoryFilters | None = None,
) -> int:
    f = filters or ScanHistoryFilters()
    stmt = _apply_filters(
        select(func.count()).select_from(SecurityTextScan),
        organization_id,
        f,
    )
    return int(session.scalar(stmt) or 0)


def average_risk_score(
    session: Session,
    organization_id: uuid.UUID,
    *,
    filters: ScanHistoryFilters | None = None,
) -> float | None:
    f = filters or ScanHistoryFilters()
    stmt = _apply_filters(
        select(func.avg(SecurityTextScan.risk_score)),
        organization_id,
        f,
    )
    val = session.scalar(stmt)
    return float(val) if val is not None else None


def risk_level_distribution(
    session: Session,
    organization_id: uuid.UUID,
    *,
    filters: ScanHistoryFilters | None = None,
) -> list[tuple[str, int]]:
    f = filters or ScanHistoryFilters()
    stmt = (
        _apply_filters(
            select(SecurityTextScan.risk_level, func.count()),
            organization_id,
            f,
        )
        .group_by(SecurityTextScan.risk_level)
        .order_by(func.count().desc())
    )
    return [(str(level), int(count)) for level, count in session.execute(stmt).all()]


def top_threat_categories(
    session: Session,
    organization_id: uuid.UUID,
    *,
    filters: ScanHistoryFilters | None = None,
    limit: int = 10,
) -> list[tuple[str, int]]:
    f = filters or ScanHistoryFilters()
    clauses = ["s.organization_id = :org_id"]
    params: dict[str, Any] = {"org_id": organization_id, "lim": limit}
    if f.scanned_from:
        clauses.append("s.scanned_at >= :scanned_from")
        params["scanned_from"] = f.scanned_from
    if f.scanned_to:
        clauses.append("s.scanned_at <= :scanned_to")
        params["scanned_to"] = f.scanned_to
    if f.risk_level:
        clauses.append("s.risk_level = :risk_level")
        params["risk_level"] = f.risk_level
    if f.content_type:
        clauses.append("s.content_type = :content_type")
        params["content_type"] = f.content_type

    where_sql = " AND ".join(clauses)
    sql = text(f"""
        SELECT elem->>'risk_category' AS cat, COUNT(*)::int AS cnt
        FROM security_text_scans s,
             LATERAL jsonb_array_elements(
                 COALESCE(s.result_payload->'findings', '[]'::jsonb)
             ) AS elem
        WHERE {where_sql}
          AND elem->>'risk_category' IS NOT NULL
        GROUP BY cat
        ORDER BY cnt DESC
        LIMIT :lim
    """)
    rows = session.execute(sql, params).all()
    return [(str(cat), int(cnt)) for cat, cnt in rows]


def scan_trends_by_day(
    session: Session,
    organization_id: uuid.UUID,
    *,
    filters: ScanHistoryFilters | None = None,
    days: int = 30,
) -> list[tuple[datetime, int, float | None]]:
    f = filters or ScanHistoryFilters()
    day = func.date_trunc("day", SecurityTextScan.scanned_at)
    stmt = (
        _apply_filters(
            select(
                day.label("day"),
                func.count().label("cnt"),
                func.avg(SecurityTextScan.risk_score).label("avg"),
            ),
            organization_id,
            f,
        )
        .group_by(day)
        .order_by(day.desc())
        .limit(days)
    )
    rows = session.execute(stmt).all()
    out = [
        (day_val, int(cnt), float(avg) if avg is not None else None)
        for day_val, cnt, avg in rows
    ]
    return list(reversed(out))
