"""Validate report download + audit trail (used by reports router)."""

from __future__ import annotations

import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.enums import ReportStatus
from app.repositories import report_repository
from app.services.audit_service import append_audit_event
from app.services.compliance_report_service import pdf_absolute_path
from app.services.http_errors import RouteHttpError


def prepare_report_pdf_download(
    db: Session,
    *,
    organization_id: uuid.UUID,
    report_id: uuid.UUID,
    actor_user_id: uuid.UUID,
    request_id: str | None,
    ip_address: str | None,
    user_agent: str | None,
) -> tuple[Path, str]:
    """Return absolute PDF path and suggested download filename, or raise ``RouteHttpError``."""

    row = report_repository.fetch_report(db, organization_id, report_id)
    if row is None or not row.storage_uri:
        raise RouteHttpError(404, "Report file not found")
    if row.status != ReportStatus.ready.value:
        raise RouteHttpError(409, "Report is not ready for download")

    path = pdf_absolute_path(row.storage_uri)
    if not path.is_file():
        raise RouteHttpError(404, "Report file missing on server")

    append_audit_event(
        db,
        organization_id=organization_id,
        actor_user_id=actor_user_id,
        action="report.downloaded",
        resource_type="report",
        resource_id=str(report_id),
        payload={"filename": path.name},
        request_id=request_id,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.commit()

    safe_name = f"scanlyr-ai-governance-{report_id}.pdf"
    return path, safe_name
