"""Orchestration for scan history list/detail APIs."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.repositories.scan_history_repository import (
    ScanHistoryFilters,
    fetch_security_text_scan,
    list_security_text_scans,
)
from app.schemas.scan import ScanResponse
from app.schemas.scan_history import (
    ScanHistoryDetail,
    ScanHistoryListResponse,
    ScanHistorySummary,
)
from app.services.http_errors import RouteHttpError


def _filters_from_query(
    *,
    risk_level: str | None,
    content_type: str | None,
    user_id: uuid.UUID | None,
    scanned_from: datetime | None,
    scanned_to: datetime | None,
    min_risk_score: int | None,
    max_risk_score: int | None,
) -> ScanHistoryFilters:
    return ScanHistoryFilters(
        risk_level=risk_level,
        content_type=content_type,
        user_id=user_id,
        scanned_from=scanned_from,
        scanned_to=scanned_to,
        min_risk_score=min_risk_score,
        max_risk_score=max_risk_score,
    )


def _row_to_summary(row: object) -> ScanHistorySummary:
    from app.models.security_text_scan import SecurityTextScan

    assert isinstance(row, SecurityTextScan)
    return ScanHistorySummary(
        id=row.id,
        scanned_at=row.scanned_at,
        user_id=row.user_id,
        content_type=row.content_type,  # type: ignore[arg-type]
        risk_score=row.risk_score,
        risk_level=row.risk_level,  # type: ignore[arg-type]
        confidence=row.confidence,
        finding_count=row.finding_count,
        input_text=row.input_text,
        input_preview=row.input_preview,
        engine_version=row.engine_version,
    )


def build_scan_history_list(
    db: Session,
    *,
    organization_id: uuid.UUID,
    limit: int,
    offset: int,
    risk_level: str | None = None,
    content_type: str | None = None,
    user_id: uuid.UUID | None = None,
    scanned_from: datetime | None = None,
    scanned_to: datetime | None = None,
    min_risk_score: int | None = None,
    max_risk_score: int | None = None,
) -> ScanHistoryListResponse:
    filters = _filters_from_query(
        risk_level=risk_level,
        content_type=content_type,
        user_id=user_id,
        scanned_from=scanned_from,
        scanned_to=scanned_to,
        min_risk_score=min_risk_score,
        max_risk_score=max_risk_score,
    )
    rows, total = list_security_text_scans(
        db,
        organization_id,
        filters=filters,
        limit=limit,
        offset=offset,
    )
    return ScanHistoryListResponse(
        items=[_row_to_summary(r) for r in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


def get_scan_history_detail(
    db: Session,
    *,
    organization_id: uuid.UUID,
    scan_id: uuid.UUID,
) -> ScanHistoryDetail:
    row = fetch_security_text_scan(db, organization_id, scan_id)
    if row is None:
        raise RouteHttpError(404, "Scan not found")
    result = ScanResponse.model_validate(row.result_payload)
    summary = _row_to_summary(row)
    detail_fields = summary.model_dump()
    detail_fields["input_text"] = row.input_text or row.input_preview.replace("…", "")
    return ScanHistoryDetail(
        **detail_fields,
        findings=list(result.findings),
        result=result,
        detection_event_id=row.detection_event_id,
    )
