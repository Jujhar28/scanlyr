"""Organization-level scan analytics."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.repositories.scan_history_repository import (
    ScanHistoryFilters,
    average_risk_score,
    count_scans_for_organization,
    risk_level_distribution,
    scan_trends_by_day,
    top_threat_categories,
)
from app.schemas.scan_history import (
    RiskLevelCount,
    ScanAnalyticsResponse,
    ScanTrendPoint,
    ThreatCount,
)


def build_organization_scan_analytics(
    db: Session,
    *,
    organization_id: uuid.UUID,
    scanned_from: datetime | None = None,
    scanned_to: datetime | None = None,
    trend_days: int = 30,
) -> ScanAnalyticsResponse:
    filters = ScanHistoryFilters(scanned_from=scanned_from, scanned_to=scanned_to)
    total = count_scans_for_organization(db, organization_id, filters=filters)
    avg = average_risk_score(db, organization_id, filters=filters)
    distribution = [
        RiskLevelCount(risk_level=level, count=count)
        for level, count in risk_level_distribution(db, organization_id, filters=filters)
    ]
    threats = [
        ThreatCount(risk_category=cat, count=cnt)
        for cat, cnt in top_threat_categories(db, organization_id, filters=filters, limit=10)
    ]
    trends = [
        ScanTrendPoint(date=day, scan_count=cnt, average_risk_score=avg_score)
        for day, cnt, avg_score in scan_trends_by_day(
            db,
            organization_id,
            filters=filters,
            days=trend_days,
        )
    ]
    return ScanAnalyticsResponse(
        organization_id=organization_id,
        total_scans=total,
        average_risk_score=round(avg, 2) if avg is not None else None,
        risk_level_distribution=distribution,
        top_threats=threats,
        trends=trends,
    )
