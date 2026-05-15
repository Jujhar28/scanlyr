"""HTTP-facing orchestration for report list / generate (keeps routers thin)."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models.membership import Membership
from app.schemas.report import (
    GenerateReportRequest,
    GenerateReportResponse,
    ReportDetail,
    ReportListResponse,
    ReportSummary,
)
from app.services.compliance_report_service import generate_compliance_pdf_report, get_report, list_reports


def build_report_list_response(
    db: Session,
    *,
    organization_id: uuid.UUID,
    limit: int,
    offset: int,
) -> ReportListResponse:
    rows, total = list_reports(db, organization_id, limit=limit, offset=offset)
    return ReportListResponse(
        items=[ReportSummary.from_orm_row(r) for r in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


def build_report_detail_response(
    db: Session,
    *,
    organization_id: uuid.UUID,
    report_id: uuid.UUID,
) -> ReportDetail | None:
    row = get_report(db, organization_id, report_id)
    if row is None:
        return None
    return ReportDetail.from_report(row)


def generate_compliance_report_response(
    db: Session,
    *,
    membership: Membership,
    body: GenerateReportRequest | None,
    request_id: str | None,
    ip_address: str | None,
    user_agent: str | None,
) -> GenerateReportResponse:
    resolved = body or GenerateReportRequest()
    report = generate_compliance_pdf_report(
        db,
        organization_id=membership.organization_id,
        created_by_user_id=membership.user_id,
        period_start=resolved.period_start,
        period_end=resolved.period_end,
        request_id=request_id,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return GenerateReportResponse(id=report.id, title=report.title, status=report.status)
