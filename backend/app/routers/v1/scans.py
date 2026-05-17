"""Scan history API at ``/api/v1/scans`` (aliases the scan history service layer)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.auth_context import AuthContext, get_auth_context, require_authenticated
from app.core.deps import get_db
from app.core.errors import ErrorResponse
from app.schemas.scan_history import ScanHistoryDetail, ScanHistoryListResponse
from app.services.http_errors import RouteHttpError
from app.services.scan_history_service import build_scan_history_list, get_scan_history_detail

router = APIRouter(
    prefix="/scans",
    tags=["scans"],
    dependencies=[Depends(require_authenticated)],
)


@router.get(
    "/history",
    response_model=ScanHistoryListResponse,
    summary="List scan history",
    description=(
        "Paginated scan history for the authenticated organization. "
        "Filter by `risk_level` (low, medium, high, critical)."
    ),
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
)
def list_scans_history(
    db: Annotated[Session, Depends(get_db)],
    auth: Annotated[AuthContext, Depends(get_auth_context)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    risk_level: Annotated[str | None, Query(description="low, medium, high, or critical")] = None,
    content_type: Annotated[str | None, Query(description="prompt, output, or auto")] = None,
    user_id: Annotated[uuid.UUID | None, Query()] = None,
    scanned_from: Annotated[datetime | None, Query()] = None,
    scanned_to: Annotated[datetime | None, Query()] = None,
    min_risk_score: Annotated[int | None, Query(ge=0, le=100)] = None,
    max_risk_score: Annotated[int | None, Query(ge=0, le=100)] = None,
) -> ScanHistoryListResponse:
    return build_scan_history_list(
        db,
        organization_id=auth.org_id,
        limit=limit,
        offset=offset,
        risk_level=risk_level,
        content_type=content_type,
        user_id=user_id,
        scanned_from=scanned_from,
        scanned_to=scanned_to,
        min_risk_score=min_risk_score,
        max_risk_score=max_risk_score,
    )


@router.get(
    "/{scan_id}",
    response_model=ScanHistoryDetail,
    summary="Get scan by id",
    description="Full scan record including input text, findings, and complete analysis result.",
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def get_scan_by_id(
    scan_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    auth: Annotated[AuthContext, Depends(get_auth_context)],
) -> ScanHistoryDetail:
    try:
        return get_scan_history_detail(db, organization_id=auth.org_id, scan_id=scan_id)
    except RouteHttpError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
