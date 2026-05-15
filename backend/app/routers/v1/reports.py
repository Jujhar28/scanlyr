from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_token_payload, require_roles
from app.core.errors import ErrorResponse
from app.models.membership import Membership
from app.schemas.report import (
    GenerateReportRequest,
    GenerateReportResponse,
    ReportDetail,
    ReportListResponse,
)
from app.services.http_errors import RouteHttpError
from app.services.report_download_service import prepare_report_pdf_download
from app.services.report_route_service import (
    build_report_detail_response,
    build_report_list_response,
    generate_compliance_report_response,
)

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post(
    "/generate",
    response_model=GenerateReportResponse,
    summary="Generate compliance report",
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
)
def generate_report(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    membership: Annotated[Membership, Depends(require_roles("admin"))],
    body: GenerateReportRequest | None = None,
) -> GenerateReportResponse:
    return generate_compliance_report_response(
        db,
        membership=membership,
        body=body,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )


@router.get(
    "",
    response_model=ReportListResponse,
    summary="List reports",
    responses={401: {"model": ErrorResponse}},
)
def reports_list(
    db: Annotated[Session, Depends(get_db)],
    payload: Annotated[dict, Depends(get_token_payload)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ReportListResponse:
    org_id = uuid.UUID(str(payload["org_id"]))
    return build_report_list_response(db, organization_id=org_id, limit=limit, offset=offset)


@router.get(
    "/{report_id}/download",
    summary="Download report PDF",
    description="Streams the stored PDF for the report when generation completed successfully.",
    responses={
        200: {
            "description": "PDF file",
            "content": {"application/pdf": {"schema": {"type": "string", "format": "binary"}}},
        },
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
)
def report_download(
    report_id: uuid.UUID,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    payload: Annotated[dict, Depends(get_token_payload)],
) -> FileResponse:
    org_id = uuid.UUID(str(payload["org_id"]))
    try:
        path, safe_name = prepare_report_pdf_download(
            db,
            organization_id=org_id,
            report_id=report_id,
            actor_user_id=uuid.UUID(str(payload["sub"])),
            request_id=getattr(request.state, "request_id", None),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except RouteHttpError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    return FileResponse(
        path,
        media_type="application/pdf",
        filename=safe_name,
        headers={"Cache-Control": "private, no-store"},
    )


@router.get(
    "/{report_id}",
    response_model=ReportDetail,
    summary="Report metadata",
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def report_detail(
    report_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    payload: Annotated[dict, Depends(get_token_payload)],
) -> ReportDetail:
    org_id = uuid.UUID(str(payload["org_id"]))
    detail = build_report_detail_response(db, organization_id=org_id, report_id=report_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return detail
